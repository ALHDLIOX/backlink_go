"""Schema and validation rules for Backlink Operations V1 records."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = "8"
PREVIOUS_SCHEMA_VERSION = "7"
LEGACY_SCHEMA_VERSION = "4"
POLICY_VERSION = "backlink-operations-v1-policy-3"

ALLOWED_STATUSES = {
    "not attempted", "in progress", "draft saved", "submitted", "submitted for review",
    "scheduled", "awaiting approval", "awaiting email verification", "published",
    "outcome unknown", "blocked — manual verification", "blocked — missing verified data",
    "blocked — account or email policy", "rejected", "removed", "unavailable", "paid-only",
    "ineligible", "duplicate — no action", "terminated by user",
}
ALLOWED_WORKFLOW_VERSIONS = {"SPD V1 Batch", "Backlink Operations V1"}
ALLOWED_COST_MODELS = {"free", "paid", "freemium", "unknown"}
EXECUTED = {"in progress", "draft saved", "submitted", "submitted for review", "scheduled",
            "awaiting approval", "awaiting email verification", "published", "outcome unknown"}
TRACKING_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                 "gclid", "fbclid", "msclkid", "ref", "referrer"}
SENSITIVE_QUERY_KEYS = {"token", "key", "api_key", "apikey", "code", "state", "session",
                        "auth", "password", "otp", "signature", "sig"}
UNVERIFIED_BACKLINK = "not checked — no public backlink verified"

PLATFORM_HEADERS = ["website_name", "platform_domain", "canonical_submission_url", "availability",
                    "cost_model", "account_required", "verification_pattern", "reciprocal_requirement",
                    "last_verified_at", "route", "source", "notes", "platform_id", "row_version"]
CAMPAIGN_HEADERS = ["product_canonical_id", "canonical_url", "campaign_id", "source_urls",
                    "source_list_reference", "batch_authorization_reference", "execution_shard_size",
                    "policy_version", "workflow_version", "row_version"]
PLACEMENT_HEADERS = ["product_canonical_id", "platform_domain", "website", "status", "public_url", "backlink_url", "anchor_text",
                     "exact_result", "follow_up", "verification", "action_at", "last_checked",
                     "placement_id", "queue_id", "campaign_id", "platform_id",
                     "route", "account_alias", "idempotency_key", "authorization_reference",
                     "evidence_reference", "execution_method", "execution_notes", "row_version"]
EVENT_HEADERS = ["event_id", "campaign_id", "queue_id", "idempotency_key", "timestamp", "action",
                 "result", "evidence_reference", "actor_alias"]
TABLE_HEADERS = {"Platforms": PLATFORM_HEADERS, "Campaigns": CAMPAIGN_HEADERS,
                 "Placements": PLACEMENT_HEADERS, "Events": EVENT_HEADERS}

SCHEMA_V7_PLACEMENT_HEADERS = ["platform_domain", "website", "status", "public_url", "backlink_url", "anchor_text",
    "exact_result", "follow_up", "verification", "action_at", "last_checked", "placement_id", "queue_id",
    "product_canonical_id", "campaign_id", "platform_id", "route", "account_alias", "idempotency_key",
    "authorization_reference", "evidence_reference", "execution_method", "execution_notes", "row_version"]
SCHEMA_V7_TABLE_HEADERS = {"Platforms": PLATFORM_HEADERS, "Campaigns": CAMPAIGN_HEADERS,
    "Placements": SCHEMA_V7_PLACEMENT_HEADERS, "Events": EVENT_HEADERS}

# Read-only legacy layouts retained solely for one-time schema migration.
SCHEMA_V6_PLATFORM_HEADERS = ["website_name", "platform_domain", "platform_type", "canonical_submission_url",
    "availability", "cost_model", "account_required", "verification_pattern", "reciprocal_requirement",
    "last_verified_at", "route", "source", "notes", "platform_id", "row_version"]
SCHEMA_V6_CAMPAIGN_HEADERS = ["product_canonical_id", "canonical_url", "campaign_id", "campaign_mode",
    "source_urls", "source_list_reference", "batch_authorization_reference", "execution_shard_size",
    "policy_version", "workflow_version", "row_version"]
SCHEMA_V6_SUBMISSION_HEADERS = ["platform_domain", "website", "status", "exact_result", "public_listing_url",
    "follow_up", "verification_preflight", "submit_timestamp", "last_checked", "queue_id",
    "product_canonical_id", "campaign_id", "platform_id", "route", "account_alias", "idempotency_key",
    "legitimacy_gate", "authorization_reference", "evidence_reference", "fields_entered", "fields_omitted",
    "agreements_subscriptions", "backend_checked", "mailbox_checked", "public_page_checked",
    "execution_shard", "execution_method", "execution_notes", "row_version"]
SCHEMA_V6_ARTICLE_HEADERS = ["platform_domain", "website", "status", "title", "public_url", "target_url",
    "anchor_text", "outbound_href", "outbound_rel", "exact_result", "follow_up", "verification_preflight",
    "published_at", "last_checked", "article_id", "queue_id", "product_canonical_id", "campaign_id",
    "platform_id", "route", "account_alias", "idempotency_key", "legitimacy_gate",
    "authorization_reference", "evidence_reference", "content_fingerprint", "canonical_policy",
    "backend_checked", "mailbox_checked", "public_page_checked", "outbound_link_checked",
    "execution_method", "execution_notes", "row_version"]
SCHEMA_V6_SOCIAL_HEADERS = ["platform_domain", "website", "status", "post_type", "title", "post_text",
    "public_url", "target_url", "outbound_href", "board_or_channel", "media_reference", "ai_disclosure",
    "utm_source", "utm_medium", "utm_campaign", "exact_result", "follow_up", "verification_preflight",
    "published_at", "last_checked", "social_post_id", "queue_id", "product_canonical_id", "campaign_id",
    "platform_id", "route", "account_alias", "idempotency_key", "legitimacy_gate",
    "authorization_reference", "evidence_reference", "content_fingerprint", "public_page_checked",
    "outbound_link_checked", "media_checked", "backend_checked", "mailbox_checked", "execution_method",
    "execution_notes", "row_version"]
SCHEMA_V6_EVENT_HEADERS = ["event_id", "record_type", "campaign_id", "queue_id", "idempotency_key",
                           "timestamp", "action", "result", "evidence_reference", "actor_alias"]
SCHEMA_V6_TABLE_HEADERS = {"Platforms": SCHEMA_V6_PLATFORM_HEADERS, "Campaigns": SCHEMA_V6_CAMPAIGN_HEADERS,
    "Submissions": SCHEMA_V6_SUBMISSION_HEADERS, "Articles": SCHEMA_V6_ARTICLE_HEADERS,
    "SocialPosts": SCHEMA_V6_SOCIAL_HEADERS, "Events": SCHEMA_V6_EVENT_HEADERS}
LEGACY_PLATFORM_HEADERS = [h for h in SCHEMA_V6_PLATFORM_HEADERS if h != "platform_type"]
LEGACY_CAMPAIGN_HEADERS = ["product_canonical_id", "canonical_url", "campaign_id", "source_urls",
    "source_list_reference", "batch_authorization_reference", "execution_shard_size", "policy_version",
    "spd_version", "row_version"]
LEGACY_SUBMISSION_HEADERS = list(SCHEMA_V6_SUBMISSION_HEADERS)
LEGACY_EVENT_HEADERS = [h for h in SCHEMA_V6_EVENT_HEADERS if h != "record_type"]
LEGACY_TABLE_HEADERS = {"Platforms": LEGACY_PLATFORM_HEADERS, "Campaigns": LEGACY_CAMPAIGN_HEADERS,
                        "Submissions": LEGACY_SUBMISSION_HEADERS, "Events": LEGACY_EVENT_HEADERS}
SCHEMA_V5_TABLE_HEADERS = {"Platforms": SCHEMA_V6_PLATFORM_HEADERS, "Campaigns": SCHEMA_V6_CAMPAIGN_HEADERS,
    "Submissions": SCHEMA_V6_SUBMISSION_HEADERS, "Articles": SCHEMA_V6_ARTICLE_HEADERS,
    "Events": SCHEMA_V6_EVENT_HEADERS}

HEADER_LABELS = {
    "website_name": "平台名称", "platform_domain": "平台域名", "canonical_submission_url": "标准入口",
    "availability": "可用状态", "cost_model": "收费模式", "account_required": "需要账号",
    "verification_pattern": "验证方式", "reciprocal_requirement": "互链要求", "last_verified_at": "最后核验",
    "route": "操作入口", "source": "信息来源", "notes": "备注", "platform_id": "平台编号",
    "row_version": "行版本", "product_canonical_id": "产品编号", "canonical_url": "产品官网",
    "campaign_id": "活动编号", "source_urls": "来源网址", "source_list_reference": "来源清单",
    "batch_authorization_reference": "批次授权", "execution_shard_size": "每批数量",
    "policy_version": "规则版本", "workflow_version": "工作流版本", "website": "操作页面",
    "status": "状态", "public_url": "公开页面", "backlink_url": "实际外链", "anchor_text": "锚文本",
    "exact_result": "准确结果", "follow_up": "后续处理", "verification": "核验情况",
    "action_at": "操作时间", "last_checked": "最后检查", "placement_id": "记录编号",
    "queue_id": "队列编号", "account_alias": "账号别名", "idempotency_key": "防重复键",
    "authorization_reference": "授权编号", "evidence_reference": "证据引用",
    "execution_method": "执行方式", "execution_notes": "执行备注", "event_id": "事件编号",
    "timestamp": "事件时间", "action": "动作", "result": "结果", "actor_alias": "操作者别名"}
# Previous labels are used only to verify an old workbook before migration.
HEADER_LABELS.update({
    "platform_type": "平台类型", "campaign_mode": "活动类型", "spd_version": "SPD 版本",
    "record_type": "记录类型", "legitimacy_gate": "合规性检查", "verification_preflight": "验证预检",
    "fields_entered": "已填写字段", "fields_omitted": "未填写字段", "agreements_subscriptions": "协议与订阅",
    "submit_timestamp": "提交时间", "public_listing_url": "公开页面网址", "backend_checked": "后台检查",
    "mailbox_checked": "邮箱检查", "public_page_checked": "公开页面检查", "execution_shard": "执行批次",
    "article_id": "文章编号", "title": "文章标题", "target_url": "目标链接",
    "outbound_href": "实际外链地址", "outbound_rel": "链接 rel", "published_at": "发布时间",
    "content_fingerprint": "内容指纹", "canonical_policy": "Canonical 规则", "outbound_link_checked": "外链检查",
    "social_post_id": "社交帖子编号", "post_type": "帖子类型", "post_text": "正文",
    "board_or_channel": "Board / 频道", "media_reference": "图片 / 媒体编号", "ai_disclosure": "AI 标识",
    "utm_source": "UTM 来源", "utm_medium": "UTM 媒介", "utm_campaign": "UTM 活动", "media_checked": "图片 / 媒体检查",
})
LEGACY_HEADER_LABELS = dict(HEADER_LABELS)
LEGACY_HEADER_LABELS.update({
    "canonical_submission_url": "标准提交入口", "route": "提交路线", "website": "提交页面", "account_required": "是否需要账号",
    "last_verified_at": "最后核验时间", "source_list_reference": "来源清单编号",
    "batch_authorization_reference": "批次授权编号", "status": "提交状态",
    "evidence_reference": "证据编号", "last_checked": "最后检查时间", "public_url": "公开文章网址",
    "anchor_text": "实际锚文本", "action": "操作", "result": "操作结果",
})
DROPDOWNS = {("Platforms", "availability"): ["available", "unavailable", "unknown"],
    ("Platforms", "cost_model"): sorted(ALLOWED_COST_MODELS),
    ("Platforms", "account_required"): ["yes", "no", "unknown"],
    ("Platforms", "reciprocal_requirement"): ["none", "optional", "required", "unknown"],
    ("Placements", "status"): sorted(ALLOWED_STATUSES)}

class RecordValidationError(ValueError): pass

def display_headers(tab_name: str) -> list[str]: return [HEADER_LABELS[h] for h in TABLE_HEADERS[tab_name]]

def normalize_url(value: str) -> str:
    raw = str(value).strip()
    if not re.match(r"^https?://", raw, flags=re.I): raise RecordValidationError(f"URL must be public HTTP(S): {raw}")
    split = urlsplit(raw)
    if not split.hostname: raise RecordValidationError(f"URL has no hostname: {raw}")
    query = [(k, v) for k, v in parse_qsl(split.query, keep_blank_values=True) if k.lower() not in TRACKING_KEYS]
    path = split.path or "/"
    if path != "/": path = path.rstrip("/")
    return urlunsplit((split.scheme.lower(), split.netloc.lower(), path, urlencode(query), ""))

def normalize_platform_domain(value: object) -> str:
    raw = str(value or "").strip().lower().rstrip(".")
    if not raw or "://" in raw or any(character in raw for character in "/?#@"):
        raise RecordValidationError(f"platform_domain must be a hostname: {raw}")
    try:
        hostname = raw.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise RecordValidationError(f"platform_domain is invalid: {raw}") from exc
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if not hostname or any(not label or not re.fullmatch(r"[a-z0-9-]+", label) or label.startswith("-") or label.endswith("-")
                           for label in hostname.split(".")):
        raise RecordValidationError(f"platform_domain is invalid: {raw}")
    return hostname

def url_matches_platform_domain(url: object, platform_domain: object) -> bool:
    normalized_url = normalize_url(str(url))
    hostname = str(urlsplit(normalized_url).hostname or "").lower().rstrip(".")
    if hostname.startswith("www."):
        hostname = hostname[4:]
    claimed = normalize_platform_domain(platform_domain)
    return hostname == claimed or hostname.endswith(f".{claimed}")

def platform_domains_match(left: object, right: object) -> bool:
    try:
        return normalize_platform_domain(left) == normalize_platform_domain(right)
    except RecordValidationError:
        return False

def require_url_matches_platform_domain(url: object, platform_domain: object, field: str) -> None:
    if not url_matches_platform_domain(url, platform_domain):
        hostname = urlsplit(str(url)).hostname or str(url)
        raise RecordValidationError(f"{field} hostname {hostname} does not match platform_domain {platform_domain}")

def compact_timestamp(value: object) -> str:
    raw = str(value or "").strip()
    if not raw or raw.lower() in {"not submitted", "not published", "unknown"}: return raw
    try: return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError as exc: raise RecordValidationError(f"invalid timestamp: {raw}") from exc

def compact_record_timestamps(record: dict[str, object]) -> dict[str, str]:
    result = {k: str(v) for k, v in record.items()}
    for field in ("last_verified_at", "action_at", "last_checked", "timestamp"):
        if field in result: result[field] = compact_timestamp(result[field])
    return result

def _empty(v: object) -> bool: return not str(v or "").strip()
def _meaningful(v: object) -> bool: return str(v or "").strip().lower() not in {"", "not applicable", "not checked", "unknown", "none", UNVERIFIED_BACKLINK}
def _require(record: dict[str, object], fields: list[str], kind: str) -> None:
    missing = [f for f in fields if _empty(record.get(f))]
    if missing: raise RecordValidationError(f"{kind} missing required fields: {', '.join(missing)}")
def _assert_time(v: object, field: str, sentinels: set[str] | None = None) -> None:
    raw = str(v or "").strip()
    if sentinels and raw.lower() in sentinels: return
    try: datetime.strptime(raw, "%Y-%m-%d %H:%M")
    except ValueError as exc: raise RecordValidationError(f"{field} must use YYYY-MM-DD HH:MM") from exc
def validate_privacy(record: dict[str, object]) -> None:
    serialized = json.dumps(record, ensure_ascii=False)
    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", serialized, flags=re.I):
        raise RecordValidationError("raw email address found; use an alias")
    if re.search(r"(?<![\w-])\+\d[\d\s().-]{7,}\d(?![\w-])", serialized):
        raise RecordValidationError("raw phone number found; use an alias")
    for field, value in record.items():
        text = str(value or "")
        if re.search(r"(?i)(password|passcode|otp|recovery[_ ]?code|cookie|session[_ ]?id|oauth[_ ]?code|magic[_ ]?link)\s*[:=]\s*(?!none\b|redacted\b)\S+", text):
            raise RecordValidationError(f"secret-bearing value is forbidden in {field}")
        if re.search(r"(?i)Bearer\s+[A-Za-z0-9._~-]+", text):
            raise RecordValidationError(f"bearer token is forbidden in {field}")
        if re.match(r"^https?://", text, flags=re.I):
            if any(k.lower() in SENSITIVE_QUERY_KEYS for k, _ in parse_qsl(urlsplit(text).query, keep_blank_values=True)):
                raise RecordValidationError(f"sensitive query parameter is forbidden in {field}")

def computed_idempotency_key(record: dict[str, object]) -> str:
    return "|".join(str(record.get(k, "")).strip() for k in ("platform_domain", "product_canonical_id", "account_alias", "route", "placement_id"))

def validate_platform(r: dict[str, object]) -> None:
    _require(r, [h for h in PLATFORM_HEADERS if h not in {"row_version", "source", "notes"}], "platform"); validate_privacy(r); require_url_matches_platform_domain(r["canonical_submission_url"], r["platform_domain"], "canonical_submission_url"); _assert_time(r["last_verified_at"], "last_verified_at")
    if r["availability"] not in {"available", "unavailable", "unknown"}: raise RecordValidationError("invalid availability")
    if r["cost_model"] not in ALLOWED_COST_MODELS: raise RecordValidationError("invalid cost_model")
    if r["account_required"] not in {"yes", "no", "unknown"}: raise RecordValidationError("invalid account_required")
    if r["reciprocal_requirement"] not in {"none", "optional", "required", "unknown"}: raise RecordValidationError("invalid reciprocal_requirement")

def normalize_campaign_input(r: dict[str, object]) -> dict[str, object]:
    result = dict(r)
    if "spd_version" in result and "workflow_version" not in result: result["workflow_version"] = "SPD V1 Batch"
    result.pop("spd_version", None); result.pop("campaign_mode", None)
    return result
def validate_campaign(r: dict[str, object]) -> None:
    _require(r, [h for h in CAMPAIGN_HEADERS if h != "row_version"], "campaign"); validate_privacy(r); normalize_url(str(r["canonical_url"]))
    if r["workflow_version"] not in ALLOWED_WORKFLOW_VERSIONS: raise RecordValidationError("invalid workflow_version")
    try:
        if int(str(r["execution_shard_size"])) < 1: raise ValueError
    except ValueError as exc: raise RecordValidationError("execution_shard_size must be a positive integer") from exc

def validate_placement_state(r: dict[str, object]) -> None:
    status = str(r.get("status", ""))
    if status not in ALLOWED_STATUSES: raise RecordValidationError("invalid placement status")
    if status in EXECUTED and not _meaningful(r.get("authorization_reference")): raise RecordValidationError("executed placement requires authorization_reference")
    if status in {"submitted", "submitted for review", "scheduled", "awaiting approval", "awaiting email verification"}:
        if not all(_meaningful(r.get(f)) for f in ("action_at", "exact_result", "evidence_reference")):
            raise RecordValidationError("submitted or pending placement requires action_at, exact_result, and evidence_reference")
    if status == "published":
        for f in ("public_url", "backlink_url", "anchor_text", "exact_result", "verification", "action_at", "last_checked", "evidence_reference"):
            if f == "action_at" and str(r.get(f, "")).strip().lower() == "unknown": continue
            if not _meaningful(r.get(f)): raise RecordValidationError(f"published placement requires {f}")
    if status == "outcome unknown" and not _meaningful(r.get("verification")): raise RecordValidationError("outcome unknown requires a concrete verification summary")
    if status == "removed" and not all(_meaningful(r.get(f)) for f in ("public_url", "action_at", "verification")):
        raise RecordValidationError("removed placement requires prior public URL, action time, and verification")

def validate_placement(r: dict[str, object]) -> None:
    _require(r, [h for h in PLACEMENT_HEADERS if h != "row_version"], "placement"); validate_privacy(r)
    require_url_matches_platform_domain(r["website"], r["platform_domain"], "website")
    for f in ("public_url", "backlink_url"):
        if _meaningful(r.get(f)): normalize_url(str(r[f]))
    expected = computed_idempotency_key(r)
    if str(r.get("idempotency_key")) != expected: raise RecordValidationError(f"idempotency_key must equal {expected}")
    _assert_time(r["last_checked"], "last_checked"); _assert_time(r["action_at"], "action_at", {"not submitted", "not published", "unknown"})
    validate_placement_state(r)
def validate_event(r: dict[str, object]) -> None:
    _require(r, EVENT_HEADERS, "event"); validate_privacy(r); _assert_time(r["timestamp"], "timestamp")

def prepare_record(kind: str, payload: dict[str, object], existing: dict[str, object] | None = None) -> dict[str, str]:
    if kind == "platform": headers, validator = PLATFORM_HEADERS, validate_platform
    elif kind == "campaign": payload, headers, validator = normalize_campaign_input(payload), CAMPAIGN_HEADERS, validate_campaign
    elif kind == "placement": headers, validator = PLACEMENT_HEADERS, validate_placement
    elif kind == "event": payload, headers, validator = {k: v for k, v in payload.items() if k != "record_type"}, EVENT_HEADERS, validate_event
    else: raise RecordValidationError(f"unsupported record kind: {kind}")
    unknown = sorted(set(payload) - set(headers) - {"expected_row_version"})
    if unknown: raise RecordValidationError("unknown fields: " + ", ".join(unknown))
    result = {h: str(payload.get(h, existing.get(h, "") if existing else "")) for h in headers}
    result = compact_record_timestamps(result)
    if kind != "event": result["row_version"] = str((int(str(existing.get("row_version", "0"))) if existing else 0) + 1)
    validator(result); return result

def row_values(headers: list[str], record: dict[str, object]) -> list[object]: return [record.get(h, "") for h in headers]
def rows_to_records(headers: list[str], rows: list[list[object]]) -> list[dict[str, str]]:
    result = []
    for row in rows:
        if not any(str(v).strip() for v in row): continue
        padded = row + [""] * (len(headers) - len(row)); result.append({h: str(padded[i]) for i, h in enumerate(headers)})
    return result

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
    return {"Platforms": platforms, "Campaigns": campaigns, "Placements": placements, "Events": events}

def migrate_legacy_record(tab_name: str, record: dict[str, object]) -> dict[str, str]:
    result = {h: str(record.get(h, "")) for h in SCHEMA_V6_TABLE_HEADERS.get(tab_name, [])}
    if tab_name == "Platforms": result["platform_type"] = "directory"
    if tab_name == "Campaigns": result.update(campaign_mode="directory", workflow_version="SPD V1 Batch")
    if tab_name == "Events": result["record_type"] = "submission"
    return result

def audit_records(*, campaigns: list[dict[str, object]], placements: list[dict[str, object]], events: list[dict[str, object]],
                  platforms: list[dict[str, object]], campaign_id: str | None = None, **_: object) -> dict[str, object]:
    errors: list[str] = []; selected_campaigns = [c for c in campaigns if not campaign_id or c.get("campaign_id") == campaign_id]
    selected = [p for p in placements if not campaign_id or p.get("campaign_id") == campaign_id]
    selected_events = [e for e in events if not campaign_id or e.get("campaign_id") == campaign_id]
    if campaign_id and not selected_campaigns: errors.append(f"campaign not found: {campaign_id}")
    for name, items, key in (("campaign_id", campaigns, "campaign_id"), ("platform_id", platforms, "platform_id"), ("placement_id", placements, "placement_id"), ("event_id", events, "event_id")):
        counts = Counter(str(i.get(key, "")) for i in items); errors.extend(f"duplicate {name}: {v}" for v, c in counts.items() if v and c > 1)
    counts = Counter(str(i.get("idempotency_key", "")) for i in placements); errors.extend(f"duplicate idempotency_key: {v}" for v, c in counts.items() if v and c > 1)
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
        if str(item.get("status")) in EXECUTED and target not in targets: errors.append(f"{target[0]}/{target[1]}: executed state requires an event")
    for item in selected_campaigns:
        try: validate_campaign(item)
        except RecordValidationError as exc: errors.append(f"campaign {item.get('campaign_id', '')}: {exc}")
    for item in platforms:
        try: validate_platform(item)
        except RecordValidationError as exc: errors.append(f"platform {item.get('platform_id', '')}: {exc}")
    return {"valid": not errors, "errors": errors, "warnings": [], "total_placements": len(selected), "total_records": len(selected), "status_counts": dict(sorted(status_counts.items()))}

def export_campaign_markdown(campaign: dict[str, object], placements: list[dict[str, object]], events: list[dict[str, object]], *_: object) -> str:
    lines = [f"# {campaign['campaign_id']} — Backlink Operations Record", "", "## Campaign", ""]
    lines.extend(f"- {HEADER_LABELS[k]}: {campaign.get(k, '')}" for k in CAMPAIGN_HEADERS[:-1])
    for item in placements:
        lines.extend(["", f"## {item['queue_id']} — {item['platform_domain']}", ""])
        lines.extend(f"- {HEADER_LABELS[k]}: {item.get(k, '')}" for k in PLACEMENT_HEADERS if k != "row_version")
        lines.extend(["", "### Attempt log", ""]); related = [e for e in events if e.get("idempotency_key") == item.get("idempotency_key")]
        lines.extend(f"- {e['timestamp']} | event_id={e['event_id']} | action={e['action']} | result={e['result']} | evidence={e['evidence_reference']}" for e in related)
        if not related: lines.append("- none")
    return "\n".join(lines) + "\n"
