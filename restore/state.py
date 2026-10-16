"""Human-readable checkpoints; raw responses remain separate and immutable."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from .urls import original_url,TARGET,HOME

def write_json(path: Path,data) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write('\n');f.flush();os.fsync(f.fileno())
    temp.replace(path)

class State:
    def __init__(self,root: Path):
        self.root=Path(root)
        self.path=self.root/'recovery/state.json'
        self.data=json.loads(self.path.read_text()) if self.path.exists() else {
            'version':1,'target_capture':TARGET,'reference_url':HOME,
            'index_complete':False,'index':{},'resources':{},'errors':[]}
        if self.data.get('version')!=1:
            raise ValueError('Unsupported checkpoint version')

    def add(self,url: str,kind: str,referrer: str='',capture: str='') -> dict | None:
        url=original_url(url)
        if not url: return None
        r=self.data['resources'].setdefault(url,{
            'url':url,'kind':kind,'referrers':[],'hints':[],'captures':[],
            'status':'queued','attempts':[]})
        for key,value in (('referrers',referrer),('hints',capture)):
            if value and value not in r[key]: r[key].append(value)
        # Explicit stylesheet references and known file extensions can correct
        # an older MIME/extension guess before bytes exist. Never change an
        # acquired payload's validated type.
        path=urlsplit(url).path.lower()
        extension='.'+path.rsplit('.',1)[-1] if '.' in path.rsplit('/',1)[-1] else ''
        image_ext={'.png','.jpg','.jpeg','.gif','.webp','.svg','.ico','.tif','.tiff'}
        other_ext={'.woff','.woff2','.ttf','.otf','.eot','.js','.mjs','.mp3','.mp4','.m4a',
                   '.wav','.ogg','.webm','.mov','.pdf','.zip','.swf'}
        if (kind=='css' or (kind=='image' and extension in image_ext)
                or (kind in ('font','script','unsupported') and extension in other_ext)) \
                and not r.get('raw_path') and r.get('status') in ('queued','failed'):
            r['kind']=kind
        return r

    def save(self) -> None:
        write_json(self.path,self.data)

    def seed(self) -> None:
        inventory=json.loads((self.root/'recovery/seeds/inventory.json').read_text())
        for page in inventory['pages']:
            self.add(page['original_url'],'html','seed',page['capture'])
        for asset in inventory.get('assets',[]):
            if asset.get('original_url'):
                self.add(asset['original_url'],'image',asset.get('parent','seed'),asset.get('capture_request',TARGET))
        self.save()
