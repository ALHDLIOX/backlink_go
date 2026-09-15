# Social publishing lane

Use this lane for Pinterest Pins, X/LinkedIn short posts, image posts, link posts, and threads. It owns operational records in `SocialPosts`; never represent a social post as a directory Submission or long-form Article.

## Preflight and history

Run `doctor`, resolve the project-local authorization, and inspect prior product history before composing:

```bash
uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py social-history --product-id PRODUCT_ID --platform-domain DOMAIN --json
```

Confirm current post format, character limits, image requirements, Board/channel, external-link behavior, AI-label rules, account state, payment conditions, and public-page visibility. Do not create a new Board, community, advertising campaign, or paid promotion without separate authorization.

## Content, image, and UTM

Write concise, original platform-native text from verified product facts. Do not invent endorsements, rankings, user counts, outcomes, certifications, or official status. Use an approved product-package asset when the post type requires media. Store its project-relative path or stable asset alias in `media_reference`, never a temporary credential-bearing URL.

The target URL must include the recorded `utm_source`, `utm_medium`, and `utm_campaign`. For ordinary backlink operations, prefer:

```text
utm_source=<platform>&utm_medium=referral&utm_campaign=backlink
```

Compute the final content fingerprint from a temporary JSON object containing `title`, `post_text`, `target_url`, and `media_reference`:

```bash
uv run python ../submit-product-directories-v1-batch/scripts/sheets_record.py fingerprint-social-post --input TEMP_JSON
```

The command returns only the SHA-256, character count, and `text_echoed: false`. Delete the temporary input after its `SocialPosts` row is safely written.

The social idempotency key is:

```text
platform_domain|product_canonical_id|account_alias|route|social_post_id
```

Create the queue item with `upsert-social-post` before entering the composer. A repeated public post should update the existing row by current `expected_row_version`; do not create another post to repair recordkeeping.

## Composer and publication

Fill only verified content and approved assets. For Pinterest, select the authorized existing Board, preserve the intended destination URL, and apply the platform's AI-modified/generated label when the asset or current rules require it. For X or LinkedIn, distinguish a short post from the platform's long-form article editor and preserve the selected lane.

Append a `social` Event before every executed state update, including composer opened, media uploaded, draft saved, scheduled, publish invoked, public verification, rejection, removal, or blockage. Then update the SocialPost with its current row version.

If the final action has an ambiguous result, do not click it again. Record `publication outcome unknown`, then inspect account backend, mailbox, and public page before any retry.

## Public verification

Mark `published` only after reopening the public post and confirming:

- the post is publicly visible under the expected account;
- title and text match the intended final content;
- the expected image or media is visible;
- the expected Board/channel is shown when the platform exposes it;
- the actual outbound destination matches `target_url`, including all required UTM parameters;
- the AI/content label is present when required.

Use `published_at: unknown` only for an existing public post whose page does not expose a trustworthy publication time; always record a precise `last_checked`. Save the public URL and a non-secret evidence reference. Finish with campaign `audit`.
