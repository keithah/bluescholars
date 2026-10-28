"""Cross-process Internet Archive cooldown; no requests are made while paused."""
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
import requests


DEFAULT_PATH = Path.home()/'.cache/bluescholars/wayback-cooldown.json'


class ArchiveCooldown(Exception):
    def __init__(self, retry_at):
        self.retry_at = retry_at
        stamp = datetime.fromtimestamp(retry_at, timezone.utc).isoformat()
        super().__init__(f'Internet Archive cooldown until {stamp}; work remains queued for retry')


class Cooldown:
    def __init__(self, path=None, clock=time.time):
        self.path = Path(path) if path is not None else DEFAULT_PATH
        self.clock = clock

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _deadline(self):
        if not self.path.exists(): return 0
        # Fail closed if the shared checkpoint is damaged.
        value = float(json.loads(self.path.read_text())['retry_at'])
        if not math.isfinite(value): raise ValueError('Invalid archive cooldown checkpoint')
        return value

    def check(self):
        with self.locked():
            deadline = self._deadline()
        if deadline > self.clock(): raise ArchiveCooldown(deadline)

    def defer(self, retry_after):
        now = self.clock()
        seconds = 60.0
        try:
            parsed = float(retry_after)
            if math.isfinite(parsed): seconds = max(seconds, parsed)
        except (TypeError, ValueError):
            try:
                seconds = max(seconds, parsedate_to_datetime(retry_after).timestamp()-now)
            except (TypeError, ValueError, AttributeError, OverflowError): pass
        with self.locked():
            deadline = max(self._deadline(), now+seconds)
            temporary = self.path.with_name(self.path.name+f'.{os.getpid()}.tmp')
            temporary.write_text(json.dumps({'retry_at':deadline,'reason':'HTTP 429'})+'\n')
            temporary.replace(self.path)
        return deadline


def archive_host(url):
    host = (urlsplit(url).hostname or '').lower()
    return host == 'archive.org' or host.endswith('.archive.org')


class RecoverySession(requests.Session):
    def __init__(self, cooldown=None):
        super().__init__()
        self.cooldown = cooldown if cooldown is not None else Cooldown()

    def send(self, request, **kwargs):
        guarded = archive_host(request.url)
        if guarded: self.cooldown.check()
        response = super().send(request, **kwargs)
        if guarded and response.status_code == 429:
            try:
                deadline = self.cooldown.defer(response.headers.get('Retry-After'))
            finally:
                response.close()
            raise ArchiveCooldown(deadline)
        return response
