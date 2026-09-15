from __future__ import annotations

import importlib.util
import io
import json
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODEL_SPEC = importlib.util.spec_from_file_location("record_model", SCRIPTS / "record_model.py")
MODEL = importlib.util.module_from_spec(MODEL_SPEC)
assert MODEL_SPEC and MODEL_SPEC.loader
sys.modules["record_model"] = MODEL
MODEL_SPEC.loader.exec_module(MODEL)

SHEETS_SPEC = importlib.util.spec_from_file_location("sheets_record", SCRIPTS / "sheets_record.py")
SHEETS = importlib.util.module_from_spec(SHEETS_SPEC)
assert SHEETS_SPEC and SHEETS_SPEC.loader
SHEETS_SPEC.loader.exec_module(SHEETS)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_submission_record_shared", SCRIPTS / "audit_submission_record.py"
)
MARKDOWN_AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
assert AUDIT_SPEC and AUDIT_SPEC.loader
AUDIT_SPEC.loader.exec_module(MARKDOWN_AUDIT)


NOW = "2026-09-15T10:00:00+08:00"


def platform(**changes):
    value = {
        "platform_id": "platform-directory-test",
        "platform_domain": "directory.test",
        "website_name": "Directory Test",
        "canonical_submission_url": "https://directory.test/submit",
        "route": "directory listing",
        "account_required": "yes",
        "verification_pattern": "email verification",
        "cost_model": "free",
        "reciprocal_requirement": "none",
        "availability": "available",
        "last_verified_at": NOW,
        "source": "live inspection",
        "notes": "none",
    }
    value.update(changes)
    return value


def campaign(campaign_id="campaign-001", product_id="product-001", **changes):
    value = {
        "campaign_id": campaign_id,
        "spd_version": "V1 Batch",
        "product_canonical_id": product_id,
        "canonical_url": f"https://{product_id}.test/",
        "source_list_reference": "source-list-001",
        "source_urls": "https://directory.test/submit",
        "batch_authorization_reference": "auth-batch-001",
        "execution_shard_size": "20",
        "policy_version": MODEL.POLICY_VERSION,
    }
    value.update(changes)
    return value


def submission(campaign_id="campaign-001", product_id="product-001", **changes):
    value = {
        "campaign_id": campaign_id,
        "queue_id": "Q-001",
        "platform_id": "platform-directory-test",
        "product_canonical_id": product_id,
        "website": "https://directory.test/submit",
        "platform_domain": "directory.test",
        "route": "directory listing",
        "account_alias": "account-001",
        "idempotency_key": f"directory.test|{product_id}|account-001|directory listing",
        "execution_shard": "shard-001",
        "execution_method": "connected browser",
        "execution_notes": "supported structured browser control",
        "legitimacy_gate": "passed",
        "authorization_reference": "auth-batch-001",
        "status": "submitted",
        "verification_preflight": "no verification presented",
        "fields_entered": "brand, URL, description",
        "fields_omitted": "none",
        "agreements_subscriptions": "terms accepted; subscriptions none",
        "submit_timestamp": NOW,
        "exact_result": "Submission received",
        "evidence_reference": "ev-001",
        "public_listing_url": "not applicable",
        "backend_checked": "not applicable",
        "mailbox_checked": "not applicable",
        "public_page_checked": "not applicable",
        "last_checked": NOW,
        "follow_up": "check approval later",
    }
    value.update(changes)
    return value


def queued_submission(campaign_id="campaign-001", product_id="product-001", **changes):
    queued = {
        "status": "not attempted",
        "verification_preflight": "not checked",
        "fields_entered": "none",
        "fields_omitted": "all",
        "agreements_subscriptions": "none",
        "submit_timestamp": "not submitted",
        "exact_result": "not attempted",
        "evidence_reference": "not applicable",
        "follow_up": "run verification preflight",
    }
    queued.update(changes)
    return submission(campaign_id, product_id, **queued)


def event(campaign_id="campaign-001", product_id="product-001", **changes):
    value = {
        "event_id": "evt-001",
        "campaign_id": campaign_id,
        "queue_id": "Q-001",
        "idempotency_key": f"directory.test|{product_id}|account-001|directory listing",
        "timestamp": NOW,
        "action": "final form submission",
        "result": "submitted",
        "evidence_reference": "ev-001",
        "actor_alias": "operator-001",
    }
    value.update(changes)
    return value


class MemoryStore:
    def __init__(self):
        self.tables = {name: [] for name in MODEL.TABLE_HEADERS}
        self.fail_after_write = False
        self.corrupt_after_write = False
        self.fail_before_write = None
        self.write_attempts = 0

    def verify_schema(self):
        return {}

    def records(self, tab_name):
        return [dict(item) for item in self.tables[tab_name]]

    def find(self, tab_name, key_field, key_value):
        for index, item in enumerate(self.tables[tab_name], start=2):
            if item.get(key_field) == key_value:
                return index, dict(item)
        return None

    def append(self, tab_name, record):
        self.write_attempts += 1
        if self.fail_before_write is not None:
            error = self.fail_before_write
            self.fail_before_write = None
            raise error
        saved = dict(record)
        if self.corrupt_after_write:
            saved[next(iter(saved))] = "corrupted"
        self.tables[tab_name].append(saved)
        if self.fail_after_write:
            self.fail_after_write = False
            raise TimeoutError("response lost")

    def update(self, tab_name, row_number, record):
        self.write_attempts += 1
        if self.fail_before_write is not None:
            error = self.fail_before_write
            self.fail_before_write = None
            raise error
        self.tables[tab_name][row_number - 2] = dict(record)
        if self.fail_after_write:
            self.fail_after_write = False
            raise TimeoutError("response lost")


class WorkbookSchemaTests(unittest.TestCase):
    def test_create_body_has_four_frozen_sheets(self):
        body = SHEETS.workbook_create_body("Backlink Operations")
        self.assertEqual([item["properties"]["title"] for item in body["sheets"]], list(MODEL.TABLE_HEADERS))
        self.assertTrue(all(item["properties"]["gridProperties"]["frozenRowCount"] == 1 for item in body["sheets"]))

    def test_initialization_adds_filter_and_dropdowns(self):
        properties = {name: {"sheetId": index} for index, name in enumerate(MODEL.TABLE_HEADERS, start=1)}
        requests = SHEETS.initialization_batch_requests(properties)
        self.assertEqual(sum("setBasicFilter" in item for item in requests), 4)
        self.assertEqual(sum("setDataValidation" in item for item in requests), len(MODEL.DROPDOWNS))
        self.assertEqual(
            requests[0]["createDeveloperMetadata"]["developerMetadata"]["metadataValue"],
            MODEL.SCHEMA_VERSION,
        )

    def test_readable_format_restores_gridlines_and_uses_readable_headers(self):
        properties = {name: {"sheetId": index} for index, name in enumerate(MODEL.TABLE_HEADERS, start=1)}
        requests = SHEETS.readable_format_requests(properties)
        sheet_updates = [item["updateSheetProperties"] for item in requests if "updateSheetProperties" in item]
        self.assertEqual(len(sheet_updates), 4)
        self.assertTrue(all(not item["properties"]["gridProperties"]["hideGridlines"] for item in sheet_updates))
        self.assertTrue(all(item["properties"]["gridProperties"]["frozenColumnCount"] == 2 for item in sheet_updates))
        self.assertEqual(MODEL.display_headers("Platforms")[0], "平台名称")
        color_rules = [item for item in requests if "addConditionalFormatRule" in item]
        self.assertEqual(
            len(color_rules),
            sum(len(values) for values in SHEETS.fixed_option_colors().values()),
        )

    def test_create_and_verify_with_fake_google_service(self):
        class Request:
            def __init__(self, payload):
                self.payload = payload

            def execute(self):
                return self.payload

        class FakeValues:
            def __init__(self):
                self.headers = {}
                self.batch_body = None

            def batchUpdate(self, **kwargs):
                self.batch_body = kwargs["body"]
                for item in kwargs["body"]["data"]:
                    self.headers[item["range"]] = item["values"]
                return Request({})

            def get(self, **kwargs):
                return Request({"values": self.headers.get(kwargs["range"], [])})

        class FakeSpreadsheets:
            def __init__(self):
                self.values_resource = FakeValues()
                self.sheet_properties = [
                    {
                        "properties": {
                            "sheetId": index,
                            "title": name,
                            "gridProperties": {
                                "columnCount": len(MODEL.TABLE_HEADERS[name]),
                                "frozenRowCount": 1,
                            },
                        }
                    }
                    for index, name in enumerate(MODEL.TABLE_HEADERS, start=1)
                ]
                self.format_requests = None

            def create(self, **kwargs):
                return Request(
                    {
                        "spreadsheetId": "sheet-001",
                        "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet-001",
                        "sheets": self.sheet_properties,
                    }
                )

            def values(self):
                return self.values_resource

            def batchUpdate(self, **kwargs):
                self.format_requests = kwargs["body"]["requests"]
                return Request({})

            def get(self, **kwargs):
                return Request(
                    {
                        "spreadsheetId": "sheet-001",
                        "properties": {"title": "Backlink Operations"},
                        "developerMetadata": [
                            {
                                "metadataKey": SHEETS.METADATA_KEY,
                                "metadataValue": MODEL.SCHEMA_VERSION,
                            }
                        ],
                        "sheets": self.sheet_properties,
                    }
                )

        class FakeService:
            def __init__(self):
                self.resource = FakeSpreadsheets()

            def spreadsheets(self):
                return self.resource

        service = FakeService()
        store, config = SHEETS.GoogleSheetsStore.create(service, "Backlink Operations")
        self.assertEqual(config["spreadsheet_id"], "sheet-001")
        self.assertEqual(service.resource.values_resource.batch_body["valueInputOption"], "RAW")
        for tab_name in MODEL.TABLE_HEADERS:
            last_column = SHEETS.column_letter(len(MODEL.TABLE_HEADERS[tab_name]))
            header_range = f"'{tab_name}'!A1:{last_column}1"
            self.assertEqual(
                service.resource.values_resource.headers[header_range],
                [MODEL.display_headers(tab_name)],
            )
        self.assertEqual(
            len(service.resource.format_requests),
            1 + 8 + len(MODEL.DROPDOWNS) + len(SHEETS.readable_format_requests({
                name: {"sheetId": index}
                for index, name in enumerate(MODEL.TABLE_HEADERS, start=1)
            })),
        )
        store.verify_schema()

    def test_column_letters(self):
        self.assertEqual(SHEETS.column_letter(1), "A")
        self.assertEqual(SHEETS.column_letter(26), "Z")
        self.assertEqual(SHEETS.column_letter(27), "AA")

    def test_api_value_writes_are_raw(self):
        class CaptureService:
            def __init__(self):
                self.calls = []

            def spreadsheets(self):
                return self

            def values(self):
                return self

            def append(self, **kwargs):
                self.calls.append(kwargs)
                return self

            def execute(self):
                return {}

        service = CaptureService()
        store = SHEETS.GoogleSheetsStore(service, "sheet-001")
        store.append("Events", {header: "=unsafe" for header in MODEL.EVENT_HEADERS})
        self.assertEqual(service.calls[0]["valueInputOption"], "RAW")

    def test_private_json_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "private" / "config.json"
            SHEETS.write_private_json(target, {"spreadsheet_id": "sheet-001"})
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_insecure_private_file_is_rejected(self):
        if SHEETS.os.name == "nt":
            self.skipTest("POSIX mode assertion")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "config"
            directory.mkdir(mode=0o700)
            target = directory / "v1-sheets.json"
            target.write_text("{}", encoding="utf-8")
            target.chmod(0o644)
            with self.assertRaisesRegex(MODEL.RecordValidationError, "0600"):
                SHEETS.require_private_file(target)

    def test_expired_token_is_refreshed_and_saved_privately(self):
        class FakeCredentials:
            expired = True
            refresh_token = "refresh-token"
            valid = False

            def refresh(self, _request):
                self.expired = False
                self.valid = True

            def to_json(self):
                return '{"token": "refreshed", "refresh_token": "refresh-token"}'

        with tempfile.TemporaryDirectory() as temporary:
            config_dir = Path(temporary) / "config"
            token_path = config_dir / "google-token.json"
            SHEETS.write_private_json(token_path, {"token": "expired"})
            credentials = FakeCredentials()
            with patch(
                "google.oauth2.credentials.Credentials.from_authorized_user_file",
                return_value=credentials,
            ), patch("google.auth.transport.requests.Request", return_value=object()):
                result = SHEETS.load_credentials(config_dir)
            self.assertIs(result, credentials)
            self.assertEqual(json.loads(token_path.read_text(encoding="utf-8"))["token"], "refreshed")
            self.assertEqual(stat.S_IMODE(token_path.stat().st_mode), 0o600)


class ValidationTests(unittest.TestCase):
    def test_platform_source_and_notes_are_optional(self):
        value = platform()
        value.pop("source")
        value.pop("notes")
        MODEL.validate_platform(value)

    def test_legacy_rows_receive_compact_times(self):
        legacy_campaign = {key: "legacy" for key in MODEL.LEGACY_CAMPAIGN_HEADERS}
        migrated_campaign = MODEL.migrate_legacy_record("Campaigns", legacy_campaign)
        self.assertEqual(migrated_campaign["policy_version"], "legacy")

        legacy_submission = {key: key for key in MODEL.LEGACY_SUBMISSION_HEADERS}
        legacy_submission.update({"submit_timestamp": NOW, "last_checked": NOW})
        migrated_submission = MODEL.migrate_legacy_record("Submissions", legacy_submission)
        self.assertEqual(migrated_submission["execution_method"], "execution_method")
        self.assertEqual(migrated_submission["submit_timestamp"], "2026-09-15 10:00")
        self.assertEqual(migrated_submission["last_checked"], "2026-09-15 10:00")

    def test_schema_v4_migration_request_preserves_tables_and_updates_metadata(self):
        properties = {name: {"sheetId": index} for index, name in enumerate(MODEL.TABLE_HEADERS, start=1)}
        records = {name: [] for name in MODEL.TABLE_HEADERS}
        requests = SHEETS.schema_v4_migration_requests(properties, records)
        sizes = {
            item["updateSheetProperties"]["properties"]["sheetId"]:
            item["updateSheetProperties"]["properties"]["gridProperties"]["columnCount"]
            for item in requests
            if "updateSheetProperties" in item
            and "columnCount" in item["updateSheetProperties"]["properties"].get("gridProperties", {})
        }
        self.assertEqual(sizes[2], len(MODEL.CAMPAIGN_HEADERS))
        self.assertEqual(sizes[3], len(MODEL.SUBMISSION_HEADERS))
        metadata = [item for item in requests if "updateDeveloperMetadata" in item]
        self.assertEqual(metadata[0]["updateDeveloperMetadata"]["developerMetadata"]["metadataValue"], "4")

    def test_timestamps_are_compacted_to_local_minute_precision(self):
        self.assertEqual(MODEL.compact_timestamp(NOW), "2026-09-15 10:00")
        prepared = MODEL.prepare_record("event", event(timestamp="2026-09-15T10:05:39+08:00"))
        self.assertEqual(prepared["timestamp"], "2026-09-15 10:05")

    def test_tracking_parameters_are_removed_but_route_query_remains(self):
        value = MODEL.normalize_url("HTTPS://Directory.Test/submit/?category=ai&utm_source=x#top")
        self.assertEqual(value, "https://directory.test/submit?category=ai")

    def test_raw_email_is_rejected(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "raw email"):
            MODEL.validate_platform(platform(notes="contact person@example.com"))

    def test_sensitive_query_is_rejected(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "sensitive"):
            MODEL.validate_platform(platform(canonical_submission_url="https://directory.test/submit?token=secret"))

    def test_raw_phone_number_is_rejected(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "raw phone"):
            MODEL.validate_platform(platform(notes="call +1 415 555 0123"))

    def test_secret_bearing_free_text_is_rejected(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "secret-bearing value"):
            MODEL.validate_platform(platform(notes="password: should-not-be-here"))

    def test_unknown_outcome_requires_all_checks(self):
        value = submission(
            status="submission outcome unknown",
            backend_checked="checked; none found",
            mailbox_checked="not checked",
            public_page_checked="checked; none found",
        )
        with self.assertRaisesRegex(MODEL.RecordValidationError, "mailbox_checked"):
            MODEL.validate_submission(value)

    def test_published_requires_public_url(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "public_listing_url"):
            MODEL.validate_submission(submission(status="published"))

    def test_published_rejects_non_url_listing_value(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "must be a public URL"):
            MODEL.validate_submission(
                submission(status="published", public_listing_url="visible in account")
            )

    def test_dry_run_validates_without_config(self):
        result = SHEETS.dry_run("upsert-platform", platform())
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["network_access"])
        self.assertFalse(result["deduplication_checked"])

    def test_auth_dry_run_reads_no_google_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = root / "client.json"
            client.write_text('{"installed": {"client_id": "redacted"}}', encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = SHEETS.main(
                    ["--config-dir", str(root / "config"), "auth", "--client-secret", str(client), "--dry-run"]
                )
            self.assertEqual(code, 0, stderr.getvalue())
            result = json.loads(stdout.getvalue())
            self.assertFalse(result["network_access"])
            self.assertFalse((root / "config").exists())

    def test_error_message_redacts_sensitive_query_and_email(self):
        error = Exception(
            "user@example.com https://x.test/cb?code=secret&state=private password=hidden"
        )
        message = SHEETS.safe_error_message(error)
        self.assertNotIn("user@example.com", message)
        self.assertNotIn("secret", message)
        self.assertNotIn("private", message)
        self.assertNotIn("hidden", message)


class StoreTests(unittest.TestCase):
    def populated_store(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform())
        SHEETS.upsert(store, "campaign", campaign())
        return store

    def test_upsert_creates_then_increments_version(self):
        store = self.populated_store()
        first = SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.append_event(store, event())
        second = SHEETS.upsert(
            store,
            "submission",
            submission(follow_up="check tomorrow", expected_row_version="1"),
        )
        self.assertEqual(first["action"], "created")
        self.assertEqual(second["action"], "updated")
        self.assertEqual(store.tables["Submissions"][0]["row_version"], "2")

    def test_exact_upsert_is_unchanged_without_version(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        result = SHEETS.upsert(store, "submission", queued_submission())
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(result["row_version"], "1")

    def test_changed_upsert_requires_current_version(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        with self.assertRaisesRegex(MODEL.RecordValidationError, "expected_row_version"):
            SHEETS.upsert(store, "submission", queued_submission(follow_up="changed"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "row version conflict"):
            SHEETS.upsert(
                store,
                "submission",
                queued_submission(follow_up="changed", expected_row_version="99"),
            )

    def test_pending_submission_cannot_be_reopened(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.append_event(store, event())
        SHEETS.upsert(store, "submission", submission(expected_row_version="1"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "cannot be reopened"):
            SHEETS.upsert(
                store,
                "submission",
                submission(
                    status="form in progress",
                    submit_timestamp="not submitted",
                    exact_result="form opened",
                    evidence_reference="ev-002",
                    expected_row_version="2",
                ),
            )

    def test_executed_state_requires_event_first(self):
        store = self.populated_store()
        with self.assertRaisesRegex(MODEL.RecordValidationError, "prior linked event"):
            SHEETS.upsert(store, "submission", submission())

    def test_same_platform_for_different_products_is_allowed(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.upsert(store, "campaign", campaign("campaign-002", "product-002"))
        second = queued_submission(
            campaign_id="campaign-002",
            product_id="product-002",
            queue_id="Q-002",
            idempotency_key="directory.test|product-002|account-001|directory listing",
        )
        SHEETS.upsert(store, "submission", second)
        self.assertEqual(len(store.tables["Submissions"]), 2)

    def test_same_idempotency_key_cannot_move_to_another_campaign(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.upsert(store, "campaign", campaign("campaign-002", "product-001"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "another campaign"):
            SHEETS.upsert(store, "submission", queued_submission(campaign_id="campaign-002"))

    def test_duplicate_queue_or_normalized_url_is_rejected(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        with self.assertRaisesRegex(MODEL.RecordValidationError, "queue_id"):
            SHEETS.upsert(
                store,
                "submission",
                queued_submission(
                    account_alias="account-002",
                    idempotency_key="directory.test|product-001|account-002|directory listing",
                ),
            )
        with self.assertRaisesRegex(MODEL.RecordValidationError, "normalized website"):
            SHEETS.upsert(
                store,
                "submission",
                queued_submission(
                    queue_id="Q-002",
                    account_alias="account-002",
                    idempotency_key="directory.test|product-001|account-002|directory listing",
                    website="https://directory.test/submit?utm_source=test",
                ),
            )

    def test_invalid_current_row_version_stops_update(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        store.tables["Submissions"][0]["row_version"] = "manual-edit"
        with self.assertRaisesRegex(MODEL.RecordValidationError, "invalid current row_version"):
            SHEETS.upsert(
                store,
                "submission",
                queued_submission(follow_up="changed", expected_row_version="manual-edit"),
            )

    def test_event_is_append_only_and_exact_replay_is_idempotent(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        first = SHEETS.append_event(store, event())
        replay = SHEETS.append_event(store, event())
        self.assertEqual(first["action"], "created")
        self.assertEqual(replay["action"], "already-recorded")
        with self.assertRaisesRegex(MODEL.RecordValidationError, "different content"):
            SHEETS.append_event(store, event(result="conflict"))

    def test_ambiguous_append_reconciles_exact_row(self):
        store = self.populated_store()
        store.fail_after_write = True
        result = SHEETS.upsert(store, "submission", queued_submission())
        self.assertEqual(result["action"], "created")
        self.assertEqual(len(store.tables["Submissions"]), 1)

    def test_readback_conflict_stops(self):
        store = self.populated_store()
        store.corrupt_after_write = True
        with self.assertRaisesRegex(MODEL.RecordValidationError, "conflicting row"):
            SHEETS.upsert(store, "submission", queued_submission())

    def test_non_retryable_api_error_is_not_replayed(self):
        class Response:
            status = 400

        class ApiError(Exception):
            resp = Response()

        store = self.populated_store()
        baseline_attempts = store.write_attempts
        store.fail_before_write = ApiError("bad request")
        with self.assertRaisesRegex(MODEL.RecordValidationError, "non-retryable"):
            SHEETS.upsert(store, "submission", queued_submission())
        self.assertEqual(store.write_attempts - baseline_attempts, 1)

    def test_retryable_503_is_retried_once_after_lookup(self):
        class Response:
            status = 503

        class ApiError(Exception):
            resp = Response()

        store = self.populated_store()
        baseline_attempts = store.write_attempts
        store.fail_before_write = ApiError("unavailable")
        SHEETS.upsert(store, "submission", queued_submission())
        self.assertEqual(store.write_attempts - baseline_attempts, 2)

    def test_audit_and_export(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.append_event(store, event())
        SHEETS.upsert(store, "submission", submission(expected_row_version="1"))
        result = SHEETS.workbook_audit(store, "campaign-001")
        self.assertTrue(result["valid"], result["errors"])
        markdown = MODEL.export_campaign_markdown(
            store.tables["Campaigns"][0], store.tables["Submissions"], store.tables["Events"]
        )
        self.assertIn("## Q-001 — directory.test", markdown)
        self.assertIn("event_id=evt-001", markdown)
        markdown_result = MARKDOWN_AUDIT.audit(markdown)
        self.assertTrue(markdown_result["valid"], markdown_result["errors"])

    def test_executed_state_without_event_fails_audit(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        store.tables["Submissions"][0].update(submission())
        store.tables["Submissions"][0]["row_version"] = "2"
        result = SHEETS.workbook_audit(store, "campaign-001")
        self.assertFalse(result["valid"])
        self.assertTrue(any("requires an event" in item for item in result["errors"]))

    def test_campaign_audit_includes_dangling_events(self):
        store = self.populated_store()
        store.tables["Events"].append(event(idempotency_key="missing|key", event_id="evt-dangling"))
        result = SHEETS.workbook_audit(store, "campaign-001")
        self.assertTrue(any("unknown idempotency_key" in item for item in result["errors"]))

    def test_full_audit_includes_submission_with_unknown_campaign(self):
        store = self.populated_store()
        orphan = MODEL.prepare_record(
            "submission",
            queued_submission(campaign_id="campaign-missing"),
        )
        store.tables["Submissions"].append(orphan)
        result = SHEETS.workbook_audit(store, None)
        self.assertTrue(any("unknown campaign_id" in item for item in result["errors"]))

    def test_event_timestamp_must_not_move_backward(self):
        store = self.populated_store()
        SHEETS.upsert(store, "submission", queued_submission())
        SHEETS.append_event(store, event(timestamp="2026-09-15T10:06:00+08:00"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "timestamp moves backward"):
            SHEETS.append_event(
                store,
                event(event_id="evt-002", timestamp="2026-09-15T10:05:00+08:00"),
            )

    def test_schema_drift_stops_before_write(self):
        store = MemoryStore()

        def fail_schema():
            raise MODEL.RecordValidationError("schema drift")

        store.verify_schema = fail_schema
        with self.assertRaisesRegex(MODEL.RecordValidationError, "schema drift"):
            SHEETS.upsert(store, "platform", platform())
        self.assertEqual(store.write_attempts, 0)


class LockTests(unittest.TestCase):
    def test_lock_descriptor_is_closed_exactly_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.object(SHEETS.os, "open", return_value=37),
                patch.object(SHEETS.os, "write"),
                patch.object(SHEETS.os, "close") as close,
            ):
                with SHEETS.writer_lock(Path(temporary)):
                    pass
            close.assert_called_once_with(37)

    def test_lock_rejects_second_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_dir = Path(temporary)
            with SHEETS.writer_lock(config_dir):
                with self.assertRaisesRegex(MODEL.RecordValidationError, "writer is active"):
                    with SHEETS.writer_lock(config_dir):
                        pass


if __name__ == "__main__":
    unittest.main()
