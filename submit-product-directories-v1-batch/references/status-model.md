# SPD V1 Batch status model

Google Sheets is the authoritative V1 record store. The workbook schema version is `1` and contains exactly four worksheets. Use `scripts/sheets_record.py`; do not locate or write cells manually.

## Platforms

One reusable platform row may serve multiple products. Required fields are platform ID, normalized domain, website name, canonical submission URL, route, account requirement, verification pattern, cost model, reciprocal requirement, availability, last verification time, source, and notes. The script owns row version and update time.

Platform knowledge does not prove a product was submitted. Recheck changing availability, pricing, reciprocal requirements, terms, verification, and routes before reuse.

## Campaigns

Required campaign controls are:

- SPD version: `V1 Batch`
- Campaign ID, product canonical ID, and canonical URL
- Source-list reference and one or more newline-separated public source URLs
- Batch authorization reference
- Positive execution-shard size and maximum active tabs
- Host platform and UI environment
- Available control capabilities and browser-routing policy
- Credential, evidence, duplicate, and ambiguous-outcome policies
- `ranking_manipulation_prohibited: yes`

The script owns created time, updated time, and row version.

## Submissions

Each submission preserves:

- campaign ID, stable queue ID, platform ID, and product canonical ID;
- website, platform domain, route, account alias, and idempotency key;
- execution shard and browser/backend routing result;
- legitimacy gate and authorization reference;
- status and verification preflight;
- fields entered/omitted and agreements/subscriptions;
- submit timestamp, exact result, and evidence reference;
- public listing URL and backend/mailbox/public-page checks;
- last checked time and follow-up.

The script owns created time, updated time, and row version. It verifies campaign and platform references before writing.

## Events

Every meaningful action appends one immutable event with event ID, campaign ID, queue ID, idempotency key, timestamp, action, result, evidence reference, and actor alias. Event IDs are globally unique. An identical retry is idempotent; a retry with different content is a conflict.

An executed submission state must have at least one linked event. Append the event and then upsert the submission state before advancing the queue cursor.

## Canonical statuses

- `not attempted`
- `form in progress`
- `draft saved`
- `submitted`
- `submission outcome unknown`
- `awaiting approval`
- `awaiting email verification`
- `published`
- `blocked — manual verification`
- `blocked — missing verified data`
- `blocked — account or email policy`
- `unavailable`
- `paid-only`
- `ineligible`
- `duplicate — no action`
- `terminated by user`

## Verification states

- `not checked`
- `automatic verification passed`
- `awaiting manual verification`
- `manual verification completed`
- `verification unavailable before form`
- `verification expired/reset`
- `no verification presented`
- `deferred by user`

## Invariants

- The idempotency key is exactly `platform domain|product canonical ID|account alias|route` and is unique across the workbook. Different products can reuse one platform because their product IDs differ.
- Within a campaign, tracking-only variants of the same normalized submission URL are duplicates.
- Use `submitted`, `awaiting approval`, or `awaiting email verification` only with a submit timestamp, exact server acknowledgment, and evidence reference.
- Use `published` only after checking a public listing URL.
- Use `submission outcome unknown` after an ambiguous final action; do not retry until backend, mailbox, and public-page checks are recorded.
- Keep `not attempted` free of entered listing fields, agreements, and submit timestamps.
- Do not start or complete a form while verification is unresolved unless the site exposes verification only after mandatory form fields and the exception is recorded.
- Do not execute a failed legitimacy gate, unavailable platform capability, or missing authorization.
- Treat registration, login, draft save, navigation, a click, or a generic thank-you page as insufficient submission evidence.
- Never store raw email addresses, secrets, private session IDs, authentication URLs, or sensitive query parameters.
- Google writes use `RAW` values so text cannot become a formula. Do not change this input mode.
- Schema drift, a conflicting readback, or an ambiguous duplicate stops the write; never guess column positions or replay blindly.

## Audit and export

```bash
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
uv run python scripts/sheets_record.py export-md --campaign-id CAMPAIGN_ID --output /approved/path/record.md
```

The Markdown output is a read-only backup/review artifact. Do not import edits back into Google Sheets.
