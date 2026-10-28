#!/usr/bin/env python3
"""Preserve the photographer source pages for CHS's 2011 Blue Scholars gallery.

This is a resumable research checkpoint. Current Flickr pages and images are
kept distinct from Wayback mementos and are never promoted to the public site.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import base64
import hashlib
import json
import re
import struct
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PRESS = ROOT / "recovery/other-archives/press-articles/manifest.json"
OUT = ROOT / "recovery/other-archives/flickr-jseattle"
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"
LICENSE = "https://creativecommons.org/licenses/by-sa/2.0/"
MAX_BYTES = 25_000_000
ADDITIONAL_PHOTOS = [
    {"photo_id": photo_id, "owner": "soundscenerevolution",
     "discovery_source": "Sound Scene Revolution's December 5, 2006 Blue Scholars interview links its Flickr Podcast 42 set",
     "source_context": "The Flickr set description says these are photos from the interview and following show with the Blue Scholars; verify each photo individually before labeling it as band-relevant.",
     "source_set_url": "https://www.flickr.com/photos/soundscenerevolution/sets/72157594407516203/"}
    for photo_id in ("315287168", "315286901", "315286550", "315286051",
                     "315285361", "315284650", "315284167", "315283665",
                     "315283206")
] + [
    {"photo_id": "3384748014", "owner": "dlogsr", "discovery_source": "Flickr search for Blue Scholars concert/performance images",
     "source_context": "Ryan D's photo captioned Blue Scholars at the February 28, 2009 premiere of Tad Nakamura's A Song For Ourselves."},
    {"photo_id": "6093660686", "owner": "asiancinevision", "discovery_source": "Flickr search for Blue Scholars concert/performance images",
     "source_context": "Asian CineVision photo titled Geo, Blue Scholars; Flickr lists August 29, 2011 for upload and capture."},
    {"photo_id": "15074004810", "owner": "do206", "discovery_source": "Flickr search for Blue Scholars concert/performance images",
     "source_context": "Do206 photo from the September 12, 2014 Blue Scholars and Made In Heights show at Showbox Market; page credits Nelson Acosta."},
]


def photo_ids() -> list[str]:
    """Derive Flickr photo IDs from the exact article image URLs."""
    manifest = json.loads(PRESS.read_text(encoding="utf-8"))
    found = set()
    for url in manifest.get("image_urls", {}):
        match = re.search(r"(?:static\.flickr\.com|live\.staticflickr\.com)/\d+/(\d+)_", url)
        if match:
            found.add(match.group(1))
    return sorted(found)


def photo_sources() -> list[dict]:
    return ([{"photo_id": photo_id, "owner": "jseattle",
              "discovery_source": "Capitol Hill Seattle embedded gallery", 
              "source_context": "Article-linked photo from CHS Pics: Blue Scholars on Broadway."}
             for photo_id in photo_ids()] + ADDITIONAL_PHOTOS)


def extract_image_object(page: bytes) -> dict | None:
    """Read Flickr's explicit JSON-LD ImageObject, if present."""
    soup = BeautifulSoup(page, "html.parser")
    for node in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(node.string or node.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        for item in data.get("@graph", []) if isinstance(data, dict) else []:
            if item.get("@type") == "ImageObject":
                return item
    return None


def extract_photo_model(page: bytes) -> dict | None:
    """Decode the page-embedded Flickr photo model with its actual size URLs."""
    text = page.decode("utf-8", errors="replace")
    match = re.search(r'"photo-models"\s*:\s*\[\s*\{\s*"data"\s*:\s*', text)
    if not match:
        return None
    start = text.find("{", match.end())
    if start < 0:
        return None
    depth, quoted, escaped = 0, False, False
    for end in range(start, len(text)):
        char = text[end]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    return None
    return None


def largest_photo_variant(page: bytes) -> dict | None:
    model = extract_photo_model(page)
    if not model:
        return None
    variants = []
    def walk(value):
        if isinstance(value, dict):
            url = value.get("displayUrl") or value.get("url")
            width, height = value.get("width"), value.get("height")
            if isinstance(url, str) and "staticflickr.com/" in url and isinstance(width, int) and isinstance(height, int):
                variants.append({"url": "https:" + url if url.startswith("//") else url,
                                 "width": width, "height": height})
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(model)
    return max(variants, key=lambda x: (x["width"] * x["height"], x["width"])) if variants else None


def dimensions(payload: bytes) -> list[int] | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        return list(struct.unpack(">II", payload[16:24]))
    if payload.startswith(b"GIF8") and len(payload) >= 10:
        return list(struct.unpack("<HH", payload[6:10]))
    if payload.startswith(b"\xff\xd8"):
        pos = 2
        while pos + 9 < len(payload):
            if payload[pos] != 0xff:
                pos += 1
                continue
            marker = payload[pos + 1]
            pos += 2
            if marker in (0xd8, 0xd9) or 0xd0 <= marker <= 0xd7:
                continue
            if pos + 2 > len(payload):
                break
            size = int.from_bytes(payload[pos:pos + 2], "big")
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
                          0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                if pos + 7 <= len(payload):
                    return [int.from_bytes(payload[pos + 5:pos + 7], "big"),
                            int.from_bytes(payload[pos + 3:pos + 5], "big")]
                break
            if size < 2:
                break
            pos += size
    return None


def sha1_base32(payload: bytes) -> str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode().rstrip("=")


def recover(delay: float = 1.0, retry_rate_limited: bool = False) -> dict:
    if delay < 0:
        raise ValueError("delay must be nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)
    (OUT / "images").mkdir(exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1,
        "discovery_source": "https://www.capitolhillseattle.com/2011/05/chs-pics-blue-scholars-on-broadway/",
        "photographer": {"name": "J", "account_url": "https://www.flickr.com/photos/jseattle",
                         "flickr_nsid": "57978228@N00"},
        "rights_note": "Current Flickr page JSON-LD states CC BY-SA 2.0; preserve its exact attribution and license evidence.",
        "photo_ids": [], "photos": {}}
    photos = manifest["photos"]
    sources = photo_sources()
    report = {"source_photo_ids": [x["photo_id"] for x in sources], "source_photos": sources,
              "processed": 0, "source_pages_saved": 0,
              "images_saved": 0, "archive_urls_queried": 0, "archive_rows": 0,
              "errors": [], "flickr_cdn_rate_limited": False, "limitations": [
                  "Flickr pages and image files below are current publisher-hosted source copies, not historical mementos.",
                  "The 2011 J gallery images came from the recovered Capitol Hill Seattle article; three later search results are page-only leads.",
                  "Original-size images were not acquired after Flickr returned HTTP 429; the rate-limited resume flag stops at the first further 429.",
                  "Files remain in research storage and are not included in the public site."]}
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source preservation)"
    report["flickr_cdn_rate_limited"] = not retry_rate_limited and any(
        "429" in str(x.get("image_error", "")) or x.get("largest_image_status") == "deferred_after_http_429"
        for x in photos.values())

    def history(record: dict, key: str, url: str) -> None:
        if key in record:
            return
        try:
            r = session.get(CDX, params={"url": url, "matchType": "exact", "output": "json",
                                         "fl": FIELDS, "filter": "statuscode:200", "limit": 100},
                            timeout=(10, 45))
            r.raise_for_status()
            data = r.json()
            record[key] = data[1:] if data else []
            record[f"{key}_queried_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            report["archive_urls_queried"] += 1
            report["archive_rows"] += len(record[key])
        except ArchiveCooldown:
            raise
        except Exception as exc:
            record[f"{key}_error"] = f"{type(exc).__name__}: {exc}"
            report["errors"].append({"url": url, "stage": key, "error": record[f"{key}_error"]})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)

    for source in sources:
        photo_id = source["photo_id"]
        owner = source["owner"]
        record = photos.setdefault(photo_id, {"photo_id": photo_id})
        page_url = f"https://www.flickr.com/photos/{owner}/{photo_id}/"
        record["canonical_page_url"] = page_url
        record["source_account"] = owner
        record["discovery_source"] = source["discovery_source"]
        record["source_context"] = source["source_context"]
        if source.get("source_set_url"):
            record["source_set_url"] = source["source_set_url"]
        if not record.get("source_page_path") or not (ROOT / record["source_page_path"]).is_file():
            try:
                response = session.get(page_url, timeout=(10, 60))
                response.raise_for_status()
                body = response.content
                if len(body) > MAX_BYTES:
                    raise ValueError("source page exceeds 25 MB")
                sha = hashlib.sha256(body).hexdigest()
                path = OUT / "pages" / f"{photo_id}-{sha}.html"
                path.write_bytes(body)
                item = extract_image_object(body)
                variant = largest_photo_variant(body)
                soup = BeautifulSoup(body, "html.parser")
                title = soup.find("meta", property="og:title")
                stats = None
                stats_match = re.search(r'"photo-stats-models"\s*:\s*\[\s*\{\s*"data"\s*:\s*(\{[^{}]*"dateTaken"[^{}]*\})', body.decode("utf-8", errors="replace"))
                if stats_match:
                    try:
                        stats = json.loads(stats_match.group(1))
                    except json.JSONDecodeError:
                        pass
                record.update({"source_page_status": response.status_code,
                    "source_page_final_url": response.url, "source_page_bytes": len(body),
                    "source_page_sha256": sha, "source_page_path": path.relative_to(ROOT).as_posix(),
                    "image_metadata": item or {}, "source_license": (item or {}).get("license"),
                    "creator": (item or {}).get("author", {}), "source_kind": "current Flickr source page",
                    "title": title.get("content", "") if title else "",
                    "date_taken": (stats or {}).get("dateTaken"), "date_posted_epoch": (stats or {}).get("datePosted"),
                    "largest_page_linked_variant": variant,
                    "model_license_id": (extract_photo_model(body) or {}).get("license")})
                report["source_pages_saved"] += 1
            except ArchiveCooldown:
                raise
            except Exception as exc:
                record["source_page_error"] = f"{type(exc).__name__}: {exc}"
                report["errors"].append({"url": page_url, "stage": "source_page", "error": record["source_page_error"]})
        if record.get("source_page_path") and not record.get("largest_page_linked_variant"):
            saved_page = (ROOT / record["source_page_path"]).read_bytes()
            record["largest_page_linked_variant"] = largest_photo_variant(saved_page)
            soup = BeautifulSoup(saved_page, "html.parser")
            title = soup.find("meta", property="og:title")
            stats_match = re.search(r'"photo-stats-models"\s*:\s*\[\s*\{\s*"data"\s*:\s*(\{[^{}]*"dateTaken"[^{}]*\})', saved_page.decode("utf-8", errors="replace"))
            stats = None
            if stats_match:
                try:
                    stats = json.loads(stats_match.group(1))
                except json.JSONDecodeError:
                    pass
            record.update({"title": record.get("title") or (title.get("content", "") if title else ""),
                           "date_taken": record.get("date_taken") or (stats or {}).get("dateTaken"),
                           "date_posted_epoch": record.get("date_posted_epoch") or (stats or {}).get("datePosted"),
                           "model_license_id": record.get("model_license_id") or (extract_photo_model(saved_page) or {}).get("license")})
        img = record.get("image_metadata", {})
        variant = record.get("largest_page_linked_variant") or {}
        image_url = variant.get("url") or img.get("contentUrl")
        if image_url:
            record["largest_current_image_url"] = image_url
            if "429" in str(record.get("image_error", "")):
                record["largest_image_status"] = "deferred_after_http_429"
                report["flickr_cdn_rate_limited"] = True
            if not record.get("largest_image_path") or not (ROOT / record["largest_image_path"]).is_file():
                try:
                    if report["flickr_cdn_rate_limited"]:
                        record["largest_image_status"] = "deferred_after_http_429"
                        raise RuntimeError("previous HTTP 429 recorded; no retry attempted")
                    response = session.get(image_url, timeout=(10, 60), stream=True)
                    if response.status_code == 429:
                        record["largest_image_status"] = "deferred_after_http_429"
                        report["flickr_cdn_rate_limited"] = True
                        raise RuntimeError("HTTP 429 from Flickr CDN; deferred without retry")
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_content(128 * 1024):
                        if not chunk:
                            continue
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("image exceeds 25 MB")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    if not body.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a")):
                        raise ValueError("current contentUrl did not return a supported raster image")
                    sha = hashlib.sha256(body).hexdigest()
                    suffix = Path(urlsplit(image_url).path).suffix or ".jpg"
                    path = OUT / "images" / f"{photo_id}-{sha}{suffix}"
                    path.write_bytes(body)
                    record.update({"largest_image_path": path.relative_to(ROOT).as_posix(), "largest_image_bytes": len(body),
                        "largest_image_sha256": sha, "largest_image_dimensions": dimensions(body),
                        "largest_image_status": "acquired",
                        "image_response_content_type": response.headers.get("Content-Type", ""),
                        "image_source_kind": "current Flickr largest page-linked image copy", "rights_status": "CC BY-SA 2.0 stated by Flickr; held local pending site-level review"})
                    report["images_saved"] += 1
                except ArchiveCooldown:
                    raise
                except Exception as exc:
                    record["image_error"] = f"{type(exc).__name__}: {exc}"
                    if record.get("largest_image_status") != "deferred_after_http_429":
                        report["errors"].append({"url": image_url, "stage": "current_image", "error": record["image_error"]})
        history(record, "page_cdx_rows", page_url)
        if image_url:
            history(record, "largest_image_cdx_rows", image_url)
        content_url = img.get("contentUrl")
        if content_url and content_url != image_url:
            history(record, "image_cdx_rows", content_url)
        report["processed"] += 1
        manifest["photo_ids"] = report["source_photo_ids"]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)

    report["page_records_total"] = len(photos)
    report["source_pages_present"] = sum(bool(x.get("source_page_path") and (ROOT / x["source_page_path"]).is_file()) for x in photos.values())
    report["current_image_files_present"] = sum(bool(x.get("image_path") and (ROOT / x["image_path"]).is_file()) for x in photos.values())
    report["current_image_bytes_total"] = sum(x.get("image_bytes", 0) for x in photos.values() if x.get("image_path") and (ROOT / x["image_path"]).is_file())
    report["distinct_current_image_payloads"] = len({x.get("image_sha256") for x in photos.values() if x.get("image_path") and (ROOT / x["image_path"]).is_file()})
    report["largest_image_files_present"] = sum(bool(x.get("largest_image_path") and (ROOT / x["largest_image_path"]).is_file()) for x in photos.values())
    report["distinct_largest_image_payloads"] = len({x.get("largest_image_sha256") for x in photos.values() if x.get("largest_image_sha256")})
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-rate-limited", action="store_true",
                        help="Retry large Flickr CDN images after the 429 cooldown; stop again at the first HTTP 429")
    args = parser.parse_args()
    print(json.dumps(recover(args.delay, args.retry_rate_limited), indent=2, ensure_ascii=False))
