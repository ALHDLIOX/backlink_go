---
name: backlink-operations-v1
description: Orchestrate and classify authorized backlink operations across product directories, third-party long-form article platforms, and unsupported short-social targets. Use when the user supplies one or more directory, blog, publishing, editor, or social URLs and wants correct routing, truthful directory submission, platform-adapted article writing, draft saving or publication, Google Sheets deduplication, evidence, audit, or a clear refusal of unsupported pins and short posts. Routes directories to SPD V1 Batch and articles to writer ephemeral-publish mode; never executes short social posts, spam, paid-link acquisition, forced reciprocal links, or policy bypass.
---

# Backlink Operations V1

## Purpose

Classify each supplied destination, then run one of two controlled lanes:

- Product, software, startup, app, or AI-tool directory: delegate to the sibling `submit-product-directories-v1-batch` skill without changing its directory workflow.
- Blog or long-form content platform: use the sibling `writer` skill in `ephemeral-publish` mode, then save a platform draft or publish only within explicit authorization.

Do not handle short social content in this version. A Pinterest pin page, X post, LinkedIn short post, forum reply, community comment, profile-link edit, or link-only post is out of scope even when it could create a backlink.

Google Sheets is the single writable record source for both lanes. Use only the bundled Python CLI in `../submit-product-directories-v1-batch/scripts/sheets_record.py`. Never use a Sheets connector, read its plugin documentation, locate cells manually, keep a second writable Markdown log, or put article body text in Sheets.

## Load only the selected lane

1. Resolve the product package from `../products/<product-id>/`. Read its profile, brand rules, asset manifest, and batch authorization. Resolve private values only from the project-local ignored `../.backlink-go/private/product-aliases.json`; never copy raw values into records or output.
2. Read [references/routing.md](references/routing.md) and perform an initial URL/surface classification before OAuth or record work. An obviously unsupported short-social target exits through the social rule below. For every directory or article candidate, run `uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py doctor` before writing or browser work, then confirm the classification from the live destination.
3. For a directory destination, read the complete sibling `../submit-product-directories-v1-batch/SKILL.md` and every reference it requires. Follow that skill exactly. Record events as `record_type: submission`.
4. For an article destination, read [references/article-publishing.md](references/article-publishing.md), the complete sibling `../writer/SKILL.md`, and `../writer/references/ephemeral-publishing.md`. Invoke the writer in `ephemeral-publish` mode. Record events as `record_type: article`.
5. Do not load both lane workflows merely because both are available. A mixed campaign may load each when its corresponding queue items are processed.

If `doctor` reports schema 4, stop normal work and run the one-step `migrate-schema-v5` command before continuing. If OAuth, API access, workbook identity, schema, or headers remain invalid, stop and report the non-secret error. Do not fall back to another record method.

## Campaign authorization gate

Create or load a Campaign using `workflow_version: Backlink Operations V1` and `campaign_mode: directory`, `article`, or `mixed` as appropriate. A reusable batch authorization permits direct article publication only when its verified source explicitly names:

- the product and campaign;
- each platform or bounded source-URL scope;
- the account alias;
- the allowed actions among `write`, `draft`, `publish`, and `upload`;
- approver alias, approval time, and a still-valid expiry.

Do not infer missing actions. `write` permits transient composition, `draft` permits editor entry and draft saving, `publish` permits the platform's final public action, and `upload` permits approved product assets. A permission for one action does not imply another. Payments, subscriptions, reciprocal links, DNS changes, policy exceptions, and tools that impose their own confirmation remain separate.

The Sheets CLI validates that `authorization_reference` exists but does not interpret the permissions encoded by an arbitrary reference string. Resolve and enforce the referenced project-local authorization before constructing an executed record; a successful `--dry-run` is structural validation, not proof that `publish` or another action is authorized.

## Shared execution order

1. After the initial classification admits a directory or article candidate, run `doctor` and inspect safe history before any final action.
2. Classify the target, create or load Campaign, and verify authorization.
3. Upsert reusable Platform facts with `platform_type: directory`, `article`, `mixed`, `social`, or `unknown` based on observed capability.
4. Create the lane-specific queue record before execution.
5. Append one typed Event after every meaningful action, then update the Submission or Article with its current row version.
6. Advance the queue only after the CLI verifies both writes by rereading the row.
7. Never replay an ambiguous website action. First record and perform the required backend, mailbox, and public-page checks.
8. Run `audit --campaign-id CAMPAIGN_ID` at close. `export-md` is read-only and contains no article body.

The CLI serializes Sheets writes with a local lock. Browser tasks may be separated, but do not run record writers concurrently.

## Result standards

- A directory form acknowledgment is not a published listing.
- A populated editor or saved article draft is not a published article.
- Mark an article `published` only after reopening its public page and verifying visibility, actual anchor text, actual `href`, required UTM parameters, and `rel`.
- Within a supported directory or article lane, when the platform prohibits the content, requires payment, or is irrelevant, record `ineligible`, `paid-only`, or the applicable blocked state and do not force another lane.
- For a short-social target, do not create Campaign, Submission, Article, or Event rows. After a live preflight, reusable non-secret platform facts may be upserted only to `Platforms` with `platform_type: social`; without complete verified Platform fields, report the classification without writing anything.
- Keep exact non-secret evidence references and truthful results. Never claim indexing, dofollow treatment, referral value, traffic, or ranking impact without separate evidence.

## Bundled resources

- [references/routing.md](references/routing.md): directory/article/social classification and generic article-platform gate.
- [references/article-publishing.md](references/article-publishing.md): article queue, history, fingerprint, browser publication, verification, and cleanup.
- `../submit-product-directories-v1-batch/scripts/sheets_record.py`: the only Sheets writer and auditor.
- `../submit-product-directories-v1-batch/references/status-model.md`: shared schema 5 fields and invariants.
- `../writer/references/ephemeral-publishing.md`: transient body and platform-adaptation rules.
