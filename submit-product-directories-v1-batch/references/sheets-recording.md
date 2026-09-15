# Backlink Operations Google Sheets recording

Use `scripts/sheets_record.py` for every V1 record operation. It owns OAuth, schema validation, row lookup, deduplication, writes, reconciliation, readback, audit, and export. Do not call a Google Sheets connector, inspect its plugin documentation, hand-author requests, or keep a second writable Markdown record.

## Setup and migration

From this skill directory:

```bash
uv run python scripts/sheets_record.py auth --client-secret /approved/local/path/client-secret.json
uv run python scripts/sheets_record.py init --title "Backlink Operations"
uv run python scripts/sheets_record.py doctor
```

Existing schema-4 workbooks require one migration:

```bash
uv run python scripts/sheets_record.py migrate-schema-v5
uv run python scripts/sheets_record.py doctor
uv run python scripts/sheets_record.py format-workbook
```

Migration preserves directory data, assigns `platform_type: directory`, maps campaigns to `workflow_version: SPD V1 Batch` and `campaign_mode: directory`, assigns old events `record_type: submission`, and creates an empty `Articles` sheet. Initialization creates all five sheets. Business timestamps accept ISO-8601 input and are displayed as local `YYYY-MM-DD HH:MM`.

Authentication and workbook configuration live in the ignored project directory `.backlink-go/runtime/`. `BACKLINK_GO_CONFIG_DIR` or `--config-dir` may override it. Stop on authentication, schema, API, or readback errors; do not fall back to plugin or Markdown writes.

## Dry runs

All record writes validate locally with `--dry-run` and do not load OAuth or contact Google:

```bash
uv run python scripts/sheets_record.py upsert-platform --input platform.json --dry-run
uv run python scripts/sheets_record.py upsert-campaign --input campaign.json --dry-run
uv run python scripts/sheets_record.py upsert-submission --input submission.json --dry-run
uv run python scripts/sheets_record.py upsert-article --input article.json --dry-run
uv run python scripts/sheets_record.py append-event --input event.json --dry-run
```

Dry-run output contains only the command, stable key, validation result, `network_access: false`, and `deduplication_checked: false`. It never prints the full record. A dry run does not prove workbook uniqueness or authorize execution.

## Write order

1. Run `doctor`.
2. Upsert Campaign, then the live-preflighted Platform.
3. Create the Submission or Article queue item.
4. For every meaningful action, append the correctly typed Event first, then update the matching record using its current row version.
5. Advance the cursor only after both writes pass readback.
6. Run campaign audit before closing.

One local file lock enforces a single writer process. Browser work may be sharded, but record writes must remain sequential.

## Shared payloads

JSON uses the snake_case field keys below; row-one Chinese labels are presentation only. Omit generated `row_version` on create. To update a row, include `expected_row_version` from the prior CLI result.

`platform_domain` must exactly match the normalized hostname of `canonical_submission_url` or `website`, including a real `www` subdomain when present. For example, `https://www.blogger.com/...` uses `www.blogger.com`, not `blogger.com`.

Platform example:

```json
{
  "platform_id": "platform-example",
  "platform_domain": "example.com",
  "platform_type": "mixed",
  "website_name": "Example",
  "canonical_submission_url": "https://example.com/new",
  "route": "article editor",
  "account_required": "yes",
  "verification_pattern": "email verification",
  "cost_model": "free",
  "reciprocal_requirement": "none",
  "availability": "available",
  "last_verified_at": "2026-09-15 10:00",
  "source": "live inspection",
  "notes": ""
}
```

Campaign example:

```json
{
  "campaign_id": "campaign-example-001",
  "workflow_version": "Backlink Operations V1",
  "campaign_mode": "mixed",
  "product_canonical_id": "product-example",
  "canonical_url": "https://product.example/",
  "source_list_reference": "source-list-example-001",
  "source_urls": "https://directory.example/submit\nhttps://blog.example/new",
  "batch_authorization_reference": "auth-batch-example-001",
  "execution_shard_size": "10",
  "policy_version": "spd-v1-policy-2"
}
```

Schema-4 directory payloads using `"spd_version": "V1 Batch"` remain accepted and normalize to the directory workflow. Directory Submission keys and invariant remain unchanged. Its idempotency key is `platform_domain|product_canonical_id|account_alias|route`.

## Article payload

Compute a content fingerprint from a temporary JSON file. The CLI never prints or stores the body:

```bash
uv run python scripts/sheets_record.py fingerprint-article --input /private/tmp/article-fingerprint.json
```

The input object contains the working `title`, `body`, and `target_url`. Delete it after the editor draft or publication result is recorded.

Article example:

```json
{
  "platform_domain": "blog.example",
  "website": "https://blog.example/new",
  "status": "not attempted",
  "title": "A useful, platform-specific article title",
  "public_url": "not applicable",
  "target_url": "https://product.example/",
  "anchor_text": "not applicable",
  "outbound_href": "not applicable",
  "outbound_rel": "not applicable",
  "exact_result": "not attempted",
  "follow_up": "write and open editor",
  "verification_preflight": "not checked",
  "published_at": "not applicable",
  "last_checked": "2026-09-15 10:00",
  "article_id": "article-example-001",
  "queue_id": "A-001",
  "product_canonical_id": "product-example",
  "campaign_id": "campaign-example-001",
  "platform_id": "platform-blog-example",
  "route": "article editor",
  "account_alias": "account-example",
  "idempotency_key": "blog.example|product-example|account-example|article editor|article-example-001",
  "legitimacy_gate": "passed",
  "authorization_reference": "auth-batch-example-001",
  "evidence_reference": "not applicable",
  "content_fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "canonical_policy": "platform default",
  "backend_checked": "not applicable",
  "mailbox_checked": "not applicable",
  "public_page_checked": "not applicable",
  "outbound_link_checked": "not applicable",
  "execution_method": "connected browser",
  "execution_notes": "Queue item created; no editor action yet"
}
```

The article key is `platform_domain|product_canonical_id|account_alias|route|article_id`. Never include body, Markdown, HTML, real email, credentials, or tokenized URLs.

Read safe history before choosing a topic:

```bash
uv run python scripts/sheets_record.py article-history --product-id product-example --json
uv run python scripts/sheets_record.py article-history --product-id product-example --platform-domain blog.example --json
```

## Events

Every Event includes `record_type` and links to exactly one existing or proposed record:

```json
{
  "event_id": "evt-example-001",
  "record_type": "article",
  "campaign_id": "campaign-example-001",
  "queue_id": "A-001",
  "idempotency_key": "blog.example|product-example|account-example|article editor|article-example-001",
  "timestamp": "2026-09-15 10:05",
  "action": "editor opened",
  "result": "completed",
  "evidence_reference": "ev-example-001",
  "actor_alias": "operator-example"
}
```

Use `record_type: submission` for directory work and `record_type: article` for article work. Events are append-only. An identical event replay is idempotent; conflicting reuse of an event ID stops.

The CLI verifies that an authorization reference is present, but it cannot infer the actions allowed by a reference string. The orchestration skill must resolve the referenced project-local authorization and enforce its platform, account, action, and expiry scope before constructing an executed state.

## Audit and export

```bash
uv run python scripts/sheets_record.py audit --campaign-id campaign-example-001
uv run python scripts/sheets_record.py audit --campaign-id campaign-example-001 --json
uv run python scripts/sheets_record.py export-md --campaign-id campaign-example-001 --output /approved/path/campaign-example-001.md
```

Audit covers Submissions, Articles, and typed Events. Export includes operational article metadata but never article body. Google Sheets remains authoritative; do not import edited Markdown.
