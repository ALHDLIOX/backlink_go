# {{PRODUCT_NAME}} approved asset manifest

Updated: {{YYYY-MM-DD}}

Only files listed as approved here may be uploaded. Inspect the live platform's dimensions, size, crop, and file-type requirements before use.

## Asset inventory

| Repository path | Role | Dimensions | Size | MIME type | Public upload | Source and rights | Approved caption or alt text | Crop or route notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `images/{{LOGO_FILE}}` | Square logo | {{WIDTH}}×{{HEIGHT}} | {{BYTES}} B | `image/{{TYPE}}` | {{YES_OR_SCOPE}} | {{PROVENANCE_AND_PERMISSION}} | {{ALT_TEXT}} | {{NOTES}} |
| `images/{{COVER_FILE}}` | Social or listing cover | {{WIDTH}}×{{HEIGHT}} | {{BYTES}} B | `image/{{TYPE}}` | {{YES_OR_SCOPE}} | {{PROVENANCE_AND_PERMISSION}} | {{ALT_TEXT}} | {{NOTES}} |
| `screenshots/{{SCREENSHOT_FILE}}` | Product screenshot | {{WIDTH}}×{{HEIGHT}} | {{BYTES}} B | `image/{{TYPE}}` | {{YES_OR_SCOPE}} | Captured from {{PUBLIC_PAGE}} on {{YYYY-MM-DD}} | {{ALT_TEXT}} | {{NOTES}} |

Delete unused example rows and add one row for every approved file.

## Upload order and selection

1. Logo field: `{{LOGO_FILE_OR_NOT_APPLICABLE}}`.
2. Primary gallery or cover: `{{PRIMARY_ASSET}}`.
3. Additional gallery order: `{{ORDERED_ASSETS_OR_NONE}}`.
4. If the destination accepts only {{LIMIT}} files, use: `{{LIMITED_SELECTION}}`.

## Route mapping

| Route or field | Preferred asset | Required | Attribution and crop check |
| --- | --- | --- | --- |
| {{ROUTE_OR_FIELD}} | `{{ASSET_PATH}}` | {{YES_NO_CONDITIONAL}} | {{ATTRIBUTION_AND_CHECK}} |

## Derived assets

- Preserve original files.
- Save resized, compressed, or reformatted variants as new files.
- Add every derivative to the inventory with its relationship to the source.
- Do not overwrite an original or remove provenance.
- Do not create testimonial, customer, generated-result, or interface claims that the source image does not support.

## Privacy and authenticity checks

- No private user data, emails, account names, API keys, tokens, private URLs, or session identifiers are visible.
- Demonstration content is labeled as demonstration content where confusion is possible.
- Customer work, testimonials, third-party marks, and licensed media include explicit reuse permission.
- The preview crop keeps the logo, product name, and essential content legible.
- The file meets the destination's current size and format limits.
