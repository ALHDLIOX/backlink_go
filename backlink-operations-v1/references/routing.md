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

## Short social and unsupported routes

Pinterest pins, X posts, LinkedIn short posts, Instagram/Facebook posts, profile link edits, forum replies, comments, and community answers are unsupported execution targets in this version. Do not silently turn them into articles or directory records. Classify the platform as `social` where appropriate, explain that no supported execution lane exists, and do not publish. Do not create Campaign, Submission, Article, or Event rows. If a live preflight establishes every required reusable Platform field, only that Platform row may be upserted; otherwise report without a Sheets write.

Also reject or record `ineligible` for irrelevant channels, terms-prohibited automation, link networks, mass guest-post schemes, copied cross-posts, fake reviews, or content whose main purpose is manipulating rankings.

## Unknown

Use `unknown` only while capability is genuinely unresolved. Perform a read-only preflight. If no eligible directory or article route is found, stop with the observed reason rather than guessing a route.
