"""Parse locally preserved WordPress RSS snapshots as a distinct source type."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from .urls import identity, is_site, original_url

CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def collect_feed_entries(root: Path) -> dict[str, dict]:
    """Return the latest feed observation for each Blue Scholars post URL.

    The XML remains the source of record. Returned paths and capture timestamps
    let the renderer identify this as feed material rather than original HTML.
    """
    feed_dir = Path(root) / "recovery/captured-sources/2026-10-18/feeds"
    entries: dict[str, dict] = {}
    if not feed_dir.is_dir():
        return entries
    manifest_path = feed_dir / "index.json"
    manifest = {}
    if manifest_path.exists():
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        for snapshot in document.get("feed_snapshots", []):
            manifest[snapshot.get("path", "")] = snapshot
    for path in sorted(feed_dir.glob("??????????????-*.xml")):
        stamp_match = re.match(r"(\d{14})-", path.name)
        if not stamp_match:
            continue
        stamp = stamp_match.group(1)
        try:
            body_bytes = path.read_bytes()
            source_record = manifest.get(path.relative_to(Path(root)).as_posix())
            if source_record:
                if (len(body_bytes) != source_record.get("bytes")
                        or hashlib.sha256(body_bytes).hexdigest() != source_record.get("sha256")):
                    raise ValueError(f"Saved feed source failed its manifest check: {path}")
            root_node = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        feed_url = (source_record or {}).get("feed_url") or (
            "http://bluescholars.com/feed/" if "-feed.xml" in path.name and "-blog-feed.xml" not in path.name
            else "http://bluescholars.com/blog/feed/")
        for item in root_node.findall(".//item"):
            link = original_url(item.findtext("link", "").strip())
            if not link or not is_site(link):
                continue
            key = identity(link)
            encoded = item.findtext(CONTENT)
            description = item.findtext("description", "")
            body = encoded if encoded and encoded.strip() else description
            if not body or not body.strip():
                continue
            entry = {
                "url": link,
                "title": " ".join((item.findtext("title", "") or "").split()),
                "published": " ".join((item.findtext("pubDate", "") or "").split()),
                "content": body.strip(),
                "content_type": "full" if encoded and encoded.strip() else "description",
                "feed_capture": stamp,
                "feed_url": feed_url,
                "feed_replay_url": (source_record or {}).get("replay_url") or
                    f"https://web.archive.org/web/{stamp}id_/{feed_url}",
                "feed_path": path.relative_to(Path(root)).as_posix(),
            }
            previous = entries.get(key)
            if previous is None or stamp > previous["feed_capture"]:
                entries[key] = entry
    return entries
