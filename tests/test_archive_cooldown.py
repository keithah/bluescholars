import pytest
import requests
from restore.cooldown import ArchiveCooldown, Cooldown, RecoverySession

class Reply:
    status_code = 429
    headers = {'Retry-After': '120'}
    def close(self): self.closed = True

def test_429_stops_and_blocks_other_sessions_until_deadline(tmp_path, monkeypatch):
    clock = [1000.0]
    gate = Cooldown(tmp_path/'gate.json', clock=lambda: clock[0])
    calls=[]
    reply=Reply()
    monkeypatch.setattr(requests.Session, 'send', lambda self, request, **kw: calls.append(request.url) or reply)
    a=RecoverySession(cooldown=gate)
    with pytest.raises(ArchiveCooldown) as caught: a.get('https://web.archive.org/web/20200101000000/http://example.com/')
    assert caught.value.retry_at == 1120
    assert reply.closed
    b=RecoverySession(cooldown=Cooldown(tmp_path/'gate.json', clock=lambda: clock[0]))
    with pytest.raises(ArchiveCooldown): b.get('https://archive.org/wayback/available?url=example.com')
    assert len(calls)==1
    clock[0]=1121
    gate.check()

def test_minimum_cooldown_and_never_shortens(tmp_path):
    gate=Cooldown(tmp_path/'gate.json', clock=lambda:1000)
    assert gate.defer('2')==1060
    assert gate.defer('180')==1180
    assert gate.defer(None)==1180

def test_other_hosts_unaffected(tmp_path, monkeypatch):
    gate=Cooldown(tmp_path/'gate.json', clock=lambda:1000)
    gate.defer(None)
    monkeypatch.setattr(requests.Session,'send',lambda *a,**k:Reply())
    assert RecoverySession(cooldown=gate).get('https://publisher.example/image.jpg').status_code==429


def test_cooldown_is_visible_in_another_process(tmp_path):
    import subprocess, sys
    gate=Cooldown(tmp_path/'gate.json')
    gate.defer('120')
    code="from restore.cooldown import Cooldown, ArchiveCooldown; import sys\ntry: Cooldown(sys.argv[1]).check()\nexcept ArchiveCooldown: sys.exit(75)\n"
    result=subprocess.run([sys.executable,'-c',code,str(gate.path)],capture_output=True)
    assert result.returncode==75


def test_retry_after_date_and_invalid_values(tmp_path):
    gate=Cooldown(tmp_path/'gate.json',clock=lambda:1000)
    assert gate.defer('Thu, 01 Jan 1970 00:20:00 GMT')==1200
    assert gate.defer('NaN')==1200
    assert gate.defer('not-a-date')==1200
