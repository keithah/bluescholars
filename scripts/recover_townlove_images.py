#!/usr/bin/env python3
"""Recover distinct archived image revisions for Blue Scholars cards on Town Love.

The captured Town Love topic pages are an independent historical source, not
Blue Scholars-owned pages. Images remain in local recovery storage pending
rights review. The manifest records every exact URL query and source memento.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import base64
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "recovery/other-archives/townlove-blue-scholars-recovery.json"
OUT = ROOT / "recovery/other-archives/townlove"
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"
MAX_BYTES = 25_000_000


def largest_image(candidates: list[tuple[str, int]]) -> str:
    """Choose the largest/original responsive-image candidate, not a thumb."""
    normalized = [(url, rank) for url, rank in candidates if url and not url.startswith("data:")]
    return max(normalized, key=lambda item: item[1])[0] if normalized else ""


def discover() -> dict[str, dict]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    found: dict[str, dict] = {}
    for page in source["records"]:
        path = ROOT / page["raw_path"]
        if not path.is_file():
            continue
        soup = BeautifulSoup(path.read_bytes(), "html.parser")
        for anchor in soup.select("a[rel*=bookmark]"):
            title = anchor.get("title") or anchor.get_text(" ", strip=True)
            if not any(term in title.casefold() for term in ("blue scholar", "prometheus brown", "sabzi")):
                continue
            image = anchor.find("img")
            if image is None:
                continue
            candidates: list[tuple[str, int]] = []
            for attr in ("data-src", "src", "data-lazy-src", "data-original"):
                if image.get(attr):
                    url = image[attr]
                    candidates.append((url, 1_000_000 if not re.search(r"-\d+x\d+(?=\.[a-zA-Z0-9]+(?:\?|$))", url) else 1))
            for attr in ("data-srcset", "srcset"):
                for item in (image.get(attr) or "").split(","):
                    if item.strip():
                        pieces = item.strip().split()
                        rank = int(pieces[1][:-1]) if len(pieces) > 1 and pieces[1].endswith("w") and pieces[1][:-1].isdigit() else 0
                        candidates.append((pieces[0], rank))
            chosen = largest_image(candidates)
            if not chosen:
                continue
            url = urljoin(page["original_url"], chosen)
            record = found.setdefault(url, {"original_url": url, "titles": [], "page_refs": []})
            if title not in record["titles"]:
                record["titles"].append(title)
            page_ref = {"timestamp": page["timestamp"], "raw_path": page["raw_path"],
                        "replay_url": page["replay_url"]}
            if page_ref not in record["page_refs"]:
                record["page_refs"].append(page_ref)
    return found


def digest_sha1(payload: bytes) -> str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii").rstrip("=")


def recover(max_urls: int = 25, max_files: int = 100, delay: float = 1.5) -> dict:
    if max_urls < 1 or max_files < 1 or delay < 0:
        raise ValueError("limits must be positive and delay nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "image-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "archive": "Internet Archive Wayback", "source": str(SOURCE.relative_to(ROOT)),
        "urls": {}, "revisions": {}}
    manifest["urls"].update(discover())
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source preservation)"
    report = {"source": "Town Love independent Northwest hip-hop archive",
              "candidate_images": len(manifest["urls"]), "queried": 0, "index_rows": 0,
              "distinct_revisions": 0, "attempted_replays": 0, "recovered": 0,
              "unique_payloads": 0, "failures": [], "rate_limited": False,
              "limitations": ["Only the largest responsive image for Blue Scholars-related cards is selected.",
                              "Every distinct CDX digest is preserved; equal-digest timestamps share the payload.",
                              "Third-party images remain local-only pending rights review."]}
    for url, record in list(manifest["urls"].items())[:max_urls]:
        if "cdx_rows" not in record:
            try:
                response = session.get(CDX, params={"url": url, "matchType": "exact", "output": "json",
                    "fl": FIELDS, "filter": "statuscode:200", "limit": 200}, timeout=(10, 45))
                if response.status_code == 429:
                    report["rate_limited"] = True
                    report["failures"].append({"url": url, "stage": "cdx", "error": "HTTP 429; stopped"})
                    break
                response.raise_for_status()
                data = response.json()
                record["cdx_rows"] = data[1:] if data else []
                record["queried_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                report["queried"] += 1
                report["index_rows"] += len(record["cdx_rows"])
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            except ArchiveCooldown:
                raise
            except Exception as exc:
                report["failures"].append({"url": url, "stage": "cdx", "error": f"{type(exc).__name__}: {exc}"})
            time.sleep(delay)

    pending = []
    for url, record in manifest["urls"].items():
        good = [row for row in record.get("cdx_rows", []) if len(row) >= 6 and row[2] == "200"
                and row[3].lower().startswith("image/")]
        by_digest: dict[str, list[list[str]]] = {}
        for row in good:
            by_digest.setdefault(row[4], []).append(row)
        for digest, rows in by_digest.items():
            key = f"{url}@@{digest}"
            if key in manifest["revisions"] and (ROOT / manifest["revisions"][key].get("raw_path", "")).is_file():
                continue
            page_stamps = [ref["timestamp"] for ref in record["page_refs"]]
            selected = min(rows, key=lambda row: min((abs(int(row[0]) - int(stamp)) for stamp in page_stamps
                if row[0].isdigit() and stamp.isdigit()), default=10**30))
            pending.append((url, key, selected, [row[0] for row in rows]))
    report["distinct_revisions"] = len(pending)
    for url, key, row, timestamps in pending:
        if report["attempted_replays"] >= max_files or report["rate_limited"]:
            break
        timestamp, original, _, mime, expected, length = row[:6]
        replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
        entry = {"original_url": original, "timestamp": timestamp, "cdx_mime": mime,
                 "cdx_digest": expected, "cdx_length": int(length), "same_digest_timestamps": timestamps,
                 "replay_url": replay, "titles": manifest["urls"][url]["titles"],
                 "page_refs": manifest["urls"][url]["page_refs"]}
        report["attempted_replays"] += 1
        try:
            response = session.get(replay, timeout=(10, 60), stream=True)
            if response.status_code == 429:
                report["rate_limited"] = True
                raise RuntimeError("HTTP 429; stopped")
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(128 * 1024):
                if chunk:
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise ValueError("image exceeded 25 MB cap")
            payload = bytes(body)
            validate_payload(payload, "image")
            if digest_sha1(payload) != expected:
                raise ValueError("replay bytes do not match CDX SHA-1")
            sha256 = hashlib.sha256(payload).hexdigest()
            ext = Path(urlsplit(original).path).suffix.lower() or ".bin"
            path = raw / f"{sha256}{ext}"
            if not path.exists():
                path.write_bytes(payload)
            entry.update({"sha256": sha256, "bytes": len(payload), "raw_path": path.relative_to(ROOT).as_posix(),
                          "response_mime": response.headers.get("Content-Type", ""),
                          "cdx_sha1_verified": True, "status": "recovered",
                          "rights_status": "review_required_before_publication"})
            report["recovered"] += 1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            entry.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
            report["failures"].append({"url": original, "timestamp": timestamp, "stage": "replay", "error": entry["error"]})
        manifest["revisions"][key] = entry
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if report["rate_limited"]:
            break
        time.sleep(delay)
    report["url_records"] = len(manifest["urls"])
    report["revision_records"] = len(manifest["revisions"])
    report["unique_payloads"] = len({x["sha256"] for x in manifest["revisions"].values() if x.get("status") == "recovered"})
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "image-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-urls", type=int, default=25)
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()
    print(json.dumps(recover(args.max_urls, args.max_files, args.delay), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
