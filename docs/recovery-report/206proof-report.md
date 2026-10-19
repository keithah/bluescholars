# 206proof.com recovery checkpoint

**Status:** initial source discovery and a small number of raw replay captures. The site has not yet been reconstructed or published.

## Archive inventory

On 2026-10-19 UTC, the Internet Archive CDX endpoint returned 6,829 rows for `206proof.com/*`, filtered to HTTP 200 and collapsed by URL key. The response covered 5,926 HTML URL keys, 803 image URL keys (636 JPEG, 84 GIF, 83 PNG), 37 CSS, 53 JavaScript, one XML, and seven `audio/mpeg` records. The collapsed rows span 2007–2026, with the largest groups in 2010 (3,016), 2008 (1,357), and 2013 (1,029).

This is a useful URL-key inventory, **not** every capture event, a verified complete domain history, or proof each response contains valid page/media bytes. The 2018–2026 tail includes parked, injected, and other later content and must not be presented as the original community. Preserve those rows as evidence only. A second uncollapsed/paginated query is still needed to inspect alternate captures URL by URL.

## Confirmed historical structures

- A 2007 Vanilla 1.1.3 forum home at `http://206proof.com:80/`; its source identifies four categories and reports 687 discussions, 15,107 comments, and 284 users. These are values shown in that capture, not independently verified statistics.
- A much larger Vanilla forum under `/forum/`, indexed from 2008 through 2012. The CDX URL-key inventory includes thousands of routes, discussion comment pages, account pages, and uploaded images. It includes 39 indexed pages for the long `DiscussionID=988` conversation.
- A 2012–2013 community-site phase with `/discussion/...`, profile/activity routes and RSS, followed by a separate vBulletin forum under `/4um/` in 2013–2014. The 2013 vBulletin index has board captures including `206proof`, `Archive`, and `Shut up and drink your coffee`; captured rows include a “Macklemore Appreciation Thread.”
- Seven MP3 records appear in CDX, with a combined indexed length of 37,849,738 bytes. None has been retrieved or validated as playable audio, so they remain acquisition leads rather than recovered media.

## Raw files saved

`recovery/206proof/recovered-pages.json` maps the following untouched replay bodies to original URLs, requested timestamps, byte lengths, and SHA-256 hashes:

- 2007 Vanilla home/discussions (`20071012230232`)
- 2013 vBulletin `/4um/` index (`20130824231448`)
- Two Vanilla `/forum/` home responses reached through replay requests (`20101120112507` and `20100111052533`)

The archive replay server began refusing new connections after those initial responses. Other board, discussion, topic, CSS/image, and audio payloads have not yet been saved. The two `/forum/` rows above should be re-requested later using their exact CDX timestamps because the first replay calls were issued against a nearby requested time and the archive redirected them to those actual captures.

The full captured CDX response, parsed inventory, and saved raw bodies are under the local ignored `recovery/206proof/` checkpoint. They are resumable working evidence and are not currently included in the Git repository.

## Independent leads and next recovery actions

Contemporaneous references corroborate that 206proof was part of Seattle hip-hop discussion: Seattle Weekly described its forum in 2009, and a 206 Zulu archive refers to a 206 Proof contributor. A secondary reference points to the notable `DiscussionID=988` thread. These references are discovery leads, not substitutes for original archived content.

Resume by:

1. Querying CDX without `collapse`, paging with resume keys, and retaining all capture timestamps/digests and status codes.
2. Recovering `/forum/` captures by edition, first the 2007–2009 discussion listings and then 2010–2012 topic/comment routes; explicitly inspect every page of the 39-page DiscussionID 988 thread.
3. Recovering `/discussion/` and `/4um/` separately, including linked boards, threads, CSS, images, and upload dependencies.
4. Retrying each indexed MP3 independently; validate actual audio bytes and document rights/availability before any publication.
5. Searching source-linked contemporary sites for exact 206proof URLs and image/media references, then checking those exact paths in Wayback and other archives.
6. Building only after enough original pages and assets are actually recovered to support a faithful static edition; retain missing routes and asset gaps as explicit gaps.

## Sources

- [Internet Archive capture index for 206proof.com](https://web.archive.org/cdx/search/cdx?url=206proof.com%2F%2A&output=json&fl=timestamp%2Coriginal%2Cmimetype%2Cstatuscode%2Cdigest%2Clength&filter=statuscode%3A200&collapse=urlkey)
- [2007 homepage replay](https://web.archive.org/web/20071012230232/http://206proof.com/)
- [2013 vBulletin forum replay](https://web.archive.org/web/20130824231448/http://www.206proof.com/4um/)
- [Seattle Weekly, March 25, 2009](https://www.seattleweekly.com/2009/03/25/a-while-back-i-wrote-a-profile-of-everett-based-mc-ripynt-pronounced/)
- [206 Zulu archive page](https://www.206zulu.org/page/81/?eventDisplay=past&tribe-bar-date=2020-07-27)
- [Secondary reference to the long-running DiscussionID 988 topic](https://en-academic.com/dic.nsf/enwiki/9841790/)
