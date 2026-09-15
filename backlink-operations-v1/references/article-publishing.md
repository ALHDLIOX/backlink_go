# Article publication lane

Query prior work first:

```bash
uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py placement-history --product-id PRODUCT_ID --platform-domain DOMAIN --json
```

Use the writer in `ephemeral-publish` mode. Keep article text in memory or an isolated `mktemp -d` directory; never write to `writer/output` and delete the transient directory when the browser task ends. Topic/title/body are execution inputs, not Sheets fields.

Before editor work, inspect content, link, account, cost, and disclosure rules and verify authorization. Create one queued Placement. Append an Event after a meaningful action and update that Placement by row version. A draft is `draft saved`; review submission is `submitted for review`.

After publication, reopen the public page and verify visibility, actual backlink destination, and actual anchor text. If the linked element is not textual, use `not applicable — image or link card`. Do not click Publish again when the outcome is unclear; inspect backend, mailbox, and public page and record the combined result in `verification`.
