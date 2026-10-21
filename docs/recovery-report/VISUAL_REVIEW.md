# Browser visual review

This is an **agent-performed** browser inspection, not a claim of human review. The reference capture is the May 29, 2021 homepage at `https://web.archive.org/web/20210529010817/http://bluescholars.com/`. Local screenshots were captured from the project-path candidate at `/bluescholars/`.

## Inspected views

- `current-archive-home.png`: landing page with three distinct edition cards (2007, 2009, 2013) and separate secondary links to the recovered related sites.
- `current-2007-news.png`: 2007 News route and functional image-map navigation.
- `current-2009-home.png`: 2009 WordPress homepage and original theme/sidebar treatment.
- `current-2013-home.png` and `current-2013-shop.png`: Squarespace-era layout, navigation, logo and locally saved imagery.
- `current-2013-mobile.png` and `current-2013-mobile-menu.png`: narrow-screen rendering and the opened, clickable mobile navigation.

The 2013 page retains the captured page structure, navigation and image placement rather than borrowing the landing-page design. At 1265×712, the archive reference and candidate were compared at matching viewport dimensions; the recovered ribbon logo and front-page photograph align with the reference after accounting for Wayback chrome and the local restoration notice. Responsive behavior was also checked at 1440, 768 and 390 CSS pixels; the 390-pixel menu opens and exposes the page links. The 2007 and 2009 views use their own source-era designs. No historical content was invented to fill absent pages.

The rebuilt root-mounted candidate was also opened in the browser at `/`, `/2007/news.html`, `/2009/`, `/2009/new-blue-scholars-song-may-day-audio/`, `/2013/`, `/2013/blog/`, `/2013/blog/2013/9/9/eugene-oregon-august-2013/`, `/2013/shows/`, `/2013/video/`, `/2013/holler/` and `/2013/shop/`. The 2007 News page links five recovered LiveJournal entries. The 2009 article includes its surviving comment and a disabled reply form; its far `/2009/page/73/` pagination target is an explicit unrecovered-page notice. The 2013 Shop listing exposes the recovered product entries and the Shows/Holler pages display locally recovered photographs. The Video page presents ordinary YouTube links without autoplay embeds.

The restored MySpace page, Mass Line Media/forum index, 206Proof editions, LiveJournal, Prometheus Brown and Sabzi were also opened in the local browser. Missing MySpace media and unavailable linked images remain labeled as gaps; the legacy fixed-width MySpace layout can overflow on narrow screens. The MySpace live-CDN scan found one locally usable linked-origin photograph, marked undated, and rejected generic camera placeholders.

On October 20, the rebuilt LiveJournal front page was inspected at `/bluescholars/lj/`. It displays the June 2, 2025 captured platform shell around six preserved post entries, with working local links to saved entries and the verified Eventful contest poster. All observed page stylesheets and images resolve to local `/bluescholars/assets/` files. Two disabled historical forms keep their explanation visually hidden and screen-reader-readable so warning text does not collide with the archived theme. The page still has visibly labeled missing profile/sidebar images and has not been compared to a contemporaneous visual capture. This browser screenshot was not saved as a new file.

## Verification boundaries

The final project-path and root-path reviewed-source link/resource checks both passed with zero errors. The automated checker reports no remote automatic asset dependencies; unresolved external media are ordinary links or explicit gaps. The root build was made in a temporary project-local hard-linked copy so path-containment checks remained active. Browser console inspection on the landing page in the prior review showed no errors. These observations cover the listed routes and screenshots, not every page in the archive inventory.

The current candidate reports 1,049 recovered pages, 12 feed pages, 2,208 explicit placeholders, one derived page and 1,505 local source assets, including 56 recovered LiveJournal routes. Current local screenshots are saved beside this report under `docs/recovery-report/screenshots/`. The precise acquisition counts, remaining placeholders and asset gaps are in `GAP_REPORT.json` and `current-checkpoint.json`. Agent visual inspection is recorded in `source/review.json`; `publish_approved` remains false because source/publication review is incomplete. The owner confirmed permission to redistribute the archived material on 2026-10-20; this owner attestation is recorded in `source/review.json` and does not establish a blanket license. This review does not claim a complete restoration or an owner/human visual sign-off.

## Prometheus Brown Twitter snapshots — October 20, 2026

The new `/twitter-prometheusbrown/` archive was inspected in the local browser at the 2009-07-25 and 2022-06-07 captures. The 2009 page retains its original Twitter header, sign-in/profile blocks, original CSS, and dated timeline; its logo and bird image resolve from captured local files. The 2022 capture retains the profile biography, tweet text, counts, and timeline. All pages use local recovered image and CSS files where available; scripts and interactive sign-in controls remain disabled. A stylesheet/srcset review confirmed zero automatic remote dependencies across the 34 generated capture pages. Missing images remain labeled. The 2024 “SQUATTING” capture is visibly classified as a later account takeover; it is preserved as evidence but kept separate from the artist profile. These are agent browser observations; no new screenshot file was saved, and this is not a claim of human review.
