"""Deterministic static output; unreviewed downloads never enter a release build."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import shutil
from urllib.parse import unquote,urlsplit
from bs4 import BeautifulSoup
from .archive import validate_payload
from .discover import discover_html
from .render import render_html,render_css,NAV
from .svg import sanitize_svg
from .state import State,write_json
from .urls import HOME,TARGET,identity,is_site,route,asset_route,base_path,livejournal_route,original_url

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
    if allow_later:
        raise ValueError('Global later-capture approval is disabled; review each resource with compatibility-review first')
    root=Path(root);state=State(root)
    catalog_path=root/'source/catalog.json'
    catalog=json.loads(catalog_path.read_text()) if catalog_path.exists() else {'version':1,'resources':{}}
    staged=[]
    # Verify all selected files before modifying the approved collection.
    for url,r in state.data['resources'].items():
        eligible=r['status']=='recovered' or (
            r['status']=='needs_review' and bool(r.get('compatibility_review'))
        )
        if eligible and r.get('raw_path') and r['kind'] in ('html','css','image'):
            staged.append((url,r,read_record(root,r,True)))
        elif url not in catalog['resources']:
            catalog['resources'][url]={k:v for k,v in r.items() if k not in ('raw_path','sha256')}
    for url,r,body in staged:
        copied=dict(r);path='source/raw/'+Path(r['raw_path']).name
        (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_bytes(body)
        copied.update(raw_path=path,source_reviewed=True,
                      later_capture_approved=bool(r.get('compatibility_review')),status='recovered')
        catalog['resources'][url]=copied
    if staged:
        write_json(root/'source/review.json',{'publish_approved':False,'visual_reviewed':False,
                   'note':'Source collection changed; review the generated site before publishing.'})
    write_json(catalog_path,catalog)
    return {'promoted':len(staged),'publish_approved':False}

def page_shell(title: str,body: str) -> str:
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'+html.escape(title)+' — Blue Scholars restoration</title></head><body><main class="archive-gap-page"><p class="archive-eyebrow">BLUE SCHOLARS / RESTORATION WORKSPACE</p><h1>'+html.escape(title)+'</h1>'+body+'</main></body></html>'

def _write_page(output: Path,path: str,text: str):
    relative=unquote(path.lstrip('/'))
    destination=output/relative if relative.lower().endswith('.html') else output/relative/'index.html'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(text,encoding='utf-8')

def edition_prefix(url: str, record: dict) -> str:
    """Place observed pages under the historical platform generation they belong to."""
    from urllib.parse import urlsplit
    path=urlsplit(url).path
    segments=path.strip('/').split('/')
    capture=record.get('actual_capture') or TARGET
    if path.rstrip('/')=='/artistedition' or capture<'20090101000000':
        return '/2007'
    if (len(segments)>1 and segments[0]=='blog' and segments[1].isdigit()
            and len(segments[1])==4 and int(segments[1])<=2012):
        return '/2009'
    if capture<'20140101000000':
        return '/2009'
    return '/2013'

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
    explicit_page_ids={identity(HOME.rstrip('/')+path) for path,_ in CORE}
    explicit_page_ids.update(identity(r['original_url']) for r in inventory.get('pages',[]))
    usable={};usable_variants={};raw={};issues=[]
    for source_key,r in records.items():
        url=r.get('url',source_key)
        if r.get('raw_path') and r.get('status')=='recovered' and r['kind'] in ('html','css','image'):
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
    min_reference_capture='20140101000000'
    selected_page_ids={
        identity(r['_source_url']) for url,r in usable_variants.items()
        if r['kind']=='html' and (
            r.get('actual_capture','')>=min_reference_capture or edition_prefix(r['_source_url'],r) in ('/2007','/2009')
        )
    }
    selected_page_ids.update(identity(r.get('final_original','')) for r in usable_variants.values()
                              if r['kind']=='html' and r.get('final_original'))
    selected_page_ids.update(explicit_page_ids)
    # Discover destination stubs only from pages selected into this edition.
    record_by_identity={}
    for key,value in records.items():
        record_by_identity.setdefault(identity(value.get('url',key)),key)
    linked_html_routes=[];linked_lj_routes=[]
    for source_key,r in list(usable_variants.items()):
        url=r['_source_url']
        if r['kind']=='html' and identity(url) in selected_page_ids:
            source_prefix=edition_prefix(url,r)
            for ref in discover_html(raw[source_key].decode('utf-8',errors='replace'),r.get('final_original',url)):
                discovered=dict(ref);referrer=discovered.pop('referrer','')
                if discovered.get('kind')=='html':
                    lj_target=livejournal_route(discovered['url'])
                    if lj_target and lj_target.startswith('/lj/posts/'):
                        linked_lj_routes.append(discovered['url'])
                    elif not urlsplit(discovered['url']).hostname=='bluescholars.livejournal.com':
                        linked_html_routes.append((source_prefix,discovered['url']))
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
    for url,r in usable.items():
        if r['kind'] in ('css','image'):
            if r['kind']=='css':
                local=('/assets/'+r['sha256']+'.css') if r.get('source_archive') else asset_route(url,'css')
            else: local='/assets/'+r['sha256']+Path(r['raw_path']).suffix
            r['local_path']=local
    # LiveJournal was a separately hosted Blue Scholars blog, not one of the
    # three official site editions. Keep its captures in their own /lj/ tree.
    lj_pages=[(key,r) for key,r in usable_variants.items()
              if r['kind']=='html' and urlsplit(r['_source_url']).hostname in ('bluescholars.livejournal.com',)]
    lj_route_by_key={}
    newest_by_url={}
    for key,r in lj_pages:
        url=r['_source_url'];path=urlsplit(url).path
        current=newest_by_url.get(url)
        if current is None or r.get('actual_capture','')>current.get('actual_capture',''):
            newest_by_url[url]=r
    for key,r in lj_pages:
        url=r['_source_url'];path=urlsplit(url).path
        if path in ('','/'):
            local='/lj/journal/' if newest_by_url[url] is r else '/lj/captures/'+r.get('actual_capture','unknown')+'/'
        elif path=='/profile': local='/lj/profile/'
        else:
            from urllib.parse import quote
            post_path='/posts/'+quote(path.rsplit('/',1)[-1],safe='.-_')
            if newest_by_url[url] is r: local='/lj'+post_path
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
    render_resources={}
    for key,r in records.items():
        original=r.get('url',key)
        if is_site(original):render_resources.setdefault(original,r)
    render_resources.update(usable)
    pages={}
    for source_key,r in records.items():
        source_url=r.get('url',source_key)
        if r['kind']!='html' or not is_site(source_url): continue
        url=r.get('final_original') if is_site(r.get('final_original','')) else source_url
        sourced_by_selected_page=any(
            not ref.startswith('CDX:') and identity(ref) in selected_page_ids
            for ref in r.get('referrers',[]) if ref
        )
        capture=r.get('actual_capture','')
        selected_capture=bool(r.get('raw_path') and r.get('status')=='recovered'
                              and (capture>=min_reference_capture or edition_prefix(url,r) in ('/2007','/2009')))
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
    if release:
        if '/2013/' not in pages or pages['/2013/'].get('_source_key') not in usable_variants or not any(r['kind']=='css' for r in usable.values()):
            raise ValueError('Publication review cannot substitute for missing homepage HTML/CSS')
    if output.exists(): shutil.rmtree(output)
    (output/'assets').mkdir(parents=True)
    ui=root/'public/archive-ui.css'
    (output/'assets/archive-ui.css').write_text(ui.read_text() if ui.exists() else FALLBACK_UI)
    # Generated, fixed destinations only. Unknown offsets stay visible rather than guessed.
    from .urls import PAGINATION
    mappings={offset:base+'/2013'+path for offset,path in PAGINATION.items() if '/2013'+path in pages}
    script='''"use strict"; (() => {\n const mapping = MAPPING;\n const params = new URLSearchParams(location.search);\n const offset = params.get("offset");\n if (location.pathname.replace(/\\/$/, "") === BLOG && [...params].length === 1 && offset && mapping[offset]) {\n  location.replace(mapping[offset] + location.hash);\n }\n})();\n'''.replace('MAPPING',json.dumps(mappings)).replace('BLOG',json.dumps(base+'/2013/blog'))
    (output/'assets/legacy.js').write_text(script)
    for url,r in usable.items():
        if r['kind'] not in ('css','image'): continue
        destination=output/r['local_path'].lstrip('/')
        if r['kind']=='css':
            source_key=r.get('_source_key',url)
            text,found=render_css(raw[source_key].decode('utf-8',errors='replace'),r.get('final_original',url),render_resources,base)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(text);issues.extend(found)
        else:
            source_key=r.get('_source_key',url)
            destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.suffix=='.svg':
                destination.write_bytes(sanitize_svg(raw[source_key]))
            else:
                destination.write_bytes(raw[source_key])
    recovered=0;placeholders=0;page_report=[]
    for page,r in sorted(pages.items()):
        url=r['url']
        source_key=r.get('_source_key',url)
        if source_key in usable_variants:
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
        rendered,found=render_html(text,r.get('final_original',url),render_resources,base,r.get('edition_prefix',''))
        issues.extend(found);_write_page(output,page,rendered)
        page_report.append({'path':page,'source':r.get('source_url',url),'canonical_url':url,
                            'source_archive':r.get('source_archive'),'status':status,
                            'actual_capture':r.get('actual_capture')})
    legacy_posts=[p for p in page_report if p['path'].startswith('/2009/blog/')
                  and p['path']!='/2009/blog/' and p['status']=='recovered']
    if legacy_posts:
        links=''.join('<li><a href="'+html.escape(p['path'],quote=True)+'">'
                      +html.escape(p['path'].strip('/').rsplit('/',1)[-1])+'</a></li>'
                      for p in sorted(legacy_posts,key=lambda p:p['path']))
        index=page_shell('Recovered 2009 WordPress posts',
                         '<p>This local index lists surviving dated WordPress captures. It is a recovery index, not an archived original listing.</p>'
                         '<ul>'+links+'</ul>')
        index,_=render_html(index,HOME,render_resources,base)
        _write_page(output,'/2009/blog/',index)
    lj_page_report=[]
    for key,r in lj_pages:
        local=lj_route_by_key[key]
        text=raw[key].decode('utf-8',errors='replace')
        rendered,found=render_html(text,r.get('final_original',r['_source_url']),
                                   render_resources,base,'/lj')
        issues.extend(found)
        _write_page(output,local,rendered)
        lj_page_report.append({'path':local,'source':r['_source_url'],
                               'actual_capture':r.get('actual_capture'),
                               'source_archive':r.get('source_archive'),'status':'recovered'})
    if lj_page_report:
        from datetime import datetime
        labels={'/lj/journal/':'Journal front page (October 2011)',
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
            label=labels.get(p['path'],'Earlier journal capture')
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
        lj_index=lj_index.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css"></head>')
        _write_page(output,'/lj/',lj_index)
        page_report.extend({'path':p['path'],'source':p['source'],'canonical_url':p['source'],
                            'source_archive':p['source_archive'],'status':'recovered',
                            'actual_capture':p['actual_capture']} for p in lj_page_report)
        recovered+=len(lj_page_report)
    else:
        lj_index=page_shell('LiveJournal archive','<p>A separately hosted Blue Scholars journal, preserved separately from the official website editions.</p><p>No LiveJournal page captures have been recovered into this build yet.</p>')
        lj_index=lj_index.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css"></head>')
        _write_page(output,'/lj/',lj_index)
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
        notice=notice.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css"></head>')
        _write_page(output,target_path,notice)
        page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                            'source_archive':None,'status':status,'actual_capture':None})
        reported_paths.add(target_path)
        route_notices.append({'path':target_path,'status':status})
    for target_url in linked_lj_routes:
        target_path=livejournal_route(target_url)
        if not target_path or target_path in reported_paths or target_path in pages:
            continue
        root_url='http://bluescholars.livejournal.com/'
        root_record=newest_by_url.get(root_url)
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
            derived=derived.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css">'+styles+'</head>')
            rendered,found=render_html(derived,root_record.get('final_original',root_url),render_resources,base,'/lj')
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
        notice=notice.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css"></head>')
        _write_page(output,target_path,notice)
        page_report.append({'path':target_path,'source':target_url,'canonical_url':target_url,
                            'source_archive':None,'status':'not_recovered','actual_capture':None})
        reported_paths.add(target_path)
        route_notices.append({'path':target_path,'status':'not_recovered'})
    placeholders+=len(route_notices)
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
            edition_text,_=render_html(edition_text,HOME,render_resources,base)
            _write_page(output,prefix+'/',edition_text)
    gateway='<p class="archive-home-intro">Choose a preserved website generation. Each edition is built from its own dated source material; gaps remain marked.</p><nav class="edition-grid" aria-label="Preserved website generations">'
    editions=(('/2007/','2007','Independent site'),
              ('/2009/','2009','WordPress site'),
              ('/2013/','2013','Squarespace site · first located in 2013'))
    for prefix,year,era in editions:
        gateway+='<a class="edition edition-card" href="'+base+prefix+'"><span class="edition-year">'+year+'</span><span class="edition-era">'+html.escape(era)+'</span><span class="edition-action">Explore this edition <span aria-hidden="true">↗</span></span></a>'
    gateway+='</nav><nav class="archive-home-links" aria-label="Other archive resources"><a class="lj-archive" href="'+base+'/lj/">LiveJournal posts <span aria-hidden="true">↗</span></a><a class="recovery-status" href="'+base+'/archive-status/">Recovery status and source gaps <span aria-hidden="true">↗</span></a></nav>'
    hub=page_shell('Blue Scholars archive',gateway).replace('<main class="archive-gap-page">','<main class="archive-gap-page archive-home">')
    hub=hub.replace('</head>','<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="'+base+'/assets/archive-ui.css"></head>')
    _write_page(output,'/',hub)
    # Deduplicate identical findings without suppressing which page referenced a gap.
    issues=list({json.dumps(i,sort_keys=True):i for i in issues}.values())
    report={'mode':'unreviewed_candidate' if candidate else 'reviewed_source_build','base_path':base,
            'recovered_pages':recovered,'placeholder_pages':placeholders,
            'derived_pages':sum(p['status']=='derived_from_capture' for p in page_report),
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
    status_text,_=render_html(page_shell('Recovery status',stats),HOME,render_resources,base)
    _write_page(output,'/archive-status/',status_text)
    write_json(output/'archive-status/report.json',report)
    missing,_=render_html(page_shell('Page not recovered','<p>This historical page is not included in this restoration.</p><p><a href="/archive-status/">View the recovery inventory</a></p>'),HOME,render_resources,base)
    (output/'404.html').write_text(missing)
    (output/'.nojekyll').touch()
    return report
