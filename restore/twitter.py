"""Offline rendering for captured Prometheus Brown Twitter profile pages."""
from __future__ import annotations

import html
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import requests


def _archive_url(timestamp: str, original: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original}"


def _twitter_query_url(value: str, original: str) -> str:
    """Normalize an observed Twitter pagination URL without losing its query."""
    absolute = urljoin(original, value)
    parts = urlsplit(absolute)
    host = (parts.hostname or "").lower()
    if host not in {"twitter.com", "www.twitter.com", "x.com", "www.x.com"}:
        return ""
    if parts.path.rstrip("/").lower() != "/prometheusbrown":
        return ""
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "max_id" not in query or query.get("page") != "2":
        return ""
    return urlunsplit(("https", "twitter.com", "/prometheusbrown",
                       urlencode(parse_qsl(parts.query, keep_blank_values=True)), ""))


def _tweet_records(source: bytes, capture: dict) -> list[dict]:
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
                       "capture_route": f"/twitter-prometheusbrown/captures/{capture.get('timestamp', '')}/"})
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
    return None


def recover_linked_assets(root: Path, max_files: int = 75, delay: float = 0.25,
                          timeout: int = 30, retry_failed: bool = False) -> dict:
    """Resumably fetch image and stylesheet references from archived profile pages."""
    root = Path(root)
    path = root / "recovery/twitter-prometheusbrown/manifest.json"
    manifest = json.loads(path.read_text())
    data_root = path.parent
    refs = []
    for capture in manifest.get("captures", []):
        if capture.get("fetch", {}).get("status") != "recovered":
            continue
        source = data_root / str(capture.get("fetch", {}).get("path", ""))
        if not source.is_file():
            continue
        soup = BeautifulSoup(source.read_bytes(), "html.parser")
        timestamp = str(capture.get("timestamp", ""))
        original = str(capture.get("original", ""))
        for node in soup.select("img[src]"):
            url = urljoin(original, str(node.get("src", "")))
            if urlsplit(url).scheme in ("http", "https"):
                refs.append((timestamp, url, "image"))
        for node in soup.select("link[rel~=stylesheet][href]"):
            url = urljoin(original, str(node.get("href", "")))
            if urlsplit(url).scheme in ("http", "https"):
                refs.append((timestamp, url, "css"))
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
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    recovered = 0
    failures = 0
    for index, (timestamp, url, kind) in enumerate(batch, 1):
        record = assets.get((timestamp, url), {"timestamp": timestamp, "url": url,
                                                 "kind": kind, "attempts": []})
        record["attempts"] = record.get("attempts", [])
        replay = f"https://web.archive.org/web/{timestamp}id_/{url}"
        try:
            response = session.get(replay, timeout=timeout)
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
        except Exception as exc:
            record.update(status="failed", last_error=f"{type(exc).__name__}: {exc}")
            record["attempts"].append({"attempt": len(record["attempts"]) + 1,
                                       "error": record["last_error"]})
            failures += 1
        assets[(timestamp, url)] = record
        if index % 25 == 0 or index == len(batch):
            manifest["assets"] = list(assets.values())
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        if delay and index < len(batch):
            time.sleep(delay)
    manifest["assets"] = list(assets.values())
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {"attempted": len(batch), "recovered": recovered, "failed": failures,
            "remaining": max(0, len(pending) - len(batch)),
            "linked_asset_pairs": len(refs),
            "unique_payloads": len({a.get("sha256") for a in assets.values()
                                    if a.get("status") == "recovered" and a.get("sha256")})}


def _capture_page(source: bytes, timestamp: str, original: str, base: str,
                  asset_map: dict[str, str], query_routes: dict[str, str] | None = None) -> str:
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
    for node in list(soup.find_all(["iframe", "object", "embed", "video", "audio"])):
        note = soup.new_tag("p", attrs={"class": "twitter-platform-gap"})
        note.string = "Embedded media was not captured for offline playback."
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
            local_query = _twitter_query_url(absolute, original) if (host.endswith("twitter.com") or host.endswith("x.com")) else ""
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
                node["href"] = base.rstrip("/") + "/twitter-prometheusbrown/tweets/"
                node["class"] = list(node.get("class", [])) + ["twitter-pagination-index"]
                node["aria-label"] = (node.get_text(" ", strip=True) or "More posts") + " — browse recovered tweets"
                node.attrs.pop("target", None)
                node.attrs.pop("rel", None)
                local_pagination = True
            elif host.endswith("twitter.com") or host.endswith("x.com"):
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
    title = soup.title.get_text(" ", strip=True) if soup.title else "Prometheus Brown on Twitter"
    body_content = "".join(str(child) for child in soup.body.contents)
    local_stylesheets = "".join(str(link) for link in soup.head.select("link[rel~=stylesheet][href]")) if soup.head else ""
    safe_title = html.escape(title)
    route = f"{base}/twitter-prometheusbrown/" if base else "/twitter-prometheusbrown/"
    notice = (
        f'<header class="twitter-archive-bar"><a href="{route}">← Capture index</a>'
        f'<span>Internet Archive capture {html.escape(timestamp)}</span>'
        f'<a href="{html.escape(_archive_url(timestamp, original), quote=True)}">Original replay</a></header>'
    )
    css = """body{margin:0;color:#20242a;background:#f5f8fa;font:15px/1.5 Arial,sans-serif}
.twitter-archive-bar{position:sticky;top:0;z-index:2;display:flex;gap:1rem;justify-content:space-between;align-items:center;padding:.8rem 1.2rem;background:#fff;border-bottom:1px solid #d5dce2}
.twitter-archive-bar a{color:#25608a}.twitter-capture-title{max-width:1100px;margin:1.5rem auto .6rem;padding:0 1rem;font-size:1.15rem}
.twitter-capture-note{max-width:1100px;margin:0 auto 1rem;padding:0 1rem;color:#53616d;font-size:.9rem}
.twitter-original{max-width:1100px;margin:0 auto 3rem;padding:1rem;background:white;overflow-wrap:anywhere}
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
        + f'<main class="twitter-original">{body_content}</main></body></html>'
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


def build_twitter_archive(root: Path, output: Path, base: str = "") -> dict:
    root = Path(root)
    output = Path(output)
    manifest_path = root / "recovery/twitter-prometheusbrown/manifest.json"
    if not manifest_path.exists():
        destination = output / "twitter-prometheusbrown" / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        prefix = base.rstrip("/")
        destination.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Prometheus Brown on Twitter — Blue Scholars restoration</title>'
            '<style>body{max-width:850px;margin:4rem auto;padding:0 1.5rem;font:18px/1.6 system-ui,sans-serif;color:#20242a}a{color:#285c83}</style>'
            '</head><body><p><a href="' + prefix + '/">← Blue Scholars archive</a></p>'
            '<h1>Prometheus Brown on Twitter</h1><p>No archived profile captures have been indexed in this build.</p></body></html>',
            encoding="utf-8")
        return {"status": "not_indexed", "captures": 0, "recovered_capture_pages": 0}
    manifest = json.loads(manifest_path.read_text())
    capture_rows = manifest.get("captures", [])
    raw_root = manifest_path.parent
    output_root = output / "twitter-prometheusbrown"
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
        local_url = base_prefix + "/twitter-prometheusbrown/assets/" + filename
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
        tweet_rows[timestamp] = _tweet_records(source, item)
        parsed = BeautifulSoup(source, "html.parser")
        next_link = parsed.select_one("a#more, a[rel~=next]")
        if next_link and next_link.get("href"):
            query = _twitter_query_url(str(next_link["href"]), str(item.get("original", "")))
            if query:
                gap={"capture": timestamp, "url": query,
                     "original_url": urljoin(str(item.get("original", "")), str(next_link["href"]))}
                pagination_gaps.append(gap)
                query_routes[query] = f"/twitter-prometheusbrown/tweets/?capture={timestamp}"
    # A query pagination link has no page-specific replay in this inventory.
    # Don't silently send users to a different profile snapshot.
    for item in capture_rows:
        timestamp = str(item.get("timestamp", ""))
        original = str(item.get("original", "https://twitter.com/prometheusbrown"))
        capture = raw_root / str(item.get("fetch", {}).get("path", ""))
        valid = timestamp.isdigit() and capture.is_file() and item.get("fetch", {}).get("status") == "recovered"
        route = f"/twitter-prometheusbrown/captures/{timestamp}/"
        if valid:
            page_assets = {url: href for (when, url), href in asset_map.items() if when == timestamp}
            page = _capture_page(capture.read_bytes(), timestamp, original, base, page_assets, query_routes)
            destination = output_root / "captures" / timestamp / "index.html"
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
    # Retain page-two targets separately so readers can open the archive replay
    # when it exists even though this project does not have its page bytes.
    unique_pagination_gaps = list({(item["capture"], item["url"]): item for item in pagination_gaps}.values())
    tweet_index_route = base_prefix + "/twitter-prometheusbrown/tweets/"
    index_path = output_root / "tweets" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tweets = []
    for timestamp, records in tweet_rows.items():
        for record in records:
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
                                    "https://twitter.com/prometheusbrown")
            local_link = base_prefix + f"/twitter-prometheusbrown/captures/{record['capture']}/#status-" + (urlsplit(urljoin(capture_original, permalink)).path.rsplit("/", 1)[-1])
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
    search_script = output_root / "tweets" / "search.js"
    search_script.write_text('''const params=new URLSearchParams(location.search);const capture=params.get("capture");const note=document.getElementById("tweet-pagination-note");if(capture&&note){note.hidden=false;note.textContent="The exact page-two capture was not found in the archive index. Showing posts preserved in the parent capture ("+capture+").";}function filterTweets(){const q=document.getElementById("tweet-search").value.toLowerCase();for(const n of document.querySelectorAll(".tweet-index-item")){n.hidden=(capture&&n.dataset.capture!==capture)||!n.textContent.toLowerCase().includes(q)}}document.getElementById("tweet-search").addEventListener("input",filterTweets);filterTweets();
'''.replace("\n+", "\n"), encoding="utf-8")
    tweet_page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Recovered tweets — Prometheus Brown</title><style>'
        'body{max-width:900px;margin:3rem auto;padding:0 1.2rem;font:16px/1.55 system-ui,sans-serif;color:#20242a}a{color:#24567d}h1{font-size:clamp(2rem,6vw,4rem);line-height:1}.tweet-search{box-sizing:border-box;width:100%;padding:.8rem;border:1px solid #aab5bf;border-radius:5px;font:inherit}.tweet-index-item{padding:1rem 0;border-bottom:1px solid #dde2e6}.tweet-index-meta{font-size:.85rem;color:#5c6872}.gap{padding:1rem;background:#f2f5f7}@media(max-width:600px){body{margin:1.5rem auto}}</style></head><body>'
        '<p><a href="' + base_prefix + '/twitter-prometheusbrown/">← Twitter archive</a></p><h1>Recovered tweets</h1>'
        '<p>' + str(len(tweets)) + ' post entries extracted from locally saved profile captures. Duplicate posts can appear when snapshots overlap.</p>'
        '<label for="tweet-search">Search post text</label><input id="tweet-search" class="tweet-search" type="search" autocomplete="off"><p id="tweet-pagination-note" class="gap" hidden></p>'
        '<h2>Unrecovered pagination targets</h2><ul class="gap">' + (gaps_html or '<li>No observed pagination targets.</li>') + '</ul>'
        + ''.join(tweet_html) + '<script src="' + base_prefix + '/twitter-prometheusbrown/tweets/search.js" defer></script>'
        '</body></html>')
    index_path.write_text(tweet_page, encoding="utf-8")
    tweet_json = output_root / "tweets" / "index.json"
    tweet_json.write_text(json.dumps({"posts": tweets, "pagination_gaps": unique_pagination_gaps}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    home = output_root / "index.html"
    profile_url = html.escape(str(manifest.get("profile", "https://twitter.com/prometheusbrown")), quote=True)
    body = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Prometheus Brown on Twitter — Blue Scholars restoration</title>'
        '<style>body{max-width:1100px;margin:4rem auto;padding:0 1.5rem;color:#20242a;font:18px/1.6 system-ui,sans-serif}h1{font-size:clamp(2.2rem,6vw,4.5rem);line-height:1.05}.note{max-width:760px;color:#53616d}table{width:100%;border-collapse:collapse;margin-top:2rem;font-size:15px}th,td{padding:.8rem .6rem;text-align:left;border-bottom:1px solid #d8dfe5;overflow-wrap:anywhere}a{color:#285c83}.digest{font:12px ui-monospace,monospace}@media(max-width:620px){body{margin:2rem auto;padding:0 1rem}table{font-size:13px}th,td{padding:.55rem .35rem}}</style></head><body>',
        '<p><a href="' + base_prefix + '/">← Blue Scholars archive</a></p>',
        '<p class="archive-eyebrow">PROMETHEUS BROWN / TWITTER ARCHIVE</p>',
        '<h1>Prometheus Brown on Twitter</h1>',
        '<p>This separate archive contains dated Internet Archive captures of <a href="' + profile_url + '">twitter.com/prometheusbrown</a>. Each recovered page is preserved as its own snapshot.</p>',
        '<p><a href="' + tweet_index_route + '">Search ' + str(len(tweets)) + ' recovered tweet entries</a></p>',
        '<p class="note">The 2024 capture belongs to a later account takeover and is marked separately. Some Twitter snapshots only contain a JavaScript-required message. Captured scripts and interactive controls are disabled; unrecovered images are labeled on each page.</p>',
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
