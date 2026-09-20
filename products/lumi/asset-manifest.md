# LUMI asset manifest

Updated: 2026-09-20

The user authorized selecting logos from this project and requested replacement marketing illustrations generated in the public website's visual style on 2026-09-20. The two logos are first-party project assets. The two concept images were newly generated for this package with the built-in image-generation tool, using `public/imgs/features/introduction.webp` and `public/imgs/background.webp` as style references only. The user then approved an OG version with LUMI and the verified tagline, and provided a split-layout reference with a solid-color text panel. No destination, campaign, or public-upload scope was supplied; obtain route authorization before uploading any file. Check the destination's current size, format, and crop requirements at that time.

## Asset inventory

| Repository path | Role | Dimensions | Size | MIME type | Public upload | Source and rights | Caption or alt text | Crop or route notes |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `images/lumi-logo-light.png` | Square logo for light backgrounds | 512×512 | 39,511 B | `image/png` | Route approval required | Copy of `public/logo/logo_light.png`; first-party project logo, selected with user authorization | LUMI logo, dark brown symbol | Transparent background; verify contrast on the destination. |
| `images/lumi-logo-dark.png` | Square logo for dark backgrounds | 512×512 | 36,988 B | `image/png` | Route approval required | Copy of `public/logo/logo_dark.png`; first-party project logo, selected with user authorization | LUMI logo, cream symbol | Transparent background; verify contrast on the destination. |
| `images/room-redesign-concept.png` | Generated room-redesign concept | 1672×941 | 2,130,158 B | `image/png` | Route approval required | Newly generated on 2026-09-20 using first-party website style references; user requested this replacement | Concept illustration of a sunlit room transitioning from a plain space to a warm minimalist living area | Do not label as a captured app screen, customer project, or verified AI output. Keep the furnished area visible in crops. |
| `images/room-redesign-og.png` | OG image derived from room-redesign concept | 1200×630 | 1,092,473 B | `image/png` | Route approval required | Derived on 2026-09-20 from `images/room-redesign-concept.png`; typography and solid-color panel follow the user-provided layout reference | LUMI — See new room styles in your own space, beside a warm minimalist living room concept | Solid dark-brown left panel with text; right panel crops the room concept. Check both panels after destination cropping. |
| `images/floor-plan-concept.png` | Generated floor-plan concept | 1672×941 | 2,051,024 B | `image/png` | Route approval required | Newly generated on 2026-09-20 using first-party website style references; user requested this replacement | Concept illustration of a paper floor plan in front of a furnished living room | The plan is illustrative, not measured or editable. Do not label as a captured app screen or verified AI output. |

The original logo creation dates are unknown. The logo copies and generated concept images were selected on 2026-09-20. No current product screenshots are included.

## Upload order and selection

1. Logo field: use `lumi-logo-light.png` on a light background or `lumi-logo-dark.png` on a dark background.
2. OG or social preview image: `room-redesign-og.png`, if the destination accepts generated marketing illustrations and the text remains legible in its preview crop.
3. Primary text-free cover or gallery image: `room-redesign-concept.png`, if the destination accepts generated marketing illustrations.
4. Additional gallery image: `floor-plan-concept.png`, if the destination accepts generated marketing illustrations.
5. If only one image is permitted, use the appropriate logo for a logo field, the OG derivative for a social preview field, or the text-free room concept for a cover field. Do not use an illustration in a field that requires a real interface screenshot.

## Route mapping

| Route or field | Preferred asset | Required | Attribution and crop check |
| --- | --- | --- | --- |
| Directory logo | `images/lumi-logo-light.png` or `images/lumi-logo-dark.png` | Conditional | Obtain route approval; choose by background contrast and keep the symbol intact. |
| OG or social preview | `images/room-redesign-og.png` | Conditional | Obtain route approval; verify the product name, tagline, and room image in the destination's preview crop. |
| Directory cover or gallery | `images/room-redesign-concept.png` | Conditional | Obtain route approval; identify it as a generated marketing concept and check the crop. |
| Additional workflow image | `images/floor-plan-concept.png` | Conditional | Obtain route approval; identify it as a generated marketing concept and check the crop. |
| Product screenshot | None | No asset available | Capture and approve an authentic current interface image if a route requires one. |

## Derived assets

- Preserve the original files in this package. Save resized or reformatted variants as new files and add them to this inventory with their source relationship.
- `images/room-redesign-og.png` is a 1200×630 split composition: a 468-pixel solid dark-brown text panel on the left and a crop of `images/room-redesign-concept.png` on the right. The headline has approximately 54 pixels of space on each side within the text panel. Its text uses the product name LUMI, the approved tagline “See new room styles in your own space,” the supported line “Explore room design ideas from your own photo,” and the canonical domain. The text-free source remains available for other covers.
- Do not imply that the generated illustrations are captured screens, customer work, or verified product output.
- Recheck image rights and destination terms before external use. The user's project-selection authorization does not specify a public-upload route.

## Privacy and authenticity checks

- Visual inspection on 2026-09-20 found no visible private user data, account names, emails, tokens, private URLs, or third-party marks in these five files.
- The two room images are generated marketing concepts. Their depicted spaces and paper plan should not be presented as actual app screens or customer examples.
- Check the final destination crop, logo contrast, file-type support, and file-size limit before upload.

## Generation prompts

- Room-redesign concept: a wide, photorealistic living room with a subtle plain-to-styled transition in one coherent space; warm ivory, sand, taupe, light oak, and cocoa; soft daylight; no interface, logo, text, people, or hard split panels.
- Floor-plan concept: a wide, photorealistic composition with a paper floor-plan sketch on a light oak surface and a warm minimalist living room beyond it; connect the two through depth of field; no interface, arrows, text, people, measurements, or CAD implication.
