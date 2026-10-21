import hashlib
import pytest

from restore.linked_origin import LinkedOriginClient, recover_linked_origin_images
from restore.state import State


class Payload:
    def __init__(self, body, url, content_type="image/jpeg"):
        self.body = body
        self.url = url
        self.status = 200
        self.headers = {"content-type": content_type}


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def test_linked_squarespace_image_is_saved_with_origin_provenance(tmp_path):
    state = State(tmp_path)
    url = "https://images.squarespace-cdn.com/content/v1/example/cover.jpg"
    row = state.add(url, "image", "https://www.bluescholars.com/shop/", "20130501000000")
    client = FakeClient(Payload(b"\xff\xd8\xffsource-image", url))

    report = recover_linked_origin_images(state, client, max_files=5)

    saved = state.data["resources"][url]
    raw = tmp_path / saved["raw_path"]
    assert report["recovered"] == 1
    assert raw.read_bytes() == b"\xff\xd8\xffsource-image"
    assert saved["sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
    assert saved["source_type"] == "linked_origin_asset"
    assert saved["source_url"] == url
    assert saved["hints"] == ["20130501000000"]
    assert "actual_capture" not in saved


def test_linked_origin_recovery_refuses_unobserved_or_unapproved_hosts(tmp_path):
    state = State(tmp_path)
    url = "https://example.invalid/cover.jpg"
    state.add(url, "image", "https://www.bluescholars.com/shop/")
    client = FakeClient(Payload(b"\xff\xd8\xffimage", url))

    report = recover_linked_origin_images(state, client, max_files=5)

    assert report["recovered"] == 0
    assert client.urls == []
    assert state.data["resources"][url]["status"] == "queued"


def test_linked_http_source_is_upgraded_only_for_allowlisted_transport():
    client = LinkedOriginClient(delay=0)
    assert client.transport_url("http://images.squarespace-cdn.com/a.jpg") == \
        "https://images.squarespace-cdn.com/a.jpg"
    with pytest.raises(ValueError):
        client.transport_url("http://untrusted.example/a.jpg")


def test_linked_origin_rejects_non_image_payload(tmp_path):
    state = State(tmp_path)
    url = "https://images.squarespace-cdn.com/content/v1/example/cover.jpg"
    state.add(url, "image", "https://www.bluescholars.com/shop/")
    client = FakeClient(Payload(b"<html>not an image</html>", url, "text/html"))

    report = recover_linked_origin_images(state, client, max_files=5)

    assert report["recovered"] == 0
    assert state.data["resources"][url]["status"] == "queued"
    assert state.data["resources"][url]["attempts"][-1]["result"] == "failed"
    assert not list((tmp_path / "recovery/raw").glob("*"))


def test_squarespace_svg_font_is_not_treated_as_an_image(tmp_path):
    state = State(tmp_path)
    url = "https://assets.squarespace.com/universal/fonts/social-icon-font.svg"
    state.add(url, "image", "https://www.bluescholars.com/2013/")
    client = FakeClient(Payload(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", url, "image/svg+xml"))

    report = recover_linked_origin_images(state, client, max_files=5)

    assert report["attempted"] == 0
    assert client.urls == []
