#!/usr/bin/env python3
"""Preserve dated photographer and Seattle Weekly pages linked from the 2011 Blue Scholars VIP story."""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import base64
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/other-archives/photographer"
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"
TARGETS = [
    "https://www.arminausejo.com/blue-scholars-kickstarter-vip-party/",
    "https://verdugo.smugmug.com/Events/Blue-Scholars-Cinemetropolis/",
    "https://www.seattleweekly.com/slideshow/blue-scholars-vip-party-theater-off-jackson-33576391/",
    "https://www.flickr.com/photos/arminausejo/sets/72157626987127616/",
    "http://www.flickr.com/photos/arminausejo/sets/72157626987127616/",
]


def sha1_base32(body: bytes) -> str:
    return base64.b32encode(hashlib.sha1(body).digest()).decode("ascii").rstrip("=")


def safe_link(url: str) -> tuple[str, list[str]]:
    """Drop transient signed/query credentials from derived provenance metadata."""
    parts = urlsplit(url)
    secret_keys = {"gototoken", "access_token", "api_key", "apikey", "auth_token", "signature"}
    kept, redacted = [], []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.casefold() in secret_keys:
            redacted.append(key)
        else:
            kept.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment)), redacted


def recover_images(max_urls: int = 20, max_files: int = 100, delay: float = 1.5) -> dict:
    """Index and preserve every distinct memento for source-linked event photos."""
    if max_urls < 1 or max_files < 1 or delay < 0:
        raise ValueError("limits must be positive and delay nonnegative")
    page_manifest_path = OUT / "manifest.json"
    page_manifest = json.loads(page_manifest_path.read_text(encoding="utf-8"))
    out = OUT / "images"
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "version": 1, "archive": "Internet Archive Wayback", "source_page_manifest": str(page_manifest_path.relative_to(ROOT)),
        "urls": {}, "revisions": {}}
    urls = manifest["urls"]
    for capture in page_manifest["captures"].values():
        for image in capture.get("images", []):
            url = image["url"]
            parsed = urlsplit(url)
            host, image_path = parsed.netloc.lower(), parsed.path.lower()
            relevant = (
                "blue-scholars-061511" in image_path or "geosabzi" in image_path
                or (host in ("verdugo.smugmug.com", "photos.smugmug.com")
                    and "blue-scholars-cinemetropolis" in image_path)
                or (host == "vvoice.vo.llnwd.net" and "blue-scholars-vip-party" in image_path)
                or (host == "media.seattleweekly.com" and image_path.endswith("/6583984.0.jpg"))
            )
            if not relevant or parsed.scheme not in ("http", "https"):
                continue
            record = urls.setdefault(url, {"original_url": url, "page_refs": []})
            ref = {"timestamp": capture["timestamp"], "page_url": capture["original_url"],
                   "title": capture.get("title", "")}
            if ref not in record["page_refs"]:
                record["page_refs"].append(ref)
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source preservation)"
    report = {"source": "2011 Blue Scholars VIP party / Cinemetropolis photographer and Seattle Weekly pages",
              "candidate_image_urls": len(urls), "queried": 0, "index_rows": 0,
              "distinct_image_revisions": 0, "attempted_replays": 0, "recovered": 0,
              "unique_payloads": 0, "failures": [], "rate_limited": False,
              "limitations": ["Only exact image URLs embedded by the recovered pages were considered.",
                              "All source images remain local-only pending rights review."]}
    unqueried = [(url, record) for url, record in urls.items() if "cdx_rows" not in record]
    for url, record in unqueried[:max_urls]:
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
        except ArchiveCooldown:
            raise
        except Exception as exc:
            record["query_error"] = f"{type(exc).__name__}: {exc}"
            report["failures"].append({"url": url, "stage": "cdx", "error": record["query_error"]})
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)
    pending = []
    for url, record in urls.items():
        good = [row for row in record.get("cdx_rows", []) if len(row) >= 6 and row[2] == "200"
                and row[3].lower().startswith("image/")]
        grouped: dict[str, list[list[str]]] = {}
        for row in good:
            grouped.setdefault(row[4], []).append(row)
        for digest, rows in grouped.items():
            key = f"{url}@@{digest}"
            if key in manifest["revisions"] and (ROOT / manifest["revisions"][key].get("raw_path", "")).is_file():
                continue
            ref_stamps = [ref["timestamp"] for ref in record["page_refs"]]
            row = min(rows, key=lambda r: min((abs(int(r[0]) - int(stamp)) for stamp in ref_stamps
                if r[0].isdigit() and stamp.isdigit()), default=10**30))
            pending.append((url, key, row, [item[0] for item in rows]))
    report["distinct_image_revisions"] = len(pending)
    for url, key, row, timestamps in pending:
        if report["attempted_replays"] >= max_files or report["rate_limited"]:
            break
        timestamp, original, _, mime, digest, length = row[:6]
        replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
        entry = {"original_url": original, "timestamp": timestamp, "cdx_mime": mime,
                 "cdx_digest": digest, "cdx_length": int(length), "same_digest_timestamps": timestamps,
                 "replay_url": replay, "page_refs": urls[url]["page_refs"]}
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
                    if len(body) > 25_000_000:
                        raise ValueError("photo exceeded 25 MB cap")
            data = bytes(body)
            from restore.archive import validate_payload
            validate_payload(data, "image")
            if sha1_base32(data) != digest:
                raise ValueError("replayed bytes do not match CDX SHA-1")
            sha256 = hashlib.sha256(data).hexdigest()
            ext = Path(urlsplit(original).path).suffix.lower() or ".bin"
            destination = raw / f"{sha256}{ext}"
            if not destination.exists():
                destination.write_bytes(data)
            entry.update({"sha256": sha256, "bytes": len(data), "raw_path": destination.relative_to(ROOT).as_posix(),
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
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if report["rate_limited"]:
            break
        time.sleep(delay)
    report["url_records"] = len(urls)
    report["revision_records"] = len(manifest["revisions"])
    report["unique_payloads"] = len({x["sha256"] for x in manifest["revisions"].values() if x.get("status") == "recovered"})
    manifest["last_report"] = report
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def recover(delay: float = 1.5) -> dict:
    if delay < 0:
        raise ValueError("delay must be nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = OUT / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "version": 1, "source_story": "https://www.arminausejo.com/blue-scholars-kickstarter-vip-party/",
        "archive": "Internet Archive Wayback", "pages": {}, "captures": {}}
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source preservation)"
    report = {"targets": len(TARGETS), "queried": 0, "capture_rows": 0, "replayed": 0,
              "verified_pages": 0, "failures": [], "rate_limited": False,
              "limitations": ["All third-party page material is local source evidence only.",
                              "Flickr histories are exact-URL checks; alternate CDN URLs were not inferred."]}
    for url in TARGETS:
        record = manifest["pages"].setdefault(url, {"original_url": url, "cdx_rows": []})
        if "queried_at" not in record and "query_error" not in record:
            try:
                response = session.get(CDX, params={"url": url, "matchType": "exact", "output": "json",
                    "fl": FIELDS, "filter": "statuscode:200", "collapse": "digest", "limit": 100}, timeout=(10, 45))
                if response.status_code == 429:
                    report["rate_limited"] = True
                    report["failures"].append({"url": url, "stage": "cdx", "error": "HTTP 429; stopped"})
                    break
                response.raise_for_status()
                data = response.json()
                record["cdx_rows"] = data[1:] if data else []
                record["queried_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                report["queried"] += 1
                report["capture_rows"] += len(record["cdx_rows"])
            except ArchiveCooldown:
                raise
            except Exception as exc:
                record["query_error"] = f"{type(exc).__name__}: {exc}"
                report["failures"].append({"url": url, "stage": "cdx", "error": record["query_error"]})
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            time.sleep(delay)
    for url, page in manifest["pages"].items():
        if report["rate_limited"]:
            break
        for timestamp, original, status, mime, digest, length in page.get("cdx_rows", []):
            key = f"{original}@@{timestamp}@@{digest}"
            old = manifest["captures"].get(key, {})
            if old.get("sha256") and (ROOT / old.get("raw_path", "")).is_file():
                continue
            replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
            try:
                response = session.get(replay, timeout=(10, 60))
                if response.status_code == 429:
                    report["rate_limited"] = True
                    raise RuntimeError("HTTP 429; stopped")
                response.raise_for_status()
                body = response.content
                if len(body) > 10_000_000:
                    raise ValueError("HTML memento exceeded 10 MB")
                if sha1_base32(body) != digest:
                    raise ValueError("replayed bytes do not match CDX SHA-1")
                sha256 = hashlib.sha256(body).hexdigest()
                out = raw / f"{timestamp}-{sha256}.html"
                out.write_bytes(body)
                soup = BeautifulSoup(body, "html.parser")
                images = []
                for node in soup.find_all(["img", "source"]):
                    for attr in ("src", "data-src", "data-lazy-src", "data-original", "poster"):
                        if node.get(attr):
                            images.append({"url": urljoin(original, node[attr]), "alt": node.get("alt", "")})
                    for attr in ("srcset", "data-srcset"):
                        for candidate in (node.get(attr) or "").split(","):
                            if candidate.strip():
                                images.append({"url": urljoin(original, candidate.strip().split()[0]), "alt": node.get("alt", "")})
                links = []
                for anchor in soup.find_all("a", href=True):
                    safe, redacted = safe_link(urljoin(original, anchor["href"]))
                    link = {"url": safe, "text": anchor.get_text(" ", strip=True)}
                    if redacted:
                        link["sensitive_query_parameters_redacted"] = redacted
                    links.append(link)
                manifest["captures"][key] = {"original_url": original, "timestamp": timestamp,
                    "cdx_mime": mime, "cdx_digest": digest, "cdx_sha1_verified": True,
                    "cdx_length": int(length), "bytes": len(body), "sha256": sha256,
                    "raw_path": out.relative_to(ROOT).as_posix(), "title": soup.title.get_text(" ", strip=True) if soup.title else "",
                    "images": images, "links": links}
                report["replayed"] += 1
                report["verified_pages"] += 1
            except ArchiveCooldown:
                raise
            except Exception as exc:
                manifest["captures"][key] = {"original_url": original, "timestamp": timestamp,
                    "cdx_digest": digest, "replay_url": replay, "error": f"{type(exc).__name__}: {exc}"}
                report["failures"].append({"url": original, "timestamp": timestamp, "stage": "replay",
                                           "error": manifest["captures"][key]["error"]})
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if report["rate_limited"]:
                break
            time.sleep(delay)
    report["page_records"] = len(manifest["pages"])
    report["capture_records"] = len(manifest["captures"])
    report["unique_page_payloads"] = len({x["sha256"] for x in manifest["captures"].values() if x.get("sha256")})
    manifest["last_report"] = report
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--images", action="store_true", help="also index and recover source-linked image revisions")
    parser.add_argument("--max-urls", type=int, default=20)
    parser.add_argument("--max-files", type=int, default=100)
    args = parser.parse_args()
    page_report = recover(args.delay)
    result = {"pages": page_report}
    if args.images:
        result["images"] = recover_images(args.max_urls, args.max_files, args.delay)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
