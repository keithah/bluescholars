# LiveJournal image and navigation recovery — October 28, 2026

## Added material

- Eight unversioned and eight versioned original LiveJournal image URLs recovered individually from Wayback. These include the header, user markers, previous/next buttons, sharing and memory controls. Versioned URLs are preserved exactly; query strings were not discarded to manufacture matches.
- The October 2, 2011 Friends page recovered. The capture has navigation but no feed entries; this is not counted as new post content.
- Twenty previously recovered Massline photos restored into later LiveJournal captures through 264 individually documented image-proxy mappings: nine Atlanta images, six Jupiter studio images, and five Kirkland images. The original-source versions were already present in older journal captures. Newer captures used broken proxy URLs. Matching the entire entry markup after replacing only image `src` values proved the image-slot correspondence; text, other markup, image count and ordering all match. These are reused local images, not new downloads. Eighteen exact original URL records were also reconciled with the Massline source inventory.

The graphics were visually inspected. The reused photos were inspected in a contact sheet and validated against their recorded hashes and expected image type. Selected source files passed the credential-redaction check. The 264 mappings were independently rechecked against the saved page hashes, identical normalized markup, image positions and asset hashes. `verify_proxy_evidence.py` reproduces that check. Records and request logs are in `recovery/batches/2026-10-28-lj-navigation/`.

## Recovery correction

The URL classifier had treated extensionless LiveJournal calendar, friends and navigation links as images. It now recognizes those page routes while retaining image/CSS classification for assets. A regression test failed before the fix and passed afterward. Thirty-five existing unresolved queue entries were corrected to HTML, preserving their prior attempts.

## Unresolved material

The three calendar captures inspected in this batch returned HTTP 404: September 2007, October 2007 and the 2004 archive. Remaining user-picture requests also failed; their failures remain separate from successful recoveries. No replacement photos or post text were invented. Friends-page recovery does not imply that its historical feed entries survived.

The shared Wayback cooldown remained in effect throughout. There was no 429 in these targeted requests. Ads and tracking pixels are not recovery priorities. Further useful leads include the original URLs behind LiveJournal's image proxy, saved monthly/post captures at alternate dates, and exact source-linked Massline images still absent from the journal catalog.

## Browser baseline

Before deployment, the public default Atlanta post (`/lj/posts/16015.html`) contained zero `<img>` elements and ten missing-image placeholders inside `.entrycontent`. This provides a direct before/after check for the recovered photo mappings.

## Verification and publication

The final code suite passed 345 tests. The code review returned zero findings for the classifier change and its regression test. Local browser inspection found all nine Atlanta article photos loaded and no remote image/script/stylesheet dependencies. Comparison with the deployed tree found 30 journal pages gaining photo hashes. Full root and `/bluescholars/` builds completed; the final outputs passed their whole-site checks with zero errors after refreshing the stylesheet cache keys. Mobile inspection found a 470px image overflow at a 390px viewport; a narrow responsive image rule reduced document width to 375px while retaining all nine loaded Atlanta photos and one timeline. The recovered Friends link navigated locally and selected 2011. Screenshot: `lj-restored-photos-mobile-2026-10-28.png`. Preview deployment follows in the corresponding Pages commit/run. The site remains an unreviewed recovery preview; source-completeness, visual-review and release approval flags are not changed.

Resume with the existing host-scoped recovery commands or explicit capture acquisition, honoring shared cooldown and inspecting each alternate response. Do not repeat successful hashes as newly recovered content. The main active checkout is `/Users/hermes/src/bluescholars`; its ignored `recovery/state.json` preserves the queue and attempts. Successful source bytes and this batch's provenance are tracked for reproduction.

A concrete next discovery request (not yet run in this batch) is:

```sh
cd /Users/hermes/src/bluescholars
./.venv311/bin/python -m restore index --url http://bluescholars.livejournal.com/2007/10/ --match exact --max-pages 1 --delay 3 --timeout 20 --retries 1
```

Inspect returned captures individually with `restore capture --url ORIGINAL --timestamp CAPTURE --kind html`; do not substitute guessed capture dates for evidence. September 2007 and the HTTPS 2004 archive already have completed exact lookups with zero indexed rows, so repeating those unchanged lookups is not a useful next action.
