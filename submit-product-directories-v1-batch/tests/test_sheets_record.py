from __future__ import annotations

import importlib.util
import io
import json
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import record_model as MODEL  # noqa: E402
import sheets_record as SHEETS  # noqa: E402

NOW = "2026-09-15 10:00"

def platform(**changes):
    value = {"website_name": "Test", "platform_domain": "example.test",
        "canonical_submission_url": "https://example.test/create", "availability": "available",
        "cost_model": "free", "account_required": "yes", "verification_pattern": "none",
        "reciprocal_requirement": "none", "last_verified_at": NOW, "route": "create",
        "source": "live inspection", "notes": "none", "platform_id": "platform-test"}
    value.update(changes); return value

def campaign(**changes):
    value = {"product_canonical_id": "product-1", "canonical_url": "https://product.test/",
        "campaign_id": "campaign-1", "source_urls": "https://example.test/create",
        "source_list_reference": "source-1", "batch_authorization_reference": "auth-1",
        "execution_shard_size": "10", "policy_version": MODEL.POLICY_VERSION,
        "workflow_version": "Backlink Operations V1"}
    value.update(changes); return value

def placement(**changes):
    value = {"platform_domain": "example.test", "website": "https://example.test/create",
        "status": "published", "public_url": "https://example.test/item/1",
        "backlink_url": "https://product.test/?utm_source=example", "anchor_text": "Product One",
        "exact_result": "public page and backlink verified", "follow_up": "recheck later",
        "verification": "public page checked; outbound link checked", "action_at": NOW,
        "last_checked": NOW, "placement_id": "placement-1", "queue_id": "Q-1",
        "product_canonical_id": "product-1", "campaign_id": "campaign-1",
        "platform_id": "platform-test", "route": "create", "account_alias": "account-1",
        "idempotency_key": "example.test|product-1|account-1|create|placement-1",
        "authorization_reference": "auth-1", "evidence_reference": "evidence-1",
        "execution_method": "browser", "execution_notes": "verified"}
    value.update(changes); return value

def event(**changes):
    value = {"event_id": "event-1", "campaign_id": "campaign-1", "queue_id": "Q-1",
        "idempotency_key": "example.test|product-1|account-1|create|placement-1",
        "timestamp": NOW, "action": "publish", "result": "published",
        "evidence_reference": "evidence-1", "actor_alias": "operator-1"}
    value.update(changes); return value

class MemoryStore:
    def __init__(self): self.tables = {name: [] for name in MODEL.TABLE_HEADERS}; self.write_attempts = 0; self.fail_after_write = False
    def verify_schema(self): return {}
    def records(self, tab): return [dict(v) for v in self.tables[tab]]
    def find(self, tab, field, value):
        for i, item in enumerate(self.tables[tab], 2):
            if item.get(field) == value: return i, dict(item)
        return None
    def append(self, tab, record):
        self.write_attempts += 1; self.tables[tab].append(dict(record))
        if self.fail_after_write: self.fail_after_write = False; raise TimeoutError("lost response")
    def update(self, tab, row, record): self.write_attempts += 1; self.tables[tab][row - 2] = dict(record)

class SchemaTests(unittest.TestCase):
    def test_schema_is_four_readable_sheets(self):
        self.assertEqual(list(MODEL.TABLE_HEADERS), ["Platforms", "Campaigns", "Placements", "Events"])
        self.assertEqual(MODEL.display_headers("Placements")[:7], ["产品编号", "平台域名", "操作页面", "状态", "公开页面", "实际外链", "锚文本"])
        body = SHEETS.workbook_create_body("Backlink Operations")
        self.assertEqual(len(body["sheets"]), 4)
        self.assertTrue(all(s["properties"]["gridProperties"]["frozenRowCount"] == 1 for s in body["sheets"]))

    def test_removed_fields_are_not_current_schema(self):
        removed = {"post_text", "media_reference", "board_or_channel", "ai_disclosure", "utm_source",
            "utm_medium", "utm_campaign", "platform_type", "record_type", "campaign_mode", "outbound_rel",
            "canonical_policy", "content_fingerprint", "title", "agreements_subscriptions"}
        current = {h for headers in MODEL.TABLE_HEADERS.values() for h in headers}
        self.assertFalse(current & removed)

    def test_format_keeps_gridlines_filters_dropdowns_and_status_colors(self):
        props = {n: {"sheetId": i} for i, n in enumerate(MODEL.TABLE_HEADERS, 1)}
        requests = SHEETS.readable_format_requests(props)
        updates = [r["updateSheetProperties"] for r in requests if "updateSheetProperties" in r]
        self.assertTrue(all(not r["properties"]["gridProperties"]["hideGridlines"] for r in updates))
        self.assertIn(("Placements", "status"), SHEETS.fixed_option_colors())
        self.assertEqual(sum("setDataValidation" in r for r in SHEETS.initialization_batch_requests(props)), len(MODEL.DROPDOWNS))

    def test_v6_migration_replaces_three_tabs(self):
        props = {n: {"sheetId": i} for i, n in enumerate(MODEL.SCHEMA_V6_TABLE_HEADERS, 1)}
        records = {n: [] for n in MODEL.TABLE_HEADERS}
        requests = SHEETS.schema_v8_migration_requests(props, records, MODEL.SCHEMA_V6_TABLE_HEADERS)
        self.assertEqual([r["deleteSheet"]["sheetId"] for r in requests if "deleteSheet" in r], [3, 4, 5])
        added = [r["addSheet"]["properties"]["title"] for r in requests if "addSheet" in r]
        self.assertEqual(added, ["Placements"])

    def test_v7_migration_reorders_existing_placement_without_deleting_it(self):
        props = {n: {"sheetId": i} for i, n in enumerate(MODEL.SCHEMA_V7_TABLE_HEADERS, 1)}
        records = {n: [] for n in MODEL.TABLE_HEADERS}
        requests = SHEETS.schema_v8_migration_requests(props, records, MODEL.SCHEMA_V7_TABLE_HEADERS)
        self.assertFalse(any("addSheet" in item or "deleteSheet" in item for item in requests))
        placement_update = next(
            item["updateCells"] for item in requests
            if "updateCells" in item and item["updateCells"]["range"]["sheetId"] == props["Placements"]["sheetId"]
        )
        first_header = placement_update["rows"][0]["values"][0]["userEnteredValue"]["stringValue"]
        self.assertEqual(first_header, "产品编号")

class ValidationTests(unittest.TestCase):
    def test_timestamp_is_compact(self):
        prepared = MODEL.prepare_record("placement", placement(action_at="2026-09-15T10:00:40+08:00", last_checked="2026-09-15T10:01:00+08:00"))
        self.assertEqual(prepared["action_at"], "2026-09-15 10:00")

    def test_anchor_text_is_required_for_published(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "anchor_text"):
            MODEL.validate_placement(placement(anchor_text="not applicable"))
        MODEL.validate_placement(placement(anchor_text="not applicable — image or link card"))

    def test_unknown_result_requires_verification_summary(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "verification summary"):
            MODEL.validate_placement(placement(status="outcome unknown", verification="not checked", public_url="not applicable"))

    def test_privacy_rejects_email_and_secret_query(self):
        with self.assertRaisesRegex(MODEL.RecordValidationError, "raw email"):
            MODEL.validate_placement(placement(execution_notes="person@example.com"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "sensitive query"):
            MODEL.validate_placement(placement(website="https://example.test/create?token=secret"))

    def test_v6_three_records_merge_and_event_keys_follow(self):
        old_campaign = {**campaign(), "campaign_mode": "mixed", "row_version": "1"}
        old_platform = {**platform(), "platform_type": "mixed", "row_version": "1"}
        base = {"platform_domain": "example.test", "website": "https://example.test/create", "status": "published",
            "exact_result": "published", "follow_up": "none", "verification_preflight": "no verification presented",
            "published_at": NOW, "last_checked": NOW, "queue_id": "S-1", "product_canonical_id": "product-1",
            "campaign_id": "campaign-1", "platform_id": "platform-test", "route": "create", "account_alias": "account-1",
            "idempotency_key": "old-social-key", "authorization_reference": "auth-1", "evidence_reference": "evidence-1",
            "public_url": "https://example.test/item/1", "target_url": "https://product.test/", "outbound_href": "https://product.test/",
            "social_post_id": "social-1", "public_page_checked": "checked", "outbound_link_checked": "checked",
            "execution_method": "browser", "execution_notes": "done", "row_version": "2"}
        source = {"Platforms": [old_platform], "Campaigns": [old_campaign], "Submissions": [], "Articles": [], "SocialPosts": [base],
            "Events": [{**event(), "record_type": "social", "idempotency_key": "old-social-key"}]}
        migrated = MODEL.migrate_v6_records(source); row = migrated["Placements"][0]
        self.assertEqual(row["anchor_text"], "not applicable — image or link card")
        self.assertEqual(migrated["Events"][0]["idempotency_key"], row["idempotency_key"])
        self.assertNotIn("record_type", migrated["Events"][0])

class StoreTests(unittest.TestCase):
    def seeded(self):
        store = MemoryStore(); SHEETS.upsert(store, "platform", platform()); SHEETS.upsert(store, "campaign", campaign()); return store

    def test_event_then_placement_write_and_versioned_update(self):
        store = self.seeded(); queued = placement(status="not attempted", public_url="not applicable", backlink_url="https://product.test/",
            anchor_text="not checked", exact_result="not attempted", verification="not checked", action_at="not submitted",
            evidence_reference="not applicable", authorization_reference="auth-1")
        SHEETS.upsert(store, "placement", queued); SHEETS.append_event(store, event(action="publish", result="published"))
        result = SHEETS.upsert(store, "placement", {**placement(), "expected_row_version": "1"})
        self.assertEqual(result["row_version"], "2")
        self.assertEqual(store.tables["Placements"][0]["anchor_text"], "Product One")

    def test_executed_write_needs_prior_event(self):
        store = self.seeded()
        with self.assertRaisesRegex(MODEL.RecordValidationError, "prior linked event"):
            SHEETS.upsert(store, "placement", placement())

    def test_ambiguous_write_is_reconciled_without_duplicate(self):
        store = self.seeded(); queued = placement(status="not attempted", public_url="not applicable", anchor_text="not checked",
            exact_result="not attempted", verification="not checked", action_at="not submitted", evidence_reference="not applicable")
        store.fail_after_write = True; SHEETS.upsert(store, "placement", queued)
        self.assertEqual(len(store.tables["Placements"]), 1)

    def test_audit_and_export_use_only_placements(self):
        store = self.seeded(); queued = MODEL.prepare_record("placement", placement(status="not attempted", public_url="not applicable",
            anchor_text="not checked", exact_result="not attempted", verification="not checked", action_at="not submitted", evidence_reference="not applicable"))
        store.tables["Placements"].append(queued)
        result = SHEETS.workbook_audit(store, "campaign-1")
        self.assertTrue(result["valid"]); self.assertEqual(result["total_placements"], 1)
        text = MODEL.export_campaign_markdown(store.tables["Campaigns"][0], [queued], [])
        self.assertIn("锚文本", text); self.assertNotIn("Content fingerprint", text)

class CliTests(unittest.TestCase):
    def test_dry_run_upsert_placement_never_loads_google(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "record.json"; source.write_text(json.dumps(placement()), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = SHEETS.main(["--config-dir", str(Path(root) / "config"), "upsert-placement", "--input", str(source), "--dry-run"])
            self.assertEqual(code, 0); self.assertTrue(json.loads(out.getvalue())["valid"])

    def test_private_json_permissions(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "private" / "config.json"; SHEETS.write_private_json(target, {"schema_version": "7"})
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

if __name__ == "__main__": unittest.main()
