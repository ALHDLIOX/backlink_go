from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO = ROOT.parent


class SkillContractTests(unittest.TestCase):
    def test_routes_supported_lanes_and_excludes_short_social(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        routing = (ROOT / "references" / "routing.md").read_text(encoding="utf-8")
        for required in (
            "submit-product-directories-v1-batch",
            "ephemeral-publish",
            "Blogger",
            "Dev.to",
            "Hashnode",
            "Substack",
            "Medium",
            "Pinterest pins",
        ):
            self.assertIn(required, skill + routing)
        self.assertIn("unsupported short-social targets", skill)
        self.assertIn("Do not create Campaign, Submission, Article, or Event rows", routing)

    def test_only_bundled_cli_is_authoritative_sheet_writer(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../submit-product-directories-v1-batch/scripts/sheets_record.py", skill)
        self.assertIn("Never use a Sheets connector", skill)
        self.assertNotIn("Google Sheets MCP", skill)

    def test_ephemeral_contract_forbids_durable_body_and_output(self) -> None:
        article = (ROOT / "references" / "article-publishing.md").read_text(encoding="utf-8")
        writer_mode = (REPO / "writer" / "references" / "ephemeral-publishing.md").read_text(
            encoding="utf-8"
        )
        combined = article + writer_mode
        for required in ("mktemp -d", "Never write to `writer/output", "delete the transient"):
            self.assertIn(required, combined)
        self.assertIn("must never contain article body", combined)

    def test_publish_requires_public_link_verification(self) -> None:
        article = (ROOT / "references" / "article-publishing.md").read_text(encoding="utf-8")
        for required in ("actual anchor text", "actual outbound `href`", "actual `rel`"):
            self.assertIn(required, article)
        self.assertIn("Do not click Publish again", article)

    def test_batch_authorization_actions_are_independent(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for action in ("`write`", "`draft`", "`publish`", "`upload`"):
            self.assertIn(action, skill)
        self.assertIn("A permission for one action does not imply another", skill)


if __name__ == "__main__":
    unittest.main()
