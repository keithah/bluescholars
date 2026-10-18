"""Resumable recovery and offline rendering for masslinemedia.com captures."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from .archive import ArchiveClient, parse_cdx, validate_payload
from .svg import sanitize_svg
from .urls import original_url

CDX_PATH = Path("recovery/massline-cdx.json")
HISTORY_PATH = Path("recovery/massline/all-captures.json")
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"


def _canonical(url: str, base: str = "") -> str:
    value = original_url(url, base)
    if not value:
        return ""
    parts = urlsplit(value)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = parts.port
    netloc = host + ((":" + str(port)) if port and port not in (80, 443) else "")
    # CDX keys use percent-escaped paths, while historical HTML often stores
    # filenames with literal spaces. Canonicalize both spellings so local
    # media/image links resolve to the bytes recovered for that URL.
    path = quote(parts.path or "/", safe="/%:@!$'()*+,;=-._~")
    query = quote(parts.query, safe="/?%:@!$&'()*+,;=-._~")
    return urlunsplit(("http", netloc, path, query, ""))


def _forum_target(query: str) -> str | None:
    # The 2007 forum used both query-style and semicolon-style SMF links.
    pairs = parse_qs(query.replace(";", "&"), keep_blank_values=True)
    topic = next(iter(pairs.get("topic", [])), "")
    board = next(iter(pairs.get("board", [])), "")
    match = re.fullmatch(r"(\d+)(?:\.(\d+)|\.msg(\d+))?", topic)
    if match:
        topic_id, offset, message = match.groups()
        if message:
            return f"/masslinemedia/forum/topic-{topic_id}-message-{message}.html"
        return f"/masslinemedia/forum/topic-{topic_id}-page-{offset or '0'}.html"
    match = re.fullmatch(r"(\d+)(?:\.(\d+))?", board)
    if match:
        board_id, offset = match.groups()
        return f"/masslinemedia/forum/board-{board_id}-page-{offset or '0'}.html"
    return None


def massline_route(url: str) -> str:
    """Map each observed Massline URL to a deterministic, collision-safe path."""
    canonical = _canonical(url)
    if not canonical:
        raise ValueError("Invalid Massline source URL")
    parts = urlsplit(canonical)
    if (parts.hostname or "").lower() not in {"masslinemedia.com", "www.masslinemedia.com"}:
        raise ValueError("URL is outside masslinemedia.com")
    if parts.path.rstrip("/") == "/smf" or parts.path.rstrip("/") == "/smf/index.php":
        forum_path = _forum_target(parts.query)
        if forum_path:
            parsed = parse_qs(parts.query.replace(";", "&"), keep_blank_values=True)
            base_key = "topic" if "topic" in parsed else "board"
            if set(parsed) - {base_key}:
                tag = sha256(canonical.encode("utf-8")).hexdigest()[:10]
                stem, suffix = forum_path.rsplit(".", 1)
                return f"{stem}-{tag}.{suffix}"
            return forum_path
        tag = sha256(canonical.encode()).hexdigest()[:12]
        return f"/masslinemedia/forum/capture-{tag}.html"
    if parts.path in ("", "/") and not parts.query:
        return "/masslinemedia/site/index.html"
    source_path = unquote(parts.path).lstrip("/") or "index.html"
    if source_path.lower() == "index.html":
        tag = sha256(canonical.encode("utf-8")).hexdigest()[:10]
        return f"/masslinemedia/site/index-{tag}.html"
    safe_segments = [quote(s, safe="@:+,;=~!$&'()[]-._") for s in source_path.split("/") if s not in ("", ".", "..")]
    suffix = "/".join(safe_segments) or "index.html"
    if parts.query:
        tag = sha256(parts.query.encode("utf-8")).hexdigest()[:12]
        if "." in suffix.rsplit("/", 1)[-1]:
            stem, ext = suffix.rsplit(".", 1)
            suffix = f"{stem}-{tag}.{ext}"
        else:
            suffix = f"{suffix.rstrip('/')}-{tag}.html"
    if not Path(suffix).suffix:
        suffix += "/index.html"
    if parts.path.startswith("/smf/"):
        return "/masslinemedia/forum/" + suffix.removeprefix("smf/")
    return "/masslinemedia/site/" + suffix


def massline_summary(rows: list[dict]) -> dict:
    """Summarize the preserved URL-key inventory without implying full capture history."""
    years = Counter()
    topics: set[str] = set()
    boards: set[str] = set()
    forum_pages = 0
    forum_html = 0
    topic_urls = 0
    board_urls = 0
    mime_types = Counter()
    for row in rows:
        timestamp = str(row.get("timestamp", ""))
        if timestamp.isdigit():
            years[timestamp[:4]] += 1
        mime_types[row.get("mimetype", "unknown")] += 1
        parts = urlsplit(row.get("original", ""))
        if parts.path.startswith("/smf/") or parts.path.rstrip("/") == "/smf":
            forum_pages += 1
            forum_html += int(row.get("mimetype") == "text/html")
            pairs = parse_qs(parts.query.replace(";", "&"), keep_blank_values=True)
            for value in pairs.get("topic", []):
                topic_urls += 1
                match = re.match(r"(\d+)", value)
                if match:
                    topics.add(match.group(1))
            for value in pairs.get("board", []):
                board_urls += 1
                match = re.match(r"(\d+)", value)
                if match:
                    boards.add(match.group(1))
    return {
        "source_rows": len(rows),
        "forum_pages": forum_pages,
        "forum_html_pages": forum_html,
        "forum_topic_urls": topic_urls,
        "forum_board_urls": board_urls,
        "topic_ids": len(topics),
        "board_ids": len(boards),
        "years": dict(sorted(years.items())),
        "mime_types": dict(sorted(mime_types.items())),
    }


def select_massline_homepage_versions(rows: list[dict]) -> list[dict]:
    """Choose each year's latest substantial homepage capture from the genuine 2006–09 site era."""
    eligible = [r for r in rows if r.get("mimetype") == "text/html"
                and urlsplit(r.get("original", "")).path == "/"
                and not urlsplit(r.get("original", "")).query
                and str(r.get("timestamp", ""))[:4] in {"2006", "2007", "2008", "2009"}
                and str(r.get("length", "")).isdigit() and int(r["length"]) >= 1000]
    selected = {}
    for row in eligible:
        year = row["timestamp"][:4]
        if year not in selected or row["timestamp"] > selected[year]["timestamp"]:
            selected[year] = row
    return [selected[y] for y in sorted(selected)]


def select_latest_massline_rows(rows: list[dict], cutoff: str = "20090831235959") -> list[dict]:
    """Select the last captured source for each URL from the authentic site era."""
    selected: dict[str, dict] = {}
    for row in rows:
        timestamp = str(row.get("timestamp", ""))
        if not timestamp.isdigit() or timestamp > cutoff or str(row.get("statuscode", "200")) != "200":
            continue
        canonical = _canonical(row.get("original", ""))
        if not canonical:
            continue
        if canonical not in selected or timestamp > selected[canonical].get("timestamp", ""):
            selected[canonical] = row
    return sorted(selected.values(), key=lambda row: (row.get("timestamp", ""), row.get("original", "")))


def _read_cdx(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    rows, resume = parse_cdx(text)
    if resume:
        raise ValueError("Massline CDX inventory is paginated and must be resumed before recovery")
    return rows


def index_massline(root: Path) -> dict:
    """Validate the saved domain CDX response and write a durable coverage report."""
    root = Path(root)
    cdx_path = root / CDX_PATH
    if not cdx_path.is_file():
        raise ValueError(f"Missing saved domain index: {CDX_PATH}")
    rows = _read_cdx(cdx_path)
    history_path = root / "recovery/massline/homepage-history.json"
    history_rows = json.loads(history_path.read_text(encoding="utf-8")).get("rows", []) if history_path.exists() else []
    versions = select_massline_homepage_versions(history_rows)
    full_history_path = root / HISTORY_PATH
    full_history = json.loads(full_history_path.read_text(encoding="utf-8")) if full_history_path.exists() else {}
    full_history_complete = bool(full_history.get("complete"))
    coverage_note = (
        f"The uncollapsed status-200 CDX query is checkpointed and complete for this domain pattern ({len(full_history.get('rows', [])):,} capture events). This exhausts the returned query, not other archives, blocked responses, or unqueried subdomains."
        if full_history_complete else
        "The saved collapsed CDX index contains one row per URL key. The uncollapsed capture-history query is incomplete or not yet saved; resume `python -m restore massline-history --max-pages 1`."
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": "https://web.archive.org/cdx/search/cdx?url=masslinemedia.com/*&output=json&filter=statuscode:200&collapse=urlkey",
        "url": "masslinemedia.com/*",
        "status_filter": "200",
        "collapse": "urlkey",
        "capture_history_complete": full_history_complete,
        "full_capture_rows": len(full_history.get("rows", [])),
        "full_capture_query_pages": full_history.get("pages", 0),
        "coverage_note": coverage_note,
        "inventory": massline_summary(rows),
        "homepage_versions": [{"year": row["timestamp"][:4], "timestamp": row["timestamp"],
                               "source_url": row["original"], "cdx_length": row.get("length", "")}
                              for row in versions],
        "errors": [],
    }
    out = root / "recovery/massline/index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"report": report, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    (root / "recovery/massline/report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def merge_massline_capture_rows(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Append CDX events without collapsing URL variants, dates, or digests."""
    seen = {(r.get("timestamp"), r.get("original"), r.get("digest"), r.get("statuscode")) for r in existing}
    rows = list(existing)
    for row in incoming:
        key = (row.get("timestamp"), row.get("original"), row.get("digest"), row.get("statuscode"))
        if key not in seen:
            rows.append(row)
            seen.add(key)
    return sorted(rows, key=lambda r: (r.get("timestamp", ""), r.get("original", ""), r.get("digest", "")))


def index_massline_history(root: Path, max_pages: int = 1, delay: float = 0.8, timeout: int = 60) -> dict:
    """Page through the uncollapsed Wayback CDX history, checkpointing every response."""
    if max_pages < 1 or delay < 0 or timeout < 1:
        raise ValueError("Invalid Massline history limits")
    root = Path(root)
    path = root / HISTORY_PATH
    history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "query": "masslinemedia.com/*", "rows": [], "pages": 0, "resume_key": None,
        "complete": False, "errors": []}
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical research; paced requests)"
    pages = 0
    while pages < max_pages and not history.get("complete"):
        params = {
            "url": "masslinemedia.com/*", "output": "json", "filter": "statuscode:200",
            "fl": "timestamp,original,mimetype,statuscode,digest,length",
            "showResumeKey": "true", "limit": "20000",
        }
        cursor = history.get("resume_key")
        if cursor:
            params["resumeKey"] = cursor
        time.sleep(delay)
        try:
            response = session.get(CDX_ENDPOINT, params=params, timeout=timeout)
            if response.status_code != 200:
                raise OSError(f"Wayback CDX HTTP {response.status_code}")
            new_rows, next_cursor = parse_cdx(response.text)
            merged = merge_massline_capture_rows(history.get("rows", []), new_rows)
            if cursor and next_cursor == cursor:
                raise ValueError("Wayback CDX returned the same resume key twice")
            history.update({
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "rows": merged, "resume_key": next_cursor,
                "complete": next_cursor is None,
            })
            history["pages"] = int(history.get("pages", 0)) + 1
            history["errors"] = []
            pages += 1
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as exc:
            history["errors"] = [f"{type(exc).__name__}: {exc}"]
            history["generated_at"] = datetime.now(timezone.utc).isoformat()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            break
    return {"rows": len(history.get("rows", [])), "pages_total": history.get("pages", 0),
            "pages_this_run": pages, "complete": bool(history.get("complete")),
            "resume_key_present": bool(history.get("resume_key")), "errors": history.get("errors", []),
            "saved_to": HISTORY_PATH.as_posix()}


def _kind(row: dict) -> str:
    mime = row.get("mimetype", "").lower()
    if mime == "text/html":
        return "html"
    if mime == "text/css":
        return "css"
    if mime.startswith("image/"):
        return "image"
    if mime.startswith(("audio/", "video/")) or mime in ("application/octet-stream", "application/x-shockwave-flash"):
        return "media"
    if "javascript" in mime:
        return "script"
    return "text"


def _extension(row: dict, kind: str) -> str:
    path = urlsplit(row["original"]).path
    suffix = Path(unquote(path)).suffix.lower()
    if suffix and re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        return suffix
    return {"html": ".html", "css": ".css", "image": ".img", "media": ".bin", "script": ".js", "text": ".txt"}[kind]


def _priority(row: dict) -> tuple[int, str, str]:
    url = row.get("original", "")
    parts = urlsplit(url)
    path = parts.path.lower()
    query = parts.query.lower()
    if path in ("/", "/index.html") or "/artists/" in path or "/commonmarket/" in path:
        band = 0
    elif _kind(row) in ("image", "media") or row.get("mimetype", "").startswith("text/css"):
        # Capture visible site assets before the very large SMF page queue.
        band = 1
    elif path.startswith("/smf/") and ("board=" in query or "topic=" in query):
        band = 2
    elif path.startswith("/smf/"):
        band = 3
    else:
        band = 4
    return band, row.get("timestamp", ""), url


def recover_massline(root: Path, max_files: int = 250, delay: float = 0.6, retry_failed: bool = False, progress=None) -> dict:
    """Fetch a bounded, resumable batch of archived pages and local dependencies."""
    root = Path(root)
    index_path = root / "recovery/massline/index.json"
    if not index_path.exists():
        index_massline(root)
    indexed = json.loads(index_path.read_text(encoding="utf-8"))
    manifest_path = root / "recovery/massline/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "resources": {}, "homepage_variants": [], "failures": [], "skipped": []}
    resources = manifest["resources"]
    variants = {item.get("year"): item for item in manifest.get("homepage_variants", [])}
    failures = {item["source_url"]: item for item in manifest.get("failures", [])}
    skipped = {item["source_url"]: item for item in manifest.get("skipped", [])}
    full_history_path = root / HISTORY_PATH
    full_history = json.loads(full_history_path.read_text(encoding="utf-8")) if full_history_path.exists() else {}
    if full_history.get("complete"):
        selected_rows = select_latest_massline_rows(full_history.get("rows", []))
        index_row_count = len(full_history.get("rows", []))
    else:
        selected_rows = select_latest_massline_rows(indexed["rows"])
        index_row_count = len(indexed["rows"])
    rows = sorted(selected_rows, key=_priority)
    eligible = [row for row in rows if row.get("mimetype") not in (
        "application/x-javascript", "application/javascript", "application/x-shockwave-flash")]
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation; paced requests)"
    client = ArchiveClient(session=session, delay=delay, retries=3, timeout=40, max_bytes=32_000_000)
    attempted = 0
    history_path = root / "recovery/massline/homepage-history.json"
    history_rows = json.loads(history_path.read_text(encoding="utf-8")).get("rows", []) if history_path.exists() else []
    for row in select_massline_homepage_versions(history_rows):
        year = row["timestamp"][:4]
        existing = variants.get(year, {})
        if existing.get("status") == "recovered" and (root / existing.get("raw_path", "missing")).is_file():
            continue
        if attempted >= max_files:
            break
        attempted += 1
        source = f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}"
        try:
            payload = client.get(source)
            validate_payload(payload.body, "html")
            text = payload.body.decode("utf-8", errors="replace").lower()
            if any(term in text[:8000] for term in ("casino bonus", "viagra", "cialis", "domain is for sale")):
                raise ValueError("Captured page is spam or a parked-domain response")
            digest = sha256(payload.body).hexdigest()
            raw_path = Path("recovery/massline/raw") / f"homepage-{year}-{digest}.html"
            destination = root / raw_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(payload.body)
            variants[year] = {"year": year, "source_url": row["original"], "canonical_url": _canonical(row["original"]),
                              "timestamp": row["timestamp"], "kind": "html", "mimetype": row.get("mimetype", "text/html"),
                              "source": source, "status": "recovered", "raw_path": raw_path.as_posix(),
                              "sha256": digest, "bytes": len(payload.body), "content_type": payload.headers.get("Content-Type", "")}
        except Exception as exc:
            variants[year] = {"year": year, "source_url": row["original"], "timestamp": row["timestamp"],
                              "status": "failed", "error": f"{type(exc).__name__}: {exc}", "source": source}
        manifest["homepage_variants"] = [variants[y] for y in sorted(variants)]
        _write_massline_manifest(manifest_path, manifest)
    for row in eligible:
        canonical = _canonical(row.get("original", ""))
        if not canonical:
            continue
        existing = resources.get(canonical)
        if existing and existing.get("timestamp") == row.get("timestamp"):
            continue
        failed = failures.get(canonical)
        if failed and failed.get("timestamp") == row.get("timestamp") and not retry_failed:
            continue
        attempted += 1
        kind = _kind(row)
        record = {
            "source_url": row["original"], "canonical_url": canonical,
            "timestamp": row["timestamp"], "mimetype": row.get("mimetype", ""),
            "kind": kind, "cdx_length": row.get("length", ""),
            "source": f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}",
            "status": "queued",
        }
        if kind == "script":
            skipped[canonical] = {**record, "status": "preserved_as_cdx_metadata_only", "reason": "Archived executable files are not fetched or run by this static restoration."}
            manifest["skipped"] = list(skipped.values())
            attempted -= 1
            continue
        try:
            payload = client.get(record["source"])
            if kind in ("html", "css", "image"):
                validate_payload(payload.body, kind)
            elif kind == "media" and (not payload.body or len(payload.body) < 300):
                raise ValueError("Captured media response is empty or implausibly short")
            elif kind == "text" and len(payload.body) < 64:
                raise ValueError("Captured text response is empty or implausibly short")
            if kind == "html":
                text = payload.body.decode("utf-8", errors="replace").lower()
                if any(term in text[:8000] for term in ("casino bonus", "viagra", "cialis", "domain is for sale")):
                    raise ValueError("Captured page is spam or a parked-domain response")
            digest = sha256(payload.body).hexdigest()
            suffix = _extension(row, kind)
            raw_path = Path("recovery/massline/raw") / (digest + suffix)
            destination = root / raw_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(payload.body)
            if existing and existing.get("timestamp") != row.get("timestamp"):
                variants_for_url = manifest.setdefault("resource_variants", [])
                existing_identity = (canonical, existing.get("timestamp"), existing.get("sha256"))
                known = {(item.get("canonical_url"), item.get("timestamp"), item.get("sha256")) for item in variants_for_url}
                if existing_identity not in known:
                    variants_for_url.append(existing)
            resources[canonical] = {
                **record, "status": "recovered", "actual_url": payload.url,
                "raw_path": raw_path.as_posix(), "sha256": digest,
                "bytes": len(payload.body), "content_type": payload.headers.get("Content-Type", ""),
            }
            failures.pop(canonical, None)
        except Exception as exc:
            failures[canonical] = {**record, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        manifest["failures"] = list(failures.values())
        manifest["skipped"] = list(skipped.values())
        _write_massline_manifest(manifest_path, manifest)
        if progress and (attempted % 25 == 0 or attempted >= max_files):
            progress({"attempted": attempted, "recovered": len(resources), "failures": len(failures), "source_url": row["original"]})
        if attempted >= max_files:
            break
    current_resources = sum(
        resources.get(_canonical(row.get("original", "")), {}).get("timestamp") == row.get("timestamp")
        for row in eligible
    )
    current_failures = sum(
        any(f.get("timestamp") == row.get("timestamp") and _canonical(f.get("source_url", "")) == _canonical(row.get("original", ""))
            for f in failures.values())
        for row in eligible
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_rows": index_row_count, "urlkey_rows": len(indexed["rows"]), "eligible_rows": len(eligible),
        "recovered": len(resources), "homepage_variants": sum(v.get("status") == "recovered" for v in variants.values()),
        "failed": len(failures), "skipped": len(skipped),
        "alternate_source_versions_preserved": len(manifest.get("resource_variants", [])),
        "remaining": max(0, len(eligible) - current_resources - current_failures),
        "complete": current_resources + current_failures >= len(eligible),
        "batch_attempted": attempted,
        "source_period_end": "2009-08-31",
        "resume": "python -m restore massline-recover --max-files 250 --delay 0.4",
        "coverage_note": indexed["report"]["coverage_note"],
    }
    manifest["report"] = report
    _write_massline_manifest(manifest_path, manifest)
    _write_massline_report(root, report, manifest)
    return report


def _write_massline_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_massline_report(root: Path, report: dict, manifest: dict) -> None:
    path = root / "docs/recovery-report/massline-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    index_path = root / "recovery/massline/index.json"
    index_report = json.loads(index_path.read_text(encoding="utf-8"))["report"] if index_path.exists() else {}
    external_index_path = root / "recovery/massline/external/assets.json"
    external_index = json.loads(external_index_path.read_text(encoding="utf-8")) if external_index_path.exists() else {"assets": []}
    external_assets = external_index.get("assets", [])
    external_resources = manifest.get("external_resources", {})
    external_summary = {
        "discovered": len(external_assets),
        "indexed": sum(item.get("status") == "indexed" for item in external_assets),
        "capture_records_found": sum(item.get("status") in ("indexed", "recovered", "download_failed", "no_valid_capture") for item in external_assets),
        "invalid_capture": sum(item.get("status") == "no_valid_capture" for item in external_assets),
        "no_captures": sum(item.get("status") == "no_captures" for item in external_assets),
        "index_failed": sum(item.get("status") == "index_failed" for item in external_assets),
        "download_failed": sum(item.get("status") == "download_failed" for item in external_assets),
        "queued": sum(item.get("status") == "queued" for item in external_assets),
        "recovered": len(external_resources),
        "images": sum(item.get("kind") == "image" for item in external_resources.values()),
        "media": sum(item.get("kind") == "media" for item in external_resources.values()),
        "bytes": sum(int(item.get("bytes", 0)) for item in external_resources.values()),
        "cooldown_until": external_index.get("cooldown_until"),
    }
    payload = {**report, "index": index_report, "external_assets": external_summary, "resources": {
        "html": sum(r.get("kind") == "html" for r in manifest["resources"].values()),
        "css": sum(r.get("kind") == "css" for r in manifest["resources"].values()),
        "images": sum(r.get("kind") == "image" for r in manifest["resources"].values()),
        "media": sum(r.get("kind") == "media" for r in manifest["resources"].values()),
        "homepage_versions": sum(v.get("status") == "recovered" for v in manifest.get("homepage_variants", [])),
        "bytes": sum(int(r.get("bytes", 0)) for r in manifest["resources"].values()),
    }, "failures": manifest.get("failures", []), "skipped": manifest.get("skipped", [])}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    inventory = index_report.get("inventory", {})
    resources = payload["resources"]
    lines = [
        "# Mass Line Media archive recovery",
        "",
        "This is a separate historical source collection for `masslinemedia.com`; its forum is preserved as its own browsable area. Captured pages retain source URLs, exact archive timestamps, byte counts, and SHA-256 hashes. Wayback raw bytes are under `recovery/massline/raw/`; linked offsite assets are under `recovery/massline/external/raw/`.",
        "",
        "## Archive evidence",
        "",
        f"- The collapsed CDX index has **{inventory.get('source_rows', 0):,} URL records**; the separate uncollapsed query has **{index_report.get('full_capture_rows', 0):,} capture events**. Of the URL records, **{inventory.get('forum_html_pages', 0):,}** are HTML under `/smf/`, **{inventory.get('forum_topic_urls', 0):,}** have a topic query, **{inventory.get('topic_ids', 0):,}** topic IDs appear, and **{inventory.get('board_ids', 0)}** board IDs appear.",
        f"- The root-history queries yielded **{len(json.loads((root / 'recovery/massline/homepage-history.json').read_text(encoding='utf-8')).get('rows', [])) if (root / 'recovery/massline/homepage-history.json').exists() else 0}** distinct homepage capture records. Representative root captures were inspected individually across 2006–2026.",
        "- The latest substantial authentic Mass Line homepage inspected is the 2009 capture below. The later root captures inspected are parked, unrelated replacement, domain-sale, or JavaScript/challenge pages, so they are retained as index evidence and excluded from the restoration.",
        "",
        "## Homepage captures selected",
        "",
    ]
    for variant in manifest.get("homepage_variants", []):
        if variant.get("status") == "recovered":
            lines.append(f"- **{variant['year']}** — `{variant['timestamp']}`; {variant.get('bytes', 0):,} bytes; [captured source]({variant['source']})")
        else:
            lines.append(f"- **{variant.get('year')}** — `{variant.get('timestamp', '')}`; not recovered: {variant.get('error', 'pending')}")
    lines += [
        "",
        "## Recovery status",
        "",
        f"- Saved: **{report.get('recovered', 0):,}** indexed resources plus **{resources.get('homepage_versions', 0)}** homepage versions ({resources.get('html', 0)} HTML pages, {resources.get('images', 0)} images, {resources.get('css', 0)} stylesheets, {resources.get('media', 0)} media files; {resources.get('bytes', 0):,} bytes).",
        f"- Unavailable or invalid responses: **{report.get('failed', 0)}**; pending indexed resources: **{report.get('remaining', 0):,}**. Current crawl complete: **{str(bool(report.get('complete'))).lower()}**.",
        "- Captured images and styles are mapped locally. Scripts are never run; forms and embedded players are disabled in the static copy. Explicit source links may open the source archive when an item is not stored locally.",
        f"- External assets referenced by recovered pages: **{external_summary['discovered']:,}** exact URLs discovered; **{external_summary['capture_records_found']:,}** have Wayback capture records ({external_summary['indexed']:,} indexed and awaiting download, {external_summary['recovered']:,} recovered); **{external_summary['no_captures']:,}** returned no capture, **{external_summary['invalid_capture']:,}** had only non-image/error payloads, **{external_summary['index_failed']:,}** index queries and **{external_summary['download_failed']:,}** payloads are retryable failures, and **{external_summary['queued']:,}** remain queued. Locally captured: **{external_summary['recovered']:,}** ({external_summary['images']} images, {external_summary['media']} media files; {external_summary['bytes']:,} bytes).",
        "- Independent archives: Common Crawl `CC-MAIN-2009-2010` supplied a separately preserved July 4, 2009 homepage; Arquivo.pt returned no forum captures and its two site records replay as HTML fallback pages. Detailed queries and raw observations are under `recovery/massline/external/`.",
        "- The raw media files are archival source material; archive availability is not a redistribution license. The candidate is not promoted into the reviewed source catalog and is not a release or human review. No Pages deployment was made as part of this recovery step.",
        "",
        "## Resume",
        "",
        "```bash",
        "python -m restore massline-index",
        "python -m restore massline-history --max-pages 1",
        "python -m restore massline-recover --max-files 250 --delay 0.4",
        "python -m restore massline-external-index --max-assets 50 --delay 2.0",
        "python -m restore massline-external-recover --max-files 40 --delay 0.6",
        "python -m restore build --candidate --base-path /bluescholars",
        "python -m restore check --candidate --base-path /bluescholars",
        "```",
        "",
        "The uncollapsed event inventory is saved in `recovery/massline/all-captures.json`; do not describe the collapsed URL count as every capture event. The current page builder chooses the latest captured URL response on or before August 31, 2009 and stores superseded downloaded versions separately.",
        "",
    ]
    (root / "docs/recovery-report/massline-report.md").write_text("\n".join(lines), encoding="utf-8")


def _local_target(value: str, base_url: str, mapping: dict[str, str]) -> str | None:
    canonical = _canonical(value, base_url)
    if not canonical:
        return None
    local = mapping.get(canonical)
    if local:
        return local
    # The older source inventory often stores HTTP URLs while later external
    # asset indexes preserve HTTPS. The same archived path should resolve in
    # either spelling without making the browser fetch the remote original.
    if canonical.startswith("http://"):
        return mapping.get("https://" + canonical[len("http://"):])
    return None


def _youtube_video_id(node) -> str | None:
    candidates = [node.get("src", ""), node.get("data", "")]
    candidates.extend(child.get("value", "") for child in node.find_all("param"))
    candidates.extend(child.get("src", "") for child in node.find_all(["iframe", "embed", "source"]))
    for value in candidates:
        try:
            parts = urlsplit(value)
        except ValueError:
            continue
        host = (parts.hostname or "").lower()
        if host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            continue
        match = re.search(r"/(?:v|embed)/([A-Za-z0-9_-]{11})(?:/|$)", parts.path)
        if match:
            return match.group(1)
        video_id = parse_qs(parts.query).get("v", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return video_id
    return None


def rewrite_massline_css(source: str, source_url: str, mapping: dict[str, str], base: str = "") -> str:
    """Keep historical CSS while constraining every automatic dependency to saved local bytes."""
    def replace_url(match):
        value = match.group(2).strip(" \t\"'")
        local = _local_target(value, source_url, mapping)
        return "url('" + (base.rstrip("/") + local if local else "data:,") + "')"
    css = re.sub(r"url\(\s*(['\"]?)(.*?)\1\s*\)", replace_url, source, flags=re.I)
    def replace_import(match):
        local = _local_target(match.group(2), source_url, mapping)
        return "@import url('" + (base.rstrip("/") + local if local else "data:,") + "');"
    css = re.sub(r"@import\s+(?:url\()?\s*(['\"])(.*?)\1\s*\)?\s*;", replace_import, css, flags=re.I)
    css = re.sub(r"(?:-moz-binding|behavior)\s*:[^;{}]+;?", "", css, flags=re.I)
    css = re.sub(r"expression\s*\([^)]*\)", "initial", css, flags=re.I)
    return css


def sanitize_massline_html(source: str, source_url: str, mapping: dict[str, str], capture: str = "", base: str = "",
                           source_link: str | None = None, source_label: str = "view source replay") -> tuple[str, list[str]]:
    """Keep captured text and layout while removing executable and remote behavior."""
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
    gaps: list[str] = []
    for node in list(soup.find_all(["script", "base", "iframe", "object", "embed", "video", "audio"])):
        if not any(parent is soup for parent in node.parents):
            continue
        if node.name in ("iframe", "object", "embed", "video", "audio"):
            target = node.get("src") or node.get("data") or ""
            video_id = _youtube_video_id(node)
            if not target and node.name == "object":
                param = node.find("param", attrs={"name": re.compile("^movie$", re.I)})
                target = param.get("value", "") if param else ""
            if not target and video_id:
                target = f"https://www.youtube.com/watch?v={video_id}"
            if target:
                gaps.append(_canonical(target, source_url))
            note = soup.new_tag("p", attrs={"class": "massline-embed-gap"})
            note.append("Archived embedded media is unavailable for offline playback.")
            if video_id:
                anchor = soup.new_tag("a", href=f"https://www.youtube.com/watch?v={video_id}",
                                      rel=["noopener", "noreferrer"], attrs={"class": "massline-external-playback"})
                thumb = _local_target(f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg", source_url, mapping)
                if thumb:
                    image = soup.new_tag("img", src=base.rstrip("/") + thumb,
                                         alt=f"Archived thumbnail for video {video_id}",
                                         attrs={"class": "massline-local-asset"})
                    anchor.append(image)
                    anchor.append(soup.new_tag("br"))
                anchor.append(f"Open video {video_id} on YouTube (external playback)")
                note.append(" ")
                note.append(anchor)
            node.replace_with(note)
        else:
            node.decompose()
    for form in list(soup.find_all("form")):
        note = soup.new_tag("p", attrs={"class": "massline-form-gap"})
        note.string = "Historical posting form disabled in this preservation copy."
        form.replace_with(note)
    for meta in list(soup.find_all("meta", attrs={"http-equiv": re.compile("^refresh$", re.I)})):
        meta.decompose()
    for node in soup.find_all(True):
        if node.attrs is None:
            continue
        for attr in list(node.attrs):
            if attr.lower().startswith("on"):
                del node.attrs[attr]
            elif attr.lower() == "href" and node.name not in ("a", "area", "link"):
                node.attrs.pop(attr, None)
            elif attr.lower() == "background":
                node.attrs.pop(attr, None)
            elif attr.lower() == "src" and node.name not in ("img", "source"):
                node.attrs.pop(attr, None)
        if node.name in ("a", "area") and node.get("href"):
            if "massline-external-playback" in node.get("class", []):
                node["rel"] = ["noopener", "noreferrer"]
                continue
            original = node.get("href", "")
            local = _local_target(original, source_url, mapping)
            if local:
                node["href"] = base.rstrip("/") + local
            else:
                canonical = _canonical(original, source_url)
                if canonical and capture.isdigit():
                    node["href"] = f"https://web.archive.org/web/{capture}/{canonical}"
                    node["rel"] = ["noopener", "noreferrer"]
                    node["class"] = list(node.get("class", [])) + ["massline-external-gap"]
                else:
                    node.unwrap()
        elif node.name == "link":
            href = node.get("href", "")
            if href and "stylesheet" in node.get("rel", []):
                local = _local_target(href, source_url, mapping)
                if local:
                    node["href"] = base.rstrip("/") + local
                else:
                    node.decompose()
            elif node.get("href"):
                local = _local_target(href, source_url, mapping)
                if local and any(r in node.get("rel", []) for r in ("icon", "shortcut", "apple-touch-icon")):
                    node["href"] = base.rstrip("/") + local
                else:
                    node.decompose()
        elif node.name in ("img", "source"):
            for attr in ("src", "poster"):
                if not node.get(attr):
                    continue
                if attr == "src" and "massline-local-asset" in node.get("class", []):
                    continue
                local = _local_target(node[attr], source_url, mapping)
                if local:
                    node[attr] = base.rstrip("/") + local
                else:
                    gaps.append(_canonical(node[attr], source_url))
                    node.attrs.pop(attr, None)
                    if node.name == "img":
                        node["alt"] = node.get("alt") or "Archived image unavailable"
            if node.get("srcset"):
                picks = []
                for item in node["srcset"].split(","):
                    parts = item.strip().split()
                    if parts:
                        local = _local_target(parts[0], source_url, mapping)
                        if local:
                            picks.append(" ".join([base.rstrip("/") + local, *parts[1:]]))
                if picks:
                    node["srcset"] = ", ".join(picks)
                else:
                    node.attrs.pop("srcset", None)
        if node.attrs is not None and node.get("style") and re.search(r"url\s*\(|@import|expression\s*\(", str(node["style"]), re.I):
            del node["style"]
    for style in list(soup.find_all("style")):
        style.string = rewrite_massline_css(style.get_text(), source_url, mapping, base)
    if capture.isdigit():
        note = soup.new_tag("aside", attrs={"class": "massline-source-note"})
        note.string = f"Historical capture · {capture[:4]}-{capture[4:6]}-{capture[6:8]} · "
        link = soup.new_tag("a", href=source_link or f"https://web.archive.org/web/{capture}/{source_url}",
                            rel="noopener noreferrer")
        link.string = source_label
        note.append(link)
        soup.body.insert(0, note)
    return "<!doctype html>\n" + str(soup), gaps


def _write_output(output: Path, route: str, body: bytes | str) -> None:
    target = output / route.lstrip("/")
    if route.endswith("/"):
        target = target / "index.html"
    elif not target.suffix:
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))


def _variant_route(url: str, timestamp: str, kind: str) -> str:
    if kind == "html":
        route = massline_route(url)
    else:
        route = f"/masslinemedia/assets/{sha256(url.encode()).hexdigest()[:20]}{_extension({'original': url}, kind)}"
    path = Path(route)
    suffix = path.suffix or ".html"
    return str(path.with_name(path.stem + "--capture-" + timestamp + suffix))


def build_massline_archive(root: Path, output: Path, base: str = "", candidate: bool = False) -> dict:
    """Build a browseable offline copy from recovered candidate or reviewed bytes."""
    root, output = Path(root), Path(output)
    manifest_path = root / ("recovery/massline/manifest.json" if candidate else "source/massline.json")
    if not manifest_path.exists():
        return {"status": "not_in_source_catalog", "recovered_pages": 0, "forum_topics": 0}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resources = {**manifest.get("resources", {}), **manifest.get("external_resources", {})}
    mapping: dict[str, str] = {}
    body_by_url: dict[str, bytes] = {}
    for canonical, record in resources.items():
        raw = (root / record["raw_path"]).resolve()
        allowed = [(root / "recovery/massline/raw").resolve(),
                   (root / "recovery/massline/external/raw").resolve(),
                   (root / "source/massline/raw").resolve()]
        if not any(raw.is_relative_to(parent) for parent in allowed) or not raw.is_file():
            continue
        body = raw.read_bytes()
        if sha256(body).hexdigest() != record.get("sha256"):
            continue
        if (record.get("kind") == "html" and
                Path(urlsplit(canonical).path).suffix.lower() in {".gif", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ico"}):
            # Preserve HTML challenges at image URLs only as raw evidence, never as displayed images.
            continue
        route = massline_route(canonical) if record.get("kind") == "html" else f"/masslinemedia/assets/{sha256(canonical.encode()).hexdigest()[:20]}{_extension({'original': canonical}, record.get('kind', 'text'))}"
        mapping[canonical] = route
        body_by_url[canonical] = body
    recovered_resource_variants = []
    for variant in manifest.get("resource_variants", []):
        raw = (root / variant.get("raw_path", "missing")).resolve()
        allowed = [(root / "recovery/massline/raw").resolve(),
                   (root / "recovery/massline/external/raw").resolve(),
                   (root / "source/massline/raw").resolve()]
        if not any(raw.is_relative_to(parent) for parent in allowed) or not raw.is_file():
            continue
        body = raw.read_bytes()
        if sha256(body).hexdigest() != variant.get("sha256"):
            continue
        kind = variant.get("kind", "")
        if kind not in ("html", "css", "image", "media"):
            continue
        variant_route = _variant_route(variant.get("canonical_url") or variant.get("source_url", ""),
                                       variant.get("timestamp", ""), kind)
        recovered_resource_variants.append((variant, body, variant_route))
    homepage_variants = []
    for variant in manifest.get("homepage_variants", []):
        if variant.get("status") != "recovered":
            continue
        raw = (root / variant["raw_path"]).resolve()
        allowed = [(root / "recovery/massline/raw").resolve(),
                   (root / "recovery/massline/external/raw").resolve(),
                   (root / "source/massline/raw").resolve()]
        if not any(raw.is_relative_to(parent) for parent in allowed) or not raw.is_file():
            continue
        body = raw.read_bytes()
        if sha256(body).hexdigest() != variant.get("sha256"):
            continue
        homepage_variants.append((variant, body))
    page_gaps = []
    routes: dict[str, str] = {}
    for canonical, record in resources.items():
        body = body_by_url.get(canonical)
        if body is None:
            continue
        route = mapping.get(canonical)
        if not route:
            continue
        kind = record.get("kind")
        if kind == "html":
            rendered, gaps = sanitize_massline_html(body.decode("utf-8", errors="replace"), canonical, mapping, record.get("timestamp", ""), base)
            page_gaps.extend({"page": canonical, "url": gap} for gap in gaps if gap)
            _write_output(output, route.removeprefix(base), rendered)
            routes[canonical] = route
        elif kind == "image":
            if b"<svg" in body[:1000].lower():
                body = sanitize_svg(body)
            _write_output(output, route.removeprefix(base), body)
        elif kind == "css":
            css = rewrite_massline_css(body.decode("utf-8", errors="replace"), canonical, mapping, base)
            _write_output(output, route.removeprefix(base), css)
        elif kind == "media":
            _write_output(output, route.removeprefix(base), body)
    for variant, body, route in recovered_resource_variants:
        if variant.get("kind") == "html":
            canonical = variant.get("canonical_url") or _canonical(variant.get("source_url", ""))
            rendered, gaps = sanitize_massline_html(body.decode("utf-8", errors="replace"), canonical, mapping,
                                                      variant.get("timestamp", ""), base,
                                                      variant.get("source"), variant.get("source_label", "view source replay"))
            page_gaps.extend({"page": canonical, "url": gap} for gap in gaps if gap)
            _write_output(output, route, rendered)
        elif variant.get("kind") == "image":
            if b"<svg" in body[:1000].lower():
                body = sanitize_svg(body)
            _write_output(output, route, body)
        elif variant.get("kind") == "css":
            css = rewrite_massline_css(body.decode("utf-8", errors="replace"),
                                       variant.get("canonical_url") or variant.get("source_url", ""), mapping, base)
            _write_output(output, route, css)
        elif variant.get("kind") == "media":
            _write_output(output, route, body)
    for variant, body in homepage_variants:
        rendered, gaps = sanitize_massline_html(body.decode("utf-8", errors="replace"), variant["canonical_url"], mapping,
                                                  variant.get("timestamp", ""), base,
                                                  variant.get("source"), variant.get("source_label", "view source replay"))
        page_gaps.extend({"page": variant["canonical_url"], "url": gap} for gap in gaps if gap)
        _write_output(output, f"/masslinemedia/site/home-{variant['year']}.html", rendered)
    html_records = [(url, item) for url, item in resources.items() if item.get("kind") == "html" and url in routes]
    board_rows = []
    topic_rows = []
    site_rows = []
    for url, record in html_records:
        parts = urlsplit(url)
        query = parse_qs(parts.query.replace(";", "&"), keep_blank_values=True)
        body = body_by_url[url]
        soup = BeautifulSoup(body, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else Path(parts.path).name
        title = title or "Untitled archived page"
        item = {"url": url, "route": routes[url], "title": title, "timestamp": record.get("timestamp", "")}
        if "topic" in query:
            topic_rows.append(item)
        elif "board" in query:
            board_rows.append(item)
        elif parts.path.startswith("/smf/"):
            continue
        else:
            site_rows.append(item)
    output_base = base.rstrip("/")
    def link(item):
        title = html.escape(item["title"])
        label = item["timestamp"][:8]
        return f'<li><a href="{html.escape(output_base + item["route"], quote=True)}">{title}</a> <small>{label}</small></li>'
    variant_links = ''.join(f'<li><a href="{output_base}/masslinemedia/site/home-{v["year"]}.html">{html.escape(v["year"])} homepage</a> <small>{v.get("timestamp", "")[:8]}</small></li>' for v, _ in homepage_variants)
    index_body = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                  '<title>Mass Line Media archive</title><style>body{max-width:980px;margin:3rem auto;padding:0 1.2rem;font:16px/1.55 system-ui;color:#202020}h1{font-size:clamp(2rem,7vw,4rem);line-height:1}li{margin:.55rem 0}small{color:#666}.archive-list{columns:2}@media(max-width:640px){.archive-list{columns:1}}.note{border-left:4px solid #3985ad;padding:.5rem 1rem;background:#f3f7f8}</style><body>'
                  '<p class="note">Historical restoration from Internet Archive captures. Page dates are shown individually; missing source material remains unfilled.</p>'
                  '<h1>Mass Line Media</h1><p><a href="'+output_base+'/">Back to Blue Scholars archive</a></p>'
                  '<ul><li><a href="'+output_base+'/masslinemedia/site/index.html">Open the latest authentic site homepage (2009)</a></li>'
                  '<li><a href="'+output_base+'/masslinemedia/forum/index.html">Browse the 2007 forum archive</a></li></ul>'
                  '<h2>Dated homepages from the original site era</h2><ul>'+variant_links+'</ul>'
                  '<h2>Other recovered page captures</h2><p><a href="'+output_base+'/masslinemedia/alternate-captures/">Browse '+str(len(recovered_resource_variants))+' separately dated page and asset variants</a></p>'
                  '<h2>Other captured site pages</h2><ul>'+''.join(link(i) for i in sorted(site_rows,key=lambda v:v["route"]))+'</ul>'
                  '</body></html>')
    _write_output(output, "/masslinemedia/index.html", index_body)
    forum_index = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                   '<title>Mass Line Forums archive</title><style>body{max-width:1100px;margin:3rem auto;padding:0 1.2rem;font:16px/1.55 system-ui;color:#202020}li{margin:.5rem 0}small{color:#666}.archive-list{columns:2}@media(max-width:640px){.archive-list{columns:1}}</style><body>'
                   '<p><a href="'+output_base+'/masslinemedia/index.html">Mass Line Media archive</a> · <a href="'+output_base+'/">Blue Scholars archive</a></p>'
                   '<h1>Mass Line Forums</h1><p>Captured forum pages, arranged from the source board and topic URLs. Each link opens an archived page saved locally.</p>'
                   '<h2>Boards</h2><ul>'+''.join(link(i) for i in sorted(board_rows,key=lambda v:v["route"]))+'</ul>'
                   '<h2>Topic and message views</h2><p>'+str(len(topic_rows))+' captured forum URLs</p><ul class="archive-list">'+''.join(link(i) for i in sorted(topic_rows,key=lambda v:v["route"]))+'</ul>'
                   '</body></html>')
    _write_output(output, "/masslinemedia/forum/index.html", forum_index)
    alternate_pages = [
        (variant, body, route) for variant, body, route in recovered_resource_variants
        if variant.get("kind") == "html"
    ]
    alternate_index = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                       '<title>Alternate Mass Line Media captures</title><style>body{max-width:1000px;margin:3rem auto;padding:0 1.2rem;font:16px/1.55 system-ui;color:#202020}li{margin:.5rem 0}small{color:#666}</style><body>'
                       '<p><a href="'+output_base+'/masslinemedia/">Mass Line Media archive</a></p><h1>Other captured page versions</h1>'
                       '<p>These pages preserve earlier captures separately from the latest selected copy. Each page is labeled with its Wayback date.</p><ul>'+
                       ''.join(f'<li><a href="{html.escape(output_base + route, quote=True)}">{html.escape((BeautifulSoup(body, "html.parser").title.get_text(" ", strip=True) if BeautifulSoup(body, "html.parser").title else variant.get("source_url", "Archived page")))}</a> <small>{html.escape(variant.get("timestamp", ""))}</small></li>'
                               for variant, body, route in sorted(alternate_pages, key=lambda item: (item[0].get("timestamp", ""), item[0].get("source_url", ""))))+
                       '</ul></body></html>')
    _write_output(output, "/masslinemedia/alternate-captures/index.html", alternate_index)
    unique_gaps = {}
    for item in page_gaps:
        entry = unique_gaps.setdefault(item["url"], {"url": item["url"], "referenced_by": 0})
        entry["referenced_by"] += 1
    index_path = root / "recovery/massline/index.json"
    inventory = json.loads(index_path.read_text(encoding="utf-8"))["report"].get("inventory", {}) if index_path.exists() else {}
    report = {"status": "built", "candidate": candidate, "recovered_pages": len(html_records) + len(homepage_variants),
              "site_pages": len(site_rows), "forum_topics": len(topic_rows), "forum_boards": len(board_rows),
              "homepage_variants": len(homepage_variants),
              "alternate_resources": len(recovered_resource_variants),
              "alternate_html_pages": len(alternate_pages),
              "inventory": inventory,
              "local_assets": sum(r.get("kind") in ("image", "css", "media") and u in mapping for u, r in resources.items()),
              "missing_embeds": list(unique_gaps.values())}
    (output / "masslinemedia/report.json").parent.mkdir(parents=True, exist_ok=True)
    (output / "masslinemedia/report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
