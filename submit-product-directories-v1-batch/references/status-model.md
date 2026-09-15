# Backlink Operations schema 8

Google Sheets is the authoritative V1 record store. Schema 8 has four worksheets: `Platforms`, `Campaigns`, `Placements`, and append-only `Events`. Directory, article, and social execution lanes all write the same Placement model. Business time is `YYYY-MM-DD HH:MM`.

## Platforms and Campaigns

`Platforms` stores reusable access facts: name/domain, canonical entry, availability, cost, account and verification requirements, reciprocal requirement, route, source, notes, ID, and row version. It does not store a platform/content type.

`Campaigns` stores product identity, canonical URL, sources, authorization reference, shard size, policy/workflow version, ID, and row version. It does not store a campaign type.

## Placements

The product ID is the first column so records can be grouped visually by product. Human-review columns then follow: platform domain, operation page, status, public page, actual backlink, anchor text, exact result, follow-up, verification summary, action time, and last check. System columns follow: placement/queue/campaign/platform IDs, route, account alias, idempotency key, authorization/evidence references, execution method/notes, and row version.

Do not store titles, content bodies, media or Board/channel details, AI labels, split UTM fields, platform/record types, `rel`, Canonical policy, content fingerprints, or agreement/subscription details. A full backlink URL may naturally include tracking parameters; there are no separate UTM columns.

The idempotency key is exactly `platform_domain|product_canonical_id|account_alias|route|placement_id`. A published result requires a public URL, actual backlink URL, anchor text, exact result, verification summary, action time, last-check time, and evidence. For a visual/link card without textual linked words, use `not applicable — image or link card`; do not invent an anchor.

Statuses are: `not attempted`, `in progress`, `draft saved`, `submitted`, `submitted for review`, `scheduled`, `awaiting approval`, `awaiting email verification`, `published`, `outcome unknown`, blocked states, `rejected`, `removed`, `unavailable`, `paid-only`, `ineligible`, `duplicate — no action`, and `terminated by user`.

## Events and audit

Events contain event ID, campaign/queue/idempotency linkage, minute timestamp, action, result, evidence, and actor alias. They do not carry a type because every event resolves to one Placement. Events append only; identical replay is idempotent and conflicting reuse stops.

Executed Placements require a prior linked Event. Updates require the current `expected_row_version`. The audit validates IDs, queue uniqueness, campaign/product/platform linkage, status evidence, event order, privacy, and row versions.
