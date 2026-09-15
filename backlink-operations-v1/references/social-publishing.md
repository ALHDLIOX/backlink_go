# Social publication lane

Use for Pinterest Pins, X/LinkedIn short posts, image/link posts, and threads. Query `placement-history` before execution. Use approved product facts/assets and respect platform rules and authorization, but do not retain post copy, title, media, Board/channel, AI label, or split tracking fields in Sheets.

Create one queued Placement before the composer. Append an Event after each meaningful action, then update the Placement with `expected_row_version`. `scheduled`, `draft saved`, and `published` remain distinct.

For `published`, reopen the public page and verify the actual backlink destination. Record visible linked words as `anchor_text`; for Pinterest imagery or a link card with no textual linked words, use `not applicable — image or link card`. Record media/Board/AI checks only transiently while satisfying the platform, not as maintained workbook fields.

Never repeat an ambiguous final action. Check backend, mailbox, and public page and summarize those checks in `verification` before resolving `outcome unknown`.
