from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillEfficiencyContractTests(unittest.TestCase):
    def test_references_are_progressively_loaded(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not preload every reference", skill)
        self.assertIn("only when the current environment has no already verified browser binding", skill)
        self.assertIn("only for initial setup, migration, exact payload syntax", skill)

    def test_product_history_is_loaded_once_per_batch(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
        recording = (ROOT / "references" / "sheets-recording.md").read_text(encoding="utf-8")
        for text in (skill, workflow, recording):
            self.assertIn("placement-history --product-id PRODUCT_ID --json", text)
            self.assertIn("in-memory", text)
        self.assertIn("exactly once for the product", skill)
        self.assertIn("Do not issue one domain-scoped history query per destination", workflow)


if __name__ == "__main__":
    unittest.main()
