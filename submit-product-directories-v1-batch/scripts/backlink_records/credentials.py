"""credentials for Backlink Operations V1."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import shutil
import stat
import tempfile
from backlink_records.model import RecordValidationError

SHEETS_SCOPE = "https://www.googleapis.com/auth/drive.file"
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
SCOPES = [SHEETS_SCOPE, GMAIL_READONLY_SCOPE]
RUNTIME_FILES = ("google-oauth-client.json", "google-token.json", "v1-sheets.json")


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


def validate_desktop_client(payload: dict[str, Any]) -> None:
    installed = payload.get("installed")
    if not isinstance(installed, dict):
        raise RecordValidationError("OAuth JSON must contain an installed desktop client")
    required = {"client_id", "client_secret", "auth_uri", "token_uri"}
    if not required.issubset(installed):
        raise RecordValidationError("OAuth desktop client JSON is incomplete")


def backup_runtime_state(
    config_dir: Path,
    filenames: tuple[str, ...] = RUNTIME_FILES,
) -> Path | None:
    existing = [config_dir / name for name in filenames if (config_dir / name).is_file()]
    if not existing:
        return None
    ensure_private_dir(config_dir)
    backup_root = config_dir / "backups"
    ensure_private_dir(backup_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_dir = backup_root / stamp
    backup_dir.mkdir(mode=0o700)
    os.chmod(backup_dir, 0o700)
    for source in existing:
        target = backup_dir / source.name
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
    return backup_dir


def restore_runtime_state(config_dir: Path, backup_dir: Path, filenames: tuple[str, ...]) -> None:
    for name in filenames:
        source = backup_dir / name
        target = config_dir / name
        if source.is_file():
            shutil.copyfile(source, target)
            os.chmod(target, 0o600)
        else:
            target.unlink(missing_ok=True)


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


def authenticate(config_dir: Path, client_secret: Path, *, replace: bool = False) -> dict[str, object]:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RecordValidationError("Google API dependencies are missing; run uv sync --dev") from exc
    if not client_secret.is_file():
        raise RecordValidationError("OAuth client-secret file does not exist")
    client_payload = read_json_file(client_secret)
    validate_desktop_client(client_payload)
    ensure_private_dir(config_dir)
    active = [config_dir / name for name in ("google-oauth-client.json", "google-token.json")]
    if any(path.exists() for path in active) and not replace:
        raise RecordValidationError("OAuth credentials already exist; rerun auth with --replace")
    backup_dir = backup_runtime_state(config_dir) if replace else None

    staged_client: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(prefix="google-oauth-client-", suffix=".json", dir=config_dir)
        os.close(descriptor)
        staged_client = Path(raw_path)
        staged_client.write_text(json.dumps(client_payload, ensure_ascii=False), encoding="utf-8")
        os.chmod(staged_client, 0o600)
        flow = InstalledAppFlow.from_client_secrets_file(str(staged_client), SCOPES)
        credentials = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent select_account",
        )
        granted = set(credentials.granted_scopes or credentials.scopes or [])
        missing = set(SCOPES) - granted
        if missing:
            raise RecordValidationError("Google authorization did not grant every required scope")
        if not credentials.refresh_token:
            raise RecordValidationError("Google authorization did not return a refresh token")
        token_payload = json.loads(credentials.to_json())
    finally:
        if staged_client is not None:
            staged_client.unlink(missing_ok=True)

    staged_targets: dict[str, Path] = {}
    try:
        for name, payload in (
            ("google-oauth-client.json", client_payload),
            ("google-token.json", token_payload),
        ):
            staged = config_dir / f".{name}.new"
            staged.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.chmod(staged, 0o600)
            staged_targets[name] = staged
        for name, staged in staged_targets.items():
            target = config_dir / name
            staged.replace(target)
            os.chmod(target, 0o600)
    except Exception as exc:
        for staged in staged_targets.values():
            staged.unlink(missing_ok=True)
        if backup_dir is not None:
            restore_runtime_state(
                config_dir,
                backup_dir,
                ("google-oauth-client.json", "google-token.json"),
            )
        else:
            for name in ("google-oauth-client.json", "google-token.json"):
                (config_dir / name).unlink(missing_ok=True)
        raise RecordValidationError("could not activate the new OAuth credentials") from exc
    return {
        "authenticated": True,
        "scopes": list(SCOPES),
        "backup": str(backup_dir) if backup_dir else None,
    }


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
    token_payload = read_json_file(token_path)
    stored_scopes = set(token_payload.get("scopes") or [])
    if not set(SCOPES).issubset(stored_scopes):
        raise RecordValidationError("OAuth token is missing required scopes; run auth --replace")
    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as exc:
            raise RecordValidationError("OAuth refresh failed; run auth --replace") from exc
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


def build_gmail_service(config_dir: Path):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RecordValidationError("Google API dependencies are missing; run uv sync --dev") from exc
    return build("gmail", "v1", credentials=load_credentials(config_dir), cache_discovery=False)
