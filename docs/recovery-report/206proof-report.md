# 206proof.com archive recovery checkpoint

**Updated:** 2026-10-20 UTC. This is a source-acquisition checkpoint, not a completed or published reconstruction. The site generations remain separate: the 2007 Vanilla 1.1.3 site, the 2008–2012 Vanilla `/forum/`, the 2012–2013 community routes, and the 2013–2014 vBulletin `/4um/` forum.

## Archive index coverage

The Wayback CDX query `206proof.com/*` was fetched uncollapsed with a 20,000-row limit and no resume key. It returned 19,874 capture events across all indexed statuses; 17,910 events have status 200. This establishes completion of that exact CDX query as returned, not all possible aliases, subdomains, external media hosts, or material absent from the archive. Both parsed responses, their query metadata, and response SHA-256 values are in `recovery/206proof/all-events-all-status.json`, `all-events-all-status.cdx.json`, `all-events-200.json`, and `all-events-200.cdx.json`.

The all-status response spans 2007–2026. Later parked, injected, and placeholder content is retained as index evidence but is excluded from the historical site editions. HTTP 200 alone is not treated as proof of usable page or media content.

## Validated source material saved

`recovery/206proof/recovered-resources.json` currently records 4,918 attempts: 4,875 payloads passed format checks and 43 responses were rejected or undecodable. The validated records include:

- 3,859 HTML documents from the 2007 Vanilla site, 2008–2012 `/forum/`, 2012–2013 community routes, and 2013–2014 `/4um/` forum.
- 890 images and 119 CSS files, including Vanilla theme/extension styles, smileys, uploaded account pictures, community profile images, and vBulletin dependencies.
- Seven MP3 files with recognizable MP3 frame/ID3 signatures: six `SongOfTheWeek` uploads indexed in December 2010 and `poopintags.mp3` indexed in 2013. They are local preservation evidence only; playable redistribution has not been reviewed or approved.
- 4,435 unique SHA-256 payload hashes occupying 126,352,301 bytes. Identical payloads share content-addressed files.

Every attempt retains requested timestamp, original URL, CDX metadata, resolved replay URL/actual timestamp when available, MIME/type validation, byte length, hash, local path, and errors. Forty-three failures remain recorded: prior empty responses, invalid content encoding, off-target responses, and failed image candidates; 29 newer failures are mostly external web addresses mis-indexed as paths beneath `/forum/`, plus the failed `/forum/` root alternate. The selected 2012 `DiscussionID=15250&page=1` response returned 1,181 bytes but failed full-HTML validation; its exact URL has only one status-200 CDX row. The three image dependencies `nl.jpg`, `triple.jpg`, and `new.png` have only 500-byte `text/html` responses in the indexed captures, not valid image payloads. Failures are not counted as recovered pages.

The content-addressed payload bytes under `recovery/206proof/raw/` are retained in this workspace and excluded from Git; the tracked manifest and indexes preserve provenance, but a fresh checkout does not contain those response bodies and must reacquire them before building this edition.

The 2008–2012 Vanilla selector identifies 5,137 distinct exact URL records with query strings and host aliases preserved. It has attempted 2,820 selected records so far; 2,317 remain queued. The latest 160 attempts recovered 131 full HTML pages; 29 malformed outbound-link paths were rejected as non-HTML. The newly recovered pages include discussion pagination, archived search-result pages, and forum listings. The route set is dominated by accounts and discussion pages. The 39-page `DiscussionID=988` thread and the 2013 vBulletin/community routes have separate records; this selector does not merge them into the Vanilla edition.

## Images, CSS, and linked media

Dependencies extracted from 3,859 recovered HTML documents produce 51,893 page-to-asset references across 1,515 distinct same-domain CSS/image URLs. The saved all-status CDX rows contain a successful response for 654 URLs; 861 have no successful match in this query. Thirty-two additional CSS/image payloads were recovered from the latest batch. The two recovered 2013 homepages added 33 references but no further distinct asset URLs. The machine-readable source/reference map is `recovery/206proof/asset-index.json`.

The current media-lead scan found 907 YouTube IDs and 58 SoundCloud paths in captured HTML (965 distinct leads). These are source-linked references, not recovered playable media. Seven MP3 files are the only audio payloads validated so far. The lead list is `recovery/206proof/media-leads.json`.

## Local reconstruction candidate

The latest local candidate builds four separate generations from validated pages: 240 pages for 2007 Vanilla, 2,739 pages for the 2008–2012 Vanilla forum, 642 community pages, and 77 vBulletin pages. The community homepage uses the latest valid root capture dated July 5, 2013 (`http://206proof.com:80/`); newer October and December replay responses were only 483- and 487-byte errors. Two earlier April and May 2013 root alternatives have also been recovered and retained as dated provenance, but are not selected over the July capture. Captured HTML and local images/styles are preserved; scripts and posting forms are disabled; missing links lead to dated source-gap pages. When an exact query-string variant is absent, links may point to the closest recovered capture at the same path; the absent query variant is recorded rather than represented as exact. The latest `/bluescholars/` build links 4,289 destinations without captured pages and records 668 unique local 206proof assets. The exact 2007 Vanilla theme stylesheets have no successful captures in the indexed history; the 2007 pages therefore use the nearest recovered same-site Vanilla CSS from 2010, with a visible notice and provenance entries. The 2012 forum uses its own contemporaneous CSS captures. The historical `hthttp://` external link found in a captured Vanilla thread is retained in the page as provenance but disabled because its scheme is malformed; it is recorded as a source issue rather than silently corrected.

The latest integrated `/bluescholars/` candidate passed its offline link and active-content check with zero errors. Root-mounted validation passed on the preceding source checkpoint. The full test suite passes 236 tests. Local browser smoke inspection opened the archive hub, Vanilla forum index, the recovered “Public apology to Seaclipse” discussion, and the July 2013 community homepage; local CSS and image requests returned successfully. Preview commit `a21d4fad` was deployed to Pages earlier, but that public snapshot predates the latest source and candidate work; none of this continuation has been deployed. Browser smoke inspection is not human visual review and does not clear redistribution rights. The reviewed release flags remain false.

## Other archive and secondary-source checks

Arquivo.pt's saved host-history lookup returned 21 root records from 2019–2025; replaying the selected later response produced an archive portal rather than a historical forum page. Six bounded Common Crawl index requests were attempted earlier and returned timeouts. A later retry of three saved 2017–2018 LiveJournal WARC records recovered all three; the new bytes are in the shared recovery state and `recovery/commoncrawl-CC-MAIN-LJ-retry-20261020-report.json`. The six 206proof forum collection requests still have only saved 502/503/504 query errors and no indexed rows; those errors are unresolved. The results are saved under `recovery/206proof/arquivo-pt-check.json` and `recovery/206proof/commoncrawl/`.

Independent contemporary sources help identify and contextualize lost pages but are not substitutes for 206proof captures: [206 Zulu's January 2008 bulletin](https://www.206zulu.org/nw-hip-hop-congress-january-bulletin/) names a 206 Proof contributor; the [October 2008 Basement Addicts post](https://basementaddicts.blogspot.com/2008/) quotes a forum exchange; [Seattle Weekly's 2009 article](https://www.seattleweekly.com/2009/03/25/a-while-back-i-wrote-a-profile-of-everett-based-mc-ripynt-pronounced/) refers to the forum; and a [secondary Seaclipse reference](https://en-academic.com/dic.nsf/enwiki/9841790/) points to `DiscussionID=988`. The 2011 [206 Zulu essay](https://www.206zulu.org/how-can-hip-hop-save-the-world-lessons-from-a-seattle-youth-service-scandal/) describes 206Proof's role in local hip-hop culture. A [2011 BoxingScene thread](https://www.boxingscene.com/forums/boxing-forums/non-stop-boxing/492124-video-lets-compare) quotes a user post and an image URL from the forum; this is a secondary lead, not an additional captured 206Proof page. Broader web search returned no newly identified full mirror.

## Resume instructions and remaining work

The CDX responses, recovery manifest, and content-addressed payloads in `recovery/206proof/` are the local checkpoint. Continue the separately dated Vanilla pages; 2,317 of the 5,137 selected routes remain unattempted:

```bash
.venv311/bin/python scripts/recover_206proof_vanilla.py --limit 160 --delay 0.6
```

The runner resumes from `recovered-resources.json`, saves each response under `recovery/206proof/raw/`, and records failures as attempts. After more HTML batches, regenerate the asset-reference index from recovered pages and continue the selected image/CSS queue with `.venv311/bin/python scripts/index_206proof_assets.py`, `.venv311/bin/python scripts/index_206proof_media.py`, and `.venv311/bin/python scripts/recover_206proof_assets.py`. Asset deduplication includes MIME role so a failed HTML attempt cannot suppress a later image capture. Keep `/forum/`, `/4um/`, 2012–2013 community pages, and 2007 HTML/CSS as separate editions during reconstruction. Retry only failed captures with a plausible alternate: three candidate image assets (`nl.jpg`, `triple.jpg`, `new.png`) have only short HTML error bodies, and the 2012 `DiscussionID=15250&page=1` response has no alternate CDX row. Do not replace these gaps with guessed content. Revisit exact YouTube/SoundCloud source URLs and the remaining asset and MP3 history, recording an archive miss separately from a failed request.

The 206proof preview has been rebuilt locally after the latest source batches but has not been approved for public deployment. Third-party redistribution rights remain unresolved for captured posts, images, and audio. The root-mounted test build was stored outside the workspace at `/tmp/bluescholars-root-candidate-preview-20261018`; the prior `_site` contents were restored afterward.
