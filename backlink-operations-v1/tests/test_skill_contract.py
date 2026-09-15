from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO = ROOT.parent


class SkillContractTests(unittest.TestCase):
    def test_routes_directory_article_and_social_lanes(self) -> None:
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
            "Pinterest Pin",
            "social-history",
            "upsert-social-post",
        ):
            self.assertIn(required, skill + routing + (ROOT / "references" / "social-publishing.md").read_text(encoding="utf-8"))
        self.assertIn("three controlled lanes", skill)
        self.assertIn("Profile-link edits", routing)

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

    def test_social_publication_requires_media_utm_ai_and_public_verification(self) -> None:
        social = (ROOT / "references" / "social-publishing.md").read_text(encoding="utf-8")
        for required in (
            "media_reference", "utm_source", "utm_medium", "utm_campaign",
            "AI-modified/generated label", "actual outbound destination", "published_at: unknown",
        ):
            self.assertIn(required, social)


if __name__ == "__main__":
    unittest.main()
