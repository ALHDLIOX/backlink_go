"""migrations / v6_to_v8 for Backlink Operations V1."""
from __future__ import annotations
from backlink_records.model import (
    CAMPAIGN_HEADERS,
    EVENT_HEADERS,
    PLATFORM_HEADERS,
    UNVERIFIED_BACKLINK,
    _meaningful,
    compact_record_timestamps,
    computed_idempotency_key,
)

def _status_from_v6(v: object) -> str:
    return {"form in progress": "in progress", "writing": "in progress", "composing": "in progress",
            "editor in progress": "in progress", "submission outcome unknown": "outcome unknown",
            "publication outcome unknown": "outcome unknown"}.get(str(v), str(v))


def _verification_summary(item: dict[str, object]) -> str:
    parts = [str(item.get("verification_preflight", "")).strip()]
    for field, label in (("backend_checked", "backend"), ("mailbox_checked", "mailbox"),
                         ("public_page_checked", "public page"), ("outbound_link_checked", "outbound link")):
        value = str(item.get(field, "")).strip()
        if value and value.lower() not in {"not checked", "not applicable", "none"}: parts.append(f"{label}: {value}")
    return "; ".join(p for p in parts if p) or "not checked"


def migrate_v6_records(source: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    campaigns = [{h: str(i.get(h, "")) for h in CAMPAIGN_HEADERS} for i in source.get("Campaigns", [])]
    platforms = [{h: str(i.get(h, "")) for h in PLATFORM_HEADERS} for i in source.get("Platforms", [])]
    placements: list[dict[str, str]] = []; key_map: dict[str, str] = {}
    def add(item: dict[str, str], kind: str) -> None:
        id_field = {"submission": "queue_id", "article": "article_id", "social": "social_post_id"}[kind]
        identity = str(item.get(id_field, "")).strip() or str(item.get("queue_id", "")).strip()
        placement_id = identity if kind != "submission" else f"submission-{item.get('campaign_id', '')}-{identity}"
        public = str(item.get("public_listing_url" if kind == "submission" else "public_url", "")).strip() or "not applicable"
        observed_backlink = str(item.get("outbound_href", "")).strip()
        backlink = observed_backlink or UNVERIFIED_BACKLINK
        anchor = str(item.get("anchor_text", "")).strip() or ("not applicable — image or link card" if kind == "social" else "not checked — no public backlink verified")
        action = str(item.get("submit_timestamp" if kind == "submission" else "published_at", "")).strip() or ("unknown" if str(item.get("status")) == "published" else "not submitted")
        status = _status_from_v6(item.get("status", ""))
        verification = _verification_summary(item)
        exact_result = str(item.get("exact_result", "")).strip()
        follow_up = str(item.get("follow_up", "")).strip()
        if not observed_backlink:
            migration_note = "legacy migration: public backlink not verified"
            verification = f"{verification}; {migration_note}" if _meaningful(verification) else migration_note
            if status == "published":
                status = "outcome unknown"
                exact_result = f"{exact_result}; {migration_note}" if _meaningful(exact_result) else migration_note
                follow_up = f"{follow_up}; revalidate public backlink" if _meaningful(follow_up) else "revalidate public backlink"
        r = {"platform_domain": str(item.get("platform_domain", "")), "website": str(item.get("website", "")),
             "status": status, "public_url": public, "backlink_url": backlink,
             "anchor_text": anchor, "exact_result": exact_result, "follow_up": follow_up,
             "verification": verification, "action_at": action, "last_checked": str(item.get("last_checked", "")),
             "placement_id": placement_id, "queue_id": str(item.get("queue_id", "")),
             "product_canonical_id": str(item.get("product_canonical_id", "")), "campaign_id": str(item.get("campaign_id", "")),
             "platform_id": str(item.get("platform_id", "")), "route": str(item.get("route", "")),
             "account_alias": str(item.get("account_alias", "")), "authorization_reference": str(item.get("authorization_reference", "")),
             "evidence_reference": str(item.get("evidence_reference", "")), "execution_method": str(item.get("execution_method", "")),
             "execution_notes": str(item.get("execution_notes", "")), "row_version": str(item.get("row_version", "1"))}
        r["idempotency_key"] = computed_idempotency_key(r); r = compact_record_timestamps(r)
        key_map[str(item.get("idempotency_key", ""))] = r["idempotency_key"]; placements.append(r)
    for i in source.get("Submissions", []): add(i, "submission")
    for i in source.get("Articles", []): add(i, "article")
    for i in source.get("SocialPosts", []): add(i, "social")
    events = []
    for item in source.get("Events", []):
        event = {h: str(item.get(h, "")) for h in EVENT_HEADERS}; event["idempotency_key"] = key_map.get(str(item.get("idempotency_key", "")), event["idempotency_key"])
        events.append(compact_record_timestamps(event))
    return {"Platforms": [compact_record_timestamps(row) for row in platforms], "Campaigns": campaigns, "Placements": placements, "Events": events}



migrate_records = migrate_v6_records
