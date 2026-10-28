"""Resumable CDX indexing and conservative raw-response acquisition."""
from __future__ import annotations
from restore.cooldown import ArchiveCooldown
from datetime import datetime,timezone
import hashlib
from urllib.parse import urlencode,urlsplit
from .archive import parse_cdx,validate_payload,capture_candidates
from .discover import discover_html,discover_css
from .state import State,write_json
from .urls import TARGET,SQUARESPACE_START,LEGACY_EDITION_END,kind_for,original_url,capture_from,in_domain,identity

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
            checkpoint.pop('last_error',None)
            checkpoint.pop('retry_at',None)
            if key=='domain': state.data['index_complete']=checkpoint['complete']
            state.save()
            if not resume: break
        except ArchiveCooldown as exc:
            checkpoint.update(retry_at=exc.retry_at, last_error=str(exc))
            state.save()
            raise
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

def index_feed_resources(state:State,client,max_urls:int=30,max_pages:int=3,retry_errors:bool=False)->dict:
    """Exact-index new source-linked URLs discovered inside archived feed bodies."""
    if max_urls<1 or max_pages<1:raise ValueError('Feed index limits must be positive')
    pending=[];deferred_errors=0
    feed_page_ids={identity(record.get('url','')) for record in state.data['resources'].values()
                   if record.get('kind')=='html'
                   and any(ref.startswith('feed:') for ref in record.get('referrers',[]))}
    for record in state.data['resources'].values():
        if record.get('kind') not in ('html','image','css'):
            continue
        refs=[ref for ref in record.get('referrers',[]) if ref]
        discovered_from_feed=any(ref.startswith('feed:') for ref in refs)
        linked_from_feed_page=any(not ref.startswith('CDX:') and identity(ref) in feed_page_ids for ref in refs)
        if (not (discovered_from_feed or linked_from_feed_page) or record.get('captures')
                or record.get('raw_path') or record.get('status')=='excluded'):
            continue
        exact=state.data['index'].get('exact:'+record['url'],{})
        if exact.get('complete'):
            continue
        if exact.get('last_error') and not exact.get('retry_at') and not retry_errors:
            deferred_errors+=1
            continue
        pending.append(record)
    # Query-free post and gallery routes are more useful than WordPress's
    # per-comment reply URLs. Then exact-index direct images/styles before
    # query variants, which are usually duplicate comment-thread lookups.
    def feed_priority(record):
        parts=urlsplit(record['url'])
        has_reply='replytocom=' in parts.query.lower() or 'replytocom=' in parts.path.lower()
        kind_order={'html':0,'image':1,'css':2}
        return (has_reply, bool(parts.query), kind_order.get(record['kind'],3), record['url'])
    pending.sort(key=feed_priority)
    selected=pending[:max_urls]
    report={'archive':'Internet Archive Wayback','query_type':'exact source-linked feed URL',
            'pending_urls':len(pending),'queried_urls':0,'indexed_capture_records':0,
            'image_urls':0,'page_urls':0,'deferred_errors':deferred_errors,
            'retry_errors':bool(retry_errors),'failures':[],'urls':[]}
    for record in selected:
        url=record['url']
        before=sum(len(item.get('captures',[])) for item in state.data['resources'].values()
                   if item.get('url')==url)
        checkpoint=index(state,client,max_pages=max_pages,url=url,match='exact')
        after=sum(len(item.get('captures',[])) for item in state.data['resources'].values()
                  if item.get('url')==url)
        report['queried_urls']+=1
        report['indexed_capture_records']+=max(0,after-before)
        report['image_urls' if record['kind']=='image' else 'page_urls']+=1
        report['urls'].append({'url':url,'kind':record['kind'],'captures_added':max(0,after-before),
                               'complete':bool(checkpoint.get('complete'))})
        if checkpoint.get('last_error'):
            report['failures'].append({'url':url,'error':checkpoint['last_error']})
    write_json(state.root/'recovery/feed-index-report.json',report)
    return report

def recover_feed_resources(state:State,client,max_files:int=30)->dict:
    """Recover indexed WordPress feed pages and media as dated variants."""
    if max_files<1:raise ValueError('Feed recovery limit must be positive')
    pending=[]
    feed_page_ids={identity(record.get('url','')) for record in state.data['resources'].values()
                   if record.get('kind')=='html'
                   and any(ref.startswith('feed:') for ref in record.get('referrers',[]))}
    for record in state.data['resources'].values():
        if record.get('kind') not in ('html','css','image'):
            continue
        refs=[ref for ref in record.get('referrers',[]) if ref]
        is_feed_source=any(ref.startswith('feed:') for ref in refs)
        is_feed_page_asset=any(not ref.startswith('CDX:') and identity(ref) in feed_page_ids for ref in refs)
        if not (is_feed_source or is_feed_page_asset):
            continue
        dates=sorted({capture.get('timestamp','') for capture in record.get('captures',[])
                      if capture.get('statuscode')=='200'
                      and capture.get('timestamp','')<=LEGACY_EDITION_END},reverse=True)
        if not dates:
            continue
        existing_dates=[variant.get('actual_capture','') for variant in state.data['resources'].values()
                        if variant.get('url')==record['url'] and variant.get('raw_path')
                        and variant.get('status') in ('recovered','needs_review')
                        and variant.get('actual_capture','')<=LEGACY_EDITION_END]
        if existing_dates and dates[0]<=max(existing_dates):
            continue
        pending.append((record,dates[0]))
    pending.sort(key=lambda item:(item[0]['kind']!='html',item[0]['url']))
    selected=pending[:max_files]
    report={'archive':'Internet Archive Wayback','edition':'2009 WordPress source frontier',
            'pending_urls':len(pending),'attempted':0,'recovered':0,'needs_review':0,
            'failures':[],'captures':[]}
    for record,stamp in selected:
        report['attempted']+=1
        try:
            result=capture_variant(state,client,record['url'],stamp,record['kind'])
            variant=state.data['resources'][result['source_key']]
            variant['referrers']=sorted(set(record.get('referrers',[])+['explicit-capture-request']))
            variant['feed_source_urls']=sorted({ref.rsplit(' -> ',1)[1] for ref in record.get('referrers',[])
                                                if ref.startswith('feed:') and ' -> ' in ref})
            state.save()
            report['recovered' if result['status']=='recovered' else 'needs_review']+=1
            report['captures'].append(result)
        except ArchiveCooldown:
            raise
        except Exception as exc:
            report['failures'].append({'url':record['url'],'timestamp':stamp,
                                       'error':f'{type(exc).__name__}: {exc}'})
    report['remaining_urls']=max(0,len(pending)-report['attempted'])
    write_json(state.root/'recovery/feed-recovery-report.json',report)
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
    if parts.hostname=='bluescholars.livejournal.com' and 'replyto' in query_keys:
        # Wayback commonly indexes individual comment-reply variants without
        # storing their HTML. Defer those repeated 404s until real pages and
        # their assets have had a recovery attempt.
        return 9,len(url)
    livejournal_css=(parts.hostname in ('l-stat.livejournal.net','l-stat.livejournal.com')
                     and record['kind']=='css')
    linked_livejournal_image=(record['kind']=='image'
        and parts.hostname in ('l-stat.livejournal.net','l-stat.livejournal.com')
        and any(urlsplit(ref).hostname in ('l-stat.livejournal.net','l-stat.livejournal.com')
                for ref in refs if ref and not ref.startswith('CDX:')))
    linked_livejournal_proxy=(record['kind']=='image'
        and parts.hostname=='imgprx.livejournal.net'
        and any(urlsplit(ref).hostname=='bluescholars.livejournal.com'
                for ref in refs if ref and not ref.startswith('CDX:')))
    if livejournal_css or linked_livejournal_image:
        return 1,len(url)
    linked_historical_page=any(
        bool((ref_parts:=urlsplit(ref)).path.strip('/'))
        and ((ref_host:=ref_parts.hostname or '')=='bluescholars.com'
             or ref_host.endswith('.bluescholars.com')
             or ref_host=='02cd02a.netsolhost.com')
        for ref in refs if ref and not ref.startswith('CDX:'))
    if record['kind'] in ('css','image') and linked_historical_page:
        return 1,len(url)
    if linked_livejournal_proxy:
        # Preserve the exact source-linked URLs, but try article bodies and
        # recoverable original images before Wayback's opaque proxy tokens.
        return 5,len(url)
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
    linked_legacy_post=(
        record['kind']=='html' and own_host and len(path.strip('/').split('/'))==1
        and any(
            (ref_parts:=urlsplit(ref)).hostname in ('bluescholars.com','www.bluescholars.com')
            and (segments:=ref_parts.path.strip('/').split('/'))[0]=='page'
            and len(segments)==2 and segments[1].isdigit()
            for ref in refs if ref and not ref.startswith('CDX:')
        )
    )
    if linked_legacy_post:
        return 3,len(url)
    if record['kind']=='html':
        return 4,len(url)
    if record['kind']=='css':
        return 6,len(url)
    return 7,len(url)

def failure_has_untried_work(record:dict,state:State)->bool:
    attempted={a.get('requested_capture') for a in record.get('attempts',[]) if a.get('result')!='deferred'}
    if any(capture not in attempted for capture in
           capture_candidates(record,state.data['target_capture'])):
        return True
    exact=state.data['index'].get('exact:'+record['url'],{})
    return not exact.get('complete')

def recover(state: State,client,max_files: int=150,retry_failed: bool=False,progress=None,
            host: str|None=None) -> dict:
    host=host.strip().lower().rstrip('.') if host else None
    processed=0;visited=set()
    while processed<max_files:
        pending=[r for r in state.data['resources'].values() if r['url'] not in visited and
                 (not host or (urlsplit(r.get('url','')).hostname or '').lower().rstrip('.')==host) and
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
        r['status']='queued';budget=MAX_CAPTURE_ATTEMPTS_PER_RESOURCE
        attempted_captures={a.get('requested_capture') for a in r.get('attempts',[]) if a.get('result')!='deferred'}
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
                    r.pop('retry_at',None)
                    attempt.update(result='downloaded',actual_capture=actual,sha256=digest)
                    if r['kind']=='html':
                        refs=discover_html(response.body.decode('utf-8',errors='replace'),final_original)
                    elif r['kind']=='css':
                        refs=[{'url':u,'kind':kind_for(u),'referrer':url} for u in discover_css(response.body.decode('utf-8',errors='replace'),final_original)]
                    else: refs=[]
                    for ref in refs: state.add(ref['url'],ref['kind'],ref['referrer'],actual)
                except ArchiveCooldown as exc:
                    attempt.update(result='deferred',retry_at=exc.retry_at,error=str(exc))
                    r['attempts'].append(attempt)
                    r.update(status='queued',retry_at=exc.retry_at,reason='Archive cooldown; capture remains queued')
                    state.save()
                    raise
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
            '2009':('20090101000000',LEGACY_EDITION_END),
            '2013':(SQUARESPACE_START,'20230930235959')}

def capture_era(state:State,client,era:str,max_files:int=2000)->dict:
    """Capture the latest successful Wayback response per URL in one site era."""
    if era not in ERA_BOUNDS:raise ValueError('Era must be 2007, 2009, or 2013')
    start,end=ERA_BOUNDS[era];selected=[];indexed_candidates={};already_recovered=set()
    successful={}
    for record in state.data['resources'].values():
        actual=record.get('actual_capture')
        if (actual and record.get('raw_path')
                and record.get('status') in ('recovered','needs_review')):
            successful.setdefault(record.get('url'),set()).add(actual)
    def has_successful_capture(url):
        return any(start<=actual<=end for actual in successful.get(url,()))
    for key,record in state.data['resources'].items():
        url=record.get('url',key)
        if record.get('kind') not in ('html','css','image'):continue
        candidates=[c.get('timestamp','') for c in record.get('captures',[])
                    if c.get('statuscode')=='200' and start<=c.get('timestamp','')<=end]
        if not candidates:continue
        candidates=sorted(set(candidates),reverse=True)
        indexed_candidates.setdefault(url,set()).update(candidates)
        if has_successful_capture(url):
            already_recovered.add(url);continue
        selected.append((url,candidates))
    selected=sorted(selected,key=lambda item:(item[1][0],item[0]))[:max_files]
    report={'era':era,'date_start':start,'date_end':end,'eligible_urls':len(set(url for url,_ in selected)),
            'indexed_urls':len(indexed_candidates),'already_recovered_urls':len(already_recovered),
            'remaining_urls':None,'selected_urls':len(selected),'batch_limit':max_files,
            'attempted':0,'recovered':0,'failures':[],'captures':[]}
    def remaining_count():
        return sum(1 for url,candidates in indexed_candidates.items()
                   if not has_successful_capture(url))
    for url,candidates in selected:
        report['attempted']+=1
        attempted=[];result=None
        for timestamp in candidates:
            attempted.append(timestamp)
            try:
                result=capture_variant(state,client,url,timestamp)
                actual=result.get('actual_capture','')
                if not start<=actual<=end:
                    later=state.data['resources'].get(result.get('source_key'))
                    if later:
                        later['status']='needs_review'
                        later['era_compatibility_exception']={
                            'requested_era':era,'requested_capture':timestamp,
                            'actual_capture':actual,
                            'reason':'Wayback redirected outside the requested edition date range.'}
                        state.save()
                    raise ValueError(f'Resolved capture {actual or "unknown"} is outside the {era} era')
                result['attempted_captures']=list(attempted)
                report['recovered']+=1;report['captures'].append(result)
                if actual:successful.setdefault(url,set()).add(actual)
                break
            except ArchiveCooldown:
                raise
            except Exception as exc:
                result=None
                last_error=f'{type(exc).__name__}: {exc}'
        if result is None:
            report['failures'].append({'url':url,'timestamps':attempted,'error':last_error})
        if report['attempted']%25==0:
            state.save();report['remaining_urls']=remaining_count()
            write_json(state.root/f'recovery/era-{era}-report.json',report)
    state.save()
    report['remaining_urls']=remaining_count()
    write_json(state.root/f'recovery/era-{era}-report.json',report)
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
