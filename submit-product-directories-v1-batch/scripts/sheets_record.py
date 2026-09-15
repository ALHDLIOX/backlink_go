#!/usr/bin/env python3
"""Direct Google Sheets record store for Backlink Operations V1."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from record_model import (
    ALLOWED_STATUSES,
    CAMPAIGN_HEADERS,
    DROPDOWNS,
    EVENT_HEADERS,
    EXECUTED,
    HEADER_LABELS,
    LEGACY_HEADER_LABELS,
    LEGACY_SCHEMA_VERSION,
    LEGACY_TABLE_HEADERS,
    PLACEMENT_HEADERS,
    PREVIOUS_SCHEMA_VERSION,
    PLATFORM_HEADERS,
    SCHEMA_VERSION,
    SCHEMA_V5_TABLE_HEADERS,
    SCHEMA_V6_TABLE_HEADERS,
    SCHEMA_V7_TABLE_HEADERS,
    TABLE_HEADERS,
    compact_record_timestamps,
    display_headers,
    migrate_legacy_record,
    migrate_v6_records,
    RecordValidationError,
    audit_records,
    export_campaign_markdown,
    normalize_campaign_input,
    platform_domains_match,
    prepare_record,
    row_values,
    rows_to_records,
    validate_campaign,
    validate_event,
    validate_placement,
    validate_platform,
)


DEFAULT_TITLE = "Backlink Operations"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
METADATA_KEY = "spd_v1_schema_version"
CONFIG_ENV = "BACKLINK_GO_CONFIG_DIR"

COLOR_GREEN = ({"red": 0.91, "green": 0.97, "blue": 0.93}, {"red": 0.12, "green": 0.38, "blue": 0.23})
COLOR_BLUE = ({"red": 0.92, "green": 0.95, "blue": 0.99}, {"red": 0.13, "green": 0.31, "blue": 0.55})
COLOR_YELLOW = ({"red": 1.0, "green": 0.97, "blue": 0.87}, {"red": 0.48, "green": 0.34, "blue": 0.06})
COLOR_RED = ({"red": 0.99, "green": 0.92, "blue": 0.93}, {"red": 0.55, "green": 0.16, "blue": 0.20})
COLOR_GRAY = ({"red": 0.95, "green": 0.96, "blue": 0.97}, {"red": 0.32, "green": 0.36, "blue": 0.42})


def fixed_option_colors() -> dict[tuple[str, str], dict[str, tuple[dict[str, float], dict[str, float]]]]:
    status = {}
    for value in ALLOWED_STATUSES:
        if value == "published": status[value] = COLOR_GREEN
        elif value in {"submitted", "submitted for review", "scheduled", "awaiting approval", "awaiting email verification"}: status[value] = COLOR_BLUE
        elif value in {"in progress", "draft saved", "outcome unknown"}: status[value] = COLOR_YELLOW
        elif value.startswith("blocked") or value in {"rejected", "removed", "unavailable", "paid-only", "ineligible"}: status[value] = COLOR_RED
        else: status[value] = COLOR_GRAY
    return {
        ("Platforms", "account_required"): {"yes": COLOR_BLUE, "no": COLOR_GREEN, "unknown": COLOR_GRAY},
        ("Platforms", "cost_model"): {
            "free": COLOR_GREEN, "freemium": COLOR_BLUE, "paid": COLOR_RED, "unknown": COLOR_GRAY,
        },
        ("Platforms", "reciprocal_requirement"): {
            "none": COLOR_GREEN, "optional": COLOR_YELLOW, "required": COLOR_RED, "unknown": COLOR_GRAY,
        },
        ("Platforms", "availability"): {
            "available": COLOR_GREEN, "unavailable": COLOR_RED, "unknown": COLOR_GRAY,
        },
        ("Placements", "status"): status,
    }


def default_config_dir() -> Path:
    repository_root = Path(__file__).resolve().parents[2]
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


def column_letter(index: int) -> str:
    if index < 1:
        raise ValueError("column index must be positive")
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def workbook_create_body(title: str) -> dict[str, Any]:
    return {
        "properties": {"title": title},
        "sheets": [
            {
                "properties": {
                    "title": tab_name,
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": len(headers),
                        "frozenRowCount": 1,
                    },
                }
            }
            for tab_name, headers in TABLE_HEADERS.items()
        ],
    }


def initialization_batch_requests(properties: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = [
        {
            "createDeveloperMetadata": {
                "developerMetadata": {
                    "metadataKey": METADATA_KEY,
                    "metadataValue": SCHEMA_VERSION,
                    "visibility": "DOCUMENT",
                    "location": {"spreadsheet": True},
                }
            }
        }
    ]
    for tab_name, headers in TABLE_HEADERS.items():
        sheet_id = properties[tab_name]["sheetId"]
        requests.extend(
            [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers),
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.12, "green": 0.32, "blue": 0.55},
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                },
                                "wrapStrategy": "WRAP",
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,wrapStrategy)",
                    }
                },
                {
                    "setBasicFilter": {
                        "filter": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "startColumnIndex": 0,
                                "endColumnIndex": len(headers),
                            }
                        }
                    }
                },
            ]
        )
    for (tab_name, header), allowed in DROPDOWNS.items():
        sheet_id = properties[tab_name]["sheetId"]
        column_index = TABLE_HEADERS[tab_name].index(header)
        requests.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": column_index,
                        "endColumnIndex": column_index + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": value} for value in allowed],
                        },
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
        )
    return requests


def readable_format_requests(properties: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Build an idempotent, readable workbook presentation."""
    requests: list[dict[str, Any]] = []
    for tab_name, headers in TABLE_HEADERS.items():
        sheet_id = properties[tab_name]["sheetId"]
        for index in reversed(range(int(properties[tab_name].get("_conditionalRuleCount", 0)))):
            requests.append({"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": index}})
        requests.extend(
            [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "hideGridlines": False,
                                "frozenRowCount": 1,
                                "frozenColumnCount": min(2, len(headers)),
                            },
                        },
                        "fields": (
                            "gridProperties.hideGridlines,gridProperties.frozenRowCount,"
                            "gridProperties.frozenColumnCount"
                        ),
                    }
                },
                {"clearBasicFilter": {"sheetId": sheet_id}},
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers),
                        }
                    }
                },
                {
                    "setBasicFilter": {
                        "filter": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "startColumnIndex": 0,
                                "endColumnIndex": len(headers),
                            }
                        }
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers),
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.86, "green": 0.90, "blue": 0.95},
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {"red": 0.12, "green": 0.16, "blue": 0.22},
                                },
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)",
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers),
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.98, "green": 0.985, "blue": 0.995},
                                "textFormat": {"foregroundColor": {"red": 0.18, "green": 0.22, "blue": 0.28}},
                                "verticalAlignment": "MIDDLE",
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                        "properties": {"pixelSize": 48},
                        "fields": "pixelSize",
                    }
                },
            ]
        )
        for index, label in enumerate(display_headers(tab_name)):
            width = min(240, max(120, len(label) * 18 + 36))
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": index,
                            "endIndex": index + 1,
                        },
                        "properties": {"pixelSize": width},
                        "fields": "pixelSize",
                    }
                }
            )
    for (tab_name, header), values in fixed_option_colors().items():
        sheet_id = properties[tab_name]["sheetId"]
        column_index = TABLE_HEADERS[tab_name].index(header)
        for value, (background, foreground) in values.items():
            requests.append(
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [
                                {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "startColumnIndex": column_index,
                                    "endColumnIndex": column_index + 1,
                                }
                            ],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": value}],
                                },
                                "format": {
                                    "backgroundColor": background,
                                    "textFormat": {"foregroundColor": foreground, "bold": True},
                                },
                            },
                        },
                        "index": 0,
                    }
                }
            )
    for (tab_name, header), allowed in DROPDOWNS.items():
        sheet_id = properties[tab_name]["sheetId"]
        column_index = TABLE_HEADERS[tab_name].index(header)
        requests.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": column_index,
                        "endColumnIndex": column_index + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": value} for value in allowed],
                        },
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
        )
    return requests


def format_workbook(store: "GoogleSheetsStore") -> dict[str, object]:
    metadata = store.metadata()
    versions = [
        item.get("metadataValue") for item in metadata.get("developerMetadata", [])
        if item.get("metadataKey") == METADATA_KEY
    ]
    properties = {}
    for sheet in metadata.get("sheets", []):
        item = dict(sheet["properties"])
        item["_conditionalRuleCount"] = len(sheet.get("conditionalFormats", []))
        properties[item["title"]] = item
    if versions != [SCHEMA_VERSION] or set(properties) != set(TABLE_HEADERS):
        raise RecordValidationError("workbook schema is missing or unsupported")
    data = []
    for tab_name, headers in TABLE_HEADERS.items():
        data.append({
            "range": f"'{tab_name}'!A1:{column_letter(len(headers))}1",
            "values": [display_headers(tab_name)],
        })
    store.service.spreadsheets().values().batchUpdate(
        spreadsheetId=store.spreadsheet_id,
        body={"valueInputOption": "RAW", "data": data},
    ).execute()
    store.service.spreadsheets().batchUpdate(
        spreadsheetId=store.spreadsheet_id,
        body={"requests": readable_format_requests(properties)},
    ).execute()
    store.verify_schema()
    return {"formatted": True, "worksheets": list(TABLE_HEADERS), "schema_valid": True}


def _cell_row(values: list[object]) -> dict[str, object]:
    return {
        "values": [
            {"userEnteredValue": {"stringValue": str(value)}}
            for value in values
        ]
    }


def schema_v8_migration_requests(
    properties: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, str]]],
    source_headers: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Build one atomic migration that replaces three result tabs with Placements."""
    next_sheet_id = max(int(item["sheetId"]) for item in properties.values()) + 1
    current_properties = {name: dict(item) for name, item in properties.items()}
    requests: list[dict[str, Any]] = []
    for tab_name, headers in TABLE_HEADERS.items():
        if tab_name in current_properties:
            continue
        current_properties[tab_name] = {
            "sheetId": next_sheet_id,
            "title": tab_name,
            "gridProperties": {
                "rowCount": max(1000, len(records.get(tab_name, [])) + 1),
                "columnCount": len(headers),
                "frozenRowCount": 1,
            },
            "index": list(TABLE_HEADERS).index(tab_name),
            "_conditionalRuleCount": 0,
        }
        next_sheet_id += 1
        requests.append(
            {
                "addSheet": {
                    "properties": {
                        key: value for key, value in current_properties[tab_name].items()
                        if not key.startswith("_")
                    }
                }
            }
        )
    for tab_name, new_headers in TABLE_HEADERS.items():
        sheet_id = current_properties[tab_name]["sheetId"]
        previous_count = len(source_headers.get(tab_name, new_headers))
        rows = [display_headers(tab_name)] + [
            row_values(new_headers, item) for item in records.get(tab_name, [])
        ]
        if tab_name in source_headers:
            requests.append({"clearBasicFilter": {"sheetId": sheet_id}})
            requests.append(
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": previous_count,
                        }
                    }
                }
            )
        requests.extend(
            [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "columnCount": len(new_headers),
                                "frozenRowCount": 1,
                            },
                        },
                        "fields": "gridProperties.columnCount,gridProperties.frozenRowCount",
                    }
                },
                {
                    "updateCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": len(rows),
                            "startColumnIndex": 0,
                            "endColumnIndex": len(new_headers),
                        },
                        "rows": [_cell_row(row) for row in rows],
                        "fields": "userEnteredValue",
                    }
                },
                {
                    "setBasicFilter": {
                        "filter": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "startColumnIndex": 0,
                                "endColumnIndex": len(new_headers),
                            }
                        }
                    }
                },
            ]
        )
    for (tab_name, header), allowed in DROPDOWNS.items():
        sheet_id = current_properties[tab_name]["sheetId"]
        column_index = TABLE_HEADERS[tab_name].index(header)
        requests.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": column_index,
                        "endColumnIndex": column_index + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": value} for value in allowed],
                        },
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
        )
    obsolete = [name for name in ("Submissions", "Articles", "SocialPosts") if name in current_properties]
    for name in obsolete:
        requests.append({"deleteSheet": {"sheetId": current_properties[name]["sheetId"]}})
        current_properties.pop(name)
    for index, name in enumerate(TABLE_HEADERS):
        requests.append({"updateSheetProperties": {"properties": {"sheetId": current_properties[name]["sheetId"], "index": index}, "fields": "index"}})
    requests.extend(readable_format_requests(current_properties))
    requests.append(
        {
            "updateDeveloperMetadata": {
                "dataFilters": [
                    {
                        "developerMetadataLookup": {
                            "metadataKey": METADATA_KEY,
                            "locationType": "SPREADSHEET",
                        }
                    }
                ],
                "developerMetadata": {"metadataValue": SCHEMA_VERSION},
                "fields": "metadataValue",
            }
        }
    )
    return requests


def migrate_schema_v8(config_dir: Path) -> dict[str, object]:
    """Migrate the configured workbook from schema v4-v7 to schema v8."""
    config_path = config_dir / "v1-sheets.json"
    require_private_file(config_path)
    config = read_json_file(config_path)
    if not config.get("spreadsheet_id"):
        raise RecordValidationError("workbook config is invalid or unsupported")
    store = GoogleSheetsStore(build_service(config_dir), str(config["spreadsheet_id"]))
    if config.get("schema_version") == SCHEMA_VERSION:
        store.verify_schema()
        return {"migrated": False, "schema_version": SCHEMA_VERSION, "reason": "already current"}
    source_version = str(config.get("schema_version", ""))
    if source_version not in {LEGACY_SCHEMA_VERSION, "5", "6", PREVIOUS_SCHEMA_VERSION}:
        raise RecordValidationError("workbook config is invalid or unsupported")

    metadata = store.metadata()
    remote_versions = [
        item.get("metadataValue") for item in metadata.get("developerMetadata", [])
        if item.get("metadataKey") == METADATA_KEY
    ]
    if remote_versions == [SCHEMA_VERSION]:
        store.verify_schema()
        config["schema_version"] = SCHEMA_VERSION
        write_private_json(config_path, config)
        return {"migrated": False, "schema_version": SCHEMA_VERSION, "reason": "reconciled config"}

    source_headers = LEGACY_TABLE_HEADERS if source_version == LEGACY_SCHEMA_VERSION else (
        SCHEMA_V5_TABLE_HEADERS if source_version == "5" else (
            SCHEMA_V6_TABLE_HEADERS if source_version == "6" else SCHEMA_V7_TABLE_HEADERS
        )
    )
    store.verify_schema(source_version, source_headers)
    source_records_by_tab: dict[str, list[dict[str, str]]] = {}
    for tab_name, old_headers in source_headers.items():
        values = store._read_values(f"'{tab_name}'!A2:{column_letter(len(old_headers))}")
        source_records = rows_to_records(old_headers, values)
        source_records_by_tab[tab_name] = (
            [migrate_legacy_record(tab_name, item) for item in source_records]
            if source_version == LEGACY_SCHEMA_VERSION else source_records
        )
    if source_version == "7":
        migrated_records = {
            tab_name: [compact_record_timestamps({key: str(item.get(key, "")) for key in TABLE_HEADERS[tab_name]}) for item in items]
            for tab_name, items in source_records_by_tab.items()
        }
    else:
        source_records_by_tab.setdefault("Articles", [])
        source_records_by_tab.setdefault("SocialPosts", [])
        migrated_records = migrate_v6_records(source_records_by_tab)
    audit = audit_records(
        campaigns=migrated_records["Campaigns"],
        placements=migrated_records["Placements"],
        events=migrated_records["Events"],
        platforms=migrated_records["Platforms"],
    )
    if not audit["valid"]:
        raise RecordValidationError("migrated data failed validation: " + "; ".join(audit["errors"]))
    properties = {}
    for sheet in metadata.get("sheets", []):
        item = dict(sheet["properties"])
        item["_conditionalRuleCount"] = len(sheet.get("conditionalFormats", []))
        properties[item["title"]] = item
    store.service.spreadsheets().batchUpdate(
        spreadsheetId=store.spreadsheet_id,
        body={"requests": schema_v8_migration_requests(properties, migrated_records, source_headers)},
    ).execute()
    store.verify_schema()
    config["schema_version"] = SCHEMA_VERSION
    write_private_json(config_path, config)
    return {
        "migrated": True,
        "from_schema_version": source_version,
        "schema_version": SCHEMA_VERSION,
        "rows": {name: len(items) for name, items in migrated_records.items()},
    }


def migrate_schema_v5(config_dir: Path) -> dict[str, object]:
    """Compatibility alias that migrates an old workbook to the current schema."""
    return migrate_schema_v8(config_dir)


def migrate_schema_v6(config_dir: Path) -> dict[str, object]:
    """Compatibility alias that migrates an old workbook to the current schema."""
    return migrate_schema_v8(config_dir)


def migrate_schema_v7(config_dir: Path) -> dict[str, object]:
    """Compatibility alias that migrates an old workbook to the current schema."""
    return migrate_schema_v8(config_dir)


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


class GoogleSheetsStore:
    def __init__(self, service: Any, spreadsheet_id: str):
        self.service = service
        self.spreadsheet_id = spreadsheet_id

    @classmethod
    def create(cls, service: Any, title: str) -> tuple["GoogleSheetsStore", dict[str, str]]:
        created = (
            service.spreadsheets()
            .create(
                body=workbook_create_body(title),
                fields="spreadsheetId,spreadsheetUrl,sheets.properties",
            )
            .execute()
        )
        store = cls(service, created["spreadsheetId"])
        properties = {
            sheet["properties"]["title"]: sheet["properties"] for sheet in created.get("sheets", [])
        }
        data = []
        for tab_name, headers in TABLE_HEADERS.items():
            last_column = column_letter(len(headers))
            data.append({"range": f"'{tab_name}'!A1:{last_column}1", "values": [display_headers(tab_name)]})
        (
            service.spreadsheets()
            .values()
            .batchUpdate(
                spreadsheetId=store.spreadsheet_id,
                body={"valueInputOption": "RAW", "data": data},
            )
            .execute()
        )
        service.spreadsheets().batchUpdate(
            spreadsheetId=store.spreadsheet_id,
            body={
                "requests": initialization_batch_requests(properties)
                + readable_format_requests(properties)
            },
        ).execute()
        return store, {
            "spreadsheet_id": store.spreadsheet_id,
            "spreadsheet_url": created["spreadsheetUrl"],
            "schema_version": SCHEMA_VERSION,
            "title": title,
        }

    def metadata(self) -> dict[str, Any]:
        return (
            self.service.spreadsheets()
            .get(
                spreadsheetId=self.spreadsheet_id,
                includeGridData=False,
                fields=(
                    "spreadsheetId,spreadsheetUrl,properties.title,developerMetadata,"
                    "sheets(properties(sheetId,title,gridProperties),conditionalFormats)"
                ),
            )
            .execute()
        )

    def verify_schema(
        self,
        schema_version: str = SCHEMA_VERSION,
        table_headers: dict[str, list[str]] = TABLE_HEADERS,
    ) -> dict[str, Any]:
        metadata = self.metadata()
        versions = [
            item.get("metadataValue")
            for item in metadata.get("developerMetadata", [])
            if item.get("metadataKey") == METADATA_KEY
        ]
        if versions != [schema_version]:
            raise RecordValidationError("workbook schema version is missing or unsupported")
        sheet_map = {item["properties"]["title"]: item["properties"] for item in metadata.get("sheets", [])}
        if set(sheet_map) != set(table_headers):
            raise RecordValidationError("workbook worksheets do not match the schema")
        for tab_name, headers in table_headers.items():
            if tab_name not in sheet_map:
                raise RecordValidationError(f"missing worksheet: {tab_name}")
            grid = sheet_map[tab_name].get("gridProperties", {})
            if grid.get("columnCount") != len(headers) or grid.get("frozenRowCount") != 1:
                raise RecordValidationError(f"schema drift in {tab_name} grid properties")
            actual = self._read_values(f"'{tab_name}'!A1:{column_letter(len(headers))}1")
            actual_headers = actual[0] if actual else []
            labels = HEADER_LABELS if schema_version in {SCHEMA_VERSION, "7"} else LEGACY_HEADER_LABELS
            expected_headers = [labels[header] for header in headers]
            if actual_headers != expected_headers:
                raise RecordValidationError(f"schema drift in {tab_name} headers")
        return metadata

    def _read_values(self, range_name: str) -> list[list[Any]]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=range_name, valueRenderOption="UNFORMATTED_VALUE")
            .execute()
        )
        return result.get("values", [])

    def records(self, tab_name: str) -> list[dict[str, str]]:
        return [record for _, record in self.records_with_rows(tab_name)]

    def records_with_rows(self, tab_name: str) -> list[tuple[int, dict[str, str]]]:
        headers = TABLE_HEADERS[tab_name]
        values = self._read_values(f"'{tab_name}'!A2:{column_letter(len(headers))}")
        result = []
        for row_number, row in enumerate(values, start=2):
            if not any(str(value).strip() for value in row):
                continue
            padded = row + [""] * (len(headers) - len(row))
            result.append((row_number, {header: str(padded[index]) for index, header in enumerate(headers)}))
        return result

    def find(self, tab_name: str, key_field: str, key_value: str) -> tuple[int, dict[str, str]] | None:
        for offset, record in self.records_with_rows(tab_name):
            if record.get(key_field) == key_value:
                return offset, record
        return None

    def append(self, tab_name: str, record: dict[str, object]) -> None:
        headers = TABLE_HEADERS[tab_name]
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab_name}'!A:{column_letter(len(headers))}",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"majorDimension": "ROWS", "values": [row_values(headers, record)]},
        ).execute()

    def update(self, tab_name: str, row_number: int, record: dict[str, object]) -> None:
        headers = TABLE_HEADERS[tab_name]
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab_name}'!A{row_number}:{column_letter(len(headers))}{row_number}",
            valueInputOption="RAW",
            body={"majorDimension": "ROWS", "values": [row_values(headers, record)]},
        ).execute()


def load_store(config_dir: Path, schema_version: str = SCHEMA_VERSION) -> GoogleSheetsStore:
    config_path = config_dir / "v1-sheets.json"
    if not config_path.is_file():
        raise RecordValidationError("workbook config not found; run init")
    require_private_file(config_path)
    config = read_json_file(config_path)
    if config.get("schema_version") != schema_version or not config.get("spreadsheet_id"):
        raise RecordValidationError("workbook config is invalid or unsupported")
    return GoogleSheetsStore(build_service(config_dir), str(config["spreadsheet_id"]))


def doctor(config_dir: Path) -> dict[str, object]:
    config_path = config_dir / "v1-sheets.json"
    require_private_file(config_path)
    config = read_json_file(config_path)
    schema_version = str(config.get("schema_version", ""))
    table_headers = {
        LEGACY_SCHEMA_VERSION: LEGACY_TABLE_HEADERS,
        "5": SCHEMA_V5_TABLE_HEADERS,
        "6": SCHEMA_V6_TABLE_HEADERS,
        PREVIOUS_SCHEMA_VERSION: SCHEMA_V7_TABLE_HEADERS,
        SCHEMA_VERSION: TABLE_HEADERS,
    }.get(schema_version)
    if table_headers is None:
        raise RecordValidationError("workbook config is invalid or unsupported")
    store = load_store(config_dir, schema_version)
    metadata = store.verify_schema(schema_version, table_headers)
    current = schema_version == SCHEMA_VERSION
    return {
        "healthy": current,
        "migration_required": not current,
        "spreadsheet_id": store.spreadsheet_id,
        "title": metadata.get("properties", {}).get("title", ""),
        "schema_version": schema_version,
        "target_schema_version": SCHEMA_VERSION,
        "worksheets": list(table_headers),
    }


def records_with_rows(store: object, tab_name: str) -> list[tuple[int, dict[str, str]]]:
    method = getattr(store, "records_with_rows", None)
    if callable(method):
        return method(tab_name)
    return list(enumerate(store.records(tab_name), start=2))


def records_equal(headers: list[str], expected: dict[str, object], actual: dict[str, object]) -> bool:
    return all(str(expected.get(header, "")) == str(actual.get(header, "")) for header in headers)


def is_retryable_write_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    status = getattr(getattr(exc, "resp", None), "status", None)
    return status == 429 or isinstance(status, int) and 500 <= status <= 599


def safe_error_message(exc: Exception) -> str:
    message = str(exc).replace("\n", " ")
    message = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", message, flags=re.I)
    message = re.sub(
        r"([?&](?:token|key|api_key|apikey|code|state|session|auth|password|otp|signature|sig)=)[^&#\s]+",
        r"\1[redacted]",
        message,
        flags=re.I,
    )
    message = re.sub(r"(?<![\w-])\+\d[\d\s().-]{7,}\d(?![\w-])", "[redacted-phone]", message)
    message = re.sub(
        r"((?:password|passcode|otp|cookie|session[_ ]?id|oauth[_ ]?code)\s*[:=]\s*)\S+",
        r"\1[redacted]",
        message,
        flags=re.I,
    )
    message = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", message, flags=re.I)
    return message[:500]


def write_with_reconciliation(
    store: GoogleSheetsStore,
    tab_name: str,
    key_field: str,
    key_value: str,
    expected: dict[str, object],
    operation: Callable[[], None],
) -> None:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            operation()
        except Exception as exc:  # Transport and API errors may be ambiguous.
            if not is_retryable_write_error(exc):
                raise RecordValidationError(f"non-retryable write failure in {tab_name}") from exc
            last_error = exc
        found = store.find(tab_name, key_field, key_value)
        if found and records_equal(TABLE_HEADERS[tab_name], expected, found[1]):
            return
        if found:
            raise RecordValidationError(f"conflicting row found after write in {tab_name}") from last_error
        if last_error is None:
            raise RecordValidationError(f"written row could not be read back from {tab_name}")
        if attempt == 1:
            raise RecordValidationError(f"write failed after reconciliation in {tab_name}") from last_error


def upsert(store: GoogleSheetsStore, kind: str, payload: dict[str, Any]) -> dict[str, str]:
    mapping = {
        "platform": ("Platforms", "platform_id", PLATFORM_HEADERS, validate_platform),
        "campaign": ("Campaigns", "campaign_id", CAMPAIGN_HEADERS, validate_campaign),
        "placement": ("Placements", "idempotency_key", PLACEMENT_HEADERS, validate_placement),
    }
    if kind == "campaign":
        payload = normalize_campaign_input(payload)
    payload = compact_record_timestamps(payload)
    tab_name, key_field, headers, validator = mapping[kind]
    store.verify_schema()
    key_value = str(payload.get(key_field, ""))
    if not key_value:
        raise RecordValidationError(f"{key_field} is required")
    validator(payload)
    existing_rows = records_with_rows(store, tab_name)
    existing_records = [record for _, record in existing_rows]
    matches = [
        (index, record) for index, record in existing_rows
        if record.get(key_field) == key_value
    ]
    if len(matches) > 1:
        raise RecordValidationError(f"duplicate {key_field} rows found in {tab_name}")
    found = matches[0] if matches else None
    if kind == "placement":
        campaign = store.find("Campaigns", "campaign_id", str(payload.get("campaign_id", "")))
        platform = store.find("Platforms", "platform_id", str(payload.get("platform_id", "")))
        if not campaign:
            raise RecordValidationError("placement references an unknown campaign_id")
        if not platform:
            raise RecordValidationError("placement references an unknown platform_id")
        if str(campaign[1].get("product_canonical_id")) != str(payload.get("product_canonical_id")):
            raise RecordValidationError("placement product_canonical_id does not match campaign")
        if not platform_domains_match(
            platform[1].get("platform_domain", ""), payload.get("platform_domain", "")
        ):
            raise RecordValidationError("placement platform_domain does not match platform")
        if found and found[1].get("campaign_id") != str(payload.get("campaign_id")):
            raise RecordValidationError("idempotency_key already belongs to another campaign")
        for record in existing_records:
            if record.get("placement_id") == str(payload.get("placement_id")) and record.get("idempotency_key") != key_value:
                raise RecordValidationError("placement_id already belongs to another placement")
            if record.get("campaign_id") == str(payload.get("campaign_id")) and record.get("queue_id") == str(payload.get("queue_id")) and record.get("idempotency_key") != key_value:
                raise RecordValidationError("queue_id already belongs to another campaign placement")
        if str(payload.get("status", "")) in EXECUTED:
            linked_events = [
                event for event in store.records("Events")
                if event.get("idempotency_key") == key_value
                and event.get("campaign_id") == str(payload.get("campaign_id"))
                and event.get("queue_id") == str(payload.get("queue_id"))
            ]
            if not linked_events:
                raise RecordValidationError("executed placement state requires a prior linked event")
    if found:
        try:
            if int(found[1].get("row_version", "")) < 1:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"invalid current row_version in {tab_name}") from exc
        business_headers = [header for header in headers if header not in {"created_at", "updated_at", "row_version"}]
        if records_equal(business_headers, payload, found[1]):
            return {
                "action": "unchanged",
                "table": tab_name,
                "key": key_value,
                "row_version": str(found[1].get("row_version", "")),
            }
        if kind == "placement":
            previous_status = str(found[1].get("status", ""))
            next_status = str(payload.get("status", ""))
            if previous_status in {"submitted", "submitted for review", "scheduled", "awaiting approval", "awaiting email verification", "published", "outcome unknown"} and next_status in {"not attempted", "in progress", "draft saved"}:
                raise RecordValidationError("completed or pending idempotency key cannot be reopened")
        expected_version = str(payload.pop("expected_row_version", "")).strip()
        current_version = str(found[1].get("row_version", "")).strip()
        if not expected_version:
            raise RecordValidationError("expected_row_version is required when updating an existing row")
        if expected_version != current_version:
            raise RecordValidationError(
                f"row version conflict in {tab_name}: expected {expected_version}, current {current_version}"
            )
    elif "expected_row_version" in payload:
        expected_version = str(payload.pop("expected_row_version")).strip()
        if expected_version not in {"", "0"}:
            raise RecordValidationError("expected_row_version must be omitted or 0 for a new row")
    prepared = prepare_record(kind, payload, found[1] if found else None)
    if found:
        row_number = found[0]
        operation = lambda: store.update(tab_name, row_number, prepared)
        action = "updated"
    else:
        operation = lambda: store.append(tab_name, prepared)
        action = "created"
    write_with_reconciliation(store, tab_name, key_field, key_value, prepared, operation)
    return {"action": action, "table": tab_name, "key": key_value, "row_version": prepared["row_version"]}


def append_event(store: GoogleSheetsStore, payload: dict[str, Any]) -> dict[str, str]:
    store.verify_schema()
    prepared = prepare_record("event", payload)
    event_id = prepared["event_id"]
    event_rows = records_with_rows(store, "Events")
    event_records = [record for _, record in event_rows]
    matches = [
        (index, record) for index, record in event_rows
        if record.get("event_id") == event_id
    ]
    if len(matches) > 1:
        raise RecordValidationError("duplicate event_id rows found in Events")
    found = matches[0] if matches else None
    if found:
        if records_equal(EVENT_HEADERS, prepared, found[1]):
            return {"action": "already-recorded", "table": "Events", "key": event_id}
        raise RecordValidationError("event_id already exists with different content")
    target = store.find("Placements", "idempotency_key", prepared["idempotency_key"])
    if not target:
        raise RecordValidationError("event references an unknown idempotency_key")
    if target[1]["campaign_id"] != prepared["campaign_id"] or target[1]["queue_id"] != prepared["queue_id"]:
        raise RecordValidationError("event campaign_id or queue_id does not match target record")
    event_time = datetime.fromisoformat(prepared["timestamp"].replace("Z", "+00:00"))
    try:
        prior_times = [
            datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            for item in event_records
            if item.get("idempotency_key") == prepared["idempotency_key"]
        ]
    except (KeyError, ValueError) as exc:
        raise RecordValidationError("invalid existing event timestamp") from exc
    if prior_times and event_time < max(prior_times):
        raise RecordValidationError("event timestamp moves backward for this idempotency_key")
    write_with_reconciliation(
        store,
        "Events",
        "event_id",
        event_id,
        prepared,
        lambda: store.append("Events", prepared),
    )
    return {"action": "created", "table": "Events", "key": event_id}


def workbook_audit(store: GoogleSheetsStore, campaign_id: str | None) -> dict[str, object]:
    store.verify_schema()
    return audit_records(
        campaigns=store.records("Campaigns"),
        placements=store.records("Placements"),
        events=store.records("Events"),
        platforms=store.records("Platforms"),
        campaign_id=campaign_id,
    )


def placement_history(
    store: GoogleSheetsStore,
    product_id: str,
    platform_domain: str | None = None,
) -> list[dict[str, str]]:
    store.verify_schema()
    selected = []
    for item in store.records("Placements"):
        if item.get("product_canonical_id") != product_id:
            continue
        if platform_domain and item.get("platform_domain", "").lower() != platform_domain.lower():
            continue
        selected.append(
            {
                key: item.get(key, "")
                for key in ("placement_id", "platform_domain", "status", "public_url", "backlink_url", "anchor_text", "last_checked", "campaign_id")
            }
        )
    return selected


def dry_run(command: str, payload: dict[str, Any] | None = None, title: str | None = None) -> dict[str, object]:
    if command == "init":
        return {
            "dry_run": True,
            "network_access": False,
            "title": title or DEFAULT_TITLE,
            "schema_version": SCHEMA_VERSION,
            "worksheets": {name: headers for name, headers in TABLE_HEADERS.items()},
        }
    if payload is None:
        raise RecordValidationError("dry-run payload is required")
    kind = {
        "upsert-platform": "platform",
        "upsert-campaign": "campaign",
        "upsert-placement": "placement",
        "append-event": "event",
    }[command]
    prepared = prepare_record(kind, payload)
    key_field = {
        "platform": "platform_id", "campaign": "campaign_id",
        "placement": "idempotency_key", "event": "event_id",
    }[kind]
    return {
        "dry_run": True,
        "network_access": False,
        "deduplication_checked": False,
        "command": command,
        "key": prepared[key_field],
        "valid": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config-dir", type=Path, default=default_config_dir())
    commands = result.add_subparsers(dest="command", required=True)

    auth_parser = commands.add_parser("auth")
    auth_parser.add_argument("--client-secret", type=Path, required=True)
    auth_parser.add_argument("--dry-run", action="store_true")

    init_parser = commands.add_parser("init")
    init_parser.add_argument("--title", default=DEFAULT_TITLE)
    init_parser.add_argument("--dry-run", action="store_true")

    commands.add_parser("doctor")
    commands.add_parser("format-workbook")
    commands.add_parser("migrate-schema-v5")
    commands.add_parser("migrate-schema-v6")
    commands.add_parser("migrate-schema-v7")
    commands.add_parser("migrate-schema-v8")

    for name in (
        "upsert-platform", "upsert-campaign", "upsert-placement", "append-event",
    ):
        item = commands.add_parser(name)
        item.add_argument("--input", type=Path, required=True)
        item.add_argument("--dry-run", action="store_true")

    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--campaign-id")
    audit_parser.add_argument("--json", action="store_true")

    export_parser = commands.add_parser("export-md")
    export_parser.add_argument("--campaign-id", required=True)
    export_parser.add_argument("--output", type=Path, required=True)

    history_parser = commands.add_parser("placement-history")
    history_parser.add_argument("--product-id", required=True)
    history_parser.add_argument("--platform-domain")
    history_parser.add_argument("--json", action="store_true")

    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config_dir: Path = args.config_dir
    try:
        if args.command == "auth":
            if args.dry_run:
                client_config = read_json_file(args.client_secret)
                if "installed" not in client_config:
                    raise RecordValidationError("OAuth JSON must contain an installed desktop client")
                output = {
                    "dry_run": True,
                    "network_access": False,
                    "command": "auth",
                    "client_secret": "valid desktop OAuth JSON",
                }
            else:
                output = authenticate(config_dir, args.client_secret)
        elif args.command == "init":
            if args.dry_run:
                output = dry_run("init", title=args.title)
            else:
                with writer_lock(config_dir):
                    if (config_dir / "v1-sheets.json").exists():
                        raise RecordValidationError("workbook is already configured; run doctor")
                    store, config = GoogleSheetsStore.create(build_service(config_dir), args.title)
                    write_private_json(config_dir / "v1-sheets.json", config)
                    store.verify_schema()
                output = config
        elif args.command in {"migrate-schema-v5", "migrate-schema-v6", "migrate-schema-v7", "migrate-schema-v8"}:
            with writer_lock(config_dir):
                output = migrate_schema_v8(config_dir)
        elif args.command == "doctor":
            output = doctor(config_dir)
        elif args.command == "format-workbook":
            with writer_lock(config_dir):
                output = format_workbook(load_store(config_dir))
        elif args.command.startswith("upsert-") or args.command == "append-event":
            payload = read_json_file(args.input)
            if args.dry_run:
                output = dry_run(args.command, payload=payload)
            else:
                with writer_lock(config_dir):
                    store = load_store(config_dir)
                    if args.command == "append-event":
                        output = append_event(store, payload)
                    else:
                        kind = {
                            "upsert-platform": "platform",
                            "upsert-campaign": "campaign",
                            "upsert-placement": "placement",
                        }[args.command]
                        output = upsert(store, kind, payload)
        elif args.command == "audit":
            result = workbook_audit(load_store(config_dir), args.campaign_id)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Valid: {result['valid']}")
                print(f"Total placements: {result['total_placements']}")
                for key, count in result["status_counts"].items():
                    print(f"{key}: {count}")
                for error in result["errors"]:
                    print(f"ERROR: {error}")
            return 0 if result["valid"] else 1
        elif args.command == "export-md":
            store = load_store(config_dir)
            result = workbook_audit(store, args.campaign_id)
            if not result["valid"]:
                raise RecordValidationError("cannot export an invalid campaign")
            campaigns = [
                item for item in store.records("Campaigns") if item["campaign_id"] == args.campaign_id
            ]
            placements = [
                item for item in store.records("Placements") if item["campaign_id"] == args.campaign_id
            ]
            keys = {item["idempotency_key"] for item in placements}
            events = [item for item in store.records("Events") if item["idempotency_key"] in keys]
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                export_campaign_markdown(campaigns[0], placements, events),
                encoding="utf-8",
            )
            output = {"exported": True, "campaign_id": args.campaign_id, "output": str(args.output)}
        elif args.command == "placement-history":
            items = placement_history(load_store(config_dir), args.product_id, args.platform_domain)
            if args.json:
                print(json.dumps({"placements": items, "count": len(items)}, ensure_ascii=False, indent=2))
            else:
                for item in items:
                    print(f"{item['placement_id']} | {item['platform_domain']} | {item['status']} | {item['anchor_text']}")
                if not items:
                    print("No placement history found")
            return 0
        else:  # pragma: no cover
            raise RecordValidationError("unknown command")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except RecordValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Avoid stack traces and credential-bearing API diagnostics.
        print(f"ERROR: {type(exc).__name__}: {safe_error_message(exc)}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("ERROR: operation cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
