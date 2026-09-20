"""Pricing migration and deferred submission invariants."""
import unittest
from test_sheets_record import MODEL, SHEETS, MemoryStore, campaign, event, placement, platform


class BadgeQueueTests(unittest.TestCase):
    def waiting(self, **changes):
        return placement(**{
            "status": "waiting badge", "action_at": "not submitted",
            "public_url": "not applicable", "backlink_url": "not checked",
            "exact_result": "Badge Launch selected; not submitted",
            "follow_up": "Install badge in later batch; https://example.test/badge",
            **changes,
        })

    def test_cost_detail_preserves_options_in_adjacent_column(self):
        detail = "Free Launch $0 wait 100 days; Badge Launch $0 badge required; Premium Launch $9.9"
        record = MODEL.prepare_record("platform", platform(cost_detail=detail))
        self.assertEqual(record["cost_detail"], detail)
        index = MODEL.PLATFORM_HEADERS.index("cost_model")
        self.assertEqual(MODEL.PLATFORM_HEADERS[index + 1], "reciprocal_requirement")
        self.assertEqual(MODEL.PLATFORM_HEADERS[index + 2], "cost_detail")
        self.assertEqual(MODEL.display_headers("Platforms")[index + 1], "Reciprocal Requirement")
        self.assertEqual(MODEL.display_headers("Platforms")[index + 2], "Cost Detail")
        with self.assertRaises(MODEL.RecordValidationError):
            MODEL.prepare_record("platform", platform(cost_detail="https://example.test/?token=secret"))

    def test_waiting_badge_rejects_submission_or_public_result(self):
        MODEL.prepare_record("placement", self.waiting())
        for changes in ({"action_at": "2026-09-20 12:00"},
                        {"public_url": "https://example.test/item"},
                        {"backlink_url": "https://product.test"},
                        {"follow_up": "not applicable"}):
            with self.subTest(changes=changes), self.assertRaises(MODEL.RecordValidationError):
                MODEL.prepare_record("placement", self.waiting(**changes))

    def test_waiting_queue_requires_reciprocal_and_event_then_resumes_same_row(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform())
        SHEETS.upsert(store, "campaign", campaign())
        queued = self.waiting(status="not attempted", exact_result="not attempted")
        SHEETS.upsert(store, "placement", queued)
        update = {**self.waiting(), "expected_row_version": "1"}
        with self.assertRaisesRegex(MODEL.RecordValidationError, "reciprocal_requirement"):
            SHEETS.upsert(store, "placement", update)
        SHEETS.upsert(store, "platform", {**platform(reciprocal_requirement="required"), "expected_row_version": "1"})
        with self.assertRaisesRegex(MODEL.RecordValidationError, "event"):
            SHEETS.upsert(store, "placement", update)
        SHEETS.append_event(store, event(action="defer", result="waiting badge"))
        result = SHEETS.upsert(store, "placement", update)
        self.assertEqual(store.tables["Placements"][0]["status"], "waiting badge")
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        store.tables["Platforms"][0]["reciprocal_requirement"] = "optional"
        self.assertFalse(SHEETS.workbook_audit(store, None)["valid"])
        store.tables["Platforms"][0]["reciprocal_requirement"] = "required"
        SHEETS.append_event(store, event(event_id="event-2", action="submit", result="badge verified; submitted"))
        resumed = SHEETS.upsert(store, "placement", {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "2"})
        self.assertEqual(resumed["row_version"], "3")
        self.assertEqual(len(store.tables["Placements"]), 1)

    def test_historical_pending_correction_requires_explicit_linked_event(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
        SHEETS.upsert(store, "campaign", campaign())
        SHEETS.upsert(store, "placement", self.waiting(status="not attempted"))
        SHEETS.append_event(store, event())
        SHEETS.upsert(store, "placement", {**self.waiting(status="awaiting approval", action_at="2026-09-20 12:00"), "expected_row_version": "1"})
        payload = {**self.waiting(), "expected_row_version": "2"}
        with self.assertRaises(MODEL.RecordValidationError):
            SHEETS.upsert(store, "placement", payload)
        with self.assertRaises(MODEL.RecordValidationError):
            SHEETS.upsert(store, "placement", payload, correction_event_id="event-1")
        SHEETS.append_event(store, event(event_id="correction-1", action="correct unsubmitted status", result="Old status was incorrect; badge selection only, no submission"))
        result = SHEETS.upsert(store, "placement", payload, correction_event_id="correction-1")
        self.assertEqual(result["row_version"], "3")
        self.assertEqual(store.tables["Placements"][0]["status"], "waiting badge")
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])

    def test_correction_cannot_reopen_published_record(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
        SHEETS.upsert(store, "campaign", campaign())
        SHEETS.upsert(store, "placement", self.waiting(status="not attempted"))
        SHEETS.append_event(store, event())
        SHEETS.upsert(store, "placement", {**placement(), "expected_row_version": "1"})
        with self.assertRaises(MODEL.RecordValidationError):
            SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "2"}, correction_event_id="event-1")
