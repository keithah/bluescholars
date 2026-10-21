import json
from pathlib import Path

from bs4 import BeautifulSoup

from restore.check import check
from restore.twitter import asset_suffix, build_twitter_archive


def test_twitter_archive_builds_local_dated_pages_without_remote_dependencies(tmp_path):
    root = tmp_path
    output = root / "_candidate"
    manifest = root / "recovery/twitter-prometheusbrown/manifest.json"
    raw = manifest.parent / "raw"
    raw.mkdir(parents=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    capture = "20090725010529"
    (raw / f"{capture}.html").write_text(
        '<!doctype html><html><head><title>Geo on Twitter</title>'
        '<script src="https://twitter.com/live.js"></script>'
        '<link rel="stylesheet" href="https://assets.twitter.com/old.css"></head>'
        '<body><div id="content"><div class="tweet" href="/prometheusbrown/status/1">Oof wit ya boy!</div>'
        '<img src="https://example.org/avatar.jpg" srcset="https://example.org/avatar2.jpg 2x" alt="Geo"></div></body></html>'
    )
    asset_root = manifest.parent / "assets"
    asset_root.mkdir()
    (asset_root / "avatar.jpg").write_bytes(b"\xff\xd8\xfftest")
    (asset_root / "old.css").write_text("body{background:url(https://example.org/missing.png)}")
    manifest.write_text(json.dumps({"captures": [{
        "timestamp": capture,
        "original": "http://twitter.com/prometheusbrown",
        "digest": "ABC123",
        "fetch": {"status": "recovered", "path": f"raw/{capture}.html"},
    }], "assets": [
        {"timestamp": capture, "url": "https://example.org/avatar.jpg", "kind": "image",
         "status": "recovered", "path": "assets/avatar.jpg", "sha256": "img1"},
        {"timestamp": capture, "url": "https://assets.twitter.com/old.css", "kind": "css",
         "status": "recovered", "path": "assets/old.css", "sha256": "css1"},
    ]}))

    report = build_twitter_archive(root, output, "/bluescholars")

    page = BeautifulSoup((output / "twitter-prometheusbrown/captures" / capture / "index.html").read_text(), "html.parser")
    index = BeautifulSoup((output / "twitter-prometheusbrown/index.html").read_text(), "html.parser")
    assert "Oof wit ya boy!" in page.get_text(" ", strip=True)
    assert not page.find("script")
    assert not page.select("div[href]")
    image = page.select_one("img")
    assert image and image["src"] == "/bluescholars/twitter-prometheusbrown/assets/avatar.jpg"
    assert not page.select('img[srcset*="example.org"]')
    assert page.select_one('link[rel="stylesheet"][href="/bluescholars/twitter-prometheusbrown/assets/old.css"]')
    assert "https://example.org/missing.png" not in (output / "twitter-prometheusbrown/assets/old.css").read_text()
    assert index.select_one(f'a[href="/bluescholars/twitter-prometheusbrown/captures/{capture}/"]')
    assert report["recovered_capture_pages"] == 1
    (output / "index.html").write_text('<a href="/bluescholars/twitter-prometheusbrown/">Twitter archive</a>')
    assert check(output, "/bluescholars") == []

    root_output = root / "_root_candidate"
    build_twitter_archive(root, root_output, "")
    (root_output / "index.html").write_text('<a href="/twitter-prometheusbrown/">Twitter archive</a>')
    assert check(root_output, "") == []


def test_twitter_index_separates_platform_errors_and_later_account_takeover(tmp_path):
    root = tmp_path
    manifest = root / "recovery/twitter-prometheusbrown/manifest.json"
    raw = manifest.parent / "raw"
    raw.mkdir(parents=True)
    captures = []
    for timestamp, content, classification in (
        ("20221206172415", "JavaScript is not available.", "platform_error"),
        ("20241115224417", "SQUATTING @prometheusbrown Joined December 2022 Posts Replies Media", "later_account_takeover"),
    ):
        rel = f"raw/{timestamp}.html"
        (manifest.parent / rel).write_text(f"<html><body>{content}</body></html>")
        captures.append({"timestamp": timestamp, "original": "https://twitter.com/prometheusbrown",
                         "digest": timestamp, "title": content[:20], "content_classification": classification,
                         "fetch": {"status": "recovered", "path": rel}})
    manifest.write_text(json.dumps({"captures": captures}))

    report = build_twitter_archive(root, root / "_site")

    index = BeautifulSoup((root / "_site/twitter-prometheusbrown/index.html").read_text(), "html.parser")
    text = index.get_text(" ", strip=True)
    assert "Platform error capture" in text
    assert "Later account takeover" in text
    assert report["platform_error_captures"] == 1
    assert report["account_takeover_captures"] == 1


def test_twitter_png_signature_is_validated_with_case_sensitive_png_magic():
    payload = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert asset_suffix(payload, "image/png", "image") == ".png"
