import json
from pathlib import Path
from types import SimpleNamespace

from restore.arquivo import harvest
from restore.state import State


class Response:
    def __init__(self, payload, url='https://arquivo.pt/textsearch'):
        self.payload = payload
        self.url = url
        self.headers = {'Content-Type': 'text/html'}
        self.content = payload
        self.status_code = 200
    def raise_for_status(self): pass
    def json(self): return self.payload


def test_arquivo_scans_distinct_inventory_pages_and_keeps_source_provenance(tmp_path, monkeypatch):
    state = State(tmp_path)
    state.add('https://bluescholars.com/', 'html', 'seed')
    state.add('https://bluescholars.com/blog/post-one', 'html', 'seed')
    state.add('https://bluescholars.com/blog/post-two', 'html', 'seed')
    state.add('https://images.squarespace-cdn.com/photo.jpg', 'image', 'seed')
    state.save()
    calls = []

    def get(url, params=None, timeout=None):
        if params:
            calls.append(params['versionHistory'])
            capture = '20210529010817'
            body = b'<html><head><title>Archived page</title></head><body>Blue Scholars</body></html>'
            item = {'tstamp': capture, 'originalURL': params['versionHistory'], 'statusCode': 200,
                    'linkToArchive': f'https://arquivo.pt/wayback/{capture}/{params["versionHistory"]}',
                    'linkToOriginalFile': f'https://arquivo.pt/noFrame/replay/{capture}id_/', 'digest': 'fixture',
                    'contentLength': len(body), 'collection': 'fixture'}
            return Response({'response_items': [item]})
        return Response(b'<html><head><title>Archived page</title></head><body>Blue Scholars</body></html>',
                        'https://arquivo.pt/noFrame/replay/20210529010817id_/')

    monkeypatch.setattr('restore.arquivo.requests.get', get)
    report = harvest(tmp_path, history_url='bluescholars.com', max_urls=10, delay=0)
    assert report['queried_urls'] == 3
    assert calls == ['https://bluescholars.com/', 'https://bluescholars.com/blog/post-one',
                     'https://bluescholars.com/blog/post-two']
    assert report['recovered_html'] == 3
    imported = [r for r in State(tmp_path).data['resources'].values()
                if r.get('source_archive') == 'Arquivo.pt']
    assert len(imported) == 3
    assert {r['url'] for r in imported} == set(calls)
    assert all(r['sha256'] and r['source_archive_url'] for r in imported)
    checkpoint = json.loads((tmp_path / 'recovery/arquivo-state.json').read_text())
    assert set(checkpoint['queried_urls']) == set(calls)


def test_arquivo_resumes_without_requerying_successful_urls(tmp_path, monkeypatch):
    state = State(tmp_path)
    state.add('https://bluescholars.com/', 'html', 'seed')
    state.save()
    calls = []
    def get(url, params=None, timeout=None):
        if params:
            calls.append(params.get('versionHistory'))
            return Response({'response_items': []})
        raise AssertionError('No replay is expected for empty history results')
    monkeypatch.setattr('restore.arquivo.requests.get', get)
    first = harvest(tmp_path, max_urls=10, delay=0)
    second = harvest(tmp_path, max_urls=10, delay=0)
    assert first['queried_urls'] == 1
    assert second['queried_urls'] == 0
    assert calls == ['https://bluescholars.com/']
