"""Inventory-scoped acquisition from the independent Arquivo.pt web archive."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
import requests
from .archive import validate_payload
from .discover import discover_html
from .state import State,write_json
from .urls import original_url,identity,in_domain,kind_for

API='https://arquivo.pt/textsearch'
CHECKPOINT='recovery/arquivo-state.json'
CDX='https://arquivo.pt/wayback/cdx'

def _site_pages(state:State,history_url:str)->list[str]:
    """Use known internal HTML URLs as exact, evidence-backed history queries."""
    parts=urlsplit(history_url if '://' in history_url else 'https://'+history_url)
    if parts.path not in ('','/') or parts.query:
        return [original_url(history_url)] if original_url(history_url) else []
    pages={}
    for key,record in state.data['resources'].items():
        url=original_url(record.get('url',key))
        p=urlsplit(url or '')
        if (record.get('kind')=='html' and p.hostname in ('bluescholars.com','www.bluescholars.com')
                and url):
            pages[url]=record
    root='https://'+parts.netloc.lower().removeprefix('www.')+'/'
    pages.setdefault(root,{'referrers':['seed']})
    # Query deliberately seeded pages first, then paths discovered in the
    # archive inventory. Stable ordering makes a bounded run resumable.
    def rank(item):
        url,record=item;p=urlsplit(url)
        seeded=any('seed' in ref.lower() for ref in record.get('referrers',[]))
        return (0 if p.path=='/' else 1,0 if seeded else 1,p.path,p.query,url)
    return [url for url,_ in sorted(pages.items(),key=rank)]

def harvest(root:Path,history_url:str='bluescholars.com',max_urls:int=200,delay:float=0.5)->dict:
    """Query exact histories for known site pages and preserve each valid memento.

    Successful history queries, including empty results, are checkpointed. A
    later run resumes the remaining inventory and retries only failed queries.
    Third-party assets are not queried here; they remain a separately scoped
    source inventory.
    """
    if max_urls<1 or delay<0:raise ValueError('Arquivo limits must be positive and delay nonnegative')
    root=Path(root);state=State(root)
    checkpoint_path=root/CHECKPOINT
    checkpoint=json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {
        'archive':'Arquivo.pt','queried_urls':[],'failures':[]}
    queried=set(checkpoint.get('queried_urls',[]));prior_failures={x['url']:x for x in checkpoint.get('failures',[])}
    targets=[url for url in _site_pages(state,history_url) if url not in queried]
    targets=targets[:max_urls]
    report={'archive':'Arquivo.pt','query_scope':'exact histories of inventoried Blue Scholars HTML pages',
            'queried_history_url':history_url,'inventory_page_urls':len(_site_pages(state,history_url)),
            'query_limit':max_urls,'queried_urls':0,'captures_found':0,'successful_http_captures':0,
            'recovered_html':0,'failures':[],'captures':[]}
    for url in targets:
        if report['queried_urls'] and delay:time.sleep(delay)
        report['queried_urls']+=1
        try:
            response=requests.get(API,params={'versionHistory':url,'maxItems':100},timeout=30)
            response.raise_for_status();items=response.json().get('response_items',[])
            queried.add(url);prior_failures.pop(url,None);report['captures_found']+=len(items)
            for item in items:
                capture=str(item.get('tstamp',''));original=original_url(item.get('originalURL',''))
                row={'timestamp':capture,'original_url':original,'statusCode':item.get('statusCode'),
                     'linkToArchive':item.get('linkToArchive'),'linkToOriginalFile':item.get('linkToOriginalFile'),
                     'digest':item.get('digest'),'contentLength':item.get('contentLength'),
                     'collection':item.get('collection'),'queried_url':url}
                report['captures'].append(row)
                if str(item.get('statusCode'))!='200' or not original or not capture.isdigit():continue
                report['successful_http_captures']+=1
                try:
                    replay=item.get('linkToOriginalFile','');replay_host=urlsplit(replay).hostname or ''
                    if urlsplit(replay).scheme!='https' or not (replay_host=='arquivo.pt' or replay_host.endswith('.arquivo.pt')):
                        raise ValueError('Arquivo.pt returned a replay URL outside its archive host')
                    page=requests.get(replay,timeout=30);page.raise_for_status();body=page.content
                    validate_payload(body,'html')
                    digest=hashlib.sha256(body).hexdigest();path='recovery/raw/'+digest+'.html'
                    dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True)
                    if not dest.exists():dest.write_bytes(body)
                    key=f'{original}@@arquivo:{capture}:{digest[:12]}'
                    if key not in state.data['resources']:
                        state.data['resources'][key]={'url':original,'kind':'html','status':'recovered',
                            'raw_path':path,'sha256':digest,'bytes':len(body),'actual_capture':capture,
                            'final_original':original,'final_url':page.url,
                            'content_type':page.headers.get('Content-Type','text/html'),
                            'source_archive':'Arquivo.pt','source_collection':item.get('collection'),
                            'source_digest':item.get('digest'),'source_archive_url':replay,
                            'referrers':['arquivo:versionHistory:'+url],'hints':[],'captures':[],
                            'attempts':[],'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
                        for ref in discover_html(body.decode('utf-8',errors='replace'),original):
                            state.add(ref['url'],ref['kind'],ref['referrer'],capture)
                    report['recovered_html']+=1
                except Exception as exc:
                    report['failures'].append({'url':original,'timestamp':capture,
                        'error':f'{type(exc).__name__}: {exc}'})
        except Exception as exc:
            failure={'url':url,'error':f'{type(exc).__name__}: {exc}'}
            prior_failures[url]=failure;report['failures'].append(failure)
        checkpoint['queried_urls']=sorted(queried)
        checkpoint['failures']=[prior_failures[k] for k in sorted(prior_failures)]
        checkpoint['last_batch']={'queried_urls':report['queried_urls'],'last_url':url}
        write_json(checkpoint_path,checkpoint);state.save()
    checkpoint['queried_urls']=sorted(queried)
    checkpoint['failures']=[prior_failures[k] for k in sorted(prior_failures)]
    write_json(checkpoint_path,checkpoint);state.save()
    report['remaining_unqueried_urls']=max(0,report['inventory_page_urls']-len(queried))
    write_json(root/'recovery/arquivo-report.json',report)
    return report

def _era(timestamp:str)->str|None:
    if not timestamp.isdigit():return None
    stamp=timestamp.ljust(14,'0')
    if '20070101000000'<=stamp<='20081231235959':return '2007'
    if '20090101000000'<=stamp<='20130920235959':return '2009'
    if '20130921000000'<=stamp<='20230930235959':return '2013'
    return None

def _latest_per_era(rows:list[dict])->list[dict]:
    latest={}
    supported={'text/html','application/xhtml+xml','text/css','image/jpeg','image/png',
                'image/gif','image/webp','image/svg+xml','image/vnd.microsoft.icon','image/x-icon'}
    for row in rows:
        url=original_url(row.get('url',''));date=str(row.get('timestamp',''));era=_era(date)
        mime=str(row.get('mime','')).split(';',1)[0].lower()
        if (not url or not in_domain(url) or not era or str(row.get('status',''))!='200'
                or mime not in supported):continue
        kind=kind_for(url,mime)
        if kind not in ('html','css','image'):continue
        key=(identity(url),era)
        old=latest.get(key)
        if old is None or (date,url)>(str(old.get('timestamp','')),str(old.get('url',''))):
            latest[key]=row
    priority={'html':0,'css':1,'image':2}
    return sorted(latest.values(),key=lambda row:(_era(row['timestamp']),
        priority[kind_for(row['url'],row.get('mime',''))],identity(row['url']),row['timestamp']))

def harvest_domain(root:Path,max_records:int=500,delay:float=0.5)->dict:
    """Enumerate Arquivo.pt's whole indexed domain and preserve latest per-era responses.

    The raw CDX response is retained as an index source. For each URL, the latest
    successful HTML, CSS, or image response in each of the three known editions
    is independently kept. Acquisition limits apply to replay downloads, not to
    the archive's small domain index query.
    """
    if max_records<1 or delay<0:raise ValueError('Arquivo limits must be positive and delay nonnegative')
    root=Path(root);state=State(root);index_path=root/'recovery/index/arquivo-domain.jsonl'
    checkpoint_path=root/'recovery/arquivo-domain-state.json'
    checkpoint=json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {
        'archive':'Arquivo.pt','completed_records':[],'failures':[]}
    index_error=None
    if index_path.exists():
        raw=index_path.read_bytes()
    else:
        try:
            response=requests.get(CDX,params={'url':'bluescholars.com','matchType':'domain',
                'output':'json','limit':100000,'resolveRevisits':'true'},timeout=90,
                headers={'User-Agent':'BlueScholarsRestoration/0.1 (historical preservation)'})
            response.raise_for_status();raw=response.content
            index_path.parent.mkdir(parents=True,exist_ok=True);index_path.write_bytes(raw)
        except Exception as exc:
            index_error=f'{type(exc).__name__}: {exc}';raw=b''
    rows=[]
    try:
        for line in raw.decode('utf-8').splitlines():
            if line.strip():rows.append(json.loads(line))
    except (UnicodeError,json.JSONDecodeError) as exc:
        index_error=f'Invalid Arquivo.pt CDX JSON-lines: {type(exc).__name__}: {exc}'
    selected=_latest_per_era(rows);completed=set(checkpoint.get('completed_records',[]))
    failures={item['record_key']:item for item in checkpoint.get('failures',[])}
    pending=[r for r in selected if f"{identity(r['url'])}@@{_era(r['timestamp'])}:{r['timestamp']}" not in completed]
    # Retry failed records first, then continue the deterministic index order.
    failed_keys=set(failures)
    pending.sort(key=lambda r:(0 if f"{identity(r['url'])}@@{_era(r['timestamp'])}:{r['timestamp']}" in failed_keys else 1,
                               selected.index(r)))
    batch=pending[:max_records];report={'archive':'Arquivo.pt','query_scope':'complete domain CDX index; latest status-200 page/style/image per URL and edition',
        'index_url':CDX,'index_rows':len(rows),'selected_latest_per_url_edition':len(selected),
        'queried_collections':'Arquivo.pt indexed captures','attempt_limit':max_records,
        'attempted_records':0,'recovered_records':0,'failed_records':[],'index_error':index_error,
        'by_era':{era:{'selected':sum(_era(r['timestamp'])==era for r in selected),
                       'attempted':0,'recovered':0} for era in ('2007','2009','2013')}}
    for i,row in enumerate(batch):
        if i and delay:time.sleep(delay)
        era=_era(row['timestamp']);url=original_url(row['url']);kind=kind_for(url,row.get('mime',''))
        record_key=f'{identity(url)}@@{era}:{row["timestamp"]}'
        report['attempted_records']+=1;report['by_era'][era]['attempted']+=1
        try:
            replay=f'https://arquivo.pt/noFrame/replay/{row["timestamp"]}id_/{url}'
            response=requests.get(replay,timeout=45,headers={'User-Agent':'BlueScholarsRestoration/0.1 (historical preservation)'})
            response.raise_for_status();body=response.content;validate_payload(body,kind)
            sha=hashlib.sha256(body).hexdigest()
            ext='.html' if kind=='html' else '.css' if kind=='css' else (
                '.jpg' if body.startswith(b'\xff\xd8') else '.png' if body.startswith(b'\x89PNG') else
                '.gif' if body.startswith(b'GIF') else '.webp' if body.startswith(b'RIFF') else '.svg')
            path='recovery/raw/'+sha+ext;destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists():destination.write_bytes(body)
            storage_key=f'{url}@@arquivo:{row["timestamp"]}:{sha[:12]}'
            record={'url':url,'kind':kind,'status':'recovered','raw_path':path,'sha256':sha,
                'bytes':len(body),'actual_capture':row['timestamp'],'final_original':url,'final_url':response.url,
                'content_type':response.headers.get('Content-Type',row.get('mime','')),
                'source_archive':'Arquivo.pt','source_collection':row.get('collection'),
                'source_digest':row.get('digest'),'source_warc':row.get('filename'),
                'source_offset':int(row['offset']) if str(row.get('offset','')).isdigit() else None,
                'source_length':int(row['length']) if str(row.get('length','')).isdigit() else None,
                'source_archive_url':replay,'source_key':storage_key,
                'referrers':['arquivo:domain-cdx'],'hints':[],'captures':[], 'attempts':[],
                'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            state.data['resources'][storage_key]=record
            refs=[]
            if kind=='html':refs=discover_html(body.decode('utf-8',errors='replace'),url)
            elif kind=='css':
                from .discover import discover_css
                refs=[{'url':u,'kind':kind_for(u),'referrer':url} for u in discover_css(body.decode('utf-8',errors='replace'),url)]
            for ref in refs:state.add(ref['url'],ref['kind'],ref['referrer'],row['timestamp'])
            completed.add(record_key);failures.pop(record_key,None)
            report['recovered_records']+=1;report['by_era'][era]['recovered']+=1
        except Exception as exc:
            failure={'record_key':record_key,'url':url,'timestamp':row['timestamp'],
                     'error':f'{type(exc).__name__}: {exc}'}
            failures[record_key]=failure;report['failed_records'].append(failure)
        checkpoint.update(completed_records=sorted(completed),failures=[failures[k] for k in sorted(failures)])
        write_json(checkpoint_path,checkpoint);state.save()
    report['completed_records']=len(completed);report['remaining_records']=max(0,len(selected)-len(completed))
    report['total_failures']=len(failures)
    write_json(root/'recovery/arquivo-domain-report.json',report)
    return report
