from restore.artist_sites import (
    EDITIONS,
    build_artist_sites,
    edition_route,
    local_asset_path,
    _pick_capture,
    _is_dynamic_avatar,
    promote_artist_sites,
    sanitize_artist_html,
)
import hashlib
import json


def test_artist_site_editions_keep_distinct_site_generations():
    assert [edition["id"] for edition in EDITIONS["prometheusbrown.com"]] == [
        "2008", "2009", "2010", "2013", "2016", "2019", "2022"
    ]


def test_capture_selection_uses_nearest_linked_capture_without_crossing_gap_limit():
    rows = [{"original": "http://sabzi.co/holla/", "timestamp": "20150223065135", "mimetype": "text/html"}]
    selected = _pick_capture(rows, "http://sabzi.co/holla", "20130704141640", lookahead_days=730)
    assert selected[0]["timestamp"] == "20150223065135"
    assert _pick_capture(rows, "http://sabzi.co/holla", "20130704141640", lookahead_days=365) == []
    assert [edition["id"] for edition in EDITIONS["sabzi.co"]] == [
        "2013", "2016", "2019", "2022"
    ]


def test_edition_routes_keep_each_domain_and_query_page_local():
    assert edition_route("prometheusbrown.com", "2013", "http://prometheusbrown.com/about.html") == "/prometheusbrown/2013/about.html"
    assert edition_route("sabzi.co", "2019", "http://sabzi.co/blog?format=amp").startswith("/sabzi/2019/blog/_q_")
    assert edition_route("sabzi.co", "2019", "http://sabzi.co/blog/entry") == "/sabzi/2019/blog/entry/index.html"

def test_external_archived_html_is_namespaced_under_its_source_host():
    route = edition_route("prometheusbrown.com", "2009", "http://imeem.com/embedsearch/E6E6E6/")
    assert route.startswith("/prometheusbrown/2009/_external/imeem.com/")


def test_artist_html_is_localized_and_active_platform_code_is_removed():
    source = '''<!doctype html><html><head><title>Saved</title><base href="https://remote.test/">
      <link rel="stylesheet" href="/site.css"><script src="https://remote.test/app.js"></script>
      <link rel="icon" href="/favicon.ico"></head><body><a href="/about">About</a><a href="https://example.org">Out</a>
      <a href="javascript:alert(1)">Bad</a><table background="https://remote.test/bg.gif"></table>
      <img src="/photo.jpg" href="/media" onload="steal()"><iframe src="https://player.test/x"></iframe>
      <form action="https://example.org"><button>Buy</button></form></body></html>'''
    mapping = {
        "http://sabzi.co/site.css": "/sabzi/2019/assets/site.css",
        "http://sabzi.co/about": "/sabzi/2019/about/index.html",
        "http://sabzi.co/photo.jpg": "/sabzi/2019/assets/photo.jpg",
        "http://sabzi.co/favicon.ico": "/sabzi/2019/assets/favicon.ico",
    }
    rendered, missing = sanitize_artist_html(source, "http://sabzi.co/", mapping, "20191023135247")
    assert 'href="/sabzi/2019/assets/site.css"' in rendered
    assert 'href="/sabzi/2019/about/index.html"' in rendered
    assert 'src="/sabzi/2019/assets/photo.jpg"' in rendered
    assert 'href="/sabzi/2019/assets/favicon.ico"' in rendered
    assert "remote.test/app.js" not in rendered
    assert "<iframe" not in rendered and "<form" not in rendered
    assert "onload" not in rendered
    assert "javascript:" not in rendered and "remote.test/bg.gif" not in rendered
    assert "<base" not in rendered
    assert 'href="https://web.archive.org/web/20191023135247id_/http://example.org"' in rendered
    assert 'href="/media"' not in rendered
    assert missing == ["http://player.test/x"]
    assert "web.archive.org/web/" in rendered


def test_local_asset_paths_are_stable_and_retain_safe_suffixes():
    path = local_asset_path("sabzi.co", "2019", "https://static.example/image/photo%20one.jpg?width=900")
    assert path.startswith("/sabzi/2019/assets/")
    assert path.endswith(".jpg")
    assert ".." not in path


def test_dynamic_gravatar_references_are_classified_as_source_gaps():
    assert _is_dynamic_avatar("http://www.gravatar.com/avatar/abc?s=50")
    assert not _is_dynamic_avatar("http://example.org/avatar/abc.jpg")

def test_sanitizer_skips_nodes_removed_during_dependency_cleanup():
    source = ('<html><head><link rel="stylesheet" href="/missing.css">'
              '<link rel="preload" href="/missing.js"><link rel="alternate" href="/feed">'
              '<link rel="archives" href="/?m=200803"></head><body><p>Kept</p></body></html>')
    rendered, _ = sanitize_artist_html(source, "http://sabzi.co/", {}, "20191023135247")
    assert "<p>Kept</p>" in rendered
    assert "alternate" not in rendered and "archives" not in rendered and "/feed" not in rendered

def test_missing_original_image_is_marked_with_a_source_link():
    rendered, missing = sanitize_artist_html(
        '<html><head></head><body><img src="/old-photo.jpg" alt=""></body></html>',
        "http://sabzi.co/", {}, "20191023135247")
    assert "Archived image unavailable" in rendered
    assert "old-photo.jpg" in rendered
    assert missing == ["http://sabzi.co/old-photo.jpg"]


def test_artist_build_uses_only_saved_resources_under_project_subpath(tmp_path):
    html = b'''<!doctype html><html><head><title>Sabzi</title><link rel="stylesheet" href="http://sabzi.co/site.css">
    <script src="https://remote.test/app.js"></script></head><body><img src="http://sabzi.co/photo.jpg">
    <a href="/about">About</a></body></html>'''
    css = b"body{background-image:url('/photo.jpg')}"
    image = b"\xff\xd8\xfftest"
    resources = {}
    for url, kind, body, suffix in (
        ("http://sabzi.co/", "html", html, ".html"),
        ("http://sabzi.co/site.css", "css", css, ".css"),
        ("http://sabzi.co/photo.jpg", "image", image, ".jpg"),
    ):
        digest = hashlib.sha256(body).hexdigest()
        raw = "recovery/artist-sites/raw/" + digest + suffix
        path = tmp_path / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        resources[url] = {"kind": kind, "raw_path": raw, "sha256": digest,
                          "actual_capture": "20160306112646"}
    manifest = {"version": 1, "editions": {"sabzi.co/2016": {
        "domain": "sabzi.co", "edition": EDITIONS["sabzi.co"][1],
        "resources": resources, "missing": []
    }}}
    path = tmp_path / "recovery/artist-sites/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest))
    output = tmp_path / "_candidate"
    output.mkdir()

    report = build_artist_sites(tmp_path, output, "/bluescholars", candidate=True)
    page = output / "sabzi/2016/index.html"
    rendered = page.read_text()
    assert report["editions"]["sabzi.co/2016"]["recovered_pages"] == 1
    assert 'src="/bluescholars/sabzi/2016/assets/' in rendered
    assert 'href="/bluescholars/sabzi/2016/assets/' in rendered
    assert "remote.test/app.js" not in rendered
    assert "Content-Security-Policy" in rendered
    assert (output / "prometheusbrown/index.html").is_file()

def test_artist_build_omits_unsafe_svg_and_counts_the_source_gap(tmp_path):
    html = b'<html><head></head><body><img src="/unsafe.svg" alt="Archived logo"></body></html>'
    svg = b'<!DOCTYPE svg [<!ENTITY x "bad">]><svg xmlns="http://www.w3.org/2000/svg"><text>&x;</text></svg>'
    resources = {}
    for url, kind, body, ext in (("http://sabzi.co/", "html", html, ".html"),
                                 ("http://sabzi.co/unsafe.svg", "image", svg, ".svg")):
        digest = hashlib.sha256(body).hexdigest()
        raw = "recovery/artist-sites/raw/" + digest + ext
        path = tmp_path / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        resources[url] = {"kind": kind, "raw_path": raw, "sha256": digest,
                          "actual_capture": "20160306112646"}
    manifest = {"editions": {"sabzi.co/2016": {"domain": "sabzi.co",
        "edition": EDITIONS["sabzi.co"][1], "resources": resources, "missing": []}}}
    path = tmp_path / "recovery/artist-sites/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest))
    output = tmp_path / "_candidate"
    output.mkdir()
    report = build_artist_sites(tmp_path, output, candidate=True)
    assert report["editions"]["sabzi.co/2016"]["unrenderable_assets"] == ["http://sabzi.co/unsafe.svg"]
    assert not (output / "sabzi/2016/assets").exists()
    assert 'alt="Archived image unavailable"' in (output / "sabzi/2016/index.html").read_text()


def test_artist_source_promotion_is_explicit_hash_checked_and_holds_later_captures(tmp_path):
    html = b"<!doctype html><html><head><title>Saved</title></head><body>Source</body></html>"
    image = b"\xff\xd8\xfflater"
    records = {}
    for url, kind, body, future in (
        ("http://sabzi.co/", "html", html, False),
        ("http://sabzi.co/late.jpg", "image", image, True),
    ):
        digest = hashlib.sha256(body).hexdigest()
        raw = "recovery/artist-sites/raw/" + digest + (".html" if kind == "html" else ".jpg")
        path = tmp_path / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        records[url] = {"kind": kind, "status": "recovered", "raw_path": raw, "sha256": digest,
                        "actual_capture": "20191023135247", "compatibility_review_required": future}
    manifest_path = tmp_path / "recovery/artist-sites/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"version": 1, "editions": {"sabzi.co/2019": {
        "domain": "sabzi.co", "edition": EDITIONS["sabzi.co"][2], "resources": records, "missing": []
    }}}))

    import pytest
    with pytest.raises(ValueError, match="--reviewed"):
        promote_artist_sites(tmp_path)
    result = promote_artist_sites(tmp_path, reviewed=True)
    approved = json.loads((tmp_path / "source/artist-sites.json").read_text())
    promoted = approved["editions"]["sabzi.co/2019"]["resources"]
    assert result["promoted"] == 1 and result["skipped_later_captures"] == 1
    assert "http://sabzi.co/" in promoted
    assert "http://sabzi.co/late.jpg" not in promoted
    review = json.loads((tmp_path / "source/review.json").read_text())
    assert review["publish_approved"] is False and review["visual_reviewed"] is False
