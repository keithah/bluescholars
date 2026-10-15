import json
import subprocess
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.run([sys.executable,'-m','restore',*map(str,args)],cwd=ROOT,text=True,capture_output=True)

def test_cli_help():
    r=run('--help')
    assert r.returncode==0 and 'recover' in r.stdout and 'promote' in r.stdout

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

def test_recovery_workflow_never_deploys():
    text=(ROOT/'.github/workflows/recover.yml').read_text()
    doc=yaml.safe_load(text)
    assert 'deploy-pages' not in text and 'pages: write' not in text
    assert 'workflow_dispatch' in (doc.get('on') or doc.get(True))
    assert 'if: always()' in text
    assert 'resume_run' in text and 'gh run download' in text

def test_deploy_requires_manual_confirmation_and_release_gate():
    text=(ROOT/'.github/workflows/pages.yml').read_text()
    doc=yaml.safe_load(text)
    assert 'inputs.confirm_publish' in text and '--release' in text
    assert 'deploy-pages@v4' in text
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
