import hashlib
import json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from restore.render import render_html,render_css
from restore.build import build,promote
from restore.check import check
from restore.state import State,write_json
from restore.urls import HOME,TARGET

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
    assert 'not recovered' in (tmp_path/'_site/index.html').read_text().lower()

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
    assert 'Recovered historical sentence.' in (tmp_path/'_site/index.html').read_text()

def test_candidate_excludes_after_reference_without_approval(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body>Later version</body></html>')
    s.data['resources'][HOME]['status']='needs_review';s.save()
    assert build(tmp_path,tmp_path/'_candidate','',candidate=True)['recovered_pages']==0
    assert promote(tmp_path,reviewed=True)['promoted']==0

def test_project_subpath_and_nested_links(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body><a href="/blog/deep/post">Post</a></body></html>')
    add_raw(s,HOME+'blog/deep/post','html',b'<html><body><a href="/">Home</a></body></html>')
    for base in ('','/bluescholars'):
        report=build(tmp_path,tmp_path/'_candidate',base,candidate=True)
        assert report['recovered_pages']==2
        assert check(tmp_path/'_candidate',base)==[]
        assert (tmp_path/'_candidate/blog/deep/post/index.html').is_file()

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
    assert soup.find('a',string='Inspect the archived source')['href'].startswith('https://web.archive.org/web/')

def test_css_import_media_whitespace_preserved():
    resources={'https://cdn.example/base.css':{'kind':'css','local_path':'/assets/base.css'}}
    text,_=render_css('@import "base.css" screen and (min-width: 600px);','https://cdn.example/site.css',resources,'')
    assert 'screen and' in text
