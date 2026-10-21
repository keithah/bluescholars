import hashlib
import json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from restore.render import render_html,render_css
from restore.discover import discover_html
from restore.build import build,promote,documented_asset_aliases
from restore.check import check
from restore.state import State,write_json
from restore.urls import HOME,TARGET,route,historical_route_prefix,route_capture_hint,livejournal_route

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

def test_renderer_localizes_stylesheets_in_conditional_comments():
    url='https://cdn.example/period.css?part=1'
    resources={**RES,url:{'kind':'css','local_path':'/assets/period-part-1.css'}}
    text='''<html><head><!--[if gte IE 9]><link rel="stylesheet" href="https://cdn.example/period.css?part=1"><![endif]--></head><body>archive</body></html>'''
    rendered,issues=render_html(text,HOME,resources,'/bluescholars')
    soup=BeautifulSoup(rendered,'html.parser')
    assert soup.find('link',rel='stylesheet',href='/bluescholars/assets/period-part-1.css')
    assert 'cdn.example' not in rendered
    assert not issues

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

def test_disabled_form_notice_avoids_colliding_with_historical_site_css():
    rendered,_=render_html('<html><head><style>.archive-notice{position:fixed;top:0;right:0}</style></head><body><form action="/submit"><input name="email"><button>Send</button></form></body></html>',HOME,RES,'')
    soup=BeautifulSoup(rendered,'html.parser')
    notice=soup.select_one('.archive-historical-form .archive-sr-only')
    assert notice and notice.get_text(strip=True)=='Historical form — submissions are disabled.'
    assert soup.select_one('.archive-historical-form[aria-disabled="true"]')
    assert not soup.select('.archive-historical-form .archive-notice')

def test_2007_image_map_labels_get_local_navigation_targets():
    source='''<html><body><map name="Map2">
      <area alt="news" coords="78,158,120,176" shape="rect">
      <area alt="bio" coords="129,159,155,177" shape="rect">
      <area alt="shows" coords="164,160,209,176" shape="rect">
      <area alt="media.htmll" coords="217,160,258,177" shape="rect">
    </map></body></html>'''
    text,_=render_html(source,'http://bluescholars.com/lyrics.html',{},'', '/2007')
    areas=BeautifulSoup(text,'html.parser').find_all('area')
    assert [area['href'] for area in areas]==[
        '/2007/news.html','/2007/bio.html','/2007/shows.html','/2007/media.html']
    assert all(area.get('tabindex')=='0' for area in areas)

def test_2007_late_image_map_coordinates_match_recovered_640px_menu():
    source='''<html><body><img src="images/new_menu.gif" width="800" height="180" usemap="#Map2">
      <map name="Map2"><area alt="news" coords="357,156,401,176" shape="rect">
      <area alt="bio" coords="415,157,445,177" shape="rect">
      <area alt="shows" coords="456,158,516,176" shape="rect">
      <area alt="media.htmll" coords="528,158,580,176" shape="rect"></map></body></html>'''
    text,_=render_html(source,'http://bluescholars.com/news.html',{},'', '/2007')
    areas=BeautifulSoup(text,'html.parser').find_all('area')
    assert [area['coords'] for area in areas]==[
        '98,158,150,176','161,159,194,177','205,160,261,176','271,160,323,177']

def test_image_map_local_pages_are_discovered_and_missing_asset_links_are_honest():
    source='<html><body><map name="nav"><area href="forum.html"><area href="/press/missing.jpg"></map></body></html>'
    discovered=discover_html(source,'http://bluescholars.com/bio.html')
    assert any(r['url']=='http://bluescholars.com/forum.html' and r['kind']=='html' for r in discovered)
    rendered,_=render_html(source,'http://bluescholars.com/bio.html',{},'','/2007')
    areas=BeautifulSoup(rendered,'html.parser').find_all('area')
    assert areas[0]['href']=='/2007/forum.html'
    assert areas[1]['href']=='/archive-status/'

def test_2007_image_map_button_has_an_explicit_local_gap_page(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    url='http://bluescholars.com/bio.html'
    add_raw(s,url,'html',b'<html><body><map name="nav"><area href="forum.html" alt="Forum"></map></body></html>')
    s.data['resources'][url]['actual_capture']='20070724082915';s.save()
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    page=BeautifulSoup((tmp_path/'_candidate/2007/bio.html').read_text(),'html.parser')
    assert page.select_one('area[alt="Forum"]')['href']=='/2007/forum.html'
    assert (tmp_path/'_candidate/2007/forum.html').is_file()
    assert any(item['path']=='/2007/forum.html' and item['status']=='not_recovered' for item in report['pages'])

def test_squarespace_mobile_menu_control_is_keyboard_and_touch_operable():
    source='''<html><body><div id="mobileNav"><nav><a href="/blog">BLOG</a></nav></div>
      <nav id="mobileMenuLink"><ul><li><a>Menu</a></li></ul></nav></body></html>'''
    text,_=render_html(source,HOME,{},'','/2013')
    menu=BeautifulSoup(text,'html.parser').select_one('#mobileMenuLink a')
    assert menu['role']=='button'
    assert menu['tabindex']=='0'
    assert menu['aria-controls']=='mobileNav'
    assert menu['aria-expanded']=='false'

def test_css_rewrites_dependencies_and_keeps_only_recovered_fonts():
    mapping=dict(RES)
    mapping['https://cdn.example/base.css']={'kind':'css','local_path':'/assets/base.css'}
    mapping['https://cdn.example/a.woff2']={'kind':'font','local_path':'/assets/a.woff2'}
    text,issues=render_css('''@import "base.css" screen; @font-face {font-family:x;src:url(a.woff2)}
    .x {background:url(bg.png);font-family:Georgia;behavior:url(evil.htc)}
    .y{background:url(missing.png)}''','https://cdn.example/style.css',mapping,'/bluescholars')
    assert '@font-face' in text and '/bluescholars/assets/a.woff2' in text
    assert '/bluescholars/assets/base.css' in text
    assert '/bluescholars/assets/bg.png' in text
    assert 'behavior' not in text
    assert 'url(missing.png)' not in text and issues

def test_css_renderers_can_reuse_a_precomputed_resource_alias_index(monkeypatch):
    import restore.render as renderer
    aliases=renderer.resource_aliases(RES)
    monkeypatch.setattr(renderer,'identity',lambda _url: (_ for _ in ()).throw(AssertionError('alias index rebuilt')))
    first,_=renderer.render_css('.a{color:red}',HOME+'a.css',RES,'',aliases=aliases)
    second,_=renderer.render_css('.b{color:blue}',HOME+'b.css',RES,'',aliases=aliases)
    assert 'color:red' in first and 'color:blue' in second

def test_html_srcset_fallback_to_recovered_asset():
    text,_=render_html('<html><body><img srcset="https://cdn.example/photo.jpg 2x"></body></html>',HOME,RES,'')
    assert BeautifulSoup(text,'html.parser').img['src']=='/assets/photo.jpg'

def test_missing_social_share_icons_are_compact_without_hiding_article_photo_gaps():
    source='''<html><body><a href="https://twitter.com/share"><img alt="Post to Twitter" src="https://cdn.example/twitter.gif"></a>
    <img alt="Original tour photo" src="https://cdn.example/tour-photo.jpg"></body></html>'''
    text,issues=render_html(source,HOME,{},'')
    soup=BeautifulSoup(text,'html.parser')
    spans=soup.select('span.archive-missing-image')
    assert len(spans)==2
    assert 'archive-missing-control' in spans[0].get('class',[])
    assert spans[0].get_text()=='Image not recovered — Post to Twitter'
    assert 'archive-missing-control' not in spans[1].get('class',[])
    assert spans[1].get_text()=='Image not recovered — Original tour photo'
    assert sum(issue['type']=='missing_asset' for issue in issues)==2

def test_html_asset_reuses_identical_source_path_over_other_scheme():
    resources={'http://cdn.example/photo.jpg':{'kind':'image','local_path':'/assets/photo.jpg'}}
    text,issues=render_html('<html><body><img src="https://cdn.example/photo.jpg"></body></html>',
                            HOME,resources,'')
    assert BeautifulSoup(text,'html.parser').img['src']=='/assets/photo.jpg'
    assert not issues

def test_squarespace_page_routes_old_wordpress_links_to_2009_edition():
    source='http://bluescholars.com/blog/2018/squarespace-post/'
    old='http://bluescholars.com/blog/2011/01/word-count/'
    text,_=render_html('<html><body><a href="'+old+'">Word Count</a></body></html>',
                       source,{},'/bluescholars','/2013')
    link=BeautifulSoup(text,'html.parser').find('a',string='Word Count')
    assert link['href']=='/bluescholars/2009/blog/2011/01/word-count/'

def test_source_documented_older_squarespace_asset_can_fill_exact_later_reference(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    later='https://images.squarespace-cdn.com/content/v1/site/photo.jpg'
    source='http://static1.squarespace.com/static/site/photo.jpg'
    add_raw(s,HOME,'html',('<html><body><img src="'+later+'" alt="Blue Scholars"></body></html>').encode())
    image=b'\xff\xd8\xffhistorical photo'
    add_raw(s,source,'image',image)
    source_record=s.data['resources'][source]
    write_json(tmp_path/'source/asset-aliases.json',{'version':1,'aliases':[{
        'url':later,'source_url':source,'actual_capture':source_record['actual_capture'],
        'sha256':source_record['sha256'],'referrer':HOME+'/holler/',
        'decision':'Same Squarespace asset family and exact source filename; earlier compatible capture.'
    }]})

    report=build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2013/index.html').read_text(),'html.parser')
    image_tag=page.find('img',alt='Blue Scholars')
    assert image_tag and image_tag['src'].startswith('/bluescholars/assets/')
    assert not any(issue.get('url')==later for issue in report['issues'])
    local=tmp_path/'_candidate'/image_tag['src'].removeprefix('/bluescholars/')
    assert local.read_bytes()==image

def test_documented_asset_alias_requires_matching_capture_and_hash(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    later='https://images.squarespace-cdn.com/content/v1/site/photo.jpg'
    source='http://static1.squarespace.com/static/site/photo.jpg'
    add_raw(s,HOME,'html',('<html><body><img src="'+later+'" alt="Blue Scholars"></body></html>').encode())
    add_raw(s,source,'image',b'\xff\xd8\xffhistorical photo')
    source_record=s.data['resources'][source]
    write_json(tmp_path/'source/asset-aliases.json',{'version':1,'aliases':[{
        'url':later,'source_url':source,'actual_capture':source_record['actual_capture'],
        'sha256':'0'*64,'referrer':HOME+'/holler/','decision':'Bad hash must not resolve.'
    }]})

    report=build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2013/index.html').read_text(),'html.parser')
    assert page.find('span',class_='archive-missing-image')
    assert any(issue.get('type')=='missing_asset' and issue.get('url')==later for issue in report['issues'])

def test_documented_alias_matches_older_capture_variant(tmp_path):
    source='http://static1.squarespace.com/static/site/photo.jpg'
    target='https://images.squarespace-cdn.com/content/v1/site/photo.jpg'
    body=b'\xff\xd8\xffolder variant'
    digest=hashlib.sha256(body).hexdigest()
    write_json(tmp_path/'source/asset-aliases.json',{'version':1,'aliases':[{
        'url':target,'source_url':source,'actual_capture':'20160214224810',
        'sha256':digest,'decision':'Exact older image variant.'
    }]})
    variants={
        source+'@@wayback:20210529010000':{'_source_url':source,'kind':'image',
            'actual_capture':'20210529010000','sha256':'f'*64,'local_path':'/new.jpg'},
        source+'@@wayback:20160214224810':{'_source_url':source,'kind':'image',
            'actual_capture':'20160214224810','sha256':digest,'local_path':'/old.jpg',
            'raw_path':'recovery/raw/'+digest+'.jpg'}
    }

    aliases,issues=documented_asset_aliases(tmp_path,variants)

    assert digest in Path(aliases[target]['local_path']).name
    assert not issues

def test_documented_site_stylesheet_alias_localizes_a_missing_variant(tmp_path):
    fixture_root(tmp_path);state=State(tmp_path)
    target='http://static1.squarespace.com/static/sitecss/site/7/template/site.css?&filterFeatures=false'
    source='http://static1.squarespace.com/static/sitecss/site/8/template/site.css?&filterFeatures=false'
    css=b'body{background:#fafafa url(http://static1.squarespace.com/static/bg.png)}.mobileNav{display:none}'
    page_url=HOME+'video'
    add_raw(state,page_url,'html',('<html><head><link rel="stylesheet" href="'+target+'"></head>'
                                   '<body><main>Recovered page</main></body></html>').encode())
    add_raw(state,source,'css',css)
    source_record=state.data['resources'][source]
    source_record['actual_capture']='20230627004401';state.save()
    write_json(tmp_path/'source/asset-aliases.json',{'version':1,'aliases':[{
        'url':target,'source_url':source,'actual_capture':'20230627004401',
        'sha256':source_record['sha256'],'referrer':page_url,
        'decision':'Same immutable Squarespace site/template IDs; identical recovered stylesheet body.'
    }]})

    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2013/video/index.html').read_text(),'html.parser')
    stylesheet=next((link for link in page.find_all('link',rel='stylesheet')
                     if link.get('href','').startswith('/bluescholars/assets/')
                     and 'archive-ui.css' not in link['href']),None)
    assert stylesheet
    local=tmp_path/'_candidate'/stylesheet['href'].split('?',1)[0].removeprefix('/bluescholars/')
    text=local.read_text()
    assert 'background:#fafafa' in text
    assert 'static1.squarespace.com' not in text

def test_early_2013_wordpress_links_use_the_legacy_edition():
    url='http://bluescholars.com/blog/2013/01/early-post/'
    assert historical_route_prefix(url,'/2013','20130101000000')=='/2009'
    assert historical_route_prefix(url,'/2013','20130922000000')=='/2013'

def test_root_level_legacy_permalink_uses_edition_from_capture_date():
    url='http://bluescholars.com/june-17-18-cinemetropolis-release-party-neumos-seattle/'
    assert historical_route_prefix(url,'/2013','20120430110634')=='/2009'
    assert historical_route_prefix(url,'/2009','20070724082915')=='/2007'
    assert historical_route_prefix(url,'/2009','20150930100000')=='/2009'

def test_early_2013_route_uses_latest_capture_hint_when_body_is_missing():
    url='http://bluescholars.com/blog/2013/01/early-post/'
    old={'captures':[{'timestamp':'20130101000000','statuscode':'200'}]}
    later={'captures':[{'timestamp':'20130101000000','statuscode':'200'},
                       {'timestamp':'20160611091915','statuscode':'200'}]}
    assert historical_route_prefix(url,'/2013',route_capture_hint(old))=='/2009'
    assert historical_route_prefix(url,'/2013',route_capture_hint(later))=='/2013'
    undated='http://bluescholars.com/blog/update-cinemetropolis-advance-digital-download/'
    assert historical_route_prefix(undated,'/2013','20110302034042')=='/2009'

def test_invalid_asset_alias_file_reports_clear_error(tmp_path):
    (tmp_path/'source').mkdir()
    (tmp_path/'source/asset-aliases.json').write_text('{')
    with pytest.raises(ValueError,match='Invalid source/asset-aliases.json'):
        documented_asset_aliases(tmp_path,{})

def test_non_object_asset_alias_is_reported_without_aborting(tmp_path):
    (tmp_path/'source').mkdir()
    write_json(tmp_path/'source/asset-aliases.json',{'version':1,'aliases':[None]})
    aliases,issues=documented_asset_aliases(tmp_path,{})
    assert not aliases and issues[0]['type']=='compatibility_alias_unavailable'

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
    suffix={'css':'.css','font':'.woff','image':'.jpg'}.get(kind,'.html')
    path='recovery/raw/'+sha+suffix
    (state.root/path).parent.mkdir(parents=True,exist_ok=True)
    (state.root/path).write_bytes(body)
    r.update(status='recovered',sha256=sha,raw_path=path,actual_capture=TARGET,bytes=len(body))
    state.save()

def test_candidate_keeps_font_provenance_without_redistributing_font_binary(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    css='https://static.example/site.css'
    font='https://static.example/universal/fonts/ui.woff'
    add_raw(s,HOME,'html',('<html><head><link rel="stylesheet" href="'+css+'"></head><body>Home</body></html>').encode())
    add_raw(s,css,'css',b"@font-face{font-family:ui;src:url('/universal/fonts/ui.woff') format('woff')}body{font-family:ui}")
    add_raw(s,font,'font',b'wOFF\x00\x01fixture')
    report=build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    assert report['local_source_assets']==1
    assert any(issue['type']=='font_not_packaged' for issue in report['issues'])
    output=(tmp_path/'_candidate/assets'/ (hashlib.sha256(b'wOFF\x00\x01fixture').hexdigest()+'.woff'))
    assert not output.exists()
    css_path=tmp_path/'_candidate/assets'/ (hashlib.sha256(css.encode()).hexdigest()[:24]+'.css')
    rendered=css_path.read_text()
    assert '@font-face' not in rendered and '.woff' not in rendered
    assert 'font-family:ui' in rendered

def test_legacy_wordpress_origin_page_uses_the_2009_site_route(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    alias='http://02cd02a.netsolhost.com:80/blog/2009/03/sxsw-2009-where-well-be/'
    add_raw(s,alias,'html',b'<html><body><h1>SXSW 2009</h1><p>Recovered entry.</p></body></html>')

    report=build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    assert report['recovered_pages']==1
    page=tmp_path/'_candidate/2009/blog/2009/03/sxsw-2009-where-well-be/index.html'
    assert page.is_file()
    assert 'Recovered entry.' in page.read_text()

def test_2007_news_page_lists_recovered_livejournal_entries(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,'http://bluescholars.com/news.html','html',
            b'<html><head><title>Blue Scholars - [news]</title></head><body><p>View my LiveJournal</p></body></html>')
    s.data['resources']['http://bluescholars.com/news.html']['actual_capture']='20070701134800';s.save()
    add_raw(s,'http://bluescholars.livejournal.com/16954.html','html',
            b'<html><body><div style="margin-left: 30px"><font><b>friday mixdown</b></font><br>Mixing the Joe Metro EP at Jupiter Studios.</div></body></html>')
    add_raw(s,'http://bluescholars.livejournal.com/17222.html','html',
            b'<html><body><div style="margin-left: 30px"><font><b>The Program</b></font><br>Five nights of Seattle hip hop shows in December 2007.</div></body></html>')
    add_raw(s,'http://bluescholars.livejournal.com/','html',
            b'<html><body><div class="entry"><h3 class="entrysubject"><a class="subj-link" href="http://bluescholars.livejournal.com/16015.html">ATL (part uno)</a></h3><span class="entrytimestampdate">9/21/07</span><div class="entrycontent">Atlanta and the Atlantis Music Conference.</div></div><div class="entry"><h3 class="entrysubject"><a class="subj-link" href="http://bluescholars.livejournal.com/16954.html">friday mixdown</a></h3><span class="entrytimestampdate">9/30/07</span><div class="entrycontent">Mixing the Joe Metro EP at Jupiter Studios.</div></div><div class="entry"><h3 class="entrysubject"><a class="subj-link" href="http://bluescholars.livejournal.com/17222.html">The Program</a></h3><span class="entrytimestampdate">10/4/07</span><div class="entrycontent">Five nights of Seattle hip hop shows in December 2007.</div></div></body></html>')

    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2007/news.html').read_text(),'html.parser')
    news=page.select_one('.recovered-news')
    assert news is not None
    assert 'separately archived LiveJournal' in news.get_text(' ',strip=True)
    assert page.select_one('a[href="/bluescholars/lj/posts/16954.html"]')
    assert page.select_one('a[href="/bluescholars/lj/posts/17222.html"]')
    assert page.select_one('a[href="/bluescholars/lj/posts/16015.html"]')
    assert 'Jupiter Studios' in news.get_text(' ',strip=True)
    assert 'Atlantis Music Conference' in news.get_text(' ',strip=True)
    assert [a.get_text(strip=True) for a in news.select('.recovered-news-entry h3 a')]==[
        'ATL (part uno)','friday mixdown','The Program']


def test_legacy_alias_host_pages_with_explicit_html_kind_are_selected(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    host='http://02cd02a.netsolhost.com'
    routes=(
        ('/blog/2009/03/sxsw-2009-where-well-be/','SXSW recovery'),
        ('/blog/2011/01/the-hip-hop-word-count-blue-scholars-approved/','Word Count recovery'),
    )
    for path,title in routes:
        add_raw(s,host+path,'html',f'<html><body><h1>{title}</h1></body></html>'.encode())

    report=build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    assert report['recovered_pages']==2
    assert 'SXSW recovery' in (tmp_path/'_candidate/2009/blog/2009/03/sxsw-2009-where-well-be/index.html').read_text()
    assert 'Word Count recovery' in (tmp_path/'_candidate/2009/blog/2011/01/the-hip-hop-word-count-blue-scholars-approved/index.html').read_text()

def test_late_capture_from_legacy_wordpress_host_stays_in_2009_edition(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    url='http://02cd02a.netsolhost.com/blog/releases/oof-ep/'
    add_raw(s,url,'html',b'<html><body><h1>OOF EP</h1></body></html>')
    s.data['resources'][url]['actual_capture']='20160304042651';s.save()

    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    assert (tmp_path/'_candidate/2009/blog/releases/oof-ep/index.html').is_file()
    assert not (tmp_path/'_candidate/2013/blog/releases/oof-ep/index.html').exists()

def test_squarespace_edition_starts_at_the_first_located_2013_capture(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    url='http://bluescholars.com/blog/page/3/'
    add_raw(s,url,'html',b'<html><body><h1>2013 listing</h1></body></html>')
    s.data['resources'][url]['actual_capture']='20130921000000';s.save()

    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    assert (tmp_path/'_candidate/2013/blog/page/3/index.html').is_file()
    assert not (tmp_path/'_candidate/2009/blog/page/3/index.html').exists()


def test_legacy_post_images_and_theme_css_are_local_in_candidate(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    post='http://02cd02a.netsolhost.com/blog/2011/01/word-count/'
    css='http://02cd02a.netsolhost.com/blog/wp-content/themes/modernpaper-10/style.css'
    image='http://www.bluescholars.com/blog/wp-content/themes/modernpaper-10/images/header.gif'
    add_raw(s,post,'html',('<html><head><link rel="stylesheet" href="'+css+'"></head>'
        '<body><img src="'+image+'" alt="WordPress header"></body></html>').encode())
    add_raw(s,css,'css',b'body{background:#fff}')
    add_raw(s,image,'image',b'GIF89a' + b'fixture')

    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2009/blog/2011/01/word-count/index.html').read_text(),'html.parser')
    assert page.find('link',rel='stylesheet',href=lambda h:h and h.startswith('/bluescholars/assets/'))
    assert page.find('img',src=lambda h:h and h.startswith('/bluescholars/assets/'))
    local_image=page.find('img')['src'].removeprefix('/bluescholars/')
    assert (tmp_path/'_candidate'/local_image).read_bytes().startswith(b'GIF89a')


def test_2007_edition_uses_clean_2007_homepage_not_later_damaged_capture(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><body><h1>July 2007 home</h1></body></html>')
    clean=s.data['resources'][HOME]
    clean['actual_capture']='20070724082915'
    dated=dict(clean,url=HOME,actual_capture='20080817084306',
        raw_path='recovery/raw/damaged.html',sha256=hashlib.sha256(b'<html><body><h1>Injected SEO links</h1></body></html>').hexdigest())
    dated['edition_exclusion']={'exclude_from_site':True,'reason':'Compromised by injected SEO-link content.'}
    damaged=b'<html><body><h1>Injected SEO links</h1></body></html>'
    (tmp_path/'recovery/raw/damaged.html').write_bytes(damaged)
    s.data['resources'][HOME+'@@wayback:20080817084306:'+dated['sha256'][:12]]=dated
    s.save()

    build(tmp_path,tmp_path/'_candidate','',candidate=True)

    page=(tmp_path/'_candidate/2007/index.html').read_text()
    assert 'July 2007 home' in page
    assert 'Injected SEO links' not in page


def test_source_promotion_does_not_copy_font_binaries(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    font='https://static.example/universal/fonts/ui.woff'
    add_raw(s,HOME,'html',b'<html><body>Home</body></html>')
    add_raw(s,font,'font',b'wOFF\x00\x01fixture')
    result=promote(tmp_path,reviewed=True)
    assert result['promoted']==1
    assert not list((tmp_path/'source/raw').glob('*.woff'))
    assert json.loads((tmp_path/'source/catalog.json').read_text())['resources'][font].get('raw_path') is None


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


def test_candidate_includes_only_resource_compatibility_reviewed_later_assets(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    image='https://images.example/hero.jpg'
    add_raw(s,HOME,'html',f'<html><body><img src="{image}" alt="Reference hero"></body></html>'.encode())
    add_raw(s,image,'image',b'\xff\xd8\xff\xe0reviewed-later-image')
    later=s.data['resources'][image]
    later.update(status='needs_review',actual_capture='20210529010844',
        compatibility_review={'actor':'Codex agent','reason':'Same-crawl image dependency.'})
    unapproved='https://images.example/unreviewed.jpg'
    add_raw(s,unapproved,'image',b'\xff\xd8\xff\xe0unreviewed-image')
    s.data['resources'][unapproved].update(status='needs_review',actual_capture='20210530000000')
    s.save()

    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)

    page=BeautifulSoup((tmp_path/'_candidate/2013/index.html').read_text(),'html.parser')
    assert page.find('img',src=lambda value:value and value.startswith('/assets/'))
    assert report['local_source_assets']==1
    assert not any(path.name.endswith('unreviewed-image.jpg') for path in (tmp_path/'_candidate/assets').iterdir())

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
    write_json(tmp_path/'source/massline.json',{'resources':{}})
    add_raw(s,HOME,'html',b'<html><head><title>BLUE SCHOLARS</title></head><body><h1>Original Squarespace homepage</h1></body></html>')
    s.data['resources'][HOME]['actual_capture']='20210529010817';s.save()
    promote(tmp_path,reviewed=True)
    report=build(tmp_path,tmp_path/'_site','')
    root=BeautifulSoup((tmp_path/'_site/index.html').read_text(),'html.parser')
    assert root.find('h1',string='Blue Scholars archive')
    assert {a.get('href') for a in root.select('a.edition')}=={'/2007/','/2009/','/2013/'}
    cards=root.select('a.edition-card')
    assert [card.select_one('.edition-year').get_text(strip=True) for card in cards]==['2007','2009','2013']
    assert [card.select_one('.edition-era').get_text(strip=True) for card in cards]==[
        'Independent site','WordPress site','Squarespace site · first located in 2013']
    assert all(card.select_one('.edition-action') for card in cards)
    assert root.select_one('a.lj-archive[href="/lj/"]')
    assert {a.get('href') for a in root.select('.archive-site-card')} == {
        '/prometheusbrown/', '/sabzi/', '/myspace/', '/twitter-prometheusbrown/', '/masslinemedia/', '/massline-forums/', '/lj/'
    }
    assert all(card.select_one('.edition-action') for card in root.select('.archive-site-card'))
    twitter=(tmp_path/'_site/twitter-prometheusbrown/index.html').read_text()
    assert 'No archived profile captures' in twitter
    assert root.select_one('a.recovery-status')
    assert 'Original Squarespace homepage' in (tmp_path/'_site/2013/index.html').read_text()
    assert all((tmp_path/'_site'/year/'index.html').is_file() for year in ('2007','2009','2013'))

def test_root_edition_cards_use_project_prefix_and_have_compact_responsive_styles(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    (tmp_path/'public/archive-ui.css').write_text((Path(__file__).resolve().parents[1]/'public/archive-ui.css').read_text())
    add_raw(s,HOME,'html',b'<html><head><title>BLUE SCHOLARS</title></head><body><h1>Original Squarespace homepage</h1></body></html>')
    s.data['resources'][HOME]['actual_capture']='20210529010817';s.save()
    promote(tmp_path,reviewed=True)
    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    root=BeautifulSoup((tmp_path/'_candidate/index.html').read_text(),'html.parser')
    assert {card['href'] for card in root.select('a.edition-card')}=={
        '/bluescholars/2007/','/bluescholars/2009/','/bluescholars/2013/'}
    styles=(tmp_path/'_candidate/assets/archive-ui.css').read_text()
    assert '.edition-grid' in styles and '@media' in styles

def test_archive_ui_stylesheet_url_is_content_versioned(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    css=(Path(__file__).resolve().parents[1]/'public/archive-ui.css').read_text()
    (tmp_path/'public/archive-ui.css').write_text(css)
    add_raw(s,HOME,'html',b'<html><head><title>BLUE SCHOLARS</title></head><body><h1>Original homepage</h1></body></html>')
    s.data['resources'][HOME]['actual_capture']='20210529010817';s.save()
    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    expected='/bluescholars/assets/archive-ui.css?v='+hashlib.sha256(css.encode()).hexdigest()[:16]
    for path in ('index.html','2013/index.html'):
        page=BeautifulSoup((tmp_path/'_candidate'/path).read_text(),'html.parser')
        assert page.find('link',rel='stylesheet',href=expected)

def test_livejournal_archive_is_a_separate_local_top_level_section(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    post=home+'16954.html'
    add_raw(s,home,'html',b'<html><head><title>Latest captured LiveJournal</title></head><body><h1>Latest journal snapshot</h1><a href="/16954.html">friday mixdown</a></body></html>')
    add_raw(s,post,'html',b'<html><head><title>bluescholars: friday mixdown</title></head><body><h1></h1><p>Captured post text.</p></body></html>')
    current=s.data['resources'].pop(post)
    older=dict(current);older['actual_capture']='20090125012333'
    older['raw_path']=current['raw_path'];older['sha256']=current['sha256']
    s.data['resources'][post+'@@wayback:20090125012333:'+older['sha256'][:12]]=older
    calendar=home+'calendar'
    add_raw(s,calendar,'html',b'<html><head><title>Journal Calendar</title></head><body>Archive</body></html>')
    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    root=BeautifulSoup((tmp_path/'_candidate/index.html').read_text(),'html.parser')
    assert root.select_one('a.lj-archive[href="/bluescholars/lj/"]')
    index=BeautifulSoup((tmp_path/'_candidate/lj/archive/index.html').read_text(),'html.parser')
    default=BeautifulSoup((tmp_path/'_candidate/lj/index.html').read_text(),'html.parser')
    assert default.find('h1',string='Latest journal snapshot')
    assert default.select_one('a[href="/bluescholars/lj/archive/"]')
    assert index.select_one('.recovered-journal-entries a[href="/bluescholars/lj/posts/16954.html"]').get_text(strip=True)=='friday mixdown'
    assert 'Earlier journal capture' not in index.get_text(' ',strip=True)
    assert index.select_one('.recovered-journal-entries a[href="/bluescholars/lj/posts/calendar"]') is None
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

def test_livejournal_http_and_https_copies_share_routes_but_keep_capture_variants(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    post='http://bluescholars.livejournal.com/16954.html'
    add_raw(s,post,'html',b'<html><body><p>2011 archived post.</p></body></html>')
    older=s.data['resources'].pop(post)
    older['actual_capture']='20111002073201'
    older['source_archive']='Internet Archive Wayback'
    s.data['resources'][post+'@@wayback:20111002073201:'+older['sha256'][:12]]=older
    secure='https://bluescholars.livejournal.com/16954.html'
    add_raw(s,secure,'html',b'<html><body><p>2018 Common Crawl post.</p></body></html>')
    newer=s.data['resources'].pop(secure)
    newer.update(actual_capture='20181210163833',source_archive='Common Crawl',
                 source_collection='CC-MAIN-2018-51',source_warc='crawl-data/example.warc.gz',
                 source_offset=123,source_length=456,source_digest='archive-digest')
    s.data['resources'][secure+'@@commoncrawl:20181210163833:'+newer['sha256'][:12]]=newer
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    assert '2018 Common Crawl post.' in (tmp_path/'_candidate/lj/posts/16954.html').read_text()
    alternate=tmp_path/'_candidate/lj/captures/20111002073201/posts/16954.html'
    assert '2011 archived post.' in alternate.read_text()
    assert '2018 Common Crawl post.' not in alternate.read_text()

def test_2007_news_includes_an_individually_recovered_livejournal_entry(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,'http://bluescholars.com/news.html','html',b'<html><head><title>Blue Scholars - [news]</title></head><body><p>View my LiveJournal</p></body></html>')
    s.data['resources']['http://bluescholars.com/news.html']['actual_capture']='20070701134800'
    root='http://bluescholars.livejournal.com/'
    add_raw(s,root,'html',b'<html><body><div class="entry"><h3 class="entrysubject"><a class="subj-link" href="/16015.html">ATL (part uno)</a></h3><span class="entrytimestampdate">9/21/07</span><div class="entrycontent">Atlanta entry excerpt.</div></div></body></html>')
    s.data['resources'][root].update(actual_capture='20180219080958',source_archive='Common Crawl')
    post='https://bluescholars.livejournal.com/16641.html'
    add_raw(s,post,'html',b'<html><body><div class="entry"><h3 class="entrysubject"><a class="subj-link" href="/16641.html">hip hop &amp; violence</a></h3><span class="entrytimestampdate">8/15/07</span><div class="entrycontent">An archived essay about hip hop and violence.</div></div></body></html>')
    s.data['resources'][post].update(actual_capture='20171119082055',source_archive='Common Crawl')
    s.save()
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    news=BeautifulSoup((tmp_path/'_candidate/2007/news.html').read_text(),'html.parser')
    link=news.select_one('.recovered-news a[href="/lj/posts/16641.html"]')
    assert link and link.get_text(strip=True)=='hip hop & violence'
    assert '8/15/07' in news.get_text(' ',strip=True)
    assert 'surviving capture: Nov 19, 2017' in news.get_text(' ',strip=True)

def test_livejournal_comment_thread_captures_get_distinct_local_routes():
    post='http://bluescholars.livejournal.com/16015.html'
    assert livejournal_route(post+'?thread=49039')=='/lj/comments/16015.html/49039/'
    assert livejournal_route(post+'?thread=50319')=='/lj/comments/16015.html/50319/'
    assert livejournal_route(post)=='/lj/posts/16015.html'

def test_livejournal_comment_thread_captures_render_at_distinct_routes(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    for thread,text in (('49039','First preserved reply.'),('50319','Second preserved reply.')):
        url=f'http://bluescholars.livejournal.com/16015.html?thread={thread}'
        add_raw(s,url,'html',f'<html><body><h1>Comment thread {thread}</h1><p>{text}</p></body></html>'.encode())
        s.data['resources'][url].update(actual_capture='20180219081048',source_archive='Common Crawl')
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    first=(tmp_path/'_candidate/lj/comments/16015.html/49039/index.html').read_text()
    second=(tmp_path/'_candidate/lj/comments/16015.html/50319/index.html').read_text()
    assert 'First preserved reply.' in first and 'Second preserved reply.' not in first
    assert 'Second preserved reply.' in second and 'First preserved reply.' not in second
    index=BeautifulSoup((tmp_path/'_candidate/lj/archive/index.html').read_text(),'html.parser')
    assert len(index.select('.recovered-comment-threads a'))==2
    assert not index.select('.recovered-journal-entries a[href*="/comments/"]')

def test_unrecovered_livejournal_comment_links_get_local_gap_pages(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    post='http://bluescholars.livejournal.com/16954.html'
    add_raw(s,post,'html',b'<html><body><h1>friday mixdown</h1><a href="?thread=999999#t999999">Read comment</a></body></html>')
    build(tmp_path,tmp_path/'_candidate','/bluescholars',candidate=True)
    gap=tmp_path/'_candidate/lj/comments/16954.html/999999/index.html'
    page=BeautifulSoup(gap.read_text(),'html.parser')
    assert 'comment thread was not recovered' in page.get_text(' ',strip=True).lower()
    assert page.select_one('a[href="/bluescholars/lj/posts/16954.html"]')
    assert check(tmp_path/'_candidate','/bluescholars')==[]

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

def test_livejournal_entry_content_is_reused_from_the_captured_front_page(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    home='http://bluescholars.livejournal.com/'
    post=home+'16015.html'
    html=('<html><body><div class="entry"><div class="entryheader"><h3><a href="'+post+'">ATL (part uno)</a></h3></div>'
          '<div class="entrytext">This exact text survives in the captured front page.</div></div></body></html>')
    add_raw(s,home,'html',html.encode())
    report=build(tmp_path,tmp_path/'_candidate','',candidate=True)
    page=(tmp_path/'_candidate/lj/posts/16015.html').read_text()
    assert 'This exact text survives in the captured front page.' in page
    assert 'derived_from_capture' in {r['status'] for r in report['pages']}
    assert report['derived_pages']==1
    index=BeautifulSoup((tmp_path/'_candidate/lj/archive/index.html').read_text(),'html.parser')
    assert index.select_one('a[href="/lj/posts/16015.html"]')
    assert 'Recovered journal entries' in index.get_text(' ',strip=True)

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
    source_page=BeautifulSoup((tmp_path/'_candidate/2013/blog/linked-post/index.html').read_text(),'html.parser')
    recovered_attachment=tmp_path/'_candidate/2009/archive-query'/route(attachment).split('/')[-2]/'index.html'
    assert 'not recovered' in tourdates.read_text().lower()
    assert source_page.find('a',string='Attachment')['href'].startswith('/2009/archive-query/')
    assert '2010 attachment capture' in recovered_attachment.read_text()
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

def test_unreviewed_post_takeover_redirect_does_not_rewrite_historical_menu_links(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    source=HOME+'blog/media/'
    target=HOME+'blog/cinemetropolis/'
    add_raw(s,source,'html',b'<html><body><a href="http://bluescholars.com/blog/cinemetropolis/">CINEMETROPOLIS</a></body></html>')
    s.data['resources'][source]['actual_capture']='20110807103740'
    record=s.add(target,'html','CDX:domain')
    record.update(status='needs_review',actual_capture='20250627045146',
                  final_original='https://www.incontro.restaurant/menu/')
    s.save()
    build(tmp_path,tmp_path/'_candidate','',candidate=True)
    source_page=(tmp_path/'_candidate/2009/blog/media/index.html').read_text()
    assert 'href="/2009/blog/cinemetropolis/"' in source_page
    assert 'href="/2009/menu/"' not in source_page
    gap=tmp_path/'_candidate/2009/blog/cinemetropolis/index.html'
    assert gap.is_file() and 'not recovered' in gap.read_text().lower()
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

def test_checker_accepts_project_prefixed_root_absolute_links(tmp_path):
    (tmp_path/'2007').mkdir()
    (tmp_path/'2007/index.html').write_text('<html></html>')
    (tmp_path/'assets').mkdir()
    (tmp_path/'assets/site.css').write_text('body{}')
    (tmp_path/'index.html').write_text('<html><head><link rel="stylesheet" href="/bluescholars/assets/site.css"></head><body><a href="/bluescholars/2007/">2007</a></body></html>')
    assert check(tmp_path,'/bluescholars')==[]

def test_checker_treats_image_map_areas_as_user_navigation(tmp_path):
    (tmp_path/'news.html').write_text('<html></html>')
    (tmp_path/'index.html').write_text('''<html><body><map name="nav">
      <area href="/news.html" alt="News" shape="rect" coords="0,0,20,10">
      <area href="https://example.org/" alt="External" shape="rect" coords="20,0,40,10">
    </map></body></html>''')
    assert check(tmp_path,'')==[]

def test_generated_stylesheet_reveals_the_recovered_mobile_menu(tmp_path):
    fixture_root(tmp_path)
    build(tmp_path,tmp_path/'_site','/bluescholars')
    css=(tmp_path/'_site/assets/archive-ui.css').read_text()
    assert '.archive-menu-open #mobileNav' in css
    assert 'height:auto!important' in css

def test_generated_pages_cache_bust_the_local_behavior_script(tmp_path):
    fixture_root(tmp_path)
    build(tmp_path,tmp_path/'_site','/bluescholars')
    page=BeautifulSoup((tmp_path/'_site/2013/index.html').read_text(),'html.parser')
    script=page.find('script',src=True)
    assert script and script['src'].startswith('/bluescholars/assets/legacy.js?v=')


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

def test_promotion_rejects_provider_error_payloads_but_keeps_other_sources(tmp_path):
    fixture_root(tmp_path);s=State(tmp_path)
    add_raw(s,HOME,'html',b'<html><head><title>Blue Scholars</title></head><body>Home</body></html>')
    invalid='http://bluescholars.com/shop'
    add_raw(s,invalid,'html',b'<html><head><title>Page Not Found</title></head><body>Page cannot be displayed by service provider</body></html>')

    result=promote(tmp_path,reviewed=True)

    assert result['promoted']==1
    assert result['rejected_provider_errors']==1
    state=State(tmp_path)
    assert state.data['resources'][invalid]['status']=='failed'
    assert 'provider/archive error' in state.data['resources'][invalid]['reason'].lower()
    catalog=json.loads((tmp_path/'source/catalog.json').read_text())['resources']
    assert catalog[invalid]['status']=='failed'
    assert not catalog[invalid].get('raw_path')

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

def test_promote_redacts_archived_google_maps_key_and_keeps_original_provenance(tmp_path):
    fixture_root(tmp_path)
    state=State(tmp_path)
    key=b'AIza'+b'A'*35
    body=b'<html><body><script>window.site={"googleMapsStaticApiKey":"'+key+b'"}</script><p>Archive page</p></body></html>'
    add_raw(state,HOME,'html',body)
    original=state.data['resources'][HOME]
    (tmp_path/'source/review.json').write_text(json.dumps({
        'redistribution_permission_confirmed':True,
        'publish_approved':False,
        'visual_reviewed':False,
    }))

    result=promote(tmp_path,reviewed=True)

    catalog=json.loads((tmp_path/'source/catalog.json').read_text())['resources']
    saved=catalog[HOME]
    public_source=(tmp_path/saved['raw_path']).read_bytes()
    assert result['redacted_payloads']==1
    assert key not in public_source
    assert b'Archive page' in public_source
    assert saved['raw_path'].startswith('source/redacted/')
    assert saved['sha256']==hashlib.sha256(public_source).hexdigest()
    assert saved['original_sha256']==original['sha256']
    assert saved['source_redaction']['field']=='googleMapsStaticApiKey'
    assert (tmp_path/original['raw_path']).read_bytes()==body
    review=json.loads((tmp_path/'source/review.json').read_text())
    assert review['redistribution_permission_confirmed'] is True
    assert review['publish_approved'] is False

def test_promote_redacts_stripe_publishable_key_from_archived_source(tmp_path):
    fixture_root(tmp_path)
    state=State(tmp_path)
    key=b'pk_live_'+b'A'*24
    body=b'<html><script>payment={"publishableApiKey":"'+key+b'"}</script><p>Archive page</p></html>'
    add_raw(state,HOME,'html',body)

    result=promote(tmp_path,reviewed=True)

    saved=json.loads((tmp_path/'source/catalog.json').read_text())['resources'][HOME]
    public_source=(tmp_path/saved['raw_path']).read_bytes()
    assert result['redacted_payloads']==1
    assert key not in public_source
    assert b'[redacted-publishable-key]' in public_source
    assert saved['source_redaction']['count']==1
    assert saved['source_redaction']['field']=='Stripe publishable API key'
    assert (tmp_path/state.data['resources'][HOME]['raw_path']).read_bytes()==body
