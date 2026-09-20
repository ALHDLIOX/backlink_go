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
        resume_payload = {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "2"}
        with self.assertRaisesRegex(MODEL.RecordValidationError, "new resume"):
            SHEETS.upsert(store, "placement", resume_payload)
        SHEETS.append_event(store, event(event_id="generic-submit", action="submit", result="badge verified; submitted"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "new resume"):
            SHEETS.upsert(store, "placement", resume_payload)
        SHEETS.append_event(store, event(event_id="event-2", action="resume after badge verification", result="badge verified; submitted"))
        resumed = SHEETS.upsert(store, "placement", resume_payload)
        self.assertEqual(resumed["row_version"], "3")
        self.assertEqual(len(store.tables["Placements"]), 1)
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.append_event(store, event(event_id="publish-after-resume", action="publish", result="published", evidence_reference="public-evidence"))
        SHEETS.upsert(store, "placement", {**placement(evidence_reference="public-evidence"), "expected_row_version": "3"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.append_event(store, event(event_id="removed-after-publication", action="verify removal", result="removed"))
        SHEETS.upsert(store, "placement", {**placement(status="removed"), "expected_row_version": "4"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        store.tables["Events"] = [event for event in store.tables["Events"] if event["event_id"] != "event-2"]
        audit = SHEETS.workbook_audit(store, None)
        self.assertFalse(audit["valid"])
        self.assertTrue(any("new resume" in error for error in audit["errors"]))


    def test_negated_badge_outcomes_do_not_count_as_success(self):
        for bad_result in ("badge verified; not submitted", "badge verified; unpublished"):
            with self.subTest(result=bad_result):
                store = MemoryStore()
                SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
                SHEETS.upsert(store, "campaign", campaign())
                SHEETS.upsert(store, "placement", self.waiting(status="not attempted", exact_result="not attempted"))
                SHEETS.append_event(store, event(action="defer for badge", result="waiting badge"))
                SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "1"})
                SHEETS.append_event(store, event(event_id="bad-resume", action="resume after badge verification", result=bad_result))
                resume = {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "2"}
                with self.assertRaisesRegex(MODEL.RecordValidationError, "exact submitted token"):
                    SHEETS.upsert(store, "placement", resume)
                store.tables["Placements"][0] = MODEL.prepare_record("placement", placement(status="submitted", public_url="not applicable", backlink_url="not checked"))
                audit = SHEETS.workbook_audit(store, None)
                self.assertFalse(audit["valid"])
                self.assertTrue(any("positive submission outcome token" in error for error in audit["errors"]))

    def test_generic_defer_event_is_not_badge_history(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform())
        SHEETS.upsert(store, "campaign", campaign())
        SHEETS.upsert(store, "placement", self.waiting(status="not attempted", exact_result="not attempted"))
        SHEETS.append_event(store, event(action="defer", result="waiting on editor input"))
        SHEETS.upsert(store, "placement", {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "1"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])

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
        for index, bad_result in enumerate(("submission confirmed", "not no submission confirmed", "no submission confirmed; submission confirmed")):
            correction_id = f"bad-correction-{index}"
            SHEETS.append_event(store, event(event_id=correction_id, action="correct unsubmitted status", result=bad_result))
            with self.assertRaisesRegex(MODEL.RecordValidationError, "exactly no submission confirmed"):
                SHEETS.upsert(store, "placement", payload, correction_event_id=correction_id)
            self.assertEqual(store.tables["Placements"][0]["status"], "awaiting approval")
        SHEETS.append_event(store, event(event_id="correction-1", action="correct unsubmitted status", result="no submission confirmed"))
        result = SHEETS.upsert(store, "placement", payload, correction_event_id="correction-1")
        self.assertEqual(result["row_version"], "3")
        self.assertEqual(store.tables["Placements"][0]["status"], "waiting badge")
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])

        resume = {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "3"}
        with self.assertRaisesRegex(MODEL.RecordValidationError, "new resume"):
            SHEETS.upsert(store, "placement", resume)
        SHEETS.append_event(store, event(event_id="corrected-resume", action="resume after badge verification", result="badge verified; submitted"))
        SHEETS.upsert(store, "placement", resume)
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.append_event(store, event(event_id="corrected-publish", action="publish", result="published"))
        SHEETS.upsert(store, "placement", {**placement(), "expected_row_version": "4"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.upsert(store, "placement", {**placement(status="removed"), "expected_row_version": "5"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        store.tables["Events"] = [item for item in store.tables["Events"] if item["event_id"] != "corrected-resume"]
        self.assertFalse(SHEETS.workbook_audit(store, None)["valid"])

    def test_correction_preserves_noncanonical_existing_urls(self):
        for field in ("public_url", "backlink_url"):
            for url in ("HTTPS://example.test/item", "  https://example.test/item  "):
                with self.subTest(field=field, url=url):
                    store = MemoryStore()
                    SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
                    SHEETS.upsert(store, "campaign", campaign())
                    SHEETS.upsert(store, "placement", self.waiting(status="not attempted"))
                    SHEETS.append_event(store, event())
                    pending = placement(status="awaiting approval", **{field: url})
                    SHEETS.upsert(store, "placement", {**pending, "expected_row_version": "1"})
                    SHEETS.append_event(store, event(event_id="correction", action="correct unsubmitted status", result="no submission confirmed"))
                    with self.assertRaisesRegex(MODEL.RecordValidationError, "cannot clear existing"):
                        SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "2"}, correction_event_id="correction")
                    self.assertEqual(store.tables["Placements"][0][field], url)

    def test_correction_cannot_reopen_published_record(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
        SHEETS.upsert(store, "campaign", campaign())
        SHEETS.upsert(store, "placement", self.waiting(status="not attempted"))
        SHEETS.append_event(store, event())
        SHEETS.upsert(store, "placement", {**placement(), "expected_row_version": "1"})
        with self.assertRaises(MODEL.RecordValidationError):
            SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "2"}, correction_event_id="event-1")

    def test_discovered_badge_pauses_then_resumes_form_after_confirmation(self):
        store = MemoryStore()
        SHEETS.upsert(store, "platform", platform(reciprocal_requirement="required"))
        SHEETS.upsert(store, "campaign", campaign())
        SHEETS.upsert(store, "placement", self.waiting(status="not attempted"))
        SHEETS.append_event(store, event(action="login", result="logged in"))
        with self.assertRaisesRegex(MODEL.RecordValidationError, "badge queue event"):
            SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "1"})
        SHEETS.append_event(store, event(event_id="pause", action="pause for badge", result="waiting badge"))
        SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "1"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.append_event(store, event(event_id="unconfirmed", action="resume after badge verification", result="badge verified; form resumed"))
        resume = {**self.waiting(status="in progress", exact_result="Form resumed; not submitted"), "expected_row_version": "2"}
        with self.assertRaisesRegex(MODEL.RecordValidationError, "user confirmed"):
            SHEETS.upsert(store, "placement", resume)
        SHEETS.append_event(store, event(event_id="confirmed", action="resume after badge verification", result="user confirmed badge deployment; badge verified; form resumed"))
        SHEETS.upsert(store, "placement", resume)
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        SHEETS.upsert(store, "placement", {**self.waiting(status="draft saved"), "expected_row_version": "3"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        with self.assertRaisesRegex(MODEL.RecordValidationError, "later submission outcome"):
            SHEETS.upsert(store, "placement", {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "4"})
        with self.assertRaisesRegex(MODEL.RecordValidationError, "fresh badge pause"):
            SHEETS.upsert(store, "placement", {**self.waiting(), "expected_row_version": "4"})
        SHEETS.append_event(store, event(event_id="submitted", action="submit", result="submitted"))
        SHEETS.upsert(store, "placement", {**placement(status="submitted", public_url="not applicable", backlink_url="not checked"), "expected_row_version": "4"})
        self.assertTrue(SHEETS.workbook_audit(store, None)["valid"])
        store.tables["Placements"][0]["status"] = "waiting badge"
        store.tables["Placements"][0].update(self.waiting())
        store.tables["Events"] = [item for item in store.tables["Events"] if item["event_id"] != "pause"]
        self.assertFalse(SHEETS.workbook_audit(store, None)["valid"])
