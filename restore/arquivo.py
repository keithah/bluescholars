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
from .urls import original_url

API='https://arquivo.pt/textsearch'
CHECKPOINT='recovery/arquivo-state.json'

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
