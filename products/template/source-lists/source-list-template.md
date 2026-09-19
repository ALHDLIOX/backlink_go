# {{PRODUCT_NAME}} — {{CAMPAIGN_OR_ROUTE_NAME}}

- Product ID: `{{PRODUCT_ID}}`
- Campaign ID: `{{CAMPAIGN_ID}}`
- Source-list reference: `{{SOURCE_LIST_REFERENCE}}`
- Route: `{{DIRECTORY_ARTICLE_OR_SOCIAL}}`
- Account alias: `{{ACCOUNT_ALIAS}}`
- Contact fallback alias: `{{CONTACT_ALIAS_OR_NOT_APPLICABLE}}`
- Authorization reference: `{{AUTHORIZATION_REFERENCE}}`
- Approver alias: `{{APPROVER_ALIAS}}`
- Approved at: `{{YYYY-MM-DD HH:MM TIMEZONE}}`
- Authorization expires: `{{YYYY-MM-DD HH:MM TIMEZONE}}`

## Destinations

| Platform | Submission or composer URL | Platform scope or notes |
| --- | --- | --- |
| {{PLATFORM_NAME}} | {{HTTPS_URL}} | {{SCOPE_OR_ROUTE_NOTES}} |

Use clean destination URLs without tracking parameters, tokens, session identifiers, magic links, or credentials.

## Authorized actions

- [ ] Open and inspect the named destinations.
- [ ] Sign in with the named account alias.
- [ ] Create an account with the named contact alias.
- [ ] Fill or update product fields.
- [ ] Upload assets listed in `../asset-manifest.md`.
- [ ] Save a draft.
- [ ] Schedule publication.
- [ ] Click the final submit or publish action.
- [ ] Read a verification email through the approved read-only mailbox route.
- [ ] Verify the public result and backlink.

Remove unchecked actions from the final authorization or state explicitly that they are not authorized.

## Approved route inputs

- Product copy source: `../product-profile.md`
- Link and anchor rules: `../brand-rules.md`
- Approved assets: {{ASSET_PATHS_OR_NOT_APPLICABLE}}
- Category or route restriction: {{CATEGORY_OR_ROUTE_RESTRICTION}}
- Additional required disclosure: {{DISCLOSURE_OR_NONE}}

## Not authorized

- Payment or credit consumption.
- Reciprocal-link changes.
- DNS or production-site changes.
- Optional mailing-list or promotional subscriptions.
- Account-setting, profile, Board, channel, or organization changes outside the named route.
- Publication to an unnamed destination.
- {{ADDITIONAL_EXCLUSION_OR_NONE}}

## Handoff conditions

- CAPTCHA or native verification requiring user action: {{HANDOFF_RULE}}.
- Required unknown product or company fact: stop and request the missing fact.
- Cost, credits, reciprocal link, or expanded permission: stop for separate authorization.
- Ambiguous final action: do not retry; inspect the account backend, mailbox, and public page first.

This file defines source scope and authorization. Submission state and events belong only in the configured Backlink Operations Google workbook.
