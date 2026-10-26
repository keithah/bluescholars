"""Deterministic static output; unreviewed downloads never enter a release build."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import shutil
from urllib.parse import parse_qsl,unquote,urlencode,urlsplit,urlunsplit
from bs4 import BeautifulSoup
from .archive import validate_payload
from .discover import discover_html
from .render import render_html,render_css,resource_aliases,NAV
from .svg import sanitize_svg
from .state import State,write_json
from .urls import HOME,TARGET,SQUARESPACE_START,identity,is_site,route,asset_route,base_path,livejournal_route,original_url,historical_route_prefix,route_capture_hint
from .artist_sites import build_artist_sites
from .massline import build_massline_archive
from .myspace import build_myspace_archive
from .feeds import collect_feed_entries
from .proof206 import build_206proof_archive
from .twitter import build_twitter_archive
from .redact import public_credential_fields, redact_public_credentials
from .press_archive import build_press_archive
from .twitter import build_twitter_archive

CORE=[('/', 'Homepage'),('/blog/','Blog'),('/shows/','Shows'),('/video/','Video'),('/shop/','Shop'),('/holler/','Holler')]
FALLBACK_UI='''.archive-restoration-notice,.archive-gap-page {font:16px/1.6 system-ui,sans-serif}
.archive-restoration-notice{padding:12px;border-bottom:1px solid #ddd}.archive-navigation a{margin-right:16px}
.archive-menu-open #mobileNav{height:auto!important;overflow:visible!important}
.archive-menu-open #mobileMenuLink a{cursor:pointer}
.archive-gap-page{max-width:900px;margin:60px auto;padding:0 24px}.archive-missing-image{display:block;padding:30px;border:1px dashed #999}
.archive-gap-page a{overflow-wrap:anywhere}.archive-gap-page table{width:100%;border-collapse:collapse}.archive-gap-page td,.archive-gap-page th{padding:12px;text-align:left;border-bottom:1px solid #ddd}'''

def read_record(root: Path,r: dict,allow_recovery: bool) -> bytes:
    path=(root/r['raw_path']).resolve()
    allowed=[(root/'source/raw').resolve(),(root/'source/redacted').resolve()]
    if allow_recovery: allowed.append((root/'recovery/raw').resolve())
    if not any(path.is_relative_to(prefix) for prefix in allowed):
        raise ValueError('Raw source path escapes the approved source directories')
    body=path.read_bytes()
    if hashlib.sha256(body).hexdigest()!=r['sha256']:
        raise ValueError(f'Source hash mismatch: {r["url"]}')
    validate_payload(body,r['kind'])
    return body

def promote(root: Path,reviewed: bool=False,allow_later: bool=False) -> dict:
    if not reviewed: raise ValueError('Source review is required: pass --reviewed after inspection')
    if allow_later:
        raise ValueError('Global later-capture approval is disabled; review each resource with compatibility-review first')
    root=Path(root);state=State(root)
    catalog_path=root/'source/catalog.json'
    catalog=json.loads(catalog_path.read_text()) if catalog_path.exists() else {'version':1,'resources':{}}
    staged=[];rejected_provider_errors=[]
    # Verify all selected files before modifying the approved collection.
    for url,r in state.data['resources'].items():
        eligible=r['status']=='recovered' or (
            r['status']=='needs_review' and bool(r.get('compatibility_review'))
        )
        if eligible and r.get('raw_path') and r['kind'] in ('html','css','image'):
            try:
                body=read_record(root,r,True)
            except ValueError as exc:
                if str(exc)!='Captured provider/archive error page, not site content':raise
                r.update(status='failed',
                         reason='Payload validation rejected this archived provider/archive error page; other indexed captures remain eligible for retry.',
                         payload_validation_error=str(exc))
                rejected_provider_errors.append(url)
                if url not in catalog['resources']:
                    catalog['resources'][url]={k:v for k,v in r.items() if k not in ('raw_path','sha256')}
                continue
            staged.append((url,r,body))
        elif url not in catalog['resources']:
            catalog['resources'][url]={k:v for k,v in r.items() if k not in ('raw_path','sha256')}
    if rejected_provider_errors:state.save()
    redacted_payloads=0
    for url,r,body in staged:
        copied=dict(r)
        public_body,redaction_count=redact_public_credentials(body)
        if redaction_count:
            redacted_payloads+=1
            fields=public_credential_fields(body)
            original_sha256=r['sha256']
            digest=hashlib.sha256(public_body).hexdigest()
            path=f'source/redacted/{digest}.html'
            copied.update(sha256=digest,original_sha256=original_sha256,
                          source_redaction={'field':', '.join(fields),
                                            'count':redaction_count,
                                            'reason':'Credential-shaped value omitted from public source copy.'})
        else:
            path='source/raw/'+Path(r['raw_path']).name
        destination=root/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(public_body)
        copied.update(raw_path=path,source_reviewed=True,
                      later_capture_approved=bool(r.get('compatibility_review')),status='recovered')
        catalog['resources'][url]=copied
    if staged:
        review_path=root/'source/review.json'
        existing=json.loads(review_path.read_text()) if review_path.exists() else {}
        write_json(review_path,{**existing,'publish_approved':False,'visual_reviewed':False,
                   'note':'Source collection changed; review the generated site before publishing.'})
    write_json(catalog_path,catalog)
    return {'promoted':len(staged),'redacted_payloads':redacted_payloads,'rejected_provider_errors':len(rejected_provider_errors),'publish_approved':False}

def page_shell(title: str,body: str) -> str:
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'+html.escape(title)+' — Blue Scholars restoration</title></head><body><main class="archive-gap-page"><p class="archive-eyebrow">BLUE SCHOLARS / RESTORATION WORKSPACE</p><h1>'+html.escape(title)+'</h1>'+body+'</main></body></html>'

def build_community_media(root:Path,output:Path,base:str,render_resources:dict,aliases:dict,ui_href:str,script_href:str)->int:
    catalog_path=root/'source/community-media.json'
    if not catalog_path.exists():return 0
    catalog=json.loads(catalog_path.read_text())
    figures=[]
    media_root=(root/'source/community-media').resolve()
    for item in catalog.get('items',[]):
        source=(root/item['path']).resolve()
        if not source.is_relative_to(media_root):raise ValueError('Community-media source escapes its collection')
        body=source.read_bytes()
        if hashlib.sha256(body).hexdigest()!=item['sha256']:
            raise ValueError('Community-media source hash mismatch: '+str(item.get('title','')))
        if not body.startswith(b'\xff\xd8\xff'):
            raise ValueError('Community-media image is not a validated JPEG: '+str(item.get('title','')))
        filename='community-media-'+item['sha256'][:16]+'.jpg'
        relative='assets/'+filename
        destination=output/relative
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(body)
        render_resources[item['asset_url']]={'url':item['asset_url'],'kind':'image','local_path':'/'+relative}
        image_url=html.escape(item['asset_url'],quote=True)
        title=html.escape(item['title'])
        alt=html.escape(item['description'],quote=True)
        commons_url=html.escape(item['commons_url'],quote=True)
        license_url=html.escape(item['license_url'],quote=True)
        source_url=item.get('source_url','')
        source_link=(f'<a href="{html.escape(source_url,quote=True)}">'
                     f'{html.escape(item.get("source_label","Original source record"))}</a> · '
                     if source_url else '')
        credit=(f'<p>{html.escape(item["author"])} · {html.escape(item["date"])}. '
                f'{source_link}<a href="{commons_url}">Wikimedia Commons file record</a>.</p>'
                f'<p>Licensed under <a href="{license_url}">{html.escape(item["license"])}</a>. '
                'Image reproduced unchanged.</p>')
        figures.append(f'<figure class="community-media-item"><img src="{image_url}" alt="{alt}" loading="lazy">'
                       f'<figcaption><strong>{title}</strong>{credit}</figcaption></figure>')
    videos=''.join(
        f'<li><a href="{html.escape(v["stream_url"],quote=True)}">{html.escape(v["title"])}</a> '
        f'({html.escape(v["date"])}, {html.escape(v["format"])}). '
        f'<a href="{html.escape(v["source_page"],quote=True)}">PBS page</a>. '
        f'{html.escape(v["note"])}</li>' for v in catalog.get('videos',[]))
    linked=''.join(
        f'<li><a href="{html.escape(v["url"],quote=True)}">{html.escape(v["title"])}</a> '
        f'({html.escape(v["uploader"])}, {html.escape(v["date"])})</li>' for v in catalog.get('linked_videos',[]))
    if not figures and not videos and not linked:return 0
    body=''
    if figures:
        body+=('<p>This image was found in a separately licensed public collection. It is supplemental context, '
               'not an asset recovered from a Blue Scholars website capture.</p>'
               '<div class="community-media-grid">'+''.join(figures)+'</div>')
    if videos:
        body+=('<h2>Linked video</h2><p>These videos are linked, not embedded: most are hosted on stream.new, and one points to its publisher. '
               'They are current-source copies, not archived captures; rights are unreviewed.</p><ul>'+videos+'</ul>')
    if linked:
        body+=('<h2>Videos on other sites</h2><p>These are links to videos referenced by recovered pages that are still public on YouTube or Vimeo. '
               'Nothing is copied or embedded here, and availability is as checked on the date in the recovery catalog.</p><ul>'+linked+'</ul>')
    text=page_shell('Supplemental community media',body)
    text,_=render_html(text,HOME,render_resources,base,aliases=aliases,ui_stylesheet=ui_href,ui_script=script_href)
    _write_page(output,'/community-media/',text)
    return len(figures)+len(catalog.get('videos',[]))+len(catalog.get('linked_videos',[]))

def _write_page(output: Path,path: str,text: str):
    relative=unquote(path.lstrip('/'))
    destination=output/relative if relative.lower().endswith('.html') else output/relative/'index.html'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(text,encoding='utf-8')

def add_global_year_navigation(text: str,year: int,base: str,ui_href: str,
                               timeline_script_href: str,page_years: dict[str,int]|None=None) -> str:
    """Add the shared year control and annotate links to dated local pages."""
    base=base_path(base);page_years=page_years or {}
    try: year=int(year)
    except (TypeError,ValueError): year=2007
    year=max(2006,min(2026,year))
    soup=BeautifulSoup(text,'html.parser')
    if soup.html is None:
        wrapper=BeautifulSoup('<!doctype html><html><head></head><body></body></html>','html.parser')
        wrapper.body.extend(list(soup.contents));soup=wrapper
    if soup.head is None: soup.html.insert(0,soup.new_tag('head'))
    if soup.body is None: soup.html.append(soup.new_tag('body'))
    if not soup.select_one('.archive-year-global'):
        section=soup.new_tag('section',attrs={'class':'archive-year-global','aria-label':'Browse the archive by year','data-default-year':str(year),'data-base-path':base})
        home=soup.new_tag('a',attrs={'class':'archive-year-global-brand','href':base+'/'})
        home.string='Blue Scholars archive';section.append(home)
        label=soup.new_tag('label',attrs={'for':'archive-year-global-control'});label.string='Year';section.append(label)
        output=soup.new_tag('output',attrs={'id':'archive-year-global-output','for':'archive-year-global-control'});output.string=str(year);section.append(output)
        control=soup.new_tag('input',attrs={'id':'archive-year-global-control','class':'archive-year-global-control','type':'range','min':'2006','max':'2026','step':'1','value':str(year),'data-default-year':str(year),'aria-label':'Choose a year and open that homepage','aria-valuetext':str(year)})
        section.append(control)
        route='/2007/' if year<=2008 else '/2009/' if year<=2012 else '/2013/'
        open_home=soup.new_tag('a',attrs={'class':'archive-year-home','href':base+route+'?year='+str(year)})
        open_home.string='Open '+str(year)+' homepage';section.append(open_home)
        soup.body.insert(0,section)
    if not soup.head.select_one('link[data-archive-year-styles]'):
        soup.head.append(soup.new_tag('link',rel='stylesheet',href=ui_href,attrs={'data-archive-year-styles':'true'}))
    if not soup.head.select_one('script[data-archive-year-script]'):
        soup.head.append(soup.new_tag('script',src=timeline_script_href,defer='defer',attrs={'data-archive-year-script':'true'}))
    for anchor in soup.find_all('a',href=True):
        parts=urlsplit(anchor['href'])
        if parts.scheme or parts.netloc or not parts.path.startswith(base+'/'):
            continue
        local_path=parts.path[len(base):]
        target_year=page_years.get(local_path)
        if target_year is None:
            target_year=page_years.get(local_path.rstrip('/')+'/')
        if target_year is None: continue
        query=parse_qsl(parts.query,keep_blank_values=True)
        if any(key=='year' for key,_ in query): continue
        query.append(('year',str(target_year)))
        anchor['href']=urlunsplit(('', '', parts.path,urlencode(query),parts.fragment))
    return str(soup)

def _default_year_for_path(path: str) -> int:
    parts=Path(path).parts
    for part in parts:
        if len(part)>=4 and part[:4].isdigit() and 2006<=int(part[:4])<=2026:
            return int(part[:4])
    defaults={'2007':2007,'2009':2009,'2013':2021,'prometheusbrown':2008,
        'sabzi':2013,'myspace':2007,'twitter-prometheusbrown':2009,
        'masslinemedia':2006,'massline-forums':2006,'206proof':2007,'lj':2008,
        'other-archives':2007}
    return defaults.get(parts[0],2007) if parts else 2007

def decorate_archive_pages(output: Path,base: str,ui_href: str,timeline_script_href: str,
                           page_report: list[dict]) -> int:
    """Install the shared slider on every page except the already interactive hub."""
    if not timeline_script_href: return 0
    page_years={}
    for row in page_report:
        path=str(row.get('path',''))
        stamp=str(row.get('actual_capture',''))
        if path and stamp[:4].isdigit(): page_years[path]=int(stamp[:4])
    changed=0
    for path in Path(output).rglob('*.html'):
        if not path.is_file(): continue
        relative=path.relative_to(output).as_posix()
        if relative=='index.html': continue
        text=path.read_text(encoding='utf-8',errors='replace')
        if 'class="archive-year-global"' in text or "class='archive-year-global'" in text: continue
        route='/'+relative.removesuffix('/index.html')
        if relative.endswith('/index.html'): route+='/'
        year=page_years.get(route,_default_year_for_path(relative))
        if relative in ('2007/index.html','2009/index.html','2013/index.html'):
            year={'2007/index.html':2007,'2009/index.html':2009,'2013/index.html':2021}[relative]
        updated=add_global_year_navigation(text,year,base,ui_href,timeline_script_href,page_years)
        if updated!=text:
            path.write_text(updated,encoding='utf-8');changed+=1
    return changed

def archive_availability(root: Path, path: str) -> tuple[int, int] | None:
    """Return an archive's observed capture-year bounds, where metadata exists."""
    root=Path(root)
    years=[]
    def add(value):
        stamp=str(value or '')
        if len(stamp)>=4 and stamp[:4].isdigit(): years.append(int(stamp[:4]))
    def walk(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ('timestamp','actual_capture','capture') and isinstance(item,(str,int)): add(item)
                else: walk(item)
        elif isinstance(value,list):
            for item in value: walk(item)
    if path in ('/2007/','/2009/','/2013/'):
        prefix={'/2007/':'/2007','/2009/':'/2009','/2013/':'/2013'}[path]
        for entry in (root/'_candidate/archive-status/report.json',root/'docs/recovery-report/GAP_REPORT.json',root/'recovery/state.json'):
            if entry.is_file():
                try:
                    report=json.loads(entry.read_text())
                    if entry.name=='state.json':
                        for item in report.get('resources',{}).values():
                            url=str(item.get('url',''))
                            if item.get('status')!='recovered': continue
                            stamp=str(item.get('actual_capture',''))
                            if prefix=='/2007' and ('bluescholars.com/artistedition' in url or stamp<'20090101000000'): add(stamp)
                            elif prefix=='/2009' and 'bluescholars.com/blog/' in url and '2009'<=stamp[:4]<='2012': add(stamp)
                            elif prefix=='/2013' and 'bluescholars.com' in url and '2013'<=stamp[:4]<='2021': add(stamp)
                    else:
                        for item in report.get('pages',[]):
                            if str(item.get('path','')).startswith(prefix+'/') and item.get('status') in ('recovered','derived_from_capture'):
                                add(item.get('actual_capture'))
                except (OSError,ValueError): pass
        site_inventory=root/'recovery/wayback-versions/manifest.json'
        if site_inventory.is_file():
            try:
                for record in json.loads(site_inventory.read_text()).get('revisions',{}).values():
                    url=str(record.get('original_url','')); stamp=str(record.get('timestamp',''))
                    if prefix=='/2007' and ('bluescholars.com/artistedition' in url or ('bluescholars.com' in url and stamp<'20090101000000')): add(stamp)
                    elif prefix=='/2009' and 'bluescholars.com/blog/' in url and '2009'<=stamp[:4]<='2012': add(stamp)
                    elif prefix=='/2013' and ('2013'<=stamp[:4]<='2021'): add(stamp)
            except (OSError,ValueError): pass
        if path=='/2007/':
            add(2007)
        defaults={'/2007/':(2007,2007),'/2009/':(2009,2012),'/2013/':(2013,2021)}
        bounds=(min(years),max(years)) if years else defaults[path]
        if path=='/2007/': return max(2007,bounds[0]),min(2008,bounds[1])
        if path=='/2009/': return max(2009,bounds[0]),min(2012,bounds[1])
        if path=='/2013/': return max(2013,bounds[0]),min(2021,bounds[1])
        return bounds
    if path in ('/prometheusbrown/','/sabzi/'):
        manifest=root/'recovery/artist-sites/manifest.json'
        if manifest.is_file():
            data=json.loads(manifest.read_text())
            domain='prometheusbrown.com' if 'prometheusbrown' in path else 'sabzi.co'
            for key,site in data.get('editions',{}).items():
                if not key.startswith(domain+'/'): continue
                for record in site.get('resources',{}).values():
                    if record.get('kind')=='html' and record.get('status')=='recovered': add(record.get('actual_capture'))
    elif path=='/myspace/':
        p=root/'recovery/myspace-blue-scholars/index/acquisition.json'
        if p.is_file():
            for item in json.loads(p.read_text()).get('records',[]):
                if item.get('status')=='recovered': add(item.get('actual_capture') or item.get('timestamp'))
    elif path=='/twitter-prometheusbrown/':
        p=root/'recovery/twitter-prometheusbrown/manifest.json'
        if p.is_file():
            for item in json.loads(p.read_text()).get('captures',[]):
                if item.get('content_classification')=='profile_content' and item.get('fetch',{}).get('status')=='recovered': add(item.get('timestamp'))
    elif path in ('/masslinemedia/','/massline-forums/'):
        p=root/'recovery/massline/manifest.json'
        if p.is_file():
            data=json.loads(p.read_text())
            for item in data.get('resource_variants',[]):
                if item.get('kind')=='html': add(item.get('timestamp'))
            for item in data.get('homepage_variants',[]): add(item.get('timestamp'))
            for item in data.get('resources',{}).values():
                if item.get('kind')=='html': add(item.get('timestamp'))
    elif path=='/206proof/':
        p=root/'recovery/206proof/manifest.json'
        if p.is_file():
            data=json.loads(p.read_text())
            for item in data.get('resources',{}).values(): add(item.get('timestamp'))
            for edition in data.get('editions',{}).values(): add(edition.get('capture'))
    elif path=='/other-archives/press/':
        p=root/'recovery/other-archives/press-articles/manifest.json'
        if p.is_file():
            for item in json.loads(p.read_text()).get('page_captures',{}).values(): add(item.get('timestamp'))
    elif path=='/lj/':
        state=root/'recovery/state.json'
        if state.is_file():
            for item in json.loads(state.read_text()).get('resources',{}).values():
                if 'livejournal.com' in str(item.get('url','')) and item.get('status')=='recovered': add(item.get('actual_capture'))
    return (min(years),max(years)) if years else None

def edition_prefix(url: str, record: dict) -> str:
    """Place observed pages under the historical platform generation they belong to."""
    from urllib.parse import urlsplit
    path=urlsplit(url).path
    segments=path.strip('/').split('/')
    capture=record.get('actual_capture') or TARGET
    if urlsplit(url).hostname=='02cd02a.netsolhost.com':return '/2009'
    if path.rstrip('/')=='/artistedition' or capture<'20090101000000':
        return '/2007'
    if (len(segments)>1 and segments[0]=='blog' and segments[1].isdigit()
            and len(segments[1])==4 and int(segments[1])<=2012):
        return '/2009'
    if capture<SQUARESPACE_START:
        return '/2009'
    return '/2013'

def eligible_site_page_capture(url: str, record: dict, min_reference_capture: str) -> bool:
    """Exclude the compromised intervening root capture from the 2007 edition.

    The 2008 root response is a keyword-injection page with the original site
    reduced to a single unarchived image. Keep its bytes in recovery, but use
    the last intact 2007 image-map homepage for the edition's root.
    """
    path=urlsplit(url).path or '/'
    capture=record.get('actual_capture','')
    if record.get('edition_exclusion',{}).get('exclude_from_site'):
        return False
    return capture>=min_reference_capture or edition_prefix(url,record) in ('/2007','/2009')

def documented_asset_aliases(root: Path,usable_variants: dict) -> tuple[dict,list]:
    """Resolve narrowly documented historical asset substitutions by provenance."""
    path=Path(root)/'source/asset-aliases.json'
    if not path.exists():return {},[]
    try:document=json.loads(path.read_text(encoding='utf-8'))
    except ValueError as exc:raise ValueError('Invalid source/asset-aliases.json') from exc
    if document.get('version')!=1 or not isinstance(document.get('aliases'),list):
        raise ValueError('Unsupported source/asset-aliases.json schema')
    aliases={};issues=[]
    for item in document['aliases']:
        if not isinstance(item,dict):
            issues.append({'type':'compatibility_alias_unavailable','url':'','source_url':'',
                           'reason':'Alias entry is not an object.'})
            continue
        target=item.get('url','');source=item.get('source_url','')
        record=next((variant for variant in usable_variants.values()
                     if variant.get('_source_url')==source
                     and variant.get('kind') in ('image','css')
                     and variant.get('sha256')==item.get('sha256')
                     and variant.get('actual_capture')==item.get('actual_capture')),None)
        source_kind=record.get('kind') if record else None
        valid=(bool(target and source and item.get('decision')) and record is not None
               and source_kind in ('image','css') and record.get('sha256')==item.get('sha256')
               and record.get('actual_capture')==item.get('actual_capture')
               and bool(record.get('local_path')))
        if not valid:
            issues.append({'type':'compatibility_alias_unavailable','url':target,
                           'source_url':source,'reason':'The documented capture/hash is not present as a validated local image or stylesheet.'})
            continue
        record=dict(record)
        local=record.get('local_path','')
        if not local or record['sha256'] not in Path(local).name:
            suffix='.css' if source_kind=='css' else Path(record['raw_path']).suffix
            record['local_path']='/assets/'+record['sha256']+suffix
        if identity(target) in aliases:
            raise ValueError(f'Duplicate documented asset alias: {target}')
        aliases[identity(target)]=record
    return aliases,issues

def build(root: Path,output: Path,base: str='',candidate: bool=False,release: bool=False) -> dict:
    root=Path(root).resolve();output=Path(output).resolve();base=base_path(base)
    if output.parent!=root or output.name not in ('_site','_candidate'):
        raise ValueError('Output must be the project’s generated _site or _candidate directory')
    review_path=root/'source/review.json'
    review=json.loads(review_path.read_text()) if review_path.exists() else {}
    if release and (candidate or not review.get('publish_approved') or not review.get('visual_reviewed')):
        raise ValueError('Publication requires source, visual and publish review approval')
    if candidate:
        data=State(root).data;records=json.loads(json.dumps(data['resources']))
        catalog_path=root/'source/catalog.json'
        if catalog_path.exists():
            catalog=json.loads(catalog_path.read_text()).get('resources',{})
            # Candidate builds read resumable bytes from recovery state, but
            # reviewed source policy lives in the tracked catalog. A capture
            # can have several archive keys, so carry dispositions across
            # aliases only when both the normalized page URL and payload hash
            # match.
            exclusions_by_capture={}
            for source_key,source_record in catalog.items():
                exclusion=source_record.get('edition_exclusion')
                digest=source_record.get('sha256')
                url=source_record.get('url',source_key)
                if exclusion and digest and url:
                    exclusions_by_capture[(identity(url),digest)]=exclusion
            for source_key,record in records.items():
                policy=catalog.get(source_key,{})
                if 'edition_exclusion' in policy:
                    record['edition_exclusion']=policy['edition_exclusion']
                else:
                    exclusion=exclusions_by_capture.get((
                        identity(record.get('url',source_key)),record.get('sha256')))
                    if exclusion:
                        record['edition_exclusion']=exclusion
    else:
        path=root/'source/catalog.json'
        catalog=json.loads(path.read_text()) if path.exists() else {'resources':{}}
        records=json.loads(json.dumps(catalog['resources']))
    inventory_path=root/'recovery/seeds/inventory.json'
    inventory=json.loads(inventory_path.read_text()) if inventory_path.exists() else {'pages':[]}
    feed_entries=collect_feed_entries(root)
    feed_entry_ids={identity(entry['url']) for entry in feed_entries.values()}
    for path,label in CORE:
        records.setdefault(HOME.rstrip('/')+path,{'url':HOME.rstrip('/')+path,'kind':'html','status':'queued'})
    for r in inventory.get('pages',[]):
        records.setdefault(r['original_url'],{'url':r['original_url'],'kind':'html','status':'queued'})
    explicit_page_ids={identity(HOME.rstrip('/')+path) for path,_ in CORE}
    explicit_page_ids.update(identity(r['original_url']) for r in inventory.get('pages',[]))
    usable={};usable_variants={};raw={};issues=[]
    for source_key,r in records.items():
        url=r.get('url',source_key)
        eligible_status=(r.get('status')=='recovered' or
                         (candidate and r.get('status')=='needs_review' and bool(r.get('compatibility_review'))))
        if r.get('raw_path') and eligible_status and r['kind'] in ('html','css','image'):
            try:
                raw[source_key]=read_record(root,r,candidate)
            except (OSError,ValueError) as exc:
                issues.append({'type':'invalid_source','url':url,'source_key':source_key,
                               'message':str(exc)})
                continue
            variant=dict(r);variant['_source_key']=source_key;variant['_source_url']=url
            usable_variants[source_key]=variant
            previous=usable.get(url)
            if previous is None or r.get('actual_capture','')>=previous.get('actual_capture',''):
                usable[url]=variant
    # The default edition follows the Squarespace capture era. Older platform
    # pages remain in the recovery/source catalog and are built separately.
    min_reference_capture=SQUARESPACE_START
    selected_page_ids={
        identity(r['_source_url']) for url,r in usable_variants.items()
        if r['kind']=='html' and eligible_site_page_capture(r['_source_url'],r,min_reference_capture)
        or r['kind']=='html' and urlsplit(r['_source_url']).hostname=='02cd02a.netsolhost.com'
    }
    selected_page_ids.update(identity(r.get('final_original','')) for r in usable_variants.values()
                              if r['kind']=='html' and r.get('final_original'))
    selected_page_ids.update(explicit_page_ids)
    # Discover destination stubs only from pages selected into this edition.
    record_by_identity={}
    for key,value in records.items():
        record_by_identity.setdefault(identity(value.get('url',key)),key)
    usable_variant_by_identity={}
    for variant in usable_variants.values():
        key=identity(variant['_source_url'])
        previous=usable_variant_by_identity.get(key)
        if previous is None or variant.get('actual_capture','')>previous.get('actual_capture',''):
            usable_variant_by_identity[key]=variant
    lj_pages=[(key,r) for key,r in usable_variants.items()
              if r['kind']=='html' and urlsplit(r['_source_url']).hostname=='bluescholars.livejournal.com']
    linked_html_routes=[];linked_lj_routes=[]
    for source_key,r in list(usable_variants.items()):
        url=r['_source_url']
        if r['kind']=='html' and identity(url) in selected_page_ids:
            source_prefix=edition_prefix(url,r)
            for ref in discover_html(raw[source_key].decode('utf-8',errors='replace'),r.get('final_original',url)):
                discovered=dict(ref);referrer=discovered.pop('referrer','')
                if discovered.get('kind')=='html':
                    lj_target=livejournal_route(discovered['url'])
                    if lj_target and lj_target.startswith(('/lj/posts/','/lj/comments/')):
                        linked_lj_routes.append(discovered['url'])
                    elif not urlsplit(discovered['url']).hostname=='bluescholars.livejournal.com':
                        destination_id=identity(discovered['url'])
                        destination_record=usable_variant_by_identity.get(destination_id)
                        discovered_record=destination_record or records.get(discovered['url'],{})
                        linked_html_routes.append((historical_route_prefix(
                            discovered['url'],source_prefix,route_capture_hint(discovered_record)),
                            discovered['url']))
                discovered.update(status='queued',referrers=[referrer] if referrer else [],edition_prefixes=[source_prefix])
                target_id=identity(ref['url'])
                existing_key=record_by_identity.get(target_id)
                if existing_key is None:
                    records[ref['url']]=discovered
                    record_by_identity[target_id]=ref['url']
                else:
                    existing=records[existing_key]
                    existing.setdefault('referrers',[])
                    if referrer and referrer not in existing['referrers']:
                        existing['referrers'].append(referrer)
                    existing.setdefault('edition_prefixes',[])
                    if source_prefix not in existing['edition_prefixes']:
                        existing['edition_prefixes'].append(source_prefix)
    # Feed bodies are source material too. Their internal links should reach
    # recovered pages where available, and honest local gap pages otherwise.
    # The source catalog in a clean checkout does not contain the resumable
    # discovery state, so collect these links directly from the preserved XML.
    for source_url,entry in feed_entries.items():
        source_prefix=historical_route_prefix(source_url,'/2009',entry['feed_capture']) or '/2009'
        for discovered in discover_html(entry['content'],source_url):
            linked_url=discovered.get('url','')
            if discovered.get('kind')!='html' or not is_site(linked_url):
                continue
            prefix=historical_route_prefix(
                linked_url,source_prefix,route_capture_hint(records.get(linked_url,{}))) or source_prefix
            linked_html_routes.append((prefix,linked_url))
    # LiveJournal itself is outside the three official editions above, but its
    # own post captures can link to comment-thread URLs that need local gap pages.
    for key,r in lj_pages:
        for ref in discover_html(raw[key].decode('utf-8',errors='replace'),r.get('final_original',r['_source_url'])):
            if ref.get('kind')!='html': continue
            lj_target=livejournal_route(ref['url'])
            if lj_target and lj_target.startswith('/lj/comments/'):
                linked_lj_routes.append(ref['url'])
    for url,r in usable.items():
        if r['kind'] in ('css','image'):
            if r['kind']=='css':
                local=('/assets/'+r['sha256']+'.css') if r.get('source_archive') else asset_route(url,'css')
            else: local='/assets/'+r['sha256']+Path(r['raw_path']).suffix
            r['local_path']=local
    # LiveJournal was a separately hosted Blue Scholars blog, not one of the
    # three official site editions. Keep its captures in their own /lj/ tree.
    lj_route_by_key={}
    newest_by_url={}
    for key,r in lj_pages:
        url=r['_source_url'];path=urlsplit(url).path;url_id=identity(url)
        current=newest_by_url.get(url_id)
        if current is None or r.get('actual_capture','')>current.get('actual_capture',''):
            newest_by_url[url_id]=r
    for key,r in lj_pages:
        url=r['_source_url'];path=urlsplit(url).path;is_latest=newest_by_url[identity(url)] is r
        if path in ('','/'):
            local='/lj/journal/' if is_latest else '/lj/captures/'+r.get('actual_capture','unknown')+'/'
        elif path=='/profile': local='/lj/profile/'
        else:
            post_route=livejournal_route(url) or '/lj/posts/'+path.rsplit('/',1)[-1]
            post_path=post_route.removeprefix('/lj')
            if is_latest: local='/lj'+post_path
            else: local='/lj/captures/'+r.get('actual_capture','unknown')+post_path
        lj_route_by_key[key]=local
    # Resolver URLs use source URLs, while variant records retain exact capture
    # provenance. Map each canonical LiveJournal URL to its latest recovered
    # local copy so links among captures never return to the hosted service.
    for url,r in newest_by_url.items():
        r['local_path']=lj_route_by_key[r['_source_key']]
    for url,r in usable.items():
        host=urlsplit(url).hostname or ''
        if r['kind']=='image' and (host.endswith('livejournal.com') or host.endswith('masslinemedia.com')):
            r['local_path']='/lj/assets/'+r['sha256']+Path(r['raw_path']).suffix
    # Keep dated WordPress source URLs resolvable even when the same original
    # URL was indexed/recovered as a capture variant. The common resolver uses
    # the canonical mapping for references inside old posts.
    for key,r in usable_variants.items():
        if r['kind'] in ('css','image'):
            canonical=r['_source_url']
            selected=usable.get(canonical)
            if selected and selected.get('local_path'):
                r['local_path']=selected['local_path']
    render_resources={}
    for key,r in records.items():
        original=r.get('url',key)
        if is_site(original):render_resources.setdefault(original,r)
    render_resources.update(usable)
    aliases=resource_aliases(render_resources)
    compatibility_aliases,alias_issues=documented_asset_aliases(root,usable_variants)
    for key,record in compatibility_aliases.items():
        if key not in aliases or not aliases[key].get('local_path'):
            aliases[key]=record
    issues.extend(alias_issues)
    pages={}
    for source_key,r in records.items():
        source_url=r.get('url',source_key)
        if r['kind']!='html' or not is_site(source_url): continue
        url=r.get('final_original') if is_site(r.get('final_original','')) else source_url
        def selected_referrer(ref):
            if not ref or ref.startswith('CDX:'):
                return False
            if identity(ref) in selected_page_ids:
                return True
            return (ref.startswith('feed:') and ' -> ' in ref and
                    identity(ref.rsplit(' -> ',1)[1]) in feed_entry_ids)
        sourced_by_selected_page=any(selected_referrer(ref) for ref in r.get('referrers',[]) if ref)
        capture=r.get('actual_capture','')
        selected_capture=bool(r.get('raw_path') and r.get('status')=='recovered'
                              and (eligible_site_page_capture(source_url,r,min_reference_capture)
                                   or urlsplit(source_url).hostname=='02cd02a.netsolhost.com'))
        if identity(url) in explicit_page_ids and r.get('raw_path') and not selected_capture:
            continue
        if identity(url) not in explicit_page_ids and not selected_capture and not sourced_by_selected_page:
            continue
        try:
            prefixes={edition_prefix(source_url,r)}
            if not r.get('raw_path') and r.get('edition_prefixes'):
                prefixes.update(r['edition_prefixes'])
            for prefix in prefixes:
                page=prefix+route(url)
                previous=pages.get(page)
                if previous is None or (source_key in usable_variants, r.get('actual_capture',''))>(previous.get('_source_key') in usable_variants,previous.get('actual_capture','')):
                    pages[page]=dict(r,url=url,source_url=source_url,edition_prefix=prefix,_source_key=source_key)
        except ValueError:
            issues.append({'type':'unsafe_route','url':url});continue
    # A saved WordPress feed can preserve an article body even when no original
    # HTML response survives. Keep it visibly distinct and never replace a
    # successfully recovered page capture with feed content.
    for source_url,entry in feed_entries.items():
        prefix=historical_route_prefix(source_url,'/2009',entry['feed_capture']) or '/2009'
        page=prefix+route(source_url)
        previous=pages.get(page)
        if previous and previous.get('_source_key') in usable_variants:
            continue
        pages[page]={'url':source_url,'source_url':source_url,'edition_prefix':prefix,
                     '_feed_entry':entry,'actual_capture':entry['feed_capture'],
                     'source_archive':'Internet Archive Wayback'}
    if release:
        if '/2013/' not in pages or pages['/2013/'].get('_source_key') not in usable_variants or not any(r['kind']=='css' for r in usable.values()):
            raise ValueError('Publication review cannot substitute for missing homepage HTML/CSS')
    if output.exists(): shutil.rmtree(output)
    (output/'assets').mkdir(parents=True)
    ui=root/'public/archive-ui.css'
    ui_text=ui.read_text() if ui.exists() else FALLBACK_UI
    ui_href=base+'/assets/archive-ui.css?v='+hashlib.sha256(ui_text.encode()).hexdigest()[:16]
    (output/'assets/archive-ui.css').write_text(ui_text)
    timeline_script=root/'public/archive-timeline.js'
    timeline_script_text=timeline_script.read_text(encoding='utf-8') if timeline_script.is_file() else ''
    timeline_script_href=(base+'/assets/archive-timeline.js?v='+hashlib.sha256(timeline_script_text.encode()).hexdigest()[:16]) if timeline_script_text else ''
    if timeline_script_text: (output/'assets/archive-timeline.js').write_text(timeline_script_text,encoding='utf-8')
    # Generated, fixed destinations only. Unknown offsets stay visible rather than guessed.
    from .urls import PAGINATION
    mappings={offset:base+'/2013'+path for offset,path in PAGINATION.items() if '/2013'+path in pages}
    script='''"use strict"; (() => {\n const mapping = MAPPING;\n const params = new URLSearchParams(location.search);\n const offset = params.get("offset");\n if (location.pathname.replace(/\\/$/, "") === BLOG && [...params].length === 1 && offset && mapping[offset]) {\n  location.replace(mapping[offset] + location.hash);\n }\n if (typeof document !== "undefined") {\n const menu = document.querySelector("#mobileMenuLink a[aria-controls='mobileNav']");\n const mobileNav = document.getElementById("mobileNav");\n if (menu && mobileNav) {\n  const setOpen = open => { document.body.classList.toggle("archive-menu-open", open); menu.setAttribute("aria-expanded", String(open)); };\n  menu.addEventListener("click", event => { event.preventDefault(); setOpen(menu.getAttribute("aria-expanded") !== "true"); });\n  menu.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); menu.click(); } });\n  mobileNav.addEventListener("click", event => { if (event.target.closest("a")) setOpen(false); });\n }\n }\n})();\n'''.replace('MAPPING',json.dumps(mappings)).replace('BLOG',json.dumps(base+'/2013/blog'))
    (output/'assets/legacy.js').write_text(script)
    script_href=base+'/assets/legacy.js?v='+hashlib.sha256(script.encode()).hexdigest()[:16]
    for url,r in usable.items():
        if r['kind'] not in ('css','image'): continue
        destination=output/r['local_path'].lstrip('/')
        if r['kind']=='css':
            source_key=r.get('_source_key',url)
            text,found=render_css(raw[source_key].decode('utf-8',errors='replace'),r.get('final_original',url),render_resources,base,aliases)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(text);issues.extend(found)
        else:
            source_key=r.get('_source_key',url)
            destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.suffix=='.svg':
                destination.write_bytes(sanitize_svg(raw[source_key]))
            else:
                destination.write_bytes(raw[source_key])
    for r in {record['_source_key']:record for record in compatibility_aliases.values()}.values():
        destination=output/r['local_path'].lstrip('/')
        if destination.exists():continue
        destination.parent.mkdir(parents=True,exist_ok=True)
        source_key=r['_source_key']
        if r.get('kind')=='css':
            text,found=render_css(raw[source_key].decode('utf-8',errors='replace'),
                                  r.get('final_original',r.get('_source_url',source_key)),
                                  render_resources,base,aliases)
            destination.write_text(text);issues.extend(found)
        elif destination.suffix=='.svg':destination.write_bytes(sanitize_svg(raw[source_key]))
        else:destination.write_bytes(raw[source_key])
    recovered=0;placeholders=0;feed_recovered=0;page_report=[]
    for page,r in sorted(pages.items()):
        url=r['url']
        source_key=r.get('_source_key',url)
        if r.get('_feed_entry'):
            entry=r['_feed_entry']
            title=entry.get('title') or urlsplit(url).path.strip('/').rsplit('/',1)[-1].replace('-',' ').title()
            feed_source=entry['feed_replay_url']
            content_label='Full article text' if entry['content_type']=='full' else 'Feed description; an excerpt'
            banner=('<aside class="archive-feed-provenance"><strong>'+content_label+'</strong> captured in an archived WordPress feed on '
                    +html.escape(entry['feed_capture'])+'. The original page HTML was not recovered. '
                    '<a class="archive-source-link" href="'+html.escape(feed_source,quote=True)+'">Inspect this feed capture</a>.</aside>')
            text=page_shell(title,banner+'<article class="archive-feed-article">'+entry['content']+'</article>')
            status='recovered_from_feed';feed_recovered+=1
        elif source_key in usable_variants:
            text=raw[source_key].decode('utf-8',errors='replace');recovered+=1;status='recovered'
        else:
            placeholders+=1;status='not_recovered'
            label=dict(CORE).get(page,page.strip('/') or 'Homepage')
            body='<p class="archive-lead">Page not recovered locally yet.</p><p>This is a recovery placeholder, not a recreation of the original design. The original HTML, styles and images must be recovered before visual fidelity can be assessed.</p>'
            if page=='/shop/': body+='<p>The historical shop is read-only. No checkout or purchasing is enabled.</p>'
            if page=='/shows/': body+='<p>Any recovered show listings will retain their historical dates.</p>'
            if page=='/holler/': body+='<p>Historical contact details will not be presented as current.</p>'
            if page=='/video/':
                videos=inventory.get('video_embeds',inventory.get('videos',[]))
                if videos:
                    body+='<h2>Previously observed embed references</h2><p>These are links, not recovered video files. Playback is unverified.</p><ol>'
                    for v in videos:
                        vid=v.get('youtube_id','')
                        import re
                        if not re.fullmatch('[A-Za-z0-9_-]{11}',vid): continue
                        label_v=v.get('title_from_archived_embed') or vid
                        body+='<li><a href="https://www.youtube.com/watch?v='+vid+'">'+html.escape(label_v)+'</a></li>'
                    body+='</ol>'
            body+='<p><a class="archive-source-link" href="https://web.archive.org/web/'+TARGET+'/'+html.escape(url,quote=True)+'">Inspect the archived source</a></p>'
            text=page_shell(label,body)
        rendered,found=render_html(text,r.get('final_original',url),render_resources,base,r.get('edition_prefix',''),aliases,ui_href,script_href)
        issues.extend(found);_write_page(output,page,rendered)
        page_report.append({'path':page,'source':r.get('source_url',url),'canonical_url':url,
                            'source_archive':r.get('source_archive'),'status':status,
                            'actual_capture':r.get('actual_capture'),
                            **({'feed_capture':r['_feed_entry']['feed_capture'],
                                'feed_source':r['_feed_entry']['feed_path'],
                                'feed_content_type':r['_feed_entry']['content_type']}
                               if r.get('_feed_entry') else {})})
    legacy_posts=[p for p in page_report if p['path'].startswith('/2009/blog/')
                  and p['path']!='/2009/blog/' and p['status']=='recovered']
    if legacy_posts:
        links=''.join('<li><a href="'+html.escape(p['path'],quote=True)+'">'
                      +html.escape(p['path'].strip('/').rsplit('/',1)[-1])+'</a></li>'
                      for p in sorted(legacy_posts,key=lambda p:p['path']))
        index=page_shell('Recovered 2009 WordPress posts',
                         '<p>This local index lists surviving dated WordPress captures. It is a recovery index, not an archived original listing.</p>'
                         '<ul>'+links+'</ul>')
        index,_=render_html(index,HOME,render_resources,base,aliases=aliases,ui_stylesheet=ui_href,ui_script=script_href)
        _write_page(output,'/2009/blog/',index)
    lj_page_report=[]
    for key,r in lj_pages:
        local=lj_route_by_key[key]
        text=raw[key].decode('utf-8',errors='replace')
        rendered,found=render_html(text,r.get('final_original',r['_source_url']),
                                   render_resources,base,'/lj',aliases,ui_href,script_href)
        issues.extend(found)
        _write_page(output,local,rendered)
        lj_page_report.append({'path':local,'source':r['_source_url'],
                               'actual_capture':r.get('actual_capture'),
                               'source_archive':r.get('source_archive'),'status':'recovered'})
    if lj_page_report:
        from datetime import datetime
        labels={'/lj/journal/':'Journal front page (February 2018)',
                '/lj/profile/':'LiveJournal profile',
                '/lj/posts/16954.html':'“friday mixdown” · Sep 30, 2007',
                '/lj/posts/17222.html':'“The Program” · Oct 4, 2007',
                '/lj/captures/20110812180628/':'Journal front page (August 2011)',
                '/lj/captures/20100209202330/':'Journal front page (Common Crawl, 2010)',
                '/lj/captures/20090125012333/posts/16954.html':'“friday mixdown” · 2009 capture',
                '/lj/captures/20110812180252/posts/17222.html':'“The Program” · August 2011 capture'}
        capture_items=[]
        for p in sorted(lj_page_report,key=lambda x:x['path']):
            stamp=p.get('actual_capture') or ''
            try: date=datetime.strptime(stamp,'%Y%m%d%H%M%S').strftime('%b %d, %Y').replace(' 0',' ')
            except ValueError: date='date unavailable'
            label=labels.get(p['path'])
            if not label:
                source=next((raw[key].decode('utf-8',errors='replace') for key,r in lj_pages
                             if lj_route_by_key.get(key)==p['path']), '')
                source_soup=BeautifulSoup(source,'html.parser')
                subject=source_soup.select_one('.entrysubject a.subj-link, .entrysubject a, .entrysubject')
                title=' '.join(subject.get_text(' ',strip=True).split()) if subject else ''
                if not title or title.lower()=='bluescholars':
                    title_node=source_soup.title
                    title=' '.join(title_node.get_text(' ',strip=True).split()) if title_node else ''
                    if ':' in title: title=title.split(':',1)[1].strip()
                    if title.lower()=='bluescholars': title=''
                path=p['path']
                if '/comments/' in path:
                    parts=path.strip('/').split('/')
                    label='Comments on '+parts[-2]+' · thread '+parts[-1]
                elif path.endswith('/calendar'):
                    label='Journal calendar'
                elif path.endswith('/profile/'):
                    label='LiveJournal profile'
                elif path.endswith('/journal/') or (path.startswith('/lj/captures/') and path.endswith('/')):
                    label='Journal front page'
                else:
                    label=title or ('Journal entry '+path.rsplit('/',1)[-1] if path.endswith('.html') else 'LiveJournal page')
            capture_items.append('<li><a href="'+base+html.escape(p['path'],quote=True)+'">'
                                 +html.escape(label)+'</a> — captured '+html.escape(date)+'</li>')
        capture_links=''.join(capture_items)
        lj_body='<p>A separately hosted Blue Scholars journal. These pages are reproduced from locally saved archive captures; they are not part of the 2007, 2009, or Squarespace website editions.</p>'
        if lj_page_report:
            lj_body+='<h2>Recovered journal captures</h2><ul>'+capture_links+'</ul>'
            lj_body+='<p>Some older entries survive only within the captured journal front page. Missing images and uncaptured entries are left marked rather than recreated.</p>'
        else:
            lj_body+='<p>No LiveJournal page captures have been recovered into this build yet.</p>'
        lj_index=page_shell('LiveJournal archive',lj_body)
        lj_index=lj_index.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'"></head>')
        _write_page(output,'/lj/',lj_index)
        page_report.extend({'path':p['path'],'source':p['source'],'canonical_url':p['source'],
                            'source_archive':p['source_archive'],'status':'recovered',
                            'actual_capture':p['actual_capture']} for p in lj_page_report)
        recovered+=len(lj_page_report)
    else:
        lj_index=page_shell('LiveJournal archive','<p>A separately hosted Blue Scholars journal, preserved separately from the official website editions.</p><p>No LiveJournal page captures have been recovered into this build yet.</p>')
        lj_index=lj_index.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'"></head>')
        _write_page(output,'/lj/',lj_index)
    # The 2007 site's News page is an image-map shell that linked readers to
    # LiveJournal. Surface the original 2007 entries that survive in that
    # separately captured journal, and link to their full local transcriptions.
    recovered_2007_posts=[]
    journal_root=newest_by_url.get(identity('http://bluescholars.livejournal.com/'))
    if journal_root:
        journal_soup=BeautifulSoup(raw[journal_root['_source_key']],'html.parser')
        for entry in journal_soup.select('div.entry'):
            date_node=entry.select_one('.entrytimestampdate')
            subject=entry.select_one('a.subj-link, .entrysubject a')
            content=entry.select_one('.entrycontent, .entrytext')
            if not date_node or not subject or not content: continue
            published=' '.join(date_node.get_text(' ',strip=True).split())
            if not (published.endswith('/07') or '2007' in published): continue
            target=original_url(subject.get('href',''),journal_root.get('final_original','http://bluescholars.livejournal.com/'))
            local=livejournal_route(target or '')
            if not local or not local.startswith('/lj/posts/'): continue
            title=' '.join(subject.get_text(' ',strip=True).split())
            excerpt=' '.join(content.get_text(' ',strip=True).split())
            if len(excerpt)>360: excerpt=excerpt[:357].rsplit(' ',1)[0]+'…'
            if not excerpt: continue
            capture=journal_root.get('actual_capture','')
            try:
                from datetime import datetime
                capture_label=datetime.strptime(capture,'%Y%m%d%H%M%S').strftime('%b %d, %Y').replace(' 0',' ')
            except ValueError: capture_label='date unavailable'
            recovered_2007_posts.append((published,title,excerpt,capture,local,capture_label))
    # Some older posts fell off LiveJournal's six-entry front page. Add any
    # independently preserved 2007 permalink that is not already represented.
    known_post_routes={entry[4] for entry in recovered_2007_posts}
    for url,record in newest_by_url.items():
        parts=urlsplit(url)
        if parts.query or not parts.path.endswith('.html'):
            continue
        local=livejournal_route(record['_source_url'])
        if not local or local in known_post_routes:
            continue
        post_soup=BeautifulSoup(raw[record['_source_key']],'html.parser')
        entry=post_soup.select_one('div.entry')
        if not entry:
            continue
        date_node=entry.select_one('.entrytimestampdate')
        subject=entry.select_one('h3.entrysubject a.subj-link, .entrysubject a')
        content=entry.select_one('.entrycontent, .entrytext')
        if not date_node or not subject or not content:
            continue
        published=' '.join(date_node.get_text(' ',strip=True).split())
        if not (published.endswith('/07') or '2007' in published):
            continue
        title=' '.join(subject.get_text(' ',strip=True).split())
        excerpt=' '.join(content.get_text(' ',strip=True).split())
        if len(excerpt)>360: excerpt=excerpt[:357].rsplit(' ',1)[0]+'…'
        if not excerpt: continue
        capture=record.get('actual_capture','')
        try:
            from datetime import datetime
            capture_label=datetime.strptime(capture,'%Y%m%d%H%M%S').strftime('%b %d, %Y').replace(' 0',' ')
        except ValueError: capture_label='date unavailable'
        recovered_2007_posts.append((published,title,excerpt,capture,local,capture_label))
        known_post_routes.add(local)
    news_path=output/'2007/news.html'
    if recovered_2007_posts and news_path.is_file():
        news_page=BeautifulSoup(news_path.read_text(encoding='utf-8'),'html.parser')
        section=news_page.new_tag('section',attrs={'class':'recovered-news','aria-label':'Recovered 2007 news entries'})
        heading=news_page.new_tag('h2');heading.string='News from the Blue Scholars journal'
        section.append(heading)
        intro=news_page.new_tag('p')
        intro.string=('The archived News page linked to LiveJournal. These 2007 entries survive in separately archived '
                      'LiveJournal front-page and individual post captures; open each local entry for the text preserved in its dated source.')
        section.append(intro)
        for published,title,excerpt,capture,local,capture_label in recovered_2007_posts:
            article=news_page.new_tag('article',attrs={'class':'recovered-news-entry'})
            h3=news_page.new_tag('h3')
            link=news_page.new_tag('a',href=base+local);link.string=title
            h3.append(link);article.append(h3)
            date=news_page.new_tag('p',attrs={'class':'recovered-news-date'})
            date.string=published+' · surviving capture: '+capture_label
            article.append(date)
            summary=news_page.new_tag('p');summary.string=excerpt;article.append(summary)
            section.append(article)
        container=news_page.select_one('td.body1') or news_page.body
        container.insert(0,section)
        style=news_page.new_tag('style',attrs={'type':'text/css'})
        style.string=('.recovered-news{margin:24px auto;max-width:760px;padding:18px 24px;border-top:1px solid #9bb7c8;'
                      'border-bottom:1px solid #9bb7c8;color:#333300;font:14px/1.55 Arial,sans-serif}'
                      '.recovered-news h2{font-size:20px;margin:0 0 10px}.recovered-news-entry{padding:12px 0;'
                      'border-top:1px solid #d7dfe3}.recovered-news-entry h3{font-size:17px;margin:0}'
                      '.recovered-news-entry p{margin:6px 0}.recovered-news-date{font-size:11px;color:#666}')
        news_page.head.append(style)
        news_path.write_text(str(news_page),encoding='utf-8')
    route_notices=[]
    reported_paths={p['path'] for p in page_report}
    recovered_by_identity={}
    for p in page_report:
        canonical=p.get('canonical_url','')
        if canonical and p['status']=='recovered':
            recovered_by_identity.setdefault(identity(canonical),p['path'])
    for prefix,target_url in linked_html_routes:
        try: target_path=prefix+route(target_url)
        except ValueError: continue
        if target_path in pages or target_path in reported_paths: continue
        target_id=identity(target_url)
        edition_path=recovered_by_identity.get(target_id)
        if edition_path:
            body=('<p>This destination has source bytes in a different historical edition. '
                  'To keep the original generations separate, its recovered page is here:</p>'
                  '<p><a href="'+base+html.escape(edition_path,quote=True)+'">Open the recovered edition copy</a></p>')
            status='edition_bridge'
        else:
            body=('<p>This linked page has not been recovered for this edition. '
                  'No historical page content has been invented.</p>'
                  '<p><a href="'+base+'/archive-status/">View the recovery inventory</a></p>')
            status='not_recovered'
        notice=page_shell('Historical link not recovered',body)
        notice=notice.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'"></head>')
        _write_page(output,target_path,notice)
        page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                            'source_archive':None,'status':status,'actual_capture':None})
        reported_paths.add(target_path)
        route_notices.append({'path':target_path,'status':status})
    for target_url in linked_lj_routes:
        target_path=livejournal_route(target_url)
        if not target_path or target_path in reported_paths or target_path in pages:
            continue
        if target_path.startswith('/lj/comments/'):
            parent_url=target_url.partition('?')[0]
            parent_path=livejournal_route(parent_url)
            body=('<p>This comment thread was linked from a recovered LiveJournal post, but the comment thread was not '
                  'recovered from the available archive captures.</p>'
                  '<p><a href="'+base+html.escape(parent_path or '/lj/',quote=True)+'">Open the locally archived post</a></p>')
            notice=page_shell('LiveJournal comment thread not recovered',body)
            notice=notice.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'"></head>')
            _write_page(output,target_path,notice)
            page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                                'source_archive':None,'status':'not_recovered','actual_capture':None})
            reported_paths.add(target_path)
            route_notices.append({'path':target_path,'status':'not_recovered'})
            continue
        root_url='http://bluescholars.livejournal.com/'
        root_record=newest_by_url.get(identity(root_url))
        extracted_entry=None;root_soup=None
        if root_record:
            root_soup=BeautifulSoup(raw[root_record['_source_key']],'html.parser')
            for anchor in root_soup.find_all('a',href=True):
                href=original_url(anchor['href'],root_record.get('final_original',root_url))
                if href and identity(href)==identity(target_url):
                    extracted_entry=anchor.find_parent('div',class_='entry')
                    if extracted_entry:
                        break
        if extracted_entry:
            title=(root_soup.find('a',href=lambda href: href and identity(original_url(href,root_url))==identity(target_url))
                   .get_text(' ',strip=True))
            source_capture=root_record.get('actual_capture','unknown')
            note=('<p class="archive-source-note">This article view is extracted from the full-text entry on the '
                  +html.escape(source_capture)+' LiveJournal front-page capture. A separate standalone post response was not found. '
                  'The saved front page contains the article text shown here; a complete standalone comment thread is unavailable.</p>'
                  '<p><a href="'+root_url+'">Open the captured LiveJournal front page</a></p>')
            derived=page_shell(title,note+str(extracted_entry))
            styles=''
            for link in root_soup.find_all('link',href=True):
                rel=link.get('rel',[])
                href=original_url(link['href'],root_record.get('final_original',root_url))
                if 'stylesheet' in rel and href and '/res/' in urlsplit(href).path:
                    styles='<link rel="stylesheet" href="'+html.escape(href,quote=True)+'">'
                    break
            derived=derived.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'">'+styles+'</head>')
            rendered,found=render_html(derived,root_record.get('final_original',root_url),render_resources,base,'/lj',ui_stylesheet=ui_href,ui_script=script_href)
            issues.extend(found);_write_page(output,target_path,rendered)
            page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                                'source_archive':root_record.get('source_archive'),
                                'status':'derived_from_capture','actual_capture':source_capture,
                                'derived_from':root_url})
            reported_paths.add(target_path)
            continue
        body=('<p>This entry has not been recovered as a standalone page. It may still appear within a saved journal front-page capture:</p>'
              '<p><a href="'+base+'/lj/journal/">Open the recovered LiveJournal front page</a></p>')
        notice=page_shell('LiveJournal entry not recovered',body)
        notice=notice.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'"></head>')
        _write_page(output,target_path,notice)
        page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                            'source_archive':None,'status':'not_recovered','actual_capture':None})
        reported_paths.add(target_path)
        route_notices.append({'path':target_path,'status':'not_recovered'})
    placeholders+=len(route_notices)
    # Make every full or front-page-derived LiveJournal entry directly
    # discoverable from /lj/, while keeping the capture basis explicit.
    lj_index_path=output/'lj/index.html'
    lj_entries=[p for p in page_report if p['path'].startswith('/lj/posts/') and p['path'].endswith('.html')
                and p['status'] in ('recovered','derived_from_capture')]
    lj_comment_threads=[p for p in page_report if p['path'].startswith('/lj/comments/')
                        and p['status'] in ('recovered','not_recovered')]
    if lj_index_path.is_file() and (lj_entries or lj_comment_threads):
        lj_index_page=BeautifulSoup(lj_index_path.read_text(encoding='utf-8'),'html.parser')
        def make_lj_list(entries,css_class,basis):
            result=lj_index_page.new_tag('ul',attrs={'class':css_class})
            for entry in sorted(entries,key=lambda p:p['path']):
                entry_file=output/entry['path'].lstrip('/')
                if entry_file.is_dir(): entry_file=entry_file/'index.html'
                if not entry_file.is_file(): continue
                entry_soup=BeautifulSoup(entry_file.read_text(encoding='utf-8'),'html.parser')
                heading=(entry_soup.select_one('.entrysubject a.subj-link, .entrysubject a, .entrysubject')
                         or entry_soup.find('h1'))
                title=heading.get_text(' ',strip=True) if heading else ''
                if title.lower()=='bluescholars': title=''
                if not title:
                    title_node=entry_soup.find('title')
                    title=title_node.get_text(' ',strip=True) if title_node else ''
                    if ':' in title: title=title.split(':',1)[1].strip()
                if not title: title=Path(entry['path']).stem
                item=lj_index_page.new_tag('li')
                link=lj_index_page.new_tag('a',href=base+entry['path']);link.string=title
                item.append(link);item.append(' — '+basis(entry))
                result.append(item)
            return result
        if lj_entries:
            entry_list=make_lj_list(lj_entries,'recovered-journal-entries',
                lambda entry:('full archived post' if entry['status']=='recovered'
                              else 'text preserved in captured journal front page'))
            heading=lj_index_page.new_tag('h2');heading.string='Recovered journal entries'
            lj_index_page.main.append(heading);lj_index_page.main.append(entry_list)
        if lj_comment_threads:
            thread_list=make_lj_list(lj_comment_threads,'recovered-comment-threads',
                lambda entry:('captured comment-thread view · '+entry.get('actual_capture','date unavailable')
                              if entry['status']=='recovered' else 'comment thread not recovered'))
            heading=lj_index_page.new_tag('h2');heading.string='Archived comment threads'
            lj_index_page.main.append(heading);lj_index_page.main.append(thread_list)
        if lj_entries or lj_comment_threads:
            lj_index_path.write_text(str(lj_index_page),encoding='utf-8')
    # Keep the descriptive index as a browseable archive, while making the
    # latest recovered LiveJournal front page the default /lj/ destination.
    if lj_index_path.is_file():
        lj_archive_path=output/'lj/archive/index.html'
        lj_archive_path.parent.mkdir(parents=True,exist_ok=True)
        lj_archive_page=BeautifulSoup(lj_index_path.read_text(encoding='utf-8'),'html.parser')
        latest_link=lj_archive_page.new_tag('a',href=base+'/lj/')
        latest_link.string='Open the latest recovered journal front page'
        latest_note=lj_archive_page.new_tag('p');latest_note.append(latest_link)
        if lj_archive_page.main: lj_archive_page.main.insert(1,latest_note)
        else: lj_archive_page.body.insert(0,latest_note)
        lj_archive_path.write_text(str(lj_archive_page),encoding='utf-8')
        latest_journal_path=output/'lj/journal/index.html'
        if latest_journal_path.is_file():
            latest_journal=BeautifulSoup(latest_journal_path.read_text(encoding='utf-8'),'html.parser')
            archive_label='LIVEJOURNAL ARCHIVE'
            for link in latest_journal.select('.archive-navigation a'):
                if link.get_text(' ',strip=True).upper()==archive_label:
                    link['href']=base+'/lj/archive/'
            journal_root=newest_by_url.get(identity('http://bluescholars.livejournal.com/'))
            stamp=(journal_root or {}).get('actual_capture','')
            capture_date=(stamp[:4]+'-'+stamp[4:6]+'-'+stamp[6:8]) if len(stamp)>=8 else 'date unavailable'
            capture_note=latest_journal.new_tag('aside',attrs={'class':'lj-current-capture'})
            capture_note.string='Latest recovered journal front page · captured '+capture_date+' · '
            archive_link=latest_journal.new_tag('a',href=base+'/lj/archive/')
            archive_link.string='browse all saved posts and dated captures'
            capture_note.append(archive_link)
            latest_journal.head.append(latest_journal.new_tag('style'))
            latest_journal.head.find_all('style')[-1].string=(
                '.lj-current-capture{box-sizing:border-box;margin:0;padding:9px 14px;background:#eef3f5;'
                'color:#364657;font:12px/1.5 system-ui,sans-serif}.lj-current-capture a{color:#24567d}')
            notice=latest_journal.select_one('.archive-restoration-notice')
            if notice: notice.insert_after(capture_note)
            else: latest_journal.body.insert(0,capture_note)
            lj_index_path.write_text(str(latest_journal),encoding='utf-8')
    # Each platform generation gets its own index. Unrecovered editions are
    # documented as gaps instead of being filled with invented historical copy.
    for prefix,label in (('/2007','2007 site'),('/2009','2009 WordPress site'),
                         ('/2013','Squarespace site (first located in 2013)')):
        if prefix+'/' not in pages:
            selected=[p for p in page_report if p['path'].startswith(prefix+'/')]
            body='<p>This is a separate historical website generation. Pages below come from dated source captures.</p>'
            if selected:
                body+='<h2>Pages in this edition</h2><ul>'+''.join(
                    '<li><a href="'+html.escape(p['path'],quote=True)+'">'+html.escape(p['path'])+'</a> — '+html.escape(p['status'].replace('_',' '))+'</li>' for p in selected)+'</ul>'
            else:
                body+='<p>No page bytes for this edition have been recovered yet. Its original appearance and blog content remain a documented gap.</p>'
            edition_text=page_shell(label,body)
            edition_text,_=render_html(edition_text,HOME,render_resources,base,aliases=aliases,ui_stylesheet=ui_href,ui_script=script_href)
            _write_page(output,prefix+'/',edition_text)
    gateway='<p class="archive-home-intro">Move through the years. Archives appear below only when a dated source shows they existed.</p><section class="archive-timeline archive-year-global" data-base-path="'+html.escape(base,quote=True)+'" aria-labelledby="archive-year-label"><a class="archive-year-global-brand" href="'+html.escape(base+'/',quote=True)+'">Blue Scholars archive</a><label id="archive-year-label" for="archive-year">Explore a year</label><div class="archive-year-readout"><output id="archive-year-output" for="archive-year">2007</output><span id="archive-era-summary">The earliest preserved site era</span></div><input id="archive-year" class="archive-year-global-control" data-default-year="2007" type="range" min="2006" max="2026" step="1" value="2007" aria-label="Select archive year" aria-valuetext="2007"><div class="archive-year-markers" aria-hidden="true"><span>2006</span><span>2010</span><span>2015</span><span>2020</span><span>2026</span></div><a class="archive-year-home" href="'+base+'/2007/?year=2007">Open 2007 homepage</a></section><p id="archive-year-count" class="archive-year-count" aria-live="polite"></p><nav class="archive-site-grid archive-timeline-results" data-year="2007" aria-label="Archives available in the selected year">'
    editions=(('/2007/','2007','Independent site'),('/2009/','2009','WordPress site'),('/2013/','2013','Squarespace site · first located in 2013'))
    for path,year,label in editions:
        bounds=archive_availability(root,path)
        if bounds:
            gateway+='<a class="archive-site-card timeline-edition-card" data-start-year="'+str(bounds[0])+'" data-end-year="'+str(bounds[1])+'" href="'+base+path+'"><span class="archive-site-title">'+year+' · '+html.escape(label)+'</span><span class="archive-site-detail">Separate Blue Scholars website edition · '+str(bounds[0])+('–'+str(bounds[1]) if bounds[1]!=bounds[0] else '')+'</span><span class="edition-action">Browse this edition <span aria-hidden="true">↗</span></span></a>'
    satellite_report=build_artist_sites(root,output,base,candidate)
    massline_report=build_massline_archive(root,output,base,candidate)
    myspace_report=build_myspace_archive(root,output,base)
    proof206_report=build_206proof_archive(root,output,base,candidate)
    twitter_report=build_twitter_archive(root,output,base)
    community_media_items=build_community_media(root,output,base,render_resources,aliases,ui_href,script_href)
    press_archive_report=build_press_archive(root,output,base,ui_href)
    gateway+='</nav><h2 class="archive-sites-heading">Other captured editions</h2><p class="archive-sites-intro">The slider follows capture dates: entries appear for years where preserved material exists. Select a year to browse.</p><nav class="archive-site-grid archive-timeline-results" data-year="2007" aria-label="Other archives available in the selected year">'
    related_sites=[
        ('/prometheusbrown/','Prometheus Brown','Artist site editions'),
        ('/sabzi/','Sabzi','Artist site editions'),
        ('/myspace/','Blue Scholars on MySpace','Dated profile captures'),
        ('/twitter-prometheusbrown/','Prometheus Brown on Twitter','Dated profile and tweet captures'),
    ]
    if massline_report.get('status')=='built':
        related_sites.append(('/masslinemedia/','Mass Line Media','Original site editions and captures'))
        related_sites.append(('/massline-forums/','Mass Line Forums','Separate SMF forum archive'))
    if proof206_report.get('status')=='built':
        related_sites.append(('/206proof/','206Proof forums','Separate historical forum generations'))
    if press_archive_report.get('status')=='built':
        related_sites.append(('/other-archives/press/','Press archive','Recovered articles, images, and audio'))
    related_sites.append(('/lj/','Blue Scholars LiveJournal','Recovered journal posts'))
    for path,title,detail in related_sites:
        extra=' lj-archive' if path=='/lj/' else ''
        bounds=archive_availability(root,path)
        if not bounds: continue
        start,end=bounds
        gateway+='<a class="archive-site-card timeline-related-card'+extra+'" data-start-year="'+str(start)+'" data-end-year="'+str(end)+'" href="'+base+path+'"><span class="archive-site-title">'+html.escape(title)+'</span><span class="archive-site-detail">'+html.escape(detail)+' · '+str(start)+('–'+str(end) if end!=start else '')+'</span><span class="edition-action">Browse archive <span aria-hidden="true">↗</span></span></a>'
    gateway+='</nav><nav class="archive-home-links" aria-label="Archive information">'
    if community_media_items:
        gateway+='<a href="'+base+'/community-media/">Supplemental community media <span aria-hidden="true">↗</span></a>'
    gateway+='<a class="recovery-status" href="'+base+'/archive-status/">Recovery status and source gaps <span aria-hidden="true">↗</span></a></nav>'
    hub=page_shell('Blue Scholars archive',gateway).replace('<main class="archive-gap-page">','<main class="archive-gap-page archive-home">')
    timeline_tag='<script src="'+timeline_script_href+'" defer></script>' if timeline_script_text else ''
    hub=hub.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+ui_href+'">'+timeline_tag+'</head>')
    _write_page(output,'/',hub)
    # Deduplicate identical findings without suppressing which page referenced a gap.
    issues=list({json.dumps(i,sort_keys=True):i for i in issues}.values())
    report={'mode':'unreviewed_candidate' if candidate else 'reviewed_source_build','base_path':base,
            'recovered_pages':recovered,'feed_recovered_pages':feed_recovered,
            'placeholder_pages':placeholders,
            'derived_pages':sum(p['status']=='derived_from_capture' for p in page_report),
            'local_source_assets':sum(r['kind'] in ('css','image') for r in usable.values()),
            'visual_fidelity_verified':bool(review.get('visual_reviewed')) and not candidate,
            'publish_approved':bool(review.get('publish_approved')) and not candidate,
            'pages':page_report,'issues':issues,'reference_capture':TARGET,'artist_sites':satellite_report,
            'myspace':myspace_report,'twitter':twitter_report,
            'community_media_items':community_media_items,
            'press_archive':press_archive_report,
            'massline':massline_report,
            '206proof':proof206_report,
            'note':'A successful build is not proof of source completeness or visual fidelity.'}
    stats=f'<p class="archive-lead">{recovered} recovered pages · {placeholders} recovery placeholders</p>'
    stats+='<p>The build is offline. It does not use Wayback or Squarespace to display its content. Original typography and layout still require visual review; the diagnostic styling is not the historical site design.</p>'
    stats+='<table><thead><tr><th>Page</th><th>Recovery status</th></tr></thead><tbody>'
    for p in page_report:
        stats+='<tr><td><a href="'+html.escape(p['path'],quote=True)+'">'+html.escape(p['path'])+'</a></td><td>'+html.escape(p['status'].replace('_',' '))+'</td></tr>'
    stats+='</tbody></table><h2>Recovery findings</h2>'
    if issues:
        stats+='<ul>'+''.join('<li>'+html.escape(i['type'].replace('_',' ')+': '+str(i.get('url',i.get('source',''))))+'</li>' for i in issues)+'</ul>'
    else: stats+='<p>No dependency findings in the generated content. This does not imply missing source files were recovered.</p>'
    # Diagnostic links enter the same single base-path rewrite as original links.
    status_text,_=render_html(page_shell('Recovery status',stats),HOME,render_resources,base,aliases=aliases,ui_stylesheet=ui_href,ui_script=script_href)
    _write_page(output,'/archive-status/',status_text)
    write_json(output/'archive-status/report.json',report)
    missing,_=render_html(page_shell('Page not recovered','<p>This historical page is not included in this restoration.</p><p><a href="/archive-status/">View the recovery inventory</a></p>'),HOME,render_resources,base,aliases=aliases,ui_stylesheet=ui_href,ui_script=script_href)
    (output/'404.html').write_text(missing)
    decorate_archive_pages(output,base,ui_href,timeline_script_href,page_report)
    (output/'.nojekyll').touch()
    return report
