"""Offline rendering for captured Prometheus Brown Twitter profile pages."""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import base64
import html
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import requests

ARCHIVED_HANDLES = {"prometheusbrown", "bluescholars", "sabzi", "wongweezy", "canhsolo"}


def _archive_url(timestamp: str, original: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original}"


def _twitter_query_url(value: str, original: str, account: str = "prometheusbrown") -> str:
    """Normalize an observed Twitter pagination URL without losing its query."""
    absolute = urljoin(original, value)
    parts = urlsplit(absolute)
    host = (parts.hostname or "").lower()
    if host not in {"twitter.com", "www.twitter.com", "x.com", "www.x.com"}:
        return ""
    path = parts.path.rstrip("/").lower()
    if path not in {f"/{account.lower()}", f"/loggedout/profile/{account.lower()}"}:
        return ""
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "max_id" not in query or query.get("page") != "2":
        return ""
    return urlunsplit(("https", "twitter.com", f"/{account}",
                       urlencode(parse_qsl(parts.query, keep_blank_values=True)), ""))


def _tweet_records(source: bytes, capture: dict, archive_slug: str = "prometheusbrown") -> list[dict]:
    """Extract evidence-backed tweet text and permalink metadata from a capture."""
    soup = BeautifulSoup(source, "html.parser")
    result = []
    seen=set()
    for node in soup.select(".hentry.status, .stream-item, .tweet"):
        content = node.select_one(".entry-content, .tweet-text, .status-body, .js-tweet-text")
        if content is None and "tweet" in node.get("class", []):
            content=node
        if not content:
            continue
        text = " ".join(content.get_text(" ", strip=True).split())
        if not text:
            continue
        link = node.select_one('a[href*="/status/"]')
        permalink=str(link.get("href", "")) if link else ""
        if (text,permalink) in seen: continue
        seen.add((text,permalink))
        date_node = node.select_one(".published, .timestamp, time")
        stamp = ""
        if date_node:
            stamp = str(date_node.get("title") or date_node.get("datetime") or date_node.get_text(" ", strip=True))
        result.append({"text": text, "permalink": permalink,
                       "date": stamp, "capture": str(capture.get("timestamp", "")),
                       "capture_route": f"/twitter-{archive_slug}/captures/{capture.get('route_id', capture.get('timestamp', ''))}/"})
    return result


def asset_suffix(payload: bytes, content_type: str, kind: str) -> str | None:
    """Validate an archived Twitter image or stylesheet and return its safe extension."""
    if kind == "image":
        if payload.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        if payload.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"
        if payload.startswith((b"GIF87a", b"GIF89a")):
            return ".gif"
        if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
            return ".webp"
        if re.search(rb"<svg\b", payload[:2048], re.I):
            return ".svg"
        return None
    if kind == "css":
        prefix = payload[:512].lstrip().lower()
        if prefix.startswith((b"<!doctype html", b"<html", b"<head", b"<body")):
            return None
        if "css" in content_type.lower() or b"{" in payload[:2048]:
            return ".css"
    if kind in ("video", "audio", "media"):
        if len(payload) >= 12 and payload[4:8] == b"ftyp":
            return ".mp4"
        if payload.startswith(b"\x1a\x45\xdf\xa3"):
            return ".webm"
        if payload.startswith(b"OggS"):
            return ".ogv" if kind == "video" else ".ogg"
        if payload.startswith(b"ID3") or (len(payload) > 1 and payload[0] == 0xff and payload[1] & 0xe0 == 0xe0):
            return ".mp3"
        if payload.startswith(b"RIFF") and payload[8:12] == b"WAVE":
            return ".wav"
    return None


def closest_asset_capture(rows: list[list[str]], reference_timestamp: str) -> list[str] | None:
    """Choose the nearest successful exact-URL CDX capture, breaking ties earlier."""
    if not str(reference_timestamp).isdigit():
        return None
    candidates = [row for row in rows if len(row) >= 6 and str(row[0]).isdigit() and row[2] == "200"]
    return min(candidates, key=lambda row: (abs(int(row[0]) - int(reference_timestamp)), row[0])) if candidates else None


def _cdx_sha1(payload: bytes) -> str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii").rstrip("=")


def _alternate_asset(session: requests.Session, timestamp: str, url: str, kind: str,
                     asset_dir: Path, timeout: int) -> dict | None:
    """Fetch the nearest digest-verified capture for the exact linked asset URL."""
    response = session.get("https://web.archive.org/cdx/search/cdx", params={
        "url": url, "output": "json", "filter": "statuscode:200",
        "fl": "timestamp,original,statuscode,mimetype,digest,length",
    }, timeout=(8, timeout))
    if response.status_code == 429:
        raise RuntimeError("Wayback CDX returned HTTP 429; recovery paused")
    response.raise_for_status()
    table = response.json()
    if table == []:
        return None
    expected = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]
    if not table or table[0] != expected:
        raise ValueError("Unexpected CDX columns while looking for an alternate asset capture")
    selected = closest_asset_capture(table[1:], timestamp)
    if not selected:
        return None
    replay = f"https://web.archive.org/web/{selected[0]}id_/{selected[1]}"
    payload_response = session.get(replay, timeout=(8, timeout))
    if payload_response.status_code == 429:
        raise RuntimeError("Wayback replay returned HTTP 429; recovery paused")
    payload_response.raise_for_status()
    payload = payload_response.content
    suffix = asset_suffix(payload, payload_response.headers.get("Content-Type", ""), kind)
    if not suffix:
        raise ValueError("Alternate capture did not contain a valid asset payload")
    actual_digest = _cdx_sha1(payload)
    if selected[4] and actual_digest != selected[4]:
        raise ValueError(f"Alternate asset CDX SHA-1 mismatch: {actual_digest} != {selected[4]}")
    digest = hashlib.sha256(payload).hexdigest()
    destination = asset_dir / f"{digest}{suffix}"
    if not destination.exists():
        destination.write_bytes(payload)
    return {"path": f"assets/{destination.name}", "bytes": len(payload), "sha256": digest,
            "content_type": payload_response.headers.get("Content-Type", ""),
            "source_capture_timestamp": selected[0], "source_original": selected[1],
            "source_cdx_digest": selected[4], "source_cdx_sha1_verified": True,
            "source_replay_url": replay}


def recover_linked_assets(root: Path, max_files: int = 75, delay: float = 0.25,
                          timeout: int = 30, retry_failed: bool = False,
                          archive_slug: str = "prometheusbrown") -> dict:
    """Resumably fetch image and stylesheet references from archived profile pages."""
    root = Path(root)
    path = root / f"recovery/twitter-{archive_slug}/manifest.json"
    manifest = json.loads(path.read_text())
    data_root = path.parent
    refs = []
    linked_pages = list(manifest.get("captures", [])) + list(manifest.get("pagination_pages", []))
    for capture in linked_pages:
        if capture.get("fetch", {}).get("status") != "recovered":
            continue
        source = data_root / str(capture.get("fetch", {}).get("path", ""))
        if not source.is_file():
            continue
        soup = BeautifulSoup(source.read_bytes(), "html.parser")
        timestamp = str(capture.get("timestamp", ""))
        original = str(capture.get("original", capture.get("target_url", "")))
        for node in soup.select("img[src]"):
            url = urljoin(original, str(node.get("src", "")))
            if urlsplit(url).scheme in ("http", "https"):
                refs.append((timestamp, url, "image"))
        for node in soup.select("link[rel~=stylesheet][href]"):
            url = urljoin(original, str(node.get("href", "")))
            if urlsplit(url).scheme in ("http", "https"):
                refs.append((timestamp, url, "css"))
        for video in soup.select("video[poster]"):
            url = urljoin(original, str(video.get("poster", "")))
            if urlsplit(url).scheme in ("http", "https"):
                refs.append((timestamp, url, "image"))
        for source_node in soup.select("video[src], audio[src], source[src], video[video-src], audio[video-src], source[video-src]"):
            raw_url = source_node.get("src") or source_node.get("video-src")
            url = urljoin(original, str(raw_url or ""))
            if urlsplit(url).scheme in ("http", "https"):
                kind = "audio" if source_node.name == "audio" or "audio" in str(source_node.get("type", "")) else "video"
                refs.append((timestamp, url, kind))
    refs = list(dict.fromkeys(refs))
    assets = {(str(item.get("timestamp", "")), str(item.get("url", ""))): item
              for item in manifest.get("assets", [])}
    pending = []
    for ref in refs:
        current = assets.get(ref[:2])
        if current and (current.get("status") == "recovered" or
                        (current.get("status") == "failed" and not retry_failed)):
            continue
        pending.append(ref)
    batch = pending[:max_files]
    asset_dir = data_root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    recovered = 0
    failures = 0
    attempted = 0
    alternate_recovered = 0
    rate_limited = False
    for index, (timestamp, url, kind) in enumerate(batch, 1):
        attempted += 1
        record = assets.get((timestamp, url), {"timestamp": timestamp, "url": url,
                                                 "kind": kind, "attempts": []})
        record["attempts"] = record.get("attempts", [])
        replay = f"https://web.archive.org/web/{timestamp}id_/{url}"
        try:
            response = session.get(replay, timeout=timeout)
            if response.status_code == 429:
                raise RuntimeError("Wayback replay returned HTTP 429; recovery paused")
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            suffix = asset_suffix(response.content, response.headers.get("Content-Type", ""), kind)
            if not suffix:
                raise ValueError(f"Invalid {kind} payload ({response.headers.get('Content-Type', '')}, {len(response.content)} bytes)")
            digest = hashlib.sha256(response.content).hexdigest()
            destination = asset_dir / f"{digest}{suffix}"
            if not destination.exists():
                destination.write_bytes(response.content)
            record.update(status="recovered", path=f"assets/{destination.name}",
                          bytes=len(response.content), sha256=digest,
                          content_type=response.headers.get("Content-Type", ""),
                          http_status=response.status_code)
            recovered += 1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            if "HTTP 429" in str(exc) or "HTTP 429" in record.get("last_error", ""):
                record.update(status="failed", last_error=f"{type(exc).__name__}: {exc}")
                failures += 1
                assets[(timestamp, url)] = record
                manifest["assets"] = list(assets.values())
                path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
                rate_limited = True
                break
            record["direct_error"] = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
                alternate = None
                record["alternate_error"] = "Skipped after a direct replay transport timeout; resumable retry remains available."
            else:
                try:
                    alternate = _alternate_asset(session, timestamp, url, kind, asset_dir, timeout)
                except ArchiveCooldown:
                    raise
                except Exception as alternate_exc:
                    alternate = None
                    record["alternate_error"] = f"{type(alternate_exc).__name__}: {alternate_exc}"
                    if "HTTP 429" in str(alternate_exc):
                        rate_limited = True
            if alternate:
                record.update(status="recovered", recovered_from_alternate_capture=True,
                              requested_capture_timestamp=timestamp, **alternate)
                recovered += 1
                alternate_recovered += 1
            else:
                record.update(status="failed", last_error=f"{type(exc).__name__}: {exc}")
                failures += 1
            record["attempts"].append({"attempt": len(record["attempts"]) + 1,
                                       "error": record.get("last_error", ""),
                                       "alternate_capture": bool(alternate)})
        assets[(timestamp, url)] = record
        manifest["assets"] = list(assets.values())
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        if delay and index < len(batch):
            if rate_limited:
                break
            time.sleep(delay)
        if rate_limited:
            break
    manifest["assets"] = list(assets.values())
    manifest["last_asset_recovery"] = {
        "queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": "Fetch exact page-linked asset URL at its profile capture date, validate the payload signature and store SHA-256; on replay failure, try the nearest successful exact-URL CDX capture and require its SHA-1 digest.",
        "attempted": attempted, "recovered": recovered, "failed": failures,
        "alternate_capture_recovered": alternate_recovered,
        "rate_limited": rate_limited, "remaining_after_run": max(0, len(pending) - attempted),
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {"attempted": attempted, "recovered": recovered, "failed": failures,
            "alternate_capture_recovered": alternate_recovered, "rate_limited": rate_limited,
            "remaining": max(0, len(pending) - attempted),
            "linked_asset_pairs": len(refs),
            "unique_payloads": len({a.get("sha256") for a in assets.values()
                                    if a.get("status") == "recovered" and a.get("sha256")})}


def _capture_page(source: bytes, timestamp: str, original: str, base: str,
                  asset_map: dict[str, str], query_routes: dict[str, str] | None = None,
                  archive_slug: str = "prometheusbrown", display_name: str = "Prometheus Brown",
                  content_classification: str = "profile_content", extra_notice: str = "") -> str:
    soup = BeautifulSoup(source, "html.parser")
    if soup.html is None:
        wrapper = BeautifulSoup("<!doctype html><html><head></head><body></body></html>", "html.parser")
        wrapper.body.extend(list(soup.contents))
        soup = wrapper
    if soup.body is None:
        soup.html.append(soup.new_tag("body"))
    for node in soup.select("script, style, base, meta[http-equiv]"):
        node.decompose()
    for link in list(soup.select("link[rel~=stylesheet][href]")):
        source_url = urljoin(original, str(link.get("href", "")))
        local = asset_map.get(source_url)
        if local:
            link["href"] = local
        else:
            link.decompose()
    for form in list(soup.find_all("form")):
        note = soup.new_tag("p", attrs={"class": "twitter-platform-gap"})
        note.string = "Twitter sign-in and interactive controls are not part of this offline capture."
        form.replace_with(note)
    for node in list(soup.find_all(["iframe", "object", "embed"])):
        note = soup.new_tag("p", attrs={"class": "twitter-platform-gap"})
        note.string = "Embedded media was not captured for offline playback."
        node.replace_with(note)
    for node in list(soup.find_all(["video", "audio"])):
        sources = [node] + list(node.find_all("source"))
        local_source = False
        for source_node in sources:
            source_url = urljoin(original, str(source_node.get("src") or source_node.get("video-src") or ""))
            local = asset_map.get(source_url)
            source_node.attrs.pop("video-src", None)
            source_node.attrs.pop("srcset", None)
            if local:
                source_node["src"] = local
                local_source = True
            else:
                source_node.attrs.pop("src", None)
        poster = str(node.get("poster", ""))
        if poster:
            local_poster = asset_map.get(urljoin(original, poster))
            if local_poster:
                node["poster"] = local_poster
            else:
                node.attrs.pop("poster", None)
        node.attrs.pop("autoplay", None)
        if local_source:
            node["controls"] = "controls"
            node["preload"] = "metadata"
        else:
            note = soup.new_tag("p", attrs={"class": "twitter-platform-gap"})
            note.string = "Embedded media has an archived source lead but no verified local playback file."
            node.replace_with(note)
    for image in list(soup.find_all("img")):
        # Twitter's srcset often points to a CDN variant that was not in the
        # exact page's archive records. The validated local `src` is the
        # preserved master; remove the automatic remote fallback.
        image.attrs.pop("srcset", None)
        source_url = urljoin(original, str(image.get("src", "")))
        alt = image.get("alt") or "Archived Twitter image"
        local = asset_map.get(source_url)
        if local:
            image["src"] = local
            image["loading"] = "lazy"
            image["decoding"] = "async"
        else:
            gap = soup.new_tag("span", attrs={"class": "twitter-image-gap", "title": source_url})
            gap.string = f"[Image not yet recovered: {alt}]"
            image.replace_with(gap)
    for node in soup.find_all(True):
        for attr in list(node.attrs):
            if attr.lower().startswith("on") or attr.lower() == "style":
                del node.attrs[attr]
        if node.name not in ("a", "area", "link") and node.has_attr("href"):
            del node["href"]
        if node.name in ("a", "area"):
            href = str(node.get("href", ""))
            if href.startswith("#") or not href:
                continue
            if href.lower().startswith(("javascript:", "data:")):
                del node["href"]
                continue
            absolute = urljoin(original, href)
            host = (urlsplit(absolute).hostname or "").lower()
            local_query = _twitter_query_url(absolute, original, archive_slug.removeprefix("twitter-")) if (host.endswith("twitter.com") or host.endswith("x.com")) else ""
            local_pagination = False
            if local_query and local_query in (query_routes or {}):
                node["data-archive-href"] = _archive_url(timestamp, absolute)
                node["href"] = base.rstrip("/") + query_routes[local_query]
                node["class"] = list(node.get("class", [])) + ["twitter-pagination-index"]
                node["aria-label"] = (node.get_text(" ", strip=True) or "More posts") + " — browse recovered tweets"
                node.attrs.pop("target", None)
                node.attrs.pop("rel", None)
                local_pagination = True
            elif local_query:
                node["data-archive-href"] = _archive_url(timestamp, absolute)
                node["href"] = base.rstrip("/") + f"/twitter-{archive_slug}/tweets/"
                node["class"] = list(node.get("class", [])) + ["twitter-pagination-index"]
                node["aria-label"] = (node.get_text(" ", strip=True) or "More posts") + " — browse recovered tweets"
                node.attrs.pop("target", None)
                node.attrs.pop("rel", None)
                local_pagination = True
            elif host.endswith("twitter.com") or host.endswith("x.com"):
                profile_path = urlsplit(absolute).path.strip("/").lower().split("/")
                if len(profile_path) == 1 and profile_path[0] in ARCHIVED_HANDLES:
                    node["href"] = base.rstrip("/") + f"/twitter-{profile_path[0]}/"
                else:
                    node["href"] = _archive_url(timestamp, absolute)
            if not local_pagination:
                node["rel"] = "noopener noreferrer"
                node["target"] = "_blank"
    for tweet in soup.select(".hentry.status, .stream-item"):
        status = tweet.get("id", "")
        match = re.search(r"(?:status[_-])?(\d{5,})$", str(status))
        if not match:
            permalink = tweet.select_one('a[href*="/status/"]')
            match = re.search(r"/status/(\d+)", str(permalink.get("href", "")) if permalink else "")
        if match:
            tweet["id"] = "status-" + match.group(1)
    title = soup.title.get_text(" ", strip=True) if soup.title else f"{display_name} on Twitter"
    body_content = "".join(str(child) for child in soup.body.contents)
    local_stylesheets = "".join(str(link) for link in soup.head.select("link[rel~=stylesheet][href]")) if soup.head else ""
    safe_title = html.escape(title)
    route = f"{base}/twitter-{archive_slug}/" if base else f"/twitter-{archive_slug}/"
    notice = (
        f'<header class="twitter-archive-bar"><a href="{route}">← Capture index</a>'
        f'<span>Internet Archive capture {html.escape(timestamp)}</span>'
        f'<a href="{html.escape(_archive_url(timestamp, original), quote=True)}">Original replay</a></header>'
        + (f'<p class="twitter-archive-note">{html.escape(extra_notice)}</p>' if extra_notice else "")
    )
    css = """body{margin:0;color:#20242a;background:#f5f8fa;font:15px/1.5 Arial,sans-serif}
.twitter-archive-bar{position:sticky;top:0;z-index:2;display:flex;gap:1rem;justify-content:space-between;align-items:center;padding:.8rem 1.2rem;background:#fff;border-bottom:1px solid #d5dce2}
.twitter-archive-bar a{color:#25608a}.twitter-capture-title{max-width:1100px;margin:1.5rem auto .6rem;padding:0 1rem;font-size:1.15rem}
.twitter-capture-note{max-width:1100px;margin:0 auto 1rem;padding:0 1rem;color:#53616d;font-size:.9rem}
.twitter-original{max-width:1100px;margin:0 auto 3rem;padding:1rem;background:white;overflow-wrap:anywhere}.twitter-original video,.twitter-original audio{max-width:100%}
.twitter-original img{max-width:100%;height:auto}.twitter-image-gap{display:inline-block;padding:.25rem .5rem;color:#596773;background:#eef2f5;border:1px dashed #aab5bf;font-size:.8rem}
.twitter-platform-gap{padding:.5rem;background:#f4f6f8;color:#596773}@media(max-width:600px){.twitter-archive-bar{flex-wrap:wrap}.twitter-original{padding:.6rem}}"""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{safe_title} — preserved capture</title>{local_stylesheets}<style>{css}</style></head><body>"
        + notice
        + f'<h1 class="twitter-capture-title">{safe_title}</h1>'
        + '<p class="twitter-capture-note">Captured page text and structure are preserved. '
        'Recovered images load locally; missing files are labeled. Scripts and live controls are disabled.</p>'
        + f'<main class="twitter-original" data-twitter-content-classification="{html.escape(content_classification, quote=True)}">{body_content}</main></body></html>'
    )


def _localize_css(data: bytes, source_url: str, asset_map: dict[str, str]) -> bytes:
    text = data.decode("utf-8", errors="replace")
    text = re.sub(r"@import\s+(?:url\()?[^;]+;", "", text, flags=re.I)
    text = re.sub(r"@font-face\s*\{[^}]*\}", "", text, flags=re.I | re.S)
    def replace_url(match):
        raw = match.group(1).strip(" \t\r\n\"'")
        if raw.startswith("data:"):
            return f'url("{raw}")'
        local = asset_map.get(urljoin(source_url, raw))
        return f'url("{local}")' if local else "none"
    text = re.sub(r"url\(\s*([^)]*?)\s*\)", replace_url, text, flags=re.I)
    return text.encode("utf-8")


def build_twitter_archive(root: Path, output: Path, base: str = "",
                          archive_slug: str = "prometheusbrown") -> dict:
    root = Path(root)
    output = Path(output)
    manifest_path = root / f"recovery/twitter-{archive_slug}/manifest.json"
    display_names = {"prometheusbrown": "Prometheus Brown", "bluescholars": "Blue Scholars",
                     "sabzi": "Sabzi", "wongweezy": "Wong Weezy", "canhsolo": "Canh Solo"}
    display_name = display_names.get(archive_slug, archive_slug.replace("-", " ").title())
    if not manifest_path.exists():
        destination = output / f"twitter-{archive_slug}" / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        prefix = base.rstrip("/")
        destination.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(display_name)} on Twitter — Blue Scholars restoration</title>'
            '<style>body{max-width:850px;margin:4rem auto;padding:0 1.5rem;font:18px/1.6 system-ui,sans-serif;color:#20242a}a{color:#285c83}</style>'
            '</head><body><p><a href="' + prefix + '/">← Blue Scholars archive</a></p>'
            f'<h1>{html.escape(display_name)} on Twitter</h1><p>No archived profile captures have been indexed in this build.</p></body></html>',
            encoding="utf-8")
        return {"status": "not_indexed", "captures": 0, "recovered_capture_pages": 0}
    manifest = json.loads(manifest_path.read_text())
    display_name = str(manifest.get("display_name") or display_name)
    capture_rows = manifest.get("captures", [])
    raw_root = manifest_path.parent
    output_root = output / f"twitter-{archive_slug}"
    output_root.mkdir(parents=True, exist_ok=True)
    base_prefix = base.rstrip("/")
    asset_map: dict[tuple[str, str], str] = {}
    for asset in manifest.get("assets", []):
        if asset.get("status") != "recovered" or not asset.get("path"):
            continue
        source_path = (raw_root / asset["path"]).resolve()
        if raw_root.resolve() not in source_path.parents or not source_path.is_file():
            continue
        filename = source_path.name
        local_file = output_root / "assets" / filename
        local_file.parent.mkdir(parents=True, exist_ok=True)
        source_url = str(asset.get("url", ""))
        local_url = base_prefix + f"/twitter-{archive_slug}/assets/" + filename
        if asset.get("kind") == "css":
            local_file.write_bytes(_localize_css(source_path.read_bytes(), source_url, {}))
        elif not local_file.exists():
            local_file.write_bytes(source_path.read_bytes())
        asset_map[(str(asset.get("timestamp", "")), source_url)] = local_url
    rows = []
    recovered_pages = 0
    query_routes: dict[str, str] = {}
    tweet_rows: dict[str, list[dict]] = {}
    pagination_gaps: list[dict] = []
    for item in capture_rows:
        timestamp = str(item.get("timestamp", ""))
        capture = raw_root / str(item.get("fetch", {}).get("path", ""))
        if item.get("fetch", {}).get("status") != "recovered" or not capture.is_file():
            continue
        source = capture.read_bytes()
        route_id = str(item.get("route_id") or timestamp)
        tweet_rows[route_id] = _tweet_records(source, item, archive_slug)
        parsed = BeautifulSoup(source, "html.parser")
        next_link = parsed.select_one("a#more, a[rel~=next]")
        if next_link and next_link.get("href"):
            query = _twitter_query_url(str(next_link["href"]), str(item.get("original", "")), archive_slug)
            if query:
                gap={"capture": timestamp, "url": query,
                     "original_url": urljoin(str(item.get("original", "")), str(next_link["href"]))}
                pagination_gaps.append(gap)
                query_routes[query] = f"/twitter-{archive_slug}/tweets/?capture={item.get('route_id', timestamp)}"
    pagination_pages = manifest.get("pagination_pages", [])
    pagination_routes = {}
    pagination_tweets = []
    for page in pagination_pages:
        fetch = page.get("fetch", {})
        if fetch.get("status") != "recovered" or not fetch.get("path"):
            continue
        source = raw_root / str(fetch["path"])
        if not source.is_file():
            continue
        target = str(page.get("target_url", ""))
        query = _twitter_query_url(target, target, archive_slug)
        if not query:
            continue
        route_id = str(page.get("route_id") or page.get("timestamp", ""))
        captured_year = str(page.get("timestamp", ""))[:4]
        route = f"/twitter-{archive_slug}/pages/{captured_year}/{route_id}/"
        pagination_routes[query] = route
        query_routes[query] = route
        replay_original = str(page.get("original", target))
        notice_text = (
            "This is an archived response to a page-two URL observed in an older profile capture. "
            "The 2022 memento may show the account as it appeared then; the saved response does not prove "
            "Twitter honored the historical max_id request."
        )
        rendered = _capture_page(source.read_bytes(), str(page.get("timestamp", "")), replay_original,
                                 base, {}, query_routes, archive_slug, display_name,
                                 extra_notice=notice_text)
        destination = output_root / "pages" / captured_year / route_id / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        for record in _tweet_records(source.read_bytes(), page, archive_slug):
            record["capture_route"] = route
            pagination_tweets.append(record)
    # A query pagination link has no page-specific replay in this inventory.
    # Don't silently send users to a different profile snapshot.
    for item in capture_rows:
        timestamp = str(item.get("timestamp", ""))
        original = str(item.get("original", f"https://twitter.com/{archive_slug}"))
        capture = raw_root / str(item.get("fetch", {}).get("path", ""))
        valid = timestamp.isdigit() and capture.is_file() and item.get("fetch", {}).get("status") == "recovered"
        route_id = str(item.get("route_id") or timestamp)
        route = f"/twitter-{archive_slug}/captures/{route_id}/"
        if valid:
            page_assets = {url: href for (when, url), href in asset_map.items() if when == timestamp}
            page = _capture_page(capture.read_bytes(), timestamp, original, base, page_assets, query_routes,
                                 archive_slug, display_name, str(item.get("content_classification", "profile_content")))
            destination = output_root / "captures" / route_id / "index.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(page, encoding="utf-8")
            recovered_pages += 1
        title = str(item.get("title") or "")
        if not title and capture.is_file():
            parsed = BeautifulSoup(capture.read_bytes(), "html.parser")
            title = parsed.title.get_text(" ", strip=True) if parsed.title else ""
        body_text = ""
        if capture.is_file():
            body_text = BeautifulSoup(capture.read_bytes(), "html.parser").get_text(" ", strip=True).lower()
        classification = item.get("content_classification", "")
        squatting = classification == "later_account_takeover" or "squatting" in title.lower() or (
            "joined december 2022" in body_text and "posts replies media" in body_text)
        platform_error = classification == "platform_error" or "javascript is not available" in body_text
        status = "Later account takeover; separate from artist profile" if squatting else (
            "Platform error capture; no profile content" if platform_error else
            "Recovered page" if valid else "Capture indexed; page not recovered")
        row = {"timestamp": timestamp, "original": original, "digest": item.get("digest", ""),
               "title": title, "route": route if valid else "", "status": status}
        rows.append(row)
    # Keep a dated index for recovered page-two responses. A query with no
    # verified memento remains visible as an explicit source gap.
    unique_pagination_gaps = list({(item["capture"], item["url"]): item for item in pagination_gaps
                                   if item["url"] not in pagination_routes}.values())
    tweet_index_route = base_prefix + f"/twitter-{archive_slug}/tweets/"
    index_path = output_root / "tweets" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tweets = []
    for timestamp, records in tweet_rows.items():
        for record in records:
            record["capture_route"] = base_prefix + record["capture_route"]
            tweets.append(record)
    for record in pagination_tweets:
        record["capture_route"] = base_prefix + record["capture_route"]
        tweets.append(record)
    tweets.sort(key=lambda item: (item["date"], item["capture"], item["permalink"]))
    tweet_html = []
    for record in tweets:
        permalink = str(record.get("permalink", ""))
        local_link = ""
        if permalink:
            capture_original = next((str(item.get("original", "")) for item in capture_rows
                                     if str(item.get("timestamp", "")) == record["capture"]),
                                    f"https://twitter.com/{archive_slug}")
            local_link = str(record.get("capture_route") or (base_prefix + f"/twitter-{archive_slug}/captures/{record['capture']}/")) + "#status-" + (urlsplit(urljoin(capture_original, permalink)).path.rsplit("/", 1)[-1])
        tweet_html.append(
            '<article class="tweet-index-item" data-capture="' + html.escape(record["capture"], quote=True) + '">'
            '<p>' + html.escape(record["text"]) + '</p><p class="tweet-index-meta">'
            + html.escape(record.get("date", "")) + ' · captured ' + html.escape(record["capture"][:8])
            + (' · <a href="' + html.escape(local_link, quote=True) + '">Open source capture</a>' if local_link else '')
            + '</p></article>')
    gaps_html = ''.join(
        '<li>Capture ' + html.escape(item["capture"]) + ': <a rel="noopener noreferrer" target="_blank" href="'
        + html.escape(_archive_url(item["capture"], item.get("original_url") or item["url"]), quote=True) + '">page two not recovered (check Wayback)</a></li>'
        for item in unique_pagination_gaps)
    pagination_html = ''.join(
        '<li>' + html.escape(str(page.get("timestamp", ""))) + ' · '
        + ('<a href="' + html.escape(base_prefix + pagination_routes[_twitter_query_url(str(page.get("target_url", "")), str(page.get("target_url", "")), archive_slug)], quote=True)
           + '">Open archived page-two response</a>'
           if _twitter_query_url(str(page.get("target_url", "")), str(page.get("target_url", "")), archive_slug) in pagination_routes
           else 'page not locally recovered')
        + ' · source: ' + html.escape(str(page.get("target_url", ""))) + '</li>'
        for page in pagination_pages if page.get("timestamp"))
    search_script = output_root / "tweets" / "search.js"
    search_script.write_text('''const params=new URLSearchParams(location.search);const capture=params.get("capture");const note=document.getElementById("tweet-pagination-note");if(capture&&note){note.hidden=false;note.textContent="The exact page-two capture was not found in the archive index. Showing posts preserved in the parent capture ("+capture+").";}function filterTweets(){const q=document.getElementById("tweet-search").value.toLowerCase();for(const n of document.querySelectorAll(".tweet-index-item")){n.hidden=(capture&&n.dataset.capture!==capture)||!n.textContent.toLowerCase().includes(q)}}document.getElementById("tweet-search").addEventListener("input",filterTweets);filterTweets();
'''.replace("\n+", "\n"), encoding="utf-8")
    tweet_page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Recovered tweets — {html.escape(display_name)}</title><style>'
        'body{max-width:900px;margin:3rem auto;padding:0 1.2rem;font:16px/1.55 system-ui,sans-serif;color:#20242a}a{color:#24567d}h1{font-size:clamp(2rem,6vw,4rem);line-height:1}.tweet-search{box-sizing:border-box;width:100%;padding:.8rem;border:1px solid #aab5bf;border-radius:5px;font:inherit}.tweet-index-item{padding:1rem 0;border-bottom:1px solid #dde2e6}.tweet-index-meta{font-size:.85rem;color:#5c6872}.gap{padding:1rem;background:#f2f5f7}@media(max-width:600px){body{margin:1.5rem auto}}</style></head><body>'
        '<p><a href="' + base_prefix + f'/twitter-{archive_slug}/">← Twitter archive</a></p><h1>Recovered tweets</h1>'
        '<p>' + str(len(tweets)) + ' post entries extracted from locally saved profile captures. Duplicate posts can appear when snapshots overlap.</p>'
        '<label for="tweet-search">Search post text</label><input id="tweet-search" class="tweet-search" type="search" autocomplete="off"><p id="tweet-pagination-note" class="gap" hidden></p>'
        '<h2>Archived page-two responses</h2><ul class="gap">' + (pagination_html or '<li>No exact paginated mementos recovered.</li>') + '</ul>'
        '<h2>Unrecovered pagination targets</h2><ul class="gap">' + (gaps_html or '<li>No remaining observed pagination targets.</li>') + '</ul>'
        + ''.join(tweet_html) + '<script src="' + base_prefix + f'/twitter-{archive_slug}/tweets/search.js" defer></script>'
        '</body></html>')
    index_path.write_text(tweet_page, encoding="utf-8")
    tweet_json = output_root / "tweets" / "index.json"
    tweet_json.write_text(json.dumps({"posts": tweets, "pagination_gaps": unique_pagination_gaps}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    home = output_root / "index.html"
    profile_url = html.escape(str(manifest.get("profile", f"https://twitter.com/{archive_slug}")), quote=True)
    takeover_note = ("A later capture is classified as a separate account takeover, not artist-authored material. "
                     if any("takeover" in row["status"].lower() for row in rows) else "")
    body = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{html.escape(display_name)} on Twitter — Blue Scholars restoration</title>'
        '<style>body{max-width:1100px;margin:4rem auto;padding:0 1.5rem;color:#20242a;font:18px/1.6 system-ui,sans-serif}h1{font-size:clamp(2.2rem,6vw,4.5rem);line-height:1.05}.note{max-width:760px;color:#53616d}table{width:100%;border-collapse:collapse;margin-top:2rem;font-size:15px}th,td{padding:.8rem .6rem;text-align:left;border-bottom:1px solid #d8dfe5;overflow-wrap:anywhere}a{color:#285c83}.digest{font:12px ui-monospace,monospace}@media(max-width:620px){body{margin:2rem auto;padding:0 1rem}table{font-size:13px}th,td{padding:.55rem .35rem}}</style></head><body>',
        '<p><a href="' + base_prefix + '/">← Blue Scholars archive</a></p>',
        f'<p class="archive-eyebrow">{html.escape(display_name.upper())} / TWITTER ARCHIVE</p>',
        f'<h1>{html.escape(display_name)} on Twitter</h1>',
        '<p>This separate archive contains dated Internet Archive captures of <a href="' + profile_url + '">' + html.escape(urlsplit(profile_url).netloc + urlsplit(profile_url).path) + '</a>. Each recovered page is preserved as its own snapshot.</p>',
        '<p><a href="' + tweet_index_route + '">Search ' + str(len(tweets)) + ' recovered tweet entries</a></p>',
        '<p class="note">' + takeover_note + 'Some Twitter snapshots only contain a JavaScript-required message. Captured scripts and interactive controls are disabled; unrecovered images are labeled on each page.</p>',
        '<table><thead><tr><th>Capture date</th><th>Archived page</th><th>Source digest</th><th>Capture status</th></tr></thead><tbody>'
    ]
    for row in rows:
        ts = row["timestamp"]
        date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts
        target = (base_prefix + row["route"]) if row["route"] else _archive_url(ts, row["original"])
        body.append(f'<tr><td>{html.escape(date)}</td><td><a href="{html.escape(target, quote=True)}">{html.escape(row["title"] or "View archived capture")}</a></td><td class="digest">{html.escape(str(row["digest"]))}</td><td>{html.escape(row["status"])}</td></tr>')
    body.append('</tbody></table></body></html>')
    home.write_text("".join(body), encoding="utf-8")
    return {"status": "built", "captures": len(rows), "recovered_capture_pages": recovered_pages,
            "tweet_entries": len(tweets), "pagination_gaps": len(unique_pagination_gaps),
            "account_takeover_captures": sum("takeover" in row["status"].lower() for row in rows),
            "platform_error_captures": sum("platform error" in row["status"].lower() for row in rows),
            "recovered_assets": sum(asset.get("status") == "recovered" for asset in manifest.get("assets", [])),
            "unique_asset_payloads": len({asset.get("sha256") for asset in manifest.get("assets", [])
                                           if asset.get("status") == "recovered" and asset.get("sha256")})}


def build_twitter_archives(root: Path, output: Path, base: str = "") -> dict[str, dict]:
    """Build separate local archives for every Twitter handle with an inventory."""
    reports = {}
    for account in ("prometheusbrown", "bluescholars", "sabzi", "wongweezy", "canhsolo"):
        manifest = Path(root) / f"recovery/twitter-{account}/manifest.json"
        if manifest.is_file() or account == "prometheusbrown":
            reports[account] = build_twitter_archive(root, output, base, account)
    return reports
