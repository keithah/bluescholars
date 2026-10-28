#!/usr/bin/env python3
"""Recover exact archived images referenced by Blue Scholars-related sites.

The candidate URLs are extracted from already recovered Prometheus Brown and
MySpace pages. Every exact CDX revision is checkpointed and locally retained
only after image validation and CDX SHA-1 verification.
"""
from __future__ import annotations
from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse, base64, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery/cross-site-assets'
CDX='https://web.archive.org/cdx/search/cdx'
FIELDS='timestamp,original,statuscode,mimetype,digest,length'
IMAGE_EXTS={'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff'}
MAX_BYTES=25_000_000

def sha1(payload:bytes)->str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode('ascii').rstrip('=')

def sources():
    found={}
    # Artist blog content often embeds Blue Scholars original images and MySpace bulletins link the same assets.
    for path in (ROOT/'recovery/artist-sites/raw').glob('*'):
        if path.suffix.lower() not in ('.html','.htm'):continue
        try:soup=BeautifulSoup(path.read_bytes(),'html.parser')
        except ArchiveCooldown:
            raise
        except Exception:continue
        title=soup.title.get_text(' ',strip=True) if soup.title else path.name
        for node in soup.find_all(['img','source']):
            value=node.get('src') or node.get('data-src') or node.get('poster')
            if not value:continue
            u=urljoin('http://prometheusbrown.com/',value);p=urlsplit(u)
            if p.scheme not in ('http','https') or Path(p.path).suffix.lower() not in IMAGE_EXTS:continue
            host=(p.hostname or '').lower()
            # Focus on artist-owned/collaborator imagery and named reference sources, not movie review embeds.
            if not any(token in host for token in ('bluescholars.com','masslinemedia.com','sabzi.co')):continue
            rec=found.setdefault(u,{'original_url':u,'source_pages':[],'alt_texts':[]})
            ref={'title':title,'recovered_file':path.name}
            if ref not in rec['source_pages']:rec['source_pages'].append(ref)
            alt=(node.get('alt') or '').strip()
            if alt and alt not in rec['alt_texts']:rec['alt_texts'].append(alt)
    # Add exact image references present in locally captured MySpace bulletins.
    for path in (ROOT/'recovery/myspace-blue-scholars/raw').glob('*.html'):
        try:soup=BeautifulSoup(path.read_bytes(),'html.parser')
        except ArchiveCooldown:
            raise
        except Exception:continue
        for node in soup.find_all('img'):
            value=node.get('src')
            if not value:continue
            u=urljoin('http://myspace.com/',value);p=urlsplit(u)
            if p.scheme not in ('http','https') or Path(p.path).suffix.lower() not in IMAGE_EXTS:continue
            if not any(h in (p.hostname or '').lower() for h in ('bluescholars.com','masslinemedia.com')):continue
            rec=found.setdefault(u,{'original_url':u,'source_pages':[],'alt_texts':[]})
            ref={'title':'Blue Scholars MySpace bulletin','recovered_file':path.name}
            if ref not in rec['source_pages']:rec['source_pages'].append(ref)
            alt=(node.get('alt') or '').strip()
            if alt and alt not in rec['alt_texts']:rec['alt_texts'].append(alt)
    return found

def recover(max_urls=80,max_files=150,delay=1.0):
    if min(max_urls,max_files)<1 or delay<0:raise ValueError('positive limits and nonnegative delay required')
    OUT.mkdir(parents=True,exist_ok=True);raw=OUT/'raw';raw.mkdir(exist_ok=True)
    mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'version':1,'archive':'Internet Archive Wayback','assets':{}}
    assets=m['assets'];found=sources()
    for u,r in found.items():
        a=assets.setdefault(u,{**r,'cdx_rows':[],'revisions':{}});a['source_pages']=r['source_pages'];a['alt_texts']=r['alt_texts']
    session=RecoverySession();session.headers['User-Agent']='BlueScholarsHistoricalRecovery/0.1 (source preservation)'
    report={'source':'locally recovered Prometheus Brown pages and Blue Scholars MySpace bulletins','candidate_urls':len(found),'queried':0,'index_rows':0,'attempted_replays':0,'recovered_revisions':0,'failures':[],'rate_limited':False,'limitations':['Only exact image URLs embedded in recovered source pages are included.','Third-party/source-linked assets remain local-only pending rights review.','A missing CDX result means no exact URL memento was returned by this query; alternate URL spellings may still exist.']}
    for u,a in list(assets.items())[:max_urls]:
        if a.get('queried_at'):continue
        try:
            r=session.get(CDX,params={'url':u,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':200},timeout=(10,45))
            if r.status_code==429:report['rate_limited']=True;raise RuntimeError('HTTP 429; stopped')
            r.raise_for_status();d=r.json();a['cdx_rows']=d[1:] if d else [];a['queried_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());report['queried']+=1;report['index_rows']+=len(a['cdx_rows'])
        except ArchiveCooldown:
            raise
        except Exception as e:
            a['query_error']=f'{type(e).__name__}: {e}';report['failures'].append({'url':u,'stage':'cdx','error':a['query_error']})
        mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
        if report['rate_limited']:break
    pending=[]
    for u,a in assets.items():
        rows=[r for r in a.get('cdx_rows',[]) if len(r)>=6 and r[2]=='200' and r[3].lower().startswith('image/')]
        groups={}
        for row in rows:groups.setdefault(row[4],[]).append(row)
        for digest,rs in groups.items():
            key=digest
            old=a['revisions'].get(key,{})
            if old.get('sha256') and (ROOT/old.get('raw_path','')).is_file():continue
            pending.append((u,a,key,min(rs,key=lambda r:r[0]),[x[0] for x in rs]))
    for u,a,key,row,timestamps in pending:
        if report['attempted_replays']>=max_files or report['rate_limited']:break
        stamp,original,_,mime,digest,length=row[:6]
        ent={'timestamp':stamp,'original_url':original,'cdx_mime':mime,'cdx_digest':digest,'cdx_length':int(length),'same_digest_timestamps':timestamps,'source_pages':a['source_pages'],'status':'failed'}
        report['attempted_replays']+=1
        try:
            resp=session.get(f'https://web.archive.org/web/{stamp}id_/{original}',timeout=(10,60),stream=True)
            if resp.status_code==429:report['rate_limited']=True;raise RuntimeError('HTTP 429; stopped')
            resp.raise_for_status();buf=bytearray()
            for chunk in resp.iter_content(128*1024):
                if chunk:
                    buf.extend(chunk)
                    if len(buf)>MAX_BYTES:raise ValueError('asset exceeded 25 MB cap')
            body=bytes(buf);validate_payload(body,'image')
            if sha1(body)!=digest:raise ValueError('replay bytes do not match CDX SHA-1')
            h=hashlib.sha256(body).hexdigest();ext=Path(urlsplit(original).path).suffix.lower() or '.bin';dest=raw/f'{h}{ext}'
            if not dest.exists():dest.write_bytes(body)
            ent.update({'status':'recovered','sha256':h,'bytes':len(body),'raw_path':dest.relative_to(ROOT).as_posix(),'cdx_sha1_verified':True,'rights_status':'review_required_before_publication'});report['recovered_revisions']+=1
        except ArchiveCooldown:
            raise
        except Exception as e:ent['error']=f'{type(e).__name__}: {e}';report['failures'].append({'url':u,'timestamp':stamp,'stage':'replay','error':ent['error']})
        a['revisions'][key]=ent;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
    report['candidate_urls_total']=len(assets);report['revision_records']=sum(len(a['revisions']) for a in assets.values());report['unique_payloads']=len({r['sha256'] for a in assets.values() for r in a['revisions'].values() if r.get('sha256')});m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--max-urls',type=int,default=80);ap.add_argument('--max-files',type=int,default=150);ap.add_argument('--delay',type=float,default=1.0);a=ap.parse_args();print(json.dumps(recover(a.max_urls,a.max_files,a.delay),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
