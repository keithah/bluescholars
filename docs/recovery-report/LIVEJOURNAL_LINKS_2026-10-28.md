# Following the 2005 LiveJournal links

The December 2005 journal homepage and the original post 8711 supplied the outgoing links for this batch. No newly recovered standalone LiveJournal posts are claimed.

## Recovered material

Four original publisher HTML pages were downloaded and checked against their Internet Archive CDX SHA-1 digests, with SHA-256 and byte counts retained in the press manifest:

- BallerStatus's Blue Scholars album review, captured August 14, 2006.
- Seattle Weekly's “Proletariat Blues” by Michaelangelo Matos, captured December 30, 2005.
- Tablet's “Seattle Hip Hop Duo Blue Scholars Builds Connections from their Beats” interview by Tyson Lynn, captured November 12, 2006.
- The Stranger's “Seattle Blows Up with Local Hiphop” by Charles Mudede, captured February 9, 2012. This is a later capture of the article linked in 2005, not a 2005 web-page capture.

The Tablet interview's original Blue Scholars photograph was recovered from a January 7, 2007 image capture and visually inspected. Its date remains separate from the article capture date. Rights remain unreviewed. Six additional photographs from the Stranger article were recovered from October 2012 captures and visually inspected: Framework, Common Market, Boom Bap Project, Grayskul, Cancer Rising, and Blue Scholars. These are the source article’s own labelled illustrations, not replacements for unrelated missing journal photos. Total: seven newly recovered image payloads.

The missing `TheLongMarch.jpg` reference uses a labelled fallback: the official site's `TheLongMarch_web.jpg`, captured February 5, 2006. It depicts the EP cover, but we do not claim it is byte-identical to the unavailable 2005 image. The local journal displays a visible substitution note.

Recovered press destinations are available to the shared link resolver, so links from the journal open the local article archive. Original capture dates and original publisher URLs remain in provenance.

## Gaps and retries

Direct replay of the six old standalone URLs (10246, 10050, 9746, 9551, 9465, 9027) returned 404. Their already recovered homepage-derived reading views remain available. The original previous/next navigation around post 8711 also returned 404. Replaying the non-port alias of 8711 yielded identical bytes and is not counted as a new post.

Exact index queries found no rows for the linked Vanguard article or RA Scion blog post. The original BallerStatus album cover and Seattle Weekly article photo also had no indexed captures. This does not prove that alternate URLs or other archives lack copies.

## Evidence and resumption

- Batch: `recovery/batches/2026-10-28-lj-linked-pages/`.
- Verified article/image bodies and manifest: `recovery/other-archives/press-articles/`.
- Documented cover fallback: `source/asset-aliases.json`.
- Retry only the missing URLs in the batch manifests using the shared ArchiveClient and resumable state. A 429 must stop the batch immediately and defer remaining requests until the shared cooldown expires.
- Next leads: alternate publisher image filenames, additional outgoing links in these recovered interviews, and alternate captures of the original LiveJournal per-post URLs. Preserve each capture's actual date and inspect it before integration.

This remains a recovery preview, not a completed or human-reviewed restoration. Verification results are recorded separately with the batch.

Example bounded retry from the repository root:

```sh
./.venv311/bin/python -m restore index --url 'http://www.livejournal.com/users/bluescholars/10246.html' --match exact --max-pages 1 --delay 3 --timeout 25 --retries 1
```

If that index returns a usable dated HTML row, recover the exact returned URL and timestamp with `python -m restore capture --url URL --timestamp TIMESTAMP --kind html --delay 3 --timeout 25 --retries 1`. Do not substitute an invented timestamp or treat a failed replay as a recovered page. Existing state retains the attempts and shared cooldown.

Browser inspection found that the original Tablet article uses a fixed-width table: at a 390-pixel viewport its document is 819 pixels wide and requires horizontal scrolling. This historical layout is retained; full mobile responsiveness is not claimed. The 2005 journal itself fits the 390-pixel viewport (375-pixel document), displays one slider, and loads the labelled cover locally. The fallback is applied to the original journal capture; the separately extracted reading views retain their existing image gaps.
