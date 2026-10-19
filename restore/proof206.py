"""Build a locally browsable, date-separated 206proof.com recovery preview."""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

from .archive import validate_payload
from .render import render_css


EDITION_DEFS = (
    ("2007", "2007 Vanilla 1.1.3", "The earliest recovered discussion site."),
    ("vanilla", "2008–2012 Vanilla forum", "The larger archived forum under /forum/."),
    ("community", "2012–2013 community site", "Discussion, profile, activity, and comment pages."),
    ("vbulletin", "2013–2014 vBulletin forum", "A separate forum generation under /4um/."),
)
SITE_HOSTS = {"206proof.com", "www.206proof.com"}
NOTICE_CSS = """.proof206-note{font:13px/1.45 Arial,sans-serif;background:#f4f0e8;color:#333;border-bottom:1px solid #b8ad9d;padding:8px 12px;margin:0}.proof206-note a{color:#164d78}.proof206-unavailable{display:inline-block;min-width:2em;min-height:1.2em;border:1px dashed #888;color:#555;padding:2px}.proof206-missing-image{display:inline-block;border:1px dashed #888;padding:4px;color:#555;font:12px Arial,sans-serif}.proof206-archive-nav{font:12px Arial,sans-serif;background:#e8e4dc;color:#333;padding:6px 12px}.proof206-archive-nav a{margin-right:14px;color:#164d78}.proof206-media-link{font:13px Arial,sans-serif}"""
HUB_CSS = """body{margin:0;background:#e9e7e2;color:#252525;font:16px/1.55 Georgia,serif}.proof206-hub{max-width:1050px;margin:38px auto;padding:0 22px}.proof206-hub h1{font:700 42px/1.05 Arial,sans-serif;margin:0 0 12px}.proof206-hub .intro{max-width:720px;color:#555}.proof206-editions{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:16px;margin:28px 0}.proof206-edition{display:flex;flex-direction:column;gap:10px;padding:20px;background:#fff;border:1px solid #c9c4ba;color:inherit;text-decoration:none;min-height:125px}.proof206-edition:hover,.proof206-edition:focus{border-color:#24577a;box-shadow:0 2px 10px #0002}.proof206-year{font:700 23px Arial,sans-serif;color:#1c5479}.proof206-meta{font:13px Arial,sans-serif;color:#555}.proof206-warning{border-top:1px solid #c9c4ba;padding-top:14px;color:#555;font-size:14px}.proof206-top{font:12px Arial,sans-serif} @media(max-width:520px){.proof206-hub{margin:24px auto}.proof206-hub h1{font-size:34px}}"""


def _capture(row: dict) -> str:
    return str(row.get("actual_capture") or row.get("requested_capture") or "")


def _parts(url: str):
    p = urlsplit(url)
    return p


def _join_url(base: str, value) -> str:
    try:
        return urljoin(base, str(value))
    except (TypeError, ValueError):
        return ""


def _source_key(url: str) -> tuple[str, str]:
    p = urlsplit(url)
    return (p.path.rstrip("/") or "/", p.query)


def _is_site_url(url: str) -> bool:
    return (urlsplit(url).hostname or "").lower() in SITE_HOSTS


def _safe_ext(url: str, kind: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        return suffix
    return {"css": ".css", "image": ".img"}.get(kind, ".bin")


def _nearest(rows: list[tuple[dict, bytes, str]], timestamp: str) -> tuple[dict, bytes, str] | None:
    """Prefer the closest capture at or before a page, then the nearest later one."""
    if not rows:
        return None
    dated = [item for item in rows if _capture(item[0])]
    if dated:
        dates = [_capture(item[0]) for item in dated]
        index = bisect_right(dates, timestamp) - 1
        return dated[max(index, 0)]
    return rows[0]


def _html_route(url: str, prefix: str) -> str:
    p = urlsplit(url)
    path = p.path or "/"
    if path == "/":
        route = "site/index" if prefix in ("2007", "community") else "index"
    else:
        route = path.strip("/")
        if route.endswith("/"):
            route += "index"
        elif route.lower().endswith(".php"):
            route = route[:-4]
            route += "/index"
        elif not Path(route).suffix:
            route += "/index"
    if p.query:
        token = hashlib.sha256(p.query.encode("utf-8")).hexdigest()[:12]
        parent = route[:-6] if route.endswith("/index") else route
        route = parent.rstrip("/") + "/_q_" + token + "/index"
    return f"/206proof/{prefix}/{route}.html"


def _era_for(row: dict) -> str | None:
    url = row.get("original", "")
    if not _is_site_url(url):
        return None
    year = int(_capture(row)[:4] or "0")
    path = urlsplit(url).path or "/"
    if year == 2007:
        return "2007"
    if 2008 <= year <= 2012 and path.startswith("/forum/"):
        return "vanilla"
    if 2012 <= year <= 2013 and (
        path in ("/", "/discussions", "/discussions/")
        or path.startswith(("/discussion/", "/profile/", "/activity", "/comments/"))
    ):
        return "community"
    if 2013 <= year <= 2014 and path.startswith("/4um/"):
        return "vbulletin"
    return None


def select_pages(resources: list[dict]) -> dict[str, list[dict]]:
    selected: dict[str, dict[tuple[str, str], dict]] = {key: {} for key, _, _ in EDITION_DEFS}
    for row in resources:
        if row.get("result") != "recovered" or row.get("kind") != "html":
            continue
        edition = _era_for(row)
        if not edition:
            continue
        key = _source_key(row["original"])
        previous = selected[edition].get(key)
        if previous is None or _capture(row) > _capture(previous):
            selected[edition][key] = row
    return {edition: sorted(rows.values(), key=lambda r: r["original"])
            for edition, rows in selected.items()}


def _read_verified(root: Path, row: dict) -> bytes:
    path = (root / row["raw_path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("206proof raw path escapes the project")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != row.get("sha256"):
        raise ValueError(f"206proof hash mismatch for {row.get('original')}")
    validate_payload(body, row["kind"])
    return body


def _hub_page(base: str, page_counts: dict[str, int], missing: dict[str, int]) -> str:
    cards = []
    for key, label, detail in EDITION_DEFS:
        href = ("/206proof/2007/site/index.html" if key == "2007" else
                f"/206proof/{key}/index.html")
        cards.append(
            f'<a class="proof206-edition" href="{base}{href}">'
            f'<span class="proof206-year">{html.escape(label)}</span>'
            f'<span>{html.escape(detail)}</span>'
            f'<span class="proof206-meta">{page_counts.get(key, 0)} captured pages'
            f" · {missing.get(key, 0)} linked pages not captured</span></a>"
        )
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; base-uri \'none\'; form-action \'none\'; frame-src \'none\'; object-src \'none\'">'
            f'<link rel="stylesheet" href="{base}/206proof/hub.css">'
            '<title>206Proof archive</title></head><body><main class="proof206-hub">'
            '<p class="proof206-top"><a href="' + base + '/">Blue Scholars restoration</a></p>'
            '<h1>206Proof archive</h1><p class="intro">Separate source-based editions of the Seattle hip-hop discussion site. Each page carries its archive date; missing pages and media are identified rather than recreated.</p>'
            '<nav class="proof206-editions" aria-label="Historical site generations">' + ''.join(cards) + '</nav>'
            '<p class="proof206-warning">This is an independent historical restoration, not a current 206Proof service. Forms, scripts, and automatic external media have been disabled. Original posts, images, and music remain attributable to their creators; this preview does not establish redistribution rights.</p>'
            '</main></body></html>')


def _page_gap_html(title: str, source: str, timestamp: str, base: str) -> str:
    wayback = f"https://web.archive.org/web/{timestamp}/{source}" if timestamp else source
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<link rel="stylesheet" href="{base}/206proof/archive-note.css"><title>{html.escape(title)} — 206Proof archive</title></head><body>'
            '<aside class="proof206-note">206Proof historical archive · source gap</aside><main style="max-width:760px;margin:3em auto;padding:0 1em">'
            f'<h1>{html.escape(title)}</h1><p>This linked page has not been recovered as valid page content.</p>'
            f'<p>Observed source: <code>{html.escape(source)}</code></p>'
            f'<p><a href="{html.escape(wayback, quote=True)}">Open the dated archive source</a></p>'
            f'<p><a href="{base}/206proof/index.html">Return to 206Proof archive</a></p></main></body></html>')


def _localize_html(text: str, original: str, timestamp: str, edition: str,
                   base: str, routes: dict, path_routes: dict, assets: dict, css_records: dict,
                   missing_pages: dict, issues: list, soup=None,
                   reused_stylesheet: bool = False) -> str:
    soup = soup or BeautifulSoup(text, "html.parser")
    if soup.html is None:
        wrapper = BeautifulSoup("<!doctype html><html><head></head><body></body></html>", "html.parser")
        for child in list(soup.contents):
            wrapper.body.append(child.extract())
        soup = wrapper
    if soup.head is None:
        soup.html.insert(0, soup.new_tag("head"))
    if soup.body is None:
        soup.html.append(soup.new_tag("body"))
    for meta in list(soup.head.find_all("meta")):
        if meta.get("charset") or str(meta.get("http-equiv", "")).lower() == "content-type":
            meta.decompose()
    charset = soup.new_tag("meta", charset="utf-8")
    soup.head.insert(0, charset)
    for node in list(soup.find_all(["script", "base", "object", "embed", "iframe", "form"])):
        attrs = node.attrs or {}
        src = attrs.get("src") or attrs.get("data") or attrs.get("action") or ""
        if node.name in ("object", "embed", "iframe") and src:
            replacement = soup.new_tag("p", attrs={"class": "proof206-media-link"})
            anchor = soup.new_tag("a", href=src)
            anchor.string = "Open source-linked media (external)"
            replacement.append(anchor)
            node.replace_with(replacement)
        elif node.name == "form":
            replacement = soup.new_tag("div", attrs={"class": "proof206-unavailable", "role": "note"})
            replacement.string = "Interactive posting form not preserved"
            node.replace_with(replacement)
        else:
            node.decompose()
    for node in soup.find_all(True):
        for attr in list(node.attrs):
            if attr.lower().startswith("on"):
                del node.attrs[attr]
        if node.name == "meta" and str(node.get("http-equiv", "")).lower() == "refresh":
            node.decompose()
    if not soup.head.find("meta", attrs={"name": "viewport"}):
        soup.head.append(soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1"}))
    csp = soup.new_tag("meta", attrs={"http-equiv": "Content-Security-Policy", "content": "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'none'; media-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"})
    soup.head.append(csp)
    note_link = soup.new_tag("link", rel="stylesheet", href=f"{base}/206proof/archive-note.css")
    soup.head.append(note_link)
    source_route = routes.get(edition, {}).get(_source_key(original))
    home_route = routes.get(edition, {}).get(("/", ""), f"/206proof/{edition}/index.html")
    nav = soup.new_tag("nav", attrs={"class": "proof206-archive-nav", "aria-label": "Archive navigation"})
    for label, target in (("206Proof archive", "/206proof/index.html"),
                          ("This edition", home_route)):
        link = soup.new_tag("a", href=base + target)
        link.string = label
        nav.append(link)
    note = soup.new_tag("aside", attrs={"class": "proof206-note"})
    note.string = f"Historical 206Proof capture · {timestamp or 'date unknown'} · {edition} edition"
    soup.body.insert(0, note)
    soup.body.insert(1, nav)
    if reused_stylesheet:
        fallback_note = soup.new_tag("p", attrs={"class": "proof206-note"})
        fallback_note.string = "2007 theme CSS was not captured. The closest recovered 206Proof Vanilla theme CSS (2010) is applied for legibility; the original 2007 styling remains a source gap."
        soup.body.insert(2, fallback_note)
    for link in list(soup.find_all("link", href=True)):
        if link.get("href", "").endswith("archive-note.css"):
            continue
        if "stylesheet" in [str(x).lower() for x in link.get("rel", [])]:
            absolute = _join_url(original, link["href"])
            local = assets.get(_source_key(absolute))
            if local:
                link["href"] = base + local
            else:
                issues.append({"type": "missing_stylesheet", "source": original, "url": absolute})
                link.decompose()
        elif link.get("rel") and any(str(x).lower() in ("icon", "shortcut") for x in link["rel"]):
            absolute = _join_url(original, link["href"])
            local = assets.get(_source_key(absolute))
            if local:
                link["href"] = base + local
            else:
                link.decompose()
        else:
            link.decompose()
    for img in list(soup.find_all(["img", "source"])):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src:
            absolute = _join_url(original, src)
            local = assets.get(_source_key(absolute))
            if local:
                img["src"] = base + local
                for attr in ("data-src", "data-original"):
                    img.attrs.pop(attr, None)
            else:
                alt = img.get("alt") or "Image not recovered"
                replacement = soup.new_tag("span", attrs={"class": "proof206-missing-image", "role": "img", "aria-label": alt})
                replacement.string = alt if alt != "" else "Image not recovered"
                img.replace_with(replacement)
                issues.append({"type": "missing_image", "source": original, "url": absolute})
        for attr in ("srcset", "data-srcset"):
            if img.get(attr):
                parts = []
                for entry in img[attr].split(","):
                    bits = entry.strip().split()
                    if not bits:
                        continue
                    joined = _join_url(original, bits[0])
                    local = assets.get(_source_key(joined)) if joined else None
                    if local:
                        parts.append(base + local + (" " + " ".join(bits[1:]) if len(bits) > 1 else ""))
                if parts:
                    img["srcset"] = ", ".join(parts)
                else:
                    img.attrs.pop(attr, None)
    for node in list(soup.find_all("style")):
        css, css_issues = render_css(node.get_text(), original, css_records, base)
        node.string = css
        issues.extend(css_issues)
    for node in soup.find_all(True):
        if node.get("style"):
            css, css_issues = render_css("x{" + node["style"] + "}", original, css_records, base)
            match = re.search(r"\{(.*)\}", css, re.S)
            node["style"] = match.group(1) if match else ""
            issues.extend(css_issues)
    for anchor in list(soup.find_all("a", href=True)):
        value = str(anchor.get("href", ""))
        if value.startswith(base + "/206proof/"):
            continue
        lower = value.strip().lower()
        if lower.startswith(("javascript:", "data:", "denied:")):
            anchor.attrs.pop("href", None)
            continue
        absolute = _join_url(original, value)
        if not absolute:
            anchor.attrs.pop("href", None)
            continue
        if not _is_site_url(absolute):
            continue
        fragment = urlsplit(value).fragment
        key = _source_key(absolute)
        target = routes.get(edition, {}).get(key)
        if target is None:
            target = path_routes.get(edition, {}).get(key[0])
            if target:
                issues.append({"type": "query_variant_not_captured", "source": original, "url": absolute})
        if target is None:
            target = missing_pages.setdefault((edition, key), {
                "route": f"/206proof/{edition}/missing/{hashlib.sha256((key[0]+'?'+key[1]).encode()).hexdigest()[:16]}.html",
                "source": absolute, "timestamp": timestamp,
            })["route"]
        anchor["href"] = base + target + ("#" + fragment if fragment else "")
    title = soup.title.get_text(" ", strip=True) if soup.title else "206Proof archive page"
    if not soup.title:
        title_node = soup.new_tag("title")
        title_node.string = title
        soup.head.append(title_node)
    return "<!doctype html>\n" + str(soup)


def build_206proof_archive(root: Path, output: Path, base: str = "", candidate: bool = False) -> dict:
    """Render captured site generations into a self-contained candidate tree."""
    root = Path(root).resolve()
    output = Path(output).resolve()
    if output.parent != root or output.name not in ("_candidate", "_site"):
        raise ValueError("Output must be the project's _candidate or _site directory")
    if not candidate:
        return {"status": "not_in_reviewed_sources", "editions": {}}
    manifest_path = root / "recovery/206proof/recovered-resources.json"
    if not manifest_path.exists():
        return {"status": "not_available", "editions": {}}
    resources = json.loads(manifest_path.read_text()).get("resources", [])
    pages = select_pages(resources)
    if not any(pages.values()):
        return {"status": "not_available", "editions": {}}
    # Verify sources before copying any bytes into the candidate output.
    valid = []
    source_issues = []
    for row in resources:
        if row.get("result") != "recovered" or row.get("kind") not in ("html", "css", "image"):
            continue
        try:
            body = _read_verified(root, row)
        except (OSError, ValueError) as exc:
            source_issues.append({"type": "invalid_source", "url": row.get("original"), "message": str(exc)})
            continue
        valid.append((row, body))
    assets_by_key: dict[tuple[str, str], list[tuple[dict, bytes]]] = defaultdict(list)
    for row, body in valid:
        if row["kind"] in ("css", "image"):
            assets_by_key[_source_key(row["original"])].append((row, body))
    # Store content-addressed image variants. CSS is rewritten per page date so
    # its own image/font dependencies also remain local and era-appropriate.
    asset_variants: dict[tuple[str, str], list[tuple[dict, bytes, str]]] = defaultdict(list)
    for key, rows in assets_by_key.items():
        for row, body in rows:
            local = f"/206proof/assets/{row['sha256']}{_safe_ext(row['original'], row['kind'])}"
            asset_variants[key].append((row, body, local))
            if row["kind"] == "image":
                dest = output / local.lstrip("/")
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(body)
    fallback_asset_keys = set()
    # The 2007 homepage's exact Vanilla 1.1.3 stylesheets are absent from the
    # archive index. Reuse the same site's later /forum/ theme files, visibly
    # labeling that compatibility choice on 2007 pages.
    for path, query in list(asset_variants):
        if path.startswith(("/forum/themes/206Proof/styles/", "/forum/extensions/Nugget/", "/forum/extensions/Signatures/")):
            alias = (path[len("/forum"):], query)
            if alias not in asset_variants:
                asset_variants[alias] = asset_variants[(path, query)]
                fallback_asset_keys.add(alias)
    routes: dict[str, dict[tuple[str, str], str]] = {e: {} for e, _, _ in EDITION_DEFS}
    path_route_rows: dict[str, dict[str, tuple[dict, str, str]]] = {e: {} for e, _, _ in EDITION_DEFS}
    selected_records: dict[str, dict[tuple[str, str], dict]] = {e: {} for e, _, _ in EDITION_DEFS}
    for edition, records in pages.items():
        for row in records:
            key = _source_key(row["original"])
            route = _html_route(row["original"], edition)
            routes[edition][key] = route
            selected_records[edition][key] = row
            previous = path_route_rows[edition].get(key[0])
            if previous is None or (not key[1] and previous[2]) or (_capture(row) > _capture(previous[0])):
                path_route_rows[edition][key[0]] = (row, route, key[1])
    path_routes = {edition: {path: value[1] for path, value in rows.items()}
                   for edition, rows in path_route_rows.items()}
    missing_pages: dict[tuple[str, tuple[str, str]], dict] = {}
    issues = list(source_issues)
    edition_reports = {}
    for edition, records in pages.items():
        generated = 0
        title_by_source = {}
        for row in records:
            try:
                body = _read_verified(root, row)
            except (OSError, ValueError):
                continue
            text = body.decode("utf-8", errors="replace")
            timestamp = _capture(row)
            page_assets: dict[tuple[str, str], str] = {}
            source_soup = BeautifulSoup(text, "html.parser")
            title_node = source_soup.title
            title_by_source[_source_key(row["original"])] = title_node.get_text(" ", strip=True) if title_node else row["original"]
            stylesheet_keys = set()
            needed_keys = set()
            def note_asset(value):
                joined = _join_url(row["original"], value)
                if joined:
                    key = _source_key(joined)
                    if key in asset_variants:
                        needed_keys.add(key)
            for link in source_soup.find_all("link", href=True):
                if "stylesheet" in [str(x).lower() for x in link.get("rel", [])]:
                    joined = _join_url(row["original"], link["href"])
                    if joined:
                        key = _source_key(joined)
                        stylesheet_keys.add(key)
                        needed_keys.add(key)
            for node in source_soup.find_all(["img", "source"]):
                for attr in ("src", "data-src", "data-original"):
                    if node.get(attr): note_asset(node.get(attr))
                for attr in ("srcset", "data-srcset"):
                    for piece in str(node.get(attr, "")).split(","):
                        if piece.strip(): note_asset(piece.strip().split()[0])
            css_texts = [style.get_text() for style in source_soup.find_all("style")]
            css_texts.extend(str(node.get("style", "")) for node in source_soup.find_all(style=True))
            for css_text in css_texts:
                for value in re.findall(r"url\(\s*['\"]?([^'\")]+)", css_text, re.I):
                    note_asset(value)
            selected_assets = {key: _nearest(asset_variants[key], timestamp) for key in needed_keys}
            selected_assets = {key: value for key, value in selected_assets.items() if value}
            # Include local images referenced by the dated stylesheet itself.
            for asset_key in tuple(stylesheet_keys):
                chosen = selected_assets.get(asset_key)
                if chosen and chosen[0]["kind"] == "css":
                    for value in re.findall(r"url\(\s*['\"]?([^'\")]+)", chosen[1].decode("utf-8", errors="replace"), re.I):
                        joined = _join_url(chosen[0]["original"], value)
                        dep_key = _source_key(joined) if joined else None
                        if dep_key in asset_variants and dep_key not in selected_assets:
                            selected_assets[dep_key] = _nearest(asset_variants[dep_key], timestamp)
            selected_assets = {key: value for key, value in selected_assets.items() if value}
            css_records = {row["original"]: {"kind": row["kind"], "local_path": local}
                           for row, _body, local in selected_assets.values() if row["kind"] == "image"}
            css_rows = {}
            for asset_key, (asset_row, asset_body, _local) in selected_assets.items():
                if asset_row["kind"] == "image":
                    page_assets[asset_key] = _local
                else:
                    css_rows[asset_key] = (asset_row, asset_body)
            for asset_key, (asset_row, asset_body) in css_rows.items():
                if asset_key not in stylesheet_keys:
                    continue
                local = f"/206proof/assets/{asset_row['sha256']}-{timestamp[:8]}.css"
                dest = output / local.lstrip("/")
                if not dest.exists():
                    css_body, css_issues = render_css(asset_body.decode("utf-8", errors="replace"), asset_row["original"], css_records, base.rstrip("/"))
                    issues.extend(css_issues)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(css_body, encoding="utf-8")
                page_assets[asset_key] = local
                css_records[asset_row["original"]] = {"kind": "css", "local_path": local}
            reused_keys = stylesheet_keys & fallback_asset_keys if edition == "2007" else set()
            for key in reused_keys:
                chosen = selected_assets.get(key)
                if chosen:
                    issues.append({"type": "later_same_site_stylesheet_used_for_2007",
                                   "source": row["original"], "asset": chosen[0]["original"],
                                   "asset_capture": _capture(chosen[0])})
            rendered = _localize_html(text, row["original"], timestamp, edition,
                                      base.rstrip("/"), routes, path_routes, page_assets,
                                      css_records, missing_pages, issues, soup=source_soup,
                                      reused_stylesheet=bool(reused_keys))
            route = routes[edition][_source_key(row["original"])]
            dest = output / unquote(route.lstrip("/"))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(rendered, encoding="utf-8")
            generated += 1
        if edition != "2007":
            landing = output / "206proof" / edition / "index.html"
            landing.parent.mkdir(parents=True, exist_ok=True)
            entries = []
            for row in records[:5000]:
                route = routes[edition][_source_key(row["original"])]
                title_text = title_by_source.get(_source_key(row["original"]), row["original"])
                entries.append(f'<li><a href="{base.rstrip("/")}{route}">{html.escape(title_text or row["original"])}</a> <small>{html.escape(_capture(row))}</small></li>')
            landing.write_text(
                '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="' + base.rstrip("/") + '/206proof/hub.css"><title>' + html.escape(dict((x[0],x[1]) for x in EDITION_DEFS)[edition]) + '</title></head><body><main class="proof206-hub"><p><a href="' + base.rstrip("/") + '/206proof/index.html">206Proof archive</a></p><h1>' + html.escape(dict((x[0],x[1]) for x in EDITION_DEFS)[edition]) + '</h1><p>Captured pages are ordered by source URL; dates identify the selected source response.</p><ul>' + ''.join(entries) + '</ul></main></body></html>',
                encoding="utf-8")
        edition_reports[edition] = {"captured_pages": generated, "source_capture_dates": sorted({_capture(r) for r in records if _capture(r)})}
    # Missing internal destinations become truthful, clickable local gap pages.
    for (edition, _key), item in missing_pages.items():
        path = output / unquote(item["route"].lstrip("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_page_gap_html("Historical page not recovered", item["source"], item["timestamp"], base.rstrip("/")), encoding="utf-8")
    (output / "206proof").mkdir(parents=True, exist_ok=True)
    index_html = output / "206proof/index.html"
    index_html.parent.mkdir(parents=True, exist_ok=True)
    index_html.write_text(_hub_page(base.rstrip("/"), {k: len(v) for k, v in pages.items()},
                                    {k: sum(1 for e, _ in missing_pages if e == k) for k, _, _ in EDITION_DEFS}),
                          encoding="utf-8")
    (output / "206proof/archive-note.css").write_text(NOTICE_CSS, encoding="utf-8")
    (output / "206proof/hub.css").write_text(HUB_CSS, encoding="utf-8")
    report = {
        "status": "built", "candidate_only": True, "base_path": base,
        "editions": edition_reports,
        "unique_local_assets": len({r["sha256"] for r, _ in valid if r["kind"] in ("css", "image")}),
        "linked_gap_pages": len(missing_pages),
        "issues": list({json.dumps(i, sort_keys=True): i for i in issues}.values()),
        "remote_automatic_dependencies": [],
        "note": "Captured pages and source-provenance dates are preserved by edition. This is a local candidate; public redistribution rights and visual review remain outstanding.",
    }
    (output / "206proof/recovery-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    return report
