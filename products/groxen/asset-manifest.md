# Groxen asset manifest

Updated: 2026-09-24

These three files are copies of first-party public assets in the Groxen product repository. They were inspected and their corresponding production URLs returned HTTP 200 on 2026-09-24. They are selected for this reusable package; no destination-specific upload has been authorized. Inspect the destination's current dimensions, size, crop, file-type, and rights rules before use.

## Asset inventory

| Repository path | Role | Dimensions | Size | MIME type | Public upload | Source and rights | Approved caption or alt text | Crop or route notes |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `images/groxen-logo.svg` | Square brand mark | 512×512 viewBox | 333 B | `image/svg+xml` | Route approval required | Exact copy of Groxen repository `public/logo.svg`, already public at `https://grokboticon.com/logo.svg`; first-party brand asset. External reuse permission is limited to authorized product promotion. | Groxen two-eye logo on peach background | SVG may be rejected by directories; keep the rounded square and both eyes intact. |
| `images/groxen-logo-180.png` | PNG logo fallback | 180×180 | 4,011 B | `image/png` | Route approval required | Exact copy of `public/apple-touch-icon.png`, already public at `https://grokboticon.com/apple-touch-icon.png`; first-party brand asset. | Groxen two-eye logo on peach background | Use when a PNG is required and 180 pixels meets the field minimum. Do not upscale and imply a higher-resolution original. |
| `images/groxen-social-cover-1200x630.png` | English social or listing cover | 1200×630 | 533,606 B | `image/png` | Route approval required | Exact copy of `public/og-groxen-v2.png`, the current English OG asset referenced by `src/lib/seo.ts` and public at `https://grokboticon.com/og-groxen-v2.png`. First-party promotional artwork, not a customer result or interface screenshot. | Groxen cover with a stylized bot avatar and “Any photo. A tiny bot.” | English text is built into the image. Preserve both the left text panel and right avatar in crops. |

Original creation dates and any third-party rights inside the cover are not separately documented; the selected files were checked on 2026-09-24. No generated user result, public-figure gallery image, or current interface screenshot is included.

## Upload order and selection

1. Logo field: `groxen-logo.svg` when SVG is accepted; otherwise `groxen-logo-180.png` if the minimum dimensions permit.
2. Social preview or cover field: `groxen-social-cover-1200x630.png` when a text-bearing marketing image is allowed.
3. If only one file is accepted, choose the logo for a logo field or the cover for a banner/social field. Do not use the cover in a field requiring a captured product interface.

## Route mapping

| Route or field | Preferred asset | Required | Attribution and crop check |
| --- | --- | --- | --- |
| Directory logo | `images/groxen-logo.svg` or `images/groxen-logo-180.png` | Conditional | Obtain route approval; check accepted format, minimum size, and legibility. |
| Social or directory cover | `images/groxen-social-cover-1200x630.png` | Conditional | Obtain route approval; verify English text, brand name, and avatar remain legible after cropping. |
| Product screenshot | None | No asset available | Capture and approve an authentic current public interface image if a route requires one. |

## Derived assets

- Preserve original copies. Save resized, compressed, or reformatted variants as new files and add each derivative to this inventory with its source relationship.
- Do not label the social cover as a captured application screen, a customer testimonial, or a verified user result.

## Privacy and authenticity checks

- Visual and source inspection on 2026-09-24 found no private user data, email addresses, account names, API keys, tokens, private URLs, or session identifiers in these assets.
- The cover shows first-party promotional illustration. Do not use public-figure gallery images as listing assets without separate rights review and route authorization.
- Check final crop, logo contrast, file-type support, destination terms, and file-size limit before upload.
