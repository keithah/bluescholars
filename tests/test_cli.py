import json
import hashlib
import subprocess
import sys
from pathlib import Path
import yaml
from restore.state import State
from restore.urls import HOME,TARGET

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.run([sys.executable,'-m','restore',*map(str,args)],cwd=ROOT,text=True,capture_output=True)

def test_cli_help():
    r=run('--help')
    assert r.returncode==0 and 'recover' in r.stdout and 'promote' in r.stdout
    assert 'recover-origin-images' in r.stdout

def test_seed_build_check_cli(tmp_path):
    (tmp_path/'recovery/seeds').mkdir(parents=True)
    (tmp_path/'recovery/seeds/inventory.json').write_text((ROOT/'recovery/seeds/inventory.json').read_text())
    r=run('--root',tmp_path,'seed'); assert r.returncode==0,r.stderr
    r=run('--root',tmp_path,'build','--base-path','/bluescholars'); assert r.returncode==0,r.stderr
    report=json.loads(r.stdout);assert report['recovered_pages']==0
    r=run('--root',tmp_path,'check','--base-path','/bluescholars'); assert r.returncode==0,r.stdout+r.stderr
    r=run('--root',tmp_path,'build','--release'); assert r.returncode!=0 and 'review' in r.stderr.lower()

def test_publish_approval_not_implicit(tmp_path):
    r=run('--root',tmp_path,'approve')
    assert r.returncode!=0
    assert not (tmp_path/'source/review.json').exists()

def test_agent_visual_review_can_be_recorded_without_publish_approval(tmp_path):
    from restore.state import write_json
    (tmp_path/'_site').mkdir()
    (tmp_path/'_site/index.html').write_text('<!doctype html><title>Archive</title>')
    evidence=tmp_path/'docs/recovery-report/VISUAL_REVIEW.md'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('Agent-performed inspection with saved comparison screenshots.')
    write_json(tmp_path/'source/review.json',{'visual_reviewed':False,'publish_approved':False})

    result=run('--root',tmp_path,'visual-review','--visual-reviewed')

    assert result.returncode==0,result.stderr
    review=json.loads((tmp_path/'source/review.json').read_text())
    assert review['visual_reviewed'] is True
    assert review['visual_reviewed_by']=='Codex agent'
    assert review['visual_review_evidence']=='docs/recovery-report/VISUAL_REVIEW.md'
    assert review['publish_approved'] is False
    assert review['human_visual_reviewed'] is False

def test_agent_visual_review_requires_built_site_and_evidence(tmp_path):
    result=run('--root',tmp_path,'visual-review','--visual-reviewed')
    assert result.returncode!=0 and 'build' in result.stderr.lower()
    (tmp_path/'_site').mkdir()
    (tmp_path/'_site/index.html').write_text('<!doctype html>')
    result=run('--root',tmp_path,'visual-review','--visual-reviewed')
    assert result.returncode!=0 and 'evidence' in result.stderr.lower()
    assert not (tmp_path/'source/review.json').exists()

def test_approval_records_agent_review_and_user_authorization_truthfully(tmp_path):
    from restore.state import write_json
    from restore.urls import HOME,TARGET
    page=b'<html><head><title>Blue Scholars</title><link rel="stylesheet" href="/site.css"></head><body>Recovered</body></html>'
    css=b'body{color:#222}'
    (tmp_path/'source/raw').mkdir(parents=True)
    (tmp_path/'source/raw/home.html').write_bytes(page)
    (tmp_path/'source/raw/site.css').write_bytes(css)
    write_json(tmp_path/'source/catalog.json',{'version':1,'resources':{
        HOME:{'url':HOME,'kind':'html','status':'recovered','raw_path':'source/raw/home.html',
              'sha256':hashlib.sha256(page).hexdigest(),'actual_capture':TARGET,'source_reviewed':True},
        HOME+'site.css':{'url':HOME+'site.css','kind':'css','status':'recovered','raw_path':'source/raw/site.css',
                         'sha256':hashlib.sha256(css).hexdigest(),'actual_capture':TARGET,'source_reviewed':True}}})

    evidence=tmp_path/'docs/recovery-report/VISUAL_REVIEW.md'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('Agent-performed browser review with saved screenshots.')
    result=run('--root',tmp_path,'approve','--visual-reviewed','--publish-approved')

    assert result.returncode==0,result.stderr
    review=json.loads((tmp_path/'source/review.json').read_text())
    assert review['visual_reviewed'] is True and review['publish_approved'] is True
    assert review['visual_reviewed_by']=='Codex agent'
    assert review['visual_review_evidence']=='docs/recovery-report/VISUAL_REVIEW.md'
    assert review['publish_authorization']=='Conditional publication authorization in CODEX_PROMPT.md'
    assert 'owner' not in review['note'].lower()


def test_approval_requires_existing_in_project_evidence(tmp_path):
    from restore.state import write_json
    from restore.urls import HOME,TARGET
    page=b'<html><head><title>Blue Scholars</title><link rel="stylesheet" href="/site.css"></head><body>Recovered</body></html>'
    css=b'body{color:#222}'
    (tmp_path/'source/raw').mkdir(parents=True)
    (tmp_path/'source/raw/home.html').write_bytes(page)
    (tmp_path/'source/raw/site.css').write_bytes(css)
    write_json(tmp_path/'source/catalog.json',{'version':1,'resources':{
        HOME:{'url':HOME,'kind':'html','status':'recovered','raw_path':'source/raw/home.html',
              'sha256':hashlib.sha256(page).hexdigest(),'actual_capture':TARGET,'source_reviewed':True},
        HOME+'site.css':{'url':HOME+'site.css','kind':'css','status':'recovered','raw_path':'source/raw/site.css',
                         'sha256':hashlib.sha256(css).hexdigest(),'actual_capture':TARGET,'source_reviewed':True}}})

    result=run('--root',tmp_path,'approve','--visual-reviewed','--publish-approved')

    assert result.returncode!=0 and 'evidence' in result.stderr.lower()
    assert not (tmp_path/'source/review.json').exists()

def test_later_capture_review_is_resource_specific(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'image','fixture',TARGET)
    record.update(status='needs_review',actual_capture='20210529010844',sha256='abc123')
    state.save()
    reason='Exact linked homepage asset resolved in the same archive crawl.'
    result=run('--root',tmp_path,'compatibility-review','--url',HOME,'--reason',reason)
    assert result.returncode==0,result.stderr
    saved=State(tmp_path).data['resources'][HOME]['compatibility_review']
    assert saved['actor']=='Codex agent' and saved['reason']==reason
    assert saved['capture']=='20210529010844' and saved['sha256']=='abc123'

def test_recovery_workflow_never_deploys():
    text=(ROOT/'.github/workflows/recover.yml').read_text()
    doc=yaml.safe_load(text)
    assert 'deploy-pages' not in text and 'pages: write' not in text
    assert 'workflow_dispatch' in (doc.get('on') or doc.get(True))
    assert 'if: always()' in text
    assert 'resume_run' in text and 'gh run download' in text
    assert 'recovery_dir="$RUNNER_TEMP/archive-recovery/$run_id"' in text
    assert '--name archive-recovery --dir "$final_dir"' in text
    assert '--name archive-recovery-indexed --dir "$indexed_dir"' in text
    assert '[[ -f "$final_dir/state.json" ]]' in text
    assert 'cp "$final_dir/state.json" "$final_dir/recovery/state.json"' in text
    assert '[[ -f "$indexed_dir/state.json" ]]' in text
    assert 'cp "$indexed_dir/state.json" "$indexed_dir/recovery/state.json"' in text
    assert 'merge-recovery' in text
    assert text.index('name: Preserve archive index before acquisition') < text.index('name: Download and discover dependencies')
    assert text.index('name: Preserve recovery checkpoint and source bytes') < text.index('name: Build a candidate for inspection')

def test_deploy_requires_manual_confirmation_and_release_gate():
    text=(ROOT/'.github/workflows/pages.yml').read_text()
    doc=yaml.safe_load(text)
    assert 'inputs.confirm_publish' in text and '--release' in text
    assert 'deploy-pages@v5' in text
    assert set((doc.get('on') or doc.get(True)))=={'workflow_dispatch'}

def test_shell_scripts_parse():
    for script in (ROOT/'scripts').glob('*.sh'):
        r=subprocess.run(['bash','-n',str(script)],capture_output=True,text=True)
        assert r.returncode==0,r.stderr

def test_preview_server_keeps_base_on_directory_redirect(tmp_path):
    import socket,time
    import requests
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    (tmp_path/'_site/blog').mkdir(parents=True)
    (tmp_path/'_site/index.html').write_text('<html>home</html>')
    (tmp_path/'_site/blog/index.html').write_text('<html>blog</html>')
    proc=subprocess.Popen([sys.executable,'-m','restore','--root',str(tmp_path),'serve','--base-path','/bluescholars','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                response=requests.get(f'http://127.0.0.1:{port}/bluescholars/blog',allow_redirects=False,timeout=1)
                break
            except requests.ConnectionError: time.sleep(.05)
        else: raise AssertionError('Preview server did not start')
        assert response.status_code in (301,302)
        assert response.headers['Location']=='/bluescholars/blog/'
    finally:
        proc.terminate();proc.wait(timeout=5)
