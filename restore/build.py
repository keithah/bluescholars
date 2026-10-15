"""Deterministic static output; unreviewed downloads never enter a release build."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import shutil
from urllib.parse import unquote
from .archive import validate_payload
from .discover import discover_html
from .render import render_html,render_css,NAV
from .svg import sanitize_svg
from .state import State,write_json
from .urls import HOME,TARGET,identity,is_site,route,asset_route,base_path

CORE=[('/', 'Homepage'),('/blog/','Blog'),('/shows/','Shows'),('/video/','Video'),('/shop/','Shop'),('/holler/','Holler')]
FALLBACK_UI='''.archive-restoration-notice,.archive-gap-page {font:16px/1.6 system-ui,sans-serif}
.archive-restoration-notice{padding:12px;border-bottom:1px solid #ddd}.archive-navigation a{margin-right:16px}
.archive-gap-page{max-width:900px;margin:60px auto;padding:0 24px}.archive-missing-image{display:block;padding:30px;border:1px dashed #999}
.archive-gap-page a{overflow-wrap:anywhere}.archive-gap-page table{width:100%;border-collapse:collapse}.archive-gap-page td,.archive-gap-page th{padding:12px;text-align:left;border-bottom:1px solid #ddd}'''

def read_record(root: Path,r: dict,allow_recovery: bool) -> bytes:
    path=(root/r['raw_path']).resolve()
    allowed=[(root/'source/raw').resolve()]
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
    root=Path(root);state=State(root)
    catalog_path=root/'source/catalog.json'
    catalog=json.loads(catalog_path.read_text()) if catalog_path.exists() else {'version':1,'resources':{}}
    staged=[]
    # Verify all selected files before modifying the approved collection.
    for url,r in state.data['resources'].items():
        eligible=r['status']=='recovered' or (allow_later and r['status']=='needs_review')
        if eligible and r.get('raw_path') and r['kind'] in ('html','css','image'):
            staged.append((url,r,read_record(root,r,True)))
        elif url not in catalog['resources']:
            catalog['resources'][url]={k:v for k,v in r.items() if k not in ('raw_path','sha256')}
    for url,r,body in staged:
        copied=dict(r);path='source/raw/'+Path(r['raw_path']).name
        (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_bytes(body)
        copied.update(raw_path=path,source_reviewed=True,later_capture_approved=r['status']=='needs_review',status='recovered')
        catalog['resources'][url]=copied
    if staged:
        write_json(root/'source/review.json',{'publish_approved':False,'visual_reviewed':False,
                   'note':'Source collection changed; review the generated site before publishing.'})
    write_json(catalog_path,catalog)
    return {'promoted':len(staged),'publish_approved':False}

def page_shell(title: str,body: str) -> str:
    return '<!doctype html><html lang="en"><head><title>'+html.escape(title)+' — Blue Scholars restoration</title></head><body><main class="archive-gap-page"><p class="archive-eyebrow">BLUE SCHOLARS / RESTORATION WORKSPACE</p><h1>'+html.escape(title)+'</h1>'+body+'</main></body></html>'

def _write_page(output: Path,path: str,text: str):
    destination=output/unquote(path.lstrip('/'))/'index.html'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(text,encoding='utf-8')

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
    else:
        path=root/'source/catalog.json'
        catalog=json.loads(path.read_text()) if path.exists() else {'resources':{}}
        records=json.loads(json.dumps(catalog['resources']))
    inventory_path=root/'recovery/seeds/inventory.json'
    inventory=json.loads(inventory_path.read_text()) if inventory_path.exists() else {'pages':[]}
    for path,label in CORE:
        records.setdefault(HOME.rstrip('/')+path,{'url':HOME.rstrip('/')+path,'kind':'html','status':'queued'})
    for r in inventory.get('pages',[]):
        records.setdefault(r['original_url'],{'url':r['original_url'],'kind':'html','status':'queued'})
    usable={};raw={};issues=[]
    for url,r in records.items():
        if r.get('raw_path') and r.get('status')=='recovered' and r['kind'] in ('html','css','image'):
            raw[url]=read_record(root,r,candidate);usable[url]=r
    # Discover destination stubs before rewriting links, including links not reached by the crawler yet.
    for url,r in list(usable.items()):
        if r['kind']=='html':
            for ref in discover_html(raw[url].decode('utf-8',errors='replace'),r.get('final_original',url)):
                records.setdefault(ref['url'],dict(ref,status='queued'))
    for url,r in usable.items():
        if r['kind'] in ('css','image'):
            if r['kind']=='css': local=asset_route(url,'css')
            else: local='/assets/'+r['sha256']+Path(r['raw_path']).suffix
            r['local_path']=local
    pages={}
    for url,r in records.items():
        if r['kind']!='html' or not is_site(url): continue
        try: page=route(url)
        except ValueError:
            issues.append({'type':'unsafe_route','url':url});continue
        # Prefer verified bytes, then the closest pre-reference source date.
        previous=pages.get(page)
        if previous is None or (url in usable, r.get('actual_capture',''))>(previous['url'] in usable,previous.get('actual_capture','')):
            pages[page]=dict(r,url=url)
    if release:
        if '/' not in pages or pages['/']['url'] not in usable or not any(r['kind']=='css' for r in usable.values()):
            raise ValueError('Publication review cannot substitute for missing homepage HTML/CSS')
    if output.exists(): shutil.rmtree(output)
    (output/'assets').mkdir(parents=True)
    ui=root/'public/archive-ui.css'
    (output/'assets/archive-ui.css').write_text(ui.read_text() if ui.exists() else FALLBACK_UI)
    # Generated, fixed destinations only. Unknown offsets stay visible rather than guessed.
    from .urls import PAGINATION
    mappings={offset:base+path for offset,path in PAGINATION.items() if path in pages}
    script='''"use strict"; (() => {\n const mapping = MAPPING;\n const params = new URLSearchParams(location.search);\n const offset = params.get("offset");\n if (location.pathname.replace(/\\/$/, "") === BLOG && [...params].length === 1 && offset && mapping[offset]) {\n  location.replace(mapping[offset] + location.hash);\n }\n})();\n'''.replace('MAPPING',json.dumps(mappings)).replace('BLOG',json.dumps(base+'/blog'))
    (output/'assets/legacy.js').write_text(script)
    for url,r in usable.items():
        if r['kind'] not in ('css','image'): continue
        destination=output/r['local_path'].lstrip('/')
        if r['kind']=='css':
            text,found=render_css(raw[url].decode('utf-8',errors='replace'),r.get('final_original',url),usable,base)
            destination.write_text(text);issues.extend(found)
        elif destination.suffix=='.svg':
            destination.write_bytes(sanitize_svg(raw[url]))
        else: destination.write_bytes(raw[url])
    recovered=0;placeholders=0;page_report=[]
    for page,r in sorted(pages.items()):
        url=r['url']
        if url in usable:
            text=raw[url].decode('utf-8',errors='replace');recovered+=1;status='recovered'
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
        rendered,found=render_html(text,r.get('final_original',url),usable,base)
        issues.extend(found);_write_page(output,page,rendered)
        page_report.append({'path':page,'source':url,'status':status,'actual_capture':r.get('actual_capture')})
    # Deduplicate identical findings without suppressing which page referenced a gap.
    issues=list({json.dumps(i,sort_keys=True):i for i in issues}.values())
    report={'mode':'unreviewed_candidate' if candidate else 'reviewed_source_build','base_path':base,
            'recovered_pages':recovered,'placeholder_pages':placeholders,
            'local_source_assets':sum(r['kind'] in ('css','image') for r in usable.values()),
            'visual_fidelity_verified':bool(review.get('visual_reviewed')) and not candidate,
            'publish_approved':bool(review.get('publish_approved')) and not candidate,
            'pages':page_report,'issues':issues,'reference_capture':TARGET,
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
    status_text,_=render_html(page_shell('Recovery status',stats),HOME,usable,base)
    _write_page(output,'/archive-status/',status_text)
    write_json(output/'archive-status/report.json',report)
    missing,_=render_html(page_shell('Page not recovered','<p>This historical page is not included in this restoration.</p><p><a href="/archive-status/">View the recovery inventory</a></p>'),HOME,usable,base)
    (output/'404.html').write_text(missing)
    (output/'.nojekyll').touch()
    return report
