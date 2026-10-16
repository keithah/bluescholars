"""Conservatively merge a downloaded recovery artifact into the local checkpoint."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import time
from .state import State,write_json

def _union(left,right):
    values=list(left or []);seen={json.dumps(v,sort_keys=True,ensure_ascii=False) for v in values}
    for value in right or []:
        marker=json.dumps(value,sort_keys=True,ensure_ascii=False)
        if marker not in seen:values.append(value);seen.add(marker)
    return values

def _variant_key(key,record,run_id):
    archive=str(record.get('source_archive') or 'wayback').lower().replace(' ','-')
    capture=str(record.get('actual_capture') or record.get('source_requested_capture') or 'unknown')
    digest=str(record.get('sha256') or hashlib.sha256((key+run_id).encode()).hexdigest())[:12]
    return f'{key}@@{archive}:{capture}:{digest}'

def _merge_record(current,incoming):
    """Merge evidence fields while keeping a recovered local payload authoritative."""
    merged=deepcopy(current);had_local_raw=bool(current.get('raw_path'))
    has_incoming_raw=bool(incoming.get('raw_path'))
    if has_incoming_raw and not had_local_raw:
        merged.update(deepcopy(incoming))
    elif has_incoming_raw and had_local_raw:
        # Caller has already separated conflicting payloads into variant keys.
        for field in ('actual_capture','sha256','raw_path','bytes','final_url','final_original',
                      'content_type','source_archive','source_collection','source_digest',
                      'source_archive_url','source_warc','source_offset','source_length'):
            if field not in merged and field in incoming:merged[field]=deepcopy(incoming[field])
        merged['status']='needs_review' if 'needs_review' in (current.get('status'),incoming.get('status')) else 'recovered'
    else:
        # Keep local recovered status/content; failures and queued entries add only provenance.
        if current.get('status') not in ('recovered','needs_review') and incoming.get('status') in ('failed','excluded'):
            merged['status']=incoming['status']
    for field in ('captures','referrers','hints','attempts'):
        merged[field]=_union(current.get(field,[]),incoming.get(field,[]))
    if current.get('compatibility_review'):
        merged['compatibility_review']=deepcopy(current['compatibility_review'])
    for field,value in incoming.items():
        if field not in merged and field not in ('raw_path','sha256','actual_capture','status'):
            merged[field]=deepcopy(value)
    return merged

def merge_artifact(root:Path,artifact:Path,run_id:str)->dict:
    """Import raw/index bytes and merge a staged ``archive-recovery`` artifact.

    The artifact is never unpacked over the working tree. Existing files are
    verified and retained; conflicting response bodies become separate records.
    Reports are archived under recovery/imported/<run_id>/ for traceability.
    """
    root=Path(root).resolve();artifact=Path(artifact).resolve()
    staged_state_path=artifact/'recovery/state.json'
    if not staged_state_path.is_file():raise ValueError('Staged artifact has no recovery/state.json')
    if not run_id.isdigit():raise ValueError('Run ID must be numeric')
    incoming=json.loads(staged_state_path.read_text())
    if incoming.get('version')!=1:raise ValueError('Unsupported staged checkpoint version')
    local=State(root);report={'run_id':run_id,'imported_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'artifact':str(artifact),'resources_in_artifact':len(incoming.get('resources',{})),
        'copied_raw_files':0,'copied_index_files':0,'duplicate_files':0,'new_resource_records':0,
        'new_variant_records':0,'merged_records':0,'conflicting_files':[]}
    for relative,counter in (('recovery/raw','copied_raw_files'),('recovery/index','copied_index_files')):
        source=artifact/relative;destination=root/relative
        if not source.exists():continue
        for item in source.rglob('*'):
            if not item.is_file():continue
            target=destination/item.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                left=hashlib.sha256(target.read_bytes()).hexdigest();right=hashlib.sha256(item.read_bytes()).hexdigest()
                if left!=right:
                    report['conflicting_files'].append(str(target.relative_to(root)))
                    # Content-addressed paths should not conflict. Preserve the
                    # artifact under a run-specific sidecar rather than overwrite.
                    target=target.with_name(f'{target.stem}.run-{run_id}{target.suffix}')
                    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=right:
                        raise ValueError(f'Conflicting staged file already exists: {target}')
                    if not target.exists():shutil.copy2(item,target);report[counter]+=1
                else:report['duplicate_files']+=1
            else:shutil.copy2(item,target);report[counter]+=1
    for key,record in incoming.get('resources',{}).items():
        record=deepcopy(record)
        if record.get('raw_path'):
            record.setdefault('source_archive','Internet Archive Wayback')
            record['recovery_run']=run_id
        current=local.data['resources'].get(key)
        if current is None:
            local.data['resources'][key]=record;report['new_resource_records']+=1;continue
        same_payload=(current.get('sha256') and current.get('sha256')==record.get('sha256')
                      and current.get('actual_capture')==record.get('actual_capture'))
        if record.get('raw_path') and current.get('raw_path') and not same_payload:
            variant=_variant_key(key,record,run_id)
            suffix=1;candidate=variant
            while candidate in local.data['resources']:
                old=local.data['resources'][candidate]
                if old.get('sha256')==record.get('sha256') and old.get('actual_capture')==record.get('actual_capture'):break
                suffix+=1;candidate=f'{variant}:{suffix}'
            if candidate not in local.data['resources']:
                local.data['resources'][candidate]=record;report['new_variant_records']+=1
            else:local.data['resources'][candidate]=_merge_record(local.data['resources'][candidate],record)
        else:
            local.data['resources'][key]=_merge_record(current,record);report['merged_records']+=1
    for name,value in incoming.get('index',{}).items():
        existing=local.data.setdefault('index',{}).get(name)
        if existing is None or (not existing.get('complete') and value.get('complete')):
            local.data['index'][name]=deepcopy(value)
    local.data['index_complete']=bool(local.data.get('index_complete') or incoming.get('index_complete'))
    local.data['errors']=_union(local.data.get('errors',[]),incoming.get('errors',[]))
    local.save()
    imported=root/'recovery/imported'/run_id;imported.mkdir(parents=True,exist_ok=True)
    for name in ('report.json','asset-index-report.json','commoncrawl-report.json','arquivo-report.json',
                 'candidate-build-report.json','candidate-check-report.json'):
        source=artifact/'recovery'/name
        if source.is_file():shutil.copy2(source,imported/name)
    write_json(imported/'merge-report.json',report)
    return report
