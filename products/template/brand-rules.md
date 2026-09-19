# {{PRODUCT_NAME}} brand and backlink rules

Updated: {{YYYY-MM-DD}}

## Canonical identity

- Product name: **{{PRODUCT_NAME}}**
- Canonical product ID: `{{PRODUCT_ID}}`
- Clean backlink target: {{CANONICAL_URL}}
- Required capitalization or spelling: {{SPELLING_RULES}}
- Names or terms that must not be used: {{PROHIBITED_NAMES_OR_NONE}}

Directory Product Name fields must use the approved product name. When a platform automatically links the product name, keep its native behavior.

## Link and anchor rules

### Directory lane

Use only the exact brand or product name, or the naked canonical URL. Do not request dofollow treatment or force commercial exact-match anchors.

| Type | Approved value | Use |
| --- | --- | --- |
| Brand or product name | {{PRODUCT_NAME}} | Product name and ordinary directory link text |
| Naked URL | {{CANONICAL_URL}} | Website and URL fields |
| Domain | {{DOMAIN}} | Platforms that omit the protocol |

### Editorial and social lanes

Contextual anchors may be used only when they read naturally, accurately describe the product, and comply with the selected publishing lane.

| Type | Approved example | Appropriate context |
| --- | --- | --- |
| Brand plus description | {{BRAND_CONTEXT_ANCHOR}} | Natural product introduction |
| Use case | {{USE_CASE_ANCHOR}} | Relevant educational or editorial passage |
| Audience | {{AUDIENCE_ANCHOR}} | Audience-specific recommendation |

Do not set anchor-text ratios or present them as ranking guarantees. After publication, record the actual rendered anchor and destination in Google Sheets.

## UTM policy

Website fields, canonical URL fields, and platforms that require a canonical URL use the clean target:

```text
{{CANONICAL_URL}}
```

When a platform permits a custom contextual link, use:

```text
{{CANONICAL_URL}}?utm_source=<platform>&utm_medium=referral&utm_campaign=backlink
```

`<platform>` must be a stable lowercase ASCII identifier. Document any product-specific UTM exception here:

- {{UTM_EXCEPTION_OR_NONE}}

## Claims and positioning boundaries

Approved positioning:

- {{APPROVED_POSITIONING}}

Do not claim:

- {{UNSUPPORTED_CLAIM}}
- {{UNSUPPORTED_CLAIM}}

Do not imply official recognition, certification, legal status, customer outcomes, exclusivity, revenue, usage scale, rankings, or performance unless the claim has current explicit evidence in `product-profile.md`.

## Copy and taxonomy rules

- Preferred category: {{PREFERRED_CATEGORY}}
- Allowed fallback categories: {{FALLBACK_CATEGORIES}}
- Prohibited or misleading categories: {{PROHIBITED_CATEGORIES}}
- Required disclosure or boundary sentence: {{REQUIRED_BOUNDARY_SENTENCE}}
- Words, tones, or calls to action to avoid: {{COPY_RESTRICTIONS_OR_NONE}}

## Offer and legal checks

- Recheck price, free credits, trials, discounts, and availability on submission day.
- Use only current terms visible on a first-party source or explicitly confirmed by the user.
- Leave optional unknown company, founder, address, funding, revenue, and legal fields blank.
- Stop when a destination requires an unknown fact, payment, reciprocal link, DNS change, or permission outside the active authorization.
