#!/usr/bin/env python3
"""Preserve openly licensed Blue Scholars photos from Wikimedia Commons.

The API is used to fetch per-file attribution and license metadata. Original
bytes are retained only when the API checksum matches the downloaded payload.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time
from pathlib import Path
from urllib.parse import unquote
import requests
ROOT=Path(__file__).resolve().parents[1]
API='https://commons.wikimedia.org/w/api.php'
CATEGORY='Category:Blue Scholars'
OUT=ROOT/'recovery/other-archives/wikimedia-blue-scholars'
RAW=OUT/'raw'
def clean_html(value):
 from bs4 import BeautifulSoup
 return BeautifulSoup(value or '', 'html.parser').get_text(' ',strip=True)
def recover(delay=.5,max_files=100):
 if delay<0 or max_files<1:raise ValueError('nonnegative delay and positive max_files required')
 OUT.mkdir(parents=True,exist_ok=True);RAW.mkdir(exist_ok=True)
 mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'archive':'Wikimedia Commons','category':CATEGORY,'files':{},'limitations':[]}
 s=requests.Session();s.headers['User-Agent']='BlueScholarsHistoricalRecovery/0.1 (cultural preservation)'
 params={'action':'query','list':'categorymembers','cmtitle':CATEGORY,'cmtype':'file','cmlimit':100,'format':'json'}
 response=s.get(API,params=params,timeout=40);response.raise_for_status();members=response.json().get('query',{}).get('categorymembers',[])
 titles=[x['title'] for x in members]
 source_catalog=json.loads((ROOT/'source/community-media.json').read_text(encoding='utf-8'))
 source_by_url={item.get('commons_url'):item for item in source_catalog.get('items',[])}
 source_by_title={re.sub(r'\.[^.]+$','',item.get('title','')).replace('_',' ').casefold():item for item in source_catalog.get('items',[])}
 report={'category_files_found':len(titles),'metadata_checked':0,'source_catalog_verified':0,'attempted':0,'downloaded_new':0,'skipped_license':0,'rate_limited':False,'failed':[],'new_bytes':0,'limitations':['All 20 category files are already represented in source/community-media.json; this pass verifies them against current Commons metadata and only fetches bytes absent locally.']}
 for start in range(0,len(titles),50):
  batch=titles[start:start+50]
  r=s.get(API,params={'action':'query','titles':'|'.join(batch),'prop':'imageinfo','iiprop':'url|size|sha1|extmetadata','format':'json'},timeout=40);r.raise_for_status()
  pages=r.json().get('query',{}).get('pages',{}).values()
  for page in pages:
   infos=page.get('imageinfo',[])
   if not infos:continue
   info=infos[0];meta=info.get('extmetadata',{});license=clean_html(meta.get('LicenseShortName',{}).get('value',''))
   allowed=clean_html(meta.get('LicenseUrl',{}).get('value',''))
   artist=clean_html(meta.get('Artist',{}).get('value',''))
   credit=clean_html(meta.get('Credit',{}).get('value',''))
   record=m['files'].setdefault(page['title'],{})
   record.update({'title':page['title'],'source_page':info.get('descriptionurl'),'original_url':info.get('url'),'source_repository':'Wikimedia Commons','source_category':CATEGORY,
    'license':license,'license_url':allowed,'artist':artist,'credit':credit,'date_original':clean_html(meta.get('DateTimeOriginal',{}).get('value','')),
    'width':info.get('width'),'height':info.get('height'),'source_bytes':info.get('size'),'source_sha1':info.get('sha1'),'attribution_required':clean_html(meta.get('AttributionRequired',{}).get('value','')).lower()=='true'})
   report['metadata_checked']+=1
   if not license or not allowed or not artist:
    record['status']='metadata_incomplete_not_downloaded';report['skipped_license']+=1;continue
   local_item=(source_by_url.get(info.get('descriptionurl')) or source_by_url.get(record.get('source_page'))
    or source_by_title.get(re.sub(r'\.[^.]+$','',page['title'].removeprefix('File:')).replace('_',' ').casefold()))
   local_path=ROOT/local_item['path'] if local_item and local_item.get('path') else None
   raw_path=record.get('raw_path');dst=ROOT/raw_path if raw_path else None
   if local_path and local_path.is_file():
    body=local_path.read_bytes()
    if len(body)==info.get('size') and hashlib.sha1(body).hexdigest()==info.get('sha1'):
     record.update({'status':'recovered_verified','raw_path':local_item['path'],'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'mediawiki_sha1_verified':True,'reused_from_reviewed_source_catalog':True})
     report['source_catalog_verified']+=1;continue
   if dst and dst.is_file() and hashlib.sha1(dst.read_bytes()).hexdigest()==info.get('sha1'):
    record['status']='recovered_verified';continue
   if report['rate_limited'] or report['attempted']>=max_files:continue
   report['attempted']+=1
   try:
    download=s.get(info['url'],timeout=90)
    if download.status_code==429:
     report['rate_limited']=True
     raise RuntimeError('HTTP 429 from Wikimedia file host; resume after cooldown')
    download.raise_for_status();body=download.content
    if len(body)!=info['size']:raise ValueError(f"size mismatch {len(body)} != {info['size']}")
    digest=hashlib.sha1(body).hexdigest()
    if digest!=info['sha1']:raise ValueError(f"MediaWiki SHA-1 mismatch {digest} != {info['sha1']}")
    name=hashlib.sha256(page['title'].encode()).hexdigest()+Path(unquote(info['url'].split('?')[0])).suffix.lower()
    dest=RAW/name;dest.write_bytes(body)
    record.update({'status':'recovered_verified','raw_path':dest.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'mediawiki_sha1_verified':True})
    report['downloaded_new']+=1;report['new_bytes']+=len(body)
   except Exception as e:
    record.update({'status':'failed','error':f'{type(e).__name__}: {e}'});report['failed'].append({'title':page['title'],'error':record['error']})
   mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
   if delay and not report['rate_limited']:time.sleep(delay)
 m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 lines=['# Wikimedia Commons Blue Scholars photo source','',f"Files discovered in [{CATEGORY}](https://commons.wikimedia.org/wiki/{CATEGORY.replace(' ','_')}): {len(titles)}.",'','The 20 files are already preserved in source/community-media.json. This manifest rechecks per-file attribution, license, dimensions and source SHA-1; reused local bytes must match the current Commons API SHA-1.','']
 for title,rec in sorted(m['files'].items()):
  lines += [f"## {title}",f"- Original date: {rec.get('date_original') or 'not stated'}",f"- Creator: {rec.get('artist') or 'not stated'}",f"- License: [{rec.get('license') or 'not stated'}]({rec.get('license_url') or rec.get('source_page')})",f"- Source: {rec.get('source_page')}",f"- Local record: {rec.get('raw_path') or rec.get('status')}",""]
 (OUT/'README.md').write_text('\n'.join(lines))
 return report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--delay',type=float,default=.5);p.add_argument('--max-files',type=int,default=100);a=p.parse_args();print(json.dumps(recover(a.delay,a.max_files),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
