# Blue Scholars — proposed static restoration design

**Status:** Proposed design for review, not an implementation plan or completed site.  
**Date:** October 15, 2026.  
**Reference:** https://web.archive.org/web/20210529010817/http://bluescholars.com/

## 1. Intended result

Restore as much of the historical bluescholars.com website as the available captures permit, with the May 29, 2021 homepage as the visual reference. Recover missing pages and assets from other capture dates. Publish ordinary static HTML, CSS, images and minimal JavaScript on GitHub Pages.

This is a restoration, not a redesign or a new band storefront. Historical publication dates and credits stay historical. The build must distinguish recovered material from missing or reconstructed material.

The user explicitly selected the reference, authorized cross-date recovery and specified GitHub Pages. The read-only treatment of old shop and contact functionality is a proposed default, rather than a request to build a live commerce or messaging service.

## 2. Recommended approach

Use **recovered original markup, styles and assets with a static cleanup/build step**. This offers the closest route to the requested appearance while avoiding dependence on a running Squarespace account.

A literal web mirror would preserve markup quickly but may retain archive wrappers, lazy-loading code, dead remote dependencies, query-based pagination and nonfunctional forms. A fresh design would be easier to control but would not satisfy fidelity. Prefer targeted repairs to the original material, documenting each deliberate departure.

Do not choose typography, logo art, dimensions, colors, spacing or desktop/mobile geometry by guesswork. Recover and inspect the original CSS and rendered reference first. Any unavoidable substitute must be marked as a substitute in the recovery report.

## 3. Recovery scope and capture selection

Start with the whole bluescholars.com domain and its captured subdomains, both observed www/non-www and HTTP/HTTPS forms, plus source-linked asset origins. Inventory redirects as well as successful captures. Keep query strings: blog offsets identify different content.

Use the archive's capture index and follow links within recovered source. Enumerate the index in resumable batches, preserve its results and do not claim complete coverage after a truncated query. An index request can fail or return a service error; validate the response before processing it.

For each URL, record all candidate captures before choosing the preferred usable one. Do not collapse to the first or newest record and lose the alternatives needed to recover around errors. Download the selected response and validate its content, not merely its HTTP status.

Prefer the selected reference and compatible captures at or before May 29, 2021. Later captures may help recover the same historical asset, but require review and provenance. A later redesign or new content must not silently replace the historical site. Older site versions may provide missing material; do not merge their unrelated navigation and styles into the reference layout.

For embedded media, follow the exact asset URLs and dependencies discovered in HTML/CSS and structured page data. Include original Squarespace image URLs and source-linked Tumblr resources when observed. Try alternate capture dates, HTTP/HTTPS versions and documented or observed image-size variants. Do not strip arbitrary query strings or assume similarly named images are interchangeable.

Follow third-party page links when they help identify a missing asset or destination. Do not recursively mirror every external website or claim that material on another site originally appeared on Blue Scholars.

## 4. Acquisition and provenance

The recovery stage is separate from the static build. Store original responses without modifying them. Record original URL, requested capture, actual resolved capture, response type, local path, retrieval result, parent reference and content hash. Keep post publication date in a separate field.

Use a persistent manifest/checkpoint, conservative request pacing, retry limits, backoff and Retry-After handling. Failed attempts stay in a retry queue; successful files are not needlessly fetched again. An interrupted run must resume without losing the URL frontier. Deduplicate file bytes by hash while retaining every source-to-file mapping.

Reject provider error pages, archive errors, login/challenge pages and HTML returned where an image was expected. Do not infer permanent absence from one failed request. Report unresolved dependencies and which alternatives were attempted.

No original-site files have been downloaded successfully in this session. The existing JSON and CSV are reconnaissance seeds only; the full recovery stage remains to be run.

## 5. Static output

Keep the visible information architecture: homepage, Blog, Shows, Video, Shop and Holler. Preserve recoverable original article paths. Emit a real `index.html` for each directory-style route so direct visits and refreshes work without a single-page-application router.

Convert old query-string pagination into real pages such as `/blog/page/2/`. Rewrite internal navigation to those paths. Maintain a small explicit mapping for old `?offset=...` links so direct historical links reach the matching recovered page; do not invent destinations for unrecovered offsets.

All internal URLs and assets must work both under a GitHub project subpath and at a future custom-domain root. Configure the deployment base path rather than hardcoding `/assets/` everywhere. Do not add a CNAME or change DNS until the actual domain and ownership are confirmed.

Localize the recovered page images, CSS backgrounds and other core assets. Preserve relative CSS dependency paths or rewrite them through the asset map. Remove the Wayback toolbar and replay scripts, old analytics/tracking and nonessential platform code. Make lazy-loaded images render as normal HTML images. Preserve meaningful image descriptions and credits.

Record font-family declarations and source references. This handoff does not package font files. Typography must use authorized sources or explicitly documented fallbacks; fidelity is not established until the original declarations can be inspected.

Use minimal replacement JavaScript only for necessary behavior, such as the mobile menu and legacy pagination mapping. Ordinary content and navigation should remain usable without JavaScript. Old embedded scripts must be reviewed rather than automatically re-executed on the new domain.

## 6. Historical functionality and missing content

**Blog:** Preserve available text, dates, authors, links, credits, captions, image ordering and article relationships. Do not generate historical prose, captions or guessed permalinks to hide gaps. Existing untitled posts remain untitled unless the source provides a title.

**Shows:** Restore the historical page and posters that can be verified. Do not label old dates as upcoming events.

**Video/audio:** Preserve the original provider IDs and ordering. Optional external players may remain network-dependent, with ordinary outbound links as fallback. Do not claim that recovering an embed URL recovers its media file. Do not rehost third-party streams or bypass access restrictions.

**Shop:** Search other captures and observed historical shop destinations. Restore verified historical catalog material as read-only. Disable cart/checkout controls instead of leaving misleading working-looking buttons. If no usable capture is recovered, publish a clearly labeled archive gap rather than reproduce the provider error as the intended design.

**Holler/contact:** Preserve historical content with context. Review outbound links before enabling them, since old destinations can change. Do not send a contact form to an old backend or claim that archived email addresses and roles are current.

Unresolved images should have a restrained missing-asset treatment and a corresponding report entry. Never use invented band photos, logos, merchandise or event posters as recovered originals.

## 7. Repository and deployment boundaries

The repository should separate `recovery/` (manifest and acquisition metadata), `source/` (reviewed material/templates), `public/` (reviewed static assets), `scripts/` (recovery/build/checking tools), and `_site/` (generated publishable output). Actual names can be adapted to the target repository.

Keep source backups and potentially bulky raw recovery artifacts separate from the published directory. Publish only `_site/`, not the entire repository or raw crawl. Do not place tokens, logs or private configuration in output.

Use two deliberate workflows: a manually triggered recovery job that returns an artifact/report without deploying, and a build/validation/deployment workflow for reviewed content. GitHub supports custom Actions-based Pages publishing. Choose workflow versions and permissions from the current official documentation at implementation time.

No runtime backend, database, Squarespace subscription, WordPress installation or always-running server is proposed. An external media player is optional and separate from hosting the core site.

A target repository is not yet known. Do not create files in an unrelated project or enable public publishing as a side effect of an acquisition test.

## 8. Acceptance checks

Before calling the result restored or deployment-ready:

1. Confirm the selected sources and compare the homepage and representative section/article pages against rendered references on desktop and mobile.
2. Check every local HTML link, image, stylesheet and CSS dependency; distinguish optional external links from required local assets.
3. Verify core pages do not request archive.org or the old Squarespace runtime to display. Test with those origins blocked and test JavaScript-disabled navigation.
4. Test directory routes, article deep links, pagination mappings and a not-found page both at `/` and under the configured project subpath.
5. Check the mobile menu, image sizing, video fallbacks and disabled historical commerce/form controls.
6. Report counts of indexed URLs, downloaded files, rejected error captures, rendered pages and unresolved items. Never combine these categories into an inflated recovery count.
7. Review attributions and permission to republish. Preserve existing credits; an archived URL is not evidence of a public-domain license.
8. Publish only after the owner reviews the result. Verify the deployed URL separately from a successful build job.

## 9. Known gaps at this stage

Original CSS, logo, typography and rendered geometry are unverified. The full archive index and raw downloads are unavailable from this session. The third blog listing and Shop need alternate captures. Several image URLs failed. Video playback is unverified. No percentage-complete estimate is justified.

The next blocking input for repository work is the target GitHub repository URL. This design describes the proposed implementation; it does not assert that any recovery runner, build or deployment has already succeeded.

## Sources

- Reference homepage: https://web.archive.org/web/20210529010817/http://bluescholars.com/
- Blog: https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/
- Second listing: https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000
- Third listing error: https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000
- Video: https://web.archive.org/web/20200802161924/http://bluescholars.com/video
- Shop error: https://web.archive.org/web/20200718164929/http://bluescholars.com/shop
- Holler: https://web.archive.org/web/20200703230805/http://bluescholars.com/holler
- Archive capture-index documentation: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
- GitHub Pages overview: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- GitHub Pages workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
