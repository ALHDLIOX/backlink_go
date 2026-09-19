# Product backlink package rules and template guide

This directory is the canonical starting point for a product backlink package. A package supplies verified product facts, approved public copy, link rules, reusable assets, and bounded campaign inputs to Backlink Operations V1.

It is an input package, not a submission tracker. Google Sheets remains the only writable source of truth for Campaigns, Platforms, Placements, and Events.

## Create a product package

1. Copy this directory to `products/<product-id>/`.
2. Rename `<product-id>` to a stable lowercase identifier, such as `example-product`.
3. Replace every `{{PLACEHOLDER}}` in the copied files.
4. Verify claims against current first-party or user-confirmed evidence.
5. Delete `PACKAGE-GUIDE.md`, template instructions, and conditional files that do not apply.
6. Put real account or contact values only in `.backlink-go/private/product-aliases.json`; keep aliases in the package.
7. Before a live campaign, create a bounded source-list file and record the Campaign in Google Sheets.

Do not leave unresolved placeholders in a live package. Use `unknown — leave blank on submission` for optional unknown facts and `not applicable — <reason>` when a field truly does not apply. A required unknown blocks the corresponding submission field; never invent a value.

## Standard folder structure

```text
products/<product-id>/
├── README.md                         # Required: package identity and reading order
├── product-profile.md                # Required: verified facts and copy variants
├── brand-rules.md                    # Required before preparing public copy or links
├── asset-manifest.md                 # Required when any route may upload media
├── images/
│   └── README.md                     # Image requirements; replace with approved assets
├── screenshots/
│   └── README.md                     # Screenshot requirements; replace with approved captures
└── source-lists/
    ├── README.md                     # Source-list naming and scope rules
    └── source-list-template.md        # Copy once per bounded campaign or route
```

Binary assets are not included in this template. Keep each directory README until its requirements have been transferred into `asset-manifest.md`; it may then be removed from the product package.

`PACKAGE-GUIDE.md` exists only in the canonical template and is not part of a finished product package.

## File requirements

| File | When required | What it contains | Must not contain |
| --- | --- | --- | --- |
| `README.md` | Always | Canonical product ID and URL, file reading order, package-specific instructions | Submission status, credentials, raw contact details |
| `product-profile.md` | Always | Verified facts, descriptions by length, features, audience, categories, tags, unsupported claims | Invented company, founder, pricing, launch, legal, or performance facts |
| `brand-rules.md` | Before public copy or linking | Product spelling, backlink target, anchor rules, UTM policy, claim boundaries | Keyword quotas presented as guarantees, unsupported SEO claims |
| `asset-manifest.md` | When uploads may occur | Approved file inventory, dimensions, MIME type, provenance, captions, upload order | Unapproved or unverifiable assets, private customer material |
| `images/*` | When a route needs public images | Approved logos, covers, illustrations, and product examples | Credentials, private exports, assets without reuse permission |
| `screenshots/*` | When a route needs UI evidence | Approved current product screenshots | Private user data, session details, tokens, private URLs |
| `source-lists/*.md` | Before each campaign or route | Destination scope, aliases, authorization boundary, approval and expiry | Passwords, OTPs, emails, cookies, auth URLs, live progress logs |

## Required evidence standard

- Mark each material fact as verified from a current first-party source, explicitly confirmed by the user, or unknown.
- Add a date to facts that can change, including price, free credits, launch state, platform availability, team size, and upload permission.
- Separate a product launch date from a legal incorporation date.
- Separate product capabilities from planned features.
- Record unsupported claims and prohibited categories explicitly so forms do not imply them.
- Recheck changing facts on the day of submission.

## Privacy and record boundaries

Committed product packages may contain public or repository-safe information only. Reference account and contact aliases such as `account-primary` or `product-public-contact`; resolve their real values from `.backlink-go/private/product-aliases.json` only immediately before an authorized action.

Never commit or record raw email addresses, passwords, OTPs, recovery codes, cookies, OAuth parameters, magic links, tokenized URLs, private browser identifiers, or Gmail content.

Do not write submission results into this package. Record queued, submitted, approved, published, blocked, and verification results through `submit-product-directories-v1-batch/scripts/sheets_record.py` in the configured Backlink Operations workbook.
