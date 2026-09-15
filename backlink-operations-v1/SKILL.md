---
name: backlink-operations-v1
description: Orchestrate authorized backlink operations across product directories, long-form article platforms, and social publishing surfaces. Use when the user supplies directory, blog, Pinterest, X, LinkedIn, or similar URLs and wants truthful submission or publication, platform-aware content, images or boards, UTM links, Google Sheets deduplication, evidence, public-result verification, and audit. Routes directories to SPD V1 Batch, articles to writer ephemeral-publish, and pins or short posts to the social lane; never performs spam, paid-link acquisition, forced reciprocal links, or policy bypass.
---

# Backlink Operations V1

## Purpose

Classify each supplied destination, then run one of three controlled lanes:

- Product, software, startup, app, or AI-tool directory: delegate to the sibling `submit-product-directories-v1-batch` skill without changing its directory workflow.
- Blog or long-form content platform: use the sibling `writer` skill in `ephemeral-publish` mode, then save a platform draft or publish only within explicit authorization.
- Pinterest Pin, X/LinkedIn short post, image post, link post, or thread: use the social publishing lane in [references/social-publishing.md](references/social-publishing.md).

Forum replies, community comments, fake engagement, unsolicited mass posting, and profile-link edits remain out of scope unless a later skill version defines a legitimate dedicated lane.

Google Sheets is the single writable record source for all three lanes. Use only the bundled Python CLI in `../submit-product-directories-v1-batch/scripts/sheets_record.py`. Never use a Sheets connector, read its plugin documentation, locate cells manually, or keep a second writable Markdown log. Article body text must not enter Sheets; short social post text is stored in `SocialPosts` for operational review.

## Load only the selected lane

1. Resolve the product package from `../products/<product-id>/`. Read its profile, brand rules, asset manifest, and batch authorization. Resolve private values only from the project-local ignored `../.backlink-go/private/product-aliases.json`; never copy raw values into records or output.
2. Read [references/routing.md](references/routing.md) and perform an initial URL/surface classification before OAuth or record work. For every admitted directory, article, or social candidate, run `uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py doctor` before writing or browser work, then confirm the classification from the live destination.
3. For a directory destination, read the complete sibling `../submit-product-directories-v1-batch/SKILL.md` and every reference it requires. Follow that skill exactly. Record events as `record_type: submission`.
4. For an article destination, read [references/article-publishing.md](references/article-publishing.md), the complete sibling `../writer/SKILL.md`, and `../writer/references/ephemeral-publishing.md`. Invoke the writer in `ephemeral-publish` mode. Record events as `record_type: article`.
5. For a social destination, read [references/social-publishing.md](references/social-publishing.md). Use the approved product package and platform composer directly; do not invoke the long-form writer merely to create a short post. Record events as `record_type: social`.
6. Do not load every lane merely because all are available. A mixed campaign may load each only when its corresponding queue items are processed.

If `doctor` reports schema 4 or 5, stop normal work and run `migrate-schema-v6` before continuing. If OAuth, API access, workbook identity, schema, or headers remain invalid, stop and report the non-secret error. Do not fall back to another record method.

## Campaign authorization gate

Create or load a Campaign using `workflow_version: Backlink Operations V1` and `campaign_mode: directory`, `article`, `social`, or `mixed` as appropriate. A reusable batch authorization permits direct article or social publication only when its verified source explicitly names:

- the product and campaign;
- each platform or bounded source-URL scope;
- the account alias;
- the allowed actions among `write`, `draft`, `schedule`, `publish`, and `upload`;
- approver alias, approval time, and a still-valid expiry.

Do not infer missing actions. `write` permits composition, `draft` permits editor entry and draft saving, `schedule` permits a future publication setting, `publish` permits the platform's final public action, and `upload` permits approved product assets. A permission for one action does not imply another. Payments, subscriptions, reciprocal links, DNS changes, policy exceptions, and tools that impose their own confirmation remain separate.

The Sheets CLI validates that `authorization_reference` exists but does not interpret the permissions encoded by an arbitrary reference string. Resolve and enforce the referenced project-local authorization before constructing an executed record; a successful `--dry-run` is structural validation, not proof that `publish` or another action is authorized.

## Shared execution order

1. After the initial classification admits a directory, article, or social candidate, run `doctor` and inspect safe history before any final action.
2. Classify the target, create or load Campaign, and verify authorization.
3. Upsert reusable Platform facts with `platform_type: directory`, `article`, `mixed`, `social`, or `unknown` based on observed capability.
4. Create the lane-specific Submission, Article, or SocialPost queue record before execution.
5. Append one typed Event after every meaningful action, then update the Submission, Article, or SocialPost with its current row version.
6. Advance the queue only after the CLI verifies both writes by rereading the row.
7. Never replay an ambiguous website action. First record and perform the required backend, mailbox, and public-page checks.
8. Run `audit --campaign-id CAMPAIGN_ID` at close. `export-md` is read-only and contains no article body.

The CLI serializes Sheets writes with a local lock. Browser tasks may be separated, but do not run record writers concurrently.

## Result standards

- A directory form acknowledgment is not a published listing.
- A populated editor or saved article draft is not a published article.
- Mark an article `published` only after reopening its public page and verifying visibility, actual anchor text, actual `href`, required UTM parameters, and `rel`.
- Mark a social post `published` only after reopening its public page and verifying the visible post and media, the destination URL and required UTM parameters, the chosen Board/channel when applicable, and the platform's AI-content label when required.
- Within any supported lane, when the platform prohibits the content, requires payment, or is irrelevant, record `ineligible`, `paid-only`, or the applicable blocked state and do not force another lane.
- Keep exact non-secret evidence references and truthful results. Never claim indexing, dofollow treatment, referral value, traffic, or ranking impact without separate evidence.

## Bundled resources

- [references/routing.md](references/routing.md): directory/article/social classification and generic platform gates.
- [references/article-publishing.md](references/article-publishing.md): article queue, history, fingerprint, browser publication, verification, and cleanup.
- [references/social-publishing.md](references/social-publishing.md): short-post history, fingerprint, media/Board handling, UTM rules, publication, and verification.
- `../submit-product-directories-v1-batch/scripts/sheets_record.py`: the only Sheets writer and auditor.
- `../submit-product-directories-v1-batch/references/status-model.md`: shared schema 6 fields and invariants.
- `../writer/references/ephemeral-publishing.md`: transient body and platform-adaptation rules.
