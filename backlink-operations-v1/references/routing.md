# Destination routing

Classify from the live destination and its current rules, not from the hostname alone.

When recording the result, use the URL's exact normalized hostname for `platform_domain`; preserve `www` when it is part of the actual hostname.

## Directory

Route to SPD V1 Batch when the primary action creates or claims a structured product, software, startup, app, AI-tool, or company listing. Directory signals include fixed product fields, categories, pricing, logo/screenshots, review/approval, and a public product profile.

`Platforms.platform_type` is `directory`, or `mixed` if the same platform also exposes a legitimate long-form editor.

## Article

Route to writer `ephemeral-publish` when the platform offers a user-controlled long-form editor and the proposed article can deliver standalone reader value. The first-version focus platforms are Blogger, Dev.to, Hashnode, Substack, and Medium.

Other platforms may enter the generic article lane only after live preflight confirms all of these:

- a real long-form post or article editor, not only a short status, pin, comment, bio, or link card;
- the account is permitted to publish the proposed subject and format;
- external links and any required disclosure are allowed;
- the content is relevant to the platform audience and is not disguised advertising, link spam, or a prohibited product promotion;
- the route is available without an unapproved payment, reciprocal link, subscription, or policy exception;
- a public result page can be reopened and verified after publication.

Use `platform_type: article`, or `mixed` when a directory listing lane also exists.

## Social

Route to the social lane when the primary action creates a Pinterest Pin, X/LinkedIn short post, image post, link post, or thread rather than a structured directory listing or standalone long-form article. Pinterest routes to `social` even when the Pin contains a title and substantial description; its image, Board, link-card behavior, and public Pin page define the lane.

Before entering a composer, live preflight must confirm all of these:

- the account and chosen Board/channel are in the user's authorized scope;
- the proposed product and link are relevant and permitted by current platform rules;
- the post is original and truthful, not fake engagement, an impersonation, or mass link spam;
- external links and required AI/content disclosures are supported;
- approved media is available when the post type requires it;
- the route needs no unapproved payment, promotion budget, new Board/community, or policy exception;
- a public result page can be reopened and its destination link verified after publication.

Use `platform_type: social`, or `mixed` only when the same platform also exposes another supported lane. Use `campaign_mode: social` for a social-only campaign. Read [social-publishing.md](social-publishing.md) before any composer action.

Profile-link edits, forum replies, comments, community answers, fake reviews, and unsolicited engagement remain unsupported. Do not silently turn them into social posts, articles, or directory records.

Also reject or record `ineligible` for irrelevant channels, terms-prohibited automation, link networks, mass guest-post schemes, copied cross-posts, fake reviews, or content whose main purpose is manipulating rankings.

## Unknown

Use `unknown` only while capability is genuinely unresolved. Perform a read-only preflight. If no eligible directory, article, or social route is found, stop with the observed reason rather than guessing a route.
