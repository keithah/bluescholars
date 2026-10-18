"""Build locally browsable, date-preserving Blue Scholars MySpace snapshots."""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
import requests
from .archive import ArchiveClient, validate_payload
from .discover import discover_css
from .urls import capture_from


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def index_myspace_assets(root: Path, max_urls: int = 100, delay: float = 1.0, retry_errors: bool = False) -> dict:
    """Index exact MySpace/CDN asset histories, checkpointing every result."""
    root = Path(root)
    archive = root / "recovery/myspace-blue-scholars"
    acquisition = json.loads((archive / "index/acquisition.json").read_text())
    linked: dict[str, set[str]] = {}
    kinds: dict[str, str] = {}

    def add(url: str, stamp: str, kind: str) -> None:
        if not url.startswith(("http://", "https://")):
            return
        host = (urlsplit(url).hostname or "").lower()
        local_profile_image = host in {"myspace.com", "www.myspace.com"} and urlsplit(url).path.startswith("/common/images/")
        if local_profile_image or any(part in host for part in ("myspacecdn.com", "myspace-", "masslinemedia.com")):
            linked.setdefault(url, set()).add(stamp)
            if kind == "css" or url not in kinds:
                kinds[url] = kind

    for record in acquisition.get("records", []):
        if record.get("status") != "recovered":
            continue
        raw = (root / record["raw_path"]).read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        original = record.get("original", "http://myspace.com/bluescholars")
        stamp = record.get("timestamp", "")
        for link in soup.find_all("link", href=True):
            if any(str(rel).lower() == "stylesheet" for rel in link.get("rel", [])):
                add(urljoin(original, link["href"]), stamp, "css")
        for style in soup.find_all("style"):
            for url in discover_css(style.get_text(), original):
                add(url, stamp, "image")
        for node in soup.find_all(attrs={"style": True}):
            for url in discover_css("x{" + str(node["style"]) + "}", original):
                add(url, stamp, "image")
        for node in soup.find_all(["img", "source", "video", "audio", "object", "embed"]):
            for attr in ("src", "data", "poster"):
                value = node.get(attr)
                if not value:
                    continue
                url = urljoin(original, value)
                add(url, stamp, "image")
    _write(archive / "index/linked-assets.json", json.dumps({
        "unique_source_linked_media_urls": len(linked),
        "records": [{"url": url, "kind": kinds.get(url, "image"), "source_captures": sorted(dates)} for url, dates in sorted(linked.items())]
    }, indent=2) + "\n")
    path = archive / "index/cdx-assets.json"
    saved = json.loads(path.read_text()) if path.exists() else {"records": []}
    rows = {r["url"]: r for r in saved.get("records", [])}
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation; paced requests)"
    attempted = 0
    for url, dates in sorted(linked.items(), key=lambda item: (kinds.get(item[0], "image") != "css", item[0])):
        old = rows.get(url)
        if old and (old.get("captures") or not retry_errors):
            continue
        if attempted >= max_urls:
            break
        record = {"url": url, "kind": kinds.get(url, "image"), "source_pages": sorted(dates)}
        try:
            response = session.get("https://web.archive.org/cdx/search/cdx", params={
                "url": url, "output": "json", "filter": "statuscode:200",
                "fl": "timestamp,original,statuscode,mimetype,digest,length", "collapse": "digest"
            }, timeout=35)
            if response.status_code == 429:
                record["index_error"] = "Wayback CDX HTTP 429; queue paused; retry after cooldown"
            else:
                response.raise_for_status()
                data = response.json()
                record["captures"] = [dict(zip(data[0], row)) for row in data[1:] if len(row) == len(data[0])]
        except Exception as exc:
            record["index_error"] = f"{type(exc).__name__}: {exc}"
        rows[url] = record
        attempted += 1
        if attempted % 10 == 0 or record.get("index_error", "").startswith("Wayback CDX HTTP 429"):
            _write(path, json.dumps({"queried": len(rows), "inventory_total": len(linked), "records": [rows[k] for k in sorted(rows)]}, indent=2) + "\n")
        if record.get("index_error", "").startswith("Wayback CDX HTTP 429"):
            break
        time.sleep(max(delay, 0))
    result = {"inventory_total": len(linked), "indexed_urls": len(rows),
              "indexed_with_captures": sum(bool(r.get("captures")) for r in rows.values()),
              "index_errors": sum(bool(r.get("index_error")) for r in rows.values()), "attempted_this_run": attempted}
    _write(path, json.dumps({"queried": len(rows), "inventory_total": len(linked), "records": [rows[k] for k in sorted(rows)]}, indent=2) + "\n")
    return result


def recover_myspace_assets(root: Path, max_files: int = 100, delay: float = 0.7, retry_failed: bool = False) -> dict:
    """Fetch validated image payloads from indexed capture alternatives."""
    root = Path(root)
    archive = root / "recovery/myspace-blue-scholars"
    indexed = json.loads((archive / "index/cdx-assets.json").read_text())
    path = archive / "index/assets.json"
    saved = json.loads(path.read_text()) if path.exists() else {"assets": []}
    records = {r["url"]: r for r in saved.get("assets", [])}
    client = ArchiveClient(delay=delay, timeout=40, retries=3)
    attempted = 0
    queue = sorted(indexed.get("records", []), key=lambda item: (item.get("kind", "image") != "css", item["url"]))
    for item in queue:
        captures = item.get("captures", [])
        if not captures:
            continue
        old = records.get(item["url"])
        if old and old.get("status") == "recovered" and (root / old["raw_path"]).is_file():
            continue
        if old and not retry_failed:
            continue
        if attempted >= max_files:
            break
        dates = item.get("source_pages", [])
        capture = min(captures, key=lambda c: (min((abs(int(c["timestamp"][:8])-int(d[:8])) for d in dates), default=99999999), -int(c["timestamp"])))
        kind = item.get("kind", "image")
        record = {"url": item["url"], "kind": kind, "source_pages": dates, "requested_capture": capture["timestamp"], "capture": capture}
        try:
            response = client.get(f"https://web.archive.org/web/{capture['timestamp']}id_/{capture['original']}")
            validate_payload(response.body, kind)
            digest = hashlib.sha256(response.body).hexdigest()
            suffix = ".css" if kind == "css" else ".jpg" if response.body.startswith(b"\xff\xd8") else ".png" if response.body.startswith(b"\x89PNG") else ".gif" if response.body.startswith((b"GIF87a", b"GIF89a")) else ".webp"
            name = digest + suffix
            raw_path = archive / "assets" / name
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            if not raw_path.exists(): raw_path.write_bytes(response.body)
            record.update(status="recovered", actual_capture=capture_from(response.url), raw_path=str(raw_path.relative_to(root)),
                          local_path="/myspace/assets/" + name, sha256=digest, bytes=len(response.body),
                          content_type=response.headers.get("Content-Type", ""))
        except Exception as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        records[item["url"]] = record
        attempted += 1
        if attempted % 10 == 0:
            _write(path, json.dumps({"attempted": len(records), "assets": [records[k] for k in sorted(records)]}, indent=2) + "\n")
    result = {"attempted_this_run": attempted, "assets": len(records),
              "recovered": sum(r.get("status") == "recovered" for r in records.values()),
              "failed": sum(r.get("status") != "recovered" for r in records.values())}
    _write(path, json.dumps({"attempted": len(records), "assets": [records[k] for k in sorted(records)]}, indent=2) + "\n")
    return result


def _sanitize(raw: str, stamp: str, assets: dict[str, str], base: str, source_url: str = "") -> str:
    soup = BeautifulSoup(raw, "html.parser")
    if soup.html is None:
        soup = BeautifulSoup("<!doctype html><html><head></head><body></body></html>", "html.parser")
    if soup.head is None:
        soup.html.insert(0, soup.new_tag("head"))
    if soup.body is None:
        soup.html.append(soup.new_tag("body"))
    if not soup.head.find("meta", attrs={"charset": True}):
        soup.head.insert(0, soup.new_tag("meta", charset="utf-8"))

    def rewrite_inline_css(css: str) -> str:
        def replace(match: re.Match[str]) -> str:
            value = match.group(2).strip()
            absolute = urljoin(source_url, value) if source_url else value
            local = assets.get(absolute) or assets.get(value)
            parsed = urlsplit(absolute)
            if not local and parsed.path.startswith("/common/images/defaultProfileCovers/") and (parsed.hostname or "").lower() in {"myspace.com", "www.myspace.com"}:
                for source, path in assets.items():
                    candidate = urlsplit(source)
                    if candidate.path == parsed.path and (candidate.hostname or "").lower() in {"myspace.com", "www.myspace.com"}:
                        local = path
                        break
            if local:
                return "url('" + base + local + "')"
            return "none"
        return re.sub(r"url\(\s*(['\"]?)(.*?)\1\s*\)", replace, css, flags=re.I)

    for tag in list(soup.find_all(["script", "iframe", "object", "embed", "video", "audio", "form", "base"])):
        if tag.name == "script" or tag.name == "base":
            tag.decompose()
        else:
            notice = soup.new_tag("p", attrs={"class": "media-gap"})
            notice.string = "Embedded MySpace media was not captured for offline playback."
            tag.replace_with(notice)
    for tag in list(soup.find_all("link")):
        # Some archived, malformed profile HTML nests void elements. Removing
        # a parent while iterating can leave descendants in this snapshot with
        # attrs=None, so skip nodes already detached by an earlier removal.
        if tag.attrs is None:
            continue
        rel = " ".join(tag.get("rel", []))
        href = tag.get("href", "")
        if "stylesheet" in rel.lower() and href in assets:
            tag["href"] = base + assets[href]
        elif "stylesheet" in rel.lower() or href.startswith(("http://", "https://", "//")):
            tag.decompose()
    for tag in soup.find_all("style"):
        if tag.attrs is None:
            continue
        css = tag.string or tag.get_text()
        tag.string = rewrite_inline_css(css)
    for tag in soup.find_all(True):
        if tag.attrs is None:
            continue
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                del tag.attrs[attr]
            elif attr.lower() == "style" and "url(" in str(tag.attrs[attr]).lower():
                tag.attrs[attr] = rewrite_inline_css(str(tag.attrs[attr]))
        if tag.name == "img":
            original = tag.get("src", "")
            localized = assets.get(original)
            if localized:
                tag["src"] = base + localized
            else:
                alt = tag.get("alt") or "unavailable image"
                replacement = soup.new_tag("span", attrs={"class": "image-gap", "role": "img"})
                replacement.string = "Archived source image is unavailable: " + alt
                tag.replace_with(replacement)
            tag.attrs.pop("srcset", None)
            tag.attrs.pop("loading", None)
        elif tag.name == "source":
            tag.decompose()
        for attr in ("src", "poster", "background"):
            value = tag.get(attr)
            if value and (value.startswith(("http://", "https://", "//")) or attr == "background"):
                tag.attrs.pop(attr, None)
    for tag in soup.find_all("a", href=True):
        value = tag["href"]
        scheme = urlsplit(value).scheme.lower()
        if scheme in {"javascript", "vbscript", "data"}:
            tag.attrs.pop("href", None)
        elif value.startswith("//"):
            tag["href"] = "https:" + value
        elif not scheme and not value.startswith("#") and source_url:
            tag["href"] = urljoin(source_url, value)
        elif value.startswith("http://") and "myspace.com" in (urlsplit(value).hostname or ""):
            tag["rel"] = ["noreferrer"]
    marker = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width,initial-scale=1"})
    soup.head.append(marker)
    style = soup.new_tag("style")
    style.string = """
      .preservation-bar{box-sizing:border-box;display:flex;justify-content:space-between;gap:1rem;padding:12px 18px;background:#14283c;color:#fff;font:14px/1.4 system-ui,sans-serif}
      .preservation-bar a{color:#d9edff}.preservation-bar strong{letter-spacing:.04em}
      .preservation-intro{box-sizing:border-box;max-width:1100px;margin:18px auto;padding:0 18px;color:#364657;font:14px/1.5 system-ui,sans-serif}
      .preservation-intro p{margin:.35em 0}.image-gap,.media-gap{display:inline-block;box-sizing:border-box;margin:4px;padding:10px;border:1px dashed #888;background:#f5f5f5;color:#555;font:12px/1.4 system-ui,sans-serif}
      @media(max-width:650px){.preservation-bar{font-size:12px;flex-wrap:wrap}.preservation-intro{font-size:12px}}
    """
    soup.head.append(style)
    bar = soup.new_tag("div", attrs={"class": "preservation-bar"})
    strong = soup.new_tag("strong"); strong.string = "BLUE SCHOLARS · MYSPACE ARCHIVE"; bar.append(strong)
    back = soup.new_tag("a", href=base + "/myspace/"); back.string = "All dated captures"; bar.append(back)
    info = soup.new_tag("div", attrs={"class": "preservation-intro"})
    notice = soup.new_tag("p"); notice.string = f"Captured {stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} · preserved source HTML, with available assets saved locally."; info.append(notice)
    gaps = soup.new_tag("p"); gaps.string = "Scripts, external automatic requests, and uncaptured player media are disabled. Gaps are identified in place."; info.append(gaps)
    soup.body.insert(0, info); soup.body.insert(0, bar)
    return "<!doctype html>\n" + str(soup)


def build_myspace_archive(root: Path, output: Path, base: str = "") -> dict:
    root, output = Path(root), Path(output)
    data_path = root / "recovery/myspace-blue-scholars/index/acquisition.json"
    records = json.loads(data_path.read_text()).get("records", []) if data_path.exists() else []
    assets_path = root / "recovery/myspace-blue-scholars/index/assets.json"
    asset_data = json.loads(assets_path.read_text()).get("assets", []) if assets_path.exists() else []
    assets = {}
    for asset in asset_data:
        if not asset.get("local_path") or not asset.get("raw_path") or not (root / asset["raw_path"]).is_file():
            continue
        assets[asset["url"]] = asset["local_path"]
        destination = output / asset["local_path"].lstrip("/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = root / asset["raw_path"]
        if asset.get("kind") == "css" or destination.suffix.lower() == ".css":
            css = source.read_text(encoding="utf-8", errors="replace")
            css = re.sub(r"@import\s+[^;]+;?", "", css, flags=re.I)
            css = re.sub(r"url\([^)]*\)", "none", css, flags=re.I)
            destination.write_text(css, encoding="utf-8")
        else:
            shutil.copyfile(source, destination)
    valid = [r for r in records if r.get("status") == "recovered" and r.get("raw_path") and (root / r["raw_path"]).is_file()]
    stamps = Counter(r.get("actual_capture") or r.get("timestamp", "unknown") for r in valid)
    rendered = []
    used_routes: set[str] = set()
    for record in valid:
        stamp = record.get("actual_capture") or record.get("timestamp", "unknown")
        source = root / record["raw_path"]
        raw = source.read_text(encoding="utf-8", errors="replace")
        digest = record.get("sha256", "")
        slug = stamp + ("-" + digest[:8] if stamps[stamp] > 1 and digest else "")
        route = f"/myspace/{stamp[:4]}/{slug}.html"
        if route in used_routes:
            suffix = 2
            while f"/myspace/{stamp[:4]}/{slug}-{suffix}.html" in used_routes:
                suffix += 1
            route = f"/myspace/{stamp[:4]}/{slug}-{suffix}.html"
        used_routes.add(route)
        _write(output / route.lstrip("/"), _sanitize(raw, stamp, assets, base, record.get("original", "")))
        title = BeautifulSoup(raw, "html.parser").title
        rendered.append({"timestamp": stamp, "route": route, "title": title.get_text(" ", strip=True) if title else "Blue Scholars MySpace profile", "source": record.get("source_url", ""), "sha256": record.get("sha256", "")})
    years = sorted({p["timestamp"][:4] for p in rendered})
    body = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Blue Scholars · MySpace archive</title><link rel='stylesheet' href='"+html.escape(base)+"/assets/archive-ui.css'></head><body><main class='archive-gap-page'>",
            "<p class='archive-eyebrow'>BLUE SCHOLARS / RELATED ARCHIVES</p><h1>MySpace profile captures</h1>",
            "<p class='archive-lead'>Individually preserved profile pages from Internet Archive captures, spanning 2007 through 2025. Each link opens a dated local snapshot.</p>",
            f"<p>{len(rendered)} validated page responses · {len(years)} capture years · {len(assets)} locally saved linked assets</p>"]
    gaps = [r for r in records if r.get("status") != "recovered"]
    for year in years:
        body.append(f"<h2>{html.escape(year)}</h2><ul>")
        body.extend(f"<li><a href='{base}{html.escape(p['route'], quote=True)}'>{html.escape(p['timestamp'])} · {html.escape(p['title'])}</a></li>" for p in rendered if p["timestamp"].startswith(year))
        body.append("</ul>")
    body.append("<h2>Capture gaps</h2>")
    if gaps:
        body.append("<ul>" + "".join(f"<li>{html.escape(str(r.get('timestamp')))}: {html.escape(str(r.get('error', 'response not recovered')))}</li>" for r in gaps) + "</ul>")
    else: body.append("<p>All indexed page responses were recovered.</p>")
    body.append("<p>Original raw response bytes, dates, hashes, and capture URLs are retained in the recovery inventory. Some profile images and embedded music may not have captures.</p></main></body></html>")
    _write(output / "myspace/index.html", "".join(body))
    result = {"status": "built", "profile": "https://myspace.com/bluescholars", "indexed_page_captures": len(records), "recovered_pages": len(valid), "failed_pages": len(gaps), "capture_years": years, "local_assets": len(assets), "pages": rendered}
    (output / "myspace/report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
