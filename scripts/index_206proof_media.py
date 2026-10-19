import json,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
root=Path('recovery/206proof');m=json.load(open(root/'recovered-resources.json'));leads={};pages=0
patterns=[('youtube',re.compile(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?(?:[^#\s\"\']*?&)?v=)|youtu\.be/)([A-Za-z0-9_-]{6,})',re.I)),('soundcloud',re.compile(r'soundcloud\.com/([A-Za-z0-9_./-]+)',re.I))]
for r in m['resources']:
 if r.get('result')!='recovered' or r.get('kind')!='html':continue
 f=Path(r['raw_path']);
 if not f.exists():continue
 pages+=1; raw=f.read_text(errors='replace'); soup=BeautifulSoup(raw,'html.parser'); text=' '.join([raw]+[str(x.get(a,'')) for x in soup.find_all(True) for a in ('href','src','data','value')])
 for provider,pat in patterns:
  for match in pat.finditer(text):
   mid=match.group(1).rstrip('/'); raw_url=match.group(0).rstrip('"\'<>),;')
   key=(provider,mid);lead=leads.setdefault(key,{'provider':provider,'media_id_or_path':mid,'references':[]}); ref={'page':r['original'],'capture':r.get('actual_capture') or r['requested_capture'],'raw_url':raw_url}
   if ref not in lead['references']:lead['references'].append(ref)
rows=sorted(leads.values(),key=lambda x:(x['provider'],x['media_id_or_path']))
out={'source_pages_scanned':pages,'lead_count':len(rows),'leads':rows}
(root/'media-leads.json').write_text(json.dumps(out,indent=2)+'\n');print('pages',pages,'leads',len(rows),'providers',{p:sum(x['provider']==p for x in rows) for p in ('youtube','soundcloud')})
