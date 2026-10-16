"""Preserve source markup while removing live platform, archive and tracking behavior."""
from __future__ import annotations
import json
import re
from urllib.parse import urlsplit,parse_qs
from bs4 import BeautifulSoup,Comment
import tinycss2
from .urls import HOME,TARGET,original_url,identity,is_site,route,base_path,livejournal_route

NAV=[('BLOG','/blog/'),('SHOWS','/shows/'),('VIDEO','/video/'),('SHOP','/shop/'),('HOLLER','/holler/')]
CSP="default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'none'; connect-src 'none'; frame-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"

class Resolver:
    def __init__(self,resources,base,issues,route_prefix=''):
        self.resources=resources;self.base=base_path(base);self.issues=issues
        self.route_prefix=route_prefix.rstrip('/')
        self.aliases={identity(u):r for u,r in resources.items()}
    def _record(self,url):
        record=self.resources.get(url) or self.aliases.get(identity(url),{})
        if record.get('local_path'):
            return record
        parts=urlsplit(url)
        if parts.scheme in ('http','https') and parts.hostname:
            alternate=('http' if parts.scheme=='https' else 'https')+'://'+parts.netloc+parts.path
            if parts.query:alternate+='?'+parts.query
            fallback=self.resources.get(alternate) or self.aliases.get(identity(alternate),{})
            if fallback.get('local_path'):
                return fallback
        return record
    def asset(self,value,url):
        if str(value).startswith('#'): return value
        u=original_url(value,url)
        record=self._record(u)
        if record.get('local_path'):
            return self.base+record['local_path']
        if u:
            self.issues.append({'type':'missing_asset','source':url,'url':u})
        return None
    def link(self,value,url):
        if value.startswith('#'): return value
        u=original_url(value,url)
        if not u: return None
        fragment=urlsplit(value).fragment
        record=self._record(u)
        if record.get('local_path'):
            target=self.base+record['local_path']
        elif (local:=livejournal_route(u)):
            target=self.base+local
        elif is_site(u):
            if record.get('kind') in ('image','css','font','script','unsupported'):
                self.issues.append({'type':'linked_asset_not_recovered','source':url,'url':u})
                return self.base+'/archive-status/'
            try: target=self.base+self.route_prefix+route(record.get('final_original') or u)
            except ValueError:
                self.issues.append({'type':'unsafe_route','source':url,'url':u})
                return self.base+'/archive-status/'
        else: target=u
        return target+('#'+fragment if fragment else '')

def _tokens(tokens,resolver,url):
    result=[]
    for t in tokens:
        if t.type=='url':
            result.append('url('+json.dumps(resolver.asset(t.value,url) or 'data:,')+')')
        elif t.type=='function':
            if t.lower_name=='url':
                args=[a for a in t.arguments if a.type not in ('whitespace','comment')]
                value=args[0].value if len(args)==1 and hasattr(args[0],'value') else ''
                result.append('url('+json.dumps(resolver.asset(value,url) or 'data:,')+')')
            elif t.lower_name not in ('expression',):
                result.append(t.name+'('+_tokens(t.arguments,resolver,url)+')')
        elif t.type in ('{} block','[] block','() block'):
            left,right={'{} block':('{','}'),'[] block':('[',']'),'() block':('(',')')}[t.type]
            result.append(left+_tokens(t.content,resolver,url)+right)
        elif t.type not in ('error','comment'):
            result.append(t.serialize())
    return ''.join(result)

def _declarations(text,resolver,url):
    output=[]
    for d in tinycss2.parse_declaration_list(text,skip_comments=True,skip_whitespace=True):
        if d.type!='declaration' or d.lower_name in ('behavior','-moz-binding'):
            continue
        output.append(d.name+':'+_tokens(d.value,resolver,url)+('!important' if d.important else '')+';')
    return ''.join(output)

def _rules(text,resolver,url):
    result=[]
    for rule in tinycss2.parse_stylesheet(text,skip_whitespace=True,skip_comments=True):
        if rule.type=='at-rule':
            name=rule.lower_at_keyword
            if name=='font-face':
                resolver.issues.append({'type':'font_not_packaged','source':url})
                continue
            if name in ('charset','namespace'): continue
            if name=='import':
                meaningful=[t for t in rule.prelude if t.type not in ('whitespace','comment')]
                if not meaningful: continue
                first=meaningful[0]
                if first.type=='string':
                    local=resolver.asset(first.value,url)
                    if not local: continue
                    prefix='url('+json.dumps(local)+')'
                else:
                    prefix=_tokens([first],resolver,url)
                    if 'data:,' in prefix: continue
                result.append('@import '+prefix+' '+_tokens(rule.prelude[rule.prelude.index(first)+1:],resolver,url)+';')
                continue
            prelude=_tokens(rule.prelude,resolver,url)
            if rule.content is None:
                result.append('@'+rule.at_keyword+prelude+';')
            else:
                nested=tinycss2.serialize(rule.content)
                result.append('@'+rule.at_keyword+prelude+'{'+_rules(nested,resolver,url)+'}')
        elif rule.type=='qualified-rule':
            result.append(_tokens(rule.prelude,resolver,url)+'{'+_declarations(tinycss2.serialize(rule.content),resolver,url)+'}')
    return '\n'.join(result)

def render_css(text: str,url: str,resources: dict,base: str) -> tuple[str,list]:
    issues=[];resolver=Resolver(resources,base,issues)
    return _rules(text,resolver,url),issues

def _media_href(value,url):
    u=original_url(value,url)
    if not u: return None
    p=urlsplit(u)
    if p.hostname in ('youtube.com','www.youtube.com','youtube-nocookie.com','www.youtube-nocookie.com') and p.path.startswith('/embed/'):
        video_id=p.path.split('/')[2]
        if re.fullmatch('[A-Za-z0-9_-]{11}',video_id):
            return 'https://www.youtube.com/watch?v='+video_id
    return u

def render_html(text: str,url: str,resources: dict,base: str,route_prefix='') -> tuple[str,list]:
    base=base_path(base);issues=[];resolver=Resolver(resources,base,issues,route_prefix)
    soup=BeautifulSoup(text,'html.parser')
    if soup.html is None:
        wrapper=BeautifulSoup('<!doctype html><html><head></head><body></body></html>','html.parser')
        for child in list(soup.contents): wrapper.body.append(child.extract())
        soup=wrapper
    if soup.head is None:
        soup.html.insert(0,soup.new_tag('head'))
    if soup.body is None:
        soup.html.append(soup.new_tag('body'))
    # Squarespace commonly stores an iframe as escaped data-html instead of live markup.
    # Parse only that inert embed fragment; never execute the associated platform code.
    def embed_fragments(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key.lower() in ('html','embedhtml') and isinstance(item,str):
                    yield item
                else:
                    yield from embed_fragments(item)
        elif isinstance(value,list):
            for item in value: yield from embed_fragments(item)
    for container in list(soup.find_all(True)):
        fragments=[]
        if container.get('data-html'): fragments.append(container['data-html'])
        if container.get('data-block-json'):
            try: fragments.extend(embed_fragments(json.loads(container['data-block-json'])))
            except (ValueError,TypeError): pass
        if fragments and not container.find('iframe'):
            seen=set()
            for fragment in fragments:
                embedded=BeautifulSoup(fragment,'html.parser')
                for frame in embedded.find_all('iframe',src=True):
                    href=_media_href(frame['src'],url)
                    if href and href not in seen:
                        seen.add(href)
                        container.append(soup.new_tag('iframe',src=frame['src']))
    # Extract stylesheet tags first. The archived Squarespace document leaves
    # void <meta> tags open to html.parser, nesting head links inside them.
    stylesheet_links=[]
    for link in list(soup.find_all('link',href=True)):
        # Decomposing a malformed stylesheet link can detach nested links
        # retained by html.parser in older LiveJournal markup.
        if link.attrs is None:
            continue
        if 'stylesheet' in link.get('rel',[]):
            stylesheet_links.append({'href':link.get('href',''),'rel':link.get('rel',[]),
                                     'media':link.get('media'),'type':link.get('type')})
            # A malformed void <link> can own later script tags in html.parser.
            # Destroy the entire untrusted subtree and recreate a clean tag below.
            link.decompose()
    for comment in list(soup.find_all(string=lambda s:isinstance(s,Comment))): comment.extract()
    for node in list(soup.select('#wm-ipp,#wm-ipp-base,#donato,#wm-capinfo-notice,.wb-autocomplete-suggestions')):
        node.decompose()
    for node in list(soup.find_all(['script','base','object','embed','applet','noscript'])): node.decompose()
    for node in list(soup.find_all('meta')):
        # BeautifulSoup's html.parser can nest later head elements under a
        # malformed/void meta tag in captured Squarespace markup. Removing an
        # earlier Open Graph parent detaches those descendants; skip them.
        if node.attrs is None:
            continue
        if node.get('http-equiv') or node.get('property','').startswith(('og:','twitter:')): node.decompose()
    for link in list(soup.find_all('link')):
        link.decompose()
    for descriptor in stylesheet_links:
        local=resolver.asset(descriptor['href'],url)
        if local:
            link=soup.new_tag('link',href=local,rel=descriptor['rel'])
            if descriptor.get('media'):link['media']=descriptor['media']
            if descriptor.get('type'):link['type']=descriptor['type']
            soup.head.append(link)
    for style in soup.find_all('style'):
        style.string=_rules(style.get_text(),resolver,url)
    for node in list(soup.find_all(['iframe','video','audio'])):
        href=_media_href(node.get('src',''),url)
        if not href:
            source=node.find('source')
            if source: href=_media_href(source.get('src',''),url)
        replacement=soup.new_tag('p',attrs={'class':'archive-media'})
        if href:
            anchor=soup.new_tag('a',href=href,rel='noopener noreferrer')
            anchor.string='Watch on YouTube' if 'youtube.com/watch' in href else 'Open original external media'
            replacement.append(anchor)
        else: replacement.string='Embedded media has not been recovered.'
        node.replace_with(replacement)
        issues.append({'type':'external_media_link_only','source':url,'url':href})
    for picture in list(soup.find_all('source')): picture.decompose()
    for img in list(soup.find_all('img')):
        values=[img.get(x,'') for x in ('data-src','data-image','data-original','src')]
        values.extend(entry.strip().split()[0] for entry in img.get('srcset',img.get('data-srcset','')).split(',') if entry.strip())
        local=None
        for value in values:
            if value and (local:=resolver.asset(value,url)): break
        if local:
            img['src']=local;img['loading']='lazy';img['decoding']='async'
            for attr in ('srcset','data-src','data-image','data-original','data-srcset'): img.attrs.pop(attr,None)
            img.attrs.setdefault('alt','')
        else:
            span=soup.new_tag('span',attrs={'class':'archive-missing-image','role':'img'})
            alt=img.get('alt','').strip()
            span.string='Image not recovered'+(' — '+alt if alt else '')
            img.replace_with(span)
    for form in list(soup.find_all('form')):
        form.name='div';form.attrs={'class':'archive-historical-form'}
        notice=soup.new_tag('p',attrs={'class':'archive-notice'})
        notice.string='Historical form — submissions are disabled.';form.insert(0,notice)
    for control in soup.find_all(['input','button','select','textarea']):
        control['disabled']='disabled'
        for attr in ('formaction','form','action','src'): control.attrs.pop(attr,None)
    for a in soup.find_all('a'):
        if a.get('href'):
            if ('archive-source-link' in a.get('class',[]) and
                a['href'].startswith('https://web.archive.org/web/')):
                target=a['href']
            else:
                target=resolver.link(a['href'],url)
            if target:
                a['href']=target
                if urlsplit(target).scheme: a['rel']='noopener noreferrer'
            else:
                a.attrs.pop('href',None)
    for node in soup.find_all(True):
        for attr in list(node.attrs):
            if attr.lower().startswith(('on','data-')) or attr.lower() in ('srcdoc','action','formaction','manifest','ping','background','xlink:href'):
                del node.attrs[attr]
        if node.get('style'):
            node['style']=_declarations(node['style'],resolver,url)
        # No stray fetching attributes on unknown elements, including inline SVG.
        if node.name not in ('img',) and node.get('src'): node.attrs.pop('src',None)
        if node.name not in ('a','link') and node.get('href'): node.attrs.pop('href',None)
        node.attrs.pop('srcset',None)
    for svg in list(soup.find_all('svg')):
        # Inline vectors can carry active/external content; retain safe geometry only.
        from .svg import sanitize_svg
        try:
            safe=BeautifulSoup(sanitize_svg(str(svg).encode()).decode(),'html.parser')
            svg.replace_with(safe)
        except ValueError:
            svg.decompose();issues.append({'type':'unsafe_svg_removed','source':url})
    if not soup.head.find('meta',attrs={'charset':True}): soup.head.insert(0,soup.new_tag('meta',charset='utf-8'))
    if not soup.head.find('meta',attrs={'name':'viewport'}):
        soup.head.append(soup.new_tag('meta',attrs={'name':'viewport','content':'width=device-width, initial-scale=1'}))
    soup.head.append(soup.new_tag('meta',attrs={'http-equiv':'Content-Security-Policy','content':CSP}))
    soup.head.append(soup.new_tag('link',rel='stylesheet',href=base+'/assets/archive-ui.css'))
    soup.head.append(soup.new_tag('script',src=base+'/assets/legacy.js',defer='defer'))
    aside=soup.new_tag('aside',attrs={'class':'archive-restoration-notice'})
    anchor=soup.new_tag('a',href=base+'/archive-status/')
    anchor.string='Historical restoration • recovery status';aside.append(anchor)
    details=soup.new_tag('details',attrs={'class':'archive-navigation'})
    summary=soup.new_tag('summary');summary.string='Navigation';details.append(summary)
    nav=soup.new_tag('nav',attrs={'aria-label':'Static navigation'})
    nav_prefix=resolver.route_prefix or '/2013'
    if resolver.route_prefix.startswith('/lj'):
        links=[('ARCHIVE HOME','/'),('LIVEJOURNAL ARCHIVE','/lj/')]
    else:
        links=[('ARCHIVE HOME','/'),('EDITION HOME','/')]
        if not resolver.route_prefix.startswith(('/2007','/2009')): links+=NAV
    for label,path in links:
        target=path if label in ('ARCHIVE HOME','LIVEJOURNAL ARCHIVE') else nav_prefix+path
        a=soup.new_tag('a',href=base+target);a.string=label;nav.append(a)
    details.append(nav);aside.append(details);soup.body.insert(0,aside)
    return str(soup),issues
