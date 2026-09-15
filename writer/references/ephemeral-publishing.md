# Ephemeral publishing mode

Load this reference only when `backlink-operations-v1` explicitly invokes the writer in `ephemeral-publish` mode. These rules override the normal writer file-output, image-generation, platform-routing, and R2-upload rules for that run. They do not change ordinary `$writer`, `$medium-writer`, `$linkedin-writer`, or `$wechat-writer` requests.

## Purpose and boundaries

- Produce one truthful, platform-adapted article for an authorized external article platform.
- Do not use this mode for short social posts, pins, forum replies, community comments, directory descriptions, or link-only posts.
- Do not generate new images by default. Use only product-package assets whose manifest permits the destination and requested upload action.
- Do not use R2 or any other remote asset store unless the campaign separately authorizes that upload.
- Never invent personal experience, independent reviews, metrics, customers, quotes, authorship, or product facts.

## Topic and platform adaptation

1. Read the verified product package and the safe output of `article-history`.
2. Select a useful topic and angle not already represented by a prior title or content fingerprint for that product. A different platform alone is not enough to justify an identical article.
3. Inspect the destination audience, editor format, AI-content or disclosure requirements, external-link policy, canonical options, account state, and payment requirements.
4. Adapt the title, opening, structure, examples, length, CTA, metadata, disclosure, and formatting to the destination. Do not mechanically copy one article across platforms.
5. Run the standard outline, fact-check, SEO audit, humanization, and post-humanization integrity checks before entering the editor.

## Transient content handling

1. Keep the working article in memory when the available tools support it. If a file is required, create a narrowly scoped system temporary directory with `mktemp -d` and keep every draft or fingerprint input inside it.
2. Do not write to `writer/output/`, the product package, the repository, Google Sheets, shell history, command arguments, logs, event evidence, or Markdown exports.
3. Pass the temporary JSON file containing `title`, `body`, and `target_url` only to `fingerprint-article --input PATH`. The CLI output contains the fingerprint and word count, never the body.
4. Fill the destination editor from the transient content. Prefer a platform draft when publication fails after editor entry.
5. After a verified publication or confirmed platform draft save, delete the temporary directory. If the platform cannot save a draft, record the operational failure and fingerprint, then delete the transient content anyway.
6. If cleanup cannot be verified, stop and report the exact temporary path without printing its contents.

## Publication result

- A saved editor draft is `draft saved`, not `published`.
- A review queue acknowledgment is `submitted for review`.
- A final click or generic success message without a verified public page is `publication outcome unknown`.
- Mark `published` only after reopening the public page and checking visibility, actual anchor text, destination `href`, required UTM parameters, and `rel`.
- Never retry an ambiguous final action until the account backend, mailbox, and public page have all been checked and recorded.
