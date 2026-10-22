# Jamglue / Blue Scholars recovery

This is a separate third-party source archive discovered from a Mass Line forum link. It is not one of the three editions of `bluescholars.com` and is not wired into the public-site build.

## Current recovery

The Wayback CDX results show three contest eras worth keeping distinct:

- The 2007 *Bayani* “Fire for the People” MC and DJ contests. Their contest hub and both result pages survive, including official rules, entry instructions, deadlines, winners, and mix/submission metadata.
- A September–October 2009 Blue Scholars “HI-808” contest on the same Jamglue route, run with Duck Down Records. Its September captures describe the entry period and 226 entries; the October 24 `/entries` capture lists 497 entries across ten pages; the 2010 hub snapshots preserve a 641-entry final state and winners.
- The 2010 shutdown page and later parked/tombstone captures, stored in the main manifest as later domain states.

The recovery presently validates 272 local capture records: 247 unique payload hashes totaling 14,393,161 bytes. That includes 37 unique contest-route payloads, 68 source-linked profile/mix payloads, 85 dated Geologic acapella track-page payloads, 25 additional mix/remix payloads, six HI-808 mix/acapella HTML captures, 11 winner-linked mix/profile/action-page captures, one Jamglue blog post, three wildcard-discovered contest-route variants, and 32 static-asset mementos. `scripts/verify_jamglue_recovery.py` checks every listed path, size, and SHA-256 without network access.

The static files include five Blue Scholars contest graphics discovered through wildcard listings plus two archived mementos of the 2009 campaign's “Start Mixing Now” button. The original banner referenced by the 2009 HI-808 contest page (`bluescholars-contest_top.v28042008.jpg`) and the linked album-art GIF have no exact or wildcard capture rows in the checked indexes. The final page names `jazzbasmati` as grand prize winner, but no capture was found for that mix page; linked pages for other HI-808 entries were recovered separately.

## Media and limits

Six exact linked MP3 download URLs were checked in CDX: the 2007 DJ mix, 2007 MC backing track, 2009 HI-808 mix, 2009 HI-808 acapella, 2009 HI-808 instrumental, and the Geologic acapella track. None returned an indexed capture row. The instrumental track HTML page also had no capture. No audio has been downloaded or reconstructed. The 2009 entries pagination links to pages 2, 3, and 10 (and displays ten pages total), but nine exact CDX checks for `page=2..10` returned no rows; this is a search result, not proof that no alternate archive holds them.

There are large numbers of Jamglue user-generated mixes, profile images, and contest entries. The recovered HTML records these as they appeared in captured pages, but this collection has not been published in the generated website. The official 2007 contest rules license the contest tracks and submitted entries CC BY-NC-SA 2.5; they do not grant a blanket license for Jamglue's website design, promotional banners, every profile image, or all user-submitted material. Keep these source captures in the recovery store pending separate publication review.

## Provenance and resume

The JSON indexes alongside this file preserve original URLs, CDX timestamps/digests/lengths, requested and actual captures, local paths, and SHA-256 hashes. Failed or empty index results remain distinct from downloaded bytes. To verify the current checkpoint from the project root:

```sh
PYTHONPATH=. .venv311/bin/python scripts/verify_jamglue_recovery.py
```

To continue, query Wayback CDX for newly discovered exact source-linked routes or route wildcards, append the returned rows to a new `*-index.json`, then fetch one timestamped `id_` memento at a time with a descriptive user agent, bounded retries and pacing. Validate each body before writing; retain each capture separately and checkpoint after every successful file. Do not use access-control bypasses. The six examined MP3 URLs and the nine missing pagination routes are in `mix-media-index.json`, `hi808-additional-audio-index.json`, and `entries-pagination-index.json`.
