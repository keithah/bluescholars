#!/usr/bin/env python3
"""Preserve relevant, unaltered image objects from recovered Billboard scans.

These are page composites, not standalone photographs. Their Blue Scholars
association comes from their placement in the issue page and must remain
qualified until the original credit is established.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "recovery/other-archives/press-pdfs"

SPECS = [
    {
        "pdf": "800fe84ab3cc3632e510583b6dc2daece77b8fd15fd9472e7d4c38d79847971a.pdf",
        "page": 35,
        "object": "I6",
        "label": "Billboard July 2006 Blue Scholars page composite",
        "association": "Probable Blue Scholars duo photograph at left; composite also includes unrelated photographs.",
        "source_page_context": "Billboard issue page headed The Blue Scholars; article text describes the Seattle duo.",
    }
]


def extract() -> dict:
    image_dir = PDF_DIR / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    images = []
    captures = json.loads((PDF_DIR / "manifest.json").read_text())["captures"]
    for spec in SPECS:
        pdf_path = PDF_DIR / "raw" / spec["pdf"]
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[spec["page"] - 1]
            matches = [im for im in page.images if im["name"] == spec["object"]]
            if len(matches) != 1:
                raise RuntimeError(f"Expected one {spec['object']} on page {spec['page']}: found {len(matches)}")
            image = matches[0]
            data = image["stream"].get_data()
            width = int(image["stream"].attrs["Width"])
            height = int(image["stream"].attrs["Height"])
        if not data.startswith(b"\xff\xd8\xff"):
            raise RuntimeError(f"{spec['object']} is not a JPEG image stream")
        digest = hashlib.sha256(data).hexdigest()
        output_path = image_dir / f"{digest}.jpg"
        output_path.write_bytes(data)
        parent = next(row for row in captures.values() if row["sha256"] == spec["pdf"].removesuffix(".pdf"))
        images.append({
            **spec,
            "source_type": "unaltered PDF image object; compound page artwork",
            "pdf_path": pdf_path.relative_to(ROOT).as_posix(),
            "pdf_sha256": spec["pdf"].removesuffix(".pdf"),
            "wayback_timestamp": parent["timestamp"],
            "wayback_replay": parent["replay_url"],
            "page_image_object": image["name"],
            "dimensions_px": {"width": width, "height": height},
            "placement_points": {k: round(float(image[k]), 2) for k in ("x0", "top", "x1", "bottom")},
            "bytes": len(data),
            "sha256": digest,
            "path": output_path.relative_to(ROOT).as_posix(),
            "visual_review": "JPEG inspected; left panel likely depicts the duo, but image is a multi-photo composite and attribution is not printed in the extracted object.",
            "rights_status": "recovery-only; rights review required",
        })
    report = {
        "description": "Unaltered compound image objects extracted from archived Billboard PDF pages.",
        "method": "Extract original JPEG XObject streams; retain entire composite and record page placement, parent PDF hash, and qualified identification.",
        "images": images,
    }
    (PDF_DIR / "billboard-image-composites.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(extract(), indent=2, ensure_ascii=False))
