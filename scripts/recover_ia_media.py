#!/usr/bin/env python3
"""Search Internet Archive item metadata and preserve selected Blue Scholars audio.

Media payloads are written only to the ignored recovery/media/ia directory.
Metadata, source URLs, hashes, sizes and rights notes stay in recovery/ia-media.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/ia-media"
MEDIA = ROOT / "recovery/media/ia"
SEARCH = "https://archive.org/advancedsearch.php"
FIELDS = ["identifier", "title", "creator", "date", "description", "licenseurl", "mediatype", "subject"]
QUERIES = [
    'mediatype:audio AND "Blue Scholars"',
    'mediatype:audio AND "DJ Sabzi"',
    'mediatype:audio AND "Prometheus Brown"',
    'mediatype:movies AND "Blue Scholars"',
]
# Direct Blue Scholars appearances and band-name items found in item metadata.
# These are research copies only, irrespective of license metadata.
SELECTED = {
    "KEXPKEXPLivePerformances_101": ["BlueScholars.mp3"],
    "AUDIOCASTVOLUME061107grandgood.com": ["AUDIOCAST VOLUME 061107 (grandgood.com).mp3"],
    "BlueScholarsatSXSWclipped": [
        "1_On_community_radio.mp3", "2_On_SXSW_and_commercialization.mp3",
        "3_On_Evergreen_riots.mp3", "4_On_masculinity_and_misogyny.mp3",
        "5_On_new_Nas_album.mp3", "6_On_file_sharing.mp3", "7_On_growing_up.mp3",
        "8_On_counterrecruitment_and_arsons.mp3", "9_On_Probrown_albums_and_new_artists.mp3",
        "10_On_the_media.mp3",
    ],
    "StillGotLove": ["06StillGotLove.mp3"],
    "radio4all-13642": ["1200-1-20050810-PTR_05-082Final.mp3"],
    "sc21wa-City_A_Go_Go": ["City_A_Go_Go.mp4"],
    # Additional independently cataloged radio mixes/programs found in the
    # October 22 metadata expansion. These are local research copies only.
    "DJPRKBlueScholarsMix1": ["BlueScholarsMix1.mp3"],
    "D_PMixTape13_SpringisComing": ["13MixTape13_SpringisComing.mp3"],
    "TheBlueCrabBlueCrab4": ["4.mp3"],
    "ListenUpNwProgram47": ["LUNW_20090515_47_taxes.mp3"],
    "ListenUpNorthwestProgram74": ["LUNW_20101228_74_Schools_Quality_of_Life.mp3"],
    "ListenUpNorthwestProgram100HipHopMoreThanMusic_213": [
        "LUNW_20100909_Hip_Hop_More_Than_Music_100_2.mp3"
    ],
    # Earlier KEXP #53 was preserved before this manifest workflow existed;
    # record and verify the existing local file without downloading it again.
    "KEXPKEXPLivePerformances_53": ["BlueScholars.mp3"],
    # Earlier Seattle Channel acquisition. Its payload exceeds this script's
    # download cap; this selection exists to keep its metadata and provenance
    # in the common item manifest, not to download a second copy.
    "SMA_12838": ["12838.mp4"],
    # IA descriptions explicitly credit Blue Scholars or DJ Sabzi in these
    # regional radio program music credits. Keep original broadcast masters
    # local-only; item-level CC terms do not clear embedded music rights.
    "ListenUpNorthwestProgram49": ["LUNW_20090604_Language.mp3"],
    "ListenUpNorthwestProgram61": ["LUNW_20090917_62_Alaska_Youth.mp3"],
    "ListenUpNorthwestProgram91Craft": ["LUNW_20100603_91_Craft.mp3"],
    "ListenUpNorthwestProgram100HipHopMoreThanMusic": [
        "LUNW_20100909_Hip_Hop_More_Than_Music_100.mp3"
    ],
    "ListenUpNorthwestProgram85": ["LUNW_20100408_Green_Collar_Jobs.mp3"],
    "ListenUpNorthwestProgram55": ["LUNW_20090724_55_white_culture.mp3"],
    # The catalog description names Geologic's interview, but does not identify
    # which numbered segment contains it. Preserve the source's full program.
    "Mother_Jones_2006_08_13": ["mojo_radio_081306.mp3"],
    # The exact Blue Scholars track and time are explicitly listed in the show
    # playlist, but the full program contains unrelated artists as well.
    "OffAir_090813": ["OffAir-33-OfFireOfFurnaces.mp3"],
    "D_PMixTape6_ConsciousChill": ["MixTape6_ConsciousChill.mp3"],
    "CommonThreads-Ep.1DaveDahl": ["CommonThreads-DaveDahl.mp3"],
    # Artist collaborations whose catalog description explicitly credits
    # Prometheus Brown; preserve only the credited track, not unrelated album
    # tracks. These remain local research copies pending rights review.
    "one-rifle-per-family": [
        "06. Books (feat. Prometheus Brown aka Geologic of Blue Scholars).mp3"
    ],
    "Sol_-_Dear_Friends__Vol._II": [
        "06 Spliff Remix (Feat. Grynch, Prometheus Brown & Thig Nat).mp3"
    ],
    # The MP3 is over the configured 100 MB cap; retain the smaller cataloged
    # Ogg source instead of weakening that acquisition limit.
    "ApexExpressMusicShow": ["20120112-Thu1900.ogg"],
    # The 2006 Amateur Hour playlist explicitly includes Blue Scholars' "Bayani".
    # Keep the original program master as-is and choose its smaller Ogg copy.
    "AmateurHourEpisode2WhyWerePissed_6": ["WhyWerePissed.ogg"],
    # Archive.org catalog entries with track-level references to Blue Scholars.
    # Its MP3 copies begin with a zero-filled corrupt header, so preserve the
    # signature-validated Ogg versions of the two 2009 Duck Down tracks.
    "Duck_Down_-_Download_The_Right_Thing-2009": [
        "13-Blue_Scholars_-_Hi_808.ogg",
        "15-Blue_Scholars_-_Coo.ogg",
    ],
    # Thomax's catalog explicitly credits a Blue Scholars remix; the item's
    # CC BY-NC-ND metadata is recorded, but this remains a local source copy.
    "pandacd-442-the-remix-files-volume-7": [
        "01-Thomax-Fire_For_The_People_REMIX_(Blue_Scholars).mp3",
    ],
    # These are complete third-party mixes whose track lists explicitly name a
    # Blue Scholars song. Preserve the smaller Ogg for the 2007 political mix.
    "PoliticalHipHopMix_666": ["PoliticalHipHopMix.ogg"],
    "stop-war-mix-tape-see-comments": ["Stop war mix tape - See comments.mp3"],
    # A Seattle public-history video documents a Geo Quibuyen speech; retain
    # its cataloged audio source (71 MB) because the video encodes exceed cap.
    "sc21wa-Teach_Truth_-_Unbanning_Books_in_Public_Schools": [
        "Teach_Truth_-_Unbanning_Books_in_Public_Schools.mp3",
    ],
}
MAX_BYTES = 100_000_000


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "audio"


def _search(session: requests.Session) -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for query in QUERIES:
        response = session.get(SEARCH, params={"q": query, "fl[]": FIELDS, "rows": 100, "output": "json"}, timeout=(8, 30))
        response.raise_for_status()
        payload = response.json()
        results.append({"query": query, "num_found": payload["response"]["numFound"],
                        "docs": payload["response"]["docs"]})
        time.sleep(0.5)
    (OUT / "search-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


def _valid_media(path: Path, content_type: str, filename: str) -> bool:
    with path.open("rb") as source:
        head = source.read(16)
    if filename.lower().endswith(".mp4"):
        return content_type.lower().startswith("video/") and len(head) >= 12 and head[4:8] == b"ftyp"
    if filename.lower().endswith(".ogg"):
        return content_type.lower().startswith(("audio/", "application/ogg")) and head.startswith(b"OggS")
    if content_type.lower().startswith("audio/"):
        return head.startswith((b"ID3", b"\xff\xfa", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftypM4A"))
    return head.startswith((b"ID3", b"\xff\xfa", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"))


def aggregate_items(items: dict) -> dict:
    """Recompute cumulative media totals from durable, verified file records."""
    files = [record for item in items.values() for record in item.get("files", {}).values()]
    unique = {}
    for record in files:
        digest = record.get("sha256")
        if digest:
            unique.setdefault(digest, record)
    file_types = Counter(Path(record.get("filename", "")).suffix.upper().lstrip(".")
                         for record in files)
    licensed_items = sum(bool(item.get("licenseurl")) for item in items.values())
    return {
        "items": len(items),
        "source_files": len(files),
        "unique_payloads": len(unique),
        "source_bytes": sum(int(record.get("bytes", 0) or 0) for record in files),
        "unique_bytes": sum(int(record.get("bytes", 0) or 0) for record in unique.values()),
        "new_file_types": dict(sorted(file_types.items())),
        "licensed_item_records": licensed_items,
        "local_storage": "recovery/media/ia (ignored; not part of public site)",
        "rights_note": "Internet Archive availability does not grant redistribution rights; all files remain local-only pending rights review.",
    }


def recover() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"version": 1, "items": {}}
    items = manifest.setdefault("items", {})
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical media preservation)"
    searches = _search(session)
    # Include the broader source-phrase query saved during the October 22
    # discovery pass. This is additive and retained separately so the
    # canonical name-search checkpoint remains easy to compare over time.
    source_phrase_path = OUT / "search-results-source-phrases.json"
    if source_phrase_path.is_file():
        phrase_results = json.loads(source_phrase_path.read_text(encoding="utf-8"))
        for result in phrase_results:
            searches.append({"query": result.get("query"), "num_found": result.get("num_found", 0),
                             "docs": result.get("docs", [])})
    candidates = {}
    for result in searches:
        for doc in result["docs"]:
            identifier = doc.get("identifier")
            if identifier in SELECTED:
                candidates[identifier] = doc
    report = {"archive": "Internet Archive item-level media", "queries": [
                  {"query": q["query"], "num_found": q["num_found"]} for q in searches],
              "selected_items": len(candidates), "selected_media_files": sum(len(v) for v in SELECTED.values()),
              "downloaded_files": 0, "downloaded_bytes": 0, "failures": [],
              "limitations": ["Only selected original MP3/MP4/Ogg files are acquired; alternate encodings and derivatives are not duplicated.",
                              "Files are stored in ignored recovery/media/ia and are not included in the public site.",
                              "Internet Archive availability does not grant redistribution rights; missing license metadata is retained as unresolved."]}
    for identifier, doc in candidates.items():
        try:
            response = session.get(f"https://archive.org/metadata/{quote(identifier)}", timeout=(8, 30))
            response.raise_for_status()
            metadata = response.json()
            meta = metadata.get("metadata", {})
            files = {f.get("name"): f for f in metadata.get("files", []) if f.get("name")}
            record = items.setdefault(identifier, {"item_url": f"https://archive.org/details/{identifier}",
                "metadata_api": f"https://archive.org/metadata/{identifier}", "search_record": doc,
                "title": meta.get("title", doc.get("title")), "creator": meta.get("creator", doc.get("creator")),
                "date": meta.get("date", doc.get("date")), "description": meta.get("description", doc.get("description")),
                "licenseurl": meta.get("licenseurl", doc.get("licenseurl")), "files": {}})
            for filename in SELECTED[identifier]:
                if filename not in files:
                    report["failures"].append({"identifier": identifier, "filename": filename, "stage": "metadata", "error": "Selected source file missing from item metadata"})
                    continue
                source = files[filename]
                length = int(source.get("size", 0) or 0)
                if Path(filename).suffix.lower() not in (".mp3", ".mp4", ".ogg") or length <= 0 or length > MAX_BYTES:
                    report["failures"].append({"identifier": identifier, "filename": filename, "stage": "metadata", "error": f"File outside supported media/size limit ({length} bytes)"})
                    continue
                file_record = record["files"].get(filename, {})
                path = MEDIA / f"{_safe_name(identifier)}--{_safe_name(filename)}"
                # Older one-off acquisition scripts used a single dash between
                # item ID and filename. Reconcile those exact payloads before
                # downloading, so repeated recovery runs stay idempotent.
                legacy_path = MEDIA / f"{_safe_name(identifier)}-{_safe_name(filename)}"
                if identifier == "SMA_12838" and filename == "12838.mp4":
                    # Seattle Channel workflow's original filename is
                    # `SMA_12838-12838.mp4`, while its Archive.org item uses
                    # `12838.mp4`.
                    legacy_path = MEDIA / "SMA_12838-12838.mp4"
                if not path.exists() and legacy_path.is_file():
                    path = legacy_path
                if path.is_file():
                    data_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                    if file_record.get("sha256") and data_hash == file_record["sha256"]:
                        continue
                    # A previously downloaded item can predate this manifest
                    # (or have had its manifest checkpoint interrupted). Verify
                    # it against the IA file MD5/size and restore provenance
                    # without needlessly fetching the same large payload.
                    expected_md5 = source.get("md5")
                    actual_md5 = hashlib.md5(path.read_bytes()).hexdigest()
                    if path.stat().st_size == length and expected_md5 and actual_md5 == expected_md5:
                        file_record.update({"filename": filename,
                            "download_url": f"https://archive.org/download/{quote(identifier, safe='')}/{quote(filename)}",
                            "raw_path": str(path.relative_to(ROOT)), "bytes": length,
                            "sha256": data_hash, "content_type": "audio/mpeg",
                            "item_license": record.get("licenseurl"),
                            "rights_status": "review_required_before_publication",
                            "source_format": source.get("format"), "source_md5": expected_md5,
                            "reconciled_existing_local_file": True})
                        record["files"][filename] = file_record
                        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                        continue
                    if identifier == "SMA_12838" and path.stat().st_size == length and data_hash == hashlib.sha256(path.read_bytes()).hexdigest():
                        file_record.update({"filename": filename,
                            "download_url": f"https://archive.org/download/{quote(identifier, safe='')}/{quote(filename)}",
                            "raw_path": str(path.relative_to(ROOT)), "bytes": length,
                            "sha256": data_hash, "content_type": "video/mp4",
                            "item_license": record.get("licenseurl"),
                            "rights_status": "review_required_before_publication",
                            "source_format": source.get("format"), "source_md5": expected_md5,
                            "reconciled_existing_local_file": True,
                            "reconciliation_note": "Previously acquired and container-validated by Seattle Channel recovery workflow."})
                        record["files"][filename] = file_record
                        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                        continue
                url = f"https://archive.org/download/{quote(identifier, safe='')}/{quote(filename)}"
                temp = path.with_suffix(path.suffix + ".part")
                with session.get(url, timeout=(8, 60), stream=True) as media:
                    media.raise_for_status()
                    content_type = media.headers.get("Content-Type", "")
                    digest = hashlib.sha256(); size = 0
                    with temp.open("wb") as output:
                        for chunk in media.iter_content(256 * 1024):
                            if not chunk: continue
                            size += len(chunk)
                            if size > MAX_BYTES: raise ValueError("Media response exceeded 100 MB cap")
                            digest.update(chunk); output.write(chunk)
                if size != length:
                    raise ValueError(f"Downloaded size {size} does not match item metadata {length}")
                if not _valid_media(temp, content_type, filename):
                    raise ValueError(f"Response did not validate as {Path(filename).suffix.upper()} ({content_type})")
                temp.replace(path)
                file_record.update({"filename": filename, "download_url": url, "raw_path": str(path.relative_to(ROOT)),
                    "bytes": size, "sha256": digest.hexdigest(), "content_type": content_type,
                    "item_license": record.get("licenseurl"), "rights_status": "review_required_before_publication",
                    "source_format": source.get("format"), "source_md5": source.get("md5")})
                record["files"][filename] = file_record
                report["downloaded_files"] += 1; report["downloaded_bytes"] += size
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                time.sleep(0.5)
        except Exception as exc:
            for temp in MEDIA.glob(f"{_safe_name(identifier)}--*.part"):
                temp.unlink(missing_ok=True)
            report["failures"].append({"identifier": identifier, "stage": "item", "error": f"{type(exc).__name__}: {exc}"})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["item_records_total"] = len(items)
    report["source_files_total"] = sum(len(x.get("files", {})) for x in items.values())
    manifest["aggregate_summary"] = aggregate_items(items)
    report["aggregate_summary"] = manifest["aggregate_summary"]
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(recover(), indent=2, ensure_ascii=False))
