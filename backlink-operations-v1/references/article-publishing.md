# Article publishing lane

Use this lane only after destination classification and campaign authorization pass.

## 1. Inspect history and platform rules

Run:

```bash
uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py article-history --product-id PRODUCT_ID --json
```

Optionally filter by `--platform-domain DOMAIN`. Use only the returned operational metadata to avoid repeated titles, angles, or content fingerprints.

Preflight the live platform's editor rules, audience, account state, external-link rules, canonical support, AI-content/disclosure policy, upload limits, payment conditions, and public-page behavior. Record observed reusable facts through `upsert-platform`.

Medium may require an AI-assistance disclosure when generated prose remains; do not use humanization to hide required disclosure. For every platform, apply the current observed policy rather than assuming these examples remain unchanged.

## 2. Write without durable body storage

Invoke the sibling writer in `ephemeral-publish` mode. Choose a non-duplicate topic from verified product facts, destination audience, and article history. Adapt each platform version's title, opening, structure, examples, length, metadata, CTA, and disclosure; do not copy one article mechanically.

Use approved product assets only when `upload` is authorized. Otherwise generate no new image and upload nothing.

If a temporary file is required, create a dedicated `mktemp -d` directory outside the repository. Never write to `writer/output`, product packages, Sheets, logs, or shell arguments.

## 3. Fingerprint and create the queue item

Place only `title`, `body`, and `target_url` in a temporary JSON file, then run:

```bash
uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py fingerprint-article --input TEMP_JSON
```

The result is `sha256:<64 lowercase hex>`. Use it in the Article record; do not copy body text into any record. Derive the article idempotency key exactly as:

```text
platform_domain|product_canonical_id|account_alias|route|article_id
```

Create the `Articles` queue item with `upsert-article`. If history or the CLI finds a duplicate ID, queue, idempotency key, or product fingerprint, record or report the duplicate and do not enter the editor.

## 4. Enter, save, or publish

Use the supported browser path for the current environment. Before entering content, confirm `write`; before saving, confirm `draft`; before a final public action, confirm `publish`; before any asset upload, confirm `upload`.

Append an `article` Event and update the Article after meaningful transitions such as writing completed, editor opened, draft saved, review submitted, final action invoked, verification performed, rejection, removal, or blockage. Do not print the article body in tool output or evidence.

If publication cannot complete, save a platform draft when authorized and possible. If the platform cannot save it, record the failure and content fingerprint, then discard the body.

## 5. Verify the result

After a public action, reopen the public page independently. Mark `published` only when all are recorded:

- public URL and publication time;
- public page is visible, not a preview or private editor;
- actual anchor text;
- actual outbound `href`, including required UTM parameters where the product rules require them;
- actual `rel`, using `none` when the link has no rel attribute;
- public-page and outbound-link checks;
- exact result and controlled evidence reference.

If the result is unclear, mark `publication outcome unknown`. Do not click Publish again. Check account backend, mailbox, and public page first and record all three.

## 6. Clean up and audit

After verified publication or confirmed platform draft save, delete the transient directory and verify it no longer exists. If cleanup fails, report its path without contents and stop. Run the campaign audit after cleanup.

`export-md` may include title, fingerprint, destination, status, and evidence metadata. It must never contain article body, HTML, or Markdown content.
