import json
import pytest


def test_current_publisher_photos_keep_retrieval_separate_from_event_date(tmp_path):
    from restore.press_archive import build_publisher_photos
    import hashlib
    directory = tmp_path / 'recovery/other-archives/publisher-current'
    directory.mkdir(parents=True)
    image = b'\xff\xd8\xff' + b'photo bytes'
    file = directory / 'photo.jpg'
    file.write_bytes(image)
    record = {'status': 'recovered', 'raw_path': str(file.relative_to(tmp_path)),
              'sha256': hashlib.sha256(image).hexdigest(), 'bytes': len(image),
              'source_url': 'https://publisher.example/photo.jpg'}
    (directory / 'manifest.json').write_text(json.dumps({'pages': [{
        'source_url': 'https://publisher.example/concert', 'title': '2010 concert photos',
        'retrieved_at': '2026-10-28', 'publication_date': '2010-07-28',
        'event_date': '2010-07-25', 'credit': 'Photographer', 'images': [record]}]}))
    out = tmp_path / 'out'
    result = build_publisher_photos(tmp_path, out, '/bluescholars', '/bluescholars/assets/ui.css')
    assert result['image_payloads'] == 1
    page = (out / result['routes'][0].lstrip('/') / 'index.html').read_text()
    assert '2026-10-28' in page and '2010-07-25' in page
    assert 'not Wayback captures' in page
    assert 'Photographer' in page
    assert '/bluescholars/other-archives/press/assets/' in page
    file.write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='hash'):
        build_publisher_photos(tmp_path, out, '', '/assets/ui.css')


def test_publisher_rejects_active_image_documents(tmp_path):
    import hashlib
    from restore.press_archive import build_publisher_photos
    directory = tmp_path / 'recovery/other-archives/publisher-current'
    directory.mkdir(parents=True)
    data = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    path = directory / 'image.jpg'
    path.write_bytes(data)
    (directory / 'manifest.json').write_text(json.dumps({'pages': [{
        'source_url': 'https://publisher.example/photo', 'title': 'Photo',
        'retrieved_at': '2026-10-28', 'images': [{'status': 'recovered',
        'raw_path': str(path.relative_to(tmp_path)), 'sha256': hashlib.sha256(data).hexdigest(),
        'bytes': len(data), 'source_url': 'https://publisher.example/photo.svg'}]}]}))
    with pytest.raises(ValueError, match='Unsupported publisher image'):
        build_publisher_photos(tmp_path, tmp_path / 'out', '', '/assets/ui.css')
