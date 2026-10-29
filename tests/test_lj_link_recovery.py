import json
from restore.render import Resolver, render_html
from restore.urls import identity


def test_valid_alias_survives_queued_primary():
    url='http://www.bluescholars.com/images/TheLongMarch.jpg'
    alias={'kind':'image','local_path':'/assets/cover.jpg','substitution_note':'Official cover from February 2006; exact 2005 file missing.'}
    resources={url:{'status':'queued','kind':'image'}}
    resolver=Resolver(resources,'/bluescholars',[],aliases={identity(url):alias})
    assert resolver.asset(url,url)=='/bluescholars/assets/cover.jpg'
    rendered,_=render_html(f'<img src="{url}">',url,resources,'/bluescholars',aliases={identity(url):alias})
    assert alias['substitution_note'] in rendered


def test_press_routes_match_builder_grouping(tmp_path):
    from restore.press_archive import recovered_press_resources, _slug, PRESS_ROOT
    directory=tmp_path/'recovery/other-archives/press-articles';directory.mkdir(parents=True)
    source='http://www.example.org/review/'
    capture='http://www.example.org:80/review/'
    (directory/'manifest.json').write_text(json.dumps({'sources':{'review':{'source_url':source}},'page_captures':{'one':{'source_page_url':source,'original_url':capture,'cdx_sha1_verified':True}}}))
    records=recovered_press_resources(tmp_path)
    expected=PRESS_ROOT+'/articles/'+_slug(source)+'/index.html'
    assert records[source]['local_path']==expected
    assert Resolver(records,'/bluescholars',[]).link(capture,source)=='/bluescholars'+expected


def test_press_image_map_links_use_publisher_origin():
    from restore.press_archive import render_press_html
    from bs4 import BeautifulSoup
    source='http://www.tabletmag.com/103/features/article.shtml'
    html,_=render_press_html('<map><area href="/103"><area href="/saved"></map>',source,{'http://www.tabletmag.com/saved':{'kind':'html','local_path':'/other-archives/press/saved/index.html'}},'/bluescholars')
    links=[x['href'] for x in BeautifulSoup(html,'html.parser').select('area')]
    assert links==['http://www.tabletmag.com/103','/bluescholars/other-archives/press/saved/index.html']
