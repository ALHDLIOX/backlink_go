---
name: submit-product-directories-v1-batch
description: SPD V1 Batch. Process large, user-supplied sets of legitimate product, software, startup, app, and AI-tool directory URLs across Windows, macOS, and Linux-capable environments through normalization, deduplication, execution sharding, verification-first queues, authorization-controlled form work, idempotent submission, recovery, and truthful throughput reporting. Use when coverage and operational throughput matter more than deep per-site quality analysis. Do not use for ranking manipulation, bulk link spam, invented data, CAPTCHA bypass, paid-link acquisition, forced reciprocal links, or routes prohibited by a site's terms.
---

# SPD V1 Batch — large-batch directory operations

## Version identity

- Canonical name: `SPD V1 Batch`.
- Invocation: `$submit-product-directories-v1-batch`.
- Optimize for queue throughput, repeatability, verification handling, and recovery across large source lists.
- Apply a fast legitimacy gate, not the deeper editorial and referral-value analysis used by `$submit-product-directories-v2-quality`.
- Route campaigns requiring careful site selection, durable-placement analysis, or SEO-quality evidence to V2 Quality.

## Load controls

1. Resolve the product package from `../products/<product-id>/` and read its verified product profile, brand rules, approved asset manifest, source list, batch authorization, and existing campaign state. Resolve real contact and credential values only from the project-local ignored `.backlink-go/private/product-aliases.json`; place only aliases in Sheets and logs. See [references/product-packages.md](references/product-packages.md).
2. Read [references/workflow.md](references/workflow.md) before planning or browser work.
3. Read [references/status-model.md](references/status-model.md) before writing or auditing records.
4. Read [references/browser-control-routing.md](references/browser-control-routing.md) before any browser or app interaction. Run the Windows/macOS/Linux capability preflight and select the backend from the current environment; do not assume a specific browser, operating system, or Computer Use support.
5. Read [references/sheets-recording.md](references/sheets-recording.md) before the first record operation. Run `uv run python scripts/sheets_record.py doctor` before processing the queue.

Google Sheets is the only writable V1 record store. Use the bundled CLI for authentication, initialization, validation, lookup, writes, audits, and Markdown exports. Do not call a Google Sheets connector, read its plugin documentation, hand-author spreadsheet requests, or maintain a second writable Markdown record. Stop on missing OAuth, unavailable API access, or schema drift.

Workbook row-one labels are readable Chinese business names, with audit-critical columns first and system fields last. Fixed-choice cells use low-saturation status colors; other cells use a light neutral background. JSON inputs and internal validation continue to use the documented snake_case field keys. Run `uv run python scripts/sheets_record.py format-workbook` to restore labels, gridlines, frozen panes, widths, and styling after manual formatting changes.

The current workbook schema is version 7. If `doctor` reports schema 4, 5, or 6, run `uv run python scripts/sheets_record.py migrate-schema-v7` once. The migration combines directory, article, and social results into `Placements`, removes retired content-specific columns, preserves operational evidence, and keeps business timestamps at local `YYYY-MM-DD HH:MM` precision.

Never invent product, company, founder, pricing, address, launch, ownership, contact, or legal facts. Keep optional unknowns blank and block required unknowns.

## Apply the batch legitimacy gate

Reject or separate any route that is irrelevant to the product, unavailable, unreleased-only, paid-link-only, forced-reciprocal, a known low-quality directory network, or prohibited for automated form work. Do not select sites because they promise dofollow links, ranking gains, DA/DR, or backlink volume.

Use only the exact brand, product name, or naked canonical URL as public link text. Never request dofollow treatment or use repeated commercial exact-match anchors.

## Build the queue

1. Normalize hostnames and submission routes. Strip tracking parameters from the record while preserving required route parameters in controlled evidence.
2. Assign a stable placement ID and derive the idempotency key from platform domain, product canonical ID, account alias, route, and placement ID.
3. Deduplicate before opening the browser. Never execute an idempotency key that is already submitted, awaiting approval, published, or outcome unknown.
4. Assign stable queue IDs and execution shards. Treat shard size and current browser capacity as operational settings, not SEO safety thresholds.
5. Classify every site into `direct form`, `account required`, `manual verification`, `email verification`, `paid/reciprocal`, `unavailable`, `ineligible`, or `unknown`.
6. Use batch-scoped authorization only when it names the allowed actions, source-list scope, approver alias, approval time, and expiry. Payments, reciprocal-site changes, DNS changes, and publication outside a directory require separate authorization.

## Run the verification-first pipeline

1. Run a read-only preflight over each shard before entering product-listing fields.
2. Expose the earliest native CAPTCHA, Turnstile, image code, email check, login, or similar safeguard.
3. Attempt only the site's ordinary native automatic verification. Never bypass, outsource, or weaken a safeguard.
4. Move unresolved items to one manual queue and continue processing eligible sites.
5. After the user completes the queue, recheck token validity and process short-lived tokens first.
6. Do not hold more active challenge tabs than the configured browser capacity.

## Execute forms at scale

1. Process only sites that passed the legitimacy gate, authorization check, duplicate check, and verification prerequisite.
2. Reuse approved field variants by length and category, while preserving exact public brand spelling and truthful meaning.
3. Keep newsletters and optional promotions off unless authorized.
4. Review plan, cost, URL, identity, category, agreements, uploads, and verification immediately before submission.
5. Submit sequentially within a browser profile. Append the action event and upsert the result with `upsert-placement` before advancing the queue cursor.
6. Never retry an ambiguous final action. Check the account backend, mailbox, and public page first.
7. Save drafts, transient failures, manual actions, and terminal outcomes as distinct states so the campaign can resume without replaying completed work.

## Protect records

- Store aliases and controlled evidence IDs, not passwords, OTPs, recovery codes, cookies, OAuth parameters, magic links, raw session IDs, raw email addresses, phone numbers, or tokenized URLs.
- Separate the shareable campaign record from controlled evidence.
- Treat a click, registration, draft, cleared form, or generic thank-you URL as insufficient submission evidence.

## Close and measure

Run from the skill directory:

On macOS or Linux:

```bash
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
```

Report totals by queue state, verification state, shard, and outcome. Measure queue completion rate, verified submissions per operator hour, duplicate avoidance, recovery rate, and unresolved manual workload. Report published listings separately from submitted forms. Do not report submission volume as proof of SEO value.

## Bundled resources

- [references/product-packages.md](references/product-packages.md): project-local product packages and private alias resolution.
- [references/workflow.md](references/workflow.md): sharding, verification queues, execution, and recovery.
- [references/status-model.md](references/status-model.md): record schema and state invariants.
- [references/sheets-recording.md](references/sheets-recording.md): direct Google API setup, fixed CLI, JSON payloads, dry runs, audit, and export.
- [references/browser-control-routing.md](references/browser-control-routing.md): backend-neutral browser selection, interaction, confirmation, recovery, and evidence rules.
- `scripts/sheets_record.py`: authoritative Google Sheets record CLI.
- `scripts/record_model.py`: shared schema, privacy, state, audit, and export rules.
