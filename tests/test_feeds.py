import hashlib
from pathlib import Path

import pytest

from restore.feeds import collect_feed_entries
from restore.build import build
from restore.state import State, write_json
from restore.urls import HOME, TARGET


def test_collect_feed_entries_keeps_original_text_and_latest_feed_provenance(tmp_path):
    feeds = tmp_path / "recovery/captured-sources/2026-10-18/feeds"
    feeds.mkdir(parents=True)
    (feeds / "20100401000000-feed.xml").write_text('''<?xml version="1.0"?>
    <rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
      <item><title>Old title</title><link>http://bluescholars.com/blog/post/</link>
        <pubDate>Mon, 01 Mar 2010 12:00:00 +0000</pubDate>
        <content:encoded><![CDATA[<p>Original archived text.</p>]]></content:encoded>
      </item>
      <item><title>Only in root feed</title><link>http://bluescholars.com/older-feed-post/</link>
        <content:encoded><![CDATA[<p>Root feed text.</p>]]></content:encoded></item>
    </channel></rss>''', encoding="utf-8")
    (feeds / "20100501000000-blog-feed.xml").write_text('''<?xml version="1.0"?>
    <rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
      <item><title>Latest title</title><link>http://bluescholars.com/blog/post/</link>
        <pubDate>Mon, 01 Mar 2010 12:00:00 +0000</pubDate>
        <content:encoded><![CDATA[<p>Revised archived text.</p>]]></content:encoded>
      </item>
      <item><title>External item</title><link>https://example.org/not-ours</link>
        <content:encoded><![CDATA[not ours]]></content:encoded></item>
    </channel></rss>''', encoding="utf-8")

    entries = collect_feed_entries(tmp_path)

    assert len(entries) == 2
    entry = entries["http://bluescholars.com/blog/post"]
    assert entry["title"] == "Latest title"
    assert entry["content"] == "<p>Revised archived text.</p>"
    assert entry["feed_capture"] == "20100501000000"
    assert entry["feed_path"].endswith("20100501000000-blog-feed.xml")
    assert entries["http://bluescholars.com/older-feed-post"]["feed_url"] == "http://bluescholars.com/feed/"


@pytest.mark.parametrize("base", ["", "/bluescholars"])
def test_candidate_renders_feed_body_with_visible_provenance_and_no_remote_image(tmp_path, base):
    (tmp_path / "source").mkdir()
    (tmp_path / "public").mkdir()
    (tmp_path / "recovery/seeds").mkdir(parents=True)
    write_json(tmp_path / "recovery/seeds/inventory.json", {"pages": [{"original_url": HOME, "capture": TARGET}], "assets": []})
    write_json(tmp_path / "source/catalog.json", {"version": 1, "resources": {}})
    write_json(tmp_path / "source/review.json", {"publish_approved": False, "visual_reviewed": False})
    (tmp_path / "public/archive-ui.css").write_text("", encoding="utf-8")
    feed_dir = tmp_path / "recovery/captured-sources/2026-10-18/feeds"
    feed_dir.mkdir(parents=True)
    (feed_dir / "20100413023239-blog-feed.xml").write_text('''<?xml version="1.0"?>
    <rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
      <item><title>Feed sourced article</title><link>http://bluescholars.com/blog/2010/04/feed-post/</link>
        <pubDate>Mon, 12 Apr 2010 16:18:20 +0000</pubDate>
        <content:encoded><![CDATA[<p>Actual text from the saved feed.</p><a href="http://bluescholars.com/blog/2010/04/feed-post/attachment/">See linked photo</a><script>bad()</script><img src="https://remote.example/image.jpg">]]></content:encoded>
      </item>
    </channel></rss>''', encoding="utf-8")

    State(tmp_path).seed()
    report = build(tmp_path, tmp_path / "_candidate", base, candidate=True)
    page = (tmp_path / "_candidate/2009/blog/2010/04/feed-post/index.html").read_text(encoding="utf-8")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, "html.parser")

    assert "Actual text from the saved feed." in page
    assert "captured in an archived WordPress feed" in page
    assert "20100413023239" in page
    assert "remote.example" not in page
    assert "<script>bad()</script>" not in page
    assert "See linked photo" in page
    assert (tmp_path / "_candidate/2009/blog/2010/04/feed-post/attachment/index.html").is_file()
    prefix = base + "/" if base else "/"
    css = soup.find("link", rel="stylesheet", href=True)["href"]
    script = soup.find("script", src=True)["src"]
    for resource in (css, script):
        assert resource.startswith(prefix)
        local = resource.removeprefix(base).lstrip("/").split("?", 1)[0]
        assert (tmp_path / "_candidate" / local).is_file()
    assert soup.find("a", string="Inspect this feed capture")
    assert report["feed_recovered_pages"] == 1
    assert any(p["status"] == "recovered_from_feed" for p in report["pages"])


def test_collect_feed_entries_rejects_changed_saved_snapshot(tmp_path):
    feeds = tmp_path / "recovery/captured-sources/2026-10-18/feeds"
    feeds.mkdir(parents=True)
    path = feeds / "20100401000000-blog-feed.xml"
    body = b'<rss><channel><item><title>x</title><link>http://bluescholars.com/x/</link><description>x</description></item></channel></rss>'
    path.write_bytes(body + b" ")
    write_json(feeds / "index.json", {"feed_snapshots": [{
        "path": path.relative_to(tmp_path).as_posix(), "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(), "feed_url": "http://bluescholars.com/blog/feed/"
    }]})
    with pytest.raises(ValueError, match="manifest check"):
        collect_feed_entries(tmp_path)


def test_state_seed_adds_feed_referenced_media_to_resumable_inventory(tmp_path):
    (tmp_path / "source").mkdir()
    (tmp_path / "recovery/seeds").mkdir(parents=True)
    write_json(tmp_path / "recovery/seeds/inventory.json", {"pages": [], "assets": []})
    feed_dir = tmp_path / "recovery/captured-sources/2026-10-18/feeds"
    feed_dir.mkdir(parents=True)
    (feed_dir / "20100401000000-feed.xml").write_text('''<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
      <item><title>Entry</title><link>http://bluescholars.com/feed-entry/</link>
      <content:encoded><![CDATA[<p><a href="http://bluescholars.com/linked-image/">Open photo</a></p>
        <img src="https://cdn.example/photo.jpg">]]></content:encoded></item>
      </channel></rss>''', encoding="utf-8")

    state = State(tmp_path)
    state.seed()

    article = state.data["resources"]["http://bluescholars.com/feed-entry/"]
    linked = state.data["resources"]["http://bluescholars.com/linked-image/"]
    image = state.data["resources"]["https://cdn.example/photo.jpg"]
    assert article["kind"] == "html"
    assert linked["kind"] == "html"
    assert image["kind"] == "image"
    assert all("feed:20100401000000" in item for item in linked["referrers"])
