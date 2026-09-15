# SPD V1 Google Sheets recording

Use `scripts/sheets_record.py` for every V1 record operation. The script owns the Google API schema, OAuth, validation, deduplication, row lookup, write reconciliation, and readback verification. Do not call a Google Sheets connector, inspect its documentation, hand-author Sheets requests, or keep a second writable Markdown record.

## One-time setup

The user must create a Google Cloud desktop OAuth client with the Google Sheets API enabled and provide the downloaded client JSON. Never search for credentials or commit them.

From the skill directory:

```bash
uv run python scripts/sheets_record.py auth --client-secret /approved/local/path/client-secret.json
uv run python scripts/sheets_record.py init --title "Backlink Operations"
uv run python scripts/sheets_record.py doctor
```

Existing schema-v1 workbooks must be upgraded once before `doctor` or any write:

```bash
uv run python scripts/sheets_record.py migrate-schema-v2
```

The migration preserves existing rows, folds repeated campaign policies into `spd-v1-policy-2`, combines the five browser/backend columns into execution method and notes, and updates the workbook atomically.

To restore the workbook's readable Chinese headers and standard presentation:

```bash
uv run python scripts/sheets_record.py format-workbook
```

The visible header labels are presentation text. JSON payloads continue to use the snake_case keys shown below.

Authentication and workbook configuration are stored inside the repository checkout under `.backlink-go/runtime/` with private file permissions. The directory is ignored by Git. `BACKLINK_GO_CONFIG_DIR` or `--config-dir` may override this location. `init` creates one empty workbook with `Platforms`, `Campaigns`, `Submissions`, and `Events`; it does not import `Free-backlink-list.md`.

If authentication, configuration, schema, or API access fails, stop and report the exact non-secret error. Do not fall back to connector writes or a local Markdown source of truth.

## Dry runs

Every record write supports `--dry-run`. A dry run validates the JSON without loading OAuth, reading config, or contacting Google:

```bash
uv run python scripts/sheets_record.py upsert-platform --input platform.json --dry-run
uv run python scripts/sheets_record.py upsert-campaign --input campaign.json --dry-run
uv run python scripts/sheets_record.py upsert-submission --input submission.json --dry-run
uv run python scripts/sheets_record.py append-event --input event.json --dry-run
```

The OAuth command also supports a local-only validation pass: `uv run python scripts/sheets_record.py auth --client-secret client.json --dry-run`.

Do not expose the full input record in logs. Successful record dry-run output contains only the command, stable key, validation result, `network_access: false`, and `deduplication_checked: false`. Because dry-run must not access Google, compare stable keys within the proposed batch yourself; structural validity does not authorize execution or prove that the key is absent from the workbook.

## Record order

1. Run `doctor` once at the start of a campaign session.
2. Upsert the campaign before its submissions.
3. Upsert each platform after live preflight establishes reusable facts.
4. Upsert a submission before form execution.
5. Append an event after every meaningful action, then upsert the corresponding submission state.
6. Advance the queue cursor only after both writes pass readback verification.
7. Run `audit --campaign-id ...` before closing the batch.

The script uses one local writer lock. Do not run record writes concurrently on the same machine.

## JSON payloads

Use exact snake_case keys. Generated `created_at`, `updated_at`, and `row_version` fields must be omitted from input. Creating a row does not need a version. Replaying identical content returns `unchanged`. To change an existing row, include `expected_row_version` with the last version returned by the CLI; a stale or missing version stops the update.

### Platform

```json
{
  "platform_id": "platform-example",
  "platform_domain": "directory.example",
  "website_name": "Example Directory",
  "canonical_submission_url": "https://directory.example/submit",
  "route": "directory listing",
  "account_required": "yes",
  "verification_pattern": "email verification",
  "cost_model": "free",
  "reciprocal_requirement": "none",
  "availability": "available",
  "last_verified_at": "2026-09-15T10:00:00+08:00",
  "source": "live inspection",
  "notes": "none"
}
```

`source` and `notes` may be omitted when no useful value is available.

`account_required`: `yes`, `no`, or `unknown`. `cost_model`: `free`, `paid`, `freemium`, or `unknown`. `reciprocal_requirement`: `none`, `optional`, `required`, or `unknown`. `availability`: `available`, `unavailable`, or `unknown`.

### Campaign

```json
{
  "campaign_id": "campaign-example-001",
  "spd_version": "V1 Batch",
  "product_canonical_id": "product-example",
  "canonical_url": "https://product.example/",
  "source_list_reference": "source-list-example-001",
  "source_urls": "https://directory.example/submit",
  "batch_authorization_reference": "auth-batch-example-001",
  "execution_shard_size": "20",
  "policy_version": "spd-v1-policy-2"
}
```

Put one public source URL per line in `source_urls`. Do not include authentication or tracking parameters.

### Submission

```json
{
  "campaign_id": "campaign-example-001",
  "queue_id": "Q-001",
  "platform_id": "platform-example",
  "product_canonical_id": "product-example",
  "website": "https://directory.example/submit",
  "platform_domain": "directory.example",
  "route": "directory listing",
  "account_alias": "account-example",
  "idempotency_key": "directory.example|product-example|account-example|directory listing",
  "execution_shard": "shard-001",
  "execution_method": "connected browser",
  "execution_notes": "supported structured browser control",
  "legitimacy_gate": "passed",
  "authorization_reference": "auth-batch-example-001",
  "status": "not attempted",
  "verification_preflight": "not checked",
  "fields_entered": "none",
  "fields_omitted": "all",
  "agreements_subscriptions": "none",
  "submit_timestamp": "not submitted",
  "exact_result": "not attempted",
  "evidence_reference": "not applicable",
  "public_listing_url": "not applicable",
  "backend_checked": "not applicable",
  "mailbox_checked": "not applicable",
  "public_page_checked": "not applicable",
  "last_checked": "2026-09-15T10:00:00+08:00",
  "follow_up": "run verification preflight"
}
```

The idempotency key must exactly equal `platform_domain|product_canonical_id|account_alias|route`. A key already owned by another campaign cannot be reassigned. Different products may reuse the same platform because their product IDs produce different keys.

### Event

```json
{
  "event_id": "evt-example-001",
  "campaign_id": "campaign-example-001",
  "queue_id": "Q-001",
  "idempotency_key": "directory.example|product-example|account-example|directory listing",
  "timestamp": "2026-09-15T10:05:00+08:00",
  "action": "inspection",
  "result": "completed",
  "evidence_reference": "ev-example-001",
  "actor_alias": "operator-example"
}
```

Events are append-only. Replaying the same event ID with identical content is idempotent; different content is a conflict.

## Audit and export

```bash
uv run python scripts/sheets_record.py audit --campaign-id campaign-example-001
uv run python scripts/sheets_record.py audit --campaign-id campaign-example-001 --json
uv run python scripts/sheets_record.py export-md --campaign-id campaign-example-001 --output /approved/path/campaign-example-001.md
```

Google Sheets remains authoritative. Markdown is a read-only export for backup or review; never edit it and import it back.
