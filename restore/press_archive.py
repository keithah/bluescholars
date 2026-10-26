"""Build a browseable, provenance-preserving view of recovered press material."""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .archive import validate_payload
from .render import render_html, resource_aliases
from .urls import base_path, identity, route, historical_route_prefix, original_url, is_site


PRESS_ROOT = "/other-archives/press"


def _esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _date(timestamp: str) -> str:
    if len(timestamp) >= 14 and timestamp[:14].isdigit():
        return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]} UTC"
    return timestamp or "Date unavailable"


def _group_key(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, parts.query, ""))


def _slug(url: str) -> str:
    parts = urlsplit(url)
    source = (parts.hostname or "source") + "-" + parts.path + ("-" + parts.query if parts.query else "")
    stem = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")[:58].strip("-") or "source"
    return stem + "-" + hashlib.sha256(_group_key(url).encode()).hexdigest()[:10]


def _read_capture(root: Path, record: dict, kind: str, directory: str) -> bytes:
    if not record.get("cdx_sha1_verified"):
        raise ValueError(f"Unverified press capture cannot be rendered: {record.get('original_url', '')}")
    raw_path = record.get("raw_path", "")
    path = (root / raw_path).resolve()
    allowed = (root / directory).resolve()
    if not raw_path or not path.is_relative_to(allowed):
        raise ValueError("Press archive raw path escapes its collection")
    body = path.read_bytes()
    actual_sha = hashlib.sha256(body).hexdigest()
    if actual_sha != record.get("sha256"):
        raise ValueError(f"Press archive hash mismatch: {raw_path}")
    if record.get("bytes") is not None and int(record["bytes"]) != len(body):
        raise ValueError(f"Press archive byte-count mismatch: {raw_path}")
    validate_payload(body, kind)
    return body


def _shell(title: str, body: str, base: str, stylesheet: str, allow_audio: bool = False) -> str:
    media_policy = "'self'" if allow_audio else "'none'"
    policy = ("default-src 'none'; img-src 'self'; style-src 'self' 'unsafe-inline'; "
              f"media-src {media_policy}; base-uri 'none'; form-action 'none'")
    style = """.press-wrap{max-width:1120px;margin:0 auto;padding:2rem 1.25rem 5rem;font:16px/1.6 system-ui,sans-serif;color:#252b31}
.press-kicker{font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;color:#5c6b79}
.press-notice{padding:1rem 1.2rem;border-left:4px solid #4d83a8;background:#eef4f7;margin:1.5rem 0}
.press-back{display:inline-block;margin:0 0 1rem;color:#245a7d}
.press-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}
.press-card{display:block;padding:1.15rem;border:1px solid #d8e0e5;border-radius:8px;background:#fff;color:inherit;text-decoration:none}
.press-card:hover,.press-card:focus{border-color:#477b9e;box-shadow:0 3px 14px #2342}
.press-meta{font-size:.9rem;color:#53616d;overflow-wrap:anywhere}
.press-table{width:100%;border-collapse:collapse}.press-table th,.press-table td{padding:.65rem;border-bottom:1px solid #dce2e6;text-align:left;vertical-align:top;overflow-wrap:anywhere}
.press-thumb{display:block;max-width:100%;max-height:220px;object-fit:contain;margin:.5rem auto}
.press-provenance{position:relative;z-index:1000;padding:.8rem 1rem;background:#edf4f7;border-bottom:2px solid #6489a3;color:#263b4a;font:14px/1.5 system-ui,sans-serif}
.press-provenance p{margin:.25rem 0}.press-provenance a{color:#174d73}
.press-article-images{margin-top:2rem;padding-top:1rem;border-top:1px solid #ccd6dc}
.press-small{font-size:.88rem}.press-audio{width:min(100%,720px);margin:1rem 0}
@media(max-width:600px){.press-table th:nth-child(3),.press-table td:nth-child(3){display:none}.press-wrap{padding:1.25rem .9rem 3rem}}"""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<meta http-equiv=\"Content-Security-Policy\" content=\"{_esc(policy)}\">"
            f"<title>{_esc(title)} — Blue Scholars archive</title>"
            f"<link rel=\"stylesheet\" href=\"{_esc(stylesheet)}\"><style>{style}</style></head>"
            f"<body><main class=\"press-wrap\"><p class=\"press-kicker\">Blue Scholars / source-linked press archive</p>"
            f"{body}</main></body></html>")


def _write(output: Path, route: str, text: str) -> None:
    destination = output / route.lstrip("/") / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _source_page_title(body: bytes, fallback_url: str) -> str:
    soup = BeautifulSoup(body, "html.parser")
    title = soup.find("meta", property="og:title")
    if title and title.get("content", "").strip():
        return " ".join(title["content"].split())
    heading = soup.find(["h1", "title"])
    if heading and heading.get_text(" ", strip=True):
        return " ".join(heading.get_text(" ", strip=True).split())
    path = urlsplit(fallback_url).path.strip("/").split("/")
    return " ".join(re.sub(r"[-_]+", " ", part) for part in path[-1:] if part) or (urlsplit(fallback_url).hostname or "Recovered press page")


def _link(base: str, route: str, label: str, css: str = "") -> str:
    return f'<a href="{_esc(base + route)}"' + (f' class="{_esc(css)}"' if css else "") + f">{_esc(label)}</a>"


def _load_media_manifests(root: Path) -> list[dict]:
    directory = root / "recovery/other-archives/press-media"
    records = []
    for path in (directory / "manifest.json", directory / "thefindmag-loyalty.json"):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for capture in data.get("captures", {}).values():
            item = dict(capture)
            item["source_page_url"] = item.get("source_page_url") or data.get("source_page", "")
            item["source_media_url"] = item.get("source_media_url") or data.get("source_media_url", "")
            item["archive"] = data.get("archive", "Internet Archive Wayback")
            records.append(item)
    return records


def build_press_archive(root: Path, output: Path, base: str, stylesheet: str) -> dict:
    """Render verified press captures, all dated media records, and explicit gaps."""
    root = Path(root).resolve()
    output = Path(output).resolve()
    base = base_path(base)
    manifest_path = root / "recovery/other-archives/press-articles/manifest.json"
    if not manifest_path.exists():
        return {"status": "not_available", "source_pages": 0, "page_capture_records": 0,
                "image_capture_records": 0, "image_payloads": 0, "audio_capture_records": 0,
                "audio_payloads": 0}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_entries = manifest.get("sources", {})
    page_records = list(manifest.get("page_captures", {}).values())
    image_records = list(manifest.get("image_captures", {}).values())

    groups: dict[str, dict] = {}
    for source in source_entries.values():
        url = source.get("source_url", "")
        if not url:
            continue
        key = _group_key(url)
        group = groups.setdefault(key, {"key": key, "url": url, "sources": [], "captures": [], "cdx_rows": []})
        group["sources"].append(source)
        group["cdx_rows"].extend(source.get("cdx_rows", []))

    validated_pages = []
    for record in page_records:
        url = record.get("source_page_url") or record.get("original_url", "")
        if not url:
            continue
        group = groups.setdefault(_group_key(url), {"key": _group_key(url), "url": url, "sources": [], "captures": [], "cdx_rows": []})
        body = _read_capture(root, record, "html", "recovery/other-archives/press-articles/pages")
        capture = dict(record)
        capture["body"] = body
        capture["title"] = _source_page_title(body, url)
        capture["route"] = f"{PRESS_ROOT}/captures/{_slug(url)}/{record['timestamp']}-{record['sha256'][:12]}-{hashlib.sha256(record.get('original_url', url).encode()).hexdigest()[:6]}"
        group["captures"].append(capture)
        validated_pages.append(capture)

    for group in groups.values():
        group["slug"] = _slug(group["url"])
        group["route"] = f"{PRESS_ROOT}/articles/{group['slug']}"
        group["captures"].sort(key=lambda item: (item.get("timestamp", ""), item.get("sha256", "")))
        group["cdx_rows"].sort(key=lambda row: (str(row[0]), str(row[1])))
        group["title"] = (group["captures"][-1]["title"] if group["captures"] else
                          " ".join(re.sub(r"[-_]+", " ", part) for part in urlsplit(group["url"]).path.strip("/").split("/")[-1:]) or
                          (urlsplit(group["url"]).hostname or "Indexed press page"))

    group_by_url = {_group_key(url): group for group in groups.values()
                    for url in [group["url"], *[s.get("source_url", "") for s in group["sources"]],
                                *[c.get("original_url", "") for c in group["captures"]]] if url}
    page_resources = {}
    for url, group in group_by_url.items():
        page_resources[url] = {"kind": "html", "local_path": group["route"] + "/index.html"}
        for source in group["sources"]:
            original = source.get("source_url", "")
            if original:
                page_resources[original] = {"kind": "html", "local_path": group["route"] + "/index.html"}
        for capture in group["captures"]:
            for original in (capture.get("original_url", ""), capture.get("source_page_url", "")):
                if original:
                    page_resources[original] = {"kind": "html", "local_path": group["route"] + "/index.html"}
    # Cross-site articles often link back to the band's own blog or navigation.
    # Resolve those URLs to this restoration's dated edition routes so an
    # offline press capture never strands the reader on an unhosted path.
    for group in groups.values():
        for source in group["sources"]:
            source_url = source.get("source_url", "")
            for row in source.get("cdx_rows", []):
                if len(row) < 2:
                    continue
                original = str(row[1])
                if not original.startswith(("http://bluescholars.com", "https://bluescholars.com",
                                            "http://www.bluescholars.com", "https://www.bluescholars.com")):
                    continue
                try:
                    prefix = historical_route_prefix(original, "/2013", str(row[0]))
                    local_route = route(original)
                except ValueError:
                    continue
                page_resources[original] = {"kind": "html", "local_path": f"{prefix}{local_route}/index.html"}
    image_by_url: dict[str, list[dict]] = defaultdict(list)
    images_by_hash: dict[str, dict] = {}
    for record in image_records:
        source_url = record.get("source_image_url") or record.get("original_url", "")
        if not source_url:
            continue
        body = _read_capture(root, record, "image", "recovery/other-archives/press-articles/images")
        sha = record["sha256"]
        suffix = Path(record.get("raw_path", "image.jpg")).suffix.lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"):
            suffix = ".img"
        asset_route = f"{PRESS_ROOT}/assets/{sha}{suffix}"
        asset_path = output / asset_route.lstrip("/")
        if not asset_path.exists():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_bytes(body)
        item = images_by_hash.setdefault(sha, {"sha256": sha, "route": f"{PRESS_ROOT}/images/{sha[:20]}",
                                               "asset_route": asset_route, "records": [], "body": body})
        item["records"].append(record)
        image_by_url[identity(source_url)].append({**record, "asset_route": asset_route})
    for variants in image_by_url.values():
        variants.sort(key=lambda item: item.get("timestamp", ""))

    image_url_candidates = manifest.get("image_urls", {})
    candidate_rows = []
    for raw_key, item in image_url_candidates.items():
        url = item.get("source_image_url", raw_key)
        if not url:
            continue
        candidate_rows.append({"url": url, "source_pages": item.get("source_pages", []),
                               "cdx_rows": item.get("cdx_rows", []),
                               "route": f"{PRESS_ROOT}/image-candidates/{hashlib.sha256(url.encode()).hexdigest()[:20]}"})
    candidate_rows.sort(key=lambda item: item["url"].lower())

    def media_for_capture(record: dict) -> dict:
        resources = dict(page_resources)
        timestamp = record.get("timestamp", "")
        for url, variants in image_by_url.items():
            earlier = [item for item in variants if item.get("timestamp", "") <= timestamp]
            selected = earlier[-1] if earlier else variants[0]
            resources[url] = {"kind": "image", "local_path": selected["asset_route"]}
        return resources

    # Add a visible capture date and provenance banner after the archived markup is sanitized.
    page_to_group = {id(capture): group for group in groups.values() for capture in group["captures"]}
    for capture in validated_pages:
        source_url = capture.get("original_url") or capture.get("source_page_url", "")
        resources = media_for_capture(capture)
        rendered, _issues = render_html(capture["body"].decode("utf-8", errors="replace"), source_url,
                                        resources, base, aliases=resource_aliases(resources),
                                        ui_stylesheet=stylesheet,
                                        ui_script=base + "/assets/legacy.js")
        doc = BeautifulSoup(rendered, "html.parser")
        group = page_to_group[id(capture)]
        # Keep links back to the band's site inside the preserved edition
        # when a matching generated page exists; otherwise point to the local
        # recovery index instead of leaving a broken path on this host.
        for anchor in doc.select("a[href]"):
            href = anchor.get("href", "")
            href_parts = urlsplit(href)
            press_site_path = href_parts.path[len(base):] if base and href_parts.path.startswith(base + "/") else href_parts.path
            if (not href_parts.netloc and press_site_path.startswith("/blog/")):
                # A few captured 2011 press articles retained absolute-path
                # links to the band's earlier blog. The surviving local
                # collection is grouped under the 2013 edition.
                candidate = "/2013" + press_site_path
                if (output / candidate.lstrip("/") / "index.html").is_file():
                    anchor["href"] = base + candidate + ("/" if not candidate.endswith("/") else "")
                else:
                    anchor["href"] = base + "/archive-status/"
                continue
            target_url = original_url(href, source_url)
            if not target_url or not is_site(target_url):
                continue
            resource = page_resources.get(target_url)
            local_path = resource.get("local_path") if resource else None
            if not local_path:
                try:
                    local_path = historical_route_prefix(target_url, "/2013", capture.get("timestamp", "")) + route(target_url) + "/index.html"
                except ValueError:
                    local_path = None
            if local_path and (output / local_path.lstrip("/")).is_file():
                anchor["href"] = base + local_path.removesuffix("index.html")
            else:
                anchor["href"] = base + "/archive-status/"
        banner = doc.new_tag("aside", attrs={"class": "press-provenance", "aria-label": "Capture provenance"})
        banner.append(BeautifulSoup(
            f'<p><strong>Recovered press capture</strong> · {_esc(_date(capture.get("timestamp", "")))}</p>'
            f'<p>Original page: <a href="{_esc(capture.get("original_url", ""))}" rel="noopener noreferrer">{_esc(capture.get("original_url", ""))}</a></p>'
            f'<p>Archive memento: <a href="{_esc(capture.get("replay_url", ""))}" rel="noopener noreferrer">{_esc(capture.get("replay_url", ""))}</a> · CDX digest <code>{_esc(capture.get("cdx_digest", ""))}</code></p>'
            f'<p>Local source SHA-256 <code>{_esc(capture.get("sha256", ""))}</code> · {_esc(capture.get("bytes", 0))} bytes · '
            f'<a href="{_esc(base + group["route"] + "/")}">all captures of this page</a> · '
            f'<a href="{_esc(base + PRESS_ROOT + "/")}">press archive index</a></p>', "html.parser"))
        doc.body.insert(0, banner)
        destination = output / capture["route"].lstrip("/") / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(str(doc), encoding="utf-8")

    # Per-source pages show every recovered variant and every indexed CDX row, including gaps.
    for group in sorted(groups.values(), key=lambda item: ((urlsplit(item["url"]).hostname or "").lower(), item["title"].lower())):
        body = (f'<a class="press-back" href="{_esc(base + PRESS_ROOT + "/articles/")}">← All source pages</a>'
                f'<h1>{_esc(group["title"])}</h1><p class="press-meta">Publisher: {_esc(urlsplit(group["url"]).hostname)} · '
                f'{len(group["captures"])} recovered page captures · {len(group["cdx_rows"])} indexed CDX rows</p>'
                '<div class="press-notice">Third-party article and image rights have not been reviewed. Each capture is shown with its source date and archive provenance.</div>')
        body += '<h2>Dated page captures</h2>'
        if group["captures"]:
            body += '<ul>' + ''.join(
                f'<li>{_link(base, capture["route"] + "/", _date(capture.get("timestamp", "")))} — '
                f'{_esc(capture.get("cdx_mime", "text/html"))} · {capture.get("bytes", 0):,} bytes · '
                f'SHA-256 <code>{_esc(capture.get("sha256", ""))}</code></li>'
                for capture in group["captures"]) + '</ul>'
        else:
            body += '<p>No verified page body was recovered for this source URL. Its index history and failed attempts remain represented below.</p>'
        related_images = []
        for item in images_by_hash.values():
            if any(_group_key(src.get("page_url", "")) == group["key"] for rec in item["records"] for src in rec.get("source_pages", [])):
                related_images.append(item)
        if related_images:
            body += '<h2>Recovered images linked to this source</h2><div class="press-grid">' + ''.join(
                f'<a class="press-card" href="{_esc(base + image["route"] + "/")}">'
                f'<img class="press-thumb" loading="lazy" src="{_esc(base + image["asset_route"])}" alt="Recovered image">'
                f'<span>Image · {_esc(image["records"][0].get("source_article_title", ""))}</span></a>'
                for image in related_images) + '</div>'
        body += '<h2>Source URL variants</h2><ul>' + ''.join(
            f'<li><a href="{_esc(item.get("source_url", ""))}" rel="noopener noreferrer">{_esc(item.get("source_url", ""))}</a>'
            f' · {len(item.get("cdx_rows", []))} index rows'
            + (f' · {_esc(item.get("coverage_note", ""))}' if item.get("coverage_note") else "")
            + (f' · Query note: {_esc(item.get("query_error", ""))}' if item.get("query_error") else "") + '</li>'
            for item in group["sources"]) + '</ul>'
        if group["cdx_rows"]:
            body += '<details><summary>Full capture index history (' + str(len(group["cdx_rows"])) + ' rows)</summary>'
            body += '<table class="press-table"><thead><tr><th>Capture (UTC)</th><th>Status / type</th><th>Digest</th><th>Availability</th></tr></thead><tbody>'
            for row in group["cdx_rows"]:
                timestamp = str(row[0]) if len(row) > 0 else ""
                original = str(row[1]) if len(row) > 1 else group["url"]
                status = str(row[2]) if len(row) > 2 else ""
                mime = str(row[3]) if len(row) > 3 else ""
                digest = str(row[4]) if len(row) > 4 else ""
                capture = next((c for c in group["captures"] if c.get("timestamp") == timestamp and c.get("cdx_digest") == digest), None)
                available = _link(base, capture["route"] + "/", "Browse local capture") if capture else "Indexed; no verified local page body"
                body += f'<tr><td><a href="https://web.archive.org/web/{_esc(timestamp)}id_/{_esc(original)}" rel="noopener noreferrer">{_esc(_date(timestamp))}</a></td><td>{_esc(status)} · {_esc(mime)}</td><td><code>{_esc(digest)}</code></td><td>{available}</td></tr>'
            body += '</tbody></table></details>'
        group_html = _shell(group["title"], body, base, stylesheet)
        _write(output, group["route"], group_html)

    # Article directory, grouped by source host, with unacquired source rows kept visible.
    article_cards = []
    for group in sorted(groups.values(), key=lambda item: ((urlsplit(item["url"]).hostname or "").lower(), item["title"].lower())):
        article_cards.append(
            f'<a class="press-card" href="{_esc(base + group["route"] + "/")}"><strong>{_esc(group["title"])}</strong>'
            f'<span class="press-meta"><br>{_esc(urlsplit(group["url"]).hostname)} · {len(group["captures"])} recovered captures · {len(group["cdx_rows"])} indexed rows</span></a>')
    # Image detail pages share identical bytes but list every observed date, URL, and source-page link.
    for item in images_by_hash.values():
        item["records"].sort(key=lambda record: record.get("timestamp", ""))
        body_html = (f'<a class="press-back" href="{_esc(base + PRESS_ROOT + "/images/")}">← All image records</a>'
                     f'<h1>Recovered press image</h1><img class="press-thumb" src="{_esc(base + item["asset_route"])}" alt="Recovered press image">'
                     f'<p><a href="{_esc(base + item["asset_route"])}">Open full image</a> · SHA-256 <code>{_esc(item["sha256"])}</code></p>'
                     '<div class="press-notice">Third-party image rights are unreviewed; relevance and credits below reflect the source inventory.</div>'
                     '<table class="press-table"><thead><tr><th>Captured (UTC)</th><th>Source and credit</th><th>Archive and rights notes</th></tr></thead><tbody>')
        for record in item["records"]:
            pages = record.get("source_pages", [])
            page_links = []
            for source in pages:
                page_url = source.get("page_url", "") if isinstance(source, dict) else ""
                group = group_by_url.get(_group_key(page_url)) if page_url.startswith(("http://", "https://")) else None
                if group:
                    page_links.append(_link(base, group["route"] + "/", page_url))
                elif page_url.startswith(("http://", "https://")):
                    page_links.append(f'<a href="{_esc(page_url)}" rel="noopener noreferrer">{_esc(page_url)}</a>')
                else:
                    note = page_url or "Source-page URL not recorded"
                    page_links.append(f'<span>{_esc(note)}</span>')
            body_html += (f'<tr><td><a href="{_esc(record.get("replay_url", ""))}" rel="noopener noreferrer">{_esc(_date(record.get("timestamp", "")))}</a></td>'
                          f'<td>{_esc(record.get("source_article_title", ""))}<br>{"<br>".join(page_links)}<br>{_esc(record.get("photographer_credit", ""))}</td>'
                          f'<td>{_esc(record.get("relevance_status", ""))}<br>{_esc(record.get("relevance_note", record.get("review_note", "")))}<br>{_esc(record.get("rights_status", "rights status unrecorded"))}<br>CDX digest <code>{_esc(record.get("cdx_digest", ""))}</code></td></tr>')
        body_html += '</tbody></table>'
        _write(output, item["route"], _shell("Recovered press image", body_html, base, stylesheet))

    # Include every indexed image URL, including candidates with no verified bytes.
    candidate_cards = []
    for candidate in candidate_rows:
        captured = [record for record in image_records if identity(record.get("source_image_url") or record.get("original_url", "")) == identity(candidate["url"])]
        payload_hashes = {record.get("sha256") for record in captured}
        candidate["payload_routes"] = [images_by_hash[sha]["route"] for sha in payload_hashes if sha in images_by_hash]
        row_dates = sorted({str(row[0]) for row in candidate["cdx_rows"] if row and str(row[0]).isdigit()})
        page_links = []
        for source in candidate["source_pages"]:
            group = group_by_url.get(_group_key(source.get("page_url", "")))
            if group:
                page_links.append(_link(base, group["route"] + "/", source.get("page_url", "Source page")))
        candidate["group_route"] = f'{PRESS_ROOT}/image-candidates/{hashlib.sha256(candidate["url"].encode()).hexdigest()[:20]}'
        details = (f'<h1>Image source record</h1><p><a href="{_esc(candidate["url"])}" rel="noopener noreferrer">{_esc(candidate["url"])}</a></p>'
                   f'<p>{len(row_dates)} indexed capture dates · {len(captured)} verified local capture records · {len(payload_hashes)} unique payloads</p>'
                   '<div class="press-notice">An index row does not mean image bytes were recovered. Only verified local payloads are shown as images.</div>')
        details += '<h2>Verified image payloads</h2>'
        if payload_hashes:
            details += '<ul>' + ''.join(f'<li>{_link(base, images_by_hash[sha]["route"] + "/", "Browse recovered image " + sha[:12])}</li>' for sha in sorted(payload_hashes) if sha in images_by_hash) + '</ul>'
        else:
            details += '<p>No verified image body is available for this URL.</p>'
        if page_links:
            details += '<h2>Source pages</h2><ul><li>' + '</li><li>'.join(page_links) + '</li></ul>'
        if row_dates:
            details += '<h2>Indexed capture history</h2><table class="press-table"><thead><tr><th>Archive date</th><th>Type / status</th><th>Digest</th><th>Local bytes</th></tr></thead><tbody>'
            for row in candidate["cdx_rows"]:
                timestamp = str(row[0]) if len(row) > 0 else ""
                original = str(row[1]) if len(row) > 1 else candidate["url"]
                status = str(row[2]) if len(row) > 2 else ""
                mime = str(row[3]) if len(row) > 3 else ""
                digest = str(row[4]) if len(row) > 4 else ""
                record = next((record for record in captured
                               if record.get("timestamp") == timestamp and record.get("cdx_digest") == digest), None)
                local = (_link(base, images_by_hash[record["sha256"]]["route"] + "/", "Browse local image")
                         if record and record.get("sha256") in images_by_hash
                         else "Indexed; no verified local image body")
                replay = f'https://web.archive.org/web/{_esc(timestamp)}id_/{_esc(original)}'
                details += (f'<tr><td><a href="{replay}" rel="noopener noreferrer">{_esc(_date(timestamp))}</a></td>'
                            f'<td>{_esc(status)} · {_esc(mime)}</td><td><code>{_esc(digest)}</code></td><td>{local}</td></tr>')
            details += '</tbody></table>'
        _write(output, candidate["group_route"], _shell("Press image source record", details, base, stylesheet))
        candidate_cards.append(f'<a class="press-card" href="{_esc(base + candidate["group_route"] + "/")}"><strong>{_esc(candidate["url"])}</strong>'
                               f'<span class="press-meta"><br>{len(row_dates)} indexed dates · {len(captured)} local captures · '
                               f'{len(payload_hashes)} unique payloads</span></a>')

    image_cards = []
    for item in images_by_hash.values():
        record = item["records"][0]
        credit = record.get("photographer_credit", "Credit not recorded")
        rights = record.get("rights_status", "Rights status unrecorded")
        image_cards.append(f'<a class="press-card" href="{_esc(base + item["route"] + "/")}">'
                           f'<img class="press-thumb" loading="lazy" src="{_esc(base + item["asset_route"])}" alt="{_esc(record.get("source_article_title", "Recovered press image"))}">'
                           f'<strong>{_esc(record.get("source_article_title", "Recovered press image"))}</strong>'
                           f'<span class="press-meta"><br>{len(item["records"])} capture records · {_esc(credit)}<br>{_esc(rights)}</span></a>')
    image_html = ('<a class="press-back" href="' + _esc(base + PRESS_ROOT + '/') + '">← Press archive</a>'
                  f'<h1>Images</h1><p>{len(image_records)} dated capture records share {len(images_by_hash)} verified local image payloads. All indexed image URLs, including unrecovered candidates, are listed below.</p>'
                  '<h2>Verified images</h2><div class="press-grid">' + ''.join(image_cards) + '</div>'
                  '<h2>Image URL history and gaps</h2><div class="press-grid">' + ''.join(candidate_cards) + '</div>')
    _write(output, PRESS_ROOT + "/images", _shell("Recovered press images", image_html, base, stylesheet))

    # Audio is served only from local, hash-verified files. The page CSP permits same-origin playback only.
    audio_records = _load_media_manifests(root)
    audio_by_hash: dict[str, dict] = {}
    for record in audio_records:
        body = _read_capture(root, record, "media", "recovery/other-archives/press-media/media")
        sha = record["sha256"]
        suffix = Path(record.get("raw_path", "track.mp3")).suffix.lower() or ".mp3"
        asset_route = f"{PRESS_ROOT}/assets/{sha}{suffix}"
        asset_path = output / asset_route.lstrip("/")
        if not asset_path.exists():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_bytes(body)
        item = audio_by_hash.setdefault(sha, {"sha256": sha, "route": f"{PRESS_ROOT}/audio/{sha[:20]}",
                                             "asset_route": asset_route, "records": []})
        item["records"].append(record)
    audio_cards = []
    for item in audio_by_hash.values():
        item["records"].sort(key=lambda record: record.get("timestamp", ""))
        record = item["records"][0]
        source_page = record.get("source_page_url", "")
        source_group = group_by_url.get(_group_key(source_page)) if source_page else None
        page_link = (_link(base, source_group["route"] + "/", source_page) if source_group else
                     f'<a href="{_esc(source_page)}" rel="noopener noreferrer">{_esc(source_page)}</a>') if source_page else "Source page unavailable"
        body_html = (f'<a class="press-back" href="{_esc(base + PRESS_ROOT + "/audio/")}">← All audio records</a>'
                     f'<h1>Recovered audio</h1><p>Source page: {page_link}</p><p>Source media URL: <a href="{_esc(record.get("source_media_url", ""))}" rel="noopener noreferrer">{_esc(record.get("source_media_url", ""))}</a></p>'
                     f'<audio class="press-audio" controls preload="none" src="{_esc(base + item["asset_route"])}">Your browser does not support local audio playback.</audio>'
                     f'<p><a href="{_esc(base + item["asset_route"])}">Download recovered audio</a> · SHA-256 <code>{_esc(item["sha256"])}</code></p>'
                     '<div class="press-notice">Third-party recording. Redistribution rights are unreviewed; this recovery record does not establish a license.</div>'
                     '<table class="press-table"><thead><tr><th>Capture (UTC)</th><th>Archive record</th><th>Rights</th></tr></thead><tbody>')
        for capture in item["records"]:
            body_html += (f'<tr><td><a href="{_esc(capture.get("replay_url", ""))}" rel="noopener noreferrer">{_esc(_date(capture.get("timestamp", "")))}</a></td>'
                          f'<td>{_esc(capture.get("archive", "Internet Archive Wayback"))} · CDX digest <code>{_esc(capture.get("cdx_digest", ""))}</code> · {capture.get("bytes", 0):,} bytes</td>'
                          f'<td>{_esc(capture.get("rights_status", "Rights status unrecorded"))}</td></tr>')
        body_html += '</tbody></table>'
        audio_page = _shell("Recovered press audio", body_html, base, stylesheet, allow_audio=True)
        _write(output, item["route"], audio_page)
        audio_cards.append(f'<a class="press-card" href="{_esc(base + item["route"] + "/")}"><strong>{_esc(urlsplit(record.get("source_media_url", "")).path.rsplit("/", 1)[-1] or "Recovered audio")}</strong>'
                           f'<span class="press-meta"><br>{len(item["records"])} capture records · {_esc(_date(record.get("timestamp", "")))}<br>{_esc(record.get("rights_status", "rights unreviewed"))}</span></a>')
    for manifest_name in ("manifest.json", "thefindmag-loyalty.json"):
        source_path = root / "recovery/other-archives/press-media" / manifest_name
        if source_path.exists():
            destination = output / PRESS_ROOT.lstrip("/") / "data" / manifest_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
    audio_html = ('<a class="press-back" href="' + _esc(base + PRESS_ROOT + '/') + '">← Press archive</a>'
                  f'<h1>Audio</h1><p>{len(audio_records)} dated audio capture records across {len(audio_by_hash)} verified local recordings.</p>'
                  '<div class="press-notice">Audio playback uses local files. Rights remain unreviewed.</div>'
                  '<div class="press-grid">' + ''.join(audio_cards) + '</div>')
    if not audio_cards:
        audio_html += '<p>No verified press audio bytes are available in this checkpoint.</p>'
    audio_html += '<p><a href="' + _esc(base + PRESS_ROOT + '/data/manifest.json') + '">Download audio capture provenance (JSON)</a></p>'
    _write(output, PRESS_ROOT + "/audio", _shell("Recovered press audio", audio_html, base, stylesheet))

    article_html = _shell("Recovered press pages", '<a class="press-back" href="' + _esc(base + PRESS_ROOT + '/') + '">← Press archive</a>'
                          '<h1>Press pages by source</h1><p>Every recovered dated page body is available with its exact source and memento details. Indexed captures without a verified body remain marked as gaps.</p>'
                          '<div class="press-grid">' + ''.join(article_cards) + '</div>', base, stylesheet)
    # Re-write the article directory after image links and capture routes are finalized.
    _write(output, PRESS_ROOT + "/articles", article_html)

    index_body = (f'<a class="press-back" href="{_esc(base + "/")}">← Blue Scholars archive</a>'
                  '<h1>Recovered press archive</h1>'
                  '<h2>Browse recovered press coverage</h2>'
                  '<p>Browse the source-linked articles, every verified dated page body, press image histories, and recovered recordings.</p>'
                  '<div class="press-notice"><strong>Recovery preview:</strong> third-party article, image, and recording rights have not been reviewed. Each item retains its publisher URL, archive date, CDX digest, and local SHA-256. These pages are separate from the Blue Scholars site editions.</div>'
                  '<div class="press-grid">'
                  f'<a class="press-card" href="{_esc(base + PRESS_ROOT + "/articles/")}"><strong>Articles and interviews</strong><span class="press-meta"><br>{len(groups)} source URLs · {len(validated_pages)} dated page captures</span></a>'
                  f'<a class="press-card" href="{_esc(base + PRESS_ROOT + "/images/")}"><strong>Images</strong><span class="press-meta"><br>{len(image_records)} dated records · {len(images_by_hash)} verified payloads · {len(candidate_rows)} indexed image URL records</span></a>'
                  f'<a class="press-card" href="{_esc(base + PRESS_ROOT + "/audio/")}"><strong>Audio</strong><span class="press-meta"><br>{len(audio_records)} dated records · {len(audio_by_hash)} local recordings</span></a>'
                  '</div><h2>Sources</h2><p>Articles are organized by publisher, with all discovered CDX rows and unavailable capture gaps recorded on each source page.</p>'
                  '<p>Capture dates are archive timestamps in UTC. A later capture may contain a changed publisher page; captures remain separate rather than being merged.</p>')
    index_body += '<p><a href="' + _esc(base + PRESS_ROOT + '/data/manifest.json') + '">Download the audio provenance manifest (JSON)</a>'
    if (output / PRESS_ROOT.lstrip("/") / "data" / "thefindmag-loyalty.json").exists():
        index_body += ' · <a href="' + _esc(base + PRESS_ROOT + '/data/thefindmag-loyalty.json') + '">The Find Mag audio capture history (JSON)</a>'
    index_body += '</p>'
    _write(output, PRESS_ROOT, _shell("Recovered press archive", index_body, base, stylesheet))

    return {"status": "built", "source_pages": len(groups), "page_capture_records": len(validated_pages),
            "image_capture_records": len(image_records), "image_payloads": len(images_by_hash),
            "image_url_records": len(candidate_rows),
            "unrecovered_image_url_records": sum(not any(identity(record.get("source_image_url") or record.get("original_url", "")) == identity(candidate["url"]) for record in image_records) for candidate in candidate_rows),
            "audio_capture_records": len(audio_records), "audio_payloads": len(audio_by_hash)}
