"""formatting for Backlink Operations V1."""
from __future__ import annotations
from typing import Any
from backlink_records.model import (
    ALLOWED_STATUSES,
    DROPDOWNS,
    RecordValidationError,
    SCHEMA_VERSION,
    TABLE_HEADERS,
    display_headers,
)

DEFAULT_TITLE = "Backlink Operations"


METADATA_KEY = "spd_v1_schema_version"


CENTERED_BODY_COLUMNS = {
    "Platforms": ("website_name", "platform_domain", "row_version"),
    "Campaigns": ("product_canonical_id", "execution_shard_size", "row_version"),
    "Placements": ("product_canonical_id", "platform_domain", "row_version"),
}


COLOR_GREEN = ({"red": 0.91, "green": 0.97, "blue": 0.93}, {"red": 0.082, "green": 0.502, "blue": 0.239})


COLOR_BLUE = ({"red": 0.92, "green": 0.95, "blue": 0.99}, {"red": 0.145, "green": 0.388, "blue": 0.922})


COLOR_YELLOW = ({"red": 1.0, "green": 0.97, "blue": 0.87}, {"red": 0.851, "green": 0.467, "blue": 0.024})


COLOR_RED = ({"red": 0.99, "green": 0.92, "blue": 0.93}, {"red": 0.863, "green": 0.149, "blue": 0.149})


COLOR_GRAY = ({"red": 0.95, "green": 0.96, "blue": 0.97}, {"red": 0.420, "green": 0.447, "blue": 0.502})


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
                                "backgroundColor": {"red": 1.0, "green": 0.953, "blue": 0.839},
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {"red": 0.247, "green": 0.204, "blue": 0.141},
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                            }
                        },
                        "fields": (
                            "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,"
                            "verticalAlignment,wrapStrategy)"
                        ),
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
        for header in CENTERED_BODY_COLUMNS.get(tab_name, ()):
            column_index = headers.index(header)
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": column_index,
                            "endColumnIndex": column_index + 1,
                        },
                        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat.horizontalAlignment",
                    }
                }
            )
    for (tab_name, header), values in fixed_option_colors().items():
        sheet_id = properties[tab_name]["sheetId"]
        column_index = TABLE_HEADERS[tab_name].index(header)
        for value, (_, foreground) in values.items():
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
