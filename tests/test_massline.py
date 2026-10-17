import hashlib
import json
from pathlib import Path

from restore.massline import (build_massline_archive, massline_route, massline_summary,
                              rewrite_massline_css, sanitize_massline_html,
                              select_massline_homepage_versions, merge_massline_capture_rows,
                              select_latest_massline_rows, _priority)


def test_massline_routes_distinguish_forum_threads_and_pages():
    first = massline_route("http://masslinemedia.com/smf/index.php?topic=10.0")
    later = massline_route("http://masslinemedia.com/smf/index.php?topic=10.15")
    message = massline_route("http://masslinemedia.com/smf/index.php?topic=10.msg101")

    assert first == "/masslinemedia/forum/topic-10-page-0.html"
    assert later == "/masslinemedia/forum/topic-10-page-15.html"
    assert message == "/masslinemedia/forum/topic-10-message-101.html"
    assert len({first, later, message}) == 3


def test_massline_routes_map_boards_and_legacy_home():
    assert massline_route("http://masslinemedia.com/smf/?board=2.0") == "/masslinemedia/forum/board-2-page-0.html"
    assert massline_route("http://www.masslinemedia.com:80/") == "/masslinemedia/site/index.html"
    assert massline_route("http://masslinemedia.com/index.html") != "/masslinemedia/site/index.html"
    assert massline_route("http://masslinemedia.com/smf/?action=;board=2.0") != massline_route("http://masslinemedia.com/smf/?board=2.0")


def test_massline_summary_reports_board_and_thread_inventory():
    rows = [
        {"timestamp": "20071014053631", "original": "http://masslinemedia.com/smf/?board=1.0", "mimetype": "text/html", "length": "1500"},
        {"timestamp": "20071019151055", "original": "http://masslinemedia.com/smf/index.php?topic=10.0", "mimetype": "text/html", "length": "6602"},
        {"timestamp": "20071019151057", "original": "http://masslinemedia.com/smf/index.php?topic=10.15", "mimetype": "text/html", "length": "6500"},
        {"timestamp": "20061011104325", "original": "http://www.masslinemedia.com:80/", "mimetype": "text/html", "length": "6380"},
    ]

    report = massline_summary(rows)
    assert report["source_rows"] == 4
    assert report["forum_pages"] == 3
    assert report["topic_ids"] == 1
    assert report["board_ids"] == 1
    assert report["years"] == {"2006": 1, "2007": 3}


def test_homepage_version_selection_uses_latest_substantial_capture_per_original_year():
    rows = [
        {"timestamp": "20061011104325", "original": "http://masslinemedia.com/", "mimetype": "text/html", "length": "6380"},
        {"timestamp": "20061231081225", "original": "http://masslinemedia.com:80/", "mimetype": "text/html", "length": "6083"},
        {"timestamp": "20090101120000", "original": "http://masslinemedia.com/", "mimetype": "text/html", "length": "216"},
        {"timestamp": "20090813183844", "original": "http://www.masslinemedia.com:80/", "mimetype": "text/html", "length": "4042"},
        {"timestamp": "20100125025818", "original": "http://masslinemedia.com/", "mimetype": "text/html", "length": "1977"},
    ]

    versions = select_massline_homepage_versions(rows)
    assert [(row["timestamp"], row["length"]) for row in versions] == [
        ("20061231081225", "6083"), ("20090813183844", "4042")]


def test_full_capture_history_merge_keeps_distinct_timestamps_and_digests():
    first = {"timestamp": "20071019151055", "original": "http://masslinemedia.com/smf/?topic=10.0", "digest": "A"}
    alternate = {"timestamp": "20071020051055", "original": "http://masslinemedia.com/smf/?topic=10.0", "digest": "B"}

    merged = merge_massline_capture_rows([first], [first, alternate])
    assert merged == [first, alternate]


def test_restoration_snapshot_uses_latest_pre_replacement_capture_per_url():
    rows = [
        {"timestamp": "20071019151055", "original": "http://masslinemedia.com/smf/?topic=10.0", "mimetype": "text/html", "statuscode": "200"},
        {"timestamp": "20081019151055", "original": "http://www.masslinemedia.com:80/smf/?topic=10.0", "mimetype": "text/html", "statuscode": "200"},
        {"timestamp": "20090901151055", "original": "http://masslinemedia.com/smf/?topic=10.0", "mimetype": "text/html", "statuscode": "200"},
        {"timestamp": "20100101151055", "original": "http://masslinemedia.com/only-later.html", "mimetype": "text/html", "statuscode": "200"},
    ]

    selected = select_latest_massline_rows(rows)
    assert len(selected) == 1
    assert selected[0]["timestamp"] == "20081019151055"


def test_massline_styles_and_forum_assets_are_prioritized_before_forum_threads():
    stylesheet = {"original": "http://masslinemedia.com/smf/Themes/default/style.css", "mimetype": "text/css", "timestamp": "2007"}
    forum_topic = {"original": "http://masslinemedia.com/smf/index.php?topic=10.0", "mimetype": "text/html", "timestamp": "2007"}
    assert _priority(stylesheet) < _priority(forum_topic)


def test_massline_sanitizer_localizes_known_pages_and_disables_forms():
    source = '''<!doctype html><html><head><script>alert(1)</script></head><body>
      <a href="http://masslinemedia.com/smf/index.php?topic=10.0">thread</a>
      <map><area href="/smf/index.php?board=1.0" alt="forum"></map>
      <img src="http://masslinemedia.com/smf/Themes/theme/logo.gif" onerror="alert(1)">
      <img src="/missing.jpg" href="store.html">
      <form action="/smf/index.php"><button>post</button></form></body></html>'''
    mapping = {
        "http://masslinemedia.com/smf/index.php?topic=10.0": "/masslinemedia/forum/topic-10-page-0.html",
        "http://masslinemedia.com/smf/index.php?board=1.0": "/masslinemedia/forum/board-1-page-0.html",
        "http://masslinemedia.com/smf/Themes/theme/logo.gif": "/masslinemedia/assets/logo.gif",
    }

    html, gaps = sanitize_massline_html(source, "http://masslinemedia.com/smf/", mapping, "20071019151055")
    assert 'href="/masslinemedia/forum/topic-10-page-0.html"' in html
    assert 'href="/masslinemedia/forum/board-1-page-0.html"' in html
    assert 'href="store.html"' not in html
    assert 'src="/masslinemedia/assets/logo.gif"' in html
    assert "<script" not in html.lower()
    assert "onerror" not in html.lower()
    assert "Historical posting form disabled" in html
    assert gaps == ["http://masslinemedia.com/missing.jpg"]


def test_massline_sanitizer_tolerates_nodes_removed_during_cleanup():
    source = '<html><head><link rel="stylesheet" href="/missing.css"></head><body><a href="javascript:void(0)"><span>label</span></a><p>content</p></body></html>'
    html, _ = sanitize_massline_html(source, "http://masslinemedia.com/", {}, "20071019151055")
    assert "label" in html
    assert "content" in html


def test_massline_css_keeps_layout_but_localizes_or_disables_dependencies():
    css = "body{background:url('/images/background.gif')} @import url('https://external.invalid/theme.css'); .old{behavior:url(x.htc);width:expression(alert(1))}"
    mapping = {"http://masslinemedia.com/images/background.gif": "/masslinemedia/assets/background.gif"}

    rendered = rewrite_massline_css(css, "http://masslinemedia.com/css/site.css", mapping, "/bluescholars")
    assert "url('/bluescholars/masslinemedia/assets/background.gif')" in rendered
    assert "external.invalid" not in rendered
    assert "behavior:" not in rendered
    assert "expression" not in rendered


def test_massline_builder_writes_local_pages_for_project_subpath(tmp_path):
    root = tmp_path / "project"
    output = tmp_path / "output"
    raw_root = root / "source/massline/raw"
    raw_root.mkdir(parents=True)
    sources = {
        "http://masslinemedia.com/": ("html", "20061011104325", b'<html><head><title>Mass Line</title><link rel="stylesheet" href="/style.css"></head><body><a href="/smf/index.php?topic=10.0">Forum</a><img src="/logo.gif"></body></html>', "text/html"),
        "http://masslinemedia.com/smf/index.php?topic=10.0": ("html", "20071019151055", b'<html><head><title>First topic</title></head><body><p>Original post text</p></body></html>', "text/html"),
        "http://masslinemedia.com/style.css": ("css", "20061011104325", b"body{background:#fff}", "text/css"),
        "http://masslinemedia.com/logo.gif": ("image", "20061011104325", b"GIF89a\x01\x00\x01\x00", "image/gif"),
        "http://masslinemedia.com/blocked.jpg": ("html", "20160120080108", b"<html><body>Archive challenge</body></html>", "text/html"),
    }
    resources = {}
    for url, (kind, timestamp, body, mime) in sources.items():
        digest = hashlib.sha256(body).hexdigest()
        raw_path = Path("source/massline/raw") / (digest + "." + {"html": "html", "css": "css", "image": "gif"}[kind])
        (root / raw_path).write_bytes(body)
        resources[url] = {"kind": kind, "timestamp": timestamp, "raw_path": raw_path.as_posix(), "sha256": digest, "mimetype": mime}
    variant_body = b'<html><head><title>Later Mass Line home</title></head><body><p>Later captured homepage</p></body></html>'
    variant_digest = hashlib.sha256(variant_body).hexdigest()
    variant_path = Path("source/massline/raw") / ("homepage-2009-" + variant_digest + ".html")
    (root / variant_path).write_bytes(variant_body)
    earlier_topic = b'<html><head><title>Earlier topic capture</title></head><body><p>Older forum text</p></body></html>'
    earlier_digest = hashlib.sha256(earlier_topic).hexdigest()
    earlier_path = Path("source/massline/raw") / (earlier_digest + ".html")
    (root / earlier_path).write_bytes(earlier_topic)
    topic_url = "http://masslinemedia.com/smf/index.php?topic=10.0"
    (root / "source").mkdir(exist_ok=True)
    (root / "source/massline.json").write_text(json.dumps({"resources": resources, "homepage_variants": [{
        "year": "2009", "canonical_url": "http://masslinemedia.com/", "timestamp": "20090813183844",
        "raw_path": variant_path.as_posix(), "sha256": variant_digest, "status": "recovered"
    }], "resource_variants": [{
        "kind": "html", "source_url": topic_url, "canonical_url": topic_url, "timestamp": "20071001151055",
        "raw_path": earlier_path.as_posix(), "sha256": earlier_digest, "status": "recovered"
    }]}), encoding="utf-8")

    report = build_massline_archive(root, output, "/bluescholars", candidate=False)
    home = (output / "masslinemedia/site/index.html").read_text(encoding="utf-8")
    topic = (output / "masslinemedia/forum/topic-10-page-0.html").read_text(encoding="utf-8")
    homepage_2009 = (output / "masslinemedia/site/home-2009.html").read_text(encoding="utf-8")
    earlier_topic_page = (output / "masslinemedia/forum/topic-10-page-0--capture-20071001151055.html").read_text(encoding="utf-8")
    assert report["status"] == "built"
    assert report["homepage_variants"] == 1
    assert "href=\"/bluescholars/masslinemedia/forum/topic-10-page-0.html\"" in home
    assert "src=\"/bluescholars/masslinemedia/assets/" in home
    assert "Original post text" in topic
    assert "Later captured homepage" in homepage_2009
    index_html = (output / "masslinemedia/index.html").read_text(encoding="utf-8")
    assert "home-2009.html" in index_html
    assert 'href="/bluescholars/masslinemedia/forum/index.html"' in index_html
    forum_index_html = (output / "masslinemedia/forum/index.html").read_text(encoding="utf-8")
    assert 'href="/bluescholars/masslinemedia/forum/topic-10-page-0.html"' in forum_index_html
    assert "Older forum text" in earlier_topic_page
    assert "Earlier topic capture" in (output / "masslinemedia/alternate-captures/index.html").read_text(encoding="utf-8")
    assert (output / "masslinemedia/index.html").is_file()
    assert (output / "masslinemedia/forum/index.html").is_file()
    assert not (output / "masslinemedia/site/blocked.jpg").exists()
