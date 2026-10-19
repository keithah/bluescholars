import json,hashlib,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlsplit
from collections import defaultdict
from restore.discover import discover_html,discover_css
base=Path('recovery/206proof'); m=json.loads((base/'recovered-resources.json').read_text()); cdx=json.loads((base/'all-events-all-status.json').read_text())['rows']
by=defaultdict(list)
for r in cdx:
 if r.get('statuscode')!='200' or r.get('mimetype') not in ('text/css','image/jpeg','image/png','image/gif','image/webp','image/svg+xml'):
  continue
 try:p=urlsplit(r['original']); host=(p.hostname or '').lower().removeprefix('www.')
 except ValueError: continue
 by[(host,p.path,p.query)].append(r)
assets={}; pages=0; malformed=0
for x in m['resources']:
 if x.get('result')!='recovered' or x.get('kind')!='html':continue
 path=Path(x['raw_path']);
 if not path.exists():continue
 pages+=1; txt=path.read_text(errors='replace'); refs=[]
 try: refs=discover_html(txt,x['original'])
 except Exception: pass
 for st in []: pass
 for ref in refs:
  u=ref['url'];
  try:p=urlsplit(u); host=(p.hostname or '').lower().removeprefix('www.')
  except ValueError: malformed+=1; continue
  if host!='206proof.com': continue
  kind=ref.get('kind')
  if kind not in ('css','image'):continue
  key=(host,p.path,p.query,kind)
  a=assets.setdefault(key,{'url':u,'kind':kind,'references':[],'captures':[]})
  a['references'].append({'page':x['original'],'page_capture':x.get('actual_capture') or x.get('requested_capture')})
  a['captures'].extend(by.get((host,p.path,p.query),[]))
for a in assets.values():
 unique={(r['timestamp'],r['original']):r for r in a['captures']};a['captures']=sorted(unique.values(),key=lambda r:r['timestamp'],reverse=True)
idx={'query':'References extracted from validated recovered 206proof HTML; captures matched against all-status CDX rows','source_pages_scanned':pages,'malformed_references':malformed,'assets':list(assets.values())}
(base/'asset-index.json').write_text(json.dumps(idx,indent=2)+'\n')
print('pages scanned',pages,'assets',len(assets),'with successful CDX',sum(bool(a['captures']) for a in assets.values()),'without',sum(not a['captures'] for a in assets.values()),'references',sum(len(a['references']) for a in assets.values()),'malformed',malformed)
