"""Resumable exact-URL recovery for external assets linked by Mass Line pages."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from .archive import ArchiveClient, validate_payload
from .massline import _canonical, _write_massline_report
from .urls import original_url

EXTERNAL_PATH = Path("recovery/massline/external/assets.json")
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".tif", ".tiff", ".bmp"}
MEDIA_EXTS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".mov", ".m4v", ".flac", ".aif", ".aiff"}


def _canonical_external(value: str, base: str = "") -> str:
    url = original_url(value, base)
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def _kind_for_reference(url: str, tag: str, mime: str = "") -> str | None:
    path = urlsplit(url).path.lower()
    ext = Path(path).suffix
    mime = mime.lower()
    if tag == "img" or ext in IMAGE_EXTS or mime.startswith("image/"):
        return "image"
    if ext in MEDIA_EXTS or mime.startswith(("audio/", "video/")):
        return "media"
    return None


def _source_documents(root: Path, manifest: dict):
    docs = []
    for url, item in manifest.get("resources", {}).items():
        if item.get("kind") == "html" or item.get("kind") == "css":
            docs.append((url, item.get("timestamp", ""), item))
    for item in manifest.get("resource_variants", []):
        if item.get("kind") in ("html", "css"):
            docs.append((item.get("canonical_url") or item.get("source_url", ""), item.get("timestamp", ""), item))
    for item in manifest.get("homepage_variants", []):
        if item.get("status") == "recovered":
            docs.append((item.get("canonical_url") or item.get("source_url", ""), item.get("timestamp", ""), item))
    seen = set()
    for url, timestamp, item in docs:
        raw_path = item.get("raw_path", "")
        path = (root / raw_path).resolve()
        allowed = [(root / "recovery/massline/raw").resolve(), (root / "recovery/massline/external/raw").resolve()]
        if not raw_path or not any(path.is_relative_to(parent) for parent in allowed) or not path.is_file():
            continue
        body = path.read_bytes()
        if item.get("sha256") and sha256(body).hexdigest() != item["sha256"]:
            continue
        key = (url, timestamp, item.get("sha256"))
        if key in seen:
            continue
        seen.add(key)
        yield url, timestamp, item, body


def discover_external_assets(root: Path) -> list[dict]:
    """Find source-linked image/audio/video files in validated Mass Line pages and stylesheets."""
    root = Path(root)
    manifest_path = root / "recovery/massline/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    found: dict[str, dict] = {}
    for page_url, timestamp, item, body in _source_documents(root, manifest):
        kind = item.get("kind")
        refs = []
        if kind == "html":
            soup = BeautifulSoup(body, "html.parser")
            for tag in soup.find_all(["img", "source", "audio", "video", "embed", "object", "a"]):
                tag_name = tag.name
                attrs = ("src", "data-src", "data-original", "href", "data")
                values = [tag.get(attr) for attr in attrs if tag.get(attr)]
                if tag.get("srcset"):
                    values.extend(part.strip().split()[0] for part in tag["srcset"].split(",") if part.strip())
                for value in values:
                    if value.startswith(("javascript:", "mailto:", "#", "data:")):
                        continue
                    absolute = _canonical_external(value, page_url)
                    if not absolute:
                        continue
                    parts = urlsplit(absolute)
                    host = (parts.hostname or "").lower()
                    if host.endswith("masslinemedia.com") or host in {"web.archive.org", "archive.org", "web-static.archive.org"}:
                        continue
                    ref_kind = _kind_for_reference(absolute, tag_name, tag.get("type", ""))
                    if ref_kind:
                        refs.append((absolute, ref_kind, tag_name))
        elif kind == "css":
            text = body.decode("utf-8", errors="replace")
            for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", text, re.I):
                value = match.group(2).strip()
                absolute = _canonical_external(value, page_url)
                if not absolute:
                    continue
                host = (urlsplit(absolute).hostname or "").lower()
                if host.endswith("masslinemedia.com") or host in {"web.archive.org", "archive.org", "web-static.archive.org"}:
                    continue
                ref_kind = _kind_for_reference(absolute, "css")
                if ref_kind:
                    refs.append((absolute, ref_kind, "css-url"))
        for url, ref_kind, tag_name in refs:
            record = found.setdefault(url, {"url": url, "kind": ref_kind, "references": [], "captures": [], "status": "queued"})
            reference = {"page": page_url, "timestamp": timestamp, "tag": tag_name}
            if reference not in record["references"]:
                record["references"].append(reference)
    return sorted(found.values(), key=lambda item: item["url"])


def _read_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "provider": "Internet Archive Wayback CDX", "generated_at": None,
            "discovery_count": 0, "assets": [], "errors": []}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def external_asset_priority(item: dict) -> tuple[int, int, str]:
    """Prioritize images used by more preserved pages, then keep processing deterministic."""
    return (-len(item.get("references", [])), 0 if item.get("kind") == "image" else 1, item.get("url", ""))



def retry_after_deadline(value: str | None, now: datetime | None = None) -> str:
    """Return an RFC-compatible UTC cooldown deadline, defaulting to one minute."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    seconds = None
    if value:
        try:
            seconds = max(0.0, float(value))
        except ValueError:
            try:
                target = parsedate_to_datetime(value)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=timezone.utc)
                seconds = max(0.0, (target - now).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
    return (now + timedelta(seconds=seconds if seconds is not None else 60)).isoformat()



def _refresh_report(root: Path) -> None:
    manifest_path = Path(root) / "recovery/massline/manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _write_massline_report(Path(root), manifest.get("report", {}), manifest)


def index_external_assets(root: Path, max_assets: int = 50, delay: float = 0.8, timeout: int = 45,
                          progress=None, refresh_discovery: bool = False) -> dict:
    """Index exact source-linked external asset URLs; each result checkpoints independently."""
    if max_assets < 1 or delay < 0 or timeout < 1:
        raise ValueError("Invalid external-asset index limits")
    root = Path(root)
    path = root / EXTERNAL_PATH
    state = _read_state(path)
    current = discover_external_assets(root) if refresh_discovery or not state.get("assets") else []
    by_url = {item["url"]: item for item in state.get("assets", [])}
    for item in current:
        old = by_url.get(item["url"])
        if old:
            refs = old.setdefault("references", [])
            for ref in item["references"]:
                if ref not in refs:
                    refs.append(ref)
            old["kind"] = item["kind"]
        else:
            by_url[item["url"]] = item
    state["assets"] = sorted(by_url.values(), key=lambda item: item["url"])
    state["discovery_count"] = len(state["assets"])
    cooldown_until = state.get("cooldown_until")
    if cooldown_until:
        try:
            deadline = datetime.fromisoformat(cooldown_until)
        except ValueError:
            deadline = datetime.min.replace(tzinfo=timezone.utc)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if deadline > datetime.now(timezone.utc):
            _refresh_report(root)
            return {"assets": len(state["assets"]), "indexed": sum(a.get("status") == "indexed" for a in state["assets"]),
                    "no_captures": sum(a.get("status") == "no_captures" for a in state["assets"]),
                    "index_failed": sum(a.get("status") == "index_failed" for a in state["assets"]),
                    "queued": sum(a.get("status") == "queued" for a in state["assets"]), "attempted": 0,
                    "cooldown_until": cooldown_until, "saved_to": EXTERNAL_PATH.as_posix()}
        state.pop("cooldown_until", None)
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (source-linked external asset index; paced requests)"
    attempted = 0
    for item in sorted(state["assets"], key=external_asset_priority):
        if attempted >= max_assets:
            break
        if item.get("status") not in ("queued", "index_failed"):
            continue
        attempted += 1
        time.sleep(delay)
        params = {"url": item["url"], "output": "json", "filter": "statuscode:200",
                  "fl": "timestamp,original,mimetype,statuscode,digest,length"}
        query = CDX_ENDPOINT + "?" + urlencode(params)
        try:
            response = session.get(query, timeout=timeout)
            if response.status_code == 429:
                item.update({"status": "index_failed", "index_query": query,
                             "index_error": "Wayback CDX HTTP 429; query paused to respect archive rate limit",
                             "indexed_at": datetime.now(timezone.utc).isoformat()})
                state["cooldown_until"] = retry_after_deadline(response.headers.get("Retry-After"))
                state["generated_at"] = datetime.now(timezone.utc).isoformat()
                state["assets"] = sorted(by_url.values(), key=lambda asset: asset["url"])
                _write_state(path, state)
                break
            if response.status_code != 200:
                raise OSError(f"Wayback CDX HTTP {response.status_code}")
            data = response.json() if response.text.strip() else []
            if data and isinstance(data[0], list):
                fields = data[0]
                captures = [dict(zip(fields, row)) for row in data[1:] if isinstance(row, list) and len(row) == len(fields)]
            elif data == []:
                captures = []
            else:
                raise ValueError("Malformed exact-URL CDX response")
            item.update({"status": "indexed" if captures else "no_captures", "captures": captures,
                         "index_query": query, "indexed_at": datetime.now(timezone.utc).isoformat(),
                         "index_http_status": response.status_code})
            item.pop("index_error", None)
        except Exception as exc:
            item.update({"status": "index_failed", "index_query": query,
                         "index_error": f"{type(exc).__name__}: {exc}",
                         "indexed_at": datetime.now(timezone.utc).isoformat()})
        state["generated_at"] = datetime.now(timezone.utc).isoformat()
        state["assets"] = sorted(by_url.values(), key=lambda item: item["url"])
        _write_state(path, state)
        if progress and (attempted % 10 == 0 or attempted >= max_assets):
            progress({"attempted": attempted, "indexed": sum(a.get("status") == "indexed" for a in state["assets"]),
                      "no_captures": sum(a.get("status") == "no_captures" for a in state["assets"]),
                      "index_failed": sum(a.get("status") == "index_failed" for a in state["assets"]),
                      "source_url": item["url"], "cooldown_until": state.get("cooldown_until")})
    _refresh_report(root)
    return {"assets": len(state["assets"]), "indexed": sum(a.get("status") == "indexed" for a in state["assets"]),
            "no_captures": sum(a.get("status") == "no_captures" for a in state["assets"]),
            "index_failed": sum(a.get("status") == "index_failed" for a in state["assets"]),
            "queued": sum(a.get("status") == "queued" for a in state["assets"]), "attempted": attempted,
            "cooldown_until": state.get("cooldown_until"), "saved_to": EXTERNAL_PATH.as_posix()}


def select_external_capture(item: dict) -> dict | None:
    """Choose the indexed image/media capture nearest to its latest referring page date."""
    failed = set(item.get("failed_capture_timestamps", []))
    captures = []
    for capture in item.get("captures", []):
        mime = str(capture.get("mimetype", "")).lower()
        if str(capture.get("statuscode", "200")) != "200" or not str(capture.get("timestamp", "")).isdigit():
            continue
        if str(capture.get("timestamp")) in failed:
            continue
        if item.get("kind") == "image" and mime and not mime.startswith("image/"):
            continue
        if item.get("kind") == "media" and mime and not mime.startswith(("audio/", "video/")):
            continue
        captures.append(capture)
    if not captures:
        return None
    dates = [str(ref.get("timestamp", "")) for ref in item.get("references", [])
             if str(ref.get("timestamp", "")).isdigit()]
    target = max(dates) if dates else "20090831235959"
    return min(captures, key=lambda capture: (abs(int(capture["timestamp"]) - int(target)),
                                               capture["timestamp"] > target, capture["timestamp"]))



def _validate_media(body: bytes) -> None:
    valid = (body.startswith((b"ID3", b"OggS", b"fLaC", b"FORM")) or
             (len(body) > 2 and body[0] == 0xFF and body[1] & 0xE0 == 0xE0) or
             (body.startswith(b"RIFF") and body[8:12] in (b"WAVE", b"AVI ")) or
             (len(body) >= 8 and body[4:8] == b"ftyp") or body.startswith(b"\x1aE\xdf\xa3"))
    if not valid:
        raise ValueError("Expected audio/video media bytes; received HTML or an unsupported payload")


def _extension(item: dict, kind: str) -> str:
    suffix = Path(urlsplit(item["url"]).path).suffix.lower()
    if suffix and re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        return suffix
    mime = item.get("mimetype", "").lower()
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
            "audio/mpeg": ".mp3", "audio/wav": ".wav", "video/mp4": ".mp4"}.get(mime, ".img" if kind == "image" else ".bin")


def recover_external_assets(root: Path, max_files: int = 40, delay: float = 0.6, retry_failed: bool = False, progress=None) -> dict:
    """Fetch a bounded number of indexed external image/media captures and checkpoint their hashes."""
    if max_files < 1 or delay < 0:
        raise ValueError("Invalid external-asset recovery limits")
    root = Path(root)
    path = root / EXTERNAL_PATH
    state = _read_state(path)
    manifest_path = root / "recovery/massline/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    downloaded = manifest.setdefault("external_resources", {})
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical source-linked asset recovery; paced requests)"
    client = ArchiveClient(session=session, delay=delay, retries=3, timeout=45, max_bytes=64_000_000)
    attempted = 0
    for item in sorted(state.get("assets", []), key=external_asset_priority):
        if attempted >= max_files:
            break
        if item.get("status") not in (("indexed", "download_failed") if retry_failed else ("indexed",)):
            continue
        capture = select_external_capture(item)
        if not capture:
            item["status"] = "no_valid_capture"
            _write_state(path, state)
            continue
        attempted += 1
        canonical = item["url"]
        if canonical in downloaded and downloaded[canonical].get("status") == "recovered":
            item.update({"status": "recovered", "selected_capture": capture["timestamp"],
                         "raw_path": downloaded[canonical].get("raw_path"), "sha256": downloaded[canonical].get("sha256")})
            continue
        replay = f"https://web.archive.org/web/{capture['timestamp']}id_/{capture['original']}"
        try:
            payload = client.get(replay)
            kind = "image" if capture.get("mimetype", "").startswith("image/") else item["kind"]
            if kind == "image":
                validate_payload(payload.body, "image")
            else:
                _validate_media(payload.body)
            digest = sha256(payload.body).hexdigest()
            raw_path = Path("recovery/massline/external/raw") / f"{digest}{_extension({**item, **capture}, kind)}"
            dest = root / raw_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(payload.body)
            record = {"source_url": capture["original"], "canonical_url": canonical,
                      "timestamp": capture["timestamp"], "mimetype": capture.get("mimetype", ""),
                      "kind": kind, "source_archive": "Internet Archive Wayback",
                      "source": replay, "status": "recovered", "actual_url": payload.url,
                      "raw_path": raw_path.as_posix(), "sha256": digest, "bytes": len(payload.body),
                      "content_type": payload.headers.get("Content-Type", ""),
                      "referenced_by": item.get("references", [])}
            downloaded[canonical] = record
            item.update({"status": "recovered", "selected_capture": capture["timestamp"],
                         "raw_path": raw_path.as_posix(), "sha256": digest, "bytes": len(payload.body),
                         "content_type": payload.headers.get("Content-Type", "")})
            item.pop("recovery_error", None)
        except Exception as exc:
            timestamp = capture["timestamp"]
            failed = item.setdefault("failed_capture_timestamps", [])
            if timestamp not in failed:
                failed.append(timestamp)
            attempts = item.setdefault("attempts", [])
            attempts.append({"timestamp": timestamp, "status": "invalid_payload_or_fetch_error",
                            "error": f"{type(exc).__name__}: {exc}"})
            item.update({"status": "download_failed", "selected_capture": timestamp,
                         "recovery_error": f"{type(exc).__name__}: {exc}"})
        state["generated_at"] = datetime.now(timezone.utc).isoformat()
        _write_state(path, state)
        _write_state(manifest_path, manifest)
        if progress and (attempted % 10 == 0 or attempted >= max_files):
            progress({"attempted": attempted, "recovered": sum(a.get("status") == "recovered" for a in state.get("assets", [])),
                      "download_failed": sum(a.get("status") == "download_failed" for a in state.get("assets", [])),
                      "source_url": canonical})
    _write_state(path, state)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _refresh_report(root)
    return {"assets": len(state.get("assets", [])), "recovered": sum(a.get("status") == "recovered" for a in state.get("assets", [])),
            "download_failed": sum(a.get("status") == "download_failed" for a in state.get("assets", [])),
            "attempted": attempted, "saved_to": EXTERNAL_PATH.as_posix()}
