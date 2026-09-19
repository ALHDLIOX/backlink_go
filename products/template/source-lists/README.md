# Campaign source lists

Create one source-list file for each bounded campaign, destination set, or publication route. Copy `source-list-template.md` and rename it with a stable scope and date, for example:

```text
directory-batch-20260920.md
pinterest-social-20260920.md
```

Each file must identify the product or campaign, destination scope, account alias, permitted actions, approver alias, approval time, and expiry. Treat `write`, `draft`, `schedule`, `publish`, and `upload` as separate permissions.

Payments, credit consumption, reciprocal links, DNS changes, account-setting changes, and publication outside the named scope require separate explicit authorization.

Source-list files define inputs and authorization boundaries. Do not update them as operational logs. Record statuses, public results, backlinks, anchor text, evidence references, and events only in the Backlink Operations workbook.
