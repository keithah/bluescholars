"""Wayback-only HTTP access with bounded retries and capture validation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import time
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup
from .urls import TARGET

@dataclass
class Payload:
    body: bytes
    url: str
    status: int
    headers: dict

class ArchiveClient:
    def __init__(self,session=None,delay=1.2,retries=3,timeout=30,max_bytes=25_000_000,sleep=time.sleep):
        self.session=session or requests.Session()
        if hasattr(self.session,'headers'):
            self.session.headers.update({'User-Agent':'BlueScholarsRestoration/0.1 (historical site preservation; paced requests)'})
        self.delay=max(0,float(delay));self.retries=max(1,int(retries))
        self.timeout=timeout;self.max_bytes=max_bytes;self.sleep=sleep

    def get(self,url: str) -> Payload:
        for redirect in range(9):
            p=urlsplit(url)
            if p.scheme!='https' or p.hostname!='web.archive.org' or p.username or p.password:
                raise ValueError('Refusing a redirect outside the archive')
            response=None
            for attempt in range(self.retries):
                self.sleep(self.delay)
                try:
                    response=self.session.get(url,timeout=self.timeout,allow_redirects=False,stream=True)
                except requests.RequestException:
                    if attempt+1==self.retries: raise
                    self.sleep(2**attempt);continue
                if response.status_code==429 or 500<=response.status_code<600:
                    wait=self._retry_wait(response.headers.get('Retry-After'),attempt)
                    response.close()
                    if attempt+1==self.retries:
                        raise OSError(f'Archive HTTP {response.status_code}: {url}')
                    self.sleep(wait);continue
                break
            if response is None:
                raise OSError('No archive response')
            if response.status_code in (301,302,303,307,308):
                location=response.headers.get('Location','')
                response.close()
                if not location: raise ValueError('Archive redirect has no Location')
                url=urljoin(url,location)
                # Wayback sometimes emits an HTTP archive redirect. Upgrade only this host.
                if url.startswith('http://web.archive.org/'):
                    url='https://'+url[len('http://'):]
                continue
            if response.status_code!=200:
                response.close()
                raise OSError(f'Archive HTTP {response.status_code}: {url}')
            try:
                body=bytearray()
                for chunk in response.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body)>self.max_bytes:
                        raise ValueError('Archive response exceeds size limit')
                return Payload(bytes(body),url,response.status_code,dict(response.headers))
            finally:
                response.close()
        raise ValueError('Too many archive redirects')

    @staticmethod
    def _retry_wait(value,attempt):
        if value:
            try: return max(0,float(value))
            except ValueError:
                try:
                    return max(0,(parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds())
                except (ValueError,TypeError): pass
        return min(60,2**(attempt+1))

def parse_cdx(text: str) -> tuple[list[dict],str | None]:
    text=text.lstrip()
    try: data,end=json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError as e: raise ValueError('Invalid CDX JSON; index is incomplete') from e
    if data==[]: return [],None
    if not isinstance(data,list) or not data or not isinstance(data[0],list):
        raise ValueError('Invalid CDX header')
    fields=data[0]
    if not {'timestamp','original','mimetype','statuscode'}.issubset(set(fields)):
        raise ValueError('Required CDX fields absent')
    rows=[];resume=None
    for values in data[1:]:
        if values==[]: continue
        if isinstance(values,list) and len(values)==1 and isinstance(values[0],str):
            resume=values[0];continue
        if not isinstance(values,list) or len(values)!=len(fields):
            raise ValueError('Malformed CDX row; index is incomplete')
        row=dict(zip(fields,values))
        if not str(row['timestamp']).isdigit(): raise ValueError('Invalid capture timestamp')
        rows.append(row)
    tail=text[end:].strip()
    if tail:
        try:
            parsed=json.loads(tail)
            if isinstance(parsed,list) and len(parsed)==1: resume=str(parsed[0])
            elif isinstance(parsed,str): resume=parsed
            else: raise ValueError('Malformed CDX resume key')
        except json.JSONDecodeError:
            if '\n' in tail or tail.startswith('<'): raise ValueError('Malformed CDX trailer')
            resume=tail
    return rows,resume

def capture_candidates(record: dict,target: str=TARGET) -> list[str]:
    values=set(record.get('hints',[]))
    for c in record.get('captures',[]):
        if str(c.get('statuscode')) in ('200','301','302','303','307','308'):
            values.add(c['timestamp'])
    before=sorted((v for v in values if v<=target),reverse=True)
    after=sorted(v for v in values if v>target)
    return list(dict.fromkeys([target]+before+after))

def validate_payload(body: bytes,kind: str) -> None:
    if not body: raise ValueError('Empty archive response')
    if kind in ('font','script','unsupported'):
        raise ValueError(f'{kind} files are excluded from recovery output')
    if kind=='image':
        prefix=body.lstrip()[:1000].lower()
        valid=(body.startswith(b'\xff\xd8\xff') or body.startswith(b'\x89PNG\r\n\x1a\n') or
               body.startswith((b'GIF87a',b'GIF89a',b'\x00\x00\x01\x00')) or
               (body.startswith(b'RIFF') and body[8:12]==b'WEBP') or
               (b'<svg' in prefix and b'<html' not in prefix))
        if not valid: raise ValueError('Expected image bytes; received HTML or unknown content')
        return
    text=body.decode('utf-8',errors='replace')
    if kind=='css':
        if '<html' in text.lower() or '<!doctype' in text.lower() or ('{' not in text and '@import' not in text):
            raise ValueError('Expected CSS; received an error or unsupported content')
        return
    if '<html' not in text.lower() and '<!doctype html' not in text.lower():
        raise ValueError('Expected a full HTML document')
    soup=BeautifulSoup(text,'html.parser')
    title=soup.title.get_text(' ',strip=True).lower() if soup.title else ''
    bad=('website expired','account not available','account unavailable','just a moment',
         'service unavailable','page not found','site not found','404 not found','wayback machine')
    body_text=' '.join(soup.get_text(' ',strip=True).lower().split())
    provider_error=('page cannot be displayed' in body_text and 'service provider' in body_text)
    if any(s in title for s in bad) or provider_error or (title.strip()=='error' and 'squarespace' in text.lower()):
        raise ValueError('Captured provider/archive error page, not site content')
