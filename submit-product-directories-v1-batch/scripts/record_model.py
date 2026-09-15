"""Schema and validation rules for SPD V1 Batch records."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SCHEMA_VERSION = "1"

ALLOWED_STATUSES = {
    "not attempted",
    "form in progress",
    "draft saved",
    "submitted",
    "submission outcome unknown",
    "awaiting approval",
    "awaiting email verification",
    "published",
    "blocked — manual verification",
    "blocked — missing verified data",
    "blocked — account or email policy",
    "unavailable",
    "paid-only",
    "ineligible",
    "duplicate — no action",
    "terminated by user",
}

ALLOWED_VERIFICATION = {
    "not checked",
    "automatic verification passed",
    "awaiting manual verification",
    "manual verification completed",
    "verification unavailable before form",
    "verification expired/reset",
    "no verification presented",
    "deferred by user",
}

ALLOWED_LEGITIMACY = {"passed", "failed", "not checked"}
ALLOWED_CAPABILITY_RESULTS = {"supported", "supported with handoff", "unavailable"}
ALLOWED_COST_MODELS = {"free", "paid", "freemium", "unknown"}
TERMINAL_OR_PENDING = {
    "submitted",
    "submission outcome unknown",
    "awaiting approval",
    "awaiting email verification",
    "published",
}
EXECUTED = TERMINAL_OR_PENDING | {"form in progress", "draft saved"}
UNRESOLVED_VERIFICATION = {
    "awaiting manual verification",
    "verification expired/reset",
    "deferred by user",
}

TRACKING_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "ref", "referrer",
}
SENSITIVE_QUERY_KEYS = {
    "token", "key", "api_key", "apikey", "code", "state", "session",
    "auth", "password", "otp", "signature", "sig",
}

PLATFORM_HEADERS = [
    "platform_id", "platform_domain", "website_name", "canonical_submission_url",
    "route", "account_required", "verification_pattern", "cost_model",
    "reciprocal_requirement", "availability", "last_verified_at", "source",
    "notes", "row_version", "updated_at",
]

CAMPAIGN_HEADERS = [
    "campaign_id", "spd_version", "product_canonical_id", "canonical_url",
    "source_list_reference", "source_urls", "batch_authorization_reference",
    "execution_shard_size", "maximum_active_tabs", "host_platform",
    "ui_environment", "available_control_capabilities", "browser_routing_policy",
    "credential_policy", "evidence_policy", "duplicate_policy",
    "ambiguous_outcome_policy", "ranking_manipulation_prohibited", "created_at",
    "updated_at", "row_version",
]

SUBMISSION_HEADERS = [
    "campaign_id", "queue_id", "platform_id", "product_canonical_id", "website",
    "platform_domain", "route", "account_alias", "idempotency_key",
    "execution_shard", "platform_capability_result", "requested_browser_constraint",
    "selected_browser_surface", "execution_backend_session_alias",
    "backend_selection_reason", "legitimacy_gate", "authorization_reference",
    "status", "verification_preflight", "fields_entered", "fields_omitted",
    "agreements_subscriptions", "submit_timestamp", "exact_result",
    "evidence_reference", "public_listing_url", "backend_checked",
    "mailbox_checked", "public_page_checked", "last_checked", "follow_up",
    "created_at", "updated_at", "row_version",
]

EVENT_HEADERS = [
    "event_id", "campaign_id", "queue_id", "idempotency_key", "timestamp",
    "action", "result", "evidence_reference", "actor_alias",
]

TABLE_HEADERS = {
    "Platforms": PLATFORM_HEADERS,
    "Campaigns": CAMPAIGN_HEADERS,
    "Submissions": SUBMISSION_HEADERS,
    "Events": EVENT_HEADERS,
}

# Human-facing labels shown in row 1. The stable snake_case keys above remain
# authoritative for JSON input, validation, exports, and record processing.
HEADER_LABELS = {
    "platform_id": "平台编号", "platform_domain": "平台域名", "website_name": "平台名称",
    "canonical_submission_url": "标准提交入口", "route": "提交路线", "account_required": "是否需要账号",
    "verification_pattern": "验证方式", "cost_model": "收费模式", "reciprocal_requirement": "互链要求",
    "availability": "可用状态", "last_verified_at": "最后核验时间", "source": "信息来源",
    "notes": "备注", "row_version": "行版本", "updated_at": "更新时间",
    "campaign_id": "活动编号", "spd_version": "SPD 版本", "product_canonical_id": "产品编号",
    "canonical_url": "产品官网", "source_list_reference": "来源清单编号", "source_urls": "来源网址",
    "batch_authorization_reference": "批次授权编号", "execution_shard_size": "每批数量",
    "maximum_active_tabs": "最大标签页数", "host_platform": "运行系统", "ui_environment": "界面环境",
    "available_control_capabilities": "可用控制能力", "browser_routing_policy": "浏览器选择规则",
    "credential_policy": "凭据规则", "evidence_policy": "证据规则", "duplicate_policy": "去重规则",
    "ambiguous_outcome_policy": "结果不明处理规则", "ranking_manipulation_prohibited": "禁止操纵排名",
    "created_at": "创建时间", "queue_id": "队列编号", "website": "提交页面",
    "account_alias": "账号别名", "idempotency_key": "防重复键", "execution_shard": "执行批次",
    "platform_capability_result": "平台操作能力", "requested_browser_constraint": "指定浏览器要求",
    "selected_browser_surface": "实际浏览器界面", "execution_backend_session_alias": "执行会话别名",
    "backend_selection_reason": "选择执行方式的原因", "legitimacy_gate": "合规性检查",
    "authorization_reference": "授权编号", "status": "提交状态", "verification_preflight": "验证预检",
    "fields_entered": "已填写字段", "fields_omitted": "未填写字段", "agreements_subscriptions": "协议与订阅",
    "submit_timestamp": "提交时间", "exact_result": "准确结果", "evidence_reference": "证据编号",
    "public_listing_url": "公开页面网址", "backend_checked": "后台检查", "mailbox_checked": "邮箱检查",
    "public_page_checked": "公开页面检查", "last_checked": "最后检查时间", "follow_up": "后续处理",
    "event_id": "事件编号", "timestamp": "事件时间", "action": "操作", "result": "操作结果",
    "actor_alias": "操作者别名",
}


def display_headers(tab_name: str) -> list[str]:
    """Return readable row-1 labels while preserving field order."""
    return [HEADER_LABELS[header] for header in TABLE_HEADERS[tab_name]]

DROPDOWNS = {
    ("Submissions", "status"): sorted(ALLOWED_STATUSES),
    ("Submissions", "verification_preflight"): sorted(ALLOWED_VERIFICATION),
    ("Submissions", "legitimacy_gate"): sorted(ALLOWED_LEGITIMACY),
    ("Submissions", "platform_capability_result"): sorted(ALLOWED_CAPABILITY_RESULTS),
    ("Campaigns", "host_platform"): ["windows", "macos", "linux", "other"],
    ("Campaigns", "ui_environment"): ["desktop", "remote desktop", "headless", "unknown"],
    ("Platforms", "account_required"): ["yes", "no", "unknown"],
    ("Platforms", "cost_model"): sorted(ALLOWED_COST_MODELS),
    ("Platforms", "reciprocal_requirement"): ["none", "optional", "required", "unknown"],
    ("Platforms", "availability"): ["available", "unavailable", "unknown"],
}


class RecordValidationError(ValueError):
    """Raised when a record cannot safely enter the workbook."""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_url(value: str) -> str:
    try:
        parts = urlsplit(str(value).strip())
    except ValueError:
        return str(value).strip()
    host = (parts.hostname or "").lower()
    if not host:
        return str(value).strip()
    port = f":{parts.port}" if parts.port else ""
    query = [
        (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_KEYS
    ]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit(((parts.scheme or "https").lower(), host + port, path, urlencode(query), ""))


def _empty(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "none", "not applicable"}


def _not_submitted(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "not submitted", "not applicable"}


def _assert_iso(value: object, field: str, *, allow_sentinel: bool = False) -> None:
    text = str(value or "").strip()
    if allow_sentinel and text.lower() in {"", "not submitted", "not checked", "not applicable"}:
        return
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordValidationError(f"{field} must be an ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise RecordValidationError(f"{field} must include a timezone")


def _check_sensitive(record: dict[str, object]) -> None:
    serialized = json.dumps(record, ensure_ascii=False)
    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", serialized, re.IGNORECASE):
        raise RecordValidationError("raw email address found; use a contact alias")
    if re.search(r"(?<![\w-])\+\d[\d\s().-]{7,}\d(?![\w-])", serialized):
        raise RecordValidationError("raw phone number found; use a contact alias")
    secret_key = re.compile(
        r"(?:password|passcode|otp|recovery[_ ]?code|cookie|session[_ ]?id|oauth[_ ]?code|magic[_ ]?link)",
        re.IGNORECASE,
    )
    for key, value in record.items():
        if secret_key.search(str(key)) and not _empty(value) and str(value).lower() != "redacted":
            raise RecordValidationError(f"secret-bearing field found: {key}")
        if isinstance(value, str):
            if re.search(
                r"(?:password|passcode|otp|recovery[_ ]?code|cookie|session[_ ]?id|"
                r"oauth[_ ]?code|magic[_ ]?link)\s*[:=]\s*(?!none\b|redacted\b)\S+",
                value,
                re.IGNORECASE,
            ):
                raise RecordValidationError("secret-bearing value found")
            for url in re.findall(r"https?://[^\s)>]+", value):
                query_keys = {key.lower() for key, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True)}
                if query_keys & SENSITIVE_QUERY_KEYS:
                    raise RecordValidationError("URL with sensitive authentication parameter found")


def validate_privacy(record: dict[str, object]) -> None:
    _check_sensitive(record)


def _require(record: dict[str, object], fields: list[str], kind: str) -> None:
    missing = [field for field in fields if field not in record or str(record[field]).strip() == ""]
    if missing:
        raise RecordValidationError(f"{kind} missing required fields: {', '.join(missing)}")


def _validate_managed_fields(record: dict[str, object], *, has_created_at: bool) -> None:
    if "row_version" in record:
        try:
            if int(record["row_version"]) < 1:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise RecordValidationError("row_version must be a positive integer") from exc
    if "updated_at" in record:
        _assert_iso(record["updated_at"], "updated_at")
    if has_created_at and "created_at" in record:
        _assert_iso(record["created_at"], "created_at")


def computed_idempotency_key(record: dict[str, object]) -> str:
    return "|".join(
        str(record.get(field, "")).strip()
        for field in ("platform_domain", "product_canonical_id", "account_alias", "route")
    )


def validate_platform(record: dict[str, object]) -> None:
    required = [field for field in PLATFORM_HEADERS if field not in {"row_version", "updated_at"}]
    _require(record, required, "platform")
    _check_sensitive(record)
    if record["account_required"] not in {"yes", "no", "unknown"}:
        raise RecordValidationError("invalid account_required")
    if record["cost_model"] not in ALLOWED_COST_MODELS:
        raise RecordValidationError("invalid cost_model")
    if record["reciprocal_requirement"] not in {"none", "optional", "required", "unknown"}:
        raise RecordValidationError("invalid reciprocal_requirement")
    if record["availability"] not in {"available", "unavailable", "unknown"}:
        raise RecordValidationError("invalid availability")
    url_domain = (urlsplit(normalize_url(str(record["canonical_submission_url"]))).hostname or "").lower()
    if url_domain != str(record["platform_domain"]).lower():
        raise RecordValidationError("platform_domain must match canonical_submission_url")
    _assert_iso(record["last_verified_at"], "last_verified_at", allow_sentinel=True)
    _validate_managed_fields(record, has_created_at=False)


def validate_campaign(record: dict[str, object]) -> None:
    generated = {"created_at", "updated_at", "row_version"}
    _require(record, [field for field in CAMPAIGN_HEADERS if field not in generated], "campaign")
    _check_sensitive(record)
    if record["spd_version"] != "V1 Batch":
        raise RecordValidationError("spd_version must be V1 Batch")
    if str(record["ranking_manipulation_prohibited"]).lower() != "yes":
        raise RecordValidationError("ranking_manipulation_prohibited must be yes")
    for field in ("execution_shard_size", "maximum_active_tabs"):
        try:
            if int(record[field]) < 1:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"{field} must be a positive integer") from exc
    if record["host_platform"] not in {"windows", "macos", "linux", "other"}:
        raise RecordValidationError("invalid host_platform")
    if record["ui_environment"] not in {"desktop", "remote desktop", "headless", "unknown"}:
        raise RecordValidationError("invalid ui_environment")
    if _empty(record["available_control_capabilities"]):
        raise RecordValidationError("available_control_capabilities must not be empty")
    if not urlsplit(str(record["canonical_url"])).hostname:
        raise RecordValidationError("canonical_url must be a public URL")
    source_urls = [item.strip() for item in str(record["source_urls"]).splitlines() if item.strip()]
    if not source_urls or any(not urlsplit(item).hostname for item in source_urls):
        raise RecordValidationError("source_urls must contain one or more newline-separated public URLs")
    _validate_managed_fields(record, has_created_at=True)


def validate_submission_state(record: dict[str, object]) -> None:
    status = str(record.get("status", ""))
    verification = str(record.get("verification_preflight", ""))
    if status not in ALLOWED_STATUSES:
        raise RecordValidationError(f"invalid status: {status}")
    if verification not in ALLOWED_VERIFICATION:
        raise RecordValidationError(f"invalid verification_preflight: {verification}")
    if record.get("legitimacy_gate") not in ALLOWED_LEGITIMACY:
        raise RecordValidationError("invalid legitimacy_gate")
    if record.get("platform_capability_result") not in ALLOWED_CAPABILITY_RESULTS:
        raise RecordValidationError("invalid platform_capability_result")
    if status in EXECUTED and record.get("platform_capability_result") == "unavailable":
        raise RecordValidationError("executed without a compatible platform capability")
    if status in EXECUTED and record.get("legitimacy_gate") != "passed":
        raise RecordValidationError("executed without a passed legitimacy gate")
    if status in EXECUTED and _empty(record.get("authorization_reference")):
        raise RecordValidationError("executed without an authorization reference")
    if status in EXECUTED and verification in UNRESOLVED_VERIFICATION:
        raise RecordValidationError("executed while verification remained unresolved")
    if status == "not attempted":
        if str(record.get("fields_entered", "")).strip().lower() not in {"none", ""}:
            raise RecordValidationError("not attempted but listing fields were entered")
        if str(record.get("agreements_subscriptions", "")).strip().lower() not in {"none", ""}:
            raise RecordValidationError("not attempted but agreements/subscriptions were selected")
        if not _not_submitted(record.get("submit_timestamp")):
            raise RecordValidationError("not attempted but has a submit timestamp")
    if status in TERMINAL_OR_PENDING:
        if _not_submitted(record.get("submit_timestamp")):
            raise RecordValidationError(f"{status} requires a submit timestamp")
        if str(record.get("exact_result", "")).strip().lower() in {"", "not attempted", "unknown"}:
            raise RecordValidationError(f"{status} requires an exact result")
        if _empty(record.get("evidence_reference")):
            raise RecordValidationError(f"{status} requires an evidence reference")
    if status == "submission outcome unknown":
        for field in ("backend_checked", "mailbox_checked", "public_page_checked"):
            if str(record.get(field, "")).strip().lower() in {"", "not applicable", "not checked"}:
                raise RecordValidationError(f"unknown outcome requires {field}")
    if status == "published" and _empty(record.get("public_listing_url")):
        raise RecordValidationError("published requires a public_listing_url")
    if status == "published" and not urlsplit(str(record.get("public_listing_url", ""))).hostname:
        raise RecordValidationError("published public_listing_url must be a public URL")
    _assert_iso(record.get("last_checked"), "last_checked")
    _assert_iso(record.get("submit_timestamp"), "submit_timestamp", allow_sentinel=True)


def validate_submission(record: dict[str, object]) -> None:
    generated = {"created_at", "updated_at", "row_version"}
    _require(record, [field for field in SUBMISSION_HEADERS if field not in generated], "submission")
    _check_sensitive(record)
    normalized = normalize_url(str(record["website"]))
    url_domain = (urlsplit(normalized).hostname or "").lower()
    if url_domain != str(record["platform_domain"]).lower():
        raise RecordValidationError("platform_domain must match website")
    expected_key = computed_idempotency_key(record)
    if record["idempotency_key"] != expected_key:
        raise RecordValidationError(f"idempotency_key must equal {expected_key}")
    validate_submission_state(record)
    _validate_managed_fields(record, has_created_at=True)


def validate_event(record: dict[str, object]) -> None:
    _require(record, EVENT_HEADERS, "event")
    _check_sensitive(record)
    _assert_iso(record["timestamp"], "timestamp")


def prepare_record(
    kind: str,
    record: dict[str, object],
    existing: dict[str, object] | None = None,
) -> dict[str, object]:
    prepared = {key: value for key, value in record.items() if value is not None}
    timestamp = now_iso()
    if kind == "platform":
        validate_platform(prepared)
        headers = PLATFORM_HEADERS
    elif kind == "campaign":
        validate_campaign(prepared)
        headers = CAMPAIGN_HEADERS
    elif kind == "submission":
        validate_submission(prepared)
        headers = SUBMISSION_HEADERS
    elif kind == "event":
        validate_event(prepared)
        return {key: str(prepared.get(key, "")) for key in EVENT_HEADERS}
    else:
        raise RecordValidationError(f"unknown record kind: {kind}")
    if existing:
        prepared["created_at"] = existing.get("created_at", timestamp)
        prepared["row_version"] = int(existing.get("row_version", 0) or 0) + 1
    else:
        if "created_at" in headers:
            prepared["created_at"] = timestamp
        prepared["row_version"] = 1
    prepared["updated_at"] = timestamp
    return {key: str(prepared.get(key, "")) for key in headers}


def row_values(headers: list[str], record: dict[str, object]) -> list[object]:
    return [record.get(header, "") for header in headers]


def rows_to_records(headers: list[str], rows: list[list[object]]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in rows:
        padded = list(row) + [""] * (len(headers) - len(row))
        records.append({header: str(padded[index]) for index, header in enumerate(headers)})
    return records


def audit_records(
    campaigns: list[dict[str, object]],
    submissions: list[dict[str, object]],
    events: list[dict[str, object]],
    platforms: list[dict[str, object]],
    campaign_id: str | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    selected_campaigns = [item for item in campaigns if not campaign_id or item.get("campaign_id") == campaign_id]
    selected_submissions = [
        item for item in submissions
        if not campaign_id or str(item.get("campaign_id", "")) == campaign_id
    ]
    selected_events = [
        item for item in events
        if not campaign_id or str(item.get("campaign_id", "")) == campaign_id
    ]

    all_submission_keys: dict[str, list[dict[str, object]]] = {}
    for item in submissions:
        all_submission_keys.setdefault(str(item.get("idempotency_key", "")), []).append(item)
    for key, matches in all_submission_keys.items():
        if key and len(matches) > 1:
            errors.append(f"duplicate idempotency_key: {key}")

    all_event_ids: Counter[str] = Counter(str(item.get("event_id", "")) for item in events)
    for event_id, count in all_event_ids.items():
        if event_id and count > 1:
            errors.append(f"duplicate event_id: {event_id}")

    all_campaign_ids: Counter[str] = Counter(str(item.get("campaign_id", "")) for item in campaigns)
    for existing_campaign_id, count in all_campaign_ids.items():
        if existing_campaign_id and count > 1:
            errors.append(f"duplicate campaign_id: {existing_campaign_id}")

    if campaign_id and not selected_campaigns:
        errors.append(f"campaign not found: {campaign_id}")
    campaign_map: dict[str, dict[str, object]] = {}
    for item in selected_campaigns:
        key = str(item.get("campaign_id", ""))
        campaign_map[key] = item
        try:
            validate_campaign(item)
        except RecordValidationError as exc:
            errors.append(f"campaign {key}: {exc}")

    platform_map: dict[str, dict[str, object]] = {}
    for item in platforms:
        key = str(item.get("platform_id", ""))
        if key in platform_map:
            errors.append(f"duplicate platform_id: {key}")
        platform_map[key] = item
        try:
            validate_platform(item)
        except RecordValidationError as exc:
            errors.append(f"platform {key}: {exc}")

    seen_campaign_urls: set[tuple[str, str]] = set()
    status_counts: Counter[str] = Counter()
    verification_counts: Counter[str] = Counter()
    shard_counts: Counter[str] = Counter()
    manual_queue: list[str] = []
    submission_pairs: set[tuple[str, str]] = set()
    for item in selected_submissions:
        key = str(item.get("idempotency_key", ""))
        label = f"{item.get('campaign_id', '')}/{item.get('queue_id', '')}"
        pair = (str(item.get("campaign_id", "")), str(item.get("queue_id", "")))
        if pair in submission_pairs:
            errors.append(f"duplicate campaign/queue pair: {pair[0]}/{pair[1]}")
        submission_pairs.add(pair)
        normalized_pair = (pair[0], normalize_url(str(item.get("website", ""))))
        if normalized_pair in seen_campaign_urls:
            errors.append(f"duplicate normalized website in campaign: {normalized_pair[1]}")
        seen_campaign_urls.add(normalized_pair)
        if str(item.get("campaign_id", "")) not in campaign_map:
            errors.append(f"{label}: unknown campaign_id")
        elif str(item.get("product_canonical_id", "")) != str(campaign_map[pair[0]].get("product_canonical_id", "")):
            errors.append(f"{label}: product_canonical_id does not match campaign")
        platform_id = str(item.get("platform_id", ""))
        if platform_id not in platform_map:
            errors.append(f"{label}: unknown platform_id")
        elif str(item.get("platform_domain", "")).lower() != str(
            platform_map[platform_id].get("platform_domain", "")
        ).lower():
            errors.append(f"{label}: platform_domain does not match platform")
        try:
            validate_submission(item)
        except RecordValidationError as exc:
            errors.append(f"{label}: {exc}")
        status = str(item.get("status", "missing"))
        verification = str(item.get("verification_preflight", "missing"))
        status_counts[status] += 1
        verification_counts[verification] += 1
        shard_counts[str(item.get("execution_shard", "missing"))] += 1
        if verification in UNRESOLVED_VERIFICATION:
            manual_queue.append(label)

    last_event_time: dict[str, datetime] = {}
    for item in selected_events:
        event_id = str(item.get("event_id", ""))
        key = str(item.get("idempotency_key", ""))
        matches = all_submission_keys.get(key, [])
        if not matches:
            errors.append(f"event {event_id}: unknown idempotency_key")
        elif not any(
            str(match.get("campaign_id", "")) == str(item.get("campaign_id", ""))
            and str(match.get("queue_id", "")) == str(item.get("queue_id", ""))
            for match in matches
        ):
            errors.append(f"event {event_id}: campaign_id or queue_id does not match submission")
        try:
            validate_event(item)
            event_time = datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00"))
            if key in last_event_time and event_time < last_event_time[key]:
                errors.append(f"event {event_id}: timestamp moves backward")
            last_event_time[key] = event_time
        except RecordValidationError as exc:
            errors.append(f"event {event_id}: {exc}")

    event_keys = {str(item.get("idempotency_key", "")) for item in selected_events}
    for item in selected_submissions:
        if str(item.get("status", "")) in EXECUTED and str(item.get("idempotency_key", "")) not in event_keys:
            errors.append(
                f"{item.get('campaign_id', '')}/{item.get('queue_id', '')}: executed state requires an event"
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "total_sites": len(selected_submissions),
        "status_counts": dict(sorted(status_counts.items())),
        "verification_counts": dict(sorted(verification_counts.items())),
        "shard_counts": dict(sorted(shard_counts.items())),
        "manual_verification_queue": manual_queue,
    }


def export_campaign_markdown(
    campaign: dict[str, object],
    submissions: list[dict[str, object]],
    events: list[dict[str, object]],
) -> str:
    control_labels = [
        ("SPD version", "spd_version"), ("Campaign ID", "campaign_id"),
        ("Product canonical ID", "product_canonical_id"), ("Canonical URL", "canonical_url"),
        ("Source-list reference", "source_list_reference"),
        ("Batch authorization reference", "batch_authorization_reference"),
        ("Execution-shard size", "execution_shard_size"),
        ("Maximum active tabs", "maximum_active_tabs"), ("Host platform", "host_platform"),
        ("UI environment", "ui_environment"),
        ("Available control capabilities", "available_control_capabilities"),
        ("Browser-routing policy", "browser_routing_policy"),
        ("Credential policy", "credential_policy"), ("Evidence policy", "evidence_policy"),
        ("Duplicate policy", "duplicate_policy"),
        ("Ambiguous-outcome policy", "ambiguous_outcome_policy"),
        ("Ranking manipulation prohibited", "ranking_manipulation_prohibited"),
    ]
    lines = [
        f"# {campaign['campaign_id']} — SPD V1 Batch Record", "",
        f"Last updated: {campaign['updated_at']}", "", "## Campaign controls", "",
    ]
    lines.extend(f"- {label}: {campaign.get(key, '')}" for label, key in control_labels)
    lines.extend(["", "## Source list", ""])
    source_urls = [item.strip() for item in str(campaign.get("source_urls", "")).splitlines() if item.strip()]
    lines.extend(f"{index}. {url}" for index, url in enumerate(source_urls, start=1))

    site_labels = [
        ("Queue ID", "queue_id"), ("Website", "website"), ("Platform domain", "platform_domain"),
        ("Route", "route"), ("Account alias", "account_alias"),
        ("Idempotency key", "idempotency_key"), ("Execution shard", "execution_shard"),
        ("Platform capability result", "platform_capability_result"),
        ("Requested browser constraint", "requested_browser_constraint"),
        ("Selected browser surface", "selected_browser_surface"),
        ("Execution backend/session alias", "execution_backend_session_alias"),
        ("Backend selection reason", "backend_selection_reason"),
        ("Legitimacy gate", "legitimacy_gate"),
        ("Authorization reference", "authorization_reference"), ("Status", "status"),
        ("Verification preflight", "verification_preflight"),
        ("Fields entered", "fields_entered"), ("Fields omitted", "fields_omitted"),
        ("Agreements/subscriptions", "agreements_subscriptions"),
        ("Submit timestamp", "submit_timestamp"), ("Exact result", "exact_result"),
        ("Evidence reference", "evidence_reference"),
        ("Public listing URL", "public_listing_url"), ("Backend checked", "backend_checked"),
        ("Mailbox checked", "mailbox_checked"), ("Public page checked", "public_page_checked"),
        ("Last checked", "last_checked"), ("Follow-up", "follow_up"),
    ]
    for submission in submissions:
        lines.extend(["", f"## {submission['queue_id']} — {submission['platform_domain']}", ""])
        lines.extend(f"- {label}: {submission.get(key, '')}" for label, key in site_labels)
        lines.extend(["", "### Attempt log", ""])
        related = [item for item in events if item.get("idempotency_key") == submission.get("idempotency_key")]
        if related:
            for event in related:
                lines.append(
                    f"- {event['timestamp']} | event_id={event['event_id']} | action={event['action']} "
                    f"| result={event['result']} | evidence={event['evidence_reference']}"
                )
        else:
            lines.append("- none")
    return "\n".join(lines) + "\n"
