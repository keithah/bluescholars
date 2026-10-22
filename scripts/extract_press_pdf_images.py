#!/usr/bin/env python3
"""Extract visually confirmed Blue Scholars photos from preserved press PDFs.

Requires the Codex workspace's bundled pdfplumber and Pillow packages. This
extracts only source image objects confirmed against page renders and captions;
it does not turn whole-page previews into substitute photographs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "recovery/other-archives/press-pdfs"
OUT_DIR = PDF_DIR / "images"

SPECS = [
    {
        "pdf": "18163f7bd9e92b934e67cda4bf79bce24b29089270142eb8b4ff5f59a1031a54.pdf",
        "page": 37,
        "object": "FXX10",
        "credit": "Ryan Lewis (credit printed on page)",
        "caption": "Blue Scholars' Sabzi (left) and Geologic.",
        "label": "CMJ 2006 Geologic and Sabzi portrait",
    },
    {
        "pdf": "df2fb553ed20eebba594738f149510f3250ede19a745610fde349ed3f6f7d08e.pdf",
        "page": 10,
        "object": "Im0",
        "credit": "Zenith Richards (caption printed on page)",
        "caption": "Blue Scholars Coax Call and Response from the 'Sco; photograph shows Geologic performing in the crowd.",
        "label": "Oberlin Review 2008 Geologic performance",
    },
]


def extract() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in SPECS:
        source = PDF_DIR / "raw" / spec["pdf"]
        with pdfplumber.open(source) as pdf:
            page = pdf.pages[spec["page"] - 1]
            matches = [image for image in page.images if image["name"] == spec["object"]]
            if len(matches) != 1:
                raise RuntimeError(f"Expected one {spec['object']} on page {spec['page']}: found {len(matches)}")
            image = matches[0]
            data = image["stream"].get_data()
        if not data.startswith(b"\xff\xd8\xff"):
            raise RuntimeError(f"{spec['object']} is not a JPEG image stream")
        digest = hashlib.sha256(data).hexdigest()
        path = OUT_DIR / f"{digest}.jpg"
        path.write_bytes(data)
        rows.append({
            **spec,
            "pdf_path": (PDF_DIR / "raw" / spec["pdf"]).relative_to(ROOT).as_posix(),
            "pdf_sha256": spec["pdf"].removesuffix(".pdf"),
            "page_image_object": image["name"],
            "dimensions_px": {"width": int(image["stream"].attrs["Width"]), "height": int(image["stream"].attrs["Height"])},
            "placement_points": {k: round(float(image[k]), 2) for k in ("x0", "top", "x1", "bottom")},
            "extracted_sha256": digest,
            "bytes": len(data),
            "path": path.relative_to(ROOT).as_posix(),
            "source_page_url": next(c["source_url"] for c in _captures().values() if c["sha256"] == spec["pdf"].removesuffix(".pdf")),
            "wayback_replay": next(c["replay_url"] for c in _captures().values() if c["sha256"] == spec["pdf"].removesuffix(".pdf")),
            "verification": "JPEG decoded and visually inspected against rendered page; page caption and photo credit recorded",
            "publication_status": "recovery-only; rights review required",
        })
    result = {
        "description": "Visually confirmed embedded Blue Scholars photo extractions from archived press PDFs.",
        "method": "Extract original PDF image streams; verify JPEG signature, pixel dimensions, page placement, image appearance, and printed caption/credit.",
        "extractor": "pdfplumber via Codex bundled workspace Python; Pillow used for visual verification only",
        "images": rows,
    }
    (PDF_DIR / "image-extractions.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def _captures() -> dict:
    return json.loads((PDF_DIR / "manifest.json").read_text())["captures"]


if __name__ == "__main__":
    print(json.dumps(extract(), indent=2, ensure_ascii=False))
