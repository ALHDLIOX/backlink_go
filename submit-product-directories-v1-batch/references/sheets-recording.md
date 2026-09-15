# Google Sheets recording

Use only the bundled CLI. Never use a Sheets connector or hand-edit rows as an execution method.

```bash
uv run python scripts/sheets_record.py doctor
uv run python scripts/sheets_record.py migrate-schema-v8
uv run python scripts/sheets_record.py format-workbook
uv run python scripts/sheets_record.py upsert-platform --input platform.json
uv run python scripts/sheets_record.py upsert-campaign --input campaign.json
uv run python scripts/sheets_record.py upsert-placement --input placement.json
uv run python scripts/sheets_record.py append-event --input event.json
uv run python scripts/sheets_record.py placement-history --product-id PRODUCT_ID --json
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
uv run python scripts/sheets_record.py export-md --campaign-id CAMPAIGN_ID --output record.md
```

All upsert and event commands accept `--dry-run`; dry run validates without Google access. `doctor` checks OAuth, workbook identity, schema 8, and exact headers. Migration accepts schema 4 through 7, combines legacy result tabs when necessary, moves the product ID to the first Placement column, and verifies the workbook. It never treats an intended campaign target as an observed backlink; published legacy rows without outbound-link evidence become `outcome unknown` pending revalidation.

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

Migration clears retained cell values before compacting rows, so blank source rows cannot leave stale trailing records. It reads back every migrated table before updating the local schema configuration. `doctor` can inspect schemas 4–7 and reports `migration_required`; schema 8 is current.

After an ambiguous update, a retry is allowed only if the original row content and physical address remain unchanged. A successful readback ends the operation without another write; changed, moved, deleted, or duplicate rows stop with an error. Placement history uses the same domain equivalence as validation (including `www`, trailing dots, and Unicode/punycode). Privacy validation inspects every HTTP(S) URL embedded in text, including multiple links in notes.
