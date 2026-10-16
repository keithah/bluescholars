import hashlib
import json
from pathlib import Path

from restore.merge import merge_artifact
from restore.state import State,write_json


def _record(root:Path,url:str,body:bytes,capture:str,status='recovered'):
    digest=hashlib.sha256(body).hexdigest();path=f'recovery/raw/{digest}.html'
    dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
    return {'url':url,'kind':'html','status':status,'raw_path':path,'sha256':digest,
            'bytes':len(body),'actual_capture':capture,'source_archive':'Internet Archive Wayback',
            'referrers':['fixture'] if status=='recovered' else [],'hints':[],'captures':[],'attempts':[]}


def test_merge_imports_new_records_and_preserves_conflicting_captures(tmp_path):
    local=tmp_path/'local';artifact=tmp_path/'stage';local.mkdir();artifact.mkdir()
    first='https://bluescholars.com/blog/post'
    state=State(local);state.data['resources'][first]=_record(local,first,b'<html>local</html>','20210529000000');state.save()
    incoming={'version':1,'index_complete':True,'index':{'domain':{'complete':True,'pages':4}},
              'resources':{first:_record(artifact,first,b'<html>new capture</html>','20120701000000'),
                           'https://bluescholars.com/old/':_record(artifact,'https://bluescholars.com/old/',b'<html>old page</html>','20120601000000')}}
    write_json(artifact/'recovery/state.json',incoming)
    (artifact/'recovery/index').mkdir(parents=True)
    (artifact/'recovery/index/index-row.json').write_text('{"capture":true}\n')
    (artifact/'recovery/report.json').write_text(json.dumps({'resource_urls':2}))

    report=merge_artifact(local,artifact,'123456')
    merged=State(local).data
    assert report['new_resource_records']==1 and report['new_variant_records']==1
    assert len([key for key in merged['resources'] if key.startswith(first+'@@')])==1
    assert merged['resources'][first]['actual_capture']=='20210529000000'
    assert merged['resources']['https://bluescholars.com/old/']['actual_capture']=='20120601000000'
    assert merged['index_complete'] is True
    assert (local/'recovery/index/index-row.json').read_text()=='{"capture":true}\n'
    assert (local/'recovery/imported/123456/report.json').is_file()


def test_merge_does_not_downgrade_local_recovery_with_artifact_failure(tmp_path):
    local=tmp_path/'local';artifact=tmp_path/'stage';local.mkdir();artifact.mkdir()
    url='https://bluescholars.com/'
    state=State(local);state.data['resources'][url]=_record(local,url,b'<html>good</html>','20210529000000');state.save()
    failed={'url':url,'kind':'html','status':'failed','attempts':[{'requested_capture':'20210529000000','result':'failed'}]}
    write_json(artifact/'recovery/state.json',{'version':1,'resources':{url:failed},'index':{},'errors':[]})
    merge_artifact(local,artifact,'987654')
    result=State(local).data['resources'][url]
    assert result['status']=='recovered'
    assert result['raw_path']=='recovery/raw/'+hashlib.sha256(b'<html>good</html>').hexdigest()+'.html'
    assert result['attempts']==failed['attempts']
