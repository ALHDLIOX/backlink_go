# Backlink Operations schema 10

Google Sheets is the authoritative V1 record store. Schema 9 has four worksheets: `Platforms`, `Campaigns`, `Placements`, and append-only `Events`. Directory, article, and social execution lanes all write the same Placement model. Business time is `YYYY-MM-DD HH:MM`.

## Platforms and Campaigns

`Platforms` stores reusable access facts: name/domain, canonical entry, availability, cost model, cost detail, account and verification requirements, reciprocal requirement, route, source, notes, ID, and row version. It does not store a platform/content type.

`Campaigns` stores product identity, canonical URL, sources, authorization reference, shard size, policy/workflow version, ID, and row version. It does not store a campaign type.

## Placements

The product ID is the first column so records can be grouped visually by product. Human-review columns then follow: platform domain, operation page, status, public page, actual backlink, anchor text, exact result, follow-up, verification summary, action time, and last check. System columns follow: placement/queue/campaign/platform IDs, route, account alias, idempotency key, authorization/evidence references, execution method/notes, and row version.

Do not store titles, content bodies, media or Board/channel details, AI labels, split UTM fields, platform/record types, `rel`, Canonical policy, content fingerprints, or agreement/subscription details. A full backlink URL may naturally include tracking parameters; there are no separate UTM columns.

The idempotency key is exactly `platform_domain|product_canonical_id|account_alias|route|placement_id`. A published result requires a public URL, actual backlink URL, anchor text, exact result, verification summary, action time, last-check time, and evidence. For a visual/link card without textual linked words, use `not applicable — image or link card`; do not invent an anchor.

`platform_domain` is a bare hostname. The canonical platform entry and Placement operation page must use that hostname (treating `www` as equivalent) or one of its subdomains. A legacy migration never substitutes the campaign target URL for an observed backlink. If an old published row lacks an observed outbound URL, migrate it as `outcome unknown` with `not checked — no public backlink verified` and require public-page revalidation.

Statuses are: `not attempted`, `in progress`, `draft saved`, `submitted`, `submitted for review`, `scheduled`, `awaiting approval`, `awaiting email verification`, `waiting badge`, `published`, `outcome unknown`, blocked states, `rejected`, `removed`, `unavailable`, `paid-only`, `ineligible`, `duplicate — no action`, and `terminated by user`.

## Events and audit

Events contain event ID, campaign/queue/idempotency linkage, minute timestamp, action, result, evidence, and actor alias. They do not carry a type because every event resolves to one Placement. Events append only; identical replay is idempotent and conflicting reuse stops.

Executed Placements require a prior linked Event. Updates require the current `expected_row_version`. The audit validates IDs, queue uniqueness, campaign/product/platform linkage, status evidence, event order, privacy, and row versions.

## Pricing and badge queue

`Platforms.reciprocal_requirement` (Reciprocal Requirement) immediately follows Cost Model, and `Platforms.cost_detail` (Cost Detail) follows Reciprocal Requirement. Record every observed submission plan, its exact price/currency, waiting time, and badge or other conditions; for example: `Free Launch $0 — wait 100 days; Badge Launch $0 — badge required; Premium Launch $9.9`. Do not infer unobserved options or duplicate pricing in Notes. Unknown legacy details may remain blank until inspected; preserve unrelated Notes.

When both a free no-badge plan with a wait and a free badge plan exist, prefer the badge plan and set the Platform's `reciprocal_requirement` to `required` even though the other plan needs no badge. Append an Event and update the existing Placement to `waiting badge`, with `action_at: not submitted`, no public/backlink URLs, and the selected plan in `exact_result`. In `follow_up`, retain the non-secret badge instructions or canonical instructions URL and the need for later batch installation. Do not store executable badge HTML in the record.

`waiting badge` is a deferred, unsubmitted state, not a failed or completed submission. Stop before any submission or button that could submit, then leave the site and continue the queue. A safe non-submitting plan selection is allowed; otherwise record the selected plan without clicking. Do not add badges now, choose the slow plan instead, pay, or mark the task submitted. This specific user-selected optional badge route is an exception to the forced-reciprocal exclusion; unrelated forced-reciprocal routes remain excluded.

Ordinary batches skip existing `waiting badge` Placements. Resume them only during the user's later badge-processing task: add badges in that authorized batch, verify each required badge is live, reopen the original route, recheck current pricing and conditions, refill the form, then submit under the applicable submission authorization. Reuse the same Placement/idempotency key and row-version checks. Immediately before leaving `waiting badge`, append a new linked Event with action `resume after badge verification`, the same evidence reference as the Placement update, and a semicolon-delimited result containing the exact positive tokens `badge verified` plus `submitted` or `published` as applicable. An older defer/select event cannot satisfy this transition. If the badge is absent or invalid, retain `waiting badge`. Badge installation is not authorized by merely queueing the site.

Historical badge-resume audits verify the linked resume evidence independently of the current lifecycle status, so a valid resumed publication can later become `removed`. Direct transitions out of `waiting badge` still require a supported resume target and matching outcome evidence.
