"""Human-readable checkpoints; raw responses remain separate and immutable."""
from __future__ import annotations
import json
import os
from pathlib import Path
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
        # Type declarations in markup are better evidence than an extension guess.
        if kind=='css': r['kind']='css'
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
