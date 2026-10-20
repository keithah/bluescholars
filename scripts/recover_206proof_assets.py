import sys,json,hashlib,datetime,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from restore.archive import ArchiveClient,validate_payload
from restore.recovery_206proof import resource_identity
from restore.urls import capture_from
root=Path('recovery/206proof'); data=json.loads((root/'asset-index.json').read_text());
def canon(u):
 p=urlsplit(u);host=(p.hostname or '').lower().removeprefix('www.');return (host,p.path,p.query)
# Deduplicate host/protocol aliases, while retaining every original asset reference and candidate capture.
groups={}
for item in data['assets']:
 if not item['captures']:continue
 key=(canon(item['url']),item['kind'])
 g=groups.setdefault(key,{'url':item['url'],'kind':item['kind'],'references':[],'captures':[],'source_urls':[]})
 g['references']+=item['references'];g['captures']+=item['captures'];g['source_urls'].append(item['url'])
for g in groups.values():
 unique={ (r['timestamp'],r['original'],r.get('digest')):r for r in g['captures'] };g['captures']=list(unique.values())
manifest_path=root/'recovered-resources.json';m=json.loads(manifest_path.read_text());seen={resource_identity(r) for r in m['resources']}
queue=[]
for g in groups.values():
 for ref in g['references']:
  ts=ref.get('page_capture') or ''
  if not ts:continue
  # Choose the indexed valid payload closest to the referring page capture.
  def score(r):return (abs(int(r['timestamp'][:8])-int(ts[:8])),0 if r['timestamp']<=ts else 1,r['timestamp'])
  row=min(g['captures'],key=score)
  key=(row['timestamp'],row['original'],g['kind'])
  if key in seen:continue
  queue.append((row,g,ref));seen.add(key)
# one best dependency variant per requested source capture; bounded batch supports retries/resume.
unique=[];got=set()
for x in queue:
 k=(x[0]['timestamp'],canon(x[0]['original']))
 if k not in got:got.add(k);unique.append(x)
client=ArchiveClient(delay=0.6,retries=3,timeout=60,max_bytes=25_000_000);attempted=0
for row,g,ref in unique[:220]:
 kind=g['kind'];p=urlsplit(row['original']); ext=Path(unquote(p.path)).suffix.lower()
 if not ext or not re.fullmatch(r'\.[a-z0-9]{1,8}',ext):ext='.css' if kind=='css' else '.img'
 item={'requested_capture':row['timestamp'],'original':row['original'],'mimetype':row['mimetype'],'statuscode':row['statuscode'],'cdx_digest':row.get('digest'),'indexed_length':row.get('length'),'kind':kind,'source_page':ref['page'],'page_capture':ref['page_capture'],'alternate_source_urls':sorted(set(g['source_urls'])),'attempted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  resp=client.get(f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}");validate_payload(resp.body,kind)
  digest=hashlib.sha256(resp.body).hexdigest();path=root/'raw'/(digest+ext);path.parent.mkdir(parents=True,exist_ok=True)
  if not path.exists():path.write_bytes(resp.body)
  item.update(result='recovered',actual_capture=capture_from(resp.url),resolved_url=resp.url,content_type=resp.headers.get('Content-Type'),bytes=len(resp.body),sha256=digest,raw_path=str(path))
 except Exception as e:item.update(result='failed',error=f'{type(e).__name__}: {e}')
 m['resources'].append(item);attempted+=1
 if attempted%5==0:
  m.update(last_updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempted_this_batch=attempted)
  manifest_path.write_text(json.dumps(m,indent=2)+'\n');print(attempted,item['result'],kind,item['original'],flush=True)
m.update(last_updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempted_this_batch=attempted)
manifest_path.write_text(json.dumps(m,indent=2)+'\n')
from collections import Counter
print('asset batch',attempted,'total resources',len(m['resources']),Counter(r['result'] for r in m['resources']))
