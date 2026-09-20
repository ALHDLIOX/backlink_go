"""operations for Backlink Operations V1."""
from __future__ import annotations
from collections import Counter
from datetime import datetime
from pathlib import Path
import re
from typing import Any
from backlink_records.credentials import build_gmail_service, read_json_file, require_private_file
from backlink_records.model import (
    CAMPAIGN_HEADERS,
    EVENT_HEADERS,
    EXECUTED,
    LEGACY_SCHEMA_VERSION,
    LEGACY_TABLE_HEADERS,
    PLACEMENT_HEADERS,
    PLATFORM_HEADERS,
    PREVIOUS_SCHEMA_VERSION,
    RecordValidationError,
    SCHEMA_V5_TABLE_HEADERS,
    SCHEMA_V6_TABLE_HEADERS,
    SCHEMA_V7_TABLE_HEADERS,
    SCHEMA_V8_TABLE_HEADERS,
    SCHEMA_V9_TABLE_HEADERS,
    SCHEMA_VERSION,
    TABLE_HEADERS,
    compact_record_timestamps,
    normalize_campaign_input,
    platform_domains_match,
    prepare_record,
    validate_campaign,
    validate_event,
    validate_placement,
    validate_platform,
)
from backlink_records.reconciliation import records_equal, write_with_reconciliation
from backlink_records.sheets_store import GoogleSheetsStore, load_store, records_with_rows

BADGE_RESUME_ACTION = "resume after badge verification"
BADGE_QUEUE_ACTIONS = {"select badge launch", "defer for badge"}
BADGE_RESUME_STATUSES = {
    "submitted", "submitted for review", "scheduled", "awaiting approval",
    "awaiting email verification", "published", "outcome unknown",
}


def _is_badge_queue_event(event: dict[str, object]) -> bool:
    return (
        str(event.get("action", "")).strip().lower() in BADGE_QUEUE_ACTIONS
        or str(event.get("result", "")).strip().lower() == "waiting badge"
    )


def _badge_resume_error(
    linked_events: list[dict[str, object]], next_status: str, evidence_reference: object,
    *, enforce_transition_outcome: bool = True,
) -> str | None:
    queue_positions = [i for i, event in enumerate(linked_events) if _is_badge_queue_event(event)]
    if not queue_positions:
        return "waiting badge transition requires a prior badge queue event"
    if next_status not in BADGE_RESUME_STATUSES:
        return "waiting badge may resume only to a submitted, pending, published, or outcome unknown state"
    queue_position = max(queue_positions)
    candidates = [
        event for i, event in enumerate(linked_events)
        if i > queue_position
        and str(event.get("action", "")).strip().lower() == BADGE_RESUME_ACTION
        and (evidence_reference is None or str(event.get("evidence_reference", "")) == str(evidence_reference))
        and str(event.get("evidence_reference", "")).strip().lower() not in {"", "not applicable", "none", "unknown"}
    ]
    if not candidates:
        return "leaving waiting badge requires a new resume after badge verification event with matching evidence"
    result = str(candidates[-1].get("result", "")).strip().lower()
    result_tokens = {token.strip() for token in re.split(r"[;|\n]+", result) if token.strip()}
    if "badge verified" not in result_tokens:
        return "badge resume event result must include the exact badge verified token"
    if not enforce_transition_outcome:
        if not result_tokens.intersection({"submitted", "published", "submission attempted"}):
            return "badge resume event result must include an exact positive submission outcome token"
        return None
    required_result = "published" if next_status == "published" else "submitted"
    if next_status == "outcome unknown" and "submission attempted" not in result_tokens:
        return "badge resume event result must include the exact submission attempted token for outcome unknown"
    if next_status != "outcome unknown" and required_result not in result_tokens:
        return f"badge resume event result must include the exact {required_result} token"
    return None


def audit_records(*, campaigns: list[dict[str, object]], placements: list[dict[str, object]], events: list[dict[str, object]],
                  platforms: list[dict[str, object]], campaign_id: str | None = None, **_: object) -> dict[str, object]:
    errors: list[str] = []; selected_campaigns = [c for c in campaigns if not campaign_id or c.get("campaign_id") == campaign_id]
    selected = [p for p in placements if not campaign_id or p.get("campaign_id") == campaign_id]
    selected_events = [e for e in events if not campaign_id or e.get("campaign_id") == campaign_id]
    if campaign_id and not selected_campaigns: errors.append(f"campaign not found: {campaign_id}")
    for name, items, key in (("campaign_id", campaigns, "campaign_id"), ("platform_id", platforms, "platform_id"), ("placement_id", placements, "placement_id"), ("event_id", events, "event_id")):
        counts = Counter(str(i.get(key, "")) for i in items); errors.extend(f"duplicate {name}: {v}" for v, c in counts.items() if v and c > 1)
    counts = Counter(str(i.get("idempotency_key", "")) for i in placements); errors.extend(f"duplicate idempotency_key: {v}" for v, c in counts.items() if v and c > 1)
    for kind, items, key in (("platform", platforms, "platform_id"), ("campaign", campaigns, "campaign_id"), ("placement", placements, "placement_id")):
        for item in items:
            try:
                if int(str(item.get("row_version", ""))) < 1: raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{kind} {item.get(key, '')}: row_version must be a positive integer")
    cmap = {str(c.get("campaign_id", "")): c for c in selected_campaigns}; pmap = {str(p.get("platform_id", "")): p for p in platforms}
    pairs = set(); status_counts: Counter[str] = Counter()
    for item in selected:
        label = f"{item.get('campaign_id', '')}/{item.get('queue_id', '')}"; pair = (str(item.get("campaign_id", "")), str(item.get("queue_id", "")))
        if pair in pairs: errors.append(f"duplicate campaign/queue pair: {label}")
        pairs.add(pair)
        if pair[0] not in cmap: errors.append(f"{label}: unknown campaign_id")
        elif str(item.get("product_canonical_id", "")) != str(cmap[pair[0]].get("product_canonical_id", "")): errors.append(f"{label}: product_canonical_id does not match campaign")
        pid = str(item.get("platform_id", ""))
        if pid not in pmap: errors.append(f"{label}: unknown platform_id")
        elif not platform_domains_match(item.get("platform_domain"), pmap[pid].get("platform_domain")): errors.append(f"{label}: platform_domain does not match platform")
        if item.get("status") == "waiting badge" and pid in pmap and pmap[pid].get("reciprocal_requirement") != "required":
            errors.append(f"{label}: waiting badge requires reciprocal_requirement required")
        try: validate_placement(item)
        except RecordValidationError as exc: errors.append(f"{label}: {exc}")
        status_counts[str(item.get("status", "missing"))] += 1
    targets = {(str(e.get("campaign_id", "")), str(e.get("queue_id", "")), str(e.get("idempotency_key", ""))) for e in selected_events}; last: dict[str, datetime] = {}
    for event in selected_events:
        eid = str(event.get("event_id", "")); key = str(event.get("idempotency_key", "")); target = next((p for p in selected if str(p.get("idempotency_key", "")) == key), None)
        if not target: errors.append(f"event {eid}: unknown idempotency_key")
        elif str(target.get("campaign_id")) != str(event.get("campaign_id")) or str(target.get("queue_id")) != str(event.get("queue_id")): errors.append(f"event {eid}: campaign_id or queue_id does not match placement")
        try:
            validate_event(event); stamp = datetime.strptime(str(event["timestamp"]), "%Y-%m-%d %H:%M")
            if key in last and stamp < last[key]: errors.append(f"event {eid}: timestamp moves backward")
            last[key] = stamp
        except RecordValidationError as exc: errors.append(f"event {eid}: {exc}")
    for item in selected:
        target = (str(item.get("campaign_id", "")), str(item.get("queue_id", "")), str(item.get("idempotency_key", "")))
        status = str(item.get("status", ""))
        if status in EXECUTED and target not in targets: errors.append(f"{target[0]}/{target[1]}: executed state requires an event")
        related = [event for event in selected_events if str(event.get("idempotency_key", "")) == target[2]]
        if status != "waiting badge" and any(_is_badge_queue_event(event) for event in related):
            resume_error = _badge_resume_error(related, status, None, enforce_transition_outcome=False)
            if resume_error: errors.append(f"{target[0]}/{target[1]}: {resume_error}")
    for item in selected_campaigns:
        try: validate_campaign(item)
        except RecordValidationError as exc: errors.append(f"campaign {item.get('campaign_id', '')}: {exc}")
    for item in platforms:
        try: validate_platform(item)
        except RecordValidationError as exc: errors.append(f"platform {item.get('platform_id', '')}: {exc}")
    return {"valid": not errors, "errors": errors, "warnings": [], "total_placements": len(selected), "total_records": len(selected), "status_counts": dict(sorted(status_counts.items()))}


def doctor(config_dir: Path, gmail_service: Any | None = None) -> dict[str, object]:
    errors: list[str] = []
    output: dict[str, object] = {
        "healthy": False,
        "migration_required": False,
        "sheets": "error",
        "gmail": "error",
        "errors": errors,
        "target_schema_version": SCHEMA_VERSION,
    }
    try:
        config_path = config_dir / "v1-sheets.json"
        require_private_file(config_path)
        config = read_json_file(config_path)
        schema_version = str(config.get("schema_version", ""))
        table_headers = {
            LEGACY_SCHEMA_VERSION: LEGACY_TABLE_HEADERS,
            "5": SCHEMA_V5_TABLE_HEADERS,
            "6": SCHEMA_V6_TABLE_HEADERS,
            "7": SCHEMA_V7_TABLE_HEADERS,
            "8": SCHEMA_V8_TABLE_HEADERS,
            "9": SCHEMA_V9_TABLE_HEADERS,
            SCHEMA_VERSION: TABLE_HEADERS,
        }.get(schema_version)
        if table_headers is None:
            raise RecordValidationError("workbook config is invalid or unsupported")
        store = load_store(config_dir, schema_version)
        metadata = store.verify_schema(schema_version, table_headers)
        current = schema_version == SCHEMA_VERSION
        output.update({
            "migration_required": not current,
            "sheets": "ok",
            "spreadsheet_id": store.spreadsheet_id,
            "title": metadata.get("properties", {}).get("title", ""),
            "schema_version": schema_version,
            "worksheets": list(table_headers),
        })
    except Exception:
        errors.append("Sheets check failed; verify the workbook config and run auth --replace if needed")

    try:
        service = gmail_service or build_gmail_service(config_dir)
        service.users().getProfile(userId="me").execute()
        output["gmail"] = "ok"
    except Exception:
        errors.append("Gmail check failed; enable Gmail API and run auth --replace if needed")

    output["healthy"] = output["sheets"] == "ok" and output["gmail"] == "ok" and not output["migration_required"]
    return output


def upsert(store: GoogleSheetsStore, kind: str, payload: dict[str, Any], *, correction_event_id: str | None = None) -> dict[str, str]:
    mapping = {
        "platform": ("Platforms", "platform_id", PLATFORM_HEADERS, validate_platform),
        "campaign": ("Campaigns", "campaign_id", CAMPAIGN_HEADERS, validate_campaign),
        "placement": ("Placements", "idempotency_key", PLACEMENT_HEADERS, validate_placement),
    }
    if kind == "campaign":
        payload = normalize_campaign_input(payload)
    payload = compact_record_timestamps(payload)
    tab_name, key_field, headers, validator = mapping[kind]
    store.verify_schema()
    key_value = str(payload.get(key_field, ""))
    if not key_value:
        raise RecordValidationError(f"{key_field} is required")
    validator(payload)
    existing_rows = records_with_rows(store, tab_name)
    existing_records = [record for _, record in existing_rows]
    matches = [
        (index, record) for index, record in existing_rows
        if record.get(key_field) == key_value
    ]
    if len(matches) > 1:
        raise RecordValidationError(f"duplicate {key_field} rows found in {tab_name}")
    found = matches[0] if matches else None
    if kind == "placement":
        campaign = store.find("Campaigns", "campaign_id", str(payload.get("campaign_id", "")))
        platform = store.find("Platforms", "platform_id", str(payload.get("platform_id", "")))
        if not campaign:
            raise RecordValidationError("placement references an unknown campaign_id")
        if not platform:
            raise RecordValidationError("placement references an unknown platform_id")
        if str(campaign[1].get("product_canonical_id")) != str(payload.get("product_canonical_id")):
            raise RecordValidationError("placement product_canonical_id does not match campaign")
        if not platform_domains_match(
            platform[1].get("platform_domain", ""), payload.get("platform_domain", "")
        ):
            raise RecordValidationError("placement platform_domain does not match platform")
        if payload.get("status") == "waiting badge" and platform[1].get("reciprocal_requirement") != "required":
            raise RecordValidationError("waiting badge requires reciprocal_requirement required")
        if found and found[1].get("campaign_id") != str(payload.get("campaign_id")):
            raise RecordValidationError("idempotency_key already belongs to another campaign")
        for record in existing_records:
            if record.get("placement_id") == str(payload.get("placement_id")) and record.get("idempotency_key") != key_value:
                raise RecordValidationError("placement_id already belongs to another placement")
            if record.get("campaign_id") == str(payload.get("campaign_id")) and record.get("queue_id") == str(payload.get("queue_id")) and record.get("idempotency_key") != key_value:
                raise RecordValidationError("queue_id already belongs to another campaign placement")
        linked_events = [
            event for event in store.records("Events")
            if event.get("idempotency_key") == key_value
            and event.get("campaign_id") == str(payload.get("campaign_id"))
            and event.get("queue_id") == str(payload.get("queue_id"))
        ]
        if str(payload.get("status", "")) in EXECUTED and not linked_events:
            raise RecordValidationError("executed placement state requires a prior linked event")
    if correction_event_id:
        if kind != "placement" or not found or found[1].get("status") != "awaiting approval" or payload.get("status") != "waiting badge":
            raise RecordValidationError("correction only permits awaiting approval to waiting badge")
        if any(str(found[1].get(field, "")).startswith(("https://", "http://")) for field in ("public_url", "backlink_url")):
            raise RecordValidationError("correction cannot clear existing public or backlink URLs")
        correction = next((event for event in linked_events if event.get("event_id") == correction_event_id), None)
        if not correction or correction.get("action") != "correct unsubmitted status" or correction.get("evidence_reference") != payload.get("evidence_reference"):
            raise RecordValidationError("correction requires a linked correction event with matching evidence")
    if found:
        try:
            if int(found[1].get("row_version", "")) < 1:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"invalid current row_version in {tab_name}") from exc
        business_headers = [header for header in headers if header not in {"created_at", "updated_at", "row_version"}]
        if records_equal(business_headers, payload, found[1]):
            return {
                "action": "unchanged",
                "table": tab_name,
                "key": key_value,
                "row_version": str(found[1].get("row_version", "")),
            }
        if kind == "placement":
            previous_status = str(found[1].get("status", ""))
            next_status = str(payload.get("status", ""))
            if previous_status == "waiting badge" and next_status != "waiting badge":
                resume_error = _badge_resume_error(linked_events, next_status, payload.get("evidence_reference"))
                if resume_error: raise RecordValidationError(resume_error)
            if previous_status in {"submitted", "submitted for review", "scheduled", "awaiting approval", "awaiting email verification", "published", "outcome unknown"} and next_status in {"not attempted", "in progress", "draft saved", "waiting badge"} and not correction_event_id:
                raise RecordValidationError("completed or pending idempotency key cannot be reopened")
        expected_version = str(payload.pop("expected_row_version", "")).strip()
        current_version = str(found[1].get("row_version", "")).strip()
        if not expected_version:
            raise RecordValidationError("expected_row_version is required when updating an existing row")
        if expected_version != current_version:
            raise RecordValidationError(
                f"row version conflict in {tab_name}: expected {expected_version}, current {current_version}"
            )
    elif "expected_row_version" in payload:
        expected_version = str(payload.pop("expected_row_version")).strip()
        if expected_version not in {"", "0"}:
            raise RecordValidationError("expected_row_version must be omitted or 0 for a new row")
    prepared = prepare_record(kind, payload, found[1] if found else None)
    if found:
        row_number = found[0]
        operation = lambda: store.update(tab_name, row_number, prepared)
        action = "updated"
    else:
        operation = lambda: store.append(tab_name, prepared)
        action = "created"
    write_with_reconciliation(store, tab_name, key_field, key_value, prepared, operation, original=found)
    return {"action": action, "table": tab_name, "key": key_value, "row_version": prepared["row_version"]}


def append_event(store: GoogleSheetsStore, payload: dict[str, Any]) -> dict[str, str]:
    store.verify_schema()
    prepared = prepare_record("event", payload)
    event_id = prepared["event_id"]
    event_rows = records_with_rows(store, "Events")
    event_records = [record for _, record in event_rows]
    matches = [
        (index, record) for index, record in event_rows
        if record.get("event_id") == event_id
    ]
    if len(matches) > 1:
        raise RecordValidationError("duplicate event_id rows found in Events")
    found = matches[0] if matches else None
    if found:
        if records_equal(EVENT_HEADERS, prepared, found[1]):
            return {"action": "already-recorded", "table": "Events", "key": event_id}
        raise RecordValidationError("event_id already exists with different content")
    target = store.find("Placements", "idempotency_key", prepared["idempotency_key"])
    if not target:
        raise RecordValidationError("event references an unknown idempotency_key")
    if target[1]["campaign_id"] != prepared["campaign_id"] or target[1]["queue_id"] != prepared["queue_id"]:
        raise RecordValidationError("event campaign_id or queue_id does not match target record")
    event_time = datetime.fromisoformat(prepared["timestamp"].replace("Z", "+00:00"))
    try:
        prior_times = [
            datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            for item in event_records
            if item.get("idempotency_key") == prepared["idempotency_key"]
        ]
    except (KeyError, ValueError) as exc:
        raise RecordValidationError("invalid existing event timestamp") from exc
    if prior_times and event_time < max(prior_times):
        raise RecordValidationError("event timestamp moves backward for this idempotency_key")
    write_with_reconciliation(
        store,
        "Events",
        "event_id",
        event_id,
        prepared,
        lambda: store.append("Events", prepared),
    )
    return {"action": "created", "table": "Events", "key": event_id}


def workbook_audit(store: GoogleSheetsStore, campaign_id: str | None) -> dict[str, object]:
    store.verify_schema()
    return audit_records(
        campaigns=store.records("Campaigns"),
        placements=store.records("Placements"),
        events=store.records("Events"),
        platforms=store.records("Platforms"),
        campaign_id=campaign_id,
    )


def placement_history(
    store: GoogleSheetsStore,
    product_id: str,
    platform_domain: str | None = None,
) -> list[dict[str, str]]:
    store.verify_schema()
    selected = []
    for item in store.records("Placements"):
        if item.get("product_canonical_id") != product_id:
            continue
        if platform_domain and not platform_domains_match(item.get("platform_domain", ""), platform_domain):
            continue
        selected.append(
            {
                key: item.get(key, "")
                for key in PLACEMENT_HEADERS
            }
        )
    return selected
