# Agent intake — generate a complete product backlink package

Fill in this file and give it to an Agent working in the `backlink-go` repository. The Agent must treat the completed answers as user-provided facts and follow the execution contract below.

Unknown optional facts may remain blank. If a required fact is missing, the Agent must create everything supported by the available evidence and report the remaining blocker without inventing a value.

## Agent execution contract

Using the completed intake below, create or update `products/<product-id>/` as a complete Backlink Operations V1 product package.

1. Read the repository `AGENTS.md`, `submit-product-directories-v1-batch/references/product-packages.md`, and `products/template/PACKAGE-GUIDE.md` before editing.
2. Use `products/template/` as the canonical source. Copy the required templates; do not redesign the package structure ad hoc.
3. If `products/<product-id>/` already exists, inspect it and update it without overwriting verified facts or approved assets silently.
4. Create `README.md` and `product-profile.md` in every package. Create `brand-rules.md` before preparing public copy or links. Keep `asset-manifest.md`, `images/`, and `screenshots/` only when approved media exists or an authorized route requires it. Create a dated source-list file only when campaign scope and authorization are supplied.
5. Replace all template placeholders. Use `unknown — leave blank on submission` for optional unknown facts and `not applicable — <reason>` only when the field truly does not apply. A required unknown remains a reported blocker.
6. Verify material claims from the supplied first-party sources or explicit user confirmations. Date changeable facts such as pricing, free credits, availability, team size, launch state, and upload permission.
7. Do not invent company, founder, location, funding, revenue, pricing, launch, ownership, contact, legal, customer, performance, or product-capability facts.
8. Keep raw contact details, credentials, OTPs, cookies, authentication URLs, tokens, and browser-session identifiers out of committed files and Google Sheets. Use only the supplied account and contact aliases. Real alias values belong in `.backlink-go/private/product-aliases.json` with mode `0600`.
9. Do not submit forms, publish content, spend credits, make payments, change reciprocal links, write Google Sheets records, or perform other external actions while generating the package.
10. Remove `PACKAGE-GUIDE.md`, `AGENT-INTAKE.md`, unused template-only source files, and instructions from the finished product directory.
11. Verify the result with:
    - `find products/<product-id> -maxdepth 3 -type f | sort`
    - `rg -n '\{\{[^}]+\}\}' products/<product-id>`; no unresolved placeholder may remain
    - `git diff --check`
    - `./scripts/check-all.sh`
12. Report created and omitted files, evidence used, optional unknowns, blocking unknowns, validation results, and any facts that must be rechecked before submission.

Do not treat the generated package as a placement log. Campaigns, Platforms, Placements, and Events remain authoritative only in the configured Backlink Operations Google workbook.

---

# Product intake form

## A. Required identity

- Product name:
- Canonical product ID, lowercase with hyphens:
- Canonical website URL:
- Product status: live / beta / waitlist / other
- Date the public product page was checked:

## B. Evidence sources

List current first-party sources the Agent may read to verify product facts and copy.

- Public homepage:
- Pricing page:
- Documentation or feature page:
- Terms, About, or company page:
- Local repository or source file paths:
- Other approved evidence:
- Facts explicitly confirmed by the user, with confirmation date:

## C. Core product copy

- Tagline:
- Short description, roughly 150–200 characters:
- Full description, roughly 400–800 characters:
- Primary problem solved:
- Main differentiation:
- Standalone boundary statement describing what the product does not provide:

If copy is not supplied, may the Agent draft it from the approved evidence? yes / no

## D. Current features

List only live capabilities. Put planned capabilities under “Not currently supported.”

- Feature 1:
- Feature 2:
- Feature 3:
- Additional features:
- Not currently supported:

## E. Audience and taxonomy

- Primary users:
- Main use cases:
- Preferred category:
- Safe fallback categories:
- Core tags:
- Feature tags:
- Audience or use-case tags:
- Categories or tags that would be misleading:

## F. Product and company facts

For each supplied fact, include its source or state that the user confirmed it. Leave unknown optional facts blank.

- Product launch year:
- Product start month:
- Country or region, and whether it describes the product or legal entity:
- Company or publisher:
- Founder or team description:
- Team size:
- Business model: free / freemium / paid / subscription / other
- Current price, free credits, trial, or offer:
- Funding status:
- Supported platforms: Web / iOS / Android / macOS / Windows / other
- Other directory facts:

## G. Brand and backlink rules

- Required product spelling and capitalization:
- Prohibited names or terms:
- Clean backlink target, if different from the canonical website:
- Approved brand anchor:
- Approved editorial contextual anchors:
- Prohibited anchors:
- Use the standard UTM rule? yes / no
- Product-specific UTM exception:
- Approved positioning:
- Unsupported claims that must never be made:
- Required disclosure or boundary sentence:
- Copy tone or call-to-action restrictions:

Standard contextual UTM rule:

```text
<canonical-url>?utm_source=<platform>&utm_medium=referral&utm_campaign=backlink
```

Website and canonical URL fields continue to use the clean URL.

## H. Approved assets

If no public upload is currently approved, write `none approved` and omit the asset folders from the finished package.

For every asset, provide:

- Local file path:
- Intended role: logo / cover / screenshot / product example / workflow / use case / other
- Source and rights:
- Public upload permission and scope:
- Caption or alt text:
- Capture or creation date:
- Crop, size, privacy, or route limitation:

Additional assets may be listed by repeating the fields above.

## I. Package-specific instructions

- Required reading order exception:
- Product-specific routing instruction:
- Fact that must be rechecked before every submission:
- Other package instruction:

## J. Optional campaign and source-list authorization

Leave this section blank when the task is only to create the reusable product package. Supplying destinations without a complete authorization creates a source input, not permission to submit or publish.

- Campaign ID:
- Campaign or route name:
- Source-list reference:
- Route: directory / article / social
- Destination names and clean URLs:
- Account alias:
- Contact fallback alias:
- Authorization reference:
- Approver alias:
- Approved at, including timezone:
- Authorization expires, including timezone:
- Authorized actions: inspect / sign in / register / fill / upload / draft / schedule / submit / publish / verify
- Explicitly excluded actions:
- Approved asset paths for this route:
- Category, disclosure, or route restrictions:
- CAPTCHA or native-verification handoff rule:

Payments, credit consumption, reciprocal-link changes, DNS changes, account-setting changes, and publication outside the named scope require separate explicit authorization.
