"""Discover dependencies without executing archived JavaScript or crawling external sites."""
from __future__ import annotations
import json
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
import tinycss2
from .urls import original_url,is_site,kind_for

def css_values(tokens):
    for token in tokens:
        if token.type=='url':
            yield token.value
        elif token.type=='function' and token.lower_name=='url':
            args=[t for t in token.arguments if t.type not in ('whitespace','comment')]
            if len(args)==1 and hasattr(args[0],'value'):
                yield args[0].value
        else:
            for name in ('content','arguments','prelude'):
                inner=getattr(token,name,None)
                if inner is not None:
                    yield from css_values(inner)

def discover_css(text: str, url: str) -> list[str]:
    rules=tinycss2.parse_stylesheet(text,skip_whitespace=True,skip_comments=True)
    values=list(css_values(rules))
    for rule in rules:
        if rule.type=='at-rule' and rule.lower_at_keyword=='import':
            first=next((t for t in rule.prelude if t.type not in ('whitespace','comment')),None)
            if first is not None and first.type=='string':
                values.append(first.value)
    return list(dict.fromkeys(u for v in values if (u:=original_url(v,url))))

def discover_html(text: str,url: str) -> list[dict]:
    soup=BeautifulSoup(text,'html.parser')
    found={}
    def add(value, kind=None, pages=False):
        u=original_url(value,url)
        host=urlsplit(u).hostname if u else None
        if not u or (pages and not (is_site(u) or host=='bluescholars.livejournal.com')):
            return
        found[u]={'url':u,'kind':kind or kind_for(u),'referrer':url}
    for a in soup.find_all('a',href=True):
        add(a['href'],None,True)
    # Image-map regions are ordinary user-activated navigation links. Discover
    # their local HTML destinations so missing pages can receive explicit gap
    # routes just like links inside anchors.
    for area in soup.find_all('area',href=True):
        add(area['href'],None,True)
    for link in soup.find_all('link',href=True):
        rel=link.get('rel',[])
        if 'stylesheet' in rel:
            add(link['href'],'css')
        elif any(r in rel for r in ('icon','shortcut','apple-touch-icon')):
            add(link['href'],'image')
    for img in soup.find_all(['img','source']):
        for attr in ('src','data-src','data-image','data-original'):
            if img.get(attr): add(img[attr],'image')
        for attr in ('srcset','data-srcset'):
            for entry in img.get(attr,'').split(','):
                if entry.strip(): add(entry.strip().split()[0],'image')
    for node in soup.find_all(True):
        if node.get('poster'): add(node['poster'],'image')
        if node.get('style'):
            for u in discover_css('x{'+node['style']+'}',url): add(u)
        data=node.get('data-block-json')
        if data:
            try:
                walk_json(json.loads(data),add)
            except (ValueError,TypeError):
                pass
    for style in soup.find_all('style'):
        for u in discover_css(style.get_text(),url): add(u)
    for script in soup.find_all('script',type='application/ld+json'):
        try:
            walk_json(json.loads(script.get_text()),add)
        except (ValueError,TypeError):
            pass
    return list(found.values())

def walk_json(value,add):
    if isinstance(value,dict):
        for k,v in value.items():
            if k.lower() in ('asseturl','thumbnailurl','image','imageurl','contenturl') and isinstance(v,str):
                add(v,'image')
            else:
                walk_json(v,add)
    elif isinstance(value,list):
        for v in value: walk_json(v,add)
