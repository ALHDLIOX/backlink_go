# Google Sheets recording

Use only the bundled CLI. Never use a Sheets connector or hand-edit rows as an execution method.

```bash
uv run python scripts/sheets_record.py doctor
uv run python scripts/sheets_record.py migrate-schema-v7
uv run python scripts/sheets_record.py format-workbook
uv run python scripts/sheets_record.py upsert-platform --input platform.json
uv run python scripts/sheets_record.py upsert-campaign --input campaign.json
uv run python scripts/sheets_record.py upsert-placement --input placement.json
uv run python scripts/sheets_record.py append-event --input event.json
uv run python scripts/sheets_record.py placement-history --product-id PRODUCT_ID --json
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
uv run python scripts/sheets_record.py export-md --campaign-id CAMPAIGN_ID --output record.md
```

All upsert and event commands accept `--dry-run`; dry run validates without Google access. `doctor` checks OAuth, workbook identity, schema 7, and exact headers. Migration accepts schema 4/5/6, combines old result tabs into `Placements`, rewrites event keys, deletes retired tabs, and verifies the new workbook.

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
