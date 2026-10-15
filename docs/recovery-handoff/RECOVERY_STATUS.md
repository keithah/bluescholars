# Blue Scholars — recovery status

Reference: https://web.archive.org/web/20210529010817/http://bluescholars.com/

Updated October 15, 2026. The requested destination is GitHub Pages. The user has authorized searching other dates and linked pages/images for recovery.

## What this handoff contains

This is a **research inventory and proposed restoration design**, not a restored website or a source-code implementation. It contains no downloaded site HTML, photographs, stylesheets, fonts, or video files. Nothing has been deployed or written to GitHub.

## Confirmed observations

The main navigation contains Blog, Shows, Video, Shop and Holler. The homepage photograph can be displayed in the web reader. Blog, Shows, Video and Holler have readable archived page structures, although some image requests fail. Shop resolves to a historical provider error.

Two readable blog listing pages contain 20 entries each, spanning publication dates from January 12 to September 9, 2013. This is a count of entries in those two listings, not a total site post count. The September 2013 Eugene article also has a readable individual permalink.

The next pagination URL, `/blog?offset=1358016466000`, resolves to a July 19, 2019 provider error. Its replay toolbar reports an earlier capture on June 11, 2016. The earlier capture could not be inspected; its precise timestamp and content are unknown.

Eleven YouTube embed references are recorded from the Video page. They are links, not recovered playable video files. Two player replays resolved to later dates than the homepage reference; do not mistake their replay dates for dates of content on the 2021 website.

## Local recovery limitation

Raw downloads failed in this session: direct requests could not resolve the archive host, the file-download tool failed for the homepage HTML and image, and archive-wide index requests were inaccessible in the web reader. Individual replay text was readable, and two images had displayed in the web tool, but no successful local binary download is claimed.

A GitHub Actions runner or another network-enabled environment is a proposed next location for recovery. Access and success there have not been tested. A resumable recovery process must handle throttling, errors and incomplete results; it must not deploy a partially crawled result automatically.

## Distinguish these states

- `page_observed`: replay structure/text was readable, not raw HTML downloaded.
- `image_opened_in_web_tool`: an image displayed, not a local binary saved.
- `archived_error_page`: the observed capture contains a provider error, not intended site content.
- `archived_url_returned_404`: that image request failed; other captures/variants remain untested.
- `inaccessible_probe`: the tool could not inspect a requested URL; no conclusion about the original content follows.

Exact source URLs, dates, image references and video IDs are in `recovery-inventory.json`. `recovery-queue.csv` is a machine-readable seed list, not the full archive URL index.

## Immediate next input

The target GitHub repository URL is needed before repository work. A search of connected repositories for `bluescholars` returned no matches. No unrelated repository has been modified.
