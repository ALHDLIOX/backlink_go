# Groxen asset manifest

Updated: 2026-09-24

The effect images use four fictional inputs and actual outputs from Groxen’s Kie model, production prompt, and provider options. The existing public-figure gallery informed the four-panel layout but is excluded from this package. Check each destination’s image and rights rules before upload; this package alone does not authorize a public upload.

## Asset inventory

“Route approval” means an asset can be considered for an authorized destination after checking its format, size, crop, and rights rules. “Reference only” identifies source proof, not a recommended listing image.

| Repository path | Role | Dimensions | Size | MIME type | Public upload | Source and rights | Caption or alt text | Crop or route notes |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| images/groxen-logo.svg | Vector logo | 512×512 viewBox | 333 B | image/svg+xml | Route approval | Exact first-party public/logo.svg copy | Groxen two-eye logo on peach | Use if SVG is accepted; preserve both eyes. |
| images/groxen-logo-180.png | Small PNG logo | 180×180 | 4,011 B | image/png | Route approval | Exact first-party public/apple-touch-icon.png copy | Groxen two-eye logo on peach | Use if 180 px meets the minimum. |
| images/groxen-logo-512.png | Standard PNG logo | 512×512 | 16,277 B | image/png | Route approval | Rasterized from first-party logo.svg | Groxen two-eye logo on peach | Preferred PNG logo; preserve rounded square. |
| images/groxen-social-cover-1200x630.png | English social cover | 1200×630 | 533,606 B | image/png | Route approval | Exact first-party public/og-groxen-v2.png copy | Groxen cover with “Any photo. A tiny bot.” | Keep text and avatar; not a screenshot. |
| images/01-four-panel-demo-2048.png | Four-panel master | 2048×2048 | 3,963,032 B | image/png | Route approval | Pixel-preserving composition of four actual outputs below | Four fictional Groxen bot avatar examples | Keep all four panels visible. |
| images/01-four-panel-demo-1200.jpg | Four-panel web version | 1200×1200 | 100,830 B | image/jpeg | Route approval | Resized JPEG from the four-panel master | Four fictional Groxen bot avatar examples | Preferred main directory gallery image. |
| images/02-before-after-person.png | Person comparison | 1480×820 | 1,316,243 B | image/png | Route approval | Fictional portrait plus actual matching Groxen output | Fictional person with teal glasses transformed into a bot avatar | Keep “Fictional input” and “Groxen output” labels. |
| images/02-before-after-pet.png | Pet comparison | 1480×820 | 1,457,370 B | image/png | Route approval | Fictional cat plus actual matching Groxen output | Fictional orange cat transformed into a bot avatar | Keep labels and demonstration caption. |
| images/03-three-step-workflow-1200x630.png | Illustrated workflow | 1200×630 | 278,182 B | image/png | Route approval | Fictional input, first-party logo, and actual matching output | Upload, generate, and download a square avatar | Illustration, not an interface screenshot. |
| screenshots/01-homepage-upload.png | Homepage screenshot | 1440×900 | 156,076 B | image/png | Route approval | Captured from https://grokboticon.com/ on 2026-09-24 | Groxen public upload interface | Recapture if the page changes. |
| screenshots/02-pricing.png | Pricing screenshot | 1440×1200 | 115,956 B | image/png | Route approval | Captured from https://grokboticon.com/pricing on 2026-09-24 | Groxen credit packs and sign-up offer | Recheck prices and offer before use. |
| screenshots/03-how-it-works.png | Workflow screenshot | 1440×900 | 132,523 B | image/png | Route approval | Captured from the public homepage on 2026-09-24 | Groxen’s three-step instructions | Authentic page section. |
| images/inputs/fictional-woman-glasses.jpg | Demo source | 1024×1024 | 123,607 B | image/jpeg | Reference only | AI-generated fictional portrait for this package | Fictional woman with dark bob and teal glasses | Source for person comparison. |
| images/inputs/fictional-man-beard.jpg | Demo source | 1024×1024 | 100,662 B | image/jpeg | Reference only | AI-generated fictional portrait for this package | Fictional man with curly hair and a beard | Source for individual output. |
| images/inputs/fictional-orange-cat.jpg | Demo source | 1024×1024 | 153,284 B | image/jpeg | Reference only | AI-generated fictional pet portrait for this package | Fictional orange tabby cat | Source for pet comparison. |
| images/inputs/original-purple-dragon.jpg | Demo source | 1024×1024 | 80,746 B | image/jpeg | Reference only | AI-generated original mascot for this package | Purple dragon mascot with teal scarf | Source for individual output. |
| images/outputs/fictional-woman-glasses-bot-icon.png | Individual output | 1254×1254 | 1,161,057 B | image/png | Route approval | Actual Groxen-model output from matching fictional input | Bot avatar with dark bob and teal glasses | Do not label as customer work. |
| images/outputs/fictional-man-beard-bot-icon.png | Individual output | 1254×1254 | 1,064,905 B | image/png | Route approval | Actual Groxen-model output from matching fictional input | Bot avatar with curly hair and beard | Preserve face and capsule eyes. |
| images/outputs/fictional-orange-cat-bot-icon.png | Individual output | 1024×1024 | 911,027 B | image/png | Route approval | Actual Groxen-model output from matching fictional input | Orange cat bot avatar | Preserve ears and capsule eyes. |
| images/outputs/original-purple-dragon-bot-icon.png | Individual output | 1254×1254 | 1,048,129 B | image/png | Route approval | Actual Groxen-model output from matching original mascot | Purple dragon bot avatar | Preserve horns and capsule eyes. |

## Upload order and selection

1. Logo: images/groxen-logo-512.png; use SVG if the destination accepts it.
2. Main gallery: images/01-four-panel-demo-1200.jpg; use the 2048 PNG for a large-image requirement.
3. Additional gallery: images/02-before-after-person.png, images/02-before-after-pet.png, then screenshots/01-homepage-upload.png.
4. Workflow slot: screenshots/03-how-it-works.png for a true screenshot or images/03-three-step-workflow-1200x630.png if illustration is accepted.
5. Cover slot: images/groxen-social-cover-1200x630.png.
6. Pricing screenshot only when the route needs it, after rechecking current terms.

## Route mapping

| Field | Preferred asset | Check |
| --- | --- | --- |
| Directory logo | images/groxen-logo-512.png | Square crop, minimum size, first-party mark. |
| Product gallery | images/01-four-panel-demo-1200.jpg | Four fictional examples from actual Groxen outputs. |
| Before/after | images/02-before-after-person.png and images/02-before-after-pet.png | Preserve labels and state that inputs are fictional. |
| Product interface | screenshots/01-homepage-upload.png | Current public UI; recapture after a design change. |
| How it works | screenshots/03-how-it-works.png | Actual page screenshot; do not relabel the illustration as a screenshot. |
| Banner | images/groxen-social-cover-1200x630.png | Promotional artwork, not a customer result. |

## Provenance and authenticity

- Four source images were created with OpenAI image generation as fictional demonstrations on 2026-09-24. They contain no real person, customer upload, or user account content. The source files were resized to JPEG and supplied to Kie through public repository URLs.
- Four outputs were generated directly through KieProvider using BOT_ICON_PROMPT, BOT_ICON_MODEL, and BOT_ICON_OPTIONS from the Groxen repository on 2026-09-24. They were not generated through a customer account. The provider returned square files of 1024 or 1254 pixels despite a 1K resolution option; actual dimensions are listed above.
- The four-panel master places resized outputs on a charcoal grid; the JPEG is a resize of the master. The comparisons place the corresponding source and result side by side. The workflow graphic uses one genuine conversion. No product output was repainted.
- Screenshots show public pages only. Visual inspection found no account name, email, token, private URL, session identifier, or customer content.
- The separate public-figure gallery in Groxen’s public/imgs/gallery-bot-icons/ was a visual reference only. Promotional likeness and input-image rights need separate review before external use.
- Do not present fictional demonstrations as testimonials, customer work, or guaranteed resemblance. Recheck pricing, sign-up credits, UI, destination rules, and final crops before publishing.
