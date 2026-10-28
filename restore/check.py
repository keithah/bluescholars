"""Offline validation of navigation and automatic resource dependencies."""
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from html.parser import HTMLParser
from .discover import discover_css
from .urls import base_path

ORIGIN='https://static.invalid'

def check(output: Path,base: str='') -> list[str]:
    output=Path(output).resolve();base=base_path(base);errors=[];target_cache={}
    def verify(value,source,automatic=False):
        if not value or value.startswith(('data:','#')): return
        parsed=urlsplit(value)
        if parsed.scheme or parsed.netloc:
            if automatic: errors.append(f'{source}: remote automatic resource {value}')
            elif parsed.scheme not in ('http','https','mailto','tel'): errors.append(f'{source}: unsafe link {value}')
            return
        source_url=ORIGIN+base+'/'+source
        # Generated site links are root-absolute and intentionally include the
        # GitHub Pages mount prefix. Resolve them from that mount directly;
        # relative links still resolve from their containing document.
        if value.startswith('/'):
            path=unquote(urlsplit(value).path)
            if base and not path.startswith(base+'/'):
                errors.append(f'{source}: escaped deployment base {value}');return
            rel=path[len(base):].lstrip('/') if base else path.lstrip('/')
        else:
            path=unquote(urlsplit(urljoin(source_url,value)).path)
            if base and not path.startswith(base+'/'):
                errors.append(f'{source}: escaped deployment base {value}');return
            rel=path[len(base):].lstrip('/') if base else path.lstrip('/')
        if rel not in target_cache:
            target=(output/rel).resolve()
            if not target.is_relative_to(output): target_cache[rel]='path traversal'
            else:
                if target.is_dir(): target=target/'index.html'
                target_cache[rel]=None if target.is_file() else 'missing local target'
        if target_cache[rel]: errors.append(f'{source}: {target_cache[rel]} {value}')

    class PageChecker(HTMLParser):
        # Validation needs attributes and style text, not an expensive DOM for
        # every preserved forum page. Keep the same checks in a streaming parser.
        def __init__(self,source):
            super().__init__(convert_charrefs=True)
            self.source=source;self.in_style=False;self.style=[]

        def handle_starttag(self,tag,attrs):
            node=dict(attrs);source=self.source
            if any(k.startswith('on') for k in node): errors.append(f'{source}: active inline handler')
            if tag=='form': errors.append(f'{source}: active historical form')
            if tag=='script' and not node.get('src'): errors.append(f'{source}: inline script')
            if tag=='meta' and str(node.get('http-equiv','')).lower()=='refresh':
                match=re.fullmatch(r"\s*0(?:\.0+)?\s*;\s*url\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s;]+))\s*",str(node.get('content','')),re.I)
                target=next((value for value in match.groups() if value is not None),"") if match else ""
                if not target or target.startswith(('#','data:')): errors.append(f'{source}: unsafe or malformed automatic refresh')
                else: verify(target,source,True)
            for attr in ('src','poster','srcset','background'):
                if node.get(attr):
                    if attr=='srcset':
                        for entry in node[attr].split(','):
                            if entry.strip(): verify(entry.strip().split()[0],source,True)
                    else: verify(node[attr],source,True)
            if node.get('href'): verify(node['href'],source,tag not in ('a','area'))
            if node.get('style'): self.check_css('x{'+node['style']+'}')
            if tag=='style': self.in_style=True;self.style=[]

        def check_css(self,text):
            for u in discover_css(text,ORIGIN+base+'/'+self.source):
                verify(u.removeprefix(ORIGIN) if u.startswith(ORIGIN+'/') else u,self.source,True)

        def handle_data(self,data):
            if self.in_style: self.style.append(data)

        def handle_endtag(self,tag):
            if tag=='style' and self.in_style:
                self.check_css(''.join(self.style));self.in_style=False;self.style=[]

    for file in output.rglob('*'):
        if not file.is_file(): continue
        source=file.relative_to(output).as_posix()
        if file.suffix.lower() in ('.php','.asp','.aspx','.cgi'):
            with file.open('rb') as stream: prefix=stream.read(1024).lower()
            if b'<html' in prefix or b'<!doctype html' in prefix:
                errors.append(f'{source}: HTML page has non-renderable static hosting suffix')
        if file.suffix.lower() not in ('.html','.htm'): continue
        parser=PageChecker(source);parser.feed(file.read_text(encoding='utf-8',errors='replace'));parser.close()
        if parser.in_style: parser.check_css(''.join(parser.style))
    for file in output.rglob('*.css'):
        if not file.is_file(): continue
        source=file.relative_to(output).as_posix()
        for u in discover_css(file.read_text(),ORIGIN+base+'/'+source):
            verify(u.removeprefix(ORIGIN) if u.startswith(ORIGIN+'/') else u,source,True)
    return sorted(set(errors))
