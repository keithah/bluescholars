"""Search and extract independently archived Common Crawl WARC responses."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
import requests
from .archive import validate_payload
from .discover import discover_html,discover_css
from .state import State,write_json
from .urls import kind_for,original_url,in_domain

INDEXES='https://index.commoncrawl.org/collinfo.json'
FIELDS='timestamp,url,mime,digest,status,filename,offset,length'

def extract_warc_response(data: bytes) -> tuple[bytes,int,dict]:
    try: data=gzip.decompress(data)
    except (OSError,EOFError) as exc: raise ValueError('Invalid compressed WARC record') from exc
    if data.startswith(b'WARC/'):
        warc_header_end=data.find(b'\r\n\r\n');delimiter=4
        if warc_header_end<0:warc_header_end=data.find(b'\n\n');delimiter=2
        if warc_header_end<0:raise ValueError('WARC headers are incomplete')
        warc_length=re.search(rb'(?im)^Content-Length:\s*(\d+)\s*$',data[:warc_header_end])
        warc_body_start=warc_header_end+delimiter
        block=(data[warc_body_start:warc_body_start+int(warc_length.group(1))]
               if warc_length else data[warc_body_start:])
    else:
        # Common Crawl's 2008–2010 collections use the older ARC record form.
        marker=data.find(b'HTTP/1.')
        if marker<0:raise ValueError('ARC record has no HTTP response')
        block=data[marker:]
    marker=block.find(b'HTTP/1.')
    if marker<0: raise ValueError('WARC record has no HTTP response')
    header_end=block.find(b'\r\n\r\n',marker)
    if header_end<0: header_end=block.find(b'\n\n',marker)
    if header_end<0: raise ValueError('HTTP response headers are incomplete')
    raw_headers=block[marker:header_end].replace(b'\r\n',b'\n').split(b'\n')
    match=re.match(rb'HTTP/\d(?:\.\d)?\s+(\d{3})',raw_headers[0])
    if not match: raise ValueError('Invalid archived HTTP status line')
    headers={}
    for line in raw_headers[1:]:
        if b':' in line:
            key,value=line.split(b':',1);headers[key.decode('latin1').strip().lower()]=value.decode('latin1').strip()
    body_offset=header_end+(4 if block[header_end:header_end+4]==b'\r\n\r\n' else 2)
    body=block[body_offset:]
    if headers.get('content-length','').isdigit(): body=body[:int(headers['content-length'])]
    status=int(match.group(1))
    if status!=200: raise ValueError(f'Archived HTTP response status {status}')
    return body,status,headers

def _request(session,url,**kw):
    response=None
    for attempt in range(3):
        try:
            response=session.get(url,timeout=40,**kw)
            if response.status_code not in (429,500,502,503,504): return response
            response.close()
        except requests.RequestException:
            if attempt==2: raise
        time.sleep(min(8,2**attempt))
    raise OSError('Archive request retries exhausted')

def query_index(index: dict) -> tuple[list[dict],dict]:
    session=requests.Session();session.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical research)'
    url=index['cdx-api']
    response=_request(session,url,params={'url':'bluescholars.com','matchType':'domain','output':'json',
        'filter':'status:200','collapse':'urlkey','fl':FIELDS})
    if response.status_code!=200: raise OSError(f"{index['id']} HTTP {response.status_code}")
    rows=[]
    for line in response.text.splitlines():
        if not line.strip(): continue
        row=json.loads(line)
        if row.get('status')=='200' and row.get('timestamp','').isdigit() and row.get('length','').isdigit(): rows.append(row)
    return rows,{'id':index['id'],'name':index.get('name'),'records':len(rows)}

def fetch_warc(row: dict) -> tuple[dict,bytes,dict]:
    start=int(row['offset']);length=int(row['length'])
    if length<1 or length>30_000_000: raise ValueError('WARC record outside 1..30MB safety limit')
    url='https://data.commoncrawl.org/'+row['filename']
    session=requests.Session();session.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical research)'
    response=_request(session,url,headers={'Range':f'bytes={start}-{start+length-1}'})
    if response.status_code!=206: raise OSError(f'WARC range request returned HTTP {response.status_code}')
    expected=f'bytes {start}-{start+length-1}/'
    if not response.headers.get('Content-Range','').startswith(expected): raise ValueError('WARC response range did not match the requested record')
    body,status,headers=extract_warc_response(response.content)
    kind=kind_for(row['url'],row.get('mime',''))
    validate_payload(body,kind)
    return row,body,{'kind':kind,'headers':headers,'status':status}

def suffix(body:bytes,kind:str)->str:
    if kind=='html':return '.html'
    if kind=='css':return '.css'
    if body.startswith(b'\xff\xd8'):return '.jpg'
    if body.startswith(b'\x89PNG'):return '.png'
    if body.startswith(b'GIF'):return '.gif'
    if body.startswith(b'RIFF'):return '.webp'
    if body.startswith((b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+')):return '.tif'
    return '.svg'

def import_rows(root:Path,collection:str,rows:list[dict])->dict:
    """Fetch WARC rows previously saved from a Common Crawl CDX response."""
    root=Path(root);state=State(root)
    report={'archive':'Common Crawl','collection':collection,'rows':len(rows),
            'attempted_records':0,'recovered_records':0,'failures':[]}
    for row in rows:
        report['attempted_records']+=1
        try:
            row,body,meta=fetch_warc(row)
            url=original_url(row['url']);kind=meta['kind'];sha=hashlib.sha256(body).hexdigest()
            old=state.data['resources'].get(url)
            if old and old.get('sha256')==sha and old.get('actual_capture')==row['timestamp']: continue
            key=url if not (old and old.get('raw_path')) else f"{url}@@commoncrawl:{row['timestamp']}:{sha[:12]}"
            path='recovery/raw/'+sha+suffix(body,kind);dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(body)
            refs=[]
            if kind=='html':refs=discover_html(body.decode('utf-8',errors='replace'),url)
            elif kind=='css':refs=[{'url':u,'kind':kind_for(u),'referrer':url} for u in discover_css(body.decode('utf-8',errors='replace'),url)]
            status='needs_review' if row['timestamp']>state.data['target_capture'] else 'recovered'
            state.data['resources'][key]={'url':url,'kind':kind,'status':status,'raw_path':path,'sha256':sha,
                'bytes':len(body),'actual_capture':row['timestamp'],'final_original':url,'final_url':url,
                'content_type':meta['headers'].get('content-type',row.get('mime','')),'source_archive':'Common Crawl',
                'source_collection':collection,'source_warc':row['filename'],'source_offset':int(row['offset']),
                'source_length':int(row['length']),'source_digest':row.get('digest'),'referrers':['commoncrawl:'+collection],
                'hints':[],'captures':[],'attempts':[],'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            for ref in refs:state.add(ref['url'],ref['kind'],ref['referrer'],row['timestamp'])
            report['recovered_records']+=1
        except Exception as exc:
            report['failures'].append({'url':row.get('url',''),'timestamp':row.get('timestamp'),
                'error':f'{type(exc).__name__}: {exc}'})
    state.save();write_json(root/f'recovery/commoncrawl-{collection}-report.json',report)
    return report

def harvest(root:Path,max_rows:int=1800,workers:int=4)->dict:
    """Fetch domain records from historical snapshots spanning 2008–2023.

    A representative snapshot per year plus the early and 2013 transition
    collections is queried to keep load bounded. Failures are checkpointed per
    collection and row; rerunning safely repeats queries and reuses hashed bodies.
    """
    root=Path(root);state=State(root)
    response=_request(requests.Session(),INDEXES)
    if response.status_code!=200:raise OSError(f'Common Crawl index list HTTP {response.status_code}')
    indexes=json.loads(response.content)
    indexes=[x for x in indexes if x.get('id','').startswith('CC-MAIN-')]
    historical=[];latest_by_year={};special={'CC-MAIN-2008-2009','CC-MAIN-2009-2010','CC-MAIN-2012'}
    for item in indexes:
        identifier=item['id']
        if identifier in special:
            historical.append(item);continue
        match=re.fullmatch(r'CC-MAIN-(20\d\d)-(\d+)',identifier)
        if not match:continue
        year,sequence=map(int,match.groups())
        if not 2013<=year<=2023:continue
        previous=latest_by_year.get(year)
        if previous is None or int(previous['id'].rsplit('-',1)[1])<sequence:latest_by_year[year]=item
    # Include both broad 2013 collections and the late-2023 snapshot in addition
    # to one representative index per year. This avoids flooding a public index
    # service with every quarterly endpoint while retaining temporal coverage.
    historical.extend(latest_by_year.values())
    for item in indexes:
        if item['id'] in ('CC-MAIN-2013-20','CC-MAIN-2013-48','CC-MAIN-2023-40','CC-MAIN-2023-50'):
            if item not in historical:historical.append(item)
    indexes=sorted(historical,key=lambda item:item['id'])
    queried=[];errors=[]
    with ThreadPoolExecutor(max_workers=max(1,min(8,workers))) as pool:
        futures={pool.submit(query_index,x):x for x in indexes}
        for future in as_completed(futures):
            item=futures[future]
            try:
                rows,meta=future.result();queried.append((item,rows));meta['outcome']='indexed'
            except Exception as exc:
                rows=[];queried.append((item,rows));meta={'id':item.get('id'),'outcome':'failed','error':f'{type(exc).__name__}: {exc}'}
            errors.append(meta)
    discovered=[]
    for index,rows in sorted(queried,key=lambda pair:pair[0]['id']):
        for row in rows:
            if in_domain(row.get('url','')) and row.get('mime','').split(';')[0] in ('text/html','text/css','image/jpeg','image/png','image/gif','image/webp','image/svg+xml','image/x-icon','image/vnd.microsoft.icon'):
                discovered.append((index,row))
    # Prefer snapshots throughout the archive, while deduplicating an identical
    # URL/date/content record reported by overlapping indexes.
    unique={}
    for index,row in discovered:
        # Later crawls found the domain compromised/parked. Retain the historical
        # Blue Scholars editions and ignore post-2023 domain takeover material.
        if row.get('timestamp','')>'20231001000000': continue
        unique[(row['url'],row['timestamp'],row['digest'])]=(index,row)
    selected=list(unique.values())[:max_rows]
    report={'archive':'Common Crawl','collections':errors,'query_records':len(discovered),
            'unique_records':len(unique),'attempted_records':0,'recovered_records':0,'failures':[],
            'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    futures=[]
    with ThreadPoolExecutor(max_workers=max(1,min(8,workers))) as pool:
        for index,row in selected: futures.append((index,row,pool.submit(fetch_warc,row)))
        for index,row,future in futures:
            report['attempted_records']+=1
            try:
                row,body,meta=future.result()
                url=original_url(row['url']);kind=meta['kind'];sha=hashlib.sha256(body).hexdigest()
                key=url
                old=state.data['resources'].get(key)
                # A source capture is immutable and each date is kept, including
                # alternates for URLs already recovered from another archive.
                if old and old.get('sha256')==sha and old.get('actual_capture')==row['timestamp']:
                    continue
                store_key=key
                if old and old.get('raw_path'):
                    store_key=f"{key}@@commoncrawl:{row['timestamp']}:{sha[:12]}"
                path='recovery/raw/'+sha+suffix(body,kind);dest=root/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():dest.write_bytes(body)
                refs=[]
                if kind=='html':refs=discover_html(body.decode('utf-8',errors='replace'),url)
                elif kind=='css':refs=[{'url':u,'kind':kind_for(u),'referrer':url} for u in discover_css(body.decode('utf-8',errors='replace'),url)]
                status='needs_review' if row['timestamp']>state.data['target_capture'] else 'recovered'
                record={'url':url,'kind':kind,'status':status,'raw_path':path,'sha256':sha,
                    'bytes':len(body),'actual_capture':row['timestamp'],'final_original':url,
                    'final_url':url,'content_type':meta['headers'].get('content-type',row.get('mime','')),
                    'source_archive':'Common Crawl','source_collection':index['id'],
                    'source_warc':row['filename'],'source_offset':int(row['offset']),
                    'source_length':int(row['length']),'source_digest':row.get('digest'),
                    'referrers':['commoncrawl:'+index['id']],'hints':[],'captures':[],
                    'attempts':[],'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
                if store_key!=key: record['source_key']=store_key
                state.data['resources'][store_key]=record
                for ref in refs:state.add(ref['url'],ref['kind'],ref['referrer'],row['timestamp'])
                report['recovered_records']+=1
            except Exception as exc:
                report['failures'].append({'collection':index['id'],'url':row.get('url',''),
                                           'error':f'{type(exc).__name__}: {exc}'})
            if report['attempted_records']%25==0: state.save();write_json(root/'recovery/commoncrawl-report.json',report)
    state.save();write_json(root/'recovery/commoncrawl-report.json',report)
    return report
