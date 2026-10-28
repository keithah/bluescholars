#!/usr/bin/env python3
"""Resume exact publisher image URLs in the saved, source-linked inventory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from restore.cooldown import ArchiveCooldown, RecoverySession
from restore.archive import validate_payload


def recover(root, max_files=25, retry_failed=False, delay=.7):
    path = root / 'recovery/other-archives/publisher-current/manifest.json'
    manifest = json.loads(path.read_text())
    report = {'attempted': 0, 'recovered': 0, 'failed': 0, 'rate_limited': False}
    for page in manifest['pages']:
        for image in page.get('images', []):
            if report['attempted'] >= max_files or report['rate_limited']:
                break
            if image.get('status') == 'recovered' or (image.get('status') == 'failed' and not retry_failed):
                continue
            report['attempted'] += 1
            attempt = {'at': datetime.now(timezone.utc).isoformat(), 'url': image['source_url']}
            try:
                with RecoverySession().get(image['source_url'], timeout=(10, 25), stream=True) as response:
                    if response.status_code == 429:
                        report['rate_limited'] = True
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_content(65536):
                        body.extend(chunk)
                        if len(body) > 25_000_000:
                            raise ValueError('Image exceeds 25 MB limit')
                    body = bytes(body)
                    validate_payload(body, 'image')
                    digest = hashlib.sha256(body).hexdigest()
                    suffix = '.png' if body.startswith(b'\x89PNG') else '.gif' if body.startswith(b'GIF') else '.jpg'
                    destination = path.parent / 'raw' / (digest + suffix)
                    destination.parent.mkdir(exist_ok=True)
                    destination.write_bytes(body)
                    image.update(status='recovered', sha256=digest, bytes=len(body),
                                 raw_path=destination.relative_to(root).as_posix(),
                                 resolved_url=response.url, content_type=response.headers.get('Content-Type'))
                    attempt['result'] = 'recovered'
                    report['recovered'] += 1
            except ArchiveCooldown:
                raise
            except Exception as exc:
                image.update(status='failed', error=f'{type(exc).__name__}: {exc}')
                attempt.update(result='failed', error=image['error'])
                report['failed'] += 1
            image.setdefault('attempts', []).append(attempt)
            path.write_text(json.dumps(manifest, indent=2) + '\n')
            if not report['rate_limited']:
                time.sleep(delay)
    manifest['last_image_recovery'] = report
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-files', type=int, default=25)
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()
    if args.max_files < 1:
        parser.error('max-files must be positive')
    print(json.dumps(recover(Path(__file__).resolve().parents[1], args.max_files, args.retry_failed), indent=2))
