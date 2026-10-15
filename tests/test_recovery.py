import json
from pathlib import Path
import pytest
from restore.archive import parse_cdx, validate_payload, ArchiveClient, Payload, capture_candidates
from restore import recover as recovery
from restore.recover import index, recover, resource_priority, capture_variant,capture_era
from restore.state import State
from restore.urls import HOME, TARGET

HEADER=['timestamp','original','mimetype','statuscode','digest']
VALID=b'<html><head><title>BLUE SCHOLARS</title></head><body><a href="/blog">Blog</a></body></html>'

def test_cdx_resume_inside_json():
    text=json.dumps([HEADER,['20200101000000',HOME,'text/html','200','D'],[],['next%21']])
    rows,key=parse_cdx(text)
    assert len(rows)==1 and key=='next%21'
    assert rows[0]['original']==HOME

def test_cdx_resume_after_json():
    rows,key=parse_cdx(json.dumps([HEADER])+ '\n\n'+json.dumps(['next']))
    assert rows==[] and key=='next'

@pytest.mark.parametrize('text',['<html>maintenance</html>','{}','[["wrong"],["row"]]'])
def test_invalid_cdx_not_complete(text):
    with pytest.raises(ValueError): parse_cdx(text)

@pytest.mark.parametrize('body',[
 b'<html><title>Website Expired</title><body>Squarespace</body></html>',
 b'<html><title>Squarespace - Account Not Available</title></html>',
 b'<html><title>Just a moment...</title></html>',
 b'<html><title>Error</title><body>Squarespace</body></html>',
])
def test_provider_error_with_200_rejected(body):
    with pytest.raises(ValueError): validate_payload(body,'html')

def test_real_content_with_error_word_not_rejected():
    validate_payload(b'<html><title>BLUE SCHOLARS</title><p>Error is the song name</p></html>','html')

def test_untitled_provider_error_capture_rejected():
    body=b'<html><body>Error. Page cannot be displayed. Please contact your service provider for more details. (18)</body></html>'
    with pytest.raises(ValueError,match='provider/archive error'):
        validate_payload(body,'html')

def test_html_masquerading_as_image_rejected():
    with pytest.raises(ValueError): validate_payload(VALID,'image')

def test_font_download_forbidden():
    with pytest.raises(ValueError): validate_payload(b'wOF2xxx','font')

def test_rank_before_reference_first():
    r={'url':HOME,'hints':['20200101000000'],'captures':[
      {'timestamp':'20250101000000','statuscode':'200'},
      {'timestamp':'20210401000000','statuscode':'200'},
      {'timestamp':'20160101000000','statuscode':'302'}]}
    ranked=capture_candidates(r)
    assert ranked[0]==TARGET
    assert ranked.index('20210401000000') < ranked.index('20250101000000')
    assert '20160101000000' in ranked

def test_core_pages_and_linked_dependencies_outrank_full_domain_legacy_css():
    homepage={'url':HOME,'kind':'html','referrers':['seed']}
    core_css={'url':'https://static1.squarespace.com/site.css','kind':'css',
              'referrers':['http://bluescholars.com/']}
    legacy_css={'url':'http://bluescholars.com/blog/wp-content/theme.css','kind':'css',
                'referrers':['CDX:domain']}
    assert resource_priority(homepage)[0] < resource_priority(core_css)[0]
    assert resource_priority(core_css)[0] < resource_priority(legacy_css)[0]

def test_article_pages_outrank_tag_filters_for_complete_blog_recovery():
    article={'url':HOME+'blog/bringing-back-the-og-t-shirt','kind':'html',
             'referrers':[HOME+'blog/']}
    tag={'url':HOME+'blog/?tag=Seattle','kind':'html','referrers':['CDX:domain']}
    assert resource_priority(article)[0] < resource_priority(tag)[0]

def test_final_squarespace_permalink_outranks_dated_wordpress_posts():
    squarespace={'url':HOME+'blog/bringing-back-the-og-t-shirt-in-green-and-gold-if',
                 'kind':'html','referrers':[HOME+'blog/']}
    wordpress={'url':HOME+'blog/2013/05/13/old-wordpress-post/',
               'kind':'html','referrers':['CDX:domain']}
    assert resource_priority(squarespace)[0] < resource_priority(wordpress)[0]

def test_squarespace_article_media_outranks_unlinked_legacy_assets():
    inline={'url':'https://media.tumblr.com/inline-photo.jpg','kind':'image',
            'referrers':[HOME+'blog/bringing-back-the-og-t-shirt-in-green-and-gold-if']}
    legacy={'url':HOME+'blog/wp-content/uploads/2012/01/old-photo.jpg',
            'kind':'image','referrers':['CDX:domain']}
    assert resource_priority(inline)[0] < resource_priority(legacy)[0]

def test_old_wordpress_media_is_not_treated_as_a_homepage_dependency():
    inline={'url':'https://media.tumblr.com/inline-photo.jpg','kind':'image',
            'referrers':[HOME+'blog/']}
    wordpress={'url':HOME+'blog/wp-content/uploads/2010/11/legacy.jpg','kind':'image',
               'referrers':[HOME]}
    assert resource_priority(inline)[0] < resource_priority(wordpress)[0]

class Response:
    def __init__(self,code=200,body=VALID,headers=None):
        self.status_code=code;self.body=body;self.headers=headers or {}
    def iter_content(self,chunk_size): yield self.body
    def close(self): pass

class Session:
    def __init__(self,responses): self.responses=list(responses);self.calls=[]
    def get(self,url,**kw):
        self.calls.append((url,kw))
        item=self.responses.pop(0)
        if isinstance(item,Exception): raise item
        return item

def test_retry_after_respected():
    waits=[];s=Session([Response(429,headers={'Retry-After':'7'}),Response()])
    c=ArchiveClient(session=s,delay=0,sleep=waits.append)
    assert c.get('https://web.archive.org/web/'+TARGET+'id_/'+HOME).body==VALID
    assert 7 in waits and len(s.calls)==2

def test_live_redirect_refused():
    s=Session([Response(302,headers={'Location':'https://bluescholars.com/'})])
    c=ArchiveClient(session=s,delay=0,sleep=lambda _:None)
    with pytest.raises(ValueError,match='archive'): c.get('https://web.archive.org/web/'+TARGET+'id_/'+HOME)
    assert len(s.calls)==1

def test_size_cap():
    c=ArchiveClient(session=Session([Response(body=b'x'*20)]),delay=0,max_bytes=10)
    with pytest.raises(ValueError,match='size'): c.get('https://web.archive.org/web/'+TARGET+'id_/'+HOME)

class Client:
    def __init__(self,handler):self.handler=handler;self.calls=[]
    def get(self,url): self.calls.append(url); return self.handler(url)

def test_index_interruption_preserves_cursor(tmp_path):
    state=State(tmp_path)
    text=json.dumps([HEADER,['20200101000000',HOME,'text/html','200','A'],[],['continue']]).encode()
    client=Client(lambda u:Payload(text,u,200,{}))
    index(state,client,max_pages=1)
    reloaded=State(tmp_path)
    assert not reloaded.data['index_complete']
    assert reloaded.data['index']['domain']['resume_key']=='continue'
    client=Client(lambda u:Payload(json.dumps([HEADER]).encode(),u,200,{}))
    index(reloaded,client,max_pages=1)
    assert reloaded.data['index_complete']
    assert 'resumeKey=continue' in client.calls[0]

def test_seed_asset_index_queries_exact_observed_urls(tmp_path):
    (tmp_path/'recovery/seeds').mkdir(parents=True)
    first='https://images.squarespace-cdn.com/content/v1/site/front-page.jpg'
    second='https://media.tumblr.com/photo.jpg'
    (tmp_path/'recovery/seeds/inventory.json').write_text(json.dumps({'assets':[
        {'original_url':first},{'original_url':second}]}))
    response=json.dumps([HEADER,['20210529010844',first,'image/jpeg','200','DIGEST']]).encode()
    client=Client(lambda url:Payload(response,url,200,{}))
    result=recovery.index_seed_assets(State(tmp_path),client,max_assets=1)
    assert result['queried_urls']==1 and result['indexed_capture_records']==1
    assert 'matchType=exact' in client.calls[0] and 'front-page.jpg' in client.calls[0]
    assert State(tmp_path).data['resources'][first]['captures'][0]['timestamp']=='20210529010844'

def test_recover_checkpoints_and_skips_success(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    client=Client(lambda u:Payload(VALID,u,200,{'Content-Type':'text/html'}))
    report=recover(state,client,max_files=1)
    record=state.data['resources'][HOME]
    assert record['status']=='recovered'
    assert (tmp_path/record['raw_path']).read_bytes()==VALID
    assert len(record['sha256'])==64
    assert HOME+'blog' in state.data['resources']
    before=len(client.calls)
    recover(state,client,max_files=1)
    assert len(client.calls)==before+1 # fetch newly discovered blog, not homepage
    assert client.calls[0] != client.calls[-1]

def test_later_capture_needs_review(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    client=Client(lambda u:Payload(VALID,'https://web.archive.org/web/20250101000000id_/'+HOME,200,{}))
    recover(state,client,max_files=1)
    assert state.data['resources'][HOME]['status']=='needs_review'
    assert state.data['resources'][HOME]['actual_capture']=='20250101000000'

def test_exact_capture_is_saved_as_a_variant_without_overwriting_homepage(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    state.data['resources'][HOME].update(status='recovered',actual_capture=TARGET,sha256='baseline')
    client=Client(lambda u:Payload(VALID,'https://web.archive.org/web/20070724082915id_/'+HOME,200,{'Content-Type':'text/html'}))
    result=capture_variant(state,client,HOME,'20070724082915')
    key=result['source_key']
    assert result['actual_capture']=='20070724082915'
    assert key in state.data['resources'] and state.data['resources'][key]['raw_path']
    assert state.data['resources'][HOME]['sha256']=='baseline'

def test_capture_era_selects_latest_valid_record_and_resumes(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'html','seed',TARGET)
    record['captures']=[{'timestamp':'20070701134606','statuscode':'200'},
                        {'timestamp':'20070724082915','statuscode':'200'},
                        {'timestamp':'20070929034602','statuscode':'404'}]
    state.save()
    client=Client(lambda u:Payload(VALID,'https://web.archive.org/web/20070724082915id_/'+HOME,200,{}))
    report=capture_era(state,client,'2007',max_files=10)
    assert report['eligible_urls']==1 and report['recovered']==1
    assert state.data['resources'][HOME+'@@wayback:20070724082915:'+__import__('hashlib').sha256(VALID).hexdigest()[:12]]['status']=='recovered'
    again=capture_era(state,client,'2007',max_files=10)
    assert again['attempted']==0

def test_capture_era_falls_back_when_newest_archive_body_is_a_provider_error(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'html','seed',TARGET)
    newest='20070724082915';older='20070701134606'
    record['captures']=[{'timestamp':older,'statuscode':'200'},
                        {'timestamp':newest,'statuscode':'200'}]
    state.save()
    bad=b'<html><body>This page cannot be displayed. Contact the service provider.</body></html>'
    def response(url):
        if newest in url:return Payload(bad,url,200,{})
        return Payload(VALID,'https://web.archive.org/web/'+older+'id_/'+HOME,200,{})
    report=capture_era(state,Client(response),'2007',max_files=10)
    assert report['recovered']==1
    assert report['captures'][0]['actual_capture']==older
    assert len(report['captures'][0]['attempted_captures'])==2

def test_download_failure_is_not_missing_forever(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    def fail(u): raise OSError('Network unavailable')
    recover(state,Client(fail),max_files=1)
    record=State(tmp_path).data['resources'][HOME]
    assert record['status']=='failed'
    assert record['attempts'] and not record.get('raw_path')
    assert not state.data['index_complete']
