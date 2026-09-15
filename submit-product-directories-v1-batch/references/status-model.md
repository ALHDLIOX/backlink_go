# Backlink Operations schema 5 status model

Google Sheets is the authoritative V1 record store. Schema version `5` contains `Platforms`, `Campaigns`, `Submissions`, `Articles`, and `Events`. SPD V1 Batch writes directory records to `Submissions`; `Articles` is owned by the sibling `backlink-operations-v1` orchestration skill. Use `scripts/sheets_record.py`; never locate or write cells manually. Business timestamps are stored at local minute precision as `YYYY-MM-DD HH:MM`.

## Platforms

One reusable platform row may serve multiple products and both placement types. Required fields describe the normalized domain, canonical route, account and verification requirements, cost, reciprocal requirements, current availability, and last verification time. `platform_type` is one of `directory`, `article`, `mixed`, `social`, or `unknown`. The script owns `row_version`.

Platform knowledge does not prove that a product was submitted or an article was published. Recheck changing availability, pricing, terms, verification, content policy, and routes before reuse.

## Campaigns

A campaign stores product identity, source URLs, authorization, shard size, policy version, workflow version, and campaign mode. Directory V1 campaigns use:

- `workflow_version: SPD V1 Batch`
- `campaign_mode: directory`
- `policy_version: spd-v1-policy-2`

The schema-4 input pair `spd_version: V1 Batch` remains accepted and is normalized to those values. New mixed or article campaigns use `workflow_version: Backlink Operations V1` with `campaign_mode: mixed` or `article`. The script owns `row_version`.

## Submissions

Each directory submission preserves the product/platform/campaign identity, route, account alias, directory idempotency key, execution and authorization context, status, verification, exact result, evidence, public listing, follow-up checks, and row version.

The directory idempotency key is exactly `platform_domain|product_canonical_id|account_alias|route`. Different products can reuse one platform because their product IDs differ.

## Articles

`Articles` holds operational metadata only: platform, status, title, public result, target link, actual anchor/href/rel, verification checks, identifiers, authorization, evidence, SHA-256 content fingerprint, canonical policy, execution notes, and row version. Article body, HTML, Markdown, credentials, and raw contact data are forbidden.

The article idempotency key is exactly `platform_domain|product_canonical_id|account_alias|route|article_id`. `article_id` is globally unique. The same product may publish distinct platform-adapted articles with distinct IDs and content, but duplicate content fingerprints are rejected across that product's article history.

Article statuses are:

- `not attempted`, `writing`, `editor in progress`, `draft saved`
- `submitted for review`, `published`, `publication outcome unknown`
- `awaiting email verification`
- `blocked — manual verification`, `blocked — missing verified data`, `blocked — account or email policy`
- `rejected`, `removed`, `unavailable`, `paid-only`, `ineligible`
- `duplicate — no action`, `terminated by user`

## Events

Every meaningful action appends one immutable event with `record_type: submission` or `record_type: article`, plus event ID, campaign ID, queue ID, idempotency key, time, action, result, evidence reference, and actor alias. Event IDs are globally unique. An identical replay is idempotent; different content is a conflict.

An executed record must have at least one correctly typed linked event. Append the event first, then upsert the matching Submission or Article state before advancing the queue cursor.

## Directory statuses and verification states

Directory statuses remain:

- `not attempted`, `form in progress`, `draft saved`, `submitted`
- `submission outcome unknown`, `awaiting approval`, `awaiting email verification`, `published`
- `blocked — manual verification`, `blocked — missing verified data`, `blocked — account or email policy`
- `unavailable`, `paid-only`, `ineligible`, `duplicate — no action`, `terminated by user`

Verification values shared by both record types are:

- `not checked`, `automatic verification passed`, `awaiting manual verification`
- `manual verification completed`, `verification unavailable before form`
- `verification expired/reset`, `no verification presented`, `deferred by user`

## Invariants

- Idempotency and queue IDs are checked across both `Submissions` and `Articles`.
- Tracking-only variants of one normalized route are duplicates within a campaign.
- Directory `submitted` and pending states require a submit time, exact acknowledgment, and evidence; `published` additionally requires a verified public listing.
- Article `published` requires a public URL, publication time, actual anchor text, actual href, rel value, public-page check, outbound-link check, and evidence.
- Article `draft saved`, `submitted for review`, `rejected`, and `removed` require an exact result and evidence. `removed` also preserves its prior public URL and publication time and records a fresh public-page check.
- `publication outcome unknown` and `submission outcome unknown` require backend, mailbox, and public-page checks before retry.
- A failed legitimacy gate, unavailable capability, missing authorization, paid-only route, or prohibited policy must not execute.
- Body fields, raw email addresses, credentials, authentication URLs, and sensitive query parameters must never enter the workbook, logs, or exports.
- Google writes use `RAW` values. Schema drift, conflicting readback, or ambiguous duplicates stop the write.

## Audit and export

```bash
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID
uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID --json
uv run python scripts/sheets_record.py export-md --campaign-id CAMPAIGN_ID --output /approved/path/record.md
```

Audit covers both placement types and typed Events. Markdown exports operational records only and never contain article bodies. Do not import edited exports back into Google Sheets.
