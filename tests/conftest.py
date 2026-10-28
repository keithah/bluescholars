import pytest

@pytest.fixture(autouse=True)
def isolated_archive_cooldown(tmp_path, monkeypatch):
    # Tests must neither inherit nor clear the user's real shared cooldown.
    monkeypatch.setattr('restore.cooldown.DEFAULT_PATH', tmp_path/'cooldown.json')

@pytest.fixture(autouse=True)
def no_live_http_in_tests(monkeypatch):
    import requests
    from urllib.parse import urlsplit
    original = requests.Session.send
    def blocked(self, request, **kwargs):
        if urlsplit(request.url).hostname in ('127.0.0.1', 'localhost', '::1'):
            return original(self, request, **kwargs)
        raise AssertionError('Live HTTP is disabled in tests; inject a fake session')
    monkeypatch.setattr('requests.Session.send', blocked)
