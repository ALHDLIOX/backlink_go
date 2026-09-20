from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPO = ROOT.parent

class SkillContractTests(unittest.TestCase):
    def combined(self) -> str:
        files = [ROOT / "SKILL.md", ROOT / "references/routing.md", ROOT / "references/article-publishing.md",
                 ROOT / "references/social-publishing.md", REPO / "writer/references/ephemeral-publishing.md"]
        return "\n".join(path.read_text(encoding="utf-8") for path in files)

    def test_routes_all_three_execution_lanes(self):
        text = self.combined()
        for required in ("submit-product-directories-v1-batch", "ephemeral-publish", "Blogger", "Dev.to",
                         "Hashnode", "Substack", "Medium", "Pinterest Pin", "X/LinkedIn"):
            self.assertIn(required, text)

    def test_one_placement_model_and_anchor_contract(self):
        text = self.combined()
        for required in ("Placements", "upsert-placement", "placement-history", "anchor_text",
                         "not applicable — image or link card", "migrate-schema-v9"):
            self.assertIn(required, text)
        self.assertIn("every event resolves to exactly one Placement", text)

    def test_removed_fields_are_explicitly_not_maintained(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for label in ("title", "body", "image", "Board/channel", "AI label", "split UTM fields",
                      "`rel`", "Canonical policy", "content fingerprint", "agreement/subscription"):
            self.assertIn(label, skill)

    def test_only_bundled_cli_writes_sheets(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/sheets_record.py", skill)
        self.assertIn("never use a Sheets connector", skill)

    def test_ephemeral_article_body_is_not_persisted(self):
        text = self.combined()
        self.assertIn("mktemp -d", text)
        self.assertIn("Never write to `writer/output`", text)
        self.assertIn("Delete the transient directory", text)

if __name__ == "__main__": unittest.main()
