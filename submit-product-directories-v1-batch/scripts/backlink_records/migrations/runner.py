"""migrations / runner for Backlink Operations V1."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from backlink_records.credentials import (
    build_service,
    read_json_file,
    require_private_file,
    write_private_json,
)
from backlink_records.formatting import (
    METADATA_KEY,
    _cell_row,
    column_letter,
    readable_format_requests,
)
from . import v4_to_v8, v5_to_v8, v6_to_v8, v7_to_v8
from backlink_records.model import (
    DROPDOWNS,
    LEGACY_SCHEMA_VERSION,
    LEGACY_TABLE_HEADERS,
    PREVIOUS_SCHEMA_VERSION,
    RecordValidationError,
    SCHEMA_V5_TABLE_HEADERS,
    SCHEMA_V6_TABLE_HEADERS,
    SCHEMA_V7_TABLE_HEADERS,
    SCHEMA_V8_TABLE_HEADERS,
    SCHEMA_V9_TABLE_HEADERS,
    SCHEMA_VERSION,
    TABLE_HEADERS,
    display_headers,
    row_values,
    rows_to_records,
)
from backlink_records.operations import audit_records
from backlink_records.sheets_store import GoogleSheetsStore

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
            # Clear the entire retained grid before compacting away blank rows.
            requests.append({"repeatCell": {
                "range": {"sheetId": sheet_id}, "cell": {},
                "fields": "userEnteredValue",
            }})
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
                                "rowCount": max(len(rows), current_properties[tab_name].get("gridProperties", {}).get("rowCount", 1000)),
                                "frozenRowCount": 1,
                            },
                        },
                        "fields": "gridProperties.columnCount,gridProperties.rowCount,gridProperties.frozenRowCount",
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
    """Migrate the configured workbook from schema v4-v9 to the current schema."""
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
    if source_version not in {LEGACY_SCHEMA_VERSION, "5", "6", "7", "8", "9"}:
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
            SCHEMA_V6_TABLE_HEADERS if source_version == "6" else (SCHEMA_V7_TABLE_HEADERS if source_version == "7" else (SCHEMA_V8_TABLE_HEADERS if source_version == "8" else SCHEMA_V9_TABLE_HEADERS))
        )
    )
    store.verify_schema(source_version, source_headers)
    source_records_by_tab: dict[str, list[dict[str, str]]] = {}
    for tab_name, old_headers in source_headers.items():
        values = store._read_values(f"'{tab_name}'!A2:{column_letter(len(old_headers))}")
        source_records = rows_to_records(old_headers, values)
        source_records_by_tab[tab_name] = source_records
    # Preserve an exact private snapshot before any remote mutation.
    from datetime import datetime, timezone
    backup = config_dir / ("schema-" + source_version + "-backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    write_private_json(backup, {"config": config, "records": source_records_by_tab, "metadata": metadata})
    transform = {"4": v4_to_v8, "5": v5_to_v8, "6": v6_to_v8, "7": v7_to_v8, "8": v7_to_v8, "9": v7_to_v8}[source_version]
    migrated_records = transform.migrate_records(source_records_by_tab)
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
    for tab_name, expected in migrated_records.items():
        if store.records(tab_name) != expected:
            raise RecordValidationError(f"migration readback mismatch in {tab_name}")
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


def migrate_schema_v9(config_dir: Path) -> dict[str, object]:
    return migrate_schema_v8(config_dir)


def migrate_schema_v10(config_dir: Path) -> dict[str, object]:
    return migrate_schema_v8(config_dir)
