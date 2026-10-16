# Blue Scholars: website recovery and source-location report

**Prepared:** October 15, 2026  
**Visual baseline:** [May 29, 2021 homepage](https://web.archive.org/web/20210529010817/http://bluescholars.com/)  
**Goal:** Recover as much original material as possible and recreate a static site suitable for GitHub Pages.  
**Scope of this report:** Source discovery, capture selection, missing-content recovery, and handoff instructions. This is not a claim that the website has been downloaded or deployed.

## Executive findings

**Yes: we need multiple archive dates, not just the 2021 homepage snapshot.** The selected homepage sends several internal links to readable 2020 captures. The initially supplied 2019 blog request resolves to a provider error, while another blog capture is readable. The older-pagination chain also reaches an error capture with an earlier 2016 capture advertised in its toolbar. [S01](https://web.archive.org/web/20210529010817/http://bluescholars.com/) [S02](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/) [S04](https://web.archive.org/web/20200703230849/http://bluescholars.com/shows) [S05](https://web.archive.org/web/20200802161924/http://bluescholars.com/video) [S07](https://web.archive.org/web/20200703230805/http://bluescholars.com/holler) [S09](https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000) [S10](https://web.archive.org/web/20190719224804/http://bluescholars.com/blog)

The expanded inventory contains **97 URL records: 14 site page/query targets, 42 image URLs, 11 video references, and 30 external source/navigation/media leads**. These are the sources actually identified so far, not an exhaustive count of everything Internet Archive holds. The accompanying CSV and JSON contain full original URLs, replay URLs, capture hints, source pages, status, and generated exact-index queries.

Of the 42 image URLs, **five displayed in the archive reader, three returned a reported 404, and 34 produced tool cache misses**. No original site files have been saved locally. The five displayed images are the homepage photograph and the four images linked by the Eugene gallery. The complete image-by-image record is in Appendix A. A cache miss in this tool must not be interpreted as a missing archive capture.

A successful restoration needs two separate decisions for every resource: **where the original material can be recovered** and **whether that version belongs in the 2021 presentation**. Recover widely; publish a deliberately chosen combination. Older content that was no longer part of the reference site can be preserved separately rather than quietly inserted into its homepage or current navigation.

## 1. How to read the evidence

| Status | What it establishes | What it does not establish |
| --- | --- | --- |
| Readable page | The replay exposes page text/structure. | That original HTML, CSS, or all dependencies were downloaded. |
| Displayed image | The reader displayed that image request. | A local binary backup, an exact original resolution, or archive-wide completeness. |
| Reported 404 | That tested replay request failed with a reported 404. | That no other capture or URL spelling works. |
| Captured provider error | The archive is replaying an error page rather than the intended website page. | That the URL never had good captures. |
| Tool cache miss / timeout | This tool could not retrieve the requested object. | An archive 404, deletion, or lack of captures. |
| Candidate | A search/retrieval instruction derived from a known source or documented format. | A tested, successful location. |

**Dates need separate fields.** A post publication date, parent HTML capture date, requested Wayback timestamp, actual resolved capture timestamp, and present-day retrieval time are different facts. Record all available values. Do not label a 2013 post as published in 2020 because that is when Wayback captured it.

The exact-index and raw-download URLs in the manifest are generated instructions. They have not all been successfully fetched. A direct raw-homepage request in this session failed because the execution environment could not resolve `web.archive.org`; bulk-index and earlier-date probes were also inaccessible through the reader. This leaves the full archive inventory open.

## 2. Core pages: exactly where to start

The links below point to known replay targets. Dates are the observed resolved captures where established, not an assertion that every page was captured on May 29, 2021.

| ID | Page / exact replay | Observed capture | Recovery state |
| --- | --- | --- | --- |
| P01 | [Homepage](https://web.archive.org/web/20210529010817/http://bluescholars.com/) | 2021-05-29 01:08:17 | Readable; original bytes still required |
| P02 | [Blog, first listing](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/) | 2020-11-09 00:08:19 | Readable; original bytes still required |
| P03 | [Shows](https://web.archive.org/web/20200703230849/http://bluescholars.com/shows) | 2020-07-03 23:08:49 | Readable; original bytes still required |
| P04 | [Video](https://web.archive.org/web/20200802161924/http://bluescholars.com/video) | 2020-08-02 16:19:24 | Readable; original bytes still required |
| P05 | [Shop](https://web.archive.org/web/20200718164929/http://bluescholars.com/shop) | 2020-07-18 16:49:29 | Provider error; replace from another capture |
| P06 | [Holler](https://web.archive.org/web/20200703230805/http://bluescholars.com/holler) | 2020-07-03 23:08:05 | Readable; original bytes still required |
| P07 | [Blog, second listing](https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000) | 2020-02-20 15:48:40 | Readable; original bytes still required |
| P08 | [Eugene article](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/2013/9/9/eugene-oregon-august-2013) | 2020-02-20 15:47:03 | Readable; original bytes still required |
| P09 | [Blog, third listing](https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000) | 2019-07-19 22:40:39 | Provider error; replace from another capture |

Source pages: [S01](https://web.archive.org/web/20210529010817/http://bluescholars.com/) [S02](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/) [S03](https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000) [S04](https://web.archive.org/web/20200703230849/http://bluescholars.com/shows) [S05](https://web.archive.org/web/20200802161924/http://bluescholars.com/video) [S06](https://web.archive.org/web/20200718164929/http://bluescholars.com/shop) [S07](https://web.archive.org/web/20200703230805/http://bluescholars.com/holler) [S08](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/2013/9/9/eugene-oregon-august-2013) [S09](https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000)

### Additional internal paths already identified

These are real source-linked URLs, but their page bodies were not retrieved in this pass. Keep them in the queue rather than inventing replacement slugs.

| ID | Observed internal URL | Why it matters |
| --- | --- | --- |
| [P10](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/bringing-back-the-og-t-shirt-in-green-and-gold-if) | `/blog/bringing-back-the-og-t-shirt-in-green-and-gold-if` | Next article from the Eugene permalink |
| [P11](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/el-primer-d-a-de-clase) | `/blog/el-primer-d-a-de-clase` | Campus article and its nine inline images |
| [P12](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/?author=51c916c2e4b05db4f944ab44) | `/blog/?author=51c916c2e4b05db4f944ab44` | Author archive: Geo |
| [P13](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/?author=51b3c159e4b0de8ae9a69517) | `/blog/?author=51b3c159e4b0de8ae9a69517` | Author archive: Alexei |
| [P14](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog?tag=Blue+Schoalrs) | `/blog?tag=Blue+Schoalrs` | Tag query; historical misspelling must survive |

## 3. What to recover from each section

### Homepage and common layout — first priority

Save the original HTML, head metadata, navigation, site-title/logo mechanism, footer, mobile-menu structure, inline styles, and every linked stylesheet. Record the ordering and roles of the five section links and the two external artist links. Obtain the homepage photograph as a separate asset, not as a screenshot of the archived page. [S01](https://web.archive.org/web/20210529010817/http://bluescholars.com/) [S11](https://web.archive.org/web/20210529010844/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371078164544-2RKW5D1QDQ5IXSVM5B2N/ke17ZwdGBToddI8pDm48kIZpWXENTEukrBXe6_rB7blZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIF2CO6JwS3nXJTgmvDX6VE5p5CmEHphUtvFe0ff6hcA8KMshLAGzx4R3EDFOm1kBS/front-page.jpg)

The homepage photograph's actual capture is **20210529010844**, 27 seconds after the HTML reference **20210529010817**. This is an important edge case: a blanket rule that discards every resource after the HTML timestamp would discard the reference image itself. Save its provenance and permit a specifically reviewed same-crawl dependency; do not turn that exception into unrestricted acceptance of later redesigns. [S11](https://web.archive.org/web/20210529010844/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371078164544-2RKW5D1QDQ5IXSVM5B2N/ke17ZwdGBToddI8pDm48kIZpWXENTEukrBXe6_rB7blZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIF2CO6JwS3nXJTgmvDX6VE5p5CmEHphUtvFe0ff6hcA8KMshLAGzx4R3EDFOm1kBS/front-page.jpg)

Do not guess the logo or typography from the text reader's blank heading. The logo could be an image, a styled title, or a CSS-dependent element; its exact mechanism remains unverified. The report contains no recovered original stylesheet or logo file.

### Blog — preserve posts and the paths connecting them

The two readable listings contain 20 entries each. They expose publication dates spanning September 9 through January 12, 2013. Treat that as **40 listing entries**, not 40 separately recovered article pages or the site's lifetime post count. Appendix C records the finding aids. [S02](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/) [S03](https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000)

For each raw article block, retain the original item ID, exact permalink, title or deliberately absent title, author, publication timestamp, body markup, source/reblog credits, tags, images, captions, embed IDs, and navigation neighbors. If only the listing survives, it may still preserve the complete body; confirm whether it is full text or an excerpt before reconstructing an article from it. Record that provenance instead of claiming an independently recovered permalink.

The known pagination chain is:

```text
/blog/
  -> /blog?offset=1362122742000
  -> /blog?offset=1358016466000
  -> additional offsets not yet established
```

Offsets are part of content identity. Do not strip queries during crawling. Preserve author/tag queries as well. Rebuild browsable static paths for these queries and retain a mapping from the historical URLs; exact query behavior needs deliberate handling rather than a directory named after a question mark.

### Shows — the poster is substantive content

The inspected Shows page references `EUGENE.jpg`; its tested image replay returned 404. Recover the original poster from another capture or source-linked URL variant. Do not infer a complete show schedule from the otherwise sparse reader output. Look for additional content in raw HTML, image captions, and older captures before concluding that the page had only that poster. [S04](https://web.archive.org/web/20200703230849/http://bluescholars.com/shows)

### Holler — preserve the historical page, not a present-day directory

Recover both image references, `scholars.jpg` and `sisters2.jpg`, plus the surrounding captions, roles, and social/contact link markup. Both tested image replays returned 404. The page's contact details are historical; this restoration should not imply that those roles, addresses, or handles are current. Extract public contact details from the source during recovery rather than expanding them into unrelated personal data. [S07](https://web.archive.org/web/20200703230805/http://bluescholars.com/holler)

### Shop — do not reproduce the provider error as the shop

The tested Shop capture contains a provider error. Search alternate captures of `/shop`, its slash/protocol variants, and any shop destination revealed by valid older navigation or redirects. Product pages, photography, descriptions, and original displayed prices are candidates only if actually found. No usable catalog or particular external store platform is confirmed yet. [S06](https://web.archive.org/web/20200718164929/http://bluescholars.com/shop)

Recommended static behavior: a read-only historical catalog with no working cart, stock claims, or checkout. If no catalog survives, retain an explicit missing-content notice rather than manufacturing products from unrelated material. The shirt posts can support a separate merchandise-history record, but they are not proof of the original Shop page's full contents.

### Video — preserve the list before solving playback

The page exposes 11 YouTube embeds in a definite order. Their IDs and archived player-title observations are in Appendix B. Player replays displayed errors; those are not recovered video files. Keep historical order and verified metadata. Mark missing titles as unresolved rather than inferring a song from the URL or appearance. [S05](https://web.archive.org/web/20200802161924/http://bluescholars.com/video)

## 4. Which older archives we need, and why

| Recovery target | First choice | Next search | Selection rule |
| --- | --- | --- | --- |
| Homepage design | Selected May 2021 HTML and its dependencies | Adjacent working captures, then compatible 2020 pages | Compare the actual layout; do not substitute a different era's design. |
| Main sections | Exact readable 2020 captures listed above | Other captures around those dates | Recover raw markup and associated dependencies together. |
| Third blog listing | The toolbar's June 11, 2016 lead | All captures of the exact offset URL; then indexed article URLs | The 2019 error capture is unsuitable as content. |
| Shop | All captures of the exact shop path | Earlier 2013–2019 captures, then older indexed variants | These date ranges are search priorities, not confirmed good captures. |
| Missing Squarespace images | All captures of the exact observed asset URL | Old parent-page captures and this site's other CDN URL families | Match the actual image, crop, and source evidence. |
| Nine Tumblr inline photos | Exact image URL and its source post | Captures near the 2013 publication period and later preserved copies | Preserve image identity and credits; a current unrelated image is not a substitute. |
| Earlier site history | Full domain index across all years | Older blog structures and source-discovered legacy paths | Preserve separately when not part of the reference-era presentation. |
| Later than May 2021 | Only a matching missing asset or explicitly approved content | Compare with older references and, where available, identical byte hashes | Never assume the newest snapshot is historically appropriate. |

The June 11, 2016 date is a **toolbar-reported lead**, not a verified good page. Its exact timestamp and body remain unknown. This date-based request is useful to try, but Wayback may redirect it: [try the June 2016 older-listing request](https://web.archive.org/web/20160611/http://bluescholars.com/blog?offset=1358016466000). Record the result, not the requested date. [S09](https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000)

A failed paginator does not end recovery. The domain index can expose individual posts or other offset URLs that are not reachable from the currently selected listing. Conversely, an index row is not itself proof that its replay contains the intended content. Validate the response.

**Do not indiscriminately combine eras.** The target is the 2021 site's appearance with documented gap-filling. Material recovered from an older site version but not shown to belong there should be placed in a separate legacy archive or held for review.

## 5. Images: three concrete host/path families

The 42 observed image URLs break down as follows. The exact URLs and tested replay states are in Appendix A and the manifest.

| Observed host/path family | URL count | Special handling |
| --- | --- | --- |
| `images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/…` | 18 | Preserve long identity paths and query variants; many basenames repeat. |
| `static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/…` | 15 | These observed URLs end with `/`, not `.jpg`; validate MIME and bytes. |
| `media.tumblr.com/…` | 9 | These are outside the main site's domain and need their own index lookups. |

The observed Squarespace site ID is:

```text
51b8c20be4b0f1f8c9dcdf4c
```

The older image paths also expose the shared collection identifier:

```text
51b8c857e4b05bf73912a42e
```

Use those identifiers to constrain searches. Do not crawl all of Squarespace or Tumblr. Start with each exact source-linked URL; then search the relevant site-specific prefix or original source post.

### Missing-image recovery ladder

**First: exact URL, all dates.** The manifest supplies an exact CDX query and a capture-calendar link for every image. Try distinct valid captures, preserving the final redirected URL and capture timestamp. Do not overwrite a failed download with an HTML error body named `.jpg`.

**Second: indexed variants of the same asset.** Search the upload/item prefix and inspect other sizes, query strings, or historical URL spellings actually found there. The same basename `image-asset.jpeg` appears on different image identities; filename-only deduplication would destroy content. Keep URL identity and file-hash identity separate.

**Third: older parent HTML.** An earlier copy of the same page may reveal an older CDN path for the image. Inspect its `src`, lazy-load attributes, responsive sources, links, and embedded metadata. A nearest-date request against a newer URL cannot automatically reveal an older URL it does not know about.

**Fourth: original source/reblog.** Appendix D records source-linked Tumblr and other posts. Recover those narrowly as evidence for the missing material, including credits. An external source must match the specific image or body; a similar photograph from the same photographer is not enough.

**Fifth: retain the gap.** If every investigated route fails, record the attempts and render a clear missing-image state that preserves any surviving caption and layout dimensions. Do not fabricate a replacement and call it restored.

HTTP/HTTPS aliases, old CDN host spellings, shorter Tumblr post URLs, `format=…` image sizes, and older Squarespace `/content/…` forms are **candidate searches**, not verified equivalent URLs. Only promote them after checking what they return.

## 6. Styling and layout: the biggest unresolved dependency

**Recover original CSS before designing substitute styling.** A content-only mirror can have every paragraph and still look nothing like the reference. None of the exact original stylesheet URLs, logo mechanism, favicon assets, font declarations, or desktop/mobile geometry has yet been verified.

In the raw homepage and one good article page, collect these evidence classes:

| Evidence to extract | Where to look | Why it matters |
| --- | --- | --- |
| Stylesheet order | `<link rel="stylesheet">`, inline `<style>`, CSS `@import` | Cascading order and template/site overrides affect the result. |
| Image dependencies | `url(...)`, backgrounds, masks, icons, sprites | Some visual assets are not in ordinary image tags. |
| Logo/title | Header markup, linked images, CSS, structured site metadata | Avoid inventing a wordmark or treating an empty parsed heading as the design. |
| Typography | `font-family`, weight/style, letter spacing, provider declarations | Record names and requirements; do not bundle unlicensed font files. |
| Layout rules | Widths, spacing, breakpoints, alignments, image fitting/focal points | Needed for an accurate static reconstruction. |
| Lazy-load/gallery behavior | `src`, `data-src`, `srcset`, `data-image`, block metadata | Recover the visible image rather than a loader placeholder. |
| Hidden navigation/data | Menu markup and source-discovered page metadata | Can expose links that a text replay omits. |
| Share/search metadata | Canonical URL, descriptions, icons, Open Graph images | Useful supplemental assets and content identity checks. |

Candidate inspection strings include `Static.SQUARESPACE_CONTEXT` and site/template identifiers in raw scripts. Their presence in this specific page is not established. Read such data as evidence; do not execute arbitrary archived JavaScript in the restored site.

Squarespace documents JSON context views such as `?format=json-pretty`. That makes JSON versions worth searching **in the archive**, but no such response for this site is confirmed here. Search the exact query URLs rather than asking today's site for a replacement. [S15](https://developers.squarespace.com/beginner-tutorial)

Useful unverified candidates include:

```text
/?format=json-pretty
/blog?format=json
/blog?format=json-pretty
/blog?offset=1362122742000&format=json
/blog?offset=1358016466000&format=json
/blog?format=rss
/sitemap.xml
/robots.txt
```

These are discovery probes, not a claim that every endpoint exists or was archived. Inspect a recovered sitemap's child links and preserve its capture date. If raw source reveals additional feed/API paths, use those exact paths.

## 7. Full-archive indexing: the acquisition runbook

### Inventory broadly; fetch selectively

Obtain the domain's capture index with original URLs and timestamps, then perform separate targeted queries for the source-linked CDN and media hosts. The CDX API supports exact, prefix, host/domain matching, JSON output, field selection, and resumable results. Do not collapse away all but one capture while collecting the master inventory. [S12](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server)

Example first batch, runnable from an environment with working archive access:

```bash
mkdir -p recovery/index
curl --fail --show-error --location --get \
  'https://web.archive.org/cdx/search/cdx' \
  --data-urlencode 'url=bluescholars.com' \
  --data-urlencode 'matchType=domain' \
  --data-urlencode 'output=json' \
  --data-urlencode 'fl=timestamp,original,statuscode,mimetype,digest,length' \
  --data-urlencode 'limit=500' \
  --data-urlencode 'showResumeKey=true' \
  -o recovery/index/domain-first-batch.json
```

This is a first batch, not a complete crawl. Follow returned continuation keys and keep each raw response. A resume key appears outside the ordinary capture rows; do not count it as an asset. The supplied recovery project already has resumable indexing logic. [S12](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server) [S19](PROJECT-INSPECTION.md)

Do not initially discard redirects, revisit records, or non-200 entries from the research inventory. They may explain moved resources. Separately choose usable payloads for the build. A success status alone does not validate a page: inspect for provider errors, parking pages, challenges, or an unrelated replacement site.

For external assets, use these **observed prefixes** rather than an unconstrained global crawl:

```text
https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/
https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/
```

For Tumblr, start with the nine exact image URLs and specific source post IDs in the manifest. Search any additional media hosts only when raw source or indexed redirects reveal them. For the main domain, preserve evidence of `www`, protocol, port, slash, and query variants before choosing a local canonical mapping.

### Retrieve raw originals and retain provenance

A raw replay request has the form:

```text
https://web.archive.org/web/<capture>id_/<original-url>
```

Normal replay URLs are for inspection; image/iframe modifiers indicate resource context. `id_` requests unrewritten content in the documented replay convention. Validate what was returned rather than assuming that adding the modifier guarantees a successful original file. [S14](https://pywb.readthedocs.io/en/develop/manual/rewriter.html)

For a single nearest-capture lead, the availability API can be useful, but it returns a closest snapshot rather than an archive-wide inventory. Inspect its actual timestamp and verify its body. [S13](https://archive.org/help/wayback_api.php)

For every downloaded object record the requested original URL, referring page, requested timestamp, resolved replay URL, resolved original URL, actual capture timestamp, content type, byte count, SHA256, and local file. Add image dimensions after decoding and record the reason any alternate-date asset is accepted. Keep untouched source bytes outside the generated static directory.

Use a resumable queue with conservative request pacing and backoff. Save failures rather than retrying a bad URL indefinitely. Network failures must not erase a checkpoint or silently trigger publication.

## 8. The five highest-value gap investigations

**A. Third blog listing.** Query all captures of `/blog?offset=1358016466000`; inspect the June 2016 lead. In parallel, enumerate all indexed `/blog` URLs and potential article records. Search archived listing JSON/RSS only as a separate fallback. Goal: discover the next offset and older post identities without depending on a broken navigation link.

**B. Three top-level images.** Prioritize A03–A05: the Shows poster and both Holler photographs. Search their exact full URLs, then older versions of the parent pages. Their basenames are useful finding aids, but identity needs the original path and visual/source match.

**C. Original CSS and logo.** Fetch raw home/article HTML, preserve stylesheet order, and recursively collect CSS image dependencies. Match site-specific styles to the selected presentation. A shared library stylesheet alone does not establish the original site's complete appearance.

**D. Older blog photographs.** The 15 extensionless Squarespace URLs and nine Tumblr inline images need explicit attention. Preserve extensionless paths, search their exact indexes, and inspect original source posts for missing variants. This is why a main-domain-only image crawler will be incomplete.

**E. Shop.** Identify a capture with real content before implementing a catalog. Follow source-proven redirects and navigation destinations; do not assume a particular store provider. Keep any historic-commerce restoration read-only.

## 9. Static output and historical behavior

GitHub Pages publishes static HTML, CSS, and JavaScript, making it suitable for the intended result. A project site conventionally lives under `/<repositoryname>/`; that prefix must be handled by generated links. This report does not claim that the target repository or Pages deployment is live. [S16](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

Recommended output mapping:

```text
/                           -> index.html
/blog/                      -> blog/index.html
/blog?offset=1362122742000   -> blog/page/2/index.html
/blog?offset=1358016466000   -> blog/page/3/index.html
/blog/<original-slug>/      -> blog/<original-slug>/index.html
/shows/                     -> shows/index.html
/video/                     -> video/index.html
/shop/                      -> shop/index.html
/holler/                    -> holler/index.html
```

Do not generate a third blog page as recovered content until its body or constituent posts are recovered. An explicit unavailable-content page is different from a fabricated reconstruction.

Preserve original internal slugs and significant tag spellings, and supply query-to-static navigation where appropriate. Keep ordinary page browsing independent of Wayback and Squarespace. Optional media playback can be an explicit external action; a local page and poster do not make a third-party stream self-contained.

Remove archive toolbar assets, trackers, obsolete commerce/form submission endpoints, and scripts not required for the static behavior. Keep source evidence separately. Replace only the necessary navigation or gallery behavior with small local code after comparing it to the archived reference.

Preserve visible credits. Before public release, review permission to republish text, photography, artwork, and other media; an archive capture should not be treated as a blanket reuse permission. This report includes URLs and metadata, not bundled original photos or font binaries.

## 10. How this expands the supplied project

The earlier project is a recovery/build toolset with a small seed inventory, not a recovered site. Its supplied README documents the separation between candidate acquisition and reviewed publication. This report adds many concrete leads; it does not modify that project or run a new deployment. [S17](project-reference/README.md) [S18](project-reference/VERIFICATION.md)

Included here is **`recovery-seeds-expanded.json`**, matching the supplied project's seed schema. It contains **14 page/query targets and 42 image URLs**. The 11 video references remain metadata. The 30 external source leads are in the report/manifest for narrow manual investigation; they are not automatically added as local pages.

For a fresh copy of the supplied project, merge the expanded seed file into `recovery/seeds/inventory.json` after preserving the existing file. Do not replace a newer working inventory with this report's older checkpoint. Then the documented commands are:

```bash
python -m restore seed
python -m restore index --max-pages 50
python -m restore recover --max-files 500 --retry-failed
python -m restore status
```

To inventory an observed external prefix with that CLI:

```bash
python -m restore index \
  --url 'https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/' \
  --match prefix --max-pages 50
```

The `50`/`500` limits above are batch limits, not declarations of completeness. Continue from the saved cursor and inspect statuses. After recovery, build a candidate, check it, and compare visually before promotion. [S17](project-reference/README.md) [S19](PROJECT-INSPECTION.md)

Important limitations found by inspecting the supplied code:

- Automatic HTML link discovery follows the apex/`www` site, not arbitrary external reblog pages. The domain index and exact/prefix queries are separate mechanisms.
- The seed loader reads page and image entries; it does not recover the `video_embeds` metadata as playable media.
- Fonts, original JavaScript, media binaries, and certain other downloads are excluded. That is intentional, but must be accounted for in completeness reporting.
- The discovery code handles several image attributes, stylesheet imports, block JSON, and JSON-LD. It is not a general extractor for every inline JavaScript configuration or archived JSON/RSS response.
- The renderer uses external media links and removes original scripts. This is not verified pixel-equivalent behavior.
- Resources resolving later than the exact target timestamp need review, including the legitimate homepage photo captured 27 seconds later.

These findings are about the packaged files inspected for this report, not the current state of any remote repository. [S19](PROJECT-INSPECTION.md)

## 11. Completion criteria and remaining unknowns

Call the **inventory** complete only when the chosen domain/prefix index queries have finished, every discovered page has been considered, and all referenced dependencies have a status. A terminated query or tool cache miss is not proof of exhaustion.

Call a **resource** recovered only when validated bytes exist locally and their provenance is recorded. A readable web-tool replay or a known video ID is not enough.

Call the **reference presentation** restored only after desktop/mobile comparison of logo/title, typography, spacing, navigation, image order/crops, article structure, and key historical interactions. Suggested comparison widths such as 1440, 768, and 390 pixels are test choices, not claimed original breakpoints.

Before publishing, verify that no automatic resource request depends on Wayback, Squarespace, or a missing local path; local navigation and historical query mappings work; gaps are honestly marked; and historic contacts, shows, and shop behavior are not presented as current services. A link/resource checker establishes technical consistency, not historical completeness.

Still unresolved: the full capture index; original CSS/logo/font declarations; image bytes; good Shop content; the third and subsequent blog listings; most individual post bodies/permalinks; additional pages not exposed by these inspected links; source-linked variants; and actual external-media playback. **There is no defensible recovery percentage yet.** The manifest is a concrete starting set, not a denominator for the whole historical website.

---

## Appendix A. Every observed image URL

Click an ID to try the observed image replay. “All dates” searches that original URL's capture history. Full original, raw-candidate, and exact CDX URLs are in `recovery-manifest.csv` and `recovery-manifest.json`.

**Displayed** means shown in the reader, not downloaded. **404** means the tested request reported 404. **Cache miss** means retrieval was inconclusive. All records have `local_file: null`.

### Named top-level and Eugene assets


| ID / replay | Finding aid | Filename / final locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [A01](https://web.archive.org/web/20210529010817im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371078164544-2RKW5D1QDQ5IXSVM5B2N/ke17ZwdGBToddI8pDm48kIZpWXENTEukrBXe6_rB7blZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIF2CO6JwS3nXJTgmvDX6VE5p5CmEHphUtvFe0ff6hcA8KMshLAGzx4R3EDFOm1kBS/front-page.jpg) | Homepage photograph | `front-page.jpg` | Displayed | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371078164544-2RKW5D1QDQ5IXSVM5B2N/ke17ZwdGBToddI8pDm48kIZpWXENTEukrBXe6_rB7blZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIF2CO6JwS3nXJTgmvDX6VE5p5CmEHphUtvFe0ff6hcA8KMshLAGzx4R3EDFOm1kBS/front-page.jpg) |
| [A02](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792276206-LCA0STYQMZGAB7MQD8EY/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIBqmMCQ1OP129tpEIJko8bi_9nfbnt8dRsNvtvnXdL8M/bluescholars-1.jpeg) | Eugene gallery / image 1 | `bluescholars-1.jpeg` | Displayed | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792276206-LCA0STYQMZGAB7MQD8EY/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIBqmMCQ1OP129tpEIJko8bi_9nfbnt8dRsNvtvnXdL8M/bluescholars-1.jpeg) |
| [A03](https://web.archive.org/web/20200703230849im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371068135452-YPT6UJGS33RF1E9C3HPX/ke17ZwdGBToddI8pDm48kANPycS1xMmB2DHMj7XKyEhZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZUJFbgE-7XRK3dMEBRBhUpzOeqS1g1ZYcZbvsTb-QQc_fimOWPjSeSh4xRIcQ1fETOzVZDfe4pqhvyCp_gm1wMU/EUGENE.jpg) | Shows poster | `EUGENE.jpg` | 404 | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371068135452-YPT6UJGS33RF1E9C3HPX/ke17ZwdGBToddI8pDm48kANPycS1xMmB2DHMj7XKyEhZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZUJFbgE-7XRK3dMEBRBhUpzOeqS1g1ZYcZbvsTb-QQc_fimOWPjSeSh4xRIcQ1fETOzVZDfe4pqhvyCp_gm1wMU/EUGENE.jpg) |
| [A04](https://web.archive.org/web/20200703230805im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371065206908-QJ2UFNNVS4QP4QJDMJSK/ke17ZwdGBToddI8pDm48kI6KiKQWAPCO4TdDSWDjF7tZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIyouxKf5guHCBBWIVtpbnsxyoyJg7S9G1Sy-6gAxXHq0KMshLAGzx4R3EDFOm1kBS/scholars.jpg) | Holler / band photograph | `scholars.jpg` | 404 | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371065206908-QJ2UFNNVS4QP4QJDMJSK/ke17ZwdGBToddI8pDm48kI6KiKQWAPCO4TdDSWDjF7tZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIyouxKf5guHCBBWIVtpbnsxyoyJg7S9G1Sy-6gAxXHq0KMshLAGzx4R3EDFOm1kBS/scholars.jpg) |
| [A05](https://web.archive.org/web/20200703230805im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371080207993-GGZ7N5WRW3KFT8QIMZ0Y/ke17ZwdGBToddI8pDm48kBOznfT3IrUCBESS1QO4nqhZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIuQHnEEFVCfrIt2ctRmbCkrtPoqg0sd8u0r9TsdY-wh4KMshLAGzx4R3EDFOm1kBS/sisters2.jpg) | Holler / team photograph | `sisters2.jpg` | 404 | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371080207993-GGZ7N5WRW3KFT8QIMZ0Y/ke17ZwdGBToddI8pDm48kBOznfT3IrUCBESS1QO4nqhZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIuQHnEEFVCfrIt2ctRmbCkrtPoqg0sd8u0r9TsdY-wh4KMshLAGzx4R3EDFOm1kBS/sisters2.jpg) |
| [A06](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792300499-WX44SOM6RD1J9EWMQSB6/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-2.jpeg) | Eugene gallery / bluescholars-2.jpeg | `bluescholars-2.jpeg` | Displayed | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792300499-WX44SOM6RD1J9EWMQSB6/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-2.jpeg) |
| [A07](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792314409-UYIDT6A1CYWCEYT20UT7/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-4.jpeg) | Eugene gallery / bluescholars-4.jpeg | `bluescholars-4.jpeg` | Displayed | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792314409-UYIDT6A1CYWCEYT20UT7/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-4.jpeg) |
| [A08](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792336701-VW176O3BLU30BR3HBJEL/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-5.jpeg) | Eugene gallery / bluescholars-5.jpeg | `bluescholars-5.jpeg` | Displayed | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1378792336701-VW176O3BLU30BR3HBJEL/ke17ZwdGBToddI8pDm48kBtpJ0h6oTA_T7DonTC8zFdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIWkiAYz5ghgEgSGJuDQ4e1ZKXpRdhEMT7SgthRpD0vyIKMshLAGzx4R3EDFOm1kBS/bluescholars-5.jpeg) |

### Other first-listing Squarespace assets


| ID / replay | Finding aid | Filename / final locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [A09](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064432757-KN92FTUAVOIA6I9GOME4/ke17ZwdGBToddI8pDm48kPHgPSpJs3pqpkUZU93_mvpZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PInndiFr6ALsCf3uCDBRk4eJzsF3rQ925VZ6DZqxvBZkQKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) | Green/gold shirt | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064432757-KN92FTUAVOIA6I9GOME4/ke17ZwdGBToddI8pDm48kPHgPSpJs3pqpkUZU93_mvpZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PInndiFr6ALsCf3uCDBRk4eJzsF3rQ925VZ6DZqxvBZkQKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) |
| [A10](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064432808-UERYRMFDJWKDV88LO8Y7/ke17ZwdGBToddI8pDm48kNyF6wJRgHLmJg9fTBX7WfBZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVECKrtgJ-oZkY66qO5m9a2ekNaApMtwVSs5uIGYtprRSBur-lC0WofN0YB1wFg-ZW0/image-asset.png) | Bellingham poster | `image-asset.png` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064432808-UERYRMFDJWKDV88LO8Y7/ke17ZwdGBToddI8pDm48kNyF6wJRgHLmJg9fTBX7WfBZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVECKrtgJ-oZkY66qO5m9a2ekNaApMtwVSs5uIGYtprRSBur-lC0WofN0YB1wFg-ZW0/image-asset.png) |
| [A11](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433035-8OXUKEXL5A4TQCTQU0R6/ke17ZwdGBToddI8pDm48kPqQfq0L3n3wpHIsRapTfg8UqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYxCRW4BPu10St3TBAUQYVKczo5Zn4xktlpMsMj-QlHXeMfNK6GwvtVkYEWiR8XAPyD3GfLCe_DXOSC_YcAacWL_/image-asset.jpeg) | Trio photograph | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433035-8OXUKEXL5A4TQCTQU0R6/ke17ZwdGBToddI8pDm48kPqQfq0L3n3wpHIsRapTfg8UqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYxCRW4BPu10St3TBAUQYVKczo5Zn4xktlpMsMj-QlHXeMfNK6GwvtVkYEWiR8XAPyD3GfLCe_DXOSC_YcAacWL_/image-asset.jpeg) |
| [A12](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433176-TOF0CZCDUTACMTTWFF5J/ke17ZwdGBToddI8pDm48kJVwuJMj7CH6fYOCWHXZJOdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIqH84A2Hox5s9hwnuGKN-h28-azLtB5B9GL4qiiz7kIcKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) | Boston photograph | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433176-TOF0CZCDUTACMTTWFF5J/ke17ZwdGBToddI8pDm48kJVwuJMj7CH6fYOCWHXZJOdZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIqH84A2Hox5s9hwnuGKN-h28-azLtB5B9GL4qiiz7kIcKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) |
| [A13](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433229-4GGG9HCJON3Q26P77RE7/ke17ZwdGBToddI8pDm48kNCH0IFo-E28D0rm_d_wnF4UqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYxCRW4BPu10St3TBAUQYVKczdH3qUBwO6oWXP_OkYMa5KbLFw5Om5Yp_Nt25Y6nc5ZZuUUY1FOqARMqv9i1pcqr/image-asset.jpeg) | Town Hall photograph | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433229-4GGG9HCJON3Q26P77RE7/ke17ZwdGBToddI8pDm48kNCH0IFo-E28D0rm_d_wnF4UqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYxCRW4BPu10St3TBAUQYVKczdH3qUBwO6oWXP_OkYMa5KbLFw5Om5Yp_Nt25Y6nc5ZZuUUY1FOqARMqv9i1pcqr/image-asset.jpeg) |
| [A14](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433271-GFTNXZ4NDR2SQA3NDZ3D/ke17ZwdGBToddI8pDm48kIMgItuLfrBfs8_Vz6fY_v9Zw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIOoLtpHiREIxpGqLX9yLlbPF78fv36IoADR8RM4bC6WYKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) | Los Angeles photograph / March | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433271-GFTNXZ4NDR2SQA3NDZ3D/ke17ZwdGBToddI8pDm48kIMgItuLfrBfs8_Vz6fY_v9Zw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIOoLtpHiREIxpGqLX9yLlbPF78fv36IoADR8RM4bC6WYKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) |
| [A15](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433298-UV185WK49E51HK2I2AXS/ke17ZwdGBToddI8pDm48kEP7RHrgx1EZ_8CHo_UWuGlZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PI-BtFo7T6gKWoc73CubQHwfeZyZCyowxCFx_85HpEbPUKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) | Purple/gold shirt | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433298-UV185WK49E51HK2I2AXS/ke17ZwdGBToddI8pDm48kEP7RHrgx1EZ_8CHo_UWuGlZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PI-BtFo7T6gKWoc73CubQHwfeZyZCyowxCFx_85HpEbPUKMshLAGzx4R3EDFOm1kBS/image-asset.jpeg) |
| [A16](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433353-HUQHF53PD2XVDYB2IQEB/ke17ZwdGBToddI8pDm48kLdJ3j-ibWYU20S6E0aDMAl7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmbFTSCh3GLTYkz25V6Y8urJIuD2y7fSNCnhoa9WQ4jB08vps1ci3DLG5R66hSaaIi/image-asset.jpeg) | Photo pair / first | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433353-HUQHF53PD2XVDYB2IQEB/ke17ZwdGBToddI8pDm48kLdJ3j-ibWYU20S6E0aDMAl7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmbFTSCh3GLTYkz25V6Y8urJIuD2y7fSNCnhoa9WQ4jB08vps1ci3DLG5R66hSaaIi/image-asset.jpeg) |
| [A17](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433366-HXN9QVN3HBWEHCRZAIUW/ke17ZwdGBToddI8pDm48kLdJ3j-ibWYU20S6E0aDMAl7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmbFTSCh3GLTYkz25V6Y8urJIuD2y7fSNCnhoa9WQ4jB08vps1ci3DLG5R66hSaaIi/image-asset.jpeg) | Photo pair / second | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433366-HXN9QVN3HBWEHCRZAIUW/ke17ZwdGBToddI8pDm48kLdJ3j-ibWYU20S6E0aDMAl7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmbFTSCh3GLTYkz25V6Y8urJIuD2y7fSNCnhoa9WQ4jB08vps1ci3DLG5R66hSaaIi/image-asset.jpeg) |
| [A18](https://web.archive.org/web/20201109000819im_/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433460-0U0R12B966WO3378H2F3/ke17ZwdGBToddI8pDm48kP0x04V1XEe0XPzqOX1MKaR7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmjw4y9jm25X_CplAKqpK2fkSw6YcmP1xW_gG8HCptQz72szHi8Rk0JAosDC56jamZ/image-asset.jpeg) | Street portrait | `image-asset.jpeg` | Cache miss | [All dates](https://web.archive.org/web/*/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371064433460-0U0R12B966WO3378H2F3/ke17ZwdGBToddI8pDm48kP0x04V1XEe0XPzqOX1MKaR7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmjw4y9jm25X_CplAKqpK2fkSw6YcmP1xW_gG8HCptQz72szHi8Rk0JAosDC56jamZ/image-asset.jpeg) |

### Campus article: nine Tumblr inline images


| ID / replay | Finding aid | Filename / final locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [A19](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/6a3e0729d8abd8b7b849861cc11db33c/tumblr_inline_mkn0vq5Tel1qz4rgp.jpg) | Campus article / inline image 1 | `tumblr_inline_mkn0vq5Tel1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/6a3e0729d8abd8b7b849861cc11db33c/tumblr_inline_mkn0vq5Tel1qz4rgp.jpg) |
| [A20](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/86812e71c1fe259a78cef3d7cd7917e5/tumblr_inline_mkn0u4tvM51qz4rgp.jpg) | Campus article / inline image 2 | `tumblr_inline_mkn0u4tvM51qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/86812e71c1fe259a78cef3d7cd7917e5/tumblr_inline_mkn0u4tvM51qz4rgp.jpg) |
| [A21](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/b507a3aa9ad9507602448b8627e43dd5/tumblr_inline_mkn0ubFVxL1qz4rgp.jpg) | Campus article / inline image 3 | `tumblr_inline_mkn0ubFVxL1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/b507a3aa9ad9507602448b8627e43dd5/tumblr_inline_mkn0ubFVxL1qz4rgp.jpg) |
| [A22](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/83322c66269ff7dec226340cff4c54c2/tumblr_inline_mkn0ufdGMl1qz4rgp.jpg) | Campus article / inline image 4 | `tumblr_inline_mkn0ufdGMl1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/83322c66269ff7dec226340cff4c54c2/tumblr_inline_mkn0ufdGMl1qz4rgp.jpg) |
| [A23](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/21a65ad1b9d672eddc17be48b09af183/tumblr_inline_mkn0ul9RPt1qz4rgp.jpg) | Campus article / inline image 5 | `tumblr_inline_mkn0ul9RPt1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/21a65ad1b9d672eddc17be48b09af183/tumblr_inline_mkn0ul9RPt1qz4rgp.jpg) |
| [A24](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/eb7153e91a9e03b8be5498d92dc59e21/tumblr_inline_mkn0uq8CvA1qz4rgp.jpg) | Campus article / inline image 6 | `tumblr_inline_mkn0uq8CvA1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/eb7153e91a9e03b8be5498d92dc59e21/tumblr_inline_mkn0uq8CvA1qz4rgp.jpg) |
| [A25](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/ab886deb86ad19885b3e6a726c8fae15/tumblr_inline_mkn0uwSMJY1qz4rgp.jpg) | Campus article / inline image 7 | `tumblr_inline_mkn0uwSMJY1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/ab886deb86ad19885b3e6a726c8fae15/tumblr_inline_mkn0uwSMJY1qz4rgp.jpg) |
| [A26](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/7b0791e6a86196a3dfe70b73ecbd7e41/tumblr_inline_mkn0v27fNl1qz4rgp.jpg) | Campus article / inline image 8 | `tumblr_inline_mkn0v27fNl1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/7b0791e6a86196a3dfe70b73ecbd7e41/tumblr_inline_mkn0v27fNl1qz4rgp.jpg) |
| [A27](https://web.archive.org/web/20201109000819im_/http://media.tumblr.com/1d353970ceef745a73f3649e932c22bb/tumblr_inline_mkn0v8iSTj1qz4rgp.jpg) | Campus article / inline image 9 | `tumblr_inline_mkn0v8iSTj1qz4rgp.jpg` | Cache miss | [All dates](https://web.archive.org/web/*/http://media.tumblr.com/1d353970ceef745a73f3649e932c22bb/tumblr_inline_mkn0v8iSTj1qz4rgp.jpg) |

### Second listing: extensionless Squarespace images


| ID / replay | Finding aid | Filename / final locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [A28](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4ab/1371064436683/) | Residency photograph | `51b8c857e4b05bf73912a4ab/1371064436683/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4ab/1371064436683/) |
| [A29](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4b1/1371064435889/) | Bowery photograph | `51b8c857e4b05bf73912a4b1/1371064435889/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4b1/1371064435889/) |
| [A30](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4bd/1371064439862/) | Website announcement image | `51b8c857e4b05bf73912a4bd/1371064439862/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4bd/1371064439862/) |
| [A31](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4c3/1371064436018/) | Los Angeles photograph / December | `51b8c857e4b05bf73912a4c3/1371064436018/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4c3/1371064436018/) |
| [A32](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4d3/1371064435828/) | Tour / Boston | `51b8c857e4b05bf73912a4d3/1371064435828/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4d3/1371064435828/) |
| [A33](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4d9/1371064436860/) | Tour / New York | `51b8c857e4b05bf73912a4d9/1371064436860/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4d9/1371064436860/) |
| [A34](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4df/1371064436759/) | Tour / Brooklyn | `51b8c857e4b05bf73912a4df/1371064436759/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4df/1371064436759/) |
| [A35](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4e5/1371064436167/) | Tour / Los Angeles | `51b8c857e4b05bf73912a4e5/1371064436167/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4e5/1371064436167/) |
| [A36](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4eb/1371064436244/) | Tour / San Diego | `51b8c857e4b05bf73912a4eb/1371064436244/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4eb/1371064436244/) |
| [A37](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4f1/1371064436152/) | Tour / San Francisco | `51b8c857e4b05bf73912a4f1/1371064436152/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4f1/1371064436152/) |
| [A38](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4f7/1371064442128/) | Tour / Portland | `51b8c857e4b05bf73912a4f7/1371064442128/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4f7/1371064442128/) |
| [A39](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4fd/1371064437973/) | Tour / Seattle | `51b8c857e4b05bf73912a4fd/1371064437973/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a4fd/1371064437973/) |
| [A40](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a503/1371064439664/) | Tour / Bellingham | `51b8c857e4b05bf73912a503/1371064439664/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a503/1371064439664/) |
| [A41](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a509/1371064435819/) | East Village photograph | `51b8c857e4b05bf73912a509/1371064435819/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a509/1371064435819/) |
| [A42](https://web.archive.org/web/20200220154840im_/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a512/1371064436688/) | Vancouver photograph | `51b8c857e4b05bf73912a512/1371064436688/` | Cache miss | [All dates](https://web.archive.org/web/*/https://static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/51b8c857e4b05bf73912a42e/51b8c857e4b05bf73912a512/1371064436688/) |

The gallery references image numbers **1, 2, 4, and 5**. There is no observed image-3 reference in that gallery; do not invent an extra slot. A03–A05 are separate top-level assets, not substitutes for the gallery.

## Appendix B. Video recovery inventory

The table preserves the order on the Video page. Titles are short finding aids from archived player metadata, not evidence of current playback. Each “Player capture” link points to the resolved replay observed during inspection. Full source-embed and resolved-embed URL variants are preserved in JSON.

| Order | Title / finding aid | YouTube ID / watch link | Player capture | State |
| --- | --- | --- | --- | --- |
| 1 | Anna Karina | [3ZODZPRywUI](https://www.youtube.com/watch?v=3ZODZPRywUI) | [2016-08-22 21:49:37](https://web.archive.org/web/20160822214937if_/https://www.youtube.com/embed/3ZODZPRywUI?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 2 | Slick Watts | [IJnuXQM41Dk](https://www.youtube.com/watch?v=IJnuXQM41Dk) | [2016-11-24 11:59:49](https://web.archive.org/web/20161124115949if_/https://www.youtube.com/embed/IJnuXQM41Dk?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 3 | Seijun Suzuki | [t4y9z3eIFLk](https://www.youtube.com/watch?v=t4y9z3eIFLk) | [2016-10-17 03:40:42](https://web.archive.org/web/20161017034042if_/https://www.youtube.com/embed/t4y9z3eIFLk?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 4 | Fou Lee | [PJLZQVRMzYM](https://www.youtube.com/watch?v=PJLZQVRMzYM) | [2016-11-30 14:17:40](https://web.archive.org/web/20161130141740if_/https://www.youtube.com/embed/PJLZQVRMzYM?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 5 | Title unresolved | [yQwihvgbJsI](https://www.youtube.com/watch?v=yQwihvgbJsI) | [2024-08-20 15:53:26](https://web.archive.org/web/20240820155326if_/https://www.youtube.com/embed/yQwihvgbJsI?feature=oembed&wmode=opaque&enablejsapi=1) | After reference; metadata only |
| 6 | HI-808 | [9vFVp00-19M](https://www.youtube.com/watch?v=9vFVp00-19M) | [2016-11-16 04:56:05](https://web.archive.org/web/20161116045605if_/https://www.youtube.com/embed/9vFVp00-19M?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 7 | Title unresolved | [uIRZ14vIiOc](https://www.youtube.com/watch?v=uIRZ14vIiOc) | [2023-06-27 00:44:35](https://web.archive.org/web/20230627004435if_/https://www.youtube.com/embed/uIRZ14vIiOc?feature=oembed&wmode=opaque&enablejsapi=1) | After reference; metadata only |
| 8 | Joe Metro | [Wz79goWQrYU](https://www.youtube.com/watch?v=Wz79goWQrYU) | [2016-12-26 13:25:26](https://web.archive.org/web/20161226132526if_/https://www.youtube.com/embed/Wz79goWQrYU?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 9 | Loyalty | [PHDyPvF0KL8](https://www.youtube.com/watch?v=PHDyPvF0KL8) | [2017-01-08 23:50:15](https://web.archive.org/web/20170108235015if_/https://www.youtube.com/embed/PHDyPvF0KL8?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 10 | Back Home | [En8DwCeKa6M](https://www.youtube.com/watch?v=En8DwCeKa6M) | [2016-12-24 13:52:01](https://web.archive.org/web/20161224135201if_/https://www.youtube.com/embed/En8DwCeKa6M?feature=oembed&wmode=opaque&enablejsapi=1) | Player error; no media file |
| 11 | Freewheelin | [0wN10msgz88](https://www.youtube.com/watch?v=0wN10msgz88) | [2016-11-15 06:56:11](https://web.archive.org/web/20161115065611if_/https://www.youtube.com/embed/0wN10msgz88?wmode=opaque&enablejsapi=1) | Player error; no media file |

The fifth and seventh player replays resolve to 2024 and 2023, even though their embed IDs come from the 2020 site page. Those player capture dates must not be used as evidence of a post-2021 change to the site's video list. [S05](https://web.archive.org/web/20200802161924/http://bluescholars.com/video)

The blog additionally references a SoundCloud player for **track 87129356** and an outbound `prometheusbrown/racist-accident` track URL (X29–X30). Both requests were cache misses here. Preserve the exact URLs and any artwork/metadata found; do not claim an audio file or working playback has been recovered.

## Appendix C. Forty blog-entry finding aids

These are compact location aids for entries seen in the two listings, **not replacement titles or a complete permalink catalog**. For titleless/reblog blocks, confirm boundaries and date associations against raw HTML before assigning content to a rebuilt article. The checklist CSV includes source pages and any known permalink record.

### Listing 1 — [source](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/)


| ID | Publication date observed | Finding aid, not original title | Permalink evidence |
| --- | --- | --- | --- |
| B01 | 2013-09-09 | Eugene gallery | [P08](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/2013/9/9/eugene-oregon-august-2013) |
| B02 | 2013-05-13 | Green/gold shirt | [P10](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/bringing-back-the-og-t-shirt-in-green-and-gold-if) |
| B03 | 2013-04-25 | Bellingham poster | Extract from raw source |
| B04 | 2013-04-25 | Trio photo | Extract from raw source |
| B05 | 2013-04-24 | Works preview | Extract from raw source |
| B06 | 2013-04-09 | Audio embed | Extract from raw source |
| B07 | 2013-04-08 | Boston photo | Extract from raw source |
| B08 | 2013-04-07 | Town Hall photo | Extract from raw source |
| B09 | 2013-04-05 | Los Angeles photo | Extract from raw source |
| B10 | 2013-04-02 | Purple/gold shirt | Extract from raw source |
| B11 | 2013-04-02 | Campus article | [P11](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/el-primer-d-a-de-clase) |
| B12 | 2013-03-31 | Tour reblog | Extract from raw source |
| B13 | 2013-03-28 | Photo/reblog block | Extract from raw source |
| B14 | 2013-03-21 | Event reminder | Extract from raw source |
| B15 | 2013-03-19 | Street portrait | Extract from raw source |
| B16 | 2013-03-19 | Video/reblog block | Extract from raw source |
| B17 | 2013-03-16 | Photography event | Extract from raw source |
| B18 | 2013-03-08 | Mixtape link | Extract from raw source |
| B19 | 2013-03-01 | Pho article link | Extract from raw source |
| B20 | 2013-02-28 | Thig reblog | Extract from raw source |

### Listing 2 — [source](https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000)


| ID | Publication date observed | Finding aid, not original title | Permalink evidence |
| --- | --- | --- | --- |
| B21 | 2013-02-27 | Conversation audio | Extract from raw source |
| B22 | 2013-02-26 | Residency | Extract from raw source |
| B23 | 2013-02-19 | Bowery photo | Extract from raw source |
| B24 | 2013-02-12 | SoundCloud notice | Extract from raw source |
| B25 | 2013-02-12 | Website notice | Extract from raw source |
| B26 | 2013-02-12 | Los Angeles photo | Extract from raw source |
| B27 | 2013-02-04 | Conversation event | Extract from raw source |
| B28 | 2013-02-01 | Photography essay | Extract from raw source |
| B29 | 2013-01-18 | Tour: Boston | Extract from raw source |
| B30 | 2013-01-18 | Tour: New York | Extract from raw source |
| B31 | 2013-01-18 | Tour: Brooklyn | Extract from raw source |
| B32 | 2013-01-18 | Tour: Los Angeles | Extract from raw source |
| B33 | 2013-01-18 | Tour: San Diego | Extract from raw source |
| B34 | 2013-01-18 | Tour: San Francisco | Extract from raw source |
| B35 | 2013-01-18 | Tour: Portland | Extract from raw source |
| B36 | 2013-01-18 | Tour: Seattle | Extract from raw source |
| B37 | 2013-01-18 | Tour: Bellingham | Extract from raw source |
| B38 | 2013-01-17 | East Village photo | Extract from raw source |
| B39 | 2013-01-17 | Album interview link | Extract from raw source |
| B40 | 2013-01-12 | Vancouver photo | Extract from raw source |

## Appendix D. External sources and link destinations

These are **specific links found in the inspected pages**, useful for recovering matching missing material. Most returned a tool cache miss, not a verified missing page. A whole external website is not part of the automatic mirror just because one source post is useful.

For Tumblr-based posts, the numeric post ID is a useful locator. Search the exact observed URL first; a shortened `/post/ID` or another host alias remains an unverified candidate until inspected. The full external original URLs and exact-index queries are in the manifest.

### First-listing source posts


| ID / replay | Purpose | Original host / locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [X01](https://web.archive.org/web/20201109000819/http://prometheusbrown.tumblr.com/post/48778453576/come-be-the-first-to-see-and-hear) | Works preview | prometheusbrown.tumblr.com / 48778453576 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/48778453576/come-be-the-first-to-see-and-hear) |
| [X02](https://web.archive.org/web/20201109000819/http://prometheusbrown.tumblr.com/post/47552337826/i-dont-know-about-you-but-ll-cool-j-still) | Song reblog | prometheusbrown.tumblr.com / 47552337826 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/47552337826/i-dont-know-about-you-but-ll-cool-j-still) |
| [X03](https://web.archive.org/web/20201109000819/http://tumblr.behzod.net/post/45999182069/geo-and-thig-leading-town-hall-seattle-in-a) | Town Hall photo source | tumblr.behzod.net / 45999182069 | Cache miss | [All dates](https://web.archive.org/web/*/http://tumblr.behzod.net/post/45999182069/geo-and-thig-leading-town-hall-seattle-in-a) |
| [X04](https://web.archive.org/web/20201109000819/http://brownouts.tumblr.com/post/47194105364/saba-los-angeles-march-2013) | Los Angeles / March source | brownouts.tumblr.com / 47194105364 | Cache miss | [All dates](https://web.archive.org/web/*/http://brownouts.tumblr.com/post/47194105364/saba-los-angeles-march-2013) |
| [X05](https://web.archive.org/web/20201109000819/http://prometheusbrown.tumblr.com/post/46946596061/el-primer-dia-de-clase) | Campus article source | prometheusbrown.tumblr.com / 46946596061 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/46946596061/el-primer-dia-de-clase) |
| [X06](https://web.archive.org/web/20201109000819/http://tigloandcole.com/post/46829552058/3-months-later-tour-is-still-distracting-me-from) | Tour reblog source | tigloandcole.com / 46829552058 | Cache miss | [All dates](https://web.archive.org/web/*/http://tigloandcole.com/post/46829552058/3-months-later-tour-is-still-distracting-me-from) |
| [X07](https://web.archive.org/web/20201109000819/http://aviloud.tumblr.com/post/45978111504) | Photographer source / photo pair | aviloud.tumblr.com / 45978111504 | Cache miss | [All dates](https://web.archive.org/web/*/http://aviloud.tumblr.com/post/45978111504) |
| [X08](https://web.archive.org/web/20201109000819/http://rapperswithcameras.tumblr.com/post/45928773522/tonight-click-photo-for-rsvp-if-it-isnt-full-yet) | Event reminder source | rapperswithcameras.tumblr.com / 45928773522 | Cache miss | [All dates](https://web.archive.org/web/*/http://rapperswithcameras.tumblr.com/post/45928773522/tonight-click-photo-for-rsvp-if-it-isnt-full-yet) |
| [X09](https://web.archive.org/web/20201109000819/http://aviloud.tumblr.com/post/45815436731) | Street portrait source | aviloud.tumblr.com / 45815436731 | Cache miss | [All dates](https://web.archive.org/web/*/http://aviloud.tumblr.com/post/45815436731) |
| [X10](https://web.archive.org/web/20201109000819/http://prometheusbrown.tumblr.com/post/45676173875/bambu-books-feat-prometheus-brown-official) | Books video source | prometheusbrown.tumblr.com / 45676173875 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/45676173875/bambu-books-feat-prometheus-brown-official) |
| [X11](https://web.archive.org/web/20201109000819/http://rapperswithcameras.tumblr.com/post/45453724308/rappers-w-cameras-at-town-hall-seattle-march-21) | Photography event source | rapperswithcameras.tumblr.com / 45453724308 | Cache miss | [All dates](https://web.archive.org/web/*/http://rapperswithcameras.tumblr.com/post/45453724308/rappers-w-cameras-at-town-hall-seattle-march-21) |
| [X12](https://web.archive.org/web/20201109000819/http://militantmantras.tumblr.com/post/44885431829/international-womens-day-mixtape) | Mixtape reblog source | militantmantras.tumblr.com / 44885431829 | Cache miss | [All dates](https://web.archive.org/web/*/http://militantmantras.tumblr.com/post/44885431829/international-womens-day-mixtape) |
| [X13](https://web.archive.org/web/20201109000819/http://thignat.tumblr.com/post/44078103689/see-what-i-did-there) | Thig reblog source | thignat.tumblr.com / 44078103689 | Cache miss | [All dates](https://web.archive.org/web/*/http://thignat.tumblr.com/post/44078103689/see-what-i-did-there) |

### Second-listing source posts


| ID / replay | Purpose | Original host / locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [X14](https://web.archive.org/web/20200220154840/http://prometheusbrown.tumblr.com/post/44160858743/click-the-photo-to-listen-to-the-live-audio-of-my) | Conversation audio source | prometheusbrown.tumblr.com / 44160858743 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/44160858743/click-the-photo-to-listen-to-the-live-audio-of-my) |
| [X15](https://web.archive.org/web/20200220154840/http://prometheusbrown.tumblr.com/post/44078753487/townhallday-this-month-i-started-a-three-month) | Residency source | prometheusbrown.tumblr.com / 44078753487 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/44078753487/townhallday-this-month-i-started-a-three-month) |
| [X16](https://web.archive.org/web/20200220154840/http://tfortaylor.com/post/38201102577/thats-love-right-there-town-all-day-tour) | Bowery photo source | tfortaylor.com / 38201102577 | Cache miss | [All dates](https://web.archive.org/web/*/http://tfortaylor.com/post/38201102577/thats-love-right-there-town-all-day-tour) |
| [X17](https://web.archive.org/web/20200220154840/http://townfolk.tumblr.com/post/42563818730/now-at-soundcloud-com-sabzi) | SoundCloud announcement source | townfolk.tumblr.com / 42563818730 | Cache miss | [All dates](https://web.archive.org/web/*/http://townfolk.tumblr.com/post/42563818730/now-at-soundcloud-com-sabzi) |
| [X18](https://web.archive.org/web/20200220154840/http://prometheusbrown.tumblr.com/post/42956212601/prometheusbrown-com-back-in-business) | Website announcement source | prometheusbrown.tumblr.com / 42956212601 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/42956212601/prometheusbrown-com-back-in-business) |
| [X19](https://web.archive.org/web/20200220154840/http://brownouts.tumblr.com/post/42939780633/saba-los-angeles-december-2012) | Los Angeles / December source | brownouts.tumblr.com / 42939780633 | Cache miss | [All dates](https://web.archive.org/web/*/http://brownouts.tumblr.com/post/42939780633/saba-los-angeles-december-2012) |
| [X20](https://web.archive.org/web/20200220154840/http://prometheusbrown.tumblr.com/post/42295559707/fresh-off-the-boat-with-eddie-huang-the-bay-area) | Conversation event source | prometheusbrown.tumblr.com / 42295559707 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/42295559707/fresh-off-the-boat-with-eddie-huang-the-bay-area) |
| [X21](https://web.archive.org/web/20200220154840/http://prometheusbrown.tumblr.com/post/42032696693/i-wrote-an-essay-on-rap-and-photography-for-the) | Photography essay source | prometheusbrown.tumblr.com / 42032696693 | Cache miss | [All dates](https://web.archive.org/web/*/http://prometheusbrown.tumblr.com/post/42032696693/i-wrote-an-essay-on-rap-and-photography-for-the) |
| [X22](https://web.archive.org/web/20200220154840/http://brownouts.tumblr.com/post/40804720276/somewhere-in-the-east-village-new-york-december) | East Village source | brownouts.tumblr.com / 40804720276 | Cache miss | [All dates](https://web.archive.org/web/*/http://brownouts.tumblr.com/post/40804720276/somewhere-in-the-east-village-new-york-december) |
| [X23](https://web.archive.org/web/20200220154840/http://brownouts.tumblr.com/post/40353069434/saba-vancouver-dec-2012) | Vancouver source | brownouts.tumblr.com / 40353069434 | Cache miss | [All dates](https://web.archive.org/web/*/http://brownouts.tumblr.com/post/40353069434/saba-vancouver-dec-2012) |

### Other article, artist, and audio destinations


| ID / replay | Purpose | Original host / locator | Test result | Other captures |
| --- | --- | --- | --- | --- |
| [X24](https://web.archive.org/web/20201109000819/http://phatlip.tumblr.com/post/44907056828/international-womens-day-mixtape) | Mixtape outbound article | phatlip.tumblr.com / 44907056828 | Cache miss | [All dates](https://web.archive.org/web/*/http://phatlip.tumblr.com/post/44907056828/international-womens-day-mixtape) |
| [X25](https://web.archive.org/web/20201109000819/http://www.bonappetit.com/blogsandforums/blogs/badaily/2013/03/macklemore-loves-pho.html) | Pho outbound article | www.bonappetit.com/blogsandforums/blogs/badaily/2013/03/macklemore-loves-pho.html | Cache miss | [All dates](https://web.archive.org/web/*/http://www.bonappetit.com/blogsandforums/blogs/badaily/2013/03/macklemore-loves-pho.html) |
| [X26](https://web.archive.org/web/20200220154840/http://www.xxlmag.com/features/2013/01/blue-scholars-break-down-cinemetropolis/) | Album outbound article | www.xxlmag.com/features/2013/01/blue-scholars-break-down-cinemetropolis/ | Cache miss | [All dates](https://web.archive.org/web/*/http://www.xxlmag.com/features/2013/01/blue-scholars-break-down-cinemetropolis/) |
| [X27](https://web.archive.org/web/20210529010817/http://prometheusbrown.com/) | Prometheus Brown navigation destination | prometheusbrown.com/ | Timeout | [All dates](https://web.archive.org/web/*/http://prometheusbrown.com/) |
| [X28](https://web.archive.org/web/20210529010817/http://sabzi.co/) | Sabzi navigation destination | sabzi.co/ | Readable 2021 capture | [All dates](https://web.archive.org/web/*/http://sabzi.co/) |
| [X29](https://web.archive.org/web/20201109000819/https://soundcloud.com/prometheusbrown/racist-accident) | SoundCloud track | soundcloud.com/prometheusbrown/racist-accident | Cache miss | [All dates](https://web.archive.org/web/*/https://soundcloud.com/prometheusbrown/racist-accident) |
| [X30](https://web.archive.org/web/20201109000819/https://w.soundcloud.com/player/?liking=false&origin=tumblr&sharing=false&url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F87129356&wmode=opaque) | SoundCloud player / track 87129356 | w.soundcloud.com/player/ | Cache miss | [All dates](https://web.archive.org/web/*/https://w.soundcloud.com/player/?liking=false&origin=tumblr&sharing=false&url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F87129356&wmode=opaque) |

Preserve other outbound links—ticketing, social accounts, photographer credits, event pages, and reference articles—as they are extracted from the raw pages. Those destinations have not all been expanded into individual manifest records; the present 30 are a targeted recovery subset, not every outbound link on the site.

## Appendix E. Deliverables and source references

| File | Contents |
| --- | --- |
| `REPORT.md` | This complete source-location and recovery report. |
| `REPORT.html` | Locally readable/printable HTML version; no external runtime assets. |
| `recovery-manifest.json` | All 97 records, evidence states, original/replay/raw/index URLs, and blog checklist. |
| `recovery-manifest.csv` | Flat URL inventory for sorting and handing to another worker. |
| `blog-entry-checklist.csv` | Forty listing entries with source and permalink evidence. |
| `recovery-seeds-expanded.json` | Compatible page/image seed data for the supplied recovery project; not a downloaded-site catalog. |
| `observed-archive-urls.txt` | Replay request URL list only. |
| `capture-search-queries.csv` | 31 targeted archive queries, separating observed URLs from unverified candidates. |
| `REQUEST-OBSERVATIONS.md` | Additional raw/index/alternate-date and replay-modifier probe outcomes. |
| `PROJECT-INSPECTION.md` | What the supplied code actually handles, and what still needs manual investigation. |
| `project-reference/` | The supplied README and verification report, copied as context. |

### Primary reference locations


S01. [Selected homepage](https://web.archive.org/web/20210529010817/http://bluescholars.com/)


S02. [First readable blog listing](https://web.archive.org/web/20201109000819/http://bluescholars.com/blog/)


S03. [Second readable blog listing](https://web.archive.org/web/20200220154840/http://bluescholars.com/blog?offset=1362122742000)


S04. [Shows](https://web.archive.org/web/20200703230849/http://bluescholars.com/shows)


S05. [Video](https://web.archive.org/web/20200802161924/http://bluescholars.com/video)


S06. [Shop / captured provider error](https://web.archive.org/web/20200718164929/http://bluescholars.com/shop)


S07. [Holler](https://web.archive.org/web/20200703230805/http://bluescholars.com/holler)


S08. [Eugene article](https://web.archive.org/web/20200220154703/http://bluescholars.com/blog/2013/9/9/eugene-oregon-august-2013)


S09. [Third blog listing / captured provider error](https://web.archive.org/web/20190719224039/http://bluescholars.com/blog?offset=1358016466000)


S10. [Original 2019 blog request, resolved error capture](https://web.archive.org/web/20190719224804/http://bluescholars.com/blog)


S11. [Homepage photo / actual capture](https://web.archive.org/web/20210529010844/https://images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/1371078164544-2RKW5D1QDQ5IXSVM5B2N/ke17ZwdGBToddI8pDm48kIZpWXENTEukrBXe6_rB7blZw-zPPgdn4jUwVcJE1ZvWQUxwkmyExglNqGp0IvTJZamWLI2zvYWH8K3-s_4yszcp2ryTI0HqTOaaUohrI8PIF2CO6JwS3nXJTgmvDX6VE5p5CmEHphUtvFe0ff6hcA8KMshLAGzx4R3EDFOm1kBS/front-page.jpg)


S12. [Internet Archive CDX API documentation](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server)


S13. [Internet Archive availability API documentation](https://archive.org/help/wayback_api.php)


S14. [Webrecorder pywb replay modifiers](https://pywb.readthedocs.io/en/develop/manual/rewriter.html)


S15. [Squarespace JSON context documentation](https://developers.squarespace.com/beginner-tutorial)


S16. [GitHub Pages static hosting documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)


S17. [Supplied project README](project-reference/README.md)


S18. [Supplied project verification report](project-reference/VERIFICATION.md)


S19. [Inspection notes on supplied recovery code](PROJECT-INSPECTION.md)


### Inspection boundary

The page, image, and video observations were rechecked in this report session on October 15, 2026. Exact alternative June 2016 content, archive-wide CDX results, and original raw downloads were not obtained. Earlier-date/JSON/CDX candidates are clearly separated from successfully observed replay content. The supplied project was inspected, not redeployed. No new GitHub operation was performed for this report.

## Continuation update — October 16, 2026

The recovery and static build continued beyond the original research handoff. The current ignored checkpoint has 4,960 resource records (1,036 recovered, 14 review-needed, 156 failed, and 3,754 queued), 8,874 attached capture rows, and 845 unique downloaded files (64,215,540 bytes). The bounded 2007 continuation `38840327453` is currently acquiring from the saved `38834520393` checkpoint; its artifact will be merged after the run finishes. The current checkpoint must be saved before changing machines because `recovery/state.json` and `recovery/raw/` are ignored by Git.

A separate `/lj/` section now has eight recovered HTML capture routes from a complete 226-row/115-URL Wayback host index plus Common Crawl: the latest old-layout October 2011 front page and two individual 2007 posts, three dated alternate captures, a 2010 Common Crawl root response, and a 2009 Common Crawl profile. Twenty locally recovered 2007–2008 photos are used by those captured pages. Four of six entry texts on the 2011 page have no standalone capture. The custom journal stylesheet is now retrieved; the separate platform stylesheet bundle was not retrieved, the 2014/2021 Eventful poster remains unapproved for compatibility, and one image request yields only a Wayback HTML lander. See [the independent archive report](OTHER_ARCHIVES.md) for per-capture hashes and exact limits.

The unreviewed candidate contains 449 recovered pages, 4 derived pages, 765 placeholders, and 420 local source assets. Candidate builds at both `/` and `/bluescholars/` have no remote automatic asset dependencies, and all eight `/lj/` capture routes have local page routes; the formerly unresolved 2009 and cross-era links now have explicit gap or edition-bridge pages, and both candidate path checks pass with zero local-link errors. A scan of generated HTML automatic references and CSS `url()` also found zero remote dependencies. The full suite passes 119 tests, but incomplete source/visual coverage and the false publication-review flags prevent release. The public `keithah/bluescholars` repository remains on `main`. At the owner’s direct request, an incomplete candidate preview is live at `https://keithah.github.io/bluescholars/` from the separate `gh-pages` branch (Pages build `38851321206`, commit `cc3ddeea338842c97ecbaa6970b591183faab384`). This preview is not a reviewed release; `source/review.json` remains false.
