# SPD V1 Batch workflow

## 1. Preflight the campaign

Create one verified product profile with approved short, medium, and long descriptions; pricing; categories; contact aliases; policy URLs; social handles; and asset references. Separate public facts from credentials and controlled evidence.

Run `uv run python scripts/sheets_record.py doctor`. If OAuth, workbook configuration, schema version, or headers fail validation, stop. Do not use a Google Sheets connector or a writable Markdown fallback.

Record:

- campaign ID and `workflow_version: SPD V1 Batch`;
- product canonical ID and canonical URL;
- source-list reference and authorization reference;
- execution-shard size and shared policy version;
- permitted actions, scope, approver alias, approval time, and expiry;
- prohibited actions, including payment, reciprocal-site modification, and DNS changes unless separately approved.

Write the campaign with `upsert-campaign`. Google Sheets is the source of truth.

## 2. Normalize and deduplicate

Before iterating over source URLs, run `placement-history --product-id PRODUCT_ID --json` once and build an in-memory index of the product's existing Placements. Each result is a complete Placement snapshot with `row_version`. Reuse that index across every source URL and update it after each successful Placement readback. To update a cached row, move its `row_version` value to `expected_row_version`, remove `row_version`, and change only the intended business fields before calling `upsert-placement`. Do not issue one domain-scoped history query per destination. Refresh a specific domain only after an interrupted resume, an ambiguous result, a detected external workbook edit, or another concrete stale-cache signal.

For every source URL:

1. lowercase the hostname;
2. remove fragments and tracking parameters;
3. preserve route parameters required to reach the form only in controlled evidence;
4. assign a stable placement ID and derive the exact idempotency key `platform_domain|product_canonical_id|account_alias|route|placement_id`;
5. merge exact and tracking-only duplicates;
6. check the batch history index and inspect public listings before scheduling a final action.

Assign a stable queue ID. Never renumber existing entries after execution begins.

After live preflight, use `upsert-platform` to preserve reusable platform facts. Platform rows may be reused across products, but each product receives its own Placement row and idempotency key.

## 3. Run fast triage

Inspect enough page state to classify the route without entering product fields.

Pass only legitimate, relevant product-directory routes with a usable submission or claim path. Remove or isolate unavailable, paid-link-only, forced-reciprocal, unrelated, unreleased-only, known directory-network, and terms-prohibited routes.

Classify passing routes by operational lane:

- direct form;
- account required;
- registration email required;
- manual verification likely;
- verification unavailable before form;
- unknown interactive route.

## 4. Create execution shards

Split the passing queue by route and browser capacity. Configure shard size explicitly; a practical default may be chosen for local resources, but it is not a search-engine safety threshold.

Before opening the first shard, apply [browser-control-routing.md](browser-control-routing.md). Detect `windows`, `macos`, `linux`, or `other`; detect desktop, remote, or headless UI availability; and inventory compatible control capabilities. Honor an explicit browser choice, use a supported browser runtime when available, use only a desktop UI adapter whose declared target matches the host platform, and hand off rather than silently switching browsers. Record only a concise execution method and optional non-secret notes; keep environment-specific identifiers outside the shareable record.

Within each shard:

1. order account and email-verification work first;
2. order short-lived verification tokens immediately before their forms;
3. cap active tabs according to current runtime capacity;
4. keep one queue cursor and the append-only `Events` worksheet; every event links to one unified Placement;
5. isolate browser profiles when account identity or session ownership differs.
6. keep each site bound to the selected backend and session alias until it reaches a recorded handoff or terminal state.

## 5. Run verification preflight

Visit every site in the shard before form entry. Expose the earliest verification or login boundary. Apply [authentication.md](authentication.md) for authorized session reuse, Google login/registration, and matching Gmail verification without renewed approval. Attempt only ordinary native automatic verification for other challenges. Preserve interactive challenges in their original tabs and add them to the manual queue.

Record one state:

- `automatic verification passed`;
- `awaiting manual verification`;
- `manual verification completed`;
- `verification unavailable before form`;
- `verification expired/reset`;
- `no verification presented`;
- `deferred by user`.

Do not bypass challenges or move issued challenges between browser profiles.

## 6. Resolve one manual queue

Present site, queue ID, browser tab, challenge type, exact blocker, and required user action. After user completion, immediately re-inspect each tab, append an event, and upsert whether the challenge completed, expired, reset, or remained blocked.

Do not keep solved short-lived tokens waiting behind unrelated work.

## 7. Execute form lanes

Process eligible items sequentially within a profile:

1. confirm authorization and idempotency;
2. confirm verification validity;
3. fill approved facts and the nearest truthful category;
4. leave unknown optional fields blank;
5. keep optional subscriptions off;
6. verify free/paid plan and reciprocal requirements;
7. submit only when the final action is allowed;
8. capture exact server text and controlled evidence reference;
9. append the action event, then upsert the submission state;
10. advance the queue cursor only after both CLI writes pass readback verification.

Apply the selected runtime's confirmation and handoff policy at action time. Campaign authorization cannot weaken that policy.

Never retry an ambiguous final action. Append the ambiguous event, mark `outcome unknown`, then inspect the account backend, mailbox, and public search before any future attempt. The CLI reconciles an ambiguous Sheets API response by key before one retry; this does not authorize retrying the directory submission itself.

## 8. Recover without replay

- Re-inspect after navigation, modal changes, user interaction, or page reloads.
- Reacquire accessibility elements instead of using stale identifiers.
- Retry transient loading once in the current tab and once in a fresh tab.
- Resume from the first queue item without a terminal or pending state in `Placements`.
- Never reopen completed idempotency keys for final action.
- Preserve exact error text and distinguish site failure from local browser failure.

## 9. Close the batch

Run `uv run python scripts/sheets_record.py audit --campaign-id CAMPAIGN_ID`, reconcile ambiguous entries, and report:

- total source URLs, normalized routes, duplicates removed, and routes rejected;
- eligible queue size and completed shards;
- submitted, awaiting approval, awaiting email verification, published, unknown outcome, blocked, unavailable, paid-only, and ineligible;
- manual-verification queue size and completion rate;
- operator time, verified submissions per hour, recovery rate, and outstanding queue.

Do not equate `submitted` with `published` or use volume as evidence of SEO value.

The user-selected free badge alternative to a free waiting plan is an explicit exception to the forced-reciprocal exclusion. Apply the pricing and badge queue rules in `status-model.md`: record all plans in Cost Detail, set reciprocal requirement to `required`, queue `waiting badge`, and leave without submitting. Skip these rows in ordinary batches; resume only in the later authorized badge-processing batch after verifying the badge.
