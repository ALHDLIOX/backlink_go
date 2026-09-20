# Google Sheets recording

Use only the bundled CLI. Never use a Sheets connector or hand-edit rows as an execution method.

```bash
uv run python scripts/sheets_record.py auth --client-secret /path/to/client.json --replace
uv run python scripts/sheets_record.py init --title "Backlink Operations" --replace-existing-config
uv run python scripts/sheets_record.py doctor
uv run python scripts/sheets_record.py migrate-schema-v10
uv run python scripts/sheets_record.py format-workbook
uv run python scripts/sheets_record.py upsert-platform --input platform.json
uv run python scripts/sheets_record.py upsert-campaign --input campaign.json
uv run python scripts/sheets_record.py upsert-placement --input placement.json
uv run python scripts/sheets_record.py append-event --input event.json
uv run python scripts/sheets_record.py placement-history --product-id PRODUCT_ID --json
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
uv run python scripts/sheets_record.py export-md --campaign-id CAMPAIGN_ID --output record.md
uv run python scripts/sheets_record.py gmail-search --query 'newer_than:7d' --max-results 10
uv run python scripts/sheets_record.py gmail-read --message-id MESSAGE_ID
```

OAuth requests `drive.file` for the workbook created by this app and `gmail.readonly` for explicit mailbox reads. `auth --replace` backs up the active client, token, and workbook configuration before opening the account-selection consent flow; it activates the new client and token only after both scopes and a refresh token are present. `init --replace-existing-config` creates and verifies a new workbook before changing the local workbook pointer. Backups stay under the ignored private runtime directory with `0700` directories and `0600` files.

`gmail-search` requires an explicit Gmail query, returns at most 50 results, and fetches message metadata only. `gmail-read` reads one explicit message ID, prefers the plain-text body, converts HTML-only mail to text, truncates body output at 100 KiB, and lists attachment metadata without downloading attachment content. Mail content is transient command output; never write it to Sheets, records, evidence, or repository files.

All upsert and event commands accept `--dry-run`; dry run validates without Google access. `doctor` checks OAuth, workbook identity, schema 10, exact headers, and Gmail API access, reporting Sheets and Gmail separately. Migration accepts schema 4 through 9, combines legacy result tabs when necessary, moves the product ID to the first Placement column, and verifies the workbook. It never treats an intended campaign target as an observed backlink; published legacy rows without outbound-link evidence become `outcome unknown` pending revalidation.

For normal batch execution, call `placement-history --product-id PRODUCT_ID --json` once after `doctor` and Campaign resolution. It returns complete Placement snapshots, including `row_version`. Build an in-memory index from those rows, use that index for all source URLs, and update it from every successful Placement readback. To update an existing Placement, copy the snapshot's `row_version` to `expected_row_version`, remove `row_version`, change the intended business fields, and pass the resulting full payload to `upsert-placement`. `--platform-domain` is a targeted refresh for interrupted, ambiguous, or externally changed state; it is not the default per-destination lookup pattern.

Minimal Placement JSON:

```json
{
  "platform_domain": "example.com",
  "website": "https://example.com/create",
  "status": "not attempted",
  "public_url": "not applicable",
  "backlink_url": "https://product.example/",
  "anchor_text": "not checked",
  "exact_result": "not attempted",
  "follow_up": "open the destination",
  "verification": "not checked",
  "action_at": "not submitted",
  "last_checked": "2026-09-15 16:00",
  "placement_id": "example-product-001",
  "queue_id": "Q-001",
  "product_canonical_id": "product-example",
  "campaign_id": "campaign-example",
  "platform_id": "platform-example",
  "route": "create",
  "account_alias": "account-primary",
  "idempotency_key": "example.com|product-example|account-primary|create|example-product-001",
  "authorization_reference": "auth-example",
  "evidence_reference": "not applicable",
  "execution_method": "connected browser",
  "execution_notes": "queued"
}
```

Append the Event before changing a Placement into an executed state. Updating an existing row requires `expected_row_version`. Ambiguous writes are reconciled by readback and retried at most once. Raw emails, credentials, OTPs, cookies, tokens, and sensitive URLs are forbidden.

## Python module layout

`scripts/sheets_record.py` remains the CLI entry point. `scripts/record_model.py` retains compatibility imports. New implementation code belongs in `scripts/backlink_records/`:

- `model.py`: schema fields, states, validation, normalization, and serialization.
- `credentials.py`: OAuth, private configuration, and the local writer lock.
- `sheets_store.py`: Sheets CRUD and physical row addresses.
- `formatting.py`: headers, colors, widths, filters, and frozen rows.
- `migrations/v4_to_v8.py` through `v7_to_v8.py`: version-specific record transforms; `migrations/runner.py` applies and verifies the workbook migration.
- `operations.py`: upserts, events, history, audit, and doctor diagnostics.
- `reconciliation.py`: bounded write retries, readback, and conflict detection.
- `cli.py`: argument parsing and output.

Migration first saves a private snapshot of source records, metadata, and configuration. Schema 9 inserts Cost Detail after Cost Model and adds the waiting badge status; existing Notes remain intact and legacy Cost Detail stays blank until verified. Migration clears retained cell values before compacting rows, so blank source rows cannot leave stale trailing records. It reads back every migrated table before updating the local schema configuration. `doctor` can inspect schemas 4–9 and reports `migration_required`; schema 10 is current.

After an ambiguous update, a retry is allowed only if the original row content and physical address remain unchanged. A successful readback ends the operation without another write; changed, moved, deleted, or duplicate rows stop with an error. Placement history uses the same domain equivalence as validation (including `www`, trailing dots, and IDNA2008 Unicode/punycode forms). Privacy validation inspects every HTTP(S) URL embedded in text, including multiple links in notes, and rejects URL authority credentials such as `user:password@host`.

For a historical `awaiting approval` row whose evidence explicitly proves no submission occurred, append an Event with action `correct unsubmitted status` explaining the old misclassification. Use `upsert-placement --correction-event-id EVENT_ID --input placement.json` to correct it to `waiting badge`. Supply the same evidence reference, current expected row version, `action_at: not submitted`, and the required badge follow-up. The CLI rejects other source/target states, missing or unrelated correction events, and existing public/backlink URLs. Do not use this to reopen real submissions. Dry run validates only the payload; live correction additionally checks the prior state and linked event.

Use `wrap-platform-notes` to set Cost Detail, Verification Pattern, and Notes to WRAP and LEFT alignment across the Platforms columns. This command changes only wrap strategy and horizontal alignment and verifies that the existing column widths are unchanged.
