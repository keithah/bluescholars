from pathlib import Path

from restore.check import check


def test_offline_check_ignores_extension_named_route_directories(tmp_path):
    output=tmp_path/'_candidate'
    (output/'index.html').parent.mkdir(parents=True)
    (output/'index.html').write_text('<html><body>archive</body></html>')
    (output/'lj/comments/16015.html/49039').mkdir(parents=True)
    assert check(output)==[]
