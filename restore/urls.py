"""URL identity is separate from capture dates and output file locations."""
from __future__ import annotations
import hashlib
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote, parse_qs, quote

TARGET = '20210529010817'
HOME = 'http://bluescholars.com/'
PAGINATION = {'1362122742000': '/blog/page/2/', '1358016466000': '/blog/page/3/'}
REPLAY = re.compile(r'^(?:https?://web\.archive\.org)?/web/(\d{1,14})(?:[a-z]+_)?/(.*)$', re.I)
FONT_EXT = {'.woff','.woff2','.ttf','.otf','.eot'}

def original_url(value: str, base: str = '') -> str:
    value = str(value or '').strip()
    if not value or any(ord(c) < 32 for c in value):
        return ''
    if value.startswith('//web.archive.org/'):
        value='https:'+value
    for _ in range(4):
        match = REPLAY.match(value)
        if not match:
            break
        value = re.sub(r'^(https?)%3[aA]',r'\1:',match.group(2))
    try:
        value = urljoin(base,value)
        parts = urlsplit(value)
        _ = parts.port
    except ValueError:
        return ''
    if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:
        return ''
    if parts.hostname in ('web.archive.org','web-static.archive.org','archive.org'):
        return ''
    return urlunsplit((parts.scheme,parts.netloc.lower(),parts.path or '/',parts.query,''))

def capture_from(url: str) -> str | None:
    match = REPLAY.match(url)
    return match.group(1) if match else None

def is_site(url: str) -> bool:
    return urlsplit(url).hostname in ('bluescholars.com','www.bluescholars.com')

def in_domain(url: str) -> bool:
    host=urlsplit(url).hostname or ''
    return host=='bluescholars.com' or host.endswith('.bluescholars.com')

def identity(url: str) -> str:
    """Unify main-site HTTP/HTTPS and www without discarding query parameters."""
    url=original_url(url)
    if not url:
        return ''
    p=urlsplit(url)
    if is_site(url):
        return urlunsplit(('http','bluescholars.com',p.path.rstrip('/') or '/',p.query,''))
    return url

def kind_for(url: str, mime: str = '') -> str:
    path=urlsplit(url).path.lower()
    ext='.'+path.rsplit('.',1)[-1] if '.' in path.rsplit('/',1)[-1] else ''
    if ext in FONT_EXT or mime.startswith('font/'):
        return 'font'
    if ext in {'.js','.mjs'} or 'javascript' in mime:
        return 'script'
    if ext=='.css' or 'text/css' in mime:
        return 'css'
    if ext in {'.png','.jpg','.jpeg','.gif','.webp','.svg','.ico','.tif','.tiff'} or mime.startswith('image/'):
        return 'image'
    if ext in {'.mp3','.mp4','.m4a','.wav','.ogg','.webm','.mov','.pdf','.zip','.swf'}:
        return 'unsupported'
    if urlsplit(url).hostname=='bluescholars.livejournal.com' and (path in ('','/','/profile') or path.endswith('.html')):
        return 'html'
    if 'html' in mime or in_domain(url):
        return 'html'
    return 'image'  # Assets without extensions need MIME/byte validation on download.

def safe_path(path: str) -> str:
    decoded=unquote(path)
    if '\\' in decoded or any(p in ('.','..') for p in decoded.split('/')):
        raise ValueError(f'Unsafe path: {path}')
    if decoded.count('/') != path.count('/') or '\x00' in decoded:
        raise ValueError(f'Encoded separator in path: {path}')
    return path

def base_path(value: str) -> str:
    value=value.strip()
    if value in ('','/'):
        return ''
    if not value.startswith('/') or value.startswith('//') or '?' in value or '#' in value:
        raise ValueError('Base path must be a local path such as /bluescholars')
    safe_path(value)
    return value.rstrip('/')

def route(url: str) -> str:
    p=urlsplit(url)
    path=p.path or '/'
    safe_path(path)
    # Squarespace exposes some runtime endpoints with comma-joined IDs in a
    # single path segment. They are not real content routes and can exceed a
    # filesystem's per-component filename limit when preserved literally.
    if any(len(unquote(part).encode('utf-8'))>180 for part in path.split('/')):
        key=hashlib.sha256(identity(url).encode()).hexdigest()[:20]
        return '/archive-path/'+key+'/'
    q=parse_qs(p.query,keep_blank_values=True)
    if p.query:
        if path.rstrip('/')=='/blog' and set(q)=={'offset'} and len(q['offset'])==1 and q['offset'][0] in PAGINATION:
            return PAGINATION[q['offset'][0]]
        key=hashlib.sha256(identity(url).encode()).hexdigest()[:20]
        return '/archive-query/'+key+'/'
    if path=='/':
        return '/'
    if path.lower().endswith('/index.html'):
        return path[:-len('index.html')]
    if path.lower().endswith('.html'):
        return path
    return path.rstrip('/')+'/'

def livejournal_route(url: str) -> str | None:
    """Map recovered and missing LiveJournal posts into the separate local archive."""
    url=original_url(url)
    if not url:
        return None
    parts=urlsplit(url)
    if parts.hostname!='bluescholars.livejournal.com':
        return None
    if parts.path in ('','/'):
        return '/lj/journal/'
    if parts.path=='/profile':
        return '/lj/profile/'
    name=parts.path.rsplit('/',1)[-1]
    if not name.endswith('.html'):
        return None
    return '/lj/posts/'+quote(name,safe='.-_')

def asset_route(url: str, kind: str) -> str:
    ext = 'css' if kind=='css' else urlsplit(url).path.rsplit('.',1)[-1].lower()
    if ext not in {'css','jpg','jpeg','png','gif','webp','svg','ico','tif','tiff'}:
        ext='img'
    return '/assets/'+hashlib.sha256(url.encode()).hexdigest()[:24]+'.'+ext
