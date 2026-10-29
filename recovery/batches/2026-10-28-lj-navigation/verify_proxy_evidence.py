import json,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
root=Path.cwd();ps=json.load(open('recovery/batches/2026-10-28-lj-navigation/proxy-matches.json'));cat=json.load(open('source/catalog.json'))['resources'];by_hash={r.get('sha256'):r for r in cat.values() if r.get('raw_path')};cache={}
def entries(digest):
 if digest in cache:return cache[digest]
 r=by_hash[digest];raw=(root/r['raw_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 result={}
 for entry in BeautifulSoup(raw,'html.parser').select('.entrycontent'):
  imgs=entry.find_all('img');urls=[im.get('src','') for im in imgs]
  for im in imgs:im['src']='SOURCE_IMAGE'
  result[hashlib.sha256(str(entry).encode()).hexdigest()]=urls
 cache[digest]=result;return result
for p in ps:
 e=p['evidence'];a=entries(e['proxy_page_sha256'])[e['entry_signature']];b=entries(e['original_page_sha256'])[e['entry_signature']]
 assert len(a)==len(b)==e['image_count'];assert a[e['image_index']]==p['url'];assert b[e['image_index']]==p['source_url'];r=by_hash[p['sha256']];assert hashlib.sha256((root/r['raw_path']).read_bytes()).hexdigest()==p['sha256']
print('Verified',len(ps),'proxy mappings against identical entry markup, exact source URLs and image hashes')
