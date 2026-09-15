---
name: backlink-operations-v1
description: Orchestrate authorized backlink operations across product directories, long-form publishing platforms, and social surfaces. Use when the user wants a truthful directory submission, article backlink, Pinterest Pin, X or LinkedIn post, with one unified Google Sheets placement record, anchor-text tracking, evidence, public-result verification, and audit.
---

# Backlink Operations V1

## Purpose

Classify each supplied destination, then run one controlled execution lane:

- Directory: load and follow `../submit-product-directories-v1-batch/SKILL.md`.
- Blog or long-form platform: load [references/article-publishing.md](references/article-publishing.md), `../writer/SKILL.md`, and `../writer/references/ephemeral-publishing.md`.
- Pinterest Pin, X/LinkedIn short post, image/link post, or thread: load [references/social-publishing.md](references/social-publishing.md).

The lane changes how the browser task is performed, not how it is recorded. All successful, pending, blocked, or skipped results use one `Placements` table. Do not persist a content type, title, body, image, Board/channel, AI label, split UTM fields, `rel`, Canonical policy, content fingerprint, or agreement/subscription details. Preserve the actual backlink destination and the actual anchor text. When a visual/link card has no textual anchor, record the truthful sentinel `not applicable — image or link card`.

Google Sheets is the only writable record source. Use only `../submit-product-directories-v1-batch/scripts/sheets_record.py`; never use a Sheets connector, locate cells manually, or keep a second writable Markdown log.

## Load and preflight

1. Resolve the verified product package from `../products/<product-id>/`. Resolve private values only from the ignored `../.backlink-go/private/product-aliases.json`; never copy raw values into records or output.
2. Read [references/routing.md](references/routing.md), classify the live destination, and load only the selected lane.
3. Run `uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py doctor` before record or browser work.
4. If schema 4 through 7 is reported, run `migrate-schema-v8`. Stop if OAuth, workbook identity, schema, or headers remain invalid.

## Authorization

Create or load a Campaign using `workflow_version: Backlink Operations V1`. A reusable batch authorization permits an action only when its source names the product/campaign, bounded platform scope, account alias, permitted actions, approver, approval time, and unexpired validity. `write`, `draft`, `schedule`, `publish`, and `upload` remain independent permissions. Payments, reciprocal links, DNS changes, and tool-enforced confirmations require separate authorization.

## Shared record order

1. Run `placement-history --product-id PRODUCT_ID [--platform-domain DOMAIN] --json` before executing.
2. Upsert the Campaign and reusable Platform facts. Platform rows describe access and cost facts only; they do not retain a content type.
3. Create one `Placements` queue row with `upsert-placement`. Generate a stable `placement_id`; use `platform_domain|product_canonical_id|account_alias|route|placement_id` as the idempotency key.
4. After every meaningful browser action, call `append-event`, then update the same Placement using `expected_row_version`.
5. Never replay an ambiguous final action. Check the account backend, mailbox, and public page, record a concise `verification` summary, and use `outcome unknown` until resolved.
6. Advance only after CLI readback succeeds. Run `audit --campaign-id CAMPAIGN_ID` at close.

Events no longer carry a record type because every event resolves to exactly one Placement. The CLI serializes writes with a local lock.

## Result standards

- A form acknowledgment is `submitted`, not `published`.
- A saved editor draft is `draft saved`.
- Mark `published` only after reopening the public page and verifying the result and actual backlink destination.
- Record the visible linked words as `anchor_text`. For an image or link card without linked words, use the explicit sentinel above; never invent anchor text.
- Use `ineligible`, `paid-only`, or the applicable blocked state when the route should not proceed.
- Never claim indexing, dofollow treatment, traffic, referral value, or ranking effect without separate evidence.

## Bundled resources

- [references/routing.md](references/routing.md): execution-lane classification.
- [references/article-publishing.md](references/article-publishing.md): long-form writing and publication.
- [references/social-publishing.md](references/social-publishing.md): short-social publication.
- `../submit-product-directories-v1-batch/references/status-model.md`: unified schema 8 fields and invariants.
- `../submit-product-directories-v1-batch/references/sheets-recording.md`: fixed CLI commands and JSON examples.
- `../writer/references/ephemeral-publishing.md`: transient article-writing rules.
