from __future__ import annotations

import unittest
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


class BrowserRoutingTests(unittest.TestCase):
    def test_skill_loads_generic_routing_reference(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/browser-control-routing.md", skill)

    def test_authentication_policy_is_reachable_from_both_entrypoints(self) -> None:
        policy = (ROOT / "references" / "authentication.md").resolve()
        for entrypoint in (ROOT / "SKILL.md", ROOT.parent / "backlink-operations-v1" / "SKILL.md"):
            links = re.findall(r"\]\(([^)]+)\)", entrypoint.read_text(encoding="utf-8"))
            targets = {(entrypoint.parent / link).resolve() for link in links}
            self.assertIn(policy, targets)
        self.assertTrue(policy.is_file())

    def test_reference_is_backend_neutral(self) -> None:
        text = (ROOT / "references" / "browser-control-routing.md").read_text(encoding="utf-8")
        for required in (
            "Platform and capability preflight", "Windows", "macOS", "Linux", "Routing order",
            "Browser runtime path", "Desktop UI-control path", "declared target matches the current platform",
            "user handoff",
        ):
            self.assertIn(required, text)
        for forbidden in ("/Users/", "Chrome-bin", "BitBrowser.app", "sole automation backend"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
