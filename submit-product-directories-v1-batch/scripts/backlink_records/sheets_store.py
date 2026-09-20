"""sheets_store for Backlink Operations V1."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from backlink_records.credentials import build_service, read_json_file, require_private_file
from backlink_records.formatting import (
    METADATA_KEY,
    column_letter,
    initialization_batch_requests,
    readable_format_requests,
    workbook_create_body,
)
from backlink_records.model import (
    HEADER_LABELS,
    LEGACY_HEADER_LABELS,
    RecordValidationError,
    SCHEMA_VERSION,
    SCHEMA_V7_HEADER_LABELS,
    TABLE_HEADERS,
    display_headers,
    row_values,
)

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
            labels = (
                HEADER_LABELS if schema_version in {SCHEMA_VERSION, "8"} else
                SCHEMA_V7_HEADER_LABELS if schema_version == "7" else
                LEGACY_HEADER_LABELS
            )
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


def records_with_rows(store: object, tab_name: str) -> list[tuple[int, dict[str, str]]]:
    method = getattr(store, "records_with_rows", None)
    if callable(method):
        return method(tab_name)
    return list(enumerate(store.records(tab_name), start=2))
