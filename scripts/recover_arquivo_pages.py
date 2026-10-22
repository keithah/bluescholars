#!/usr/bin/env python3
"""Search Arquivo.pt for dated HTML captures of known Blue Scholars sources.

Pages are kept as raw, recovery-only evidence. This does not add any captured
third-party page to the public-site build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests

from restore.archive import validate_payload

API = "https://arquivo.pt/textsearch"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/arquivo-pages"
URLS = [
    "http://www.xlr8r.com/features?page=1&uid=3B2F773B56B0FC66704ECB5249456966",
    "http://www.kexp.org/learn/docu_music_revolutionaries.asp",
    "http://rapreviews.com/special/nov2007_bluescholars.html",
    "http://www.accesshiphop.com/store/?itemid=17774",
    "http://evolvingmusic.mixmatchmusic.com/2007/10/",
    "http://slizg.eu/viewtopic.php?f=12&t=32593",
    "http://www.punch.pt/2011/06/11/blue-scholars/",
    "http://myspace.com/bluescholars",
    "http://www.myspace.com/bluescholars",
    "https://myspace.com/bluescholars",
    "http://bluescholars.livejournal.com/",
    "http://twitter.com/prometheusbrown",
    "https://twitter.com/prometheusbrown",
    "http://masslinemedia.com/",
    "http://masslinemedia.com/smf/",
    "http://206proof.com/",
    "http://prometheusbrown.com/",
    "http://prometheusbrown.com/blog/",
    "http://sabzi.co/",
    # Artist-related LiveJournal posts found in Arquivo.pt full-text results.
    "https://ceruleanlobster.livejournal.com/459775.html",
    "https://matalicious-rex.livejournal.com/2009/04/02",
    "https://matalicious-rex.livejournal.com/2009/01/03",
    "https://elfypiratequeen.livejournal.com/",
    "https://galkovskyi.livejournal.com/?skip=20",
    "https://jeremytblack.livejournal.com/tag/canton",
    "https://fightingwords.livejournal.com/2009/03",
    "https://xaotica.livejournal.com/2009/07/26",
    "https://lossenelin.livejournal.com/tag/blue+scholars",
    "https://lossenelin.livejournal.com/tag/video",
    "https://brad.livejournal.com/2394003.html",
    "https://sunlit-shadows.livejournal.com/tag/oberlin",
    "https://sunlit-shadows.livejournal.com/",
    "https://fightingwords.livejournal.com/2009/02/28",
    "https://fightingwords.livejournal.com/2009/03/03",
    "https://xaotica.livejournal.com/659642.html",
    "https://minusbaby.livejournal.com/2007/09/11",
    # A Line Out story explicitly linked from a 2009 fan LiveJournal post.
    "http://lineout.thestranger.com/lineout/archives/2009/01/01/the_hiphop_of_snow_and_coffee",
    "http://beatnikside.livejournal.com/693155.html",
    # Independent Beacon Hill Blog coverage links to two snow videos and
    # several official Blue Scholars releases.
    "https://beaconhill.seattle.wa.us/2012/01/19/coffee-and-snow-a-beacon-hill-winter-soundtrack/",
    "https://beaconhill.seattle.wa.us/tag/blue-scholars/",
    "https://beaconhill.seattle.wa.us/2011/09/15/get-off-the-hill-blue-scholars-world-on-a-wire/",
    "https://beaconhill.seattle.wa.us/2012/01/25/blue-scholars-new-video-is-out-seijun-suzuki/",
]
MAX_CAPTURE_BYTES = 20_000_000


def recover(max_urls: int = 50, delay: float = 0.35, offset: int = 0) -> dict:
    if max_urls < 1 or delay < 0 or offset < 0:
        raise ValueError("max_urls must be positive and delay nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    old_path = OUT / "manifest.json"
    manifest = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {
        "version": 1, "captures": {}}
    captures = manifest.setdefault("captures", {})
    raw_indexes = []
    report = {"archive": "Arquivo.pt", "endpoint": API, "known_urls": len(URLS),
              "queried_urls": 0, "history_rows": 0, "successful_html_captures": 0,
              "recovered_payloads": 0, "failures": [], "not_found": [],
              "limitations": ["Exact-URL history queries cover only the listed URLs.",
                              "A missing Arquivo.pt row does not establish that another archive lacks the page."]}
    for url in URLS[offset:offset + max_urls]:
        report["queried_urls"] += 1
        try:
            response = session.get(API, params={"versionHistory": url, "maxItems": 100}, timeout=45)
            response.raise_for_status()
            data = response.json()
            items = data.get("response_items", [])
            raw_indexes.append({"queried_url": url, "estimated_nr_results": data.get("estimated_nr_results"),
                                "items": items})
            report["history_rows"] += len(items)
            if not items:
                report["not_found"].append(url)
            for item in items:
                timestamp = str(item.get("tstamp") or "")
                original = str(item.get("originalURL") or url)
                replay = str(item.get("linkToOriginalFile") or "")
                row_key = f"{original}@@arquivo:{timestamp}:{item.get('digest') or ''}"
                if str(item.get("statusCode")) != "200" or not timestamp.isdigit():
                    continue
                report["successful_html_captures"] += 1
                if row_key in captures and (ROOT / captures[row_key].get("raw_path", "")).is_file():
                    continue
                parsed = urlsplit(replay)
                if parsed.scheme != "https" or parsed.hostname not in ("arquivo.pt", "www.arquivo.pt"):
                    report["failures"].append({"url": original, "timestamp": timestamp,
                                               "error": "Rejected replay outside arquivo.pt"})
                    continue
                try:
                    saved = session.get(replay, timeout=45, stream=True)
                    saved.raise_for_status()
                    body = bytearray()
                    for chunk in saved.iter_content(128 * 1024):
                        body.extend(chunk)
                        if len(body) > MAX_CAPTURE_BYTES:
                            raise ValueError("HTML response exceeded 20 MB acquisition limit")
                    content = bytes(body)
                    validate_payload(content, "html")
                    digest = hashlib.sha256(content).hexdigest()
                    relative = f"recovery/arquivo-pages/raw/{digest}.html"
                    path = ROOT / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_bytes(content)
                    captures[row_key] = {"original_url": original, "timestamp": timestamp,
                                         "sha256": digest, "bytes": len(content), "kind": "html",
                                         "raw_path": relative, "mime": saved.headers.get("Content-Type", ""),
                                         "source_archive": "Arquivo.pt", "source_replay_url": replay,
                                         "source_digest": item.get("digest"),
                                         "source_collection": item.get("collection"),
                                         "queried_url": url, "title": item.get("title", "")}
                    report["recovered_payloads"] += 1
                except Exception as exc:
                    report["failures"].append({"url": original, "timestamp": timestamp,
                                               "error": f"{type(exc).__name__}: {exc}"})
        except Exception as exc:
            report["failures"].append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        old_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)
    (OUT / "query-results.json").write_text(json.dumps(raw_indexes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["unique_payloads"] = len({record["sha256"] for record in captures.values()})
    report["capture_records"] = len(captures)
    manifest["last_report"] = report
    old_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-urls", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--offset", type=int, default=0, help="skip this many known URLs before querying")
    args = parser.parse_args()
    print(json.dumps(recover(args.max_urls, args.delay, args.offset), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
