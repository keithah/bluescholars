import importlib.util
import json
import hashlib
import pytest
from pathlib import Path


@pytest.mark.parametrize('digest_state', ['valid', 'missing', 'mismatch'])
def test_reused_verified_image_is_recorded_as_recovered(tmp_path, monkeypatch, digest_state):
    path = Path(__file__).resolve().parents[1] / 'scripts/recover_massline_older_images.py'
    spec = importlib.util.spec_from_file_location('older_images', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = tmp_path / 'raw/image.jpg'
    raw.parent.mkdir()
    raw.write_bytes(b'existing verified payload')
    digest = module.sha1b(raw.read_bytes()) if digest_state == 'valid' else ('WRONG' if digest_state == 'mismatch' else None)
    monkeypatch.setattr(module.requests.Session, 'get', lambda *a, **k: (_ for _ in ()).throw(ValueError('download needed')))
    manifest = tmp_path / 'recovery/massline/manifest.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'resources': {'image': {
        'status': 'recovered', 'capture_digest': digest, 'raw_path': 'raw/image.jpg',
        'timestamp': '20060101000000', 'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(), 'bytes': raw.stat().st_size,
        'content_type': 'image/jpeg'}}, 'resource_variants': []}))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'MANIFEST', manifest)
    monkeypatch.setattr(module, 'OUT', raw.parent)
    monkeypatch.setattr(module, '_write_massline_report', lambda *args: None)
    monkeypatch.setattr(module, 'candidates', lambda: [{
        'original': 'http://masslinemedia.com/images/band_geo.jpg', 'timestamp': '20070101000000',
        'mimetype': 'image/jpeg', 'digest': digest, 'length': '25', 'statuscode': '200'}])
    result = module.recover(max_files=1, delay=0)
    if digest_state != 'valid':
        assert result['reused'] == 0
        assert result['failed'] == 1
        assert not json.loads(manifest.read_text())['resource_variants']
        return
    assert result['reused'] == 1
    assert json.loads(manifest.read_text())['resource_variants'][0]['status'] == 'recovered'
