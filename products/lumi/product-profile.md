# LUMI — verified product profile

Updated: 2026-09-20

Copy only field values, not headings or evidence notes. Recheck changeable facts on the submission day. This package describes the legacy public product selected by the user, not the `tan` preview.

## Product identity

| Field | Approved value | Evidence and reuse boundary |
| --- | --- | --- |
| Canonical product ID | `lumi` | User confirmed this stable package identifier on 2026-09-20. |
| Product name | LUMI | User confirmed the name on 2026-09-20; preserve capitalization. |
| Official landing page | https://raumplaner.io/ | User confirmed the clean URL on 2026-09-20. |
| Product status | Live public web app, legacy version | User confirmed the product is live on 2026-09-20; recheck availability before submission. |
| Company or publisher | ColorMon LLC | User confirmed the exact legal spelling on 2026-09-20. |
| Founded or product launch year | Product launched in 2025 | User confirmed December 2025 as the product launch; this is not a legal incorporation date. |
| Started | December 2025 | Product launch month, user-confirmed on 2026-09-20. |
| Country or region | Delaware, United States | Legal-entity jurisdiction supplied by the user on 2026-09-20; product operating region is unknown. |
| Founder or team description | Ethan is the only team member; founder status unknown — leave blank on submission | User confirmed team composition on 2026-09-20; do not infer legal ownership. |
| Team size | 1 | User-confirmed on 2026-09-20; recheck if a form requires it. |
| Business model | Freemium: two free credits after registration, with one-time paid credit packs | User confirmed the free allowance, 30-day free-credit validity, discontinued legacy subscriptions, and public pack purchase availability on 2026-09-20. |
| Current price and credit terms | Mini USD $9 / 80 credits; Popular USD $19 / 200 credits; Pro USD $49 / 600 credits | User confirmed USD and that these packs are publicly purchasable on 2026-09-20. See the dated offer details below; recheck before submission. |
| Funding | No external funding | User-confirmed on 2026-09-20; do not infer revenue or profitability. |
| Platform | Web only | User confirmed there are no native iOS, Android, macOS, or Windows clients on 2026-09-20. |
| Public asset upload | Package assets identified; route approval required before upload | The user authorized selection from the project on 2026-09-20. No destination or public-upload scope was supplied. See `asset-manifest.md`. |
| Preferred category | AI Interior Design | Suggested from the photo-based room redesign workflow; use only when the destination taxonomy fits. |
| Safe broad fallback | Room Planner; AI Design Tool | Visual room concepts and AI image generation are supported; do not imply measured planning. |

## Product name

LUMI

Character count: 4. Known destination limit: not applicable — no destination supplied.

## Tagline

See new room styles in your own space

Character count: 37. Recommended target: 60 characters or fewer unless a destination specifies another limit.

## Short description

LUMI helps homeowners and renters explore room design ideas from a photo. Choose a style, generate visual options, and compare results with the original before making changes.

Character count: 175. Use for a directory field that allows this length.

## Full description

LUMI is a browser-based AI room planner for homeowners, renters, and people exploring interior design ideas. Upload a photo of a real room or select an image from a saved project, choose a room type and style, and add optional instructions or furniture references. The app generates visual concepts that you can compare with the original, revisit in a project, and download. It is useful for discussing color, furniture direction, and possible layouts before buying or renovating. Results are illustrative; LUMI does not provide measured floor plans, verified furniture fit, or construction approval.

Character count: 600. Use for a directory field that allows this length.

## Current credit offer

The user confirmed the following prices, USD currency, and public purchase availability on 2026-09-20. Pack amounts and benefits appear in the user-provided pricing screenshot.

| Pack | Price (USD) | Credits |
| --- | ---: | ---: |
| Mini | $9 | 80 |
| Popular | $19 | 200 |
| Pro | $49 | 600 |

The screenshot states that each design uses one credit, the listed packs require no subscription, paid-pack results have no watermark, and purchased credits never expire. The user confirmed that accounts receive two free credits after registration; these are valid for 30 days and free-credit results carry a watermark. The old subscription plans have been discontinued. Do not apply the purchased-credit expiry or watermark terms to free credits.

## Features

Select only features that the destination field can represent and that are currently available in the legacy product.

- **Room-image input** — Upload a room image or select an existing image from a saved project.
- **Style and room-type choices** — Set a visual direction and optionally describe the desired change.
- **Furniture references** — Add optional furniture items with descriptions and reference images to guide a generation.
- **Floor-plan visualization** — Turn a floor-plan image into an illustrative room design concept; no measured or editable 3D model is provided.
- **Empty-room mode** — Explore a furnished concept from an empty room image.
- **Visual comparison** — Compare a generated image with its source image in the browser.
- **Projects and downloads** — Keep generated images in projects and download individual results.

### Compact feature line

Room-image upload, floor-plan visualization, empty-room mode, style presets, furniture references, before-and-after comparison, saved projects, image downloads

### Claims withheld pending workflow verification

Do not list public share links, collaboration, measured floor-plan editing, or editable 3D modeling as current features solely because marketing text mentions them. The inspected legacy UI and server paths did not verify those complete workflows.

## Standalone boundary statement

LUMI creates visual room design concepts from images; it does not provide scale-accurate plans, verified furniture fit, or construction approval. Check dimensions, materials, and feasibility separately.

## Target market

Homeowners, renters, and people exploring interior design ideas. Typical uses are comparing styles in an existing room, discussing furniture direction, and preparing a visual reference before shopping or renovating.

## Categories and tags

Choose the closest available category and only relevant tags. Do not paste the entire list into every destination.

- Primary category options: AI Interior Design; Room Visualizer.
- Secondary category options: Room Planner; AI Design Tool.
- Core tags: AI room planner, interior design, room visualizer.
- Feature tags: photo-based redesign, floor-plan visualization, empty-room mode, style presets, furniture references, before-and-after comparison, saved projects, image download.
- Audience or use-case tags: homeowners, renters, room makeover, decorating ideas.
- Do not select: CAD Software, Floor Plan Editor, 3D Modeling, Furniture Marketplace, Contractor Service, free without sign-up.

## Submission accuracy notes

- Pricing and offer checked on: 2026-09-20 against a user-provided pricing screenshot and explicit user confirmation of USD, two free credits after registration (30-day validity, watermarked results), discontinued subscriptions, and live purchase availability. The older indexed [public pricing page](https://raumplaner.io/pricing) showed different offers. Recheck the public offer before each submission.
- Public product page checked on: 2026-09-20 through indexed first-party [homepage](https://raumplaner.io/) and [room-planner page](https://raumplaner.io/en/room-planner-online); direct network fetch was unavailable. Recheck the live page before submission.
- Primary product evidence: [public room-planner page](https://raumplaner.io/en/room-planner-online); legacy [ALHDLIOX/raumplaner source commit](https://github.com/ALHDLIOX/raumplaner/commit/6d78fd26ace27f79da5f025b9bf604e65ad3b256) paths `src/shared/blocks/room-planner/room-planner-context.tsx`, `room-planner-content.tsx`, `sidebar-image-section.tsx`, `sidebar-furniture-section.tsx`, `src/shared/blocks/projects/project-detail.tsx`, and `src/app/api/projects/route.ts`.
- User-confirmed facts and confirmation date: Product name LUMI, product ID `lumi`, canonical URL `https://raumplaner.io/`, legacy-version scope, live product status, company name ColorMon LLC, December 2025 product launch, Delaware legal-entity jurisdiction, one-person team led by Ethan, no external funding, Web-only platform, floor-plan visualization, empty-room mode, public purchase availability, USD pricing, two free credits on registration, 30-day free-credit validity, and free-result watermark were confirmed on 2026-09-20.
- Required unknowns that block submission: None for the reusable package. If a destination requires a founder, legal incorporation date, product operating region, or another unconfirmed legal fact, obtain current evidence or user confirmation.
- Additional route-specific limitations: No destination list, campaign authorization, contact alias, or public-upload scope was supplied. The files in `images/` are selected package assets only. This package is reusable source material, not a submission or placement record.
