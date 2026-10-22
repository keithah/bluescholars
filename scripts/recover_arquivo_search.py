#!/usr/bin/env python3
"""Search Arquivo.pt full text and preserve relevant dated Blue Scholars pages.

Search responses and accepted HTML remain recovery-only, with query, URL, date,
archive URL, digest, and local hash recorded for each response.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery/arquivo-search'
API='https://arquivo.pt/textsearch'
QUERIES=('"Blue Scholars"','"Prometheus Brown"','Sabzi "Blue Scholars"',
         'Blue Scholars MySpace','Blue Scholars Massline','Blue Scholars LiveJournal',
         'Blue Scholars forum')
MAX_BYTES=20_000_000

def related(item):
    title=str(item.get('title') or '').casefold()
    url=str(item.get('originalURL') or '').casefold()
    snippet=str(item.get('snippet') or '').casefold()
    # Arquivo.pt's broad phrase ranking includes SEO pages which scrape the
    # band name into unrelated MP3/cheat pages. Preserve the search response,
    # but do not treat those pages as relevant recovery candidates.
    if (any(term in title for term in ('free ', ' mp3', 'cheats', 'remove blur', 'download', 'keygen', 'crack'))
            and not any(term in title for term in ('blue scholar', 'bluescholar', 'prometheus brown', 'geologic', 'sabzi'))):
        return False
    primary=('blue scholar' in title or 'bluescholar' in url or 'blue-scholar' in url
             or 'prometheus brown' in title or 'sabzi' in title)
    contextual=('blue scholars' in snippet and any(x in snippet for x in
        ('prometheus brown','sabzi','geologic','blue scholars band','seattle hip-hop')))
    return primary or contextual

def update_aggregate_summary(manifest, current_report):
    """Recompute durable counts from all saved ranked-query responses."""
    import glob
    response_pages={}
    leads={}
    for name in glob.glob(str(OUT/'query-results*.json')):
        if name.endswith('-failed-initial.json'):
            continue
        try: batches=json.loads(Path(name).read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError): continue
        for page in batches:
            query=page.get('query');number=page.get('page')
            if query is None or number is None: continue
            response_pages[(query,number)]=page
            for item in page.get('items',[]):
                if related(item) and item.get('linkToOriginalFile') and item.get('mimeType','').lower().split(';')[0] in ('text/html','application/xhtml+xml'):
                    key=f"{item.get('originalURL')}@@arquivo:{item.get('tstamp','')}:{item.get('digest','')}"
                    leads.setdefault(key,item)
    captures=manifest.get('captures',{})
    old_path=OUT/'summary.json'
    prior=json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    failures={ (x.get('url'),x.get('timestamp'),x.get('error')):x for x in prior.get('failures',[]) }
    for failure in current_report.get('failures',[]):
        failures[(failure.get('url'),failure.get('timestamp'),failure.get('error'))]=failure
    records=[value for value in captures.values() if value.get('relevance_review')!='false_positive']
    summary={
        'archive':'Arquivo.pt Full Text Search','endpoint':API,'queries':len({q for q,_ in response_pages}),
        'highest_page_examined':max((number for _,number in response_pages),default=0),
        'saved_query_pages':len(response_pages),
        'search_rows':sum(len(page.get('items',[])) for page in response_pages.values()),
        'unique_relevant_html_candidates':len(leads),
        'validated_html_capture_records':len(records),
        'unique_payload_hashes':len({value.get('sha256') for value in records if value.get('sha256')}),
        'unresolved_candidate_records':sum(key not in captures for key in leads),
        'excluded_false_positive_capture_records':sum(value.get('relevance_review')=='false_positive' for value in captures.values()),
        'failures':list(failures.values()),'local_manifest':'recovery/arquivo-search/manifest.json',
        'query_result_files':[Path(name).relative_to(ROOT).as_posix() for name in sorted(glob.glob(str(OUT/'query-results*.json')))],
        'limitations':['This is a ranked, bounded full-text search, not an export of the complete Arquivo.pt index.','The saved query pages are a sample, not an exhaustive index export.','Search snippets and relevance filters yield false positives. Captured third-party pages remain raw recovery-only data pending content and rights review.'],
        'capture_attempts_total':int(prior.get('capture_attempts_total',0))+int(current_report.get('attempted',0)),
    }
    old_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return summary

def recover(limit=100,delay=0.6,pages=3,start_page=1,queries=None):
    if limit<1 or delay<0 or pages<1 or start_page<1: raise ValueError('limit, pages and start_page must be positive and delay nonnegative')
    OUT.mkdir(parents=True,exist_ok=True)
    session=requests.Session();session.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical preservation)'
    mp=OUT/'manifest.json';manifest=json.loads(mp.read_text()) if mp.exists() else {'version':1,'captures':{}}
    captures=manifest.setdefault('captures',{}); response_pages=[]; leads={}
    report={'archive':'Arquivo.pt Full Text Search','endpoint':API,'queries':[], 'search_rows':0,
            'relevant_candidates':0,'attempted':0,'recovered':0,'failures':[],
            'limitations':['This is a ranked, bounded full-text search, not an export of the complete Arquivo.pt index.',
                           'Only valid archived HTML is saved; third-party content remains recovery-only pending source/reuse review.']}
    selected_queries=queries or QUERIES
    for query in selected_queries:
        next_url=API
        params={'q':query,'maxItems':50,'prettyPrint':'true','from':'20000101000000','to':'20261231235959'}
        if start_page>1: params['offset']=str((start_page-1)*50)
        for page in range(start_page,start_page+pages):
            try:
                resp=session.get(next_url,params=params if page==start_page else None,timeout=(10,45));resp.raise_for_status();data=resp.json()
                rows=data.get('response_items',[]);report['search_rows']+=len(rows)
                page_rows=[]
                for item in rows:
                    entry={**item,'query':query,'page':page};page_rows.append(entry)
                    if related(item) and item.get('linkToOriginalFile') and item.get('mimeType','').lower().split(';')[0] in ('text/html','application/xhtml+xml'):
                        url=str(item['originalURL']);stamp=str(item.get('tstamp') or '');dig=str(item.get('digest') or '')
                        key=f'{url}@@arquivo:{stamp}:{dig}'
                        leads.setdefault(key,entry)
                response_pages.append({'query':query,'page':page,'next_page':data.get('next_page'),'estimated_nr_results':data.get('estimated_nr_results'),'items':page_rows})
                report['queries'].append({'query':query,'page':page,'rows':len(rows),'estimated_nr_results':data.get('estimated_nr_results')})
                next_url=data.get('next_page')
                if not next_url or len(rows)==0: break
                parsed=urlsplit(next_url)
                if parsed.scheme!='https' or parsed.hostname not in ('arquivo.pt','www.arquivo.pt'):
                    raise ValueError('Rejected next page outside arquivo.pt')
                time.sleep(delay)
            except Exception as exc:
                report['queries'].append({'query':query,'page':page,'error':f'{type(exc).__name__}: {exc}'})
                break
    if queries:
        query_tag=hashlib.sha256('\n'.join(selected_queries).encode()).hexdigest()[:12]
        result_name=f'query-results-custom-{query_tag}-pages-{start_page}-{start_page+pages-1}.json'
    else:
        result_name='query-results.json' if start_page==1 else f'query-results-pages-{start_page}-{start_page+pages-1}.json'
    (OUT/result_name).write_text(json.dumps(response_pages,indent=2,ensure_ascii=False)+'\n')
    report['relevant_candidates']=len(leads)
    for key,item in leads.items():
        if key in captures and (ROOT/captures[key].get('raw_path','')).is_file(): continue
        if report['attempted']>=limit: break
        replay=str(item['linkToOriginalFile']);parsed=urlsplit(replay)
        if parsed.scheme!='https' or parsed.hostname not in ('arquivo.pt','www.arquivo.pt'):
            report['failures'].append({'url':item.get('originalURL'),'timestamp':item.get('tstamp'),'error':'Rejected replay outside arquivo.pt'});continue
        report['attempted']+=1
        try:
            resp=session.get(replay,timeout=(10,45),stream=True);resp.raise_for_status();body=bytearray()
            for chunk in resp.iter_content(128*1024):
                body.extend(chunk)
                if len(body)>MAX_BYTES:raise ValueError('HTML response exceeded 20 MB limit')
            content=bytes(body);validate_payload(content,'html');digest=hashlib.sha256(content).hexdigest()
            rel=f'recovery/arquivo-search/raw/{digest}.html';target=ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_bytes(content)
            captures[key]={**item,'raw_path':rel,'sha256':digest,'bytes':len(content),'kind':'html',
                           'mime':resp.headers.get('Content-Type',''),'source_archive':'Arquivo.pt',
                           'review_required_before_publication':True}
            report['recovered']+=1
        except Exception as exc:report['failures'].append({'url':item.get('originalURL'),'timestamp':item.get('tstamp'),'title':item.get('title'),'error':f'{type(exc).__name__}: {exc}'})
        time.sleep(delay)
        manifest['last_report']=report;mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    report['capture_records']=len(captures);report['unique_payloads']=len({x['sha256'] for x in captures.values()})
    manifest['last_report']=report;mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    update_aggregate_summary(manifest,report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int,default=100);parser.add_argument('--delay',type=float,default=.6);parser.add_argument('--pages',type=int,default=3);parser.add_argument('--start-page',type=int,default=1);parser.add_argument('--query',action='append',help='search only this query (repeatable); defaults to all saved query families');args=parser.parse_args()
    print(json.dumps(recover(args.limit,args.delay,args.pages,args.start_page,args.query),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
