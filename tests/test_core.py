import json
import pytest
from restore.urls import original_url, route, kind_for, is_site, base_path, asset_route
from restore.discover import discover_html, discover_css
from restore.state import State

HOME = 'http://bluescholars.com/'

@pytest.mark.parametrize('url',[
 'https://web.archive.org/web/20210529010817/http://bluescholars.com/blog?offset=1',
 '/web/20210529010817id_/http://bluescholars.com/blog?offset=1',
 'https://web.archive.org/web/20210529010817im_/http%3A//bluescholars.com/blog?offset=1',
])
def test_unwrap_replay_preserves_query(url):
    assert original_url(url, HOME) == 'http://bluescholars.com/blog?offset=1'

def test_unwrap_does_not_decode_original_path():
    assert original_url('/web/20210529010817/http://bluescholars.com/a%2Fb', HOME).endswith('/a%2Fb')

def test_relative_asset_resolution():
    assert original_url('../images/a.jpg', HOME+'blog/') == HOME+'images/a.jpg'

@pytest.mark.parametrize('bad',['javascript:alert(1)','data:text/html,x','mailto:x@y.z','https://x:y@bluescholars.com/','file:///tmp/x'])
def test_non_http_and_credentials_rejected(bad):
    assert original_url(bad, HOME) == ''

def test_crawl_scope():
    assert is_site('https://www.bluescholars.com/blog')
    assert not is_site('https://bluescholars.com.evil.example/blog')
    assert not is_site('https://youtube.com/x')

def test_explicit_pagination():
    assert route(HOME+'blog?offset=1362122742000') == '/blog/page/2/'
    assert route(HOME+'blog?offset=1358016466000') == '/blog/page/3/'
    assert route(HOME+'blog?offset=111') != route(HOME+'blog?offset=112')
    assert route(HOME+'blog#top') == '/blog/'

def test_different_query_parameters_do_not_collapse():
    assert route(HOME+'blog?offset=1362122742000&tag=live') != '/blog/page/2/'

def test_unusually_long_observed_endpoint_gets_a_safe_static_route():
    endpoint=HOME+'api/blog-like-count/' + ','.join(['51b8c857e4b05bf73912a431']*80)
    result=route(endpoint)
    assert result.startswith('/archive-path/')
    assert len(result)<64

def test_legacy_file_routes_keep_html_paths_without_index_conflicts():
    assert route(HOME+'artistedition/01_a.html') == '/artistedition/01_a.html'
    assert route(HOME+'artistedition/index.html') == '/artistedition/'

def test_css_asset_route_uses_a_css_extension_for_browser_mime_detection():
    assert asset_route('https://static1.squarespace.com/site.css','css').endswith('.css')

@pytest.mark.parametrize('bad',['/../private','/%2e%2e/private','//evil.example','/x/../../private','/x%2fy','/x\\y'])
def test_unsafe_base_paths(bad):
    with pytest.raises(ValueError): base_path(bad)

def test_base_path_normalization():
    assert base_path('/') == ''
    assert base_path('/bluescholars/') == '/bluescholars'

def test_discover_lazy_images_and_styles_not_external_pages():
    refs=discover_html('''<base href="https://evil.example/"><a href="/blog?offset=1">old</a>
    <a href="https://other.example/">outbound</a><img data-src="//cdn.example/a.jpg"
    src="data:image/gif,x" srcset="https://cdn.example/b.jpg 2x">
    <link rel="stylesheet" href="/site.css"><script src="/old.js"></script>
    <iframe src="https://www.youtube.com/embed/ABCDEFGHIJK"></iframe>
    <div style="background-image:url('/bg.png')"></div>''',HOME)
    urls={r['url'] for r in refs}
    assert HOME+'blog?offset=1' in urls
    assert 'http://cdn.example/a.jpg' in urls
    assert 'https://cdn.example/b.jpg' in urls
    assert HOME+'site.css' in urls and HOME+'bg.png' in urls
    assert HOME+'old.js' not in urls
    assert 'https://other.example/' not in urls
    assert not any('youtube' in u for u in urls)

def test_css_urls_imports_and_font_tracking():
    found=discover_css('''@import "base.css"; @font-face{src:url(font.woff2)}
    .x { background: url('../img/a.png'); content:"url(fake.jpg)" }
    ''','https://cdn.example/css/site.css')
    assert set(found)=={'https://cdn.example/css/base.css','https://cdn.example/css/font.woff2','https://cdn.example/img/a.png'}
    assert kind_for('https://cdn.example/font.woff2') == 'font'

def test_state_seed_and_reload(tmp_path):
    s=State(tmp_path)
    s.add(HOME,'html','seed','20210529010817')
    s.add(HOME,'html','second','20201109000819')
    s.save()
    loaded=State(tmp_path)
    r=loaded.data['resources'][HOME]
    assert r['hints']==['20210529010817','20201109000819']
    assert r['referrers']==['seed','second']
    assert len(loaded.data['resources'])==1
    assert loaded.data['index_complete'] is False

def test_checkpoint_is_valid_json(tmp_path):
    s=State(tmp_path);s.add(HOME,'html','seed');s.save()
    assert json.loads((tmp_path/'recovery/state.json').read_text())['version']==1
