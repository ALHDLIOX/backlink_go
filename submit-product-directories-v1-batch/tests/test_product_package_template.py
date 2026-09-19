from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1]
REPO_ROOT = SKILL_ROOT.parent
TEMPLATE_ROOT = REPO_ROOT / "products" / "template"


class ProductPackageTemplateTests(unittest.TestCase):
    def test_canonical_template_contains_every_documented_text_file(self) -> None:
        expected = {
            "AGENT-INTAKE.md",
            "PACKAGE-GUIDE.md",
            "README.md",
            "product-profile.md",
            "brand-rules.md",
            "asset-manifest.md",
            "images/README.md",
            "screenshots/README.md",
            "source-lists/README.md",
            "source-lists/source-list-template.md",
        }
        actual = {
            str(path.relative_to(TEMPLATE_ROOT))
            for path in TEMPLATE_ROOT.rglob("*.md")
        }
        self.assertEqual(expected, actual)

    def test_guide_defines_structure_privacy_and_record_boundaries(self) -> None:
        guide = (TEMPLATE_ROOT / "PACKAGE-GUIDE.md").read_text(encoding="utf-8")
        for required in (
            "products/<product-id>/",
            "Required evidence standard",
            "Privacy and record boundaries",
            "Google Sheets remains the only writable source of truth",
            ".backlink-go/private/product-aliases.json",
            "Never commit or record raw email addresses",
        ):
            self.assertIn(required, guide)

    def test_templates_cover_product_copy_assets_and_bounded_authorization(self) -> None:
        profile = (TEMPLATE_ROOT / "product-profile.md").read_text(encoding="utf-8")
        brand = (TEMPLATE_ROOT / "brand-rules.md").read_text(encoding="utf-8")
        assets = (TEMPLATE_ROOT / "asset-manifest.md").read_text(encoding="utf-8")
        source = (
            TEMPLATE_ROOT / "source-lists" / "source-list-template.md"
        ).read_text(encoding="utf-8")

        for required in ("{{PRODUCT_ID}}", "Tagline", "Short description", "Full description", "Do not select"):
            self.assertIn(required, profile)
        for required in ("Directory lane", "Editorial and social lanes", "UTM policy", "Do not claim"):
            self.assertIn(required, brand)
        for required in ("Source and rights", "Public upload", "Derived assets", "Privacy and authenticity checks"):
            self.assertIn(required, assets)
        for required in (
            "Account alias",
            "Authorization reference",
            "Approver alias",
            "Approved at",
            "Authorization expires",
            "Not authorized",
            "Payment or credit consumption",
        ):
            self.assertIn(required, source)

    def test_package_reference_points_to_the_canonical_template(self) -> None:
        reference = (
            SKILL_ROOT / "references" / "product-packages.md"
        ).read_text(encoding="utf-8")
        self.assertIn("../../products/template/", reference)
        self.assertIn("AGENT-INTAKE.md", reference)
        self.assertIn("PACKAGE-GUIDE.md", reference)

    def test_agent_intake_can_drive_package_generation_without_external_actions(self) -> None:
        intake = (TEMPLATE_ROOT / "AGENT-INTAKE.md").read_text(encoding="utf-8")
        for required in (
            "Agent execution contract",
            "Product intake form",
            "products/<product-id>/",
            "Do not invent company",
            "Do not submit forms",
            "rg -n",
            "./scripts/check-all.sh",
            "Optional campaign and source-list authorization",
        ):
            self.assertIn(required, intake)


if __name__ == "__main__":
    unittest.main()
