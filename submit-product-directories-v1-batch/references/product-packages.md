# Project-local product packages

V1 product inputs live in the repository root under `products/<product-id>/`. This keeps product facts, brand rules, approved assets, source lists, and authorization references available to the Skill and to black-box test agents without depending on another project.

Use this layout when the corresponding material exists:

```text
products/<product-id>/
├── README.md
├── product-profile.md
├── brand-rules.md
├── asset-manifest.md
├── images/
├── screenshots/
└── source-lists/
```

Product packages contain public or repository-safe facts only. Do not commit raw email addresses, credentials, tokens, cookies, authentication URLs, or private browser-session identifiers.

Real values behind account and contact aliases live inside this repository checkout at `.backlink-go/private/product-aliases.json`. The directory is ignored by Git and each private file must use mode `0600`. The file maps stable aliases to real values used during authorized browser work. Never copy a resolved value into Google Sheets, events, evidence identifiers, command output, or a committed file.

Google Sheets remains the source of truth for campaigns, platforms, submissions, and events. Product packages are reusable inputs, not a second submission tracker. Historical Markdown records may remain in their source project for reference; do not migrate them into the V1 workbook automatically.
