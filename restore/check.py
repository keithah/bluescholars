"""Offline validation of navigation and automatic resource dependencies."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
from .discover import discover_css
from .urls import base_path

ORIGIN='https://static.invalid'

def check(output: Path,base: str='') -> list[str]:
    output=Path(output).resolve();base=base_path(base);errors=[]
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
            # Root-mounted shared resources are an exception: the source HTML
            # contains /assets/* while Pages serves them below the project base.
            if base and path.startswith('/assets/'):
                path=base+path
            if base and not path.startswith(base+'/'):
                errors.append(f'{source}: escaped deployment base {value}');return
            rel=path[len(base):].lstrip('/') if base else path.lstrip('/')
        else:
            path=unquote(urlsplit(urljoin(source_url,value)).path)
            if base and not path.startswith(base+'/'):
                errors.append(f'{source}: escaped deployment base {value}');return
            rel=path[len(base):].lstrip('/') if base else path.lstrip('/')
        target=(output/rel).resolve()
        if not target.is_relative_to(output):
            errors.append(f'{source}: path traversal {value}');return
        if target.is_dir(): target=target/'index.html'
        if not target.is_file(): errors.append(f'{source}: missing local target {value}')
    for file in output.rglob('*.html'):
        source=file.relative_to(output).as_posix();soup=BeautifulSoup(file.read_text(),'html.parser')
        for node in soup.find_all(True):
            if any(k.lower().startswith('on') for k in node.attrs): errors.append(f'{source}: active inline handler')
            if node.name=='form': errors.append(f'{source}: active historical form')
            if node.name=='script' and not node.get('src'): errors.append(f'{source}: inline script')
            if node.name=='meta' and str(node.get('http-equiv','')).lower()=='refresh': errors.append(f'{source}: automatic refresh')
            for attr in ('src','poster','srcset','background'):
                if node.get(attr):
                    if attr=='srcset':
                        for entry in node[attr].split(','):
                            if entry.strip(): verify(entry.strip().split()[0],source,True)
                    else: verify(node[attr],source,True)
            # Image-map areas are navigation controls like anchors. Their
            # destinations are fetched only after user activation, never as
            # automatic page dependencies.
            if node.get('href'): verify(node['href'],source,node.name not in ('a','area'))
            if node.get('style'):
                for u in discover_css('x{'+node['style']+'}',ORIGIN+base+'/'+source):
                    verify(u.removeprefix(ORIGIN) if u.startswith(ORIGIN+'/') else u,source,True)
        for style in soup.find_all('style'):
            for u in discover_css(style.get_text(),ORIGIN+base+'/'+source):
                verify(u.removeprefix(ORIGIN) if u.startswith(ORIGIN+'/') else u,source,True)
    for file in output.rglob('*.css'):
        source=file.relative_to(output).as_posix()
        for u in discover_css(file.read_text(),ORIGIN+base+'/'+source):
            verify(u.removeprefix(ORIGIN) if u.startswith(ORIGIN+'/') else u,source,True)
    return sorted(set(errors))
