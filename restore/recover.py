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
                if not original or (match=='domain' and not in_domain(original)): continue
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

def suffix(body,kind):
    if kind=='html': return '.html'
    if kind=='css': return '.css'
    if body.startswith(b'\xff\xd8'): return '.jpg'
    if body.startswith(b'\x89PNG'): return '.png'
    if body.startswith(b'GIF'): return '.gif'
    if body.startswith(b'RIFF'): return '.webp'
    if body.startswith(b'\x00\x00'): return '.ico'
    return '.svg'

CORE_PATHS={'','/blog','/shows','/video','/shop','/holler'}

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
    if record['kind']=='html' and own_host and path=='':
        return 0,len(url)
    if record['kind']=='image' and 'seed' in refs:
        return 1,len(url)
    linked_core=any(
        (ref_parts:=urlsplit(ref)).hostname in ('bluescholars.com','www.bluescholars.com')
        and ref_parts.path.rstrip('/')==''
        for ref in refs if ref and not ref.startswith('CDX:')
    )
    if record['kind'] in ('css','image') and linked_core:
        return 1,len(url)
    if (record['kind']=='html' and own_host and path in CORE_PATHS
            and not (path=='/blog' and query_keys.intersection({'tag','author'}))):
        return 2,len(url)
    if record['kind']=='html' and 'seed' in refs:
        return 3,len(url)
    if record['kind']=='html' and own_host and path.startswith('/blog/') and path!='/blog/':
        if not query_keys.intersection({'tag','author','offset'}):
            return 3,len(url)
        return 5,len(url)
    if record['kind']=='html':
        return 4,len(url)
    if record['kind']=='css':
        return 6,len(url)
    return 7,len(url)

def recover(state: State,client,max_files: int=150,retry_failed: bool=False) -> dict:
    processed=0;visited=set()
    while processed<max_files:
        pending=[r for r in state.data['resources'].values() if r['url'] not in visited and
                 (r['status']=='queued' or (retry_failed and r['status']=='failed'))]
        if not pending: break
        pending.sort(key=resource_priority)
        r=pending[0];url=r['url'];visited.add(url);processed+=1
        if r['kind'] in ('font','script','unsupported'):
            r['status']='excluded';r['reason']='No font/script/media binary redistribution';state.save();continue
        tried=set();r['status']='failed'
        # First try the reference and observed hints. If necessary, discover other dates.
        for phase in range(2):
            for capture in capture_candidates(r,state.data['target_capture']):
                if capture in tried: continue
                tried.add(capture)
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
            if phase==0: index(state,client,max_pages=3,url=url,match='exact')
    report=summary(state)
    write_json(state.root/'recovery/report.json',report)
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
