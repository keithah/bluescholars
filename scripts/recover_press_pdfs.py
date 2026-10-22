#!/usr/bin/env python3
"""Recover archive-indexed PDF scans containing Blue Scholars press material."""
from __future__ import annotations
import argparse,base64,hashlib,json,time
from pathlib import Path
import requests
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery/other-archives/press-pdfs'
RAW=OUT/'raw'
CDX='https://web.archive.org/cdx/search/cdx'
FIELDS='timestamp,original,statuscode,mimetype,digest,length'
SOURCES={
 'CMJ 2006 New Music Monthly':'https://www.worldradiohistory.com/Archive-All-Music/CMJ/2006/CMJ-New-Music-2006-152.pdf',
 'Spokane Sidekick May 17, 2007':'https://spocool.com/sidekick/resources/0210-SiDEKiCK_051707_web.pdf',
 'Oberlin Review March 14, 2008':'https://www2.oberlin.edu/stupub/ocreview/2008/03/14/ISSUE.pdf',
 'Pacific Citizen September 2 issue':'https://www.pacificcitizen.org/wp-content/uploads/bsk-pdf-manager/19_SEPT._2_ISSUEWEB.PDF',
 'Billboard July 15, 2006':'https://www.worldradiohistory.com/Archive-All-Music/Billboard/00s/2006/BB-2006-07-15.pdf',
 'Billboard July 7, 2007':'https://www.worldradiohistory.com/Archive-All-Music/Billboard/00s/2007/BB-2007-07-07.pdf',
 'Billboard August 6, 2011':'https://www.worldradiohistory.com/Archive-All-Music/Billboard/00s/2011/BB-2011-08-06.pdf',
}
MAX_BYTES=100_000_000

def sha1b(data):return base64.b32encode(hashlib.sha1(data).digest()).decode().rstrip('=')

def recover(delay=1.0,max_files=20):
 if delay<0 or max_files<1:raise ValueError('positive max_files and nonnegative delay required')
 OUT.mkdir(parents=True,exist_ok=True);RAW.mkdir(exist_ok=True)
 mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'archive':'Internet Archive Wayback','sources':{},'captures':{}}
 s=requests.Session();s.headers['User-Agent']='BlueScholarsHistoricalRecovery/0.1 (publication preservation)'
 report={'archive':'Internet Archive Wayback','sources':len(SOURCES),'queried_sources':0,'capture_rows':0,'attempted':0,'recovered':0,'failures':[],'not_found':[],'rights_status':'third-party magazine/newspaper scans; recovery-only pending rights review'}
 for label,url in SOURCES.items():
  if url not in m['sources'] or m['sources'][url].get('query_error'):
   try:
    r=s.get(CDX,params={'url':url,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':100},timeout=(10,50));r.raise_for_status();rows=r.json();rows=rows[1:] if rows else []
    m['sources'][url]={'url':url,'label':label,'cdx_rows':rows,'queried_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    if not rows:report['not_found'].append(url)
   except Exception as e:
    m['sources'][url]={'url':url,'label':label,'cdx_rows':[],'query_error':f'{type(e).__name__}: {e}'}
    report['failures'].append({'url':url,'stage':'cdx','error':m['sources'][url]['query_error']})
   report['queried_sources']+=1;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
  for row in m['sources'][url].get('cdx_rows',[]):
   if len(row)<6 or row[2]!='200' or row[3].lower()!='application/pdf':continue
   ts,original,status,mime,digest,length=row[:6];key=f'{original}@@{ts}@@{digest}'
   if key in m['captures'] and (ROOT/m['captures'][key].get('raw_path','')).is_file():continue
   if report['attempted']>=max_files:break
   report['attempted']+=1;replay=f'https://web.archive.org/web/{ts}id_/{original}'
   try:
    r=s.get(replay,timeout=(10,90),stream=True);r.raise_for_status();body=bytearray()
    for part in r.iter_content(256*1024):
     if part:
      body.extend(part)
      if len(body)>MAX_BYTES:raise ValueError('PDF exceeds 100 MB cap')
    data=bytes(body);validate_payload(data,'pdf');actual=sha1b(data)
    if digest and actual!=digest:raise ValueError(f'CDX SHA-1 mismatch: {actual} != {digest}')
    sha=hashlib.sha256(data).hexdigest();path=RAW/f'{sha}.pdf'
    if not path.exists():path.write_bytes(data)
    m['captures'][key]={'label':label,'source_url':original,'timestamp':ts,'replay_url':replay,'cdx_mime':mime,'cdx_digest':digest,'cdx_sha1_verified':bool(digest),'cdx_length':int(length),'bytes':len(data),'sha256':sha,'raw_path':path.relative_to(ROOT).as_posix(),'review_required_before_publication':True}
    report['recovered']+=1
   except Exception as e:report['failures'].append({'label':label,'url':original,'timestamp':ts,'error':f'{type(e).__name__}: {e}'})
   report['capture_rows']+=1;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
 report['total_capture_records']=len(m['captures']);report['unique_pdf_payloads']=len({r['sha256'] for r in m['captures'].values()})
 m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--delay',type=float,default=1.0);p.add_argument('--max-files',type=int,default=20);a=p.parse_args();print(json.dumps(recover(a.delay,a.max_files),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
