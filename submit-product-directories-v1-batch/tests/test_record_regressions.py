"""Regression coverage for migration grids, ambiguous writes, and package entry points."""
from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_sheets_record import MODEL, MemoryStore, campaign, event, placement, platform
from backlink_records import cli, credentials, operations
from backlink_records.migrations import runner
from backlink_records.sheets_store import GoogleSheetsStore


def queued(**changes):
    return placement(**{
        "status": "not attempted", "public_url": "not applicable",
        "anchor_text": "not checked", "exact_result": "not attempted",
        "verification": "not checked", "action_at": "not submitted",
        "evidence_reference": "not applicable", **changes,
    })


class GridStore(GoogleSheetsStore):
    """Apply the value/grid subset of Sheets batch requests to physical rows."""
    def __init__(self, version, headers, records):
        self.spreadsheet_id = "test-sheet"
        self.version = version
        self.props = {tab: {"sheetId": i, "title": tab, "gridProperties": {
            "rowCount": 1000, "columnCount": len(fields), "frozenRowCount": 1}}
            for i, (tab, fields) in enumerate(headers.items(), 1)}
        labels = (
            MODEL.HEADER_LABELS if version in {MODEL.SCHEMA_VERSION, "8", "9"} else
            MODEL.SCHEMA_V7_HEADER_LABELS if version == "7" else
            MODEL.LEGACY_HEADER_LABELS
        )
        self.grid = {tab: [[labels[h] for h in fields], [], *[
            MODEL.row_values(fields, row) for row in records.get(tab, [])]]
            for tab, fields in headers.items()}
        self.service = self
        self.requests = []

    def spreadsheets(self): return self
    def batchUpdate(self, *, spreadsheetId, body):
        self.requests = body["requests"]
        return self

    def execute(self):
        for request in self.requests:
            if "addSheet" in request:
                props = copy.deepcopy(request["addSheet"]["properties"])
                self.props[props["title"]] = props
                self.grid[props["title"]] = []
            for kind in ("repeatCell", "updateCells"):
                if kind not in request: continue
                data = request[kind]; area = data["range"]
                tab = next(t for t, p in self.props.items() if p["sheetId"] == area["sheetId"])
                if data["fields"] != "userEnteredValue": continue
                if kind == "repeatCell":
                    self.grid[tab] = []
                else:
                    start = area.get("startRowIndex", 0)
                    rows = [[cell.get("userEnteredValue", {}).get("stringValue", "")
                             for cell in row["values"]] for row in data["rows"]]
                    while len(self.grid[tab]) < start + len(rows): self.grid[tab].append([])
                    self.grid[tab][start:start + len(rows)] = rows
            if "updateSheetProperties" in request:
                props = request["updateSheetProperties"]["properties"]
                target = next(p for p in self.props.values() if p["sheetId"] == props["sheetId"])
                target.setdefault("gridProperties", {}).update(props.get("gridProperties", {}))
            if "deleteSheet" in request:
                tab = next(t for t, p in self.props.items() if p["sheetId"] == request["deleteSheet"]["sheetId"])
                del self.props[tab]; del self.grid[tab]
            if "updateDeveloperMetadata" in request:
                self.version = request["updateDeveloperMetadata"]["developerMetadata"]["metadataValue"]
        return {}

    def metadata(self):
        return {"properties": {"title": "Test"}, "developerMetadata": [
            {"metadataKey": runner.METADATA_KEY, "metadataValue": self.version}],
            "sheets": [{"properties": p} for p in self.props.values()]}

    def _read_values(self, range_name):
        tab, area = range_name.split("!"); tab = tab.strip("'")
        return copy.deepcopy(self.grid[tab][:1] if area.startswith("A1:") else self.grid[tab][1:])


class MigrationRegressionTests(unittest.TestCase):
    def test_each_legacy_version_clears_retained_rows_and_reads_back(self):
        schemas = {"4": MODEL.LEGACY_TABLE_HEADERS, "5": MODEL.SCHEMA_V5_TABLE_HEADERS,
                   "6": MODEL.SCHEMA_V6_TABLE_HEADERS, "7": MODEL.SCHEMA_V7_TABLE_HEADERS, "8": MODEL.SCHEMA_V8_TABLE_HEADERS, "9": MODEL.SCHEMA_V9_TABLE_HEADERS}
        for version, headers in schemas.items():
            with self.subTest(version=version), tempfile.TemporaryDirectory() as root:
                source = {"Platforms": [{**platform(last_verified_at="2026-09-15T10:00:00+08:00"), "row_version": "1"}],
                          "Campaigns": [{**campaign(), "row_version": "1"}]}
                if version in {"7", "8", "9"}:
                    source["Placements"] = [MODEL.prepare_record("placement", queued())]
                    source["Events"] = [MODEL.prepare_record("event", event())]
                store = GridStore(version, headers, source)
                config = Path(root)
                credentials.write_private_json(config / "v1-sheets.json", {
                    "schema_version": version, "spreadsheet_id": store.spreadsheet_id})
                with patch.object(runner, "GoogleSheetsStore", return_value=store), patch.object(runner, "build_service"):
                    result = runner.migrate_schema_v8(config)
                self.assertTrue(result["migrated"])
                self.assertEqual(store.records("Platforms")[0]["cost_detail"], "")
                self.assertEqual(store.records("Platforms")[0]["notes"], "none")
                self.assertEqual(len(list(config.glob("schema-*-backup-*.json"))), 1)
                with patch.object(runner, "GoogleSheetsStore", return_value=store), patch.object(runner, "build_service"):
                    self.assertFalse(runner.migrate_schema_v9(config)["migrated"])
                self.assertEqual(store.version, MODEL.SCHEMA_VERSION)
                self.assertTrue(operations.workbook_audit(store, None)["valid"])
                for tab in MODEL.TABLE_HEADERS:
                    self.assertEqual(len(store.records(tab)), len(source.get(tab, [])))
                self.assertEqual(store.records("Platforms")[0]["last_verified_at"], "2026-09-15 10:00")


class WriteRegressionTests(unittest.TestCase):
    def seeded(self):
        store = MemoryStore()
        operations.upsert(store, "platform", platform())
        operations.upsert(store, "campaign", campaign())
        operations.upsert(store, "placement", queued())
        return store

    def test_update_timeout_before_or_after_apply_and_real_conflicts(self):
        for mode in ("before", "after", "conflict", "moved", "deleted", "always", "duplicate"):
            with self.subTest(mode=mode):
                store = self.seeded(); calls = []
                normal = store.update
                def update(tab, row, record):
                    calls.append(row)
                    if len(calls) == 1 or mode == "always":
                        if mode == "after": normal(tab, row, record)
                        if mode == "conflict": store.tables[tab][0]["execution_notes"] = "another writer"
                        if mode == "moved": store.tables[tab].insert(0, {})
                        if mode == "deleted": store.tables[tab].clear()
                        if mode == "duplicate": store.tables[tab].append(dict(record))
                        raise TimeoutError("transport")
                    normal(tab, row, record)
                store.update = update
                payload = queued(execution_notes="changed", expected_row_version="1")
                if mode in {"before", "after"}:
                    self.assertEqual(operations.upsert(store, "placement", payload)["row_version"], "2")
                    self.assertEqual(len(calls), 2 if mode == "before" else 1)
                    self.assertEqual(len(store.tables["Placements"]), 1)
                else:
                    with self.assertRaises(MODEL.RecordValidationError):
                        operations.upsert(store, "placement", payload)
                    self.assertEqual(len(calls), 2 if mode == "always" else 1)

    def test_live_upsert_updates_physical_row_after_blank(self):
        store = self.seeded()
        grid = object.__new__(GoogleSheetsStore)
        grid._read_values = lambda _: [[], MODEL.row_values(MODEL.PLACEMENT_HEADERS, store.tables["Placements"][0])]
        original_rows = lambda tab: list(enumerate(store.records(tab), 2))
        store.records_with_rows = lambda tab: grid.records_with_rows(tab) if tab == "Placements" else original_rows(tab)
        rows = []
        def update(tab, row, record):
            rows.append(row); store.tables[tab][0] = dict(record)
        store.update = update
        operations.upsert(store, "placement", queued(execution_notes="changed", expected_row_version="1"))
        self.assertEqual(rows, [3])

    def test_embedded_sensitive_urls_rejected_by_write_and_audit(self):
        for text in ("redirected to https://example.test/cb?token=secret",
                     "See https://example.test/ok then https://example.test/cb?%6bey=secret",
                     "[callback](HTTPS://example.test/cb?auth=secret)",
                     "two lines\nhttps://example.test/cb?state="):
            with self.subTest(text=text):
                store = self.seeded()
                with self.assertRaisesRegex(MODEL.RecordValidationError, "sensitive query"):
                    operations.upsert(store, "placement", queued(execution_notes=text, expected_row_version="1"))
                store.tables["Placements"][0]["execution_notes"] = text
                self.assertFalse(operations.workbook_audit(store, None)["valid"])
        MODEL.validate_privacy({"notes": "See https://example.test/?utm_source=test and https://example.test/ok"})

    def test_embedded_url_authority_credentials_rejected_by_write_and_audit(self):
        for text in ("https://user:abc$@example.test/create",
                     "redirected to https://user@example.test/create"):
            with self.subTest(text=text):
                store = self.seeded()
                with self.assertRaisesRegex(
                    MODEL.RecordValidationError,
                    "authority credentials|raw email",
                ):
                    operations.upsert(
                        store, "placement",
                        queued(execution_notes=text, expected_row_version="1"),
                    )
                store.tables["Placements"][0]["execution_notes"] = text
                self.assertFalse(operations.workbook_audit(store, None)["valid"])

    def test_history_matches_domain_variants_and_product(self):
        store = self.seeded()
        for stored, query in (("WWW.Example.Test.", "example.test"), ("bücher.test", "xn--bcher-kva.test")):
            store.tables["Placements"][0]["platform_domain"] = stored
            history = operations.placement_history(store, "product-1", query)
            self.assertEqual(len(history), 1)
            self.assertEqual(list(history[0]), MODEL.PLACEMENT_HEADERS)
            self.assertEqual(history[0]["row_version"], "1")
            self.assertEqual(operations.placement_history(store, "other", query), [])
            self.assertEqual(operations.placement_history(store, "product-1", "unrelated.test"), [])

    def test_history_snapshot_can_resume_an_existing_placement(self):
        store = self.seeded()
        snapshot = operations.placement_history(store, "product-1")[0]
        expected_row_version = snapshot.pop("row_version")
        snapshot.update(
            execution_notes="resumed from batch history",
            expected_row_version=expected_row_version,
        )

        result = operations.upsert(store, "placement", snapshot)

        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["row_version"], "2")
        self.assertEqual(store.tables["Placements"][0]["execution_notes"], "resumed from batch history")


class PackageRegressionTests(unittest.TestCase):
    def test_default_config_root_survives_module_move(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(credentials.default_config_dir(), Path(__file__).resolve().parents[2] / ".backlink-go/runtime")

    def test_legacy_entrypoint_runs_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "scripts/sheets_record.py"
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run([sys.executable, str(script), "init", "--dry-run"], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["network_access"])

    def test_doctor_cli_all_supported_versions(self):
        gmail = type("Gmail", (), {
            "users": lambda self: self,
            "getProfile": lambda self, **kwargs: self,
            "execute": lambda self: {"emailAddress": "redacted@example.test"},
        })()
        for version in ("4", "5", "6", "7", "8", "9", "10"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as root:
                config = Path(root)
                credentials.write_private_json(config / "v1-sheets.json", {"schema_version": version, "spreadsheet_id": "sheet"})
                store = type("Store", (), {"spreadsheet_id": "sheet", "verify_schema": lambda self, *args: {}})()
                out = io.StringIO()
                with patch.object(operations, "load_store", return_value=store), patch.object(
                    operations, "build_gmail_service", return_value=gmail
                ), redirect_stdout(out):
                    code = cli.main(["--config-dir", root, "doctor"])
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out.getvalue())["migration_required"], version != MODEL.SCHEMA_VERSION)
