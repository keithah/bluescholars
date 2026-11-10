import hashlib
import json

from restore.artist_sites import EDITIONS, build_artist_sites
from restore.build import add_global_year_navigation
from restore.fallback import choose, page_fallbacks, page_keys


def test_page_keys_match_extensions_permalinks_and_reply_queries():
    assert ('path', 'bluescholars.com', 'events') in page_keys('http://www.bluescholars.com/events.htm')
    assert ('path', 'bluescholars.com', 'events') in page_keys('http://bluescholars.com/events.html')
    flat = page_keys('http://bluescholars.com/geo-in-hawaii-this-week/')
    dated = page_keys('http://bluescholars.com/blog/2010/11/geo-in-hawaii-this-week/?replytocom=5')
    assert ('slug', 'bluescholars.com', 'geo-in-hawaii-this-week') in flat
    assert ('slug', 'bluescholars.com', 'geo-in-hawaii-this-week') in dated
    # A query-only post URL must not fall back to the homepage.
    assert ('path', 'bluescholars.com', '') not in page_keys('http://bluescholars.com/?p=12')
    # Short or numeric last segments are not treated as post slugs.
    assert not any(key[0] == 'slug' for key in page_keys('http://bluescholars.com/blog/page/2/'))


def test_choose_prefers_latest_copy_not_after_the_edition():
    rows = [{'path': '/a/', 'actual_capture': '20080101000000'},
            {'path': '/b/', 'actual_capture': '20110101000000'},
            {'path': '/c/', 'actual_capture': '20150101000000'}]
    assert choose(rows, '20121231235959')['path'] == '/b/'
    assert choose(rows, '20051231235959')['path'] == '/a/'


def test_placeholders_fall_back_to_the_closest_saved_copy():
    report = [
        {'path': '/2007/bio.html', 'canonical_url': 'http://bluescholars.com/bio.html',
         'status': 'recovered', 'actual_capture': '20080314051926'},
        {'path': '/2013/bio.html', 'canonical_url': 'http://bluescholars.com/bio.html',
         'status': 'not_recovered', 'actual_capture': None},
        {'path': '/2009/blog/2010/11/geo/', 'canonical_url': 'http://bluescholars.com/blog/2010/11/geo-in-hawaii/',
         'status': 'recovered', 'actual_capture': '20101218164316'},
        {'path': '/2013/geo-in-hawaii/', 'canonical_url': 'http://bluescholars.com/geo-in-hawaii/',
         'status': 'not_recovered', 'actual_capture': None},
        {'path': '/2013/never-saved/', 'canonical_url': 'http://bluescholars.com/never-saved/',
         'status': 'not_recovered', 'actual_capture': None},
    ]
    fallbacks = page_fallbacks(report)
    assert fallbacks['/2013/bio.html']['path'] == '/2007/bio.html'
    assert fallbacks['/2013/geo-in-hawaii/']['path'] == '/2009/blog/2010/11/geo/'
    assert '/2013/never-saved/' not in fallbacks


def test_links_to_placeholders_open_the_saved_copy_with_its_year():
    page = '<html><head></head><body><a href="/bs/2013/bio.html?year=2021#top">Bio</a></body></html>'
    out = add_global_year_navigation(page, 2021, '/bs', '/ui.css', '/ui.js',
                                     {'/2007/bio.html': 2008}, {2008: '/2007/', 2021: '/2013/'},
                                     fallbacks={'/2013/bio.html': '/2007/bio.html'})
    assert 'href="/bs/2007/bio.html?year=2008#top"' in out


def test_artist_edition_opens_a_page_kept_by_another_edition(tmp_path):
    body = b'<!doctype html><html><head><title>Post</title></head><body><p>Saved</p></body></html>'
    root = b'<!doctype html><html><head><title>Home</title></head><body><a href="/blog/post">Post</a></body></html>'
    def saved(content, capture):
        digest = hashlib.sha256(content).hexdigest()
        raw = 'recovery/artist-sites/raw/' + digest + '.html'
        (tmp_path / raw).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / raw).write_bytes(content)
        return {'kind': 'html', 'raw_path': raw, 'sha256': digest, 'actual_capture': capture}
    old, new = EDITIONS['sabzi.co'][1], EDITIONS['sabzi.co'][2]
    manifest = {'version': 1, 'editions': {
        'sabzi.co/' + old['id']: {'domain': 'sabzi.co', 'edition': old, 'missing': [],
            'resources': {'http://sabzi.co/blog/post': saved(body, '20160101000000')}},
        'sabzi.co/' + new['id']: {'domain': 'sabzi.co', 'edition': new,
            'missing': [{'url': 'http://sabzi.co/blog/post', 'kind': 'html'}],
            'resources': {'http://sabzi.co/': saved(root, new['capture'])}},
    }}
    path = tmp_path / 'recovery/artist-sites/manifest.json'
    path.write_text(json.dumps(manifest))
    output = tmp_path / '_candidate'
    output.mkdir()

    report = build_artist_sites(tmp_path, output, '/bs', candidate=True)
    home = (output / 'sabzi' / new['id'] / 'index.html').read_text()
    assert 'href="/bs/sabzi/' + old['id'] + '/blog/post/index.html"' in home
    stub = (output / 'sabzi' / new['id'] / 'blog/post/index.html').read_text()
    assert 'http-equiv="refresh"' in stub and '/bs/sabzi/' + old['id'] + '/blog/post/index.html' in stub
    assert report['editions']['sabzi.co/' + new['id']]['pages_from_other_editions'] == 1
