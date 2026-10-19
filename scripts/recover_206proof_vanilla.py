#!/usr/bin/env python3
"""Resume validated 2008–2012 206proof Vanilla pages from a local CDX checkpoint."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from restore.archive import ArchiveClient, validate_payload
from restore.recovery_206proof import select_latest_vanilla
from restore.urls import capture_from


def recover(root: Path, limit: int = 160, delay: float = 0.6) -> dict:
    checkpoint = root / "recovery/206proof"
    rows = json.loads((checkpoint / "all-events-all-status.json").read_text())["rows"]
    manifest_path = checkpoint / "recovered-resources.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"resources": []}
    seen = {(r.get("requested_capture"), r.get("original")) for r in manifest["resources"]}
    queue = [r for r in select_latest_vanilla(rows)
             if (r["timestamp"], r["original"]) not in seen][:limit]
    client = ArchiveClient(delay=delay, retries=3, timeout=70, max_bytes=25_000_000)
    attempted = 0
    for row in queue:
        item = {
            "requested_capture": row["timestamp"], "original": row["original"],
            "mimetype": row["mimetype"], "statuscode": row["statuscode"],
            "cdx_digest": row.get("digest"), "indexed_length": row.get("length"),
            "kind": "html", "archive_era": "Vanilla forum, latest indexed capture 2008-2012",
            "attempted_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        try:
            response = client.get(f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}")
            validate_payload(response.body, "html")
            digest = hashlib.sha256(response.body).hexdigest()
            raw_path = checkpoint / "raw" / f"{digest}.html"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            if not raw_path.exists():
                raw_path.write_bytes(response.body)
            item.update(result="recovered", actual_capture=capture_from(response.url),
                        resolved_url=response.url, content_type=response.headers.get("Content-Type"),
                        bytes=len(response.body), sha256=digest,
                        raw_path=str(raw_path.relative_to(root)))
        except Exception as exc:  # Each failure is a durable, retryable source observation.
            item.update(result="failed", error=f"{type(exc).__name__}: {exc}")
        manifest["resources"].append(item)
        attempted += 1
        if attempted % 5 == 0:
            manifest.update(last_updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                            attempted_this_batch=attempted)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            print(f"{attempted}/{len(queue)} {item['result']} {item['original']}", flush=True)
    manifest.update(last_updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                    attempted_this_batch=attempted)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"attempted": attempted, "selected_routes": len(select_latest_vanilla(rows)),
            "remaining": sum((r["timestamp"], r["original"]) not in {
                (x.get("requested_capture"), x.get("original")) for x in manifest["resources"]
            } for r in select_latest_vanilla(rows)), "resources": len(manifest["resources"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=int, default=160)
    parser.add_argument("--delay", type=float, default=0.6)
    args = parser.parse_args()
    if args.limit < 1 or args.delay < 0:
        parser.error("--limit must be positive and --delay cannot be negative")
    print(json.dumps(recover(args.root.resolve(), args.limit, args.delay), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
