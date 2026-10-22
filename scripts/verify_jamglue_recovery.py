"""Verify every locally saved Jamglue capture against its recovery manifests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "recovery" / "jamglue"


def read(name: str) -> dict:
    return json.loads((COLLECTION / name).read_text(encoding="utf-8"))


def records() -> list[dict]:
    result: list[dict] = []
    manifest = read("manifest.json")
    for page in manifest["pages"].values():
        result.extend(x for x in page["captures"] if x.get("raw_path"))
    result.extend(x for x in read("recovered-assets.json")["resources"] if x.get("raw_path"))
    mixes = read("mix-media-index.json")
    for key in ("mix_page_resources", "linked_mix_resources"):
        result.extend(x for x in mixes.get(key, []) if x.get("raw_path"))
    result.extend(x for x in read("blog-posts.json")["resources"] if x.get("raw_path"))
    result.extend(x for x in read("related-pages.json")["records"] if x.get("raw_path"))
    result.extend(x for x in read("additional-route-pages.json")["resources"] if x.get("raw_path"))
    result.extend(x for x in read("hi808-media-pages.json")["resources"] if x.get("raw_path"))
    result.extend(x for x in read("geologic-acapella-captures.json")["records"] if x.get("raw_path"))
    result.extend(x for x in read("hi808-winners-pages.json")["resources"] if x.get("raw_path"))
    result.extend(x for x in read("hi808-winner-wildcard-pages.json")["resources"] if x.get("raw_path"))
    return result


def main() -> int:
    items = records()
    errors: list[str] = []
    hashes: set[str] = set()
    total_bytes = 0
    raw_root = (COLLECTION / "raw").resolve()
    for item in items:
        path = (ROOT / item["raw_path"]).resolve()
        if not path.is_relative_to(raw_root):
            errors.append(f"path escapes Jamglue raw directory: {item['raw_path']}")
            continue
        if not path.is_file():
            errors.append(f"missing file: {item['raw_path']}")
            continue
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != item.get("bytes") or digest != item.get("sha256"):
            errors.append(f"size/hash mismatch: {item['raw_path']}")
            continue
        hashes.add(digest)
        total_bytes += len(body)
    summary = {
        "records": len(items),
        "unique_files": len({x["raw_path"] for x in items}),
        "unique_sha256": len(hashes),
        "bytes": total_bytes,
        "errors": len(errors),
    }
    print(json.dumps(summary, indent=2))
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
