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


def test_arquivo_domain_index_preserves_latest_capture_per_edition_and_resumes(tmp_path, monkeypatch):
    from restore.arquivo import harvest_domain
    rows = [
        {'url': 'https://bluescholars.com/', 'timestamp': '20191019105504', 'mime': 'text/html',
         'status': '200', 'digest': 'root-old', 'collection': 'AWP30'},
        {'url': 'https://bluescholars.com/', 'timestamp': '20210529010817', 'mime': 'text/html',
         'status': '200', 'digest': 'root-new', 'collection': 'AWP40'},
        {'url': 'https://bluescholars.com/2009/about', 'timestamp': '20120601000000', 'mime': 'text/html',
         'status': '200', 'digest': 'wp', 'collection': 'AWP20'},
        {'url': 'https://bluescholars.com/2009/about', 'timestamp': '20120701000000', 'mime': 'text/html',
         'status': '404', 'digest': 'bad', 'collection': 'AWP20'},
        {'url': 'https://bluescholars.com/image.jpg', 'timestamp': '20200501000000', 'mime': 'image/jpeg',
         'status': '200', 'digest': 'photo', 'collection': 'AWP40'},
        {'url': 'https://unrelated.example/page', 'timestamp': '20200501000000', 'mime': 'text/html',
         'status': '200', 'digest': 'other', 'collection': 'AWP40'},
    ]
    index_body = '\n'.join(json.dumps(row) for row in rows).encode()
    calls = []
    def get(url, params=None, timeout=None, headers=None):
        calls.append((url, params))
        if params:
            assert url == 'https://arquivo.pt/wayback/cdx'
            return Response(index_body, url)
        body = (b'\xff\xd8\xfffixture' if url.endswith('image.jpg') else
                b'<html><head><title>Archive capture</title></head><body>historical text</body></html>')
        return Response(body, url)
    monkeypatch.setattr('restore.arquivo.requests.get', get)

    first = harvest_domain(tmp_path, max_records=1, delay=0)
    assert first['index_rows'] == 6
    assert first['selected_latest_per_url_edition'] == 3
    assert first['attempted_records'] == 1
    assert first['remaining_records'] == 2
    assert len([call for call in calls if call[1]]) == 1

    second = harvest_domain(tmp_path, max_records=5, delay=0)
    assert second['attempted_records'] == 2
    assert second['recovered_records'] == 2
    assert second['remaining_records'] == 0
    assert len([call for call in calls if call[1]]) == 1
    archived = [r for r in State(tmp_path).data['resources'].values()
                if r.get('source_archive') == 'Arquivo.pt']
    assert {r['actual_capture'] for r in archived} == {
        '20210529010817', '20120601000000', '20200501000000'}
    assert all(r['sha256'] and r['source_archive_url'] and r['source_digest'] for r in archived)
    raw_index = tmp_path / 'recovery/index/arquivo-domain.jsonl'
    assert raw_index.read_bytes() == index_body


def test_arquivo_domain_cli_propagates_index_failure(tmp_path, monkeypatch, capsys):
    from restore import __main__ as cli
    monkeypatch.setattr(cli, 'harvest_arquivo_domain',
                        lambda *args: {'archive': 'Arquivo.pt', 'index_error': 'connection refused'})
    code = cli.main(['--root', str(tmp_path), 'arquivo-domain'])
    assert code == 2
    assert json.loads(capsys.readouterr().out)['index_error'] == 'connection refused'
