#!/usr/bin/env python3
"""Recover archived image dependencies from the new Wayback HTML mementos."""
from __future__ import annotations
from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'recovery/wayback-related-assets';CDX='https://web.archive.org/cdx/search/cdx';FIELDS='timestamp,original,statuscode,mimetype,digest,length';MAX_BYTES=25_000_000

def suffix(url):
 s=Path(urlsplit(url).path).suffix.lower()
 return s if s in ('.jpg','.jpeg','.png','.gif','.webp','.bmp') else ''

def collect():
 manifest=json.loads((ROOT/'recovery/wayback-related/manifest.json').read_text())
 leads={}
 pages=list(manifest['captures'].values())
 # Revision captures expose older MySpace profile image URLs and later
 # Squarespace image dependencies that are absent from a single page sample.
 versions_path=ROOT/'recovery/wayback-versions/manifest.json'
 if versions_path.exists():
  versions=json.loads(versions_path.read_text())
  pages.extend(versions.get('revisions',{}).values())
 for page in pages:
  path=ROOT/page['raw_path']
  if not path.exists():continue
  soup=BeautifulSoup(path.read_bytes(),'html.parser')
  page_title=' '.join(soup.title.get_text(' ',strip=True).split()) if soup.title else ''
  refs=[]
  for node in soup.find_all(['img','source']):
   for attr in ('src','data-src','data-original','data-image','poster'):
    if node.get(attr):refs.append((node[attr],node.get('alt','')))
   for attr in ('srcset','data-srcset'):
    for part in (node.get(attr) or '').split(','):
     if part.strip():refs.append((part.strip().split()[0],node.get('alt','')))
  for node in soup.select('meta[property="og:image"],meta[name="twitter:image"],meta[property="twitter:image"]'):
   if node.get('content'):refs.append((node['content'],node.get('alt','')))
  for value,alt in refs:
   u=urljoin(page['original_url'],value);p=urlsplit(u)
   if p.scheme not in ('http','https') or not p.netloc or not suffix(u):continue
   if any(x in u.lower() for x in ('pixel','spacer','tracking','1x1')):continue
   item=leads.setdefault(u,{'original_url':u,'referrers':[],'alt_texts':[]})
   item['referrers'].append({'page_url':page['original_url'],'page_timestamp':page['timestamp'],'page_title':(page.get('matched_titles') or [page_title])[0]})
   if alt and alt not in item['alt_texts']:item['alt_texts'].append(alt)
 return leads

def filter_leads(leads,source_contains='',alt_contains=''):
 source_contains=source_contains.casefold();alt_contains=alt_contains.casefold()
 return {url:item for url,item in leads.items()
         if (not source_contains or any(source_contains in ref.get('page_url','').casefold()
                                        for ref in item.get('referrers',[])))
         and (not alt_contains or any(alt_contains in alt.casefold()
                                      for alt in item.get('alt_texts',[])))}

def recover(max_urls=50,max_files=50,delay=.6,source_contains='',alt_contains=''):
 if max_urls<1 or max_files<1 or delay<0:raise ValueError('limits must be positive and delay nonnegative')
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'raw').mkdir(exist_ok=True)
 mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'version':1,'indexes':{},'assets':{}}
 indexes=m.setdefault('indexes',{});assets=m.setdefault('assets',{});leads=filter_leads(collect(),source_contains,alt_contains)
 ordered=sorted(leads.values(),key=lambda x:('blue scholar' not in ' '.join(x['alt_texts']+[(x['referrers'][0].get('page_title') or '') for _ in (0,)]).casefold(),x['original_url']))[:max_urls]
 session=RecoverySession();session.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical preservation)'
 report={'archive':'Internet Archive Wayback','source':'image references in recovery/wayback-related and recovery/wayback-versions HTML captures','source_url_filter':source_contains or None,'alt_text_filter':alt_contains or None,'candidate_images_total':len(leads),'candidate_images_queried':0,'index_rows':0,'images_with_mementos':0,'attempted':0,'recovered':0,'failures':[],'limitations':['Only image URLs explicitly referenced by the newly acquired HTML pages were considered.','At most one image memento nearest each referring HTML capture was selected.','Some image references may be third-party decorations or unrelated page assets; raw files remain review-only.']}
 for lead in ordered:
  url=lead['original_url']
  if url not in indexes:
   try:
    resp=session.get(CDX,params={'url':url,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':100},timeout=(8,35))
    if resp.status_code==429:
     report['failures'].append({'url':url,'stage':'cdx','error':'HTTP 429; stopped to respect Wayback rate limit'});break
    resp.raise_for_status();d=resp.json();rows=d[1:] if d else []
    good=[r for r in rows if len(r)>5 and r[2]=='200' and r[3].lower().startswith('image/')]
    indexes[url]={'cdx_rows':rows,'image_mementos':len(good),'referrers':lead['referrers'],'alt_texts':lead['alt_texts']}
    report['candidate_images_queried']+=1;report['index_rows']+=len(rows);report['images_with_mementos']+=bool(good)
    mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
   except ArchiveCooldown:
       raise
   except Exception as e:
    indexes[url]={'cdx_rows':[],'image_mementos':0,'referrers':lead['referrers'],'error':f'{type(e).__name__}: {e}'}
    report['failures'].append({'url':url,'stage':'cdx','error':indexes[url]['error']});mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay);continue
  rows=[r for r in indexes[url].get('cdx_rows',[]) if len(r)>5 and r[2]=='200' and r[3].lower().startswith('image/')]
  if not rows:continue
  target=lead['referrers'][0].get('page_timestamp','')
  row=min(rows,key=lambda r:abs(int(r[0])-int(target)) if str(r[0]).isdigit() and str(target).isdigit() else 10**30)
  key=f"{row[1]}@@wayback:{row[0]}:{row[4]}"
  if key in assets and (ROOT/assets[key].get('raw_path','')).is_file():continue
  if report['attempted']>=max_files:break
  report['attempted']+=1;replay=f'https://web.archive.org/web/{row[0]}id_/{row[1]}'
  try:
   r=session.get(replay,timeout=(8,45),stream=True)
   if r.status_code==429:
    report['failures'].append({'url':row[1],'timestamp':row[0],'stage':'replay','error':'HTTP 429; stopped to respect Wayback rate limit'});break
   r.raise_for_status();body=bytearray()
   for chunk in r.iter_content(128*1024):
    body.extend(chunk)
    if len(body)>MAX_BYTES:raise ValueError('image memento exceeded 25 MB')
   content=bytes(body);validate_payload(content,'image');digest=hashlib.sha256(content).hexdigest();ext=suffix(row[1]) or '.bin'
   rel=f'recovery/wayback-related-assets/raw/{digest}{ext}';dest=ROOT/rel
   if not dest.exists():dest.write_bytes(content)
   assets[key]={'original_url':row[1],'timestamp':row[0],'cdx_mime':row[3],'cdx_digest':row[4],'sha256':digest,'bytes':len(content),'mime':r.headers.get('Content-Type',''),'raw_path':rel,'source_archive':'Internet Archive Wayback','referrers':lead['referrers'],'alt_texts':lead['alt_texts'],'review_required_before_publication':True};report['recovered']+=1
  except ArchiveCooldown:
      raise
  except Exception as e:report['failures'].append({'url':row[1],'timestamp':row[0],'stage':'replay','error':f'{type(e).__name__}: {e}'})
  mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
 report['index_records_total']=len(indexes);report['asset_records_total']=len(assets);report['unique_payloads_total']=len({x['sha256'] for x in assets.values()})
 m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--max-urls',type=int,default=50);p.add_argument('--max-files',type=int,default=50);p.add_argument('--delay',type=float,default=.6);p.add_argument('--source-url-contains',default='');p.add_argument('--alt-contains',default='');a=p.parse_args();print(json.dumps(recover(a.max_urls,a.max_files,a.delay,a.source_url_contains,a.alt_contains),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
