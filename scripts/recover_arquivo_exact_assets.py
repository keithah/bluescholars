#!/usr/bin/env python3
"""Check exact image URLs from recovered pages against Arquivo.pt history.

Every lookup and replay is checkpointed with the page capture that exposed the
URL. Files remain recovery-only; an Arquivo.pt record is not a reuse license.
"""
from __future__ import annotations
from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse, hashlib, json, time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from restore.archive import validate_payload
from scripts.recover_press_archive_pages import article_image_candidates

ROOT=Path(__file__).resolve().parents[1]
PRESS=ROOT/'recovery/other-archives/press-articles/manifest.json'
OUT=ROOT/'recovery/arquivo-pages'
RAW=OUT/'exact-assets-raw'
API='https://arquivo.pt/textsearch'
MAX_BYTES=25_000_000

def recover(source_page='s100.chasejarvis.com/people/bluescholars',max_urls=20,max_files=100,delay=.6):
    if max_urls<1 or max_files<1 or delay<0:raise ValueError('positive limits and nonnegative delay required')
    source=json.loads(PRESS.read_text(encoding='utf-8'))
    candidates={}
    for page in source.get('page_captures',{}).values():
        raw=ROOT/page.get('raw_path','')
        if not raw.is_file():continue
        refs=article_image_candidates(raw.read_bytes(),page.get('original_url',''))
        for url in refs:
            if source_page in page.get('original_url',''):
                candidates.setdefault(url,[]).append({'page_url':page.get('original_url'),'timestamp':page.get('timestamp'),'page_sha256':page.get('sha256')})
    OUT.mkdir(parents=True,exist_ok=True);RAW.mkdir(exist_ok=True)
    mp=OUT/'exact-assets-manifest.json'
    manifest=json.loads(mp.read_text(encoding='utf-8')) if mp.exists() else {'archive':'Arquivo.pt','assets':{}}
    assets=manifest.setdefault('assets',{})
    session=RecoverySession();session.headers['User-Agent']='BlueScholarsHistoricalRecovery/0.1 (archive research)'
    report={'archive':'Arquivo.pt exact image history','source_page_filter':source_page,'candidate_urls':len(candidates),'queried_urls':0,'history_rows':0,'attempted_replays':0,'recovered':0,'failures':[],'not_found':[],'rights_status':'local-only pending rights review'}
    pending=[(url,refs) for url,refs in candidates.items() if url not in assets or assets[url].get('query_error')]
    for url,refs in pending[:max_urls]:
        entry=assets.setdefault(url,{'source_url':url,'source_pages':refs,'history_rows':[]})
        entry['source_pages']=refs
        try:
            response=session.get(API,params={'versionHistory':url,'maxItems':100},timeout=(10,45));response.raise_for_status()
            items=response.json().get('response_items',[])
            entry['history_rows']=items;entry.pop('query_error',None);report['history_rows']+=len(items)
            if not items:entry['status']='no_archived_image_history';report['not_found'].append(url)
            for item in items:
                mime=(item.get('mimeType') or '').split(';',1)[0].lower()
                if item.get('statusCode')!='200' or not mime.startswith('image/'):continue
                replay=item.get('linkToOriginalFile') or ''
                parsed=urlsplit(replay)
                if parsed.scheme!='https' or parsed.hostname not in ('arquivo.pt','www.arquivo.pt'):
                    entry.setdefault('failures',[]).append({'timestamp':item.get('tstamp'),'error':'Rejected replay outside arquivo.pt'});continue
                key=f"{item.get('tstamp')}@@{item.get('digest')}@@{replay}"
                if any(x.get('archive_key')==key and (ROOT/x.get('raw_path','')).is_file() for x in entry.get('payloads',[])):continue
                if report['attempted_replays']>=max_files:break
                report['attempted_replays']+=1
                try:
                    result=session.get(replay,timeout=(10,60),stream=True);result.raise_for_status();body=bytearray()
                    for block in result.iter_content(128*1024):
                        if block:
                            body.extend(block)
                            if len(body)>MAX_BYTES:raise ValueError('image exceeds 25 MB cap')
                    content=bytes(body);validate_payload(content,'image');sha=hashlib.sha256(content).hexdigest()
                    suffix='.jpg' if content.startswith(b'\xff\xd8\xff') else '.png' if content.startswith(b'\x89PNG\r\n\x1a\n') else '.gif' if content.startswith((b'GIF87a',b'GIF89a')) else '.webp'
                    path=RAW/f'{sha}{suffix}'
                    if not path.exists():path.write_bytes(content)
                    entry.setdefault('payloads',[]).append({'archive_key':key,'timestamp':item.get('tstamp'),'archive_url':replay,'mime_type':mime,'archive_digest':item.get('digest'),'archive_length':item.get('contentLength'),'bytes':len(content),'sha256':sha,'raw_path':path.relative_to(ROOT).as_posix(),'source_pages':refs,'digest_semantics':'Arquivo.pt digest retained as supplied; local SHA-256 recorded, no equivalence assumption'})
                    report['recovered']+=1
                except ArchiveCooldown:
                    raise
                except Exception as exc:
                    entry.setdefault('failures',[]).append({'timestamp':item.get('tstamp'),'archive_url':replay,'error':f'{type(exc).__name__}: {exc}'})
                time.sleep(delay)
            report['queried_urls']+=1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            entry['query_error']=f'{type(exc).__name__}: {exc}';report['failures'].append({'url':url,'stage':'history','error':entry['query_error']});report['queried_urls']+=1
        manifest['last_report']=report;mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        time.sleep(delay)
    report['remaining_urls']=max(0,len(pending)-report['queried_urls'])
    report['total_asset_urls']=len(assets);report['total_payload_records']=sum(len(x.get('payloads',[])) for x in assets.values())
    manifest['last_report']=report;mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');(OUT/'exact-assets-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-page',default='s100.chasejarvis.com/people/bluescholars');p.add_argument('--max-urls',type=int,default=20);p.add_argument('--max-files',type=int,default=100);p.add_argument('--delay',type=float,default=.6);a=p.parse_args();print(json.dumps(recover(a.source_page,a.max_urls,a.max_files,a.delay),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
