from scripts.recover_photographer_current_images import candidates as photographer_images
from scripts.recover_photographer_sources import safe_link
from scripts.recover_townlove_images import discover as townlove_images, largest_image
from scripts.recover_press_archive_pages import article_image_candidates, focus_image_candidates, select_page_targets, page_capture_matches, read_additional_page_urls
from scripts.recover_flickr_jseattle import extract_image_object, dimensions, largest_photo_variant
from scripts.recover_archiveit import _relevant as archiveit_relevant
from scripts.recover_wayback_related_assets import filter_leads
from scripts.recover_wayback_versions import cdx_sha1_base32
from scripts.recover_wayback_press_media import cdx_sha1
from restore.archive import validate_payload


def test_archiveit_keeps_explicit_common_market_sequel_to_blue_scholars_video() -> None:
    result = {
        "title": 'YouTube - Common Market "Tobacco and Snow Covered Roads" Music Video HQ',
        "original_url": "http://www.youtube.com/watch?v=nR81pG2DI5A",
        "result_text": "A Sequel to Blue Scholars' \"Coffee and Snow\" Director/DP/Editor: Zia Mohajerjasbi",
    }
    assert archiveit_relevant(result)
    assert not archiveit_relevant({"title": "Common Market video", "original_url": "https://example.org/video"})


def test_wayback_asset_filter_can_target_original_page_and_caption() -> None:
    leads = {
        "https://images.example/cover.jpg": {
            "alt_texts": ["Coffee & Snow 2 Cover Art"],
            "referrers": [{"page_url": "https://bluescholars.bandcamp.com/album/coffee-snow-2"}],
        },
        "https://images.example/logo.jpg": {
            "alt_texts": ["Logo"],
            "referrers": [{"page_url": "https://bluescholars.bandcamp.com/album/coffee-snow-2"}],
        },
    }
    assert list(filter_leads(leads, "bluescholars.bandcamp.com/album/coffee-snow-2", "cover art")) == [
        "https://images.example/cover.jpg"
    ]


def test_press_article_images_excludes_template_and_selects_largest_srcset() -> None:
    markup = b'''<html><body>
      <header><img src="/site-logo.png"></header>
      <article><div class="entry-content">
        <img src="/photo-small.jpg" srcset="/photo-small.jpg 200w, /photo-large.jpg 1000w">
        <img src="https://pixel.example/p.gif">
      </div></article>
      <img src="/footer-badge.png">
    </body></html>'''
    assert article_image_candidates(markup, "https://news.example/story/") == [
        "https://news.example/photo-small.jpg", "https://news.example/photo-large.jpg"
    ]


def test_press_image_extraction_includes_all_entries_on_a_multi_post_page() -> None:
    markup = b'''<html><body><header><img src="/chrome.png"></header>
      <article><div class="entry-content"><img src="/post-one.jpg"></div></article>
      <article><div class="entry-content"><img src="/post-two.jpg"></div></article>
      <footer><img src="/footer.png"></footer></body></html>'''
    assert article_image_candidates(markup, "https://news.example/archive/") == [
        "https://news.example/post-one.jpg", "https://news.example/post-two.jpg"
    ]


def test_focused_press_page_filters_image_sources_before_replay() -> None:
    candidates = {
        "https://news.example/target.jpg": [
            {"page_url": "https://news.example/target"},
            {"page_url": "https://news.example/other"},
        ],
        "https://news.example/other.jpg": [{"page_url": "https://news.example/other"}],
    }
    assert focus_image_candidates(candidates, "news.example/target") == {
        "https://news.example/target.jpg": [{"page_url": "https://news.example/target"}]
    }


def test_press_image_only_run_does_not_requery_all_pages() -> None:
    pages = ["https://news.example/one", "https://news.example/two"]
    assert select_page_targets(pages, only_source_page="news.example/one") == []
    assert select_page_targets(pages, only_image_url="https://img.example/a.jpg") == []
    assert select_page_targets(pages, only_page_url="two") == ["https://news.example/two"]


def test_press_image_source_capture_can_exclude_replaced_site_era() -> None:
    capture = {"original_url": "http://food.example/", "timestamp": "20191018040940"}
    assert page_capture_matches(capture, "food.example", "20200101000000")
    assert not page_capture_matches({**capture, "timestamp": "20200930200851"}, "food.example", "20200101000000")
    assert not page_capture_matches(capture, "other.example", "20200101000000")


def test_press_recovery_loads_observed_extra_urls_from_route_graph(tmp_path) -> None:
    path = tmp_path / "routes.json"
    path.write_text('{"urls":[{"url":"https://food.example/blog/a"},"https://food.example/blog/a","javascript:bad"]}')
    assert read_additional_page_urls(str(path)) == ["https://food.example/blog/a"]


def test_townlove_selector_uses_largest_responsive_candidate() -> None:
    selected = largest_image([
        ("https://example.org/photo-50x50.jpg", 50),
        ("https://example.org/photo-705x705.jpg", 705),
        ("https://example.org/photo.jpg", 1_000_000),
    ])
    assert selected == "https://example.org/photo.jpg"
    assert largest_image([("https://example.org/photo-50x50.jpg", 50),
                          ("https://example.org/photo-705x705.jpg", 705)]) == "https://example.org/photo-705x705.jpg"


def test_townlove_recovery_discovers_only_blue_scholars_release_cards() -> None:
    found = townlove_images()
    # The two 50px variants found in the initial pass are deliberately
    # superseded by larger srcset candidates; the manifest retains those old
    # exact-URL checks as provenance.
    assert len(found) == 9
    assert any("cinemetropolis" in url for url in found)
    assert all("blue scholar" in " ".join(item["titles"]).casefold()
               or "prometheus brown" in " ".join(item["titles"]).casefold()
               for item in found.values())


def test_photographer_recovery_selects_one_largest_public_variant_per_photo() -> None:
    found = photographer_images()
    smugmug = [item for item in found if item.get("photo_id")]
    assert len(smugmug) == 31
    assert len({item["photo_id"] for item in smugmug}) == 31
    assert len(found) == 32  # 31 gallery images plus the photographer's article original
    assert any("blue-scholars-061511-84.jpg" in item["url"] for item in found if not item.get("photo_id"))


def test_photographer_source_metadata_redacts_signed_login_tokens() -> None:
    url, redacted = safe_link("https://secure.example/login?goTo=https%3A%2F%2Fexample&goToToken=secret&mode=photos")
    assert "goToToken" not in url
    assert "secret" not in url
    assert "mode=photos" in url
    assert redacted == ["goToToken"]


def test_flickr_image_object_keeps_license_and_creator_provenance() -> None:
    html = b'''<html><script type="application/ld+json">{"@graph":[{"@type":"ImageObject","contentUrl":"https://live.staticflickr.com/1/2_a_b.jpg","license":"https://creativecommons.org/licenses/by-sa/2.0/","author":{"name":"J","url":"https://www.flickr.com/photos/jseattle"}}]}</script></html>'''
    image = extract_image_object(html)
    assert image["contentUrl"].endswith("2_a_b.jpg")
    assert image["license"].endswith("by-sa/2.0/")
    assert image["author"]["url"].endswith("/jseattle")


def test_flickr_jpeg_dimensions_read_source_payload() -> None:
    # Minimal JPEG SOF0 header with a 640 x 480 frame.
    payload = bytes.fromhex("ffd8ffc000110801e00280030111000100021101031101ffd9")
    assert dimensions(payload) == [640, 480]


def test_flickr_largest_variant_comes_from_explicit_page_size_model() -> None:
    html = b'''<script>modelExport: {"main":{"photo-models":[{"data":{"sizes":{"data":{"z":{"data":{"displayUrl":"//live.staticflickr.com/1/photo_z.jpg","width":640,"height":427}},"o":{"data":{"displayUrl":"//live.staticflickr.com/1/photo_o.jpg","width":4000,"height":2667}}}}}}]}}</script>'''
    variant = largest_photo_variant(html)
    assert variant == {"url": "https://live.staticflickr.com/1/photo_o.jpg", "width": 4000, "height": 2667}


def test_wayback_cdx_sha1_uses_unpadded_base32() -> None:
    assert cdx_sha1_base32(b"abc") == "VGMT4NSHA2AWVOR6EVYXQUGCNSONBWE5"


def test_wayback_press_media_digest_and_signature_validation() -> None:
    assert cdx_sha1(b"abc") == "VGMT4NSHA2AWVOR6EVYXQUGCNSONBWE5"
    validate_payload(b"ID3" + b"\0" * 20, "media")
