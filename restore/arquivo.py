"""Import independently archived Arquivo.pt captures into the recovery checkpoint."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time
import requests
from .archive import validate_payload
from .discover import discover_html
from .state import State,write_json
from .urls import original_url

API='https://arquivo.pt/textsearch'

def harvest(root:Path,history_url:str='bluescholars.com')->dict:
    root=Path(root);state=State(root)
    response=requests.get(API,params={'versionHistory':history_url,'maxItems':100},timeout=30)
    response.raise_for_status();items=response.json().get('response_items',[])
    report={'archive':'Arquivo.pt','queried_history_url':history_url,'captures_found':len(items),
            'successful_http_captures':0,'recovered_html':0,'failures':[],'captures':[]}
    for item in items:
        capture=item.get('tstamp','');original=original_url(item.get('originalURL',''))
        row={'timestamp':capture,'original_url':original,'statusCode':item.get('statusCode'),
             'linkToArchive':item.get('linkToArchive'),'linkToOriginalFile':item.get('linkToOriginalFile'),
             'digest':item.get('digest'),'contentLength':item.get('contentLength'),'collection':item.get('collection')}
        report['captures'].append(row)
        if str(item.get('statusCode'))!='200' or not original or not capture.isdigit():continue
        report['successful_http_captures']+=1
        try:
            page=requests.get(item['linkToOriginalFile'],timeout=30)
            page.raise_for_status();body=page.content
            validate_payload(body,'html')
            digest=hashlib.sha256(body).hexdigest();path='recovery/raw/'+digest+'.html'
            dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(body)
            key=f'{original}@@arquivo:{capture}:{digest[:12]}'
            if key not in state.data['resources']:
                state.data['resources'][key]={'url':original,'kind':'html','status':'recovered',
                    'raw_path':path,'sha256':digest,'bytes':len(body),'actual_capture':capture,
                    'final_original':original,'final_url':page.url,'content_type':page.headers.get('Content-Type','text/html'),
                    'source_archive':'Arquivo.pt','source_collection':item.get('collection'),
                    'source_digest':item.get('digest'),'source_archive_url':item.get('linkToOriginalFile'),
                    'referrers':['arquivo:versionHistory'],'hints':[],'captures':[],'attempts':[],
                    'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
                for ref in discover_html(body.decode('utf-8',errors='replace'),original):
                    state.add(ref['url'],ref['kind'],ref['referrer'],capture)
            report['recovered_html']+=1
        except Exception as exc:
            report['failures'].append({'url':original,'timestamp':capture,'error':f'{type(exc).__name__}: {exc}'})
    state.save();write_json(root/'recovery/arquivo-report.json',report)
    return report
