import json
from pathlib import Path

from restore.archive import validate_payload
from restore.myspace import index_myspace_assets, recover_myspace_assets, _sanitize, build_myspace_archive


def test_rate_limited_myspace_retry_continues_after_saved_cursor(tmp_path, monkeypatch):
    archive = tmp_path / "recovery/myspace-blue-scholars"
    (archive / "index").mkdir(parents=True)
    (archive / "raw").mkdir()
    raw = archive / "raw/profile.html"
    raw.write_text('''<html><head><link rel="stylesheet" href="https://x.myspacecdn.com/a.css"></head>
      <body><img src="https://x.myspacecdn.com/a.jpg"><img src="https://x.myspacecdn.com/b.jpg">
      <img src="https://x.myspacecdn.com/c.jpg"></body></html>''')
    (archive / "index/acquisition.json").write_text(json.dumps({"records": [{
        "status": "recovered", "raw_path": str(raw.relative_to(tmp_path)),
        "original": "https://myspace.com/bluescholars", "timestamp": "20130623052030"
    }]}))
    urls = [
        ("https://x.myspacecdn.com/a.css", "css"),
        ("https://x.myspacecdn.com/a.jpg", "image"),
        ("https://x.myspacecdn.com/b.jpg", "image"),
        ("https://x.myspacecdn.com/c.jpg", "image"),
    ]
    (archive / "index/cdx-assets.json").write_text(json.dumps({
        "records": [{"url": url, "kind": kind, "source_pages": ["20130623052030"],
                     "index_error": "Wayback CDX HTTP 429"} for url, kind in urls],
        "retry_cursor": {"kind": "image", "url": "https://x.myspacecdn.com/b.jpg"}
    }))

    class Response:
        status_code = 200

        def __init__(self, url):
            self.url = url

        def raise_for_status(self):
            return None

        def json(self):
            return [["timestamp", "original", "statuscode", "mimetype", "digest", "length"],
                    ["20130623052030", self.url, "200", "image/jpeg", "digest", "100"]]

    class Session:
        def __init__(self):
            self.headers = {}
            self.requested = []

        def get(self, endpoint, params, timeout):
            self.requested.append(params["url"])
            return Response(params["url"])

    session = Session()
    monkeypatch.setattr("restore.myspace.requests.Session", lambda: session)

    report = index_myspace_assets(tmp_path, max_urls=2, delay=0, retry_errors=True)

    assert session.requested == ["https://x.myspacecdn.com/c.jpg", "https://x.myspacecdn.com/a.css"]
    assert report["attempted_this_run"] == 2
    saved = json.loads((archive / "index/cdx-assets.json").read_text())
    assert saved["retry_cursor"] == {"kind": "css", "url": "https://x.myspacecdn.com/a.css"}


def test_myspace_retry_queue_does_not_slice_negative_limits(tmp_path, monkeypatch):
    archive = tmp_path / "recovery/myspace-blue-scholars"
    (archive / "index").mkdir(parents=True)
    (archive / "raw").mkdir()
    raw = archive / "raw/profile.html"
    raw.write_text('<img src="https://x.myspacecdn.com/a.jpg"><img src="https://x.myspacecdn.com/b.jpg">')
    (archive / "index/acquisition.json").write_text(json.dumps({"records": [{
        "status": "recovered", "raw_path": str(raw.relative_to(tmp_path)),
        "original": "https://myspace.com/bluescholars", "timestamp": "20130623052030"
    }]}))
    urls = ["https://x.myspacecdn.com/a.jpg", "https://x.myspacecdn.com/b.jpg"]
    (archive / "index/cdx-assets.json").write_text(json.dumps({"records": [
        {"url": url, "kind": "image", "source_pages": ["20130623052030"], "index_error": "HTTP 429"}
        for url in urls
    ]}))

    class Session:
        headers = {}
        def __init__(self): self.requested = []
        def get(self, endpoint, params, timeout):
            self.requested.append(params["url"])
            raise AssertionError("nonpositive limit must not start a request")

    session = Session()
    monkeypatch.setattr("restore.myspace.requests.Session", lambda: session)
    report = index_myspace_assets(tmp_path, max_urls=-1, delay=0, retry_errors=True)
    assert report["attempted_this_run"] == 0
    assert session.requested == []


def test_myspace_movie_param_is_indexed_as_flash(tmp_path, monkeypatch):
    archive = tmp_path / "recovery/myspace-blue-scholars"
    (archive / "index").mkdir(parents=True)
    (archive / "raw").mkdir()
    raw = archive / "raw/profile.html"
    raw.write_text('<object><param name="movie" value="/videos/Main.swf"></object>')
    (archive / "index/acquisition.json").write_text(json.dumps({"records": [{
        "status": "recovered", "raw_path": str(raw.relative_to(tmp_path)), "original": "",
        "timestamp": "20130623052030"
    }]}))

    class Response:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return [["timestamp", "original", "statuscode", "mimetype", "digest", "length"],
                    ["20130623052030", "http://myspace.com/videos/Main.swf", "200",
                     "application/x-shockwave-flash", "digest", "100"]]

    class Session:
        def __init__(self): self.headers = {}; self.urls = []
        def get(self, _endpoint, params, timeout):
            self.urls.append(params["url"])
            return Response()

    session = Session()
    monkeypatch.setattr("restore.myspace.requests.Session", lambda: session)
    index_myspace_assets(tmp_path, max_urls=1, delay=0)
    expected = "http://myspace.com/videos/Main.swf"
    assert session.urls == [expected]
    linked = json.loads((archive / "index/linked-assets.json").read_text())
    assert any(r["url"] == expected and r["kind"] == "flash" for r in linked["records"])


def test_myspace_flash_is_preserved_as_downloadable_inert_media(tmp_path):
    raw = b"CWS\x09\x10\x00\x00\x00preserved flash bytes"
    validate_payload(raw, "flash")
    import pytest
    with pytest.raises(ValueError, match="Flash"):
        validate_payload(b"<html>not a SWF file</html>", "flash")

    page = _sanitize('''<html><head></head><body>
      <object data="https://cdn.example/missing.swf"><param name="movie" value="/videos/Main.swf"></object>
      <embed src="https://cdn.example/Main.swf"></body></html>''', "20130623",
      {"http://myspace.com/videos/Main.swf": "/myspace/assets/main.swf",
       "https://cdn.example/Main.swf": "/myspace/assets/main.swf"}, "/bluescholars",
      "")
    assert page.count('href="/bluescholars/myspace/assets/main.swf"') == 2
    assert 'download=""' in page
    assert "<object" not in page and "<embed" not in page


def test_recover_retries_failed_myspace_asset_when_indexed_kind_changes(tmp_path, monkeypatch):
    archive = tmp_path / "recovery/myspace-blue-scholars"
    (archive / "index").mkdir(parents=True)
    (archive / "index/cdx-assets.json").write_text(json.dumps({"records": [{
        "url": "http://cdn.example/player.swf", "kind": "flash", "source_pages": ["20101203040806"],
        "captures": [{"timestamp": "20101201003249", "original": "http://cdn.example/player.swf"}]
    }]}))
    (archive / "index/assets.json").write_text(json.dumps({"assets": [{
        "url": "http://cdn.example/player.swf", "kind": "image", "status": "failed",
        "error": "Expected image bytes"
    }]}))

    class Payload:
        body = b"CWS\x09\x10\x00\x00\x00preserved flash bytes"
        url = "https://web.archive.org/web/20101201003249id_/http://cdn.example/player.swf"
        headers = {"Content-Type": "application/x-shockwave-flash"}

    class Client:
        def __init__(self, **_kwargs): pass
        def get(self, _url): return Payload()

    monkeypatch.setattr("restore.myspace.ArchiveClient", Client)
    report = recover_myspace_assets(tmp_path, max_files=1, delay=0, retry_failed=False)
    saved = json.loads((archive / "index/assets.json").read_text())["assets"][0]
    assert report["recovered"] == 1
    assert saved["kind"] == "flash" and saved["status"] == "recovered"
    assert (tmp_path / saved["raw_path"]).read_bytes() == Payload.body


def test_myspace_build_preserves_dates_and_strips_remote_loads(tmp_path):
    source = tmp_path / "recovery/myspace-blue-scholars"
    (source / "raw").mkdir(parents=True)
    (source / "index").mkdir()
    html = '''<!doctype html><html><head><title>Blue Scholars</title>
      <link rel="stylesheet" href="https://cdn.example/archived.css">
      <style>body{background:url(https://cdn.example/bg.jpg)}</style>
      <script src="https://cdn.example/app.js"></script></head><body>
      <h1>Blue Scholars</h1><img src="https://cdn.example/profile.jpg" alt="Band">
      <img src="https://cdn.example/missing.jpg" alt="Uncaptured">
      <object><link rel="stylesheet" href="https://cdn.example/nested.css"></object>
      <a href="javascript:runProfileCode()">Unsafe source action</a>
      <a href="/some-page">Relative profile link</a>
      <a href="https://www.myspace.com/bluescholars">Profile</a></body></html>'''
    raw = source / "raw/20070307131210-test.html"
    raw.write_text(html)
    asset = source / "assets/profile.jpg"
    asset.parent.mkdir()
    asset.write_bytes(b"\xff\xd8\xfflocal-image")
    css = source / "assets/theme.css"
    css.write_text("body { color: #123; background-image: url(https://cdn.example/bg.jpg) }")
    (source / "index/assets.json").write_text(json.dumps({"assets": [{
        "url": "https://cdn.example/profile.jpg", "local_path": "/myspace/assets/profile.jpg",
        "raw_path": str(asset.relative_to(tmp_path)), "status": "recovered", "kind": "image"
    }, {
        "url": "https://cdn.example/archived.css", "local_path": "/myspace/assets/theme.css",
        "raw_path": str(css.relative_to(tmp_path)), "status": "recovered", "kind": "css"
    }]}))
    (source / "index/acquisition.json").write_text(json.dumps({"records": [{
        "status": "recovered", "timestamp": "20070307131210", "actual_capture": "20070307131210",
        "raw_path": str(raw), "original": "http://myspace.com/bluescholars", "sha256": "abc"
    }]}))
    result = build_myspace_archive(tmp_path, tmp_path / "_candidate", "/bluescholars")
    page = tmp_path / "_candidate/myspace/2007/20070307131210.html"
    text = page.read_text()
    assert '<meta charset="utf-8"' in text
    assert "Blue Scholars" in text
    assert "Archived source image is unavailable" in text
    assert "javascript:" not in text
    assert 'href="http://myspace.com/some-page"' in text
    assert (tmp_path / "_candidate/myspace/assets/profile.jpg").read_bytes() == asset.read_bytes()
    assert "https://cdn.example/archived.css" not in text
    assert "/bluescholars/myspace/assets/theme.css" in text
    assert "background: url(https://cdn.example/bg.jpg)" not in (tmp_path / "_candidate/myspace/assets/theme.css").read_text()
    assert "cdn.example" not in text
    assert "https://www.myspace.com/bluescholars" in text
    assert (tmp_path / "_candidate/myspace/index.html").exists()
    assert result["recovered_pages"] == 1


def test_real_archived_myspace_markup_with_detached_link_nodes_is_sanitized():
    source = Path(__file__).resolve().parents[1] / "recovery/myspace-blue-scholars/raw/20130623052030-870a6dd67b21.html"
    text = _sanitize(source.read_text(errors="replace"), "20130623052030", {}, "")
    assert "BLUE SCHOLARS · MYSPACE ARCHIVE" in text
    assert "x.myspacecdn.com/new/common/css" not in text


def test_inline_style_localizes_captured_background_and_removes_missing_background():
    html = '''<!doctype html><html><head></head><body>
      <div id="captured" style="background-image:url('/common/images/defaultProfileCovers/cover.jpg')"></div>
      <div id="missing" style="background-image:url('/common/images/defaultProfileCovers/missing.jpg')"></div>
    </body></html>'''
    assets = {"https://myspace.com/common/images/defaultProfileCovers/cover.jpg": "/myspace/assets/cover.jpg"}
    text = _sanitize(html, "20130623052030", assets, "/bluescholars", "http://www.myspace.com/bluescholars")
    assert "url('/bluescholars/myspace/assets/cover.jpg')" in text
    assert "/common/images/missing.jpg" not in text
