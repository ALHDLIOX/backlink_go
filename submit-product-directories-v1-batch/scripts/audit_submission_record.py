#!/usr/bin/env python3
"""Audit an SPD V1 Batch Markdown campaign record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from record_model import (  # noqa: E402
    RecordValidationError,
    UNRESOLVED_VERIFICATION,
    normalize_url,
    validate_privacy,
    validate_submission_state,
)

REQUIRED_CONTROLS = {
    "SPD version",
    "Campaign ID",
    "Product canonical ID",
    "Canonical URL",
    "Source-list reference",
    "Batch authorization reference",
    "Execution-shard size",
    "Maximum active tabs",
    "Host platform",
    "UI environment",
    "Available control capabilities",
    "Browser-routing policy",
    "Credential policy",
    "Evidence policy",
    "Duplicate policy",
    "Ambiguous-outcome policy",
    "Ranking manipulation prohibited",
}

REQUIRED_SITE_FIELDS = {
    "Queue ID",
    "Website",
    "Platform domain",
    "Route",
    "Account alias",
    "Idempotency key",
    "Execution shard",
    "Platform capability result",
    "Requested browser constraint",
    "Selected browser surface",
    "Execution backend/session alias",
    "Backend selection reason",
    "Legitimacy gate",
    "Authorization reference",
    "Status",
    "Verification preflight",
    "Fields entered",
    "Fields omitted",
    "Agreements/subscriptions",
    "Submit timestamp",
    "Exact result",
    "Evidence reference",
    "Last checked",
    "Follow-up",
}

def clean(value: str) -> str:
    return re.sub(r"[*`]", "", value).strip()


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in re.finditer(r"^- ([^:\n]+):\s*(.*)$", body, re.MULTILINE):
        fields[clean(match.group(1))] = clean(match.group(2))
    return fields


def parse_record(text: str) -> tuple[dict[str, str], list[dict[str, object]]]:
    controls_match = re.search(
        r"^## Campaign controls\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE
    )
    controls = parse_fields(controls_match.group(1)) if controls_match else {}

    sites: list[dict[str, object]] = []
    headings = list(re.finditer(r"^## (?!Campaign controls$|Source list$)(.+)$", text, re.MULTILINE))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end]
        fields = parse_fields(body)
        sites.append({"name": heading.group(1).strip(), "fields": fields})
    return controls, sites


def audit(text: str) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    controls, sites = parse_record(text)

    missing_controls = sorted(REQUIRED_CONTROLS - controls.keys())
    if missing_controls:
        errors.append("missing campaign controls: " + ", ".join(missing_controls))
    if controls.get("SPD version") != "V1 Batch":
        errors.append("SPD version must be V1 Batch")
    if controls.get("Ranking manipulation prohibited", "").lower() != "yes":
        errors.append("Ranking manipulation prohibited must be yes")
    for numeric in ("Execution-shard size", "Maximum active tabs"):
        value = controls.get(numeric, "")
        if not value.isdigit() or int(value) < 1:
            errors.append(f"{numeric} must be a positive integer")
    if controls.get("Host platform", "").lower() not in {"windows", "macos", "linux", "other"}:
        errors.append("Host platform must be windows, macos, linux, or other")
    if controls.get("UI environment", "").lower() not in {"desktop", "remote desktop", "headless", "unknown"}:
        errors.append("UI environment must be desktop, remote desktop, headless, or unknown")
    if controls.get("Available control capabilities", "").lower() in {"", "none", "not applicable"}:
        errors.append("Available control capabilities must record at least one capability or user handoff")

    if not re.search(r"^## Source list\s*$\n(?:\s*\n)*1\.\s+\S+", text, re.MULTILINE):
        errors.append("Source list must contain at least one URL")

    try:
        validate_privacy({"document": text})
    except RecordValidationError as exc:
        errors.append(str(exc))
    secret_label = re.search(
        r"^-\s*(?:password|passcode|otp|recovery code|cookie|session id|oauth code|"
        r"magic link)\s*:\s*(?!not applicable|none|redacted)\S+",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if secret_label:
        errors.append("secret-bearing field found in shareable record")
    seen_keys: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    status_counts: Counter[str] = Counter()
    verification_counts: Counter[str] = Counter()
    manual_queue: list[str] = []

    for site in sites:
        name = str(site["name"])
        fields = site["fields"]
        assert isinstance(fields, dict)
        missing = sorted(REQUIRED_SITE_FIELDS - fields.keys())
        if missing:
            errors.append(f"{name}: missing fields: " + ", ".join(missing))

        status = fields.get("Status", "")
        verification = fields.get("Verification preflight", "")
        status_counts[status or "missing"] += 1
        verification_counts[verification or "missing"] += 1
        if verification in UNRESOLVED_VERIFICATION:
            manual_queue.append(name)

        idem = fields.get("Idempotency key", "")
        if idem:
            if idem in seen_keys:
                errors.append(f"{name}: duplicate idempotency key also used by {seen_keys[idem]}")
            else:
                seen_keys[idem] = name

        website = fields.get("Website", "")
        normalized = normalize_url(website) if website else ""
        if normalized:
            if normalized in seen_urls:
                errors.append(f"{name}: duplicate normalized website also used by {seen_urls[normalized]}")
            else:
                seen_urls[normalized] = name

        state_record = {
            "status": status,
            "verification_preflight": verification,
            "platform_capability_result": fields.get("Platform capability result", ""),
            "legitimacy_gate": fields.get("Legitimacy gate", ""),
            "authorization_reference": fields.get("Authorization reference", ""),
            "fields_entered": fields.get("Fields entered", ""),
            "agreements_subscriptions": fields.get("Agreements/subscriptions", ""),
            "submit_timestamp": fields.get("Submit timestamp", ""),
            "exact_result": fields.get("Exact result", ""),
            "evidence_reference": fields.get("Evidence reference", ""),
            "public_listing_url": fields.get("Public listing URL", ""),
            "backend_checked": fields.get("Backend checked", ""),
            "mailbox_checked": fields.get("Mailbox checked", ""),
            "public_page_checked": fields.get("Public page checked", ""),
            "last_checked": fields.get("Last checked", ""),
        }
        try:
            validate_submission_state(state_record)
        except RecordValidationError as exc:
            errors.append(f"{name}: {exc}")

    if not sites:
        errors.append("record contains no website sections")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "total_sites": len(sites),
        "status_counts": dict(sorted(status_counts.items())),
        "verification_counts": dict(sorted(verification_counts.items())),
        "manual_verification_queue": manual_queue,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.record.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Valid: {result['valid']}")
        print(f"Total sites: {result['total_sites']}")
        for key, count in result["status_counts"].items():
            print(f"{key}: {count}")
        if result["manual_verification_queue"]:
            print("Manual verification queue: " + ", ".join(result["manual_verification_queue"]))
        for error in result["errors"]:
            print("ERROR: " + error)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
