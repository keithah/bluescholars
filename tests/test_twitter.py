import json
import hashlib
from pathlib import Path

from bs4 import BeautifulSoup

from restore.check import check
from restore import twitter
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
        '<a id="more" rel="next" class="round more" href="/prometheusbrown?max_id=1&amp;page=2&amp;twttr=true">more</a>'
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
    assert report["tweet_entries"] == 1
    assert report["pagination_gaps"] == 1
    more = page.select_one("a.twitter-pagination-index")
    assert more and more["href"] == "/bluescholars/twitter-prometheusbrown/tweets/?capture=20090725010529"
    assert more["data-archive-href"] == "https://web.archive.org/web/20090725010529/http://twitter.com/prometheusbrown?max_id=1&page=2&twttr=true"
    tweet_index = BeautifulSoup((output / "twitter-prometheusbrown/tweets/index.html").read_text(), "html.parser")
    assert "Oof wit ya boy!" in tweet_index.get_text(" ", strip=True)
    assert tweet_index.select_one('script[src="/bluescholars/twitter-prometheusbrown/tweets/search.js"]')
    assert not tweet_index.find("script", string=True)
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


def test_twitter_builder_supports_separate_named_accounts(tmp_path):
    root = tmp_path
    archive = root / "recovery/twitter-bluescholars"
    (archive / "raw").mkdir(parents=True)
    timestamp = "20090919073718"
    (archive / "raw" / f"{timestamp}.html").write_text(
        '<html><head><title>bluescholars (BlueScholars) on Twitter</title></head>'
        '<body><div class="tweet"><p class="tweet-text">Seattle: Bumbershoot weekend!</p>'
        '<a href="https://twitter.com/sabzi">@sabzi</a></div></body></html>'
    )
    (archive / "manifest.json").write_text(json.dumps({
        "profile": "https://twitter.com/bluescholars",
        "display_name": "Blue Scholars",
        "captures": [{"timestamp": timestamp, "original": "http://twitter.com/bluescholars",
                      "digest": "CDX", "fetch": {"status": "recovered", "path": f"raw/{timestamp}.html"}}],
        "assets": [],
    }))

    report = build_twitter_archive(root, root / "_candidate", "/bluescholars", "bluescholars")

    assert report["tweet_entries"] == 1
    index = BeautifulSoup((root / "_candidate/twitter-bluescholars/index.html").read_text(), "html.parser")
    assert "Blue Scholars on Twitter" in index.get_text(" ", strip=True)
    assert index.select_one('a[href="/bluescholars/twitter-bluescholars/captures/20090919073718/"]')
    capture = BeautifulSoup((root / "_candidate/twitter-bluescholars/captures/20090919073718/index.html").read_text(), "html.parser")
    assert capture.select_one('a[href="/bluescholars/twitter-sabzi/"]')
    tweet_index = BeautifulSoup((root / "_candidate/twitter-bluescholars/tweets/index.html").read_text(), "html.parser")
    assert "Seattle: Bumbershoot weekend!" in tweet_index.get_text(" ", strip=True)


def test_twitter_asset_fallback_selects_nearest_real_capture():
    rows = [
        ["20090101000000", "https://pbs.twimg.com/photo.jpg", "200", "image/jpeg", "A", "100"],
        ["20100101000000", "https://pbs.twimg.com/photo.jpg", "200", "image/jpeg", "B", "100"],
        ["20120101000000", "https://pbs.twimg.com/photo.jpg", "200", "image/jpeg", "C", "100"],
    ]

    selector = getattr(twitter, "closest_asset_capture", None)
    assert selector is not None, "Twitter linked assets need an alternate-capture selector"
    selected = selector(rows, "20110101000000")

    assert selected == rows[1]


def test_twitter_pagination_links_open_a_verified_local_page_two_response(tmp_path):
    root = tmp_path
    archive = root / "recovery/twitter-bluescholars"
    raw = archive / "raw"
    (raw / "pagination").mkdir(parents=True)
    timestamp = "20090804184918"
    query = "https://twitter.com/bluescholars?max_id=3112555357&page=2&twttr=true"
    (raw / f"{timestamp}.html").write_text(
        '<html><head><title>Blue Scholars (BlueScholars) on Twitter</title></head>'
        '<body><div id="pagination"><a id="more" rel="next" href="http://twitter.com:80/loggedout/profile/bluescholars?max_id=3112555357&amp;page=2&amp;twttr=true">more</a></div></body></html>'
    )
    page_path = "raw/pagination/20200221160110-abc123.html"
    (archive / page_path).write_text(
        '<html><head><title>Blue Scholars profile, archived page response</title></head>'
        '<body><div class="stream-item"><p class="tweet-text">Observed archived response.</p></div></body></html>'
    )
    (archive / "manifest.json").write_text(json.dumps({
        "display_name": "Blue Scholars", "profile": "https://twitter.com/bluescholars",
        "captures": [{"timestamp": timestamp, "original": "http://twitter.com/bluescholars",
                      "digest": "CDX", "fetch": {"status": "recovered", "path": f"raw/{timestamp}.html"}}],
        "pagination_pages": [{"target_url": query, "parent_captures": [timestamp],
                              "timestamp": "20200221160110", "original": query,
                              "route_id": "20200221160110-abc123", "digest": "SHA1",
                              "fetch": {"status": "recovered", "path": page_path,
                                        "cdx_sha1_verified": True}}],
        "assets": [],
    }))

    report = build_twitter_archive(root, root / "_candidate", "/bluescholars", "bluescholars")

    source_page = BeautifulSoup((root / "_candidate/twitter-bluescholars/captures" / timestamp / "index.html").read_text(), "html.parser")
    more = source_page.select_one("a.twitter-pagination-index")
    assert more and more["href"] == "/bluescholars/twitter-bluescholars/pages/2020/20200221160110-abc123/"
    preserved = BeautifulSoup((root / "_candidate/twitter-bluescholars/pages/2020/20200221160110-abc123/index.html").read_text(), "html.parser")
    assert "Observed archived response." in preserved.get_text(" ", strip=True)
    assert "does not prove Twitter honored" in preserved.get_text(" ", strip=True)
    tweet_index = BeautifulSoup((root / "_candidate/twitter-bluescholars/tweets/index.html").read_text(), "html.parser")
    assert "Observed archived response." in tweet_index.get_text(" ", strip=True)
    assert report["pagination_gaps"] == 0


def test_twitter_same_timestamp_variants_keep_separate_routes(tmp_path):
    archive = tmp_path / "recovery/twitter-canhsolo"
    raw = archive / "raw"
    raw.mkdir(parents=True)
    timestamp = "20140709203912"
    captures = []
    for route_id, phrase in ((f"{timestamp}-twitter-a1b2c3", "Twitter host version"),
                             (f"{timestamp}-mobile-d4e5f6", "Mobile host version")):
        rel = f"raw/{route_id}.html"
        (archive / rel).write_text(
            f'<html><head><title>{phrase}</title></head><body><p>{phrase}</p></body></html>')
        captures.append({"timestamp": timestamp, "route_id": route_id,
                         "original": "https://twitter.com/canhsolo", "digest": route_id,
                         "fetch": {"status": "recovered", "path": rel}})
    (archive / "manifest.json").write_text(json.dumps({
        "display_name": "Canh Solo", "profile": "https://twitter.com/canhsolo",
        "captures": captures, "assets": [],
    }))

    build_twitter_archive(tmp_path, tmp_path / "_candidate", "/bluescholars", "canhsolo")

    for route_id, phrase in ((f"{timestamp}-twitter-a1b2c3", "Twitter host version"),
                             (f"{timestamp}-mobile-d4e5f6", "Mobile host version")):
        page = tmp_path / "_candidate/twitter-canhsolo/captures" / route_id / "index.html"
        assert phrase in BeautifulSoup(page.read_text(), "html.parser").get_text(" ", strip=True)
    assert not (tmp_path / "_candidate/twitter-canhsolo/captures" / timestamp / "index.html").exists()


def test_twitter_video_source_is_rebuilt_as_local_playable_media(tmp_path):
    archive = tmp_path / "recovery/twitter-wongweezy"
    raw = archive / "raw"
    assets = archive / "assets"
    raw.mkdir(parents=True)
    assets.mkdir()
    timestamp = "20150829164440"
    media_url = "https://pbs.twimg.com/tweet_video/CMTETg6WcAAkwcK.mp4"
    media = b"\x00\x00\x00\x18ftypmp42" + b"fixture media"
    (assets / "video.mp4").write_bytes(media)
    (raw / f"{timestamp}.html").write_text(
        '<html><head><title>Wong Weezy video</title></head><body>'
        '<video poster="https://pbs.twimg.com/tweet_video_thumb/poster.png"><source type="video/mp4" '
        'video-src="https://pbs.twimg.com/tweet_video/CMTETg6WcAAkwcK.mp4"></video></body></html>'
    )
    (archive / "manifest.json").write_text(json.dumps({
        "display_name": "Wong Weezy", "profile": "https://twitter.com/wongweezy",
        "captures": [{"timestamp": timestamp, "original": "https://twitter.com/wongweezy",
                      "digest": "fixture", "fetch": {"status": "recovered", "path": f"raw/{timestamp}.html"}}],
        "assets": [{"timestamp": timestamp, "url": media_url, "kind": "video", "status": "recovered",
                     "path": "assets/video.mp4", "sha256": hashlib.sha256(media).hexdigest()}],
    }))

    build_twitter_archive(tmp_path, tmp_path / "_candidate", "/bluescholars", "wongweezy")

    page = BeautifulSoup((tmp_path / "_candidate/twitter-wongweezy/captures" / timestamp / "index.html").read_text(), "html.parser")
    video = page.select_one("video")
    assert video and video.has_attr("controls")
    assert not video.has_attr("poster")
    source = video.select_one("source")
    assert source["src"] == "/bluescholars/twitter-wongweezy/assets/video.mp4"
    assert not source.has_attr("video-src")
    assert "pbs.twimg.com" not in str(video)


def test_twitter_mp4_payload_signature_is_validated():
    assert asset_suffix(b"\x00\x00\x00\x18ftypmp42fixture", "video/mp4", "video") == ".mp4"
