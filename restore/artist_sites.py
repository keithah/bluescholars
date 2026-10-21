"""Source-backed preservation for the separate Prometheus Brown and Sabzi sites.

These domains have their own Wayback histories and incompatible templates. They
are indexed and built as satellite editions instead of being folded into the
Blue Scholars domain's source catalog.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup
import requests

from .archive import ArchiveClient, parse_cdx, validate_payload
from .discover import discover_css
from .redact import redact_public_credentials
from .svg import sanitize_svg
from .urls import capture_from, kind_for

EDITIONS = {
    "prometheusbrown.com": [
        {"id": "2008", "label": "2008 blog", "capture": "20080706232724", "root": "http://prometheusbrown.com/"},
        {"id": "2009", "label": "2009 WordPress blog", "capture": "20091228010642", "root": "http://prometheusbrown.com:80/blog/"},
        {"id": "2010", "label": "2010 WordPress blog", "capture": "20100925222301", "root": "http://prometheusbrown.com:80/blog/"},
        {"id": "2013", "label": "2013 portfolio", "capture": "20130602191441", "lookahead_days": 365, "root": "http://prometheusbrown.com/"},
        {"id": "2016", "label": "2016 portfolio", "capture": "20161016112218", "root": "http://prometheusbrown.com/"},
        {"id": "2019", "label": "2019 Squarespace", "capture": "20191017201508", "root": "https://www.prometheusbrown.com/"},
        {"id": "2022", "label": "2022 Squarespace archive", "capture": "20220625044901", "root": "https://www.prometheusbrown.com/"},
    ],
    "sabzi.co": [
        {"id": "2013", "label": "2013 Squarespace", "capture": "20130704141640", "lookahead_days": 730, "root": "http://sabzi.co/"},
        {"id": "2016", "label": "2016 Squarespace", "capture": "20160306112646", "root": "http://sabzi.co/"},
        {"id": "2019", "label": "2019 Squarespace and blog", "capture": "20191023135247", "root": "http://sabzi.co/"},
        {"id": "2022", "label": "2022 latest archived homepage", "capture": "20220518171534", "root": "http://sabzi.co/"},
    ],
}

ALIASES = {
    "prometheusbrown.com": {"prometheusbrown.com", "www.prometheusbrown.com"},
    "sabzi.co": {"sabzi.co", "www.sabzi.co"},
}

SOURCE_INSPECTIONS = [
    {"url": "http://prometheusbrown.com:80/0.html", "timestamp": "20090901043719",
     "digest": "Z66XHTT6SF6M2R763IR7U25MIB57L55J", "title": "Cialis Get Viagra", "decision": "excluded_spam_injection",
     "source": "https://web.archive.org/web/20090901043719/http://prometheusbrown.com:80/0.html"},
    {"url": "http://prometheusbrown.com:80/blog/", "timestamp": "20090205184511",
     "digest": "UJGRPY7B6O7CUE7STVIHKLYZSGOFPTYU", "title": "Prometheus Brown", "decision": "genuine_wordpress_blog_capture",
     "source": "https://web.archive.org/web/20090205184511/http://prometheusbrown.com:80/blog/"},
    {"url": "http://prometheusbrown.com:80/blog/", "timestamp": "20091228010642",
     "digest": "SUX4RETGZQ5YHOV5ZUYRX7B7MDI3FZHP", "title": "Prometheus Brown", "decision": "genuine_wordpress_blog_edition",
     "source": "https://web.archive.org/web/20091228010642/http://prometheusbrown.com:80/blog/"},
    {"url": "http://prometheusbrown.com:80/blog/", "timestamp": "20100925222301",
     "digest": "RNFWORZAALWO4OYI4YPBZTMMWK7PHAWU", "title": "Prometheus Brown", "decision": "genuine_wordpress_blog_edition",
     "source": "https://web.archive.org/web/20100925222301/http://prometheusbrown.com:80/blog/"},
    *[
        {"url": "http://prometheusbrown.com/", "timestamp": timestamp, "digest": digest,
         "title": title, "decision": "excluded_casino_spam",
         "source": f"https://web.archive.org/web/{timestamp}/http://prometheusbrown.com/"}
        for timestamp, digest, title in (
            ("20240703110247", "OPKXOIVVIS6CGVWRYKGGVXO5NZNMCBCD", "JAYA77 : Link Login Game Online Pt Game Gampang Jackpot"),
            ("20240703173210", "WQC3XFWLHGZOO7BN5W7LP277G2JMHT4U", "JAYA77 : Link Login Game Online Pt Game Gampang Jackpot"),
            ("20240707084257", "HG7PC6LCUACCLKTDF7FWCJO65IVKKITU", "JAYA77 : Link Login Game Online Pt Game Gampang Jackpot"),
            ("20240713083443", "EIMWEMN6IY6EJ6JNCA4WGBVESOVA4TIP", "JAYA77 : Link Login Game Online Pt Game Gampang Jackpot"),
            ("20240724121337", "WACUGPMXMIB3MVGU3ZQQLCFYTMXPK6VJ", "JAYA77 : Daftar Situs Resmi Game Slot Online Bocor Parah"),
            ("20240724121339", "GMV72YRD4GOLCQWMKN44GIFKJB2WSU2T", "JAYA77 : Daftar Situs Resmi Game Slot Online Bocor Parah"),
            ("20240724150348", "5K3E6IVYFP4HHNRL35SKIKECYUKR2F7P", "JAYA77 : Daftar Situs Resmi Game Slot Online Bocor Parah"),
            ("20240821063833", "CGIQZ2X2BD36GJP3HVSYYUT4AZRHSHDX", "JAYA77 : Daftar Situs Resmi Game Slot Online Bocor Parah"),
        )
    ],
]


def _canonical(value: str, base: str = "") -> str:
    try:
        value = urljoin(base, str(value or "").strip())
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return ""
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    netloc = host + ((":" + str(port)) if port and port not in (80, 443) else "")
    return parts._replace(scheme="http", netloc=netloc, fragment="").geturl()


def _site_host(host: str, domain: str) -> bool:
    return host.lower() in ALIASES[domain]


def _is_dynamic_avatar(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host in {"gravatar.com", "www.gravatar.com", "secure.gravatar.com"} and "/avatar/" in urlsplit(url).path


def _relative_path(url: str) -> str:
    """Return a stable, traversal-safe output path for a source URL."""
    parts = urlsplit(url)
    raw_path = unquote(parts.path or "/")
    segments = [segment for segment in raw_path.split("/") if segment]
    if any(segment in (".", "..") or "\\" in segment for segment in segments):
        raise ValueError("Unsafe source path")
    encoded = "/".join(quote(segment, safe="@:+,;=~!$&'()[]-._") for segment in segments)
    path = "/" + encoded
    if parts.query:
        query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
        tag = hashlib.sha256(query.encode("utf-8")).hexdigest()[:10]
        path = path.rstrip("/") + "/_q_" + tag
    if not path.endswith("/") and not PathLikeExtension.has_extension(path):
        path += "/"
    return path + ("" if path.endswith("/") else "")


class PathLikeExtension:
    @staticmethod
    def has_extension(path: str) -> bool:
        return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", path.rsplit("/", 1)[-1]))


def edition_route(domain: str, edition: str, url: str) -> str:
    """Map an archived URL into one independently browsable site edition."""
    if domain not in EDITIONS or edition not in {e["id"] for e in EDITIONS[domain]}:
        raise ValueError("Unknown artist-site edition")
    canonical = _canonical(url)
    if not canonical:
        raise ValueError("Invalid archived page URL")
    host = urlsplit(canonical).hostname or ""
    path = _relative_path(canonical)
    if not _site_host(host, domain):
        # Some archived pages contain linked hosted-media documents (e.g. old
        # Imeem embeds). Keep those captured documents local, but isolate them
        # by source host so they cannot collide with the artist site's routes.
        path = "/_external/" + quote(host, safe=".-") + path
    base = "/prometheusbrown" if domain == "prometheusbrown.com" else "/sabzi"
    route = f"{base}/{edition}{path}"
    if not PathLikeExtension.has_extension(path):
        route += "index.html"
    return route


def local_asset_path(domain: str, edition: str, url: str, suffix: str | None = None) -> str:
    """Create collision-resistant local names for assets, including query URLs."""
    if domain not in EDITIONS or edition not in {item["id"] for item in EDITIONS[domain]}:
        raise ValueError("Unknown artist-site edition")
    canonical = _canonical(url)
    if not canonical:
        raise ValueError("Invalid asset URL")
    parts = urlsplit(canonical)
    extension = suffix or (parts.path.rsplit(".", 1)[-1].lower() if "." in parts.path.rsplit("/", 1)[-1] else "bin")
    if not re.fullmatch(r"[a-z0-9]{1,8}", extension):
        extension = "bin"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    prefix = "/prometheusbrown" if domain == "prometheusbrown.com" else "/sabzi"
    return f"{prefix}/{edition}/assets/{digest}.{extension}"


def _local_target(value: str, base: str, mapping: dict[str, str]) -> str | None:
    canonical = _canonical(value, base)
    if not canonical:
        return None
    return mapping.get(canonical)


def sanitize_artist_html(source: str, source_url: str, mapping: dict[str, str], capture: str = "") -> tuple[str, list[str]]:
    """Localize saved dependencies and remove executable/platform behavior."""
    soup = BeautifulSoup(source, "html.parser")
    if soup.html is None:
        wrapper = BeautifulSoup("<!doctype html><html><head></head><body></body></html>", "html.parser")
        for child in list(soup.contents):
            wrapper.body.append(child.extract())
        soup = wrapper
    if soup.head is None:
        soup.html.insert(0, soup.new_tag("head"))
    if soup.body is None:
        soup.html.append(soup.new_tag("body"))
    if not soup.head.find("meta", attrs={"charset": True}):
        meta = soup.new_tag("meta", charset="utf-8")
        soup.head.insert(0, meta)
    if not soup.head.find("meta", attrs={"name": "viewport"}):
        meta = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1"})
        soup.head.append(meta)
    missing: list[str] = []
    for node in list(soup.find_all("script")):
        node.decompose()
    for node in list(soup.find_all("base")):
        node.decompose()
    for node in list(soup.find_all("meta", attrs={"http-equiv": re.compile("^refresh$", re.I)})):
        node.decompose()
    for node in list(soup.find_all(["iframe", "video", "audio", "object", "embed"])):
        value = node.get("src") or node.get("data") or ""
        canonical = _canonical(value, source_url) if value else ""
        if canonical:
            missing.append(canonical)
        note = soup.new_tag("p", attrs={"class": "archive-embed-gap"})
        note.string = "Archived embedded media is not available for offline playback."
        if canonical and capture.isdigit():
            link = soup.new_tag("a", href=_archive_url(capture, canonical))
            link.string = "Open its archived source"
            note.append(" "); note.append(link)
        node.replace_with(note)
    for node in list(soup.find_all("form")):
        note = soup.new_tag("p", attrs={"class": "archive-form-gap"})
        note.string = "Historical form disabled in this preservation copy."
        node.replace_with(note)
    for node in soup.find_all(True):
        if node.attrs is None:  # removed while cleaning an earlier dependency
            continue
        for attr in list(node.attrs):
            if attr.lower().startswith("on"):
                del node.attrs[attr]
        if node.name not in ("a", "area", "link"):
            node.attrs.pop("href", None)
        if node.name == "link" and "stylesheet" in node.get("rel", []):
            target = _local_target(node.get("href", ""), source_url, mapping)
            if target:
                node["href"] = target
            else:
                node.decompose()
                continue
        elif node.name == "link" and any(rel in node.get("rel", []) for rel in ("icon", "shortcut", "apple-touch-icon")):
            target = _local_target(node.get("href", ""), source_url, mapping)
            if target:
                node["href"] = target
            else:
                node.decompose()
                continue
        elif node.name == "link" and node.get("href") and any(
                rel in node.get("rel", []) for rel in ("preload", "prefetch", "preconnect", "dns-prefetch", "modulepreload")):
            node.decompose()
            continue
        elif node.name == "link":
            # Feeds, canonical/archive hints, pingbacks, and platform control
            # endpoints are not part of the offline visual document.
            node.decompose()
            continue
        elif node.name in ("img", "source", "video", "audio"):
            missing_image = ""
            for attr in ("src", "poster"):
                if node.get(attr):
                    target = _local_target(node[attr], source_url, mapping)
                    if target:
                        node[attr] = target
                    else:
                        unavailable = _canonical(node[attr], source_url)
                        missing.append(unavailable)
                        if node.name == "img" and attr == "src":
                            missing_image = unavailable
                        node.attrs.pop(attr, None)
            if missing_image:
                node["alt"] = "Archived image unavailable"
                node["title"] = "Archived image unavailable: " + missing_image
                node["aria-label"] = "Archived image unavailable"
                node["class"] = list(node.get("class", [])) + ["archive-source-gap-image"]
                node.attrs.pop("width", None)
                node.attrs.pop("height", None)
                node["style"] = (str(node.get("style", "")) +
                    ";display:inline-block;max-width:100%;width:auto;height:auto;padding:.35em;"
                    "border:1px dashed #888;background:#f5f5f2;color:#555;font:12px/1.4 sans-serif").lstrip(";")
                if capture.isdigit() and node.find_parent("a") is None:
                    link = soup.new_tag("a", href=_archive_url(capture, missing_image))
                    node.wrap(link)
            if node.get("srcset"):
                candidates = []
                for item in node["srcset"].split(","):
                    url = item.strip().split()[0] if item.strip() else ""
                    target = _local_target(url, source_url, mapping)
                    if target:
                        candidates.append(target + (" " + " ".join(item.split()[1:]) if len(item.split()) > 1 else ""))
                if candidates:
                    node["srcset"] = ", ".join(candidates)
                else:
                    node.attrs.pop("srcset", None)
        elif node.name in ("a", "area") and node.get("href"):
            value = str(node["href"]).strip()
            if value.startswith("#") or urlsplit(value).scheme.lower() in ("mailto", "tel"):
                pass
            else:
                candidate = _canonical(value, source_url)
                target = _local_target(value, source_url, mapping)
                if target:
                    fragment = urlsplit(urljoin(source_url, value)).fragment
                    node["href"] = target + ("#" + fragment if fragment else "")
                elif not candidate:
                    node.attrs.pop("href", None)
                elif urlsplit(candidate).hostname:
                    host = urlsplit(candidate).hostname or ""
                    if any(_site_host(host, domain) for domain in EDITIONS):
                        node["href"] = candidate
                    elif capture.isdigit():
                        node["href"] = _archive_url(capture, candidate)
                    else:
                        node.attrs.pop("href", None)
        if node.get("background"):
            target = _local_target(node["background"], source_url, mapping)
            if target:
                node["background"] = target
            else:
                node.attrs.pop("background", None)
        if node.name in ("audio", "video"):
            node.attrs.pop("autoplay", None)
        if node.get("style"):
            node["style"] = _rewrite_css(node["style"], source_url, mapping)
    for style in soup.find_all("style"):
        style.string = _rewrite_css(style.get_text(), source_url, mapping)
    return str(soup), sorted(set(x for x in missing if x))


def _rewrite_css(text: str, base: str, mapping: dict[str, str]) -> str:
    pattern = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)

    def replace(match):
        value = match.group(2).strip()
        if value.startswith(("data:", "#")):
            return match.group(0)
        target = _local_target(value, base, mapping)
        return "url(" + (target if target else "data:,") + ")"

    text = pattern.sub(replace, text)
    return re.sub(r"@import\s+(?:url\([^)]*\)|['\"][^'\"]*['\"])[^;]*;", "", text, flags=re.I)


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _index_url(url: str, session, delay: float = 0.2) -> list[dict]:
    if delay:
        time.sleep(delay)
    response = session.get(
        "https://web.archive.org/cdx/search/cdx",
        params={"url": url, "output": "json", "fl": "original,timestamp,statuscode,mimetype,digest,length",
                "filter": "statuscode:200", "showResumeKey": "true", "limit": "20000"},
        timeout=45,
    )
    if response.status_code != 200:
        raise OSError(f"Wayback CDX HTTP {response.status_code} for {url}")
    rows, resume = parse_cdx(response.text)
    if resume:
        raise ValueError(f"Wayback CDX result is paginated for {url}; resume key {resume!r} was not exhausted")
    return rows


def index_artist_sites(root: Path, delay: float = 0.2) -> dict:
    """Save complete CDX inventories for both artist domains and exact roots."""
    root = Path(root)
    path = root / "recovery/artist-sites/index.json"
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical research; paced requests)"
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "archives": {}, "errors": []}
    all_rows = {}
    for domain in EDITIONS:
        try:
            rows = _index_url(domain + "/*", session, delay)
            clean = []
            for row in rows:
                original = row.get("original", "")
                host = urlsplit(original).hostname or ""
                if not _site_host(host, domain) or not row.get("timestamp", "").isdigit():
                    continue
                clean.append(row)
            all_rows[domain] = clean
            report["archives"][domain] = {
                "index_url": "https://web.archive.org/cdx/search/cdx?url=" + domain + "/*",
                "rows": len(clean), "unique_urls": len({_canonical(row["original"]) for row in clean}),
                "captures_by_year": {}, "mime_types": {},
            }
            for row in clean:
                year = row["timestamp"][:4]
                report["archives"][domain]["captures_by_year"][year] = report["archives"][domain]["captures_by_year"].get(year, 0) + 1
                mime = row.get("mimetype", "")
                report["archives"][domain]["mime_types"][mime] = report["archives"][domain]["mime_types"].get(mime, 0) + 1
        except Exception as exc:
            report["errors"].append({"domain": domain, "error": f"{type(exc).__name__}: {exc}"})
    _write_json(path, {"report": report, "rows": all_rows})
    return report


def _pick_capture(rows: list[dict], url: str, target: str, lookahead_days: int = 0) -> list[dict]:
    canonical = _canonical(url)
    parts = urlsplit(canonical)
    aliases = {canonical}
    if not PathLikeExtension.has_extension(parts.path.rsplit("/", 1)[-1]):
        stem = parts.path.rstrip("/") or "/"
        aliases.add(parts._replace(path=stem).geturl())
        aliases.add(parts._replace(path=stem + ("/" if stem != "/" else "")).geturl())
    candidates = [row for row in rows if _canonical(row.get("original", "")) in aliases
                  and row.get("mimetype", "") in
                  ("text/html", "text/css", "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/x-icon")]
    before = [row for row in candidates if row.get("timestamp", "") <= target]
    if before:
        return sorted(before, key=lambda row: row.get("timestamp", ""), reverse=True)
    if lookahead_days:
        try:
            cutoff = (datetime.strptime(target[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
                      + timedelta(days=lookahead_days)).strftime("%Y%m%d")
        except ValueError:
            cutoff = target[:8]
        after = [row for row in candidates if row.get("timestamp", "")[:8] <= cutoff]
        return sorted(after, key=lambda row: row.get("timestamp", ""))
    return []


def _kind_for_row(row: dict, url: str) -> str:
    mime = row.get("mimetype", "")
    if mime == "text/html":
        return "html"
    return kind_for(url, mime)


def _archive_url(timestamp: str, url: str) -> str:
    return "https://web.archive.org/web/" + timestamp + "id_/" + url


def _is_compromised_html(body: bytes) -> bool:
    soup = BeautifulSoup(body, "html.parser")
    title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
    text = " ".join(soup.get_text(" ", strip=True).lower().split())[:12000]
    spam_terms = ("cialis", "viagra", "levitra", "phentermine", "online pharmacy", "casino bonus")
    return any(term in title or term in text[:3000] for term in spam_terms)


def _discover_artist_links(body: bytes, url: str, domain: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(body, "html.parser")
    found: dict[str, str] = {}

    def add(value: str, base: str, forced: str | None = None):
        canonical = _canonical(value, base)
        if not canonical:
            return
        parts = urlsplit(canonical)
        host = parts.hostname or ""
        kind = forced or kind_for(canonical)
        internal = _site_host(host, domain)
        # External automatic dependencies are limited to stylesheets and images.
        if internal or kind in ("css", "image"):
            if kind in ("html", "css", "image"):
                found.setdefault(canonical, kind)

    for anchor in soup.select("a[href], area[href]"):
        add(anchor.get("href", ""), url, "html")
    for link in soup.select("link[href]"):
        rel = link.get("rel", [])
        if "stylesheet" in rel:
            add(link["href"], url, "css")
        elif any(token in rel for token in ("icon", "shortcut", "apple-touch-icon")):
            add(link["href"], url, "image")
    for node in soup.select("img[src], source[src], video[poster]"):
        if node.name == "source" and str(node.get("type", "")).startswith(("audio/", "video/")):
            continue
        add(node.get("src") or node.get("poster", ""), url, "image")
        for entry in node.get("srcset", "").split(","):
            if entry.strip():
                add(entry.strip().split()[0], url, "image")
    for node in soup.select("[background]"):
        add(node.get("background", ""), url, "image")
    for node in soup.select("[style]"):
        for ref in discover_css("x{" + node["style"] + "}", url):
            add(ref, url)
    for style in soup.find_all("style"):
        for ref in discover_css(style.get_text(), url):
            add(ref, url)
    return list(found.items())


def _asset_suffix(body: bytes, kind: str, mime: str) -> str:
    if kind == "html": return ".html"
    if kind == "css": return ".css"
    if body.startswith(b"\xff\xd8"): return ".jpg"
    if body.startswith(b"\x89PNG"): return ".png"
    if body.startswith((b"GIF87a", b"GIF89a")): return ".gif"
    if body.startswith(b"RIFF") and body[8:12] == b"WEBP": return ".webp"
    if b"<svg" in body[:1000].lower(): return ".svg"
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp",
              "image/svg+xml": ".svg", "text/css": ".css"}.get(mime)
    return suffix or ".bin"


def recover_artist_sites(root: Path, max_files: int = 1800, delay: float = 0.6,
                         progress=None, retry_failed: bool = False) -> dict:
    """Resumably fetch linked pages and visual dependencies for every dated edition."""
    root = Path(root)
    index_path = root / "recovery/artist-sites/index.json"
    manifest_path = root / "recovery/artist-sites/manifest.json"
    if not index_path.exists():
        raise ValueError("Run artist-index before artist-recover")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "editions": {}, "external_index": {}, "failures": []}
    rows_by_domain = index.get("rows", {})
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation; paced requests)"
    client = ArchiveClient(session=session, delay=delay, timeout=40, retries=3)
    attempts = 0
    for domain, editions in EDITIONS.items():
        domain_rows = rows_by_domain.get(domain, [])
        for edition in editions:
            eid = edition["id"]
            key = domain + "/" + eid
            site = manifest["editions"].setdefault(key, {"domain": domain, "edition": edition, "resources": {}, "missing": []})
            records: dict[str, dict] = site["resources"]
            missing: dict[str, dict] = {item["url"]: item for item in site.get("missing", [])}
            queue = [_canonical(edition["root"])]
            visited = set()
            while queue and attempts < max_files:
                url = queue.pop(0)
                canonical = _canonical(url)
                if canonical in visited:
                    continue
                visited.add(canonical)
                if _is_dynamic_avatar(canonical):
                    missing[canonical] = {"url": canonical, "kind": "image", "status": "excluded_dynamic_avatar",
                                          "reason": "Gravatar avatar endpoints are dynamic third-party profile images, not stable site-owned media; their dated replays were unavailable during this pass."}
                    site["missing"] = list(missing.values())
                    _write_json(manifest_path, manifest)
                    continue
                if canonical in missing and not retry_failed:
                    continue
                existing = records.get(canonical)
                if existing and existing.get("raw_path") and (root / existing["raw_path"]).is_file():
                    body = (root / existing["raw_path"]).read_bytes()
                    kind = existing["kind"]
                else:
                    kind = kind_for(canonical)
                    internal_url = _site_host(urlsplit(canonical).hostname or "", domain)
                    source_rows = domain_rows if internal_url else manifest["external_index"].get(canonical, [])
                    if source_rows is None:
                        try:
                            source_rows = _index_url(canonical, session, delay)
                            manifest["external_index"][canonical] = source_rows
                        except Exception as exc:
                            missing[canonical] = {"url": canonical, "kind": kind, "status": "index_failed", "error": f"{type(exc).__name__}: {exc}"}
                            _write_json(manifest_path, manifest)
                            continue
                    candidates = _pick_capture(source_rows, canonical, edition["capture"], edition.get("lookahead_days", 0))
                    if not candidates and internal_url:
                        missing[canonical] = {"url": canonical, "kind": kind, "status": "not_indexed_before_edition"}
                        continue
                    body = b""
                    chosen = None
                    last_error = ""
                    if not internal_url:
                        # Linked Squarespace assets are sometimes absent from a
                        # full-domain CDX query, so request the dated replay
                        # directly. Wayback redirects to the capture actually
                        # available for that resource.
                        attempts += 1
                        try:
                            response = client.get(_archive_url(edition["capture"], canonical))
                            kind = kind_for(canonical, response.headers.get("Content-Type", "").split(";", 1)[0])
                            if kind in ("html", "css", "image"):
                                validate_payload(response.body, kind)
                                actual = capture_from(response.url) or edition["capture"]
                                body = response.body
                                chosen = {"original": canonical, "timestamp": actual, "mimetype": response.headers.get("Content-Type", "").split(";", 1)[0],
                                          "digest": ""}
                            else:
                                last_error = "excluded unsupported linked resource type: " + kind
                        except Exception as exc:
                            last_error = f"{type(exc).__name__}: {exc}"
                    for row in candidates:
                        if chosen is not None:
                            break
                        kind = _kind_for_row(row, canonical)
                        if kind not in ("html", "css", "image"):
                            last_error = "excluded unsupported resource type: " + kind
                            break
                        attempts += 1
                        try:
                            response = client.get(_archive_url(row["timestamp"], row["original"]))
                            validate_payload(response.body, kind)
                            if kind == "html" and _is_compromised_html(response.body):
                                last_error = "excluded spam-injected capture"
                                continue
                            actual = capture_from(response.url) or row["timestamp"]
                            if actual != row["timestamp"]:
                                try:
                                    latest_allowed = (datetime.strptime(edition["capture"][:8], "%Y%m%d")
                                        + timedelta(days=edition.get("lookahead_days", 0))).strftime("%Y%m%d") + "235959"
                                except ValueError:
                                    latest_allowed = edition["capture"]
                                if actual > latest_allowed:
                                    last_error = "archive replay resolved outside the edition capture window"
                                    continue
                            chosen = dict(row)
                            chosen["requested_capture"] = row["timestamp"]
                            chosen["timestamp"] = actual
                            actual_row = next((item for item in candidates if item["timestamp"] == actual), None)
                            if actual_row:
                                chosen.update(actual_row)
                                chosen["requested_capture"] = row["timestamp"]
                            body = response.body; break
                        except Exception as exc:
                            last_error = f"{type(exc).__name__}: {exc}"
                    if chosen is None:
                        missing[canonical] = {"url": canonical, "kind": kind, "status": "unavailable_or_excluded", "error": last_error}
                        site["missing"] = list(missing.values())
                        _write_json(manifest_path, manifest)
                        if attempts % 10 == 0 and progress: progress({"attempted": attempts, "edition": key, "url": canonical, "status": "missing"})
                        continue
                    digest = hashlib.sha256(body).hexdigest()
                    suffix = _asset_suffix(body, kind, chosen.get("mimetype", ""))
                    relative = "recovery/artist-sites/raw/" + digest + suffix
                    destination = root / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.exists(): destination.write_bytes(body)
                    existing = {"url": canonical, "kind": kind, "status": "recovered", "raw_path": relative,
                                "sha256": digest, "bytes": len(body), "actual_capture": chosen["timestamp"],
                                "requested_capture": chosen.get("requested_capture", chosen["timestamp"]),
                                "capture_digest": chosen.get("digest"), "mime": chosen.get("mimetype", ""),
                                "source_archive": "Internet Archive Wayback", "source_original": chosen["original"]}
                    records[canonical] = existing
                    if chosen["timestamp"] > edition["capture"]:
                        existing["capture_relation"] = "after_edition_homepage"
                        existing["compatibility_review_required"] = True
                    missing.pop(canonical, None)
                    site["missing"] = list(missing.values())
                    _write_json(manifest_path, manifest)
                    if attempts % 10 == 0 and progress: progress({"attempted": attempts, "edition": key, "url": canonical, "status": "recovered"})
                if kind in ("html", "css"):
                    if kind == "html":
                        refs = _discover_artist_links(body, canonical, domain)
                    else:
                        refs = [(ref, kind_for(ref)) for ref in discover_css(body.decode("utf-8", errors="replace"), canonical)]
                    for ref, ref_kind in refs:
                        if ref_kind in ("html", "css", "image") and ref not in visited and ref not in queue:
                            queue.append(ref)
            site["missing"] = list(missing.values())
            site["complete"] = not queue
            site["attempted"] = len(visited)
            _write_json(manifest_path, manifest)
            if progress: progress({"attempted": attempts, "edition": key, "remaining_queue": len(queue), "status": "checkpointed"})
            if attempts >= max_files:
                break
        if attempts >= max_files:
            break
    resources = []
    gaps = []
    for key, site in manifest["editions"].items():
        for url, record in site.get("resources", {}).items():
            resources.append({"edition": key, "url": url, "kind": record.get("kind"),
                              "actual_capture": record.get("actual_capture"), "sha256": record.get("sha256"),
                              "bytes": record.get("bytes"), "source_archive": record.get("source_archive"),
                              "source_original": record.get("source_original"), "capture_digest": record.get("capture_digest"),
                              "compatibility_review_required": bool(record.get("compatibility_review_required"))})
        for item in site.get("missing", []):
            gaps.append({"edition": key, **item})
    report = {"attempted_records": attempts,
              "editions": {key: {"recovered": sum(1 for r in value["resources"].values() if r.get("raw_path")),
                                  "missing": len(value.get("missing", [])), "complete": value.get("complete", False)}
                           for key, value in manifest["editions"].items()},
              "unique_sha256": len({item["sha256"] for item in resources if item.get("sha256")}),
              "resources": resources, "gaps": gaps, "source_inspections": SOURCE_INSPECTIONS,
              "index_coverage": index.get("report", {}).get("archives", {}),
              "failures": manifest.get("failures", [])}
    manifest["report"] = report
    _write_json(manifest_path, manifest)
    report_path = root / "docs/recovery-report/artist-sites-report.json"
    _write_json(report_path, report)
    lines = ["# Prometheus Brown and Sabzi archive recovery", "",
             "Source pages remain separated by host and dated edition. The machine-readable report lists every recovered capture and known failed or unavailable linked resource.", "",
             "## Internet Archive index coverage", ""]
    for domain, details in report["index_coverage"].items():
        lines.append(f"- `{domain}`: {details['rows']} successful CDX rows across {details['unique_urls']} normalized URLs; available timestamp years: "
                     + ", ".join(sorted(details["captures_by_year"])) + ".")
    lines += ["", "## Recovered editions", ""]
    for key, details in report["editions"].items():
        lines.append(f"- `{key}`: {details['recovered']} locally saved responses; {details['missing']} unresolved or excluded linked resources; "
                     + ("crawl queue drained." if details["complete"] else "recovery queue remains; rerun `python -m restore artist-recover` to resume."))
    lines += ["", "## Source-integrity notes", "",
              f"The acquisition contains {report['unique_sha256']} unique SHA-256 payloads. Each recovered record retains the original URL, capture timestamp, Wayback source, and CDX digest when available.",
              "A sampled Prometheus Brown `/0.html` capture from 2009-09-01 is spam-injected (its page title is ‘Cialis Get Viagra’), while the `/blog/` capture from 2009-12-28 is a genuine Prometheus Brown WordPress blog. Those are kept distinct. Eight unique 2024 root digests (15 index rows) were inspected individually; all are spam-injected JAYA77 casino pages. They are not treated as artist-site editions. 2024–2026 rows remain in the source index for continued review, and the latest selected artist homepage remains 2022.",
              "Missing linked resources are listed in `artist-sites-report.json`; a failed dependency is not silently replaced with a live asset. Dynamic Gravatar profile-image URLs are listed as excluded gaps. Site pages have scripts, embedded remote frames and forms removed; CSS/image rendering dependencies are local-only in generated output.",
              ""]
    report_path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    return report


def build_artist_sites(root: Path, output: Path, base: str = "", candidate: bool = False) -> dict:
    """Render captured artist-site pages under independent dated prefixes."""
    root = Path(root)
    output = Path(output)
    manifest_path = (root / "recovery/artist-sites/manifest.json" if candidate
                     else root / "source/artist-sites.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"editions": {}}
    for domain, editions in EDITIONS.items():
        for edition in editions:
            manifest["editions"].setdefault(domain + "/" + edition["id"], {
                "domain": domain, "edition": edition, "resources": {}, "missing": [], "complete": False
            })
    summary: dict = {"editions": {}, "source": "candidate" if candidate else "reviewed"}
    base = "/" + base.strip("/") if base and base.strip("/") else ""
    for key, site in manifest.get("editions", {}).items():
        domain = site["domain"]
        edition = site["edition"]["id"]
        resources = site.get("resources", {})
        urlmap: dict[str, str] = {}
        unrenderable: set[str] = set()
        for url, record in resources.items():
            if not record.get("raw_path"):
                continue
            if record.get("kind") == "image" and Path(record["raw_path"]).suffix.lower() == ".svg":
                raw = (root / record["raw_path"]).resolve()
                raw_root = (root / "recovery/artist-sites/raw").resolve()
                source_root = (root / "source/artist-sites/raw").resolve()
                if not (raw.is_relative_to(raw_root) or raw.is_relative_to(source_root)):
                    unrenderable.add(url)
                    continue
                try:
                    sanitize_svg(raw.read_bytes())
                except (OSError, ValueError):
                    unrenderable.add(url)
                    continue
            if record.get("kind") == "html":
                local = edition_route(domain, edition, url)
            else:
                local = local_asset_path(domain, edition, url, Path(record.get("raw_path", "")).suffix.lstrip("."))
            record["local_path"] = local
            urlmap[_canonical(url)] = base + local
        for missing in site.get("missing", []):
            url = missing.get("url", "")
            if missing.get("kind") == "html" and _canonical(url) not in urlmap:
                try:
                    urlmap[_canonical(url)] = base + edition_route(domain, edition, url)
                except ValueError:
                    pass

        found = pages = assets = gaps = 0
        for url, record in resources.items():
            if url in unrenderable:
                gaps += 1
                continue
            raw_path = record.get("raw_path")
            if not raw_path:
                continue
            source = (root / raw_path).resolve()
            if not any(source.is_relative_to((root / prefix).resolve()) for prefix in (
                "recovery/artist-sites/raw", "source/artist-sites/raw", "source/artist-sites/redacted"
            )):
                continue
            body = source.read_bytes()
            if hashlib.sha256(body).hexdigest() != record.get("sha256"):
                continue
            kind = record.get("kind")
            local = record["local_path"]
            destination = (output / local.removeprefix(base).lstrip("/")).resolve()
            if not destination.is_relative_to(output.resolve()):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if kind == "html":
                text, dependencies = sanitize_artist_html(body.decode("utf-8", errors="replace"), url, urlmap,
                                                       record.get("actual_capture", ""))
                soup = BeautifulSoup(text, "html.parser")
                csp = soup.new_tag("meta", attrs={"http-equiv": "Content-Security-Policy",
                    "content": "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; media-src 'none'; object-src 'none'; form-action 'none'; base-uri 'none'"})
                soup.head.append(csp)
                destination.write_text("<!doctype html>\n" + str(soup), encoding="utf-8")
                pages += 1
                gaps += len(dependencies)
            elif kind == "css":
                destination.write_text(_rewrite_css(body.decode("utf-8", errors="replace"), url, urlmap), encoding="utf-8")
                assets += 1
            elif kind == "image":
                if destination.suffix.lower() == ".svg":
                    destination.write_bytes(sanitize_svg(body))
                else:
                    destination.write_bytes(body)
                assets += 1
            found += 1

        for missing in site.get("missing", []):
            url = missing.get("url", "")
            if missing.get("kind") != "html" or not url:
                continue
            local = urlmap.get(_canonical(url))
            if not local:
                continue
            destination = (output / local.removeprefix(base).lstrip("/")).resolve()
            if not destination.is_relative_to(output.resolve()) or destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            archive_url = "https://web.archive.org/web/" + quote(url, safe=":/?&=%#@+;,-._~")
            destination.write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Source gap</title><body><main><p>Historical source gap</p><h1>This page was linked but its archived response was unavailable.</h1>'
                '<p><a href="' + archive_url + '">Check the Internet Archive capture</a></p></main></body></html>',
                encoding="utf-8")
            gaps += 1
        root_page = output / edition_route(domain, edition, site["edition"]["root"]).removeprefix(base).lstrip("/")
        if not root_page.exists():
            root_page.parent.mkdir(parents=True, exist_ok=True)
            root_page.write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Edition source gap</title><body><main><p>HISTORICAL SITE ARCHIVE</p><h1>'
                + labels_placeholder(domain) + ' · ' + edition + '</h1><p>The archive index records this edition, but its homepage capture has not been recovered into this build.</p>'
                '<p><a href="' + base + ('/prometheusbrown/' if domain == 'prometheusbrown.com' else '/sabzi/') + '">Back to editions</a></p></main></body></html>',
                encoding="utf-8")
            gaps += 1
        summary["editions"][key] = {"recovered_pages": pages, "local_assets": assets,
                                    "source_gaps": gaps, "indexed_missing": len(site.get("missing", [])),
                                    "unrenderable_assets": sorted(unrenderable),
                                    "later_captures_needing_review": sum(1 for record in resources.values()
                                                                          if record.get("compatibility_review_required")),
                                    "root": site["edition"]["root"], "capture": site["edition"]["capture"]}

    labels = {"prometheusbrown.com": "Prometheus Brown", "sabzi.co": "Sabzi"}
    for domain, slug in (("prometheusbrown.com", "prometheusbrown"), ("sabzi.co", "sabzi")):
        editions = [site for key, site in manifest.get("editions", {}).items() if site.get("domain") == domain]
        cards = []
        for site in sorted(editions, key=lambda item: item["edition"]["id"]):
            eid = site["edition"]["id"]
            path = base + edition_route(domain, eid, site["edition"]["root"])
            stats = summary["editions"].get(domain + "/" + eid, {})
            later = stats.get("later_captures_needing_review", 0)
            review_note = f" · {later} later-page captures need review" if later else ""
            cards.append(f'<a class="artist-edition" href="{path}"><strong>{eid}</strong><span>{site["edition"]["label"]}</span><small>{stats.get("recovered_pages", 0)} pages · {stats.get("local_assets", 0)} local assets{review_note}</small></a>')
        hub = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               '<title>' + labels[domain] + ' — archived editions</title><style>'
               'body{margin:0;background:#f2f0eb;color:#20211f;font:16px/1.5 system-ui,sans-serif}main{max-width:900px;margin:8vh auto;padding:24px}h1{font-size:clamp(2.5rem,8vw,5rem);letter-spacing:-.06em;margin:12px 0}p{max-width:60ch}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:32px}.artist-edition{display:grid;gap:8px;padding:22px;border:1px solid #aaa;background:#fff;color:inherit;text-decoration:none}.artist-edition:hover,.artist-edition:focus{outline:3px solid #376184}.artist-edition strong{font-size:2rem}.artist-edition small{color:#666}'
               '</style></head><body><main><p>HISTORICAL SITE ARCHIVE · SEPARATE FROM BLUE SCHOLARS</p><h1>' + labels[domain] + '</h1>'
               '<p>Each card opens a separately preserved site edition based on dated archived source material. Some pages or external media may remain unavailable.</p>'
               '<nav class="grid" aria-label="Archived editions">' + "".join(cards) + '</nav><p><a href="' + base + '/">Back to Blue Scholars archive</a></p></main></body></html>')
        destination = output / slug / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(hub, encoding="utf-8")
    return summary


def labels_placeholder(domain: str) -> str:
    return "Prometheus Brown" if domain == "prometheusbrown.com" else "Sabzi"


def promote_artist_sites(root: Path, reviewed: bool = False) -> dict:
    """Promote hash-verified artist-site captures after an explicit source review.

    Later-than-homepage captures remain candidate-only until a reviewer stores a
    per-resource compatibility note in the acquisition manifest.
    """
    if not reviewed:
        raise ValueError("Artist-site source review is required: pass --reviewed after inspection")
    root = Path(root)
    candidate_path = root / "recovery/artist-sites/manifest.json"
    if not candidate_path.exists():
        raise ValueError("Run artist-recover before promoting artist-site sources")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    approved = {"version": 1, "editions": {}, "source_inspections": candidate.get("report", {}).get("source_inspections", []),
                "source_review": {"actor": "Codex agent", "reviewed_at": datetime.now(timezone.utc).isoformat(),
                                  "note": "Artist-site source bytes were hash-verified after a separate edition review."}}
    staged = 0
    skipped_later = 0
    for key, site in candidate.get("editions", {}).items():
        edition = {k: v for k, v in site.items() if k != "resources"}
        edition["resources"] = {}
        for url, record in site.get("resources", {}).items():
            if not record.get("raw_path") or record.get("kind") not in ("html", "css", "image"):
                continue
            if record.get("compatibility_review_required") and not record.get("compatibility_review"):
                skipped_later += 1
                continue
            source = (root / record["raw_path"]).resolve()
            raw_root = (root / "recovery/artist-sites/raw").resolve()
            if not source.is_relative_to(raw_root):
                raise ValueError(f"Artist source path escapes the recovery store: {url}")
            body = source.read_bytes()
            if hashlib.sha256(body).hexdigest() != record.get("sha256"):
                raise ValueError(f"Artist source hash mismatch: {url}")
            validate_payload(body, record["kind"])
            body, redaction_count = redact_public_credentials(body)
            relative = (
                f"source/artist-sites/redacted/{hashlib.sha256(body).hexdigest()}{Path(record['raw_path']).suffix}"
                if redaction_count else "source/artist-sites/raw/" + Path(record["raw_path"]).name
            )
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(body)
            copied = dict(record)
            copied.update(raw_path=relative, sha256=hashlib.sha256(body).hexdigest(),
                          source_reviewed=True, status="recovered")
            if redaction_count:
                copied["original_sha256"] = record["sha256"]
                copied["source_redaction"] = {"field": "credential-shaped API value", "count": redaction_count,
                    "reason": "Credential-shaped value omitted from public source copy."}
            edition["resources"][url] = copied
            staged += 1
        approved["editions"][key] = edition
    _write_json(root / "source/artist-sites.json", approved)
    if staged:
        _write_json(root / "source/review.json", {"publish_approved": False, "visual_reviewed": False,
                    "note": "Artist-site source collection changed; review the generated site before publishing."})
    return {"promoted": staged, "skipped_later_captures": skipped_later,
            "publish_approved": False, "visual_reviewed": False}


def review_artist_capture(root: Path, edition_key: str, url: str, reason: str) -> dict:
    """Record a compatibility decision for one later-linked-page capture."""
    reason = reason.strip()
    if not reason:
        raise ValueError("A resource-specific compatibility reason is required")
    path = Path(root) / "recovery/artist-sites/manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    site = manifest.get("editions", {}).get(edition_key)
    if site is None:
        raise ValueError("Unknown artist-site edition")
    canonical = _canonical(url)
    record = site.get("resources", {}).get(canonical)
    if record is None or not record.get("compatibility_review_required"):
        raise ValueError("Capture is not a later source awaiting compatibility review")
    if record.get("compatibility_review"):
        raise ValueError("This capture already has a compatibility decision")
    review = {"actor": "Codex agent", "reviewed_at": datetime.now(timezone.utc).isoformat(),
              "capture": record.get("actual_capture"), "sha256": record.get("sha256"), "reason": reason}
    record["compatibility_review"] = review
    _write_json(path, manifest)
    return {"edition": edition_key, "url": canonical, **review}
