#!/usr/bin/env python3
"""Recover older Massline image mementos linked to Blue Scholars pages.

Uses the complete saved Massline CDX inventory rather than repeating index
queries. Exact timestamp, URL, CDX SHA-1, local SHA-256 and memento provenance
are retained. Files remain in the local recovery store pending rights review.
"""
from __future__ import annotations
from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse,base64,hashlib,json,time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from restore.archive import validate_payload
from restore.massline import _canonical,_extension,_kind,_write_massline_manifest,_write_massline_report
ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/'recovery/massline/all-captures.json'
MANIFEST=ROOT/'recovery/massline/manifest.json'
OUT=ROOT/'recovery/massline/raw'
TERMS=('bluescholars','blue_scholars','blue-scholars','band_geo','band_saba','longmarchep','bslp2005','rel_bluescholars','bio_bluescholars','bayanipro')
def sha1b(data):return base64.b32encode(hashlib.sha1(data).digest()).decode().rstrip('=')
def candidates():
 rows=json.loads(HISTORY.read_text()).get('rows',[])
 result=[]
 for r in rows:
  u=r.get('original','');path=urlsplit(u).path.lower();mime=r.get('mimetype','').lower()
  if r.get('statuscode')!='200' or not mime.startswith('image/') or '/smf/' in path:continue
  if not any(t in path for t in TERMS):continue
  result.append(r)
 return result
def recover(max_files=50,delay=0.8):
 if max_files<1 or delay<0:raise ValueError('positive max_files and nonnegative delay required')
 m=json.loads(MANIFEST.read_text());variants=m.setdefault('resource_variants',[]);resources=m.setdefault('resources',{})
 seen={(x.get('canonical_url'),x.get('timestamp')) for x in [*resources.values(),*variants] if x.get('status')=='recovered'}
 failed={(x.get('canonical_url'),x.get('timestamp')) for x in m.setdefault('variant_failures',[])}
 todo=[]
 for row in candidates():
  u=_canonical(row['original']);stamp=row.get('timestamp','');key=(u,stamp)
  if key in seen or key in failed:continue
  todo.append((key,row))
 session=RecoverySession();session.headers['User-Agent']='BlueScholarsHistoricalRecovery/0.1 (source preservation)'
 report={'source':'saved uncollapsed masslinemedia.com CDX capture inventory','candidate_rows':len(candidates()),'pending':len(todo),'attempted':0,'recovered':0,'reused':0,'failed':0,'failures':[],'rights_status':'review_required_before_publication'}
 digests={}
 for item in [*resources.values(),*variants]:
  p=ROOT/item.get('raw_path','missing')
  if p.is_file() and item.get('status')=='recovered' and item.get('capture_digest'):
   data=p.read_bytes()
   if sha1b(data)==item['capture_digest'] and hashlib.sha256(data).hexdigest()==item.get('sha256'):
    digests.setdefault(item['capture_digest'],item)
 OUT.mkdir(parents=True,exist_ok=True)
 for (canonical,stamp),row in todo[:max_files]:
  kind=_kind(row);rec={'source_url':row['original'],'canonical_url':canonical,'timestamp':stamp,'mimetype':row['mimetype'],'kind':kind,'cdx_length':row.get('length',''),'capture_digest':row.get('digest'),'source':f"https://web.archive.org/web/{stamp}id_/{row['original']}",'status':'failed','recovery_scope':'older Blue Scholars related image'}
  report['attempted']+=1
  try:
   known=digests.get(row.get('digest')) if row.get('digest') else None
   if known:
    for k in ('raw_path','sha256','bytes','content_type'):rec[k]=known[k]
    rec['reused_digest_from']=known.get('timestamp');rec['cdx_sha1_verified']=True;report['reused']+=1
   else:
    resp=session.get(rec['source'],timeout=(10,60),stream=True);resp.raise_for_status();buf=bytearray()
    for chunk in resp.iter_content(128*1024):
     if chunk:
      buf.extend(chunk)
      if len(buf)>25_000_000:raise ValueError('image exceeded 25 MB cap')
    data=bytes(buf);validate_payload(data,'image')
    if row.get('digest') and sha1b(data)!=row['digest']:raise ValueError('CDX SHA-1 mismatch')
    h=hashlib.sha256(data).hexdigest();path=OUT/f'{h}{_extension(row,kind)}'
    if not path.exists():path.write_bytes(data)
    rec.update({'raw_path':path.relative_to(ROOT).as_posix(),'sha256':h,'bytes':len(data),'content_type':resp.headers.get('Content-Type',''),'cdx_sha1_verified':bool(row.get('digest'))})
    if row.get('digest'):digests[row['digest']]=rec
    report['recovered']+=1
   rec['status']='recovered'
   variants.append(rec);seen.add((canonical,stamp))
  except ArchiveCooldown:
      raise
  except Exception as e:
   rec['error']=f'{type(e).__name__}: {e}';m['variant_failures'].append(rec);report['failed']+=1;report['failures'].append({'url':row['original'],'timestamp':stamp,'error':rec['error']})
  _write_massline_manifest(MANIFEST,m);time.sleep(delay)
 report['remaining']=max(0,len(todo)-report['attempted']);report['unique_payloads']=len({x.get('sha256') for x in variants if x.get('sha256')});m['older_blue_scholars_image_report']=report;_write_massline_manifest(MANIFEST,m);_write_massline_report(ROOT,m.get('report',{}),m);(ROOT/'recovery/massline/older-blue-scholars-images-report.json').write_text(json.dumps(report,indent=2)+'\n');return report
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--max-files',type=int,default=50);ap.add_argument('--delay',type=float,default=.8);a=ap.parse_args();print(json.dumps(recover(a.max_files,a.delay),indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
