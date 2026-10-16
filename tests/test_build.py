import hashlib
import json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from restore.render import render_html,render_css
from restore.build import build,promote
from restore.check import check
from restore.state import State,write_json
from restore.urls import HOME,TARGET,route

RES={
 HOME+'site.css':{'kind':'css','local_path':'/assets/site.css'},
 'https://cdn.example/photo.jpg':{'kind':'image','local_path':'/assets/photo.jpg'},
 'https://cdn.example/bg.png':{'kind':'image','local_path':'/assets/bg.png'},
}
HTML='''<!doctype html><html><head><title>BLUE SCHOLARS</title><base href="https://evil.example/">
<link rel="stylesheet" href="/site.css"><script>alert(1)</script></head>
<body class="original-layout"><div id="wm-ipp">Wayback toolbar</div><h1>BLUE SCHOLARS</h1>
<a href="/blog?offset=1362122742000">Older</a><a href="javascript:alert(1)">bad</a>
<img data-src="https://cdn.example/photo.jpg" src="/placeholder.gif" onerror="alert(1)">
<img src="https://cdn.example/missing.jpg" alt="Historical photo">
<iframe src="https://www.youtube.com/embed/ABCDEFGHIJK"></iframe>
<form action="/send"><input name="email"><button>Send</button></form>
<div style="background:url(https://cdn.example/bg.png)">Background</div></body></html>'''

def test_selected_archive_homepage_renders_despite_nested_metadata():
    fixture=Path(__file__).parent/'fixtures'/'squarespace-homepage-20210529.html'
    html=fixture.read_text(encoding='utf-8')
    css='https://static1.squarespace.com/static/sitecss/51b8c20be4b0f1f8c9dcdf4c/22/4fb28dfb24ac7489f45b43a8/51b8c20de4b0f1f8c9dce08a/623-05142015/1371067617126/site.css'
    resources={**RES,css:{'kind':'css','local_path':'/assets/site.css'}}
    rendered,issues=render_html(html,HOME,resources,'')
    soup=BeautifulSoup(rendered,'html.parser')
    assert 'BLUE SCHOLARS' in rendered
    assert soup.find('link',rel='stylesheet',href='/assets/site.css')
    assert not soup.find('script',string=lambda value:value and 'COOKIE_BANNER' in value)

def test_renderer_skips_stylesheet_detached_by_malformed_metadata(monkeypatch):
    import restore.render as renderer
    parser=renderer.BeautifulSoup
    def nested_parser(*args,**kwargs):
        soup=parser(*args,**kwargs)
        parent=soup.find('link',rel='stylesheet')
        if parent:
            parent.append(soup.new_tag('link',href='https://cdn.example/nested-prev'))
        return soup
    monkeypatch.setattr(renderer,'BeautifulSoup',nested_parser)
    rendered,_=render_html('<html><head><link rel="stylesheet" href="https://cdn.example/site.css"></head><body>x</body></html>',HOME,RES,'')
    assert 'nested-prev' not in rendered

def test_html_localizes_preserves_layout_and_removes_tracking():
    text,issues=render_html(HTML,HOME,RES,'/bluescholars')
    soup=BeautifulSoup(text,'html.parser')
    assert soup.body['class']==['original-layout']
    assert not soup.find(id='wm-ipp') and not soup.find('base')
    assert not soup.find('iframe') and not soup.find('form')
    assert all(not s.get_text(strip=True) for s in soup.find_all('script'))
    assert soup.find('img')['src']=='/bluescholars/assets/photo.jpg'
    assert not soup.find('img').get('onerror')
    assert soup.find('a',string='Older')['href']=='/bluescholars/blog/page/2/'
    assert not soup.find('a',string='bad').get('href')
    assert soup.find('input').has_attr('disabled')
    assert 'https://www.youtube.com/watch?v=ABCDEFGHIJK' in text
    assert any('missing.jpg' in str(i) for i in issues)
    assert '/bluescholars/assets/bg.png' in text
    assert 'Content-Security-Policy' in text

def test_css_rewrites_dependencies_and_removes_fonts():
    mapping=dict(RES)
    mapping['https://cdn.example/base.css']={'kind':'css','local_path':'/assets/base.css'}
    text,issues=render_css('''@import "base.css" screen; @font-face {font-family:x;src:url(a.woff2)}
    .x {background:url(bg.png);font-family:Georgia;behavior:url(evil.htc)}
    .y{background:url(missing.png)}''','https://cdn.example/style.css',mapping,'/bluescholars')
    assert '@font-face' not in text and 'a.woff2' not in text
    assert '/bluescholars/assets/base.css' in text
    assert '/bluescholars/assets/bg.png' in text
    assert 'behavior' not in text
    assert 'url(missing.png)' not in text and issues

def test_html_srcset_fallback_to_recovered_asset():
    text,_=render_html('<html><body><img srcset="https://cdn.example/photo.jpg 2x"></body></html>',HOME,RES,'')
    assert BeautifulSoup(text,'html.parser').img['src']=='/assets/photo.jpg'

def test_html_asset_reuses_identical_source_path_over_other_scheme():
    resources={'http://cdn.example/photo.jpg':{'kind':'image','local_path':'/assets/photo.jpg'}}
    text,issues=render_html('<html><body><img src="https://cdn.example/photo.jpg"></body></html>',
                            HOME,resources,'')
    assert BeautifulSoup(text,'html.parser').img['src']=='/assets/photo.jpg'
    assert not issues

def test_javascript_encoded_control_characters_removed():
    text,_=render_html('<html><body><a href="java&#10;script:alert(1)">x</a><img src="x" onload="bad()"></body></html>',HOME,{},'')
    assert 'javascript:' not in text and 'onload=' not in text
    assert not BeautifulSoup(text,'html.parser').find('a',string='x').get('href')

def fixture_root(root):
    (root/'source').mkdir(exist_ok=True)
    (root/'public').mkdir(exist_ok=True)
    (root/'recovery/seeds').mkdir(parents=True,exist_ok=True)
    write_json(root/'recovery/seeds/inventory.json',{'pages':[{'original_url':HOME,'capture':TARGET}],'assets':[],'video_embeds':[]})
    write_json(root/'source/catalog.json',{'version':1,'resources':{}})
    write_json(root/'source/review.json',{'publish_approved':False,'visual_reviewed':False})

def add_raw(state,url,kind,body):
    r=state.add(url,kind,'fixture',TARGET)
    sha=hashlib.sha256(body).hexdigest()
    path='recovery/raw/'+sha+('.css' if kind=='css' else '.html')
    (state.root/path).parent.mkdir(parents=True,exist_ok=True)
    (state.root/path).write_bytes(body)
    r.update(status='recovered',sha256=sha,raw_path=path,actual_capture=TARGET,bytes=len(body))
    state.save()

def test_empty_preview_honest_and_links_valid(tmp_path):
    fixture_root(tmp_path)
    report=build(tmp_path,tmp_path/'_site','/bluescholars')
    assert report['recovered_pages']==0
    assert report['placeholder_pages']>=6
    assert check(tmp_path/'_site','/bluescholars')==[]
    assert 'not recovered' in (tmp_path/'_site/2013/index.html').read_text().lower()

def test_release_refuses_empty_site(tmp_path):
    fixture_root(tmp_path)
    with pytest.raises(ValueError,match='review'):build(tmp_path,tmp_path/'_site','',release=True)

def test_raw_response_not_published_until_promoted(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body><p>Recovered historical sentence.</p></body></html>')
    report=build(tmp_path,tmp_path/'_site','')
    assert report['recovered_pages']==0
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert report['recovered_pages']==1
    with pytest.raises(ValueError):promote(tmp_path,reviewed=False)
    promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    assert report['recovered_pages']==1
    assert 'Recovered historical sentence.' in (tmp_path/'_site/2013/index.html').read_text()

def test_candidate_build_uses_exact_dated_image_variant_payload(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    url=HOME+'images/bayaniposter.jpg'
    body=b'\xff\xd8\xff\xe0fixture-image-bytes'
    sha=hashlib.sha256(body).hexdigest()
    path='recovery/raw/'+sha+'.jpg'
    (tmp_path/path).parent.mkdir(parents=True,exist_ok=True)
    (tmp_path/path).write_bytes(body)
    key=url+'@@wayback:20070701135556:'+sha[:12]
    s.data['resources'][key]={'url':url,'kind':'image','status':'recovered','raw_path':path,
        'sha256':sha,'actual_capture':'20070701135556','bytes':len(body),'source_archive':'Internet Archive Wayback'}
    s.save()
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert report['local_source_assets']==1
    assert (tmp_path/'_candidate/assets'/f'{sha}.jpg').read_bytes()==body

def test_candidate_excludes_after_reference_without_approval(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body>Later version</body></html>')
    s.data['resources'][HOME]['status']='needs_review';s.save()
    assert build(tmp_path,tmp_path/'_candidate','',candidate=True)['recovered_pages']==0
    assert promote(tmp_path,reviewed=True)['promoted']==0

def test_candidate_reports_stale_provider_error_as_a_gap(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    provider_error=(b'<html><head><title></title></head><body><p>This page cannot be displayed. '
                    b'Please contact the service provider.</p></body></html>')
    add_raw(s,HOME,'html',provider_error)
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert report['recovered_pages']==0
    assert any(issue['type']=='invalid_source' and issue['url']==HOME for issue in report['issues'])
    assert check(tmp_path/'_candidate','')==[]

def test_later_capture_promotion_requires_resource_specific_review(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    first=HOME+'first';second=HOME+'second'
    add_raw(s,first,'html',b'<html><body>First later capture</body></html>')
    add_raw(s,second,'html',b'<html><body>Second later capture</body></html>')
    for url in (first,second): s.data['resources'][url]['status']='needs_review'
    s.data['resources'][first]['compatibility_review']={
        'actor':'Codex agent','reason':'Matched same-crawl homepage dependency.'
    }
    s.save()
    assert promote(tmp_path,reviewed=True)['promoted']==1
    catalog=json.loads((tmp_path/'source/catalog.json').read_text())['resources']
    assert first in catalog and catalog[first]['compatibility_review']['actor']=='Codex agent'
    assert second in catalog and 'raw_path' not in catalog[second]
    with pytest.raises(ValueError,match='Global later-capture'):
        promote(tmp_path,reviewed=True,allow_later=True)

def test_project_subpath_and_nested_links(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body><a href="/blog/deep/post">Post</a></body></html>')
    add_raw(s,HOME+'blog/deep/post','html',b'<html><body><a href="/">Home</a></body></html>')
    for base in ('','/bluescholars'):
        report=build(tmp_path,tmp_path/'_candidate',base,candidate=True)
        assert report['recovered_pages']==2
        assert check(tmp_path/'_candidate',base)==[]
        assert (tmp_path/'_candidate/2013/blog/deep/post/index.html').is_file()

def test_pre_squarespace_posts_do_not_enter_the_reference_edition(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    old=HOME+'blog/?p=555'
    add_raw(s,old,'html',b'<html><body><p>WordPress era copy.</p></body></html>')
    s.data['resources'][old]['actual_capture']='20100626072734';s.save()
    promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    assert any(p['source']==old and p['path'].startswith('/2009/') for p in report['pages'])
    assert not any(p['path'].startswith('/2013/archive-query/') for p in report['pages'])

def test_legacy_article_navigation_has_a_local_edition_index(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    old=HOME+'blog/2010/01/saved-post'
    add_raw(s,old,'html',b'<html><body><a href="/blog/">Blog</a><p>Recovered post.</p></body></html>')
    s.data['resources'][old]['actual_capture']='20100626072734';s.save();promote(tmp_path,reviewed=True)
    for base in ('','/bluescholars'):
        build(tmp_path,tmp_path/'_site',base)
        index=BeautifulSoup((tmp_path/'_site/2009/blog/index.html').read_text(),'html.parser')
        assert index.find('h1',string='Recovered 2009 WordPress posts')
        assert index.find('a',href=base+'/2009/blog/2010/01/saved-post/')
        assert check(tmp_path/'_site',base)==[]

def test_root_is_a_gateway_to_separate_historical_editions(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><head><title>BLUE SCHOLARS</title></head><body><h1>Original Squarespace homepage</h1></body></html>')
    s.data['resources'][HOME]['actual_capture']='20210529010817';s.save()
    promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    root=BeautifulSoup((tmp_path/'_site/index.html').read_text(),'html.parser')
    assert root.find('h1',string='Blue Scholars archive')
    assert {a.get('href') for a in root.select('a.edition')}=={'/2007/','/2009/','/2013/'}
    assert root.find('a',href='/lj/',string='LiveJournal archive')
    assert 'Original Squarespace homepage' in (tmp_path/'_site/2013/index.html').read_text()
    assert all((tmp_path/'_site'/year/'index.html').is_file() for year in ('2007','2009','2013'))

def test_livejournal_archive_is_a_separate_local_top_level_section(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    post=home+'16954.html'
    add_raw(s,home,'html',b'<html><body><a href="/16954.html">friday mixdown</a></body></html>')
    add_raw(s,post,'html',b'<html><body><h1>friday mixdown</h1><p>Captured post text.</p></body></html>')
    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    root=BeautifulSoup((tmp_path/'_candidate/index.html').read_text(),'html.parser')
    assert root.find('a',href='/bluescholars/lj/',string='LiveJournal archive')
    index=BeautifulSoup((tmp_path/'_candidate/lj/index.html').read_text(),'html.parser')
    assert index.find('a',href='/bluescholars/lj/posts/16954.html')
    rendered=(tmp_path/'_candidate/lj/posts/16954.html').read_text()
    assert 'Captured post text.' in rendered
    assert 'http://bluescholars.livejournal.com/16954.html' not in rendered

def test_livejournal_keeps_post_capture_variants_without_overwriting(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    post=home+'16954.html'
    add_raw(s,post,'html',b'<html><body><p>Older post capture.</p></body></html>')
    older=s.data['resources'].pop(post)
    older['actual_capture']='20090125012333'
    older['source_archive']='Internet Archive Wayback'
    s.data['resources'][post+'@@wayback:20090125012333:'+older['sha256'][:12]]=older
    add_raw(s,post,'html',b'<html><body><p>Newer post capture.</p></body></html>')
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert 'Newer post capture.' in (tmp_path/'_candidate/lj/posts/16954.html').read_text()
    alternate=tmp_path/'_candidate/lj/captures/20090125012333/posts/16954.html'
    assert 'Older post capture.' in alternate.read_text()

def test_livejournal_captured_stylesheet_is_served_locally(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    css=home+'res/19020223/stylesheet?1317269339'
    add_raw(s,home,'html',('<html><head><link rel="stylesheet" href="'+css+'"></head>'
                            '<body><p>Journal entry.</p></body></html>').encode())
    add_raw(s,css,'css',b'.entry { margin-bottom: 2em; }')
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    page=(tmp_path/'_candidate/lj/journal/index.html').read_text()
    local_css=BeautifulSoup(page,'html.parser').find('link',rel='stylesheet')['href']
    assert local_css.startswith('/assets/')
    assert (tmp_path/'_candidate'/local_css.lstrip('/')).is_file()

def test_livejournal_missing_entry_links_stay_inside_archive(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    add_raw(s,home,'html',b'<html><body><a href="http://bluescholars.livejournal.com/16015.html">ATL (part uno)</a></body></html>')
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    page=(tmp_path/'_candidate/lj/journal/index.html').read_text()
    gap=tmp_path/'_candidate/lj/posts/16015.html'
    assert 'href="/lj/posts/16015.html"' in page
    assert 'not been recovered as a standalone page' in gap.read_text()
    assert check(tmp_path/'_candidate','')==[]

def test_unrecovered_edition_links_get_gap_pages_or_honest_cross_edition_bridges(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    old_source=HOME+'blog/2010/09/source-post/'
    add_raw(s,old_source,'html',b'<html><body><a href="/blog/tourdates/">Tour dates</a></body></html>')
    s.data['resources'][old_source]['actual_capture']='20100626072734'
    squarespace_post=HOME+'blog/linked-post/'
    attachment=HOME+'blog/?attachment_id=2764'
    add_raw(s,squarespace_post,'html',b'<html><body><a href="/blog/?attachment_id=2764">Attachment</a></body></html>')
    s.data['resources'][squarespace_post]['actual_capture']='20210529010817'
    add_raw(s,attachment,'html',b'<html><body><p>2010 attachment capture.</p></body></html>')
    s.data['resources'][attachment]['actual_capture']='20101219152112'
    s.save()
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    tourdates=tmp_path/'_candidate/2009/blog/tourdates/index.html'
    attachment_alias=tmp_path/'_candidate/2013/archive-query'/route(attachment).split('/')[-2]/'index.html'
    assert 'not recovered' in tourdates.read_text().lower()
    assert '/2009/archive-query/' in attachment_alias.read_text()
    assert report['placeholder_pages'] >= 1
    assert check(tmp_path/'_candidate','')==[]

def test_selected_edition_link_gets_local_gap_alias_for_unrecovered_target(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    source=HOME+'blog/2010/09/source-post/'
    add_raw(s,source,'html',b'<html><body><a href="/blog/tourdates/">Tour dates</a></body></html>')
    s.data['resources'][source]['actual_capture']='20100626072734'
    s.add(HOME+'blog/tourdates/','html','CDX:domain')
    s.save()
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert (tmp_path/'_candidate/2009/blog/tourdates/index.html').is_file()
    assert check(tmp_path/'_candidate','')==[]

def test_same_homepage_url_keeps_older_and_squarespace_captures_separate(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    current=b'<html><body><h1>Squarespace May 2021</h1></body></html>'
    add_raw(s,HOME,'html',current)
    earlier=b'<html><body><h1>2007 independent design</h1></body></html>'
    sha=hashlib.sha256(earlier).hexdigest();path='recovery/raw/'+sha+'.html'
    (tmp_path/path).write_bytes(earlier)
    s.data['resources'][HOME+'@@commoncrawl:20080907180956:'+sha[:12]]={
        'url':HOME,'kind':'html','status':'recovered','raw_path':path,'sha256':sha,
        'actual_capture':'20080907180956','bytes':len(earlier),'source_archive':'Common Crawl'}
    s.save();promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    assert '2007 independent design' in (tmp_path/'_site/2007/index.html').read_text()
    assert 'Squarespace May 2021' in (tmp_path/'_site/2013/index.html').read_text()
    assert {p['path'] for p in report['pages']}>={'/2007/','/2013/'}

def test_linked_current_article_gets_a_truthful_placeholder(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    listing=HOME+'blog/'
    add_raw(s,listing,'html',b'<html><body><article><a href="/blog/original-observed-slug">Original title</a></article></body></html>')
    promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    assert any(p['path']=='/2013/blog/original-observed-slug/' and p['status']=='not_recovered'
               for p in report['pages'])

def test_discovered_link_merges_existing_cdx_referrers_and_builds_placeholder(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME+'blog/','html',b'<html><body><a href="/blog/2009/01/linked-post/">Linked</a></body></html>')
    target=HOME+'blog/2009/01/linked-post/'
    s.add(target,'html','CDX:domain');s.save();promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    assert any(p['path']=='/2009/blog/2009/01/linked-post/' and p['status']=='not_recovered'
               for p in report['pages'])

def test_checker_detects_broken_local_link_and_remote_image(tmp_path):
    (tmp_path/'index.html').write_text('<html><body><a href="/missing/">Missing</a><img src="https://x.example/a.png"></body></html>')
    errors=check(tmp_path,'')
    assert any('missing' in x for x in errors)
    assert any('remote' in x.lower() for x in errors)

def test_build_refuses_deleting_outside_output(tmp_path):
    fixture_root(tmp_path)
    with pytest.raises(ValueError): build(tmp_path,tmp_path,'')

def test_promote_verifies_raw_hash(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body>old</body></html>')
    record=s.data['resources'][HOME]
    (tmp_path/record['raw_path']).write_bytes(b'<html><body>modified</body></html>')
    with pytest.raises(ValueError,match='hash'):promote(tmp_path,reviewed=True)

def test_diagnostic_source_link_stays_on_wayback(tmp_path):
    fixture_root(tmp_path)
    build(tmp_path,tmp_path/'_site','/bluescholars')
    soup=BeautifulSoup((tmp_path/'_site/index.html').read_text(),'html.parser')
    source=(tmp_path/'_site/2013/index.html').read_text()
    assert BeautifulSoup(source,'html.parser').find('a',string='Inspect the archived source')['href'].startswith('https://web.archive.org/web/')

def test_css_import_media_whitespace_preserved():
    resources={'https://cdn.example/base.css':{'kind':'css','local_path':'/assets/base.css'}}
    text,_=render_css('@import "base.css" screen and (min-width: 600px);','https://cdn.example/site.css',resources,'')
    assert 'screen and' in text
