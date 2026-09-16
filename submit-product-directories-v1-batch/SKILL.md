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

Start with this entrypoint. Do not preload every reference or every file in the product package.

1. Resolve `../products/<product-id>/` and initially read only the verified product profile, the selected source list, the applicable batch authorization, and existing campaign state. Load brand rules immediately before preparing public copy, the asset manifest only when an upload is required, and [references/product-packages.md](references/product-packages.md) only when package discovery or private alias resolution is needed. Resolve a real contact or credential value only when the current site requires its approved alias; never copy the raw value into Sheets or logs.
2. The workflow below is the normal execution contract. Load [references/workflow.md](references/workflow.md) only when detailed sharding, manual-verification, recovery, or closeout guidance is needed.
3. Load [references/status-model.md](references/status-model.md) immediately before constructing the first record payload, interpreting a status invariant, or auditing records; retain that loaded schema context for the rest of the batch.
4. Load [references/browser-control-routing.md](references/browser-control-routing.md) only when the current environment has no already verified browser binding, the user changes the requested surface, the environment changes, or the active binding fails. Reuse a verified binding within the batch.
5. Load [references/sheets-recording.md](references/sheets-recording.md) only for initial setup, migration, exact payload syntax, or a write/reconciliation failure. Run `uv run python scripts/sheets_record.py doctor` before processing the queue.

Google Sheets is the only writable V1 record store. Use the bundled CLI for authentication, initialization, validation, lookup, writes, audits, and Markdown exports. The same private OAuth token may use the bundled Gmail read-only commands for an explicit mailbox search or a single-message read; keep mail content transient and never copy it into the record store. Do not call a Google Sheets connector, read its plugin documentation, hand-author spreadsheet requests, or maintain a second writable Markdown record. Stop on missing OAuth, unavailable API access, or schema drift.

Workbook row-one labels are readable English business names, with audit-critical columns first and system fields last. Fixed-choice cells use bright, readable semantic text colors without colored fills; other cells use a light neutral background. JSON inputs and internal validation continue to use the documented snake_case field keys. Run `uv run python scripts/sheets_record.py format-workbook` to restore labels, gridlines, frozen panes, widths, and styling after manual formatting changes.

The current workbook schema is version 8. If `doctor` reports schema 4 through 7, run `uv run python scripts/sheets_record.py migrate-schema-v8` once. The migration combines legacy result tables into `Placements`, preserves operational evidence, puts the product ID first, and keeps business timestamps at local `YYYY-MM-DD HH:MM` precision.

Never invent product, company, founder, pricing, address, launch, ownership, contact, or legal facts. Keep optional unknowns blank and block required unknowns.

## Apply the batch legitimacy gate

Reject or separate any route that is irrelevant to the product, unavailable, unreleased-only, paid-link-only, forced-reciprocal, a known low-quality directory network, or prohibited for automated form work. Do not select sites because they promise dofollow links, ranking gains, DA/DR, or backlink volume.

Use only the exact brand, product name, or naked canonical URL as public link text. Never request dofollow treatment or use repeated commercial exact-match anchors.

## Build the queue

1. After `doctor` and Campaign resolution, run `placement-history --product-id PRODUCT_ID --json` exactly once for the product. The command returns complete Placement snapshots, including `row_version`. Build one in-memory history index for the batch and update it after each successful Placement readback. To update a cached Placement, copy its `row_version` to `expected_row_version`, remove `row_version`, change the intended business fields, and call `upsert-placement`. Do not repeat domain-scoped history calls for every source URL. Use a targeted refresh only after an interrupted resume, an ambiguous result, a detected external workbook edit, or another concrete reason the cached history may be stale.
2. Normalize hostnames and submission routes. Strip tracking parameters from the record while preserving required route parameters in controlled evidence.
3. Assign a stable placement ID and derive the idempotency key from platform domain, product canonical ID, account alias, route, and placement ID.
4. Deduplicate against both the normalized source list and the in-memory history index before opening the browser. Never execute an idempotency key that is already submitted, awaiting approval, published, or outcome unknown.
5. Assign stable queue IDs and execution shards. Treat shard size and current browser capacity as operational settings, not SEO safety thresholds.
6. Classify every site into `direct form`, `account required`, `manual verification`, `email verification`, `paid/reciprocal`, `unavailable`, `ineligible`, or `unknown`.
7. Use batch-scoped authorization only when it names the allowed actions, source-list scope, approver alias, approval time, and expiry. Payments, reciprocal-site changes, DNS changes, and publication outside a directory require separate authorization.

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

- Store aliases and controlled evidence IDs, not passwords, OTPs, recovery codes, cookies, OAuth parameters, magic links, raw session IDs, raw email addresses, phone numbers, tokenized URLs, or Gmail message content. Gmail command output is transient and must not be copied into Sheets, evidence, or repository files.
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
- `scripts/sheets_record.py`: authoritative Google Sheets record and Gmail read-only CLI.
- `scripts/record_model.py`: shared schema, privacy, state, audit, and export rules.
