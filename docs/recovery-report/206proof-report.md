# 206proof.com archive recovery checkpoint

**Updated:** 2026-10-19 UTC. This is a source-acquisition checkpoint, not a completed or published reconstruction. The site generations remain separate: the 2007 Vanilla 1.1.3 site, the 2008–2012 Vanilla `/forum/`, the 2012–2013 community routes, and the 2013–2014 vBulletin `/4um/` forum.

## Archive index coverage

The Wayback CDX query `206proof.com/*` was fetched uncollapsed with a 20,000-row limit and no resume key. It returned 19,874 capture events across all indexed statuses; 17,910 events have status 200. This establishes completion of that exact CDX query as returned, not all possible aliases, subdomains, external media hosts, or material absent from the archive. Both parsed responses, their query metadata, and response SHA-256 values are in `recovery/206proof/all-events-all-status.json`, `all-events-all-status.cdx.json`, `all-events-200.json`, and `all-events-200.cdx.json`.

The all-status response spans 2007–2026. Later parked, injected, and placeholder content is retained as index evidence but is excluded from the historical site editions. HTTP 200 alone is not treated as proof of usable page or media content.

## Validated source material saved

`recovery/206proof/recovered-resources.json` currently records 3,337 attempts: 3,328 payloads passed format checks and nine responses were rejected or undecodable. The validated records include:

- 2,430 HTML documents from the 2007 Vanilla site, 2008–2012 `/forum/`, 2012–2013 community routes, and 2013–2014 `/4um/` forum.
- 800 images and 91 CSS files, including Vanilla theme/extension styles, smileys, uploaded account pictures, community profile images, and vBulletin dependencies.
- Seven MP3 files with recognizable MP3 frame/ID3 signatures: six `SongOfTheWeek` uploads indexed in December 2010 and `poopintags.mp3` indexed in 2013. They are local preservation evidence only; playable redistribution has not been reviewed or approved.
- 3,075 unique SHA-256 payload hashes, summing 95,007,939 bytes across capture records. The raw directory occupies about 94 MB because identical payloads share files.

Every attempt retains requested timestamp, original URL, CDX metadata, resolved replay URL/actual timestamp when available, MIME/type validation, byte length, hash, local path, and errors. Nine failures remain recorded: three empty responses, four non-HTML/placeholder responses, and two invalid content-encoding responses. They are not counted as recovered pages.

The 2008–2012 Vanilla selector identifies 5,137 distinct exact URL records with query strings and host aliases preserved. It has attempted 1,360 selected records so far; 3,777 remain queued. Five recent batches added 440 validated pages, including discussion pages with query-string pagination. The route set is dominated by accounts and discussion pages. The 39-page `DiscussionID=988` thread and the 2013 vBulletin/community routes have separate records; this selector does not merge them into the Vanilla edition.

## Images, CSS, and linked media

Dependencies extracted from all 2,430 recovered HTML documents produce 31,271 page-to-asset references across 1,446 distinct same-domain CSS/image URLs. The saved all-status CDX rows contain a successful response for 629 of those URLs; 817 have no successful match in this query. The current manifest contains 891 image/CSS capture records (629 distinct normalized asset URLs). The machine-readable source/reference map is `recovery/206proof/asset-index.json`.

The media-lead scan found 404 YouTube IDs and 26 SoundCloud paths in captured HTML (430 distinct leads). These are source-linked references, not recovered playable media. Seven MP3 files are the only audio payloads validated so far. The lead list is `recovery/206proof/media-leads.json`.

## Local reconstruction candidate

The candidate renderer builds four separate generations from validated pages: 240 pages for 2007 Vanilla, 1,351 pages for the 2008–2012 Vanilla forum, 642 community pages, and 77 vBulletin pages. Captured HTML and local images/styles are preserved; scripts and posting forms are disabled; missing links lead to dated source-gap pages. When an exact query-string variant is absent, links may point to the closest recovered capture at the same path; the absent query variant is recorded rather than represented as exact. The latest build links 4,242 destinations without captured pages to clearly labeled gap pages. The exact 2007 Vanilla theme stylesheets have no successful captures in the indexed history; the 2007 pages therefore use the nearest recovered same-site Vanilla theme CSS from 2010, with a visible notice and provenance entries. The 2012 forum uses its own contemporaneous CSS captures.

The integrated `/bluescholars/` candidate passed the offline link and active-content check with zero errors after the latest 160-page recovery batch, and all 228 tests passed. The separately built root-mounted candidate also passed before the last two Vanilla batches (the latest included pages use the same renderer and routes). CI for commit `043a0208` passed its current source-only root and `/bluescholars/` checks; those release builds omit this unreviewed candidate material. Browser previews confirmed the main archive hub, the source-based 2007 Vanilla homepage, the 2012 Vanilla discussion index, and the 2014 vBulletin forum render with local assets. This is a browser smoke test, not human visual review, and it does not clear redistribution rights. No public release has been made from this candidate.

## Other archive and secondary-source checks

Arquivo.pt's saved host-history lookup returned 21 root records from 2019–2025; replaying the selected later response produced an archive portal rather than a historical forum page. Six bounded Common Crawl index requests were attempted; they returned timeouts or no matching captures, so no Common Crawl body is counted as recovered. The results are saved under `recovery/206proof/arquivo-pt-check.json` and `recovery/206proof/commoncrawl/`.

Independent contemporary sources help identify and contextualize lost pages but are not substitutes for 206proof captures: [206 Zulu's January 2008 bulletin](https://www.206zulu.org/nw-hip-hop-congress-january-bulletin/) names a 206 Proof contributor; the [October 2008 Basement Addicts post](https://basementaddicts.blogspot.com/2008/) quotes a forum exchange; [Seattle Weekly's 2009 article](https://www.seattleweekly.com/2009/03/25/a-while-back-i-wrote-a-profile-of-everett-based-mc-ripynt-pronounced/) refers to the forum; and a [secondary Seaclipse reference](https://en-academic.com/dic.nsf/enwiki/9841790/) points to `DiscussionID=988`. The 2011 [206 Zulu essay](https://www.206zulu.org/how-can-hip-hop-save-the-world-lessons-from-a-seattle-youth-service-scandal/) describes 206Proof's role in local hip-hop culture.

## Resume instructions and remaining work

The CDX responses, recovery manifest, and content-addressed payloads in `recovery/206proof/` are the local checkpoint. Continue the separately dated Vanilla pages with:

```bash
.venv311/bin/python scripts/recover_206proof_vanilla.py --limit 160 --delay 0.6
```

The runner resumes from `recovered-resources.json`, saves each response under `recovery/206proof/raw/`, and records failures as attempts. After more HTML batches, regenerate the asset-reference index from recovered pages and continue the selected image/CSS queue with `.venv311/bin/python scripts/index_206proof_assets.py`, `.venv311/bin/python scripts/index_206proof_media.py`, and `.venv311/bin/python scripts/recover_206proof_assets.py`. Keep `/forum/`, `/4um/`, 2012–2013 community pages, and 2007 HTML/CSS as separate editions during reconstruction. Retry the nine failed captures individually when the archive permits; do not replace them with guessed content. Revisit exact YouTube/SoundCloud source URLs and the remaining asset and MP3 history, recording an archive miss separately from a failed request.

The 206proof preview has been built locally but has not been approved for public deployment. Third-party redistribution rights remain unresolved for captured posts, images, and audio. The root-mounted test build was stored outside the workspace at `/tmp/bluescholars-root-candidate-preview-20261018`; the prior `_site` contents were restored afterward.
