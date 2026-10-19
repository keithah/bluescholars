from restore.recovery_206proof import select_latest_vanilla
from restore.proof206 import build_206proof_archive


def test_select_latest_vanilla_keeps_queries_and_excludes_later_editions():
    rows = [
        {"timestamp": "20101201000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120401000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120402000000", "original": "http://206proof.com/forum/?page=2", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20130801000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120403000000", "original": "http://206proof.com/forum/bad", "statuscode": "404", "mimetype": "text/html"},
        {"timestamp": "20120404000000", "original": "http://206proof.com/forum/style.css", "statuscode": "200", "mimetype": "text/css"},
    ]

    selected = select_latest_vanilla(rows)

    assert [(r["timestamp"], r["original"]) for r in selected] == [
        ("20120401000000", "http://206proof.com/forum/"),
        ("20120402000000", "http://206proof.com/forum/?page=2"),
    ]


def test_select_latest_vanilla_keeps_host_alias_as_distinct_source_identity():
    rows = [
        {"timestamp": "20120101000000", "original": "http://206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
        {"timestamp": "20120301000000", "original": "http://www.206proof.com/forum/", "statuscode": "200", "mimetype": "text/html"},
    ]
    assert len(select_latest_vanilla(rows)) == 2


def test_build_preserves_separate_206proof_editions_and_localizes_captured_content(tmp_path):
    import hashlib
    import json

    root = tmp_path
    output = root / "_candidate"
    output.mkdir()
    source = root / "recovery/206proof/raw"
    source.mkdir(parents=True)
    pages = [
        ("http://206proof.com/", "20071012230232", '<!doctype html><html><head><title>206Proof home</title><link rel="stylesheet" href="/themes/206Proof/styles/default/vanilla.css"></head><body><h1>206Proof</h1><a href="/forum/">Forum</a></body></html>'),
        ("http://www.206proof.com/forum/", "20120305080527", '<!doctype html><html><head><title>206Proof Forum</title><link rel="stylesheet" href="/forum/themes/206Proof/styles/default/vanilla.css"></head><body><h1>General</h1><a href="/forum/comments.php?DiscussionID=9">A recovered topic</a><a href="/forum/comments.php?DiscussionID=10">Uncaptured variant</a><a href="/forum/missing.php">Missing topic</a><form action="/forum/post.php"><button>Post</button></form><img src="/forum/uploads/avatar.jpg"><script src="http://tracker.test/ad.js"></script></body></html>'),
        ("http://206proof.com/forum/comments.php?DiscussionID=9", "20120305090000", '<!doctype html><html><head><title>A recovered topic</title></head><body><h1>A recovered topic</h1><a href="/forum/">Back to discussions</a></body></html>'),
        ("http://206proof.com/4um/", "20130824231448", '<!doctype html><html><head><title>Seattle Message Board</title></head><body><h1>vBulletin edition</h1></body></html>'),
    ]
    assets = [
        ("http://206proof.com/forum/themes/206Proof/styles/default/vanilla.css", "css", b"body{background-image:url('/forum/uploads/avatar.jpg');color:#222}"),
        ("http://206proof.com/forum/uploads/avatar.jpg", "image", b"\xff\xd8\xffavatar"),
    ]
    records = []
    for url, timestamp, body in pages:
        digest = hashlib.sha256(body.encode()).hexdigest()
        path = source / f"{digest}.html"
        path.write_bytes(body.encode())
        records.append({"kind": "html", "result": "recovered", "original": url,
                        "requested_capture": timestamp, "actual_capture": timestamp,
                        "raw_path": str(path.relative_to(root)), "bytes": len(body), "sha256": digest})
    for url, kind, body in assets:
        digest = hashlib.sha256(body).hexdigest()
        suffix = ".css" if kind == "css" else ".jpg"
        path = source / f"{digest}{suffix}"
        path.write_bytes(body)
        records.append({"kind": kind, "result": "recovered", "original": url,
                        "requested_capture": "20120305070000", "actual_capture": "20120305070000",
                        "raw_path": str(path.relative_to(root)), "bytes": len(body), "sha256": digest})
    manifest = root / "recovery/206proof/recovered-resources.json"
    manifest.write_text(json.dumps({"resources": records}))

    report = build_206proof_archive(root, output, "/bluescholars", candidate=True)

    assert report["status"] == "built"
    assert (output / "206proof/index.html").is_file()
    assert (output / "206proof/2007/site/index.html").is_file()
    assert (output / "206proof/vanilla/forum/index.html").is_file()
    assert (output / "206proof/vbulletin/4um/index.html").is_file()
    index = (output / "206proof/index.html").read_text()
    assert "/bluescholars/206proof/vanilla/index.html" in index
    assert "/bluescholars/206proof/vanilla/forum/index.html" in (output / "206proof/vanilla/index.html").read_text()
    old_home = (output / "206proof/2007/site/index.html").read_text()
    assert "stylesheet" in old_home and "2007 theme CSS was not captured" in old_home
    note_css = (output / "206proof/archive-note.css").read_text()
    assert ".proof206-note" in note_css and ".206proof-archive-note" not in note_css
    vanilla = (output / "206proof/vanilla/forum/index.html").read_text()
    assert "/bluescholars/206proof/vanilla/forum/comments/" in vanilla
    assert "Uncaptured variant" in vanilla and "/bluescholars/206proof/vanilla/missing/" not in vanilla.split("Uncaptured variant")[0][-150:]
    assert "tracker.test" not in vanilla and "<form" not in vanilla
    assert "A recovered topic" in vanilla
    assert "2012" in vanilla
    assert "src=\"/bluescholars/206proof/assets/" in vanilla
    from bs4 import BeautifulSoup
    css_link = next(link["href"] for link in BeautifulSoup(vanilla, "html.parser").find_all("link", rel="stylesheet") if "archive-note.css" not in link["href"])
    css = (output / css_link.removeprefix("/bluescholars/")).read_text()
    assert "/bluescholars/206proof/assets/" in css
    assert "206proof.com" not in css
    assert "<script" not in vanilla.lower()
    assert "https://web.archive.org" not in vanilla
    gap = next((output / "206proof/vanilla/missing").glob("*.html"))
    assert "not been recovered" in gap.read_text()
    assert "206Proof archive" in (output / "206proof/index.html").read_text()
