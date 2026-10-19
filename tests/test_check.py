from pathlib import Path

from restore.check import check


def test_offline_check_ignores_extension_named_route_directories(tmp_path):
    output=tmp_path/'_candidate'
    (output/'index.html').parent.mkdir(parents=True)
    (output/'index.html').write_text('<html><body>archive</body></html>')
    (output/'lj/comments/16015.html/49039').mkdir(parents=True)
    assert check(output)==[]


def test_offline_check_allows_same_site_meta_refresh_to_existing_page(tmp_path):
    output = tmp_path / "_candidate"
    (output / "masslinemedia/forum").mkdir(parents=True)
    (output / "massline-forums").mkdir(parents=True)
    (output / "masslinemedia/forum/index.html").write_text(
        '<meta http-equiv="refresh" content="0; url=/massline-forums/index.html">')
    (output / "massline-forums/index.html").write_text("<h1>Forum archive</h1>")

    assert check(output) == []


def test_offline_check_rejects_remote_meta_refresh(tmp_path):
    output = tmp_path / "_candidate"
    output.mkdir()
    (output / "index.html").write_text(
        '<meta http-equiv="refresh" content="0; url=https://example.invalid/">')

    errors = check(output)
    assert any("remote automatic resource" in error for error in errors)
