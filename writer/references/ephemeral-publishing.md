# Ephemeral publishing mode

Use this mode only when a caller is authorized to prepare content for a third-party editor.

1. Read the verified product package and safe `placement-history` output.
2. Select a truthful, non-duplicative topic suitable for the platform audience.
3. Draft, fact-check, SEO-audit, and humanize the article in memory or an isolated `mktemp -d` directory.
4. Never write to `writer/output`; do not persist title/body, content fingerprint, or Canonical metadata in the backlink workbook.
5. Transfer the content to the authorized editor. Prefer a platform draft when publication fails.
6. Delete the transient directory after a draft is safely saved, publication is verified, or the attempt terminates.

The caller records only unified Placement metadata: status, public page, actual backlink, anchor text, exact result, verification, timing, IDs, authorization, evidence, and execution notes.
