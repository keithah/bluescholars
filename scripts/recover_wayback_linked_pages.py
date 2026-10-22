#!/usr/bin/env python3
"""Cross-check Archive-It discoveries against the Internet Archive Wayback CDX.

The script stores its own query and replay checkpoint. It does not publish any
third-party page; each memento stays in recovery-only storage with both archive
provenances recorded.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit
import requests
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery/wayback-related'
CDX='https://web.archive.org/cdx/search/cdx'
FIELDS='timestamp,original,statuscode,mimetype,digest,length'
MAX_BYTES=25_000_000

def relevant(record):
    direct=' '.join(str(record.get(k,'')) for k in ('title','original_url')).casefold()
    if any(x in direct for x in ('blue scholar','bluescholar','prometheusbrown','prometheus brown','sabzi of blue scholars','geologic')):
        return True
    snippet=str(record.get('result_text','')).casefold()
    return any(x in snippet for x in ('blue scholars film contest finalist','blue scholars inkwell','blue scholars "slick watts"','pays homage to the seattle based hip-hop duo blue scholars'))

def nearest(rows, target):
    rows=[r for r in rows if len(r)>5 and r[2]=='200' and r[3].lower() in ('text/html','application/xhtml+xml')]
    if not rows:return []
    def distance(r):
        try:return abs(int(r[0])-int(target))
        except (ValueError,TypeError):return 10**30
    return [min(rows,key=distance)]

def recover(max_urls=120,max_files=100,delay=.5):
    if max_urls<1 or max_files<1 or delay<0:raise ValueError('limits must be positive and delay nonnegative')
    OUT.mkdir(parents=True,exist_ok=True);raw=(OUT/'raw');raw.mkdir(parents=True,exist_ok=True)
    mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'version':1,'indexes':{},'captures':{}}
    indexes=m.setdefault('indexes',{});captures=m.setdefault('captures',{})
    files=sorted((ROOT/'recovery/archiveit').glob('search-results*.json'))
    candidates={}
    for p in files:
        if not p.exists():continue
        for page in json.loads(p.read_text()):
            for r in page.get('records',[]):
                if not relevant(r):continue
                u=str(r.get('original_url',''))
                parsed=urlsplit(u)
                if parsed.scheme not in ('http','https') or not parsed.netloc:continue
                rec=candidates.setdefault(u,{'original_url':u,'source_captures':[],'titles':[],'queries':[]})
                rec['source_captures'].append({'timestamp':r.get('timestamp'),'collection_id':r.get('collection_id'),'replay_url':r.get('replay_url')})
                if r.get('title') not in rec['titles']:rec['titles'].append(r.get('title'))
                if r.get('query') not in rec['queries']:rec['queries'].append(r.get('query'))
    def priority(rec):
        s=(rec['original_url']+' '+' '.join(rec['titles'])).casefold()
        terms=('youtube.com/user/bluescholars','youtube.com/watch','kexp.org','npr.org','mtv.com','seattlechannel.org','filmandmusic.seattle.gov','jamglue.com/contests/bluescholars','twitter.com/bluescholars','myspace.com/bluescholars')
        return min((i for i,t in enumerate(terms) if t in s),default=len(terms)),rec['original_url']
    ordered=sorted(candidates.values(),key=priority)[:max_urls]
    session=requests.Session();session.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical preservation)'
    report={'archive':'Internet Archive Wayback CDX','discovery_source':'All saved Archive-It search-result files','candidate_urls_total':len(candidates),'candidate_urls_queried':0,'index_rows':0,'urls_with_html_mementos':0,'attempted_replays':0,'recovered_payloads':0,'failures':[],'limitations':['This cross-check covers relevant original URLs found in saved Archive-It search-result files; unsaved ranges are not included.','One nearest dated HTML memento is selected per URL; other Wayback revisions remain indexed in this checkpoint.','Third-party pages remain recovery-only pending relevance and rights review.']}
    for rec in ordered:
        url=rec['original_url']
        if url not in indexes:
            report['candidate_urls_queried']+=1
            try:
                resp=session.get(CDX,params={'url':url,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':200},timeout=(8,35));resp.raise_for_status()
                data=resp.json();rows=data[1:] if data else []
                good=[row for row in rows if len(row)>5 and row[2]=='200' and row[3].lower() in ('text/html','application/xhtml+xml')]
                indexes[url]={**rec,'cdx_rows':rows,'html_mementos':len(good),'queried_at':datetime.utcnow().isoformat()+'Z'}
                report['index_rows']+=len(rows)
                if good:report['urls_with_html_mementos']+=1
                mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
            except Exception as e:
                indexes[url]={**rec,'cdx_rows':[],'query_error':f'{type(e).__name__}: {e}'}
                report['failures'].append({'url':url,'stage':'cdx','error':indexes[url]['query_error']})
                mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay);continue
        idx=indexes[url];rows=idx.get('cdx_rows',[])
        if not rows:continue
        # Choose the memento closest in time to the Archive-It observation.
        target=(rec.get('source_captures') or [{}])[0].get('timestamp','')
        selected=nearest(rows,target)
        for row in selected:
            key=f'{row[1]}@@wayback:{row[0]}:{row[4]}'
            if key in captures and (ROOT/captures[key].get('raw_path','')).is_file():continue
            if report['attempted_replays']>=max_files:break
            report['attempted_replays']+=1
            replay=f'https://web.archive.org/web/{row[0]}id_/{row[1]}'
            try:
                response=session.get(replay,timeout=(8,45),stream=True);response.raise_for_status()
                body=bytearray()
                for chunk in response.iter_content(128*1024):
                    body.extend(chunk)
                    if len(body)>MAX_BYTES:raise ValueError('memento exceeded 25 MB limit')
                payload=bytes(body);validate_payload(payload,'html');digest=hashlib.sha256(payload).hexdigest()
                path=f'recovery/wayback-related/raw/{digest}.html';dest=ROOT/path
                if not dest.exists():dest.write_bytes(payload)
                captures[key]={'original_url':row[1],'timestamp':row[0],'cdx_mime':row[3],'cdx_digest':row[4],'cdx_length':row[5],'sha256':digest,'bytes':len(payload),'mime':response.headers.get('Content-Type',''),'raw_path':path,'source_archive':'Internet Archive Wayback','matched_archiveit_records':rec['source_captures'],'matched_titles':rec['titles'],'review_required_before_publication':True}
                report['recovered_payloads']+=1
            except Exception as e:report['failures'].append({'url':row[1],'timestamp':row[0],'stage':'replay','error':f'{type(e).__name__}: {e}'})
            mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
            time.sleep(delay)
        time.sleep(delay)
    report['candidate_urls_queried']=len(indexes)
    report['index_rows']=sum(len(r.get('cdx_rows',[])) for r in indexes.values())
    report['urls_with_html_mementos']=sum(bool(r.get('html_mementos')) for r in indexes.values())
    report['capture_records_total']=len(captures);report['unique_payloads_total']=len({r['sha256'] for r in captures.values()})
    m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--max-urls',type=int,default=120);ap.add_argument('--max-files',type=int,default=100);ap.add_argument('--delay',type=float,default=.5);a=ap.parse_args()
    print(json.dumps(recover(a.max_urls,a.max_files,a.delay),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
