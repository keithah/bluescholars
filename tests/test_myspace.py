import json
from pathlib import Path

from restore.myspace import _sanitize, build_myspace_archive


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
