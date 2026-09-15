"""credentials for Backlink Operations V1."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from typing import Any
import json
import os
import shutil
import stat
from backlink_records.model import RecordValidationError

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


CONFIG_ENV = "BACKLINK_GO_CONFIG_DIR"


def default_config_dir() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    return Path(os.environ.get(CONFIG_ENV, repository_root / ".backlink-go" / "runtime"))


def ensure_private_dir(config_dir: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(config_dir, 0o700)


def write_private_json(target: Path, payload: dict[str, Any]) -> None:
    ensure_private_dir(target.parent)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(target)
    os.chmod(target, 0o600)


def require_private_file(target: Path) -> None:
    if not target.is_file():
        raise RecordValidationError(f"required private file not found: {target.name}")
    if os.name != "nt" and stat.S_IMODE(target.parent.stat().st_mode) & 0o077:
        raise RecordValidationError("configuration directory permissions must be 0700")
    if os.name != "nt" and stat.S_IMODE(target.stat().st_mode) & 0o077:
        raise RecordValidationError(f"private file permissions must be 0600: {target.name}")


def read_json_file(source: Path) -> dict[str, Any]:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecordValidationError(f"cannot read valid JSON input: {source}") from exc
    if not isinstance(payload, dict):
        raise RecordValidationError("input JSON must be an object")
    return payload


@contextmanager
def writer_lock(config_dir: Path):
    ensure_private_dir(config_dir)
    lock_path = config_dir / "v1-sheets.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        stale = False
        try:
            owner_pid = int(lock_path.read_text(encoding="utf-8").strip())
            os.kill(owner_pid, 0)
        except (ValueError, ProcessLookupError, OSError):
            stale = True
        if not stale:
            raise RecordValidationError("another V1 Sheets writer is active") from exc
        lock_path.unlink(missing_ok=True)
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
    finally:
        os.close(descriptor)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def authenticate(config_dir: Path, client_secret: Path) -> dict[str, str]:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RecordValidationError("Google API dependencies are missing; run uv sync --dev") from exc
    if not client_secret.is_file():
        raise RecordValidationError("OAuth client-secret file does not exist")
    ensure_private_dir(config_dir)
    stored_client = config_dir / "google-oauth-client.json"
    shutil.copyfile(client_secret, stored_client)
    os.chmod(stored_client, 0o600)
    flow = InstalledAppFlow.from_client_secrets_file(str(stored_client), SCOPES)
    credentials = flow.run_local_server(port=0)
    token_payload = json.loads(credentials.to_json())
    write_private_json(config_dir / "google-token.json", token_payload)
    return {"authenticated": "yes", "scope": SCOPES[0]}


def load_credentials(config_dir: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RecordValidationError("Google API dependencies are missing; run uv sync --dev") from exc
    token_path = config_dir / "google-token.json"
    if not token_path.is_file():
        raise RecordValidationError("OAuth token not found; run the auth command")
    require_private_file(token_path)
    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        write_private_json(token_path, json.loads(credentials.to_json()))
    if not credentials.valid:
        raise RecordValidationError("OAuth credentials are invalid; run the auth command again")
    return credentials


def build_service(config_dir: Path):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RecordValidationError("Google API dependencies are missing; run uv sync --dev") from exc
    return build("sheets", "v4", credentials=load_credentials(config_dir), cache_discovery=False)
