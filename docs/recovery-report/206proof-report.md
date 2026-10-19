# 206proof.com archive recovery checkpoint

**Updated:** 2026-10-19 UTC. This is a source-acquisition checkpoint, not a completed or published reconstruction. The site generations remain separate: the 2007 Vanilla 1.1.3 site, the 2008–2012 Vanilla `/forum/`, the 2012–2013 community routes, and the 2013–2014 vBulletin `/4um/` forum.

## Archive index coverage

The Wayback CDX query `206proof.com/*` was fetched uncollapsed with a 20,000-row limit and no resume key. It returned 19,874 capture events across all indexed statuses; 17,910 events have status 200. This establishes completion of that exact CDX query as returned, not all possible aliases, subdomains, external media hosts, or material absent from the archive. Both parsed responses, their query metadata, and response SHA-256 values are in `recovery/206proof/all-events-all-status.json`, `all-events-all-status.cdx.json`, `all-events-200.json`, and `all-events-200.cdx.json`.

The all-status response spans 2007–2026. Later parked, injected, and placeholder content is retained as index evidence but is excluded from the historical site editions. HTTP 200 alone is not treated as proof of usable page or media content.

## Validated source material saved

`recovery/206proof/recovered-resources.json` currently records 2,967 attempts: 2,958 payloads passed format checks and nine responses were rejected or undecodable. The validated records include:

- 2,070 HTML documents from the 2007 Vanilla site, 2008–2012 `/forum/`, 2012–2013 community routes, and 2013–2014 `/4um/` forum.
- 790 images and 91 CSS files, including Vanilla theme/extension styles, smileys, uploaded account pictures, community profile images, and vBulletin dependencies.
- Seven MP3 files with recognizable MP3 frame/ID3 signatures: six `SongOfTheWeek` uploads indexed in December 2010 and `poopintags.mp3` indexed in 2013. They are local preservation evidence only; playable redistribution has not been reviewed or approved.
- 2,708 unique SHA-256 payload hashes, summing 88,141,692 bytes across capture records. The raw directory currently occupies about 86.2 MB because identical payloads share files.

Every attempt retains requested timestamp, original URL, CDX metadata, resolved replay URL/actual timestamp when available, MIME/type validation, byte length, hash, local path, and errors. Nine failures remain recorded: three empty responses, four non-HTML/placeholder responses, and two invalid content-encoding responses. They are not counted as recovered pages.

The 2008–2012 Vanilla selector currently identifies 5,137 distinct exact URL records with query strings and host aliases preserved. It has attempted 1,000 selected records so far: 995 validated, five failed, and 4,137 still queued. The route set is dominated by accounts and discussion pages. The 39-page `DiscussionID=988` thread and the 2013 vBulletin/community routes have separate records; this selector does not merge them into the Vanilla edition.

## Images, CSS, and linked media

Dependencies extracted from all 2,070 recovered HTML documents produce 25,099 page-to-asset references across 1,442 distinct same-domain CSS/image URLs. The saved all-status CDX rows contain a successful response for 625 of those URLs; 817 have no successful match in this query. 881 image/CSS capture records (624 distinct normalized asset URLs) have been downloaded and validated; one capture-bearing asset URL remains unattempted in this pass. The machine-readable source/reference map is `recovery/206proof/asset-index.json`.

The media-lead scan found 342 YouTube IDs and 21 SoundCloud paths in captured HTML. These are source-linked references, not recovered playable media. Seven MP3 files are the only audio payloads validated so far. The lead list is `recovery/206proof/media-leads.json`.

## Other archive and secondary-source checks

Arquivo.pt's saved host-history lookup returned 21 root records from 2019–2025; replaying the selected later response produced an archive portal rather than a historical forum page. Six bounded Common Crawl index requests were attempted; they returned timeouts or no matching captures, so no Common Crawl body is counted as recovered. The results are saved under `recovery/206proof/arquivo-pt-check.json` and `recovery/206proof/commoncrawl/`.

Independent contemporary sources help identify and contextualize lost pages but are not substitutes for 206proof captures: [206 Zulu's January 2008 bulletin](https://www.206zulu.org/nw-hip-hop-congress-january-bulletin/) names a 206 Proof contributor; the [October 2008 Basement Addicts post](https://basementaddicts.blogspot.com/2008/) quotes a forum exchange; [Seattle Weekly's 2009 article](https://www.seattleweekly.com/2009/03/25/a-while-back-i-wrote-a-profile-of-everett-based-mc-ripynt-pronounced/) refers to the forum; and a [secondary Seaclipse reference](https://en-academic.com/dic.nsf/enwiki/9841790/) points to `DiscussionID=988`. The 2011 [206 Zulu essay](https://www.206zulu.org/how-can-hip-hop-save-the-world-lessons-from-a-seattle-youth-service-scandal/) describes 206Proof's role in local hip-hop culture.

## Resume instructions and remaining work

The CDX responses, recovery manifest, and content-addressed payloads in `recovery/206proof/` are the local checkpoint. Continue the separately dated Vanilla pages with:

```bash
.venv311/bin/python scripts/recover_206proof_vanilla.py --limit 160 --delay 0.6
```

The runner resumes from `recovered-resources.json`, saves each response under `recovery/206proof/raw/`, and records failures as attempts. After more HTML batches, regenerate the asset-reference index from recovered pages and continue the selected image/CSS queue with `.venv311/bin/python scripts/index_206proof_assets.py`, `.venv311/bin/python scripts/index_206proof_media.py`, and `.venv311/bin/python scripts/recover_206proof_assets.py`. Keep `/forum/`, `/4um/`, 2012–2013 community pages, and 2007 HTML/CSS as separate editions during reconstruction. Retry the nine failed captures individually when the archive permits; do not replace them with guessed content. Revisit exact YouTube/SoundCloud source URLs and the remaining asset and MP3 history, recording an archive miss separately from a failed request.

No 206proof public edition has been built or visually reviewed, and no deployment was made from this checkpoint. Third-party redistribution rights remain unresolved for captured posts, images, and audio.
