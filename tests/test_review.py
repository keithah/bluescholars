"""Regression cases found in the separate final self-review."""
import json
import subprocess
from bs4 import BeautifulSoup
from restore.urls import original_url,HOME,TARGET
from restore.discover import discover_html
from restore.render import render_html
from restore.svg import sanitize_svg
from restore.build import build
from restore.state import State,write_json
from restore.archive import Payload
from restore.recover import recover


def test_malformed_source_url_does_not_abort_discovery():
    assert original_url('https://[broken',HOME)==''
    assert discover_html('<img src="https://[broken"><a href="/blog">Blog</a>',HOME)[0]['url']==HOME+'blog'

def test_linked_image_not_mistaken_for_html_page():
    refs=discover_html('<a href="/poster.jpg">Download poster</a>',HOME)
    assert refs[0]['kind']=='image'

def test_squarespace_lazy_embed_becomes_outbound_video_link():
    text='''<html><body><div data-html="&lt;iframe src='https://www.youtube.com/embed/ABCDEFGHIJK'&gt;&lt;/iframe&gt;"></div></body></html>'''
    output,_=render_html(text,HOME,{},'')
    assert 'https://www.youtube.com/watch?v=ABCDEFGHIJK' in output
    assert not BeautifulSoup(output,'html.parser').find('iframe')

def test_svg_external_and_active_content_removed():
    value=b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><image href="https://evil.example/x.png"/><path onload="bad()" d="M0,0 L2,2"/></svg>'
    clean=sanitize_svg(value).decode()
    assert '<script' not in clean and 'onload' not in clean and 'evil.example' not in clean
    assert 'path' in clean

def test_svg11_standard_external_doctype_is_removed_before_sanitizing():
    value=b'''<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0h4v4z"/></svg>'''
    clean=sanitize_svg(value).decode()
    assert '<!DOCTYPE' not in clean
    assert '<path' in clean

def test_homepage_styles_before_blog_backlog(tmp_path):
    s=State(tmp_path);s.add(HOME,'html','seed',TARGET)
    seen=[]
    class Client:
        def get(self,url):
            seen.append(url)
            if url.endswith('site.css'):
                body=b'body{max-width:900px}'
            else:
                body=b'<html><head><link rel="stylesheet" href="/site.css"></head><body><a href="/blog">Blog</a></body></html>'
            return Payload(body,url,200,{})
    recover(s,Client(),max_files=2)
    assert seen[1].endswith('/site.css')

def test_legacy_offset_redirect_does_not_discard_filters(tmp_path):
    (tmp_path/'recovery/seeds').mkdir(parents=True)
    write_json(tmp_path/'recovery/seeds/inventory.json',{'pages':[{'original_url':HOME+'blog?offset=1362122742000'}]})
    build(tmp_path,tmp_path/'_site','/bluescholars')
    script=(tmp_path/'_site/assets/legacy.js').read_text()
    node_script='''const vm=require('vm'); const results=[];
    for (const search of ['?offset=1362122742000','?offset=1362122742000&tag=live']) {
      let redirected=null;
      const location={pathname:'/bluescholars/2013/blog',search,hash:'',replace:value=>{redirected=value}};
      vm.runInNewContext(SCRIPT,{location,URLSearchParams});results.push(redirected);
    } console.log(JSON.stringify(results));'''.replace('SCRIPT',json.dumps(script))
    r=subprocess.run(['node','-e',node_script],text=True,capture_output=True,check=True)
    assert json.loads(r.stdout)==['/bluescholars/2013/blog/page/2/',None]
