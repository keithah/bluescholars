import gzip
from restore.commoncrawl import extract_warc_response


def test_extract_warc_response_from_range_record():
    payload=b'<html><body>archived</body></html>'
    warc=(b'WARC/1.0\r\nWARC-Type: response\r\nContent-Length: '
          +str(len(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')+len(payload)).encode()
          +b'\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'+payload+b'\r\n\r\n')
    body,status,headers=extract_warc_response(gzip.compress(warc))
    assert body==payload
    assert status==200
    assert headers['content-type']=='text/html'


def test_reject_bad_warc_response():
    import pytest
    with pytest.raises(ValueError): extract_warc_response(b'not a WARC response')


def test_extract_old_arc_record():
    payload=b'<html>older crawl</html>'
    arc=(b'http://example.com/ 127.0.0.1 20090101000000 text/html '
         +str(len(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')+len(payload)).encode()
         +b'\nHTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'+payload)
    body,status,headers=extract_warc_response(gzip.compress(arc))
    assert body==payload and status==200

def test_commoncrawl_capture_after_reference_is_held_for_review(tmp_path,monkeypatch):
    from restore import commoncrawl
    from restore.state import State
    url='http://bluescholars.com/blog/old-post/'
    row={'url':url,'timestamp':'20230927103524','filename':'crawl.warc.gz',
         'offset':'100','length':'200','digest':'sha1:fixture','mime':'text/html'}
    body=b'<html><body><h1>Captured post</h1></body></html>'
    monkeypatch.setattr(commoncrawl,'fetch_warc',lambda value:(value,body,
        {'kind':'html','headers':{'content-type':'text/html'}}))

    commoncrawl.import_rows(tmp_path,'CC-MAIN-2023-40',[row])

    assert State(tmp_path).data['resources'][url]['status']=='needs_review'
