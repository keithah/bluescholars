"""Resumable CDX indexing and conservative raw-response acquisition."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib
from urllib.parse import urlencode,urlsplit
from .archive import parse_cdx,validate_payload,capture_candidates
from .discover import discover_html,discover_css
from .state import State,write_json
from .urls import TARGET,kind_for,original_url,capture_from,in_domain

CDX='https://web.archive.org/cdx/search/cdx?'
FIELDS='timestamp,original,mimetype,statuscode,digest'

def now(): return datetime.now(timezone.utc).isoformat()

def index(state: State,client,max_pages: int=20,url: str='bluescholars.com',match: str='domain') -> dict:
    key='domain' if match=='domain' and url=='bluescholars.com' else match+':'+url
    checkpoint=state.data['index'].setdefault(key,{'resume_key':None,'complete':False,'pages':0,'rows':0})
    if checkpoint['complete']: return checkpoint
    for _ in range(max_pages):
        params={'url':url,'matchType':match,'output':'json','fl':FIELDS,'showResumeKey':'true','limit':'500'}
        old_cursor=checkpoint.get('resume_key')
        if old_cursor: params['resumeKey']=old_cursor
        try:
            response=client.get(CDX+urlencode(params))
            rows,resume=parse_cdx(response.body.decode('utf-8'))
            if resume and resume==old_cursor: raise ValueError('CDX cursor did not advance')
            digest=hashlib.sha256(response.body).hexdigest()
            path=state.root/'recovery/index'/f'{digest}.json'
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(response.body)
            for row in rows:
                original=original_url(row['original'])
                if not original: continue
                if match=='domain':
                    query_host=urlsplit(url if '://' in url else 'http://'+url).hostname or ''
                    original_host=urlsplit(original).hostname or ''
                    # The primary query includes www.bluescholars.com as well
                    # as the apex. Supplemental historical hosts are scoped to
                    # the queried host and its subdomains, never unrelated CDX rows.
                    allowed=(in_domain(original) if query_host in ('bluescholars.com','www.bluescholars.com')
                             else original_host==query_host or original_host.endswith('.'+query_host))
                    if not allowed: continue
                r=state.add(original,kind_for(original,row['mimetype']),'CDX:'+key)
                if row not in r['captures']: r['captures'].append(row)
                # Exact CDX lookups can return a normalized HTTP/HTTPS spelling.
                if match=='exact' and url in state.data['resources']:
                    requested=state.data['resources'][url]
                    if row not in requested['captures']: requested['captures'].append(row)
            checkpoint.update(resume_key=resume,complete=not bool(resume),pages=checkpoint['pages']+1,rows=checkpoint['rows']+len(rows),last_success=now())
            if key=='domain': state.data['index_complete']=checkpoint['complete']
            state.save()
            if not resume: break
        except (OSError,ValueError,UnicodeError) as exc:
            checkpoint['last_error']=str(exc)
            state.data['errors'].append({'stage':'index','url':url,'at':now(),'error':str(exc)})
            state.save();break
    return checkpoint

def index_seed_assets(state:State,client,max_assets:int=100,max_pages:int=3)->dict:
    """Index exact image URLs explicitly observed in the expanded source inventory."""
    import json
    inventory_path=state.root/'recovery/seeds/inventory.json'
    inventory=json.loads(inventory_path.read_text()) if inventory_path.exists() else {'assets':[]}
    urls=list(dict.fromkeys(item.get('original_url','') for item in inventory.get('assets',[])
                            if item.get('original_url','').startswith(('http://','https://'))))
    selected=urls[:max_assets]
    report={'archive':'Internet Archive Wayback','query_type':'exact source-linked asset URL',
            'inventory_urls':len(urls),'queried_urls':0,'indexed_capture_records':0,'failures':[]}
    for url in selected:
        before=sum(len(record.get('captures',[])) for key,record in state.data['resources'].items()
                   if record.get('url',key)==url)
        checkpoint=index(state,client,max_pages=max_pages,url=url,match='exact')
        after=sum(len(record.get('captures',[])) for key,record in state.data['resources'].items()
                  if record.get('url',key)==url)
        report['queried_urls']+=1;report['indexed_capture_records']+=max(0,after-before)
        if checkpoint.get('last_error'):
            report['failures'].append({'url':url,'error':checkpoint['last_error']})
    state.save();write_json(state.root/'recovery/asset-index-report.json',report)
    return report

def suffix(body,kind):
    if kind=='html': return '.html'
    if kind=='css': return '.css'
    if kind=='font': return '.woff2' if body.startswith(b'wOF2') else '.woff' if body.startswith(b'wOFF') else '.otf' if body.startswith(b'OTTO') else '.ttf'
    if body.startswith(b'\xff\xd8'): return '.jpg'
    if body.startswith(b'\x89PNG'): return '.png'
    if body.startswith(b'GIF'): return '.gif'
    if body.startswith(b'RIFF'): return '.webp'
    if body.startswith((b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+')): return '.tif'
    if body.startswith(b'\x00\x00'): return '.ico'
    return '.svg'

CORE_PATHS={'','/blog','/shows','/video','/shop','/holler'}
MAX_CAPTURE_ATTEMPTS_PER_RESOURCE=3

def resource_priority(record: dict) -> tuple[int,int]:
    """Put the selected Squarespace pages and their observed dependencies first.

    A full-domain CDX scan includes an unrelated older WordPress site and later
    parked-domain captures. Its stylesheet rows must not starve the selected
    2021 homepage and linked resources.
    """
    url=record['url'];parts=urlsplit(url);path=parts.path.rstrip('/')
    query_keys={part.split('=',1)[0].lower() for part in parts.query.split('&') if part}
    own_host=parts.hostname in ('bluescholars.com','www.bluescholars.com')
    refs=record.get('referrers',[])
    if record['kind']=='html' and parts.hostname=='02cd02a.netsolhost.com':
        return 3,len(url)
    if record['kind']=='html' and own_host and path=='':
        return 0,len(url)
    if record['kind']=='image' and 'seed' in refs:
        return 1,len(url)
    linked_core=any(
        (ref_parts:=urlsplit(ref)).hostname in ('bluescholars.com','www.bluescholars.com')
        and ref_parts.path.rstrip('/')==''
        for ref in refs if ref and not ref.startswith('CDX:')
    )
    cdn_host=parts.hostname in {
        'static1.squarespace.com','static.squarespace.com','assets.squarespace.com',
        'images.squarespace-cdn.com','media.tumblr.com','66.media.tumblr.com'
    }
    internal_core_asset=(own_host and not path.startswith(('/blog/wp-','/blog/tag/','/blog/20')))
    if record['kind'] in ('css','image') and linked_core and (cdn_host or internal_core_asset):
        return 1,len(url)
    linked_squarespace_article=any(
        (ref_parts:=urlsplit(ref)).hostname in ('bluescholars.com','www.bluescholars.com')
        and ref_parts.path.startswith('/blog/')
        and not (ref_parts.path.split('/')[2:3] and ref_parts.path.split('/')[2].isdigit()
                 and len(ref_parts.path.split('/')[2])==4)
        and not ref_parts.path.startswith(('/blog/wp-','/blog/tag/'))
        for ref in refs if ref and not ref.startswith('CDX:')
    )
    if record['kind'] in ('css','image') and linked_squarespace_article:
        return 1,len(url)
    if (record['kind']=='html' and own_host and path in CORE_PATHS
            and not (path=='/blog' and query_keys.intersection({'tag','author'}))):
        return 2,len(url)
    if record['kind']=='html' and 'seed' in refs:
        return 3,len(url)
    if record['kind']=='html' and own_host and path.startswith('/blog/') and path!='/blog/':
        if not query_keys.intersection({'tag','author','offset'}):
            # The current Squarespace edition uses direct slug permalinks. Dated
            # /blog/YYYY/MM/... routes belong to the separate WordPress edition.
            first_segment=path.split('/')[2:3]
            if first_segment and len(first_segment[0])==4 and first_segment[0].isdigit():
                return 7,len(url)
            return 3,len(url)
        return 5,len(url)
    if record['kind']=='html':
        return 4,len(url)
    if record['kind']=='css':
        return 6,len(url)
    return 7,len(url)

def failure_has_untried_work(record:dict,state:State)->bool:
    attempted={a.get('requested_capture') for a in record.get('attempts',[])}
    if any(capture not in attempted for capture in
           capture_candidates(record,state.data['target_capture'])):
        return True
    exact=state.data['index'].get('exact:'+record['url'],{})
    return not exact.get('complete')

def recover(state: State,client,max_files: int=150,retry_failed: bool=False,progress=None) -> dict:
    processed=0;visited=set()
    while processed<max_files:
        pending=[r for r in state.data['resources'].values() if r['url'] not in visited and
                 (r['status']=='queued' or
                  (retry_failed and r['status']=='failed' and failure_has_untried_work(r,state)))]
        if not pending: break
        # Do not let a repeatedly failing, high-priority resource starve
        # untouched pages across resumable batches. Finish the queued frontier
        # first, then use any remaining capacity to retry known failures.
        pending.sort(key=lambda r:(r['status']!='queued',resource_priority(r)))
        r=pending[0];url=r['url'];visited.add(url);processed+=1
        if r['kind'] in ('font','script','unsupported'):
            r['status']='excluded';r['reason']='No font/script/media binary redistribution';state.save();continue
        r['status']='failed';budget=MAX_CAPTURE_ATTEMPTS_PER_RESOURCE
        attempted_captures={a.get('requested_capture') for a in r.get('attempts',[])}
        # Try only a few capture dates per URL per batch. Failed dates stay in
        # provenance and are skipped on resume, so one difficult URL cannot
        # consume the whole runner before untouched pages are reached.
        exact_queried=False
        for phase in range(2):
            candidates=[c for c in capture_candidates(r,state.data['target_capture'])
                        if c not in attempted_captures]
            if not candidates and budget>0 and phase==0:
                exact=state.data['index'].get('exact:'+url,{})
                if not exact.get('complete'):
                    index(state,client,max_pages=3,url=url,match='exact')
                    exact_queried=True
                    candidates=[c for c in capture_candidates(r,state.data['target_capture'])
                                if c not in attempted_captures]
            for capture in candidates[:budget]:
                attempted_captures.add(capture);budget-=1
                replay=f'https://web.archive.org/web/{capture}id_/{url}'
                attempt={'requested_capture':capture,'request_url':replay,'at':now()}
                try:
                    response=client.get(replay)
                    validate_payload(response.body,r['kind'])
                    actual=capture_from(response.url)
                    if not actual: raise ValueError('No resolved capture timestamp in archive response')
                    digest=hashlib.sha256(response.body).hexdigest()
                    path='recovery/raw/'+digest+suffix(response.body,r['kind'])
                    destination=state.root/path
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    if not destination.exists(): destination.write_bytes(response.body)
                    final_original=original_url(response.url) or url
                    r.update(status='needs_review' if actual>state.data['target_capture'] else 'recovered',
                             raw_path=path,sha256=digest,bytes=len(response.body),actual_capture=actual,
                             final_url=response.url,final_original=final_original,
                             content_type=response.headers.get('Content-Type',''),retrieved_at=now())
                    attempt.update(result='downloaded',actual_capture=actual,sha256=digest)
                    if r['kind']=='html':
                        refs=discover_html(response.body.decode('utf-8',errors='replace'),final_original)
                    elif r['kind']=='css':
                        refs=[{'url':u,'kind':kind_for(u),'referrer':url} for u in discover_css(response.body.decode('utf-8',errors='replace'),final_original)]
                    else: refs=[]
                    for ref in refs: state.add(ref['url'],ref['kind'],ref['referrer'],actual)
                except Exception as exc:
                    # A failed URL must not erase the rest of an interrupted crawl.
                    # KeyboardInterrupt/SystemExit are intentionally not caught.
                    attempt.update(result='failed',error=f'{type(exc).__name__}: {exc}')
                r['attempts'].append(attempt);state.save()
                if r['status'] in ('recovered','needs_review'): break
            if r['status'] in ('recovered','needs_review'): break
            if phase==0 and budget>0:
                # Query the exact URL only after its already indexed dates have
                # been exhausted; broad CDX rows usually make this redundant.
                remaining=[c for c in capture_candidates(r,state.data['target_capture'])
                           if c not in attempted_captures]
                exact=state.data['index'].get('exact:'+url,{})
                if not remaining and not exact.get('complete') and not exact_queried:
                    index(state,client,max_pages=3,url=url,match='exact')
                    exact_queried=True
        if r['status'] not in ('recovered','needs_review'):
            remaining=[c for c in capture_candidates(r,state.data['target_capture'])
                       if c not in attempted_captures]
            exact=state.data['index'].get('exact:'+url,{})
            if remaining or not exact.get('complete'):
                r['status']='queued';r['reason']='Untried capture dates or exact-URL index pages remain'
            else:
                r['status']='failed';r['reason']='All indexed capture dates failed validation or retrieval'
            state.save()
        if progress and (processed%25==0 or processed==max_files):
            progress({'processed':processed,'limit':max_files,'url':url,'status':r['status']})
    report=summary(state)
    write_json(state.root/'recovery/report.json',report)
    return report

def capture_variant(state:State,client,url:str,timestamp:str,kind_override:str|None=None)->dict:
    """Recover one explicitly selected capture without replacing a URL's other dates."""
    if not timestamp.isdigit():raise ValueError('Capture timestamp must be numeric')
    canonical=original_url(url)
    if not canonical:raise ValueError('Invalid original URL')
    kind=kind_override or kind_for(canonical)
    if kind not in ('html','css','image','font'):raise ValueError(f'Unsupported capture kind: {kind}')
    replay=f'https://web.archive.org/web/{timestamp}id_/{canonical}'
    response=client.get(replay)
    validate_payload(response.body,kind)
    actual=capture_from(response.url)
    if not actual:raise ValueError('Resolved archive response has no capture timestamp')
    digest=hashlib.sha256(response.body).hexdigest()
    path='recovery/raw/'+digest+suffix(response.body,kind);destination=state.root/path
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():destination.write_bytes(response.body)
    final_original=original_url(response.url) or canonical
    key=f'{canonical}@@wayback:{actual}:{digest[:12]}'
    record={'url':canonical,'kind':kind,'status':'needs_review' if actual>TARGET else 'recovered',
        'raw_path':path,'sha256':digest,'bytes':len(response.body),'actual_capture':actual,
        'final_url':response.url,'final_original':final_original,
        'content_type':response.headers.get('Content-Type',''),'source_archive':'Internet Archive Wayback',
        'source_requested_capture':timestamp,'referrers':['explicit-capture-request'],'hints':[],
        'captures':[],'attempts':[],'retrieved_at':now()}
    state.data['resources'][key]=record
    if kind=='html':
        refs=discover_html(response.body.decode('utf-8',errors='replace'),final_original)
    elif kind=='css':
        refs=[{'url':u,'kind':kind_for(u),'referrer':canonical} for u in discover_css(response.body.decode('utf-8',errors='replace'),final_original)]
    else:refs=[]
    for ref in refs:state.add(ref['url'],ref['kind'],ref.get('referrer',canonical),actual)
    state.save()
    return {'url':canonical,'source_key':key,'requested_capture':timestamp,'actual_capture':actual,
            'status':record['status'],'sha256':digest,'bytes':len(response.body),'kind':kind}

ERA_BOUNDS={'2007':('20070101000000','20081231235959'),
            '2009':('20090101000000','20130920235959'),
            '2013':('20130921000000','20230930235959')}

def capture_era(state:State,client,era:str,max_files:int=2000)->dict:
    """Capture the latest successful Wayback response per URL in one site era."""
    if era not in ERA_BOUNDS:raise ValueError('Era must be 2007, 2009, or 2013')
    start,end=ERA_BOUNDS[era];selected=[]
    existing_success={(r.get('url'),r.get('source_requested_capture')) for r in state.data['resources'].values()
                       if r.get('source_requested_capture') and r.get('raw_path')
                       and r.get('status') in ('recovered','needs_review')}
    for key,record in state.data['resources'].items():
        url=record.get('url',key)
        if record.get('kind') not in ('html','css','image'):continue
        candidates=[c.get('timestamp','') for c in record.get('captures',[])
                    if c.get('statuscode')=='200' and start<=c.get('timestamp','')<=end]
        if not candidates:continue
        candidates=sorted(set(candidates),reverse=True)
        if any((url,timestamp) in existing_success for timestamp in candidates):continue
        selected.append((url,candidates))
    selected=sorted(selected,key=lambda item:(item[1][0],item[0]))[:max_files]
    report={'era':era,'date_start':start,'date_end':end,'eligible_urls':len(set(url for url,_ in selected)),
            'attempted':0,'recovered':0,'failures':[],'captures':[]}
    for url,candidates in selected:
        report['attempted']+=1
        attempted=[];result=None
        for timestamp in candidates:
            attempted.append(timestamp)
            try:
                result=capture_variant(state,client,url,timestamp)
                result['attempted_captures']=list(attempted)
                report['recovered']+=1;report['captures'].append(result)
                break
            except Exception as exc:
                last_error=f'{type(exc).__name__}: {exc}'
        if result is None:
            report['failures'].append({'url':url,'timestamps':attempted,'error':last_error})
        if report['attempted']%25==0:
            state.save();write_json(state.root/f'recovery/era-{era}-report.json',report)
    state.save();write_json(state.root/f'recovery/era-{era}-report.json',report)
    report['eligible_urls']=len(set(url for url,_ in selected))
    return report

def summary(state: State) -> dict:
    resources=list(state.data['resources'].values())
    statuses={s:sum(r['status']==s for r in resources) for s in ('queued','recovered','needs_review','failed','excluded')}
    valid=[r for r in resources if r['status'] in ('recovered','needs_review') and r.get('sha256')]
    return {'resource_urls':len(resources),'statuses':statuses,
            'indexed_capture_records':sum(len(r['captures']) for r in resources),
            'index_complete':state.data['index_complete'],
            'unique_downloaded_files':len({r['sha256'] for r in valid}),
            'downloaded_bytes':sum({r['sha256']:r.get('bytes',0) for r in valid}.values()),
            'failed_attempts':sum(a['result']=='failed' for r in resources for a in r['attempts']),
            'generated_at':now()}
