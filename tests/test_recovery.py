import json
from pathlib import Path
import pytest
from restore.archive import parse_cdx, validate_payload, ArchiveClient, Payload, capture_candidates
from restore import recover as recovery
from restore.recover import index, recover, resource_priority, capture_variant,capture_era,index_feed_resources,recover_feed_resources
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

def test_tiff_image_payload_is_preserved():
    validate_payload(b'II*\x00\x08\x00\x00\x00'+b'\x00'*16,'image')

def test_audio_media_requires_a_recognized_binary_signature():
    validate_payload(b'ID3\x04\x00\x00\x00\x00\x00\x00'+b'\x00'*32,'media')
    validate_payload(b'\xff\xfb\x90d'+b'\x00'*32,'media')
    with pytest.raises(ValueError,match='media signature'):
        validate_payload(b'<html><body>archive error</body></html>','media')
    with pytest.raises(ValueError,match='media signature'):
        validate_payload(b'not media','media')

def test_font_capture_requires_a_recognized_binary_signature():
    validate_payload(b'wOF2fixture','font')
    with pytest.raises(ValueError,match='font signature'): validate_payload(b'<html>landed page</html>','font')

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

def test_confirmed_legacy_wordpress_host_pages_get_acquisition_priority():
    alias={'url':'http://02cd02a.netsolhost.com:80/blog/2009/03/sxsw-2009-where-well-be/',
           'kind':'html','referrers':['CDX:domain:02cd02a.netsolhost.com']}
    unrelated={'url':'https://example.org/old-post/','kind':'html','referrers':['CDX:domain']}
    assert resource_priority(alias)[0] < resource_priority(unrelated)[0]

def test_posts_linked_from_recovered_wordpress_archive_pages_are_prioritized():
    linked={'url':HOME+'cinemetropolis-now-available-for-digital-download/','kind':'html',
            'referrers':[HOME+'page/5/']}
    unrelated={'url':HOME+'legacy-tool-endpoint/','kind':'html','referrers':['CDX:domain']}
    assert resource_priority(linked)[0] < resource_priority(unrelated)[0]

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

def test_livejournal_platform_css_images_are_prioritized_as_source_dependencies():
    linked={'url':'https://l-stat.livejournal.net/img/schemius/logo.svg?v=51065',
            'kind':'image','referrers':['https://l-stat.livejournal.net/??schemius_v4/header.css']}
    css={'url':'https://l-stat.livejournal.net/??lj_base.css?v=1518685122',
         'kind':'css','referrers':['https://bluescholars.livejournal.com/']}
    tracking={'url':'https://xc3.services.livejournal.com/ljcounter/?d=profile',
              'kind':'image','referrers':['https://bluescholars.livejournal.com/']}
    post_photo={'url':'https://imgprx.livejournal.net/example/photo-token',
                'kind':'image','referrers':['https://bluescholars.livejournal.com/']}
    unrelated={'url':'https://example.org/other-site-logo.png','kind':'image',
               'referrers':['CDX:domain']}
    assert resource_priority(linked)[0] < resource_priority(unrelated)[0]
    assert resource_priority(css)[0] < resource_priority(unrelated)[0]
    assert resource_priority(post_photo)[0] < resource_priority(unrelated)[0]
    content={'url':'https://bluescholars.com/blog/2013/9/9/eugene-oregon-august-2013',
             'kind':'html','referrers':['seed']}
    assert resource_priority(content)[0] < resource_priority(post_photo)[0]
    assert resource_priority(tracking)[0] > resource_priority(css)[0]

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

def test_archive_client_decodes_brotli_encoded_html():
    import base64,io
    from requests import Response as RequestsResponse
    from urllib3._collections import HTTPHeaderDict
    from urllib3.response import HTTPResponse

    encoded=base64.b64decode('H1QAUBwHbkzHftbXiWqfMDI6xUNVZXPgkBOgC168RdQChxweNG6ehdRqAmT46ZcgA5gHJ7cI')
    url='https://web.archive.org/web/20230930162408id_/https://bluescholars.com/'
    response=RequestsResponse()
    response.status_code=200
    response.url=url
    response.headers={'Content-Type':'text/html','Content-Encoding':'br'}
    response.raw=HTTPResponse(body=io.BytesIO(encoded),headers=HTTPHeaderDict(response.headers),preload_content=False)
    client=ArchiveClient(session=Session([response]),delay=0,sleep=lambda _:None)

    assert client.get(url).body==b'<!doctype html><html><head><title>Test</title></head><body>Archive data</body></html>'

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

def test_successful_domain_reindex_clears_stale_error(tmp_path):
    state=State(tmp_path)
    state.data['index']['domain:shop.bluescholars.com']={
        'resume_key':None,'complete':False,'pages':0,'rows':0,'last_error':'previous timeout'}
    client=Client(lambda u:Payload(json.dumps([HEADER]).encode(),u,200,{}))

    result=index(state,client,max_pages=1,url='shop.bluescholars.com',match='domain')

    assert result['complete'] is True
    assert 'last_error' not in result

def test_index_accepts_an_explicit_non_target_alias_domain(tmp_path):
    alias='http://02cd02a.netsolhost.com:80/blog/2009/03/sxsw-2009-where-well-be/'
    foreign='http://unrelated.example/blog/post/'
    text=json.dumps([HEADER,
        ['20100312073016',alias,'text/html','200','ALIAS'],
        ['20100312073017',foreign,'text/html','200','OTHER']]).encode()
    state=State(tmp_path)
    client=Client(lambda u:Payload(text,u,200,{}))

    result=index(state,client,max_pages=1,url='02cd02a.netsolhost.com',match='domain')

    assert result['complete']
    assert alias in state.data['resources']
    assert state.data['resources'][alias]['kind']=='html'
    assert foreign not in state.data['resources']

def test_checkpoint_reclassifies_unfetched_legacy_wordpress_permalink(tmp_path):
    state=State(tmp_path)
    url='http://02cd02a.netsolhost.com/blog/2009/03/sxsw-2009-where-well-be/'
    state.add(url,'image','legacy CDX inventory')
    state.save()

    assert State(tmp_path).data['resources'][url]['kind']=='html'

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

def test_feed_index_prioritizes_page_links_that_can_reveal_original_images(tmp_path):
    state=State(tmp_path)
    image='https://cdn.example/feed-photo.jpg'
    page='http://bluescholars.com/feed-linked-page/'
    state.add(page,'html','feed:20100401000000:http://bluescholars.com/feed/')
    state.add(image,'image','feed:20100401000000:http://bluescholars.com/feed/')
    text=json.dumps([HEADER,['20100401000000',page,'text/html','200','PAGE']]).encode()
    client=Client(lambda url:Payload(text,url,200,{}))

    report=index_feed_resources(state,client,max_urls=1,max_pages=1)

    assert report['pending_urls']==2 and report['queried_urls']==1
    assert report['page_urls']==1 and report['indexed_capture_records']==1
    assert 'feed-linked-page' in client.calls[0] and 'matchType=exact' in client.calls[0]
    assert state.data['resources'][page]['captures'][0]['digest']=='PAGE'
    assert (tmp_path/'recovery/feed-index-report.json').is_file()

def test_feed_index_follows_assets_linked_from_recovered_feed_pages(tmp_path):
    state=State(tmp_path)
    article='http://bluescholars.com/blog/2010/04/feed-post/'
    image='http://bluescholars.com/blog/wp-content/uploads/feed-photo.jpg'
    source=state.add(article,'html','feed:20100401000000:http://bluescholars.com/blog/feed/')
    source.update(status='recovered',raw_path='source/recovered-feed-post.html')
    state.add(image,'image',article)
    text=json.dumps([HEADER,['20120401000000',image,'image/jpeg','200','NESTED-PHOTO']]).encode()
    client=Client(lambda url:Payload(text,url,200,{}))

    report=index_feed_resources(state,client,max_urls=1,max_pages=1)

    assert report['pending_urls']==1 and report['image_urls']==1
    assert 'feed-photo.jpg' in client.calls[0]
    assert state.data['resources'][image]['captures'][0]['digest']=='NESTED-PHOTO'

def test_feed_recovery_selects_a_dated_pre_squarespace_page_capture(tmp_path):
    state=State(tmp_path)
    page='http://bluescholars.com/blog/2010/04/feed-linked-page/'
    state.add(page,'html','feed:20100401000000:http://bluescholars.com/feed/')
    state.data['resources'][page]['captures']=[{'timestamp':'20110401010203','statuscode':'200'}]
    client=Client(lambda url:Payload(VALID,'https://web.archive.org/web/20110401010203id_/'+page,200,{'Content-Type':'text/html'}))

    report=recover_feed_resources(state,client,max_files=1)

    assert report['attempted']==1 and report['recovered']==1
    assert report['captures'][0]['url']==page
    variant=state.data['resources'][report['captures'][0]['source_key']]
    assert variant['actual_capture']=='20110401010203'
    assert variant['status']=='recovered'
    assert (tmp_path/'recovery/feed-recovery-report.json').is_file()
    before=len(client.calls)
    resumed=recover_feed_resources(state,client,max_files=1)
    assert resumed['pending_urls']==0 and resumed['attempted']==0
    assert len(client.calls)==before

def test_feed_recovery_adds_a_newer_2009_variant_without_replacing_existing_source(tmp_path):
    state=State(tmp_path)
    page='http://bluescholars.com/blog/2009/09/feed-post/'
    record=state.add(page,'html','feed:20090901000000:http://bluescholars.com/blog/feed/')
    record.update(status='recovered',raw_path='source/older.html',actual_capture='20090901000000',sha256='older')
    record['captures']=[{'timestamp':'20100701010203','statuscode':'200'}]
    client=Client(lambda url:Payload(VALID,'https://web.archive.org/web/20100701010203id_/'+page,200,{'Content-Type':'text/html'}))

    report=recover_feed_resources(state,client,max_files=1)

    assert report['attempted']==1 and report['recovered']==1
    assert record['actual_capture']=='20090901000000'
    variant=state.data['resources'][report['captures'][0]['source_key']]
    assert variant['actual_capture']=='20100701010203'

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

def test_untouched_queued_pages_precede_retries_of_failed_high_priority_urls(tmp_path):
    state=State(tmp_path)
    failed=state.add(HOME,'html','seed',TARGET)
    failed.update(status='failed',hints=[TARGET],captures=[])
    queued_url=HOME+'blog/archived-entry'
    queued=state.add(queued_url,'html',HOME+'blog/',TARGET)
    client=Client(lambda url:Payload(VALID,url,200,{'Content-Type':'text/html'}))

    recover(state,client,max_files=1,retry_failed=True)

    assert state.data['resources'][queued_url]['status']=='recovered'
    assert len(client.calls)==1 and queued_url in client.calls[0]

def test_recover_can_target_a_host_without_touching_other_queued_sites(tmp_path):
    state=State(tmp_path)
    unrelated=state.add(HOME+'store.html','html','seed',TARGET)
    target='http://shop.bluescholars.com/products/autographed-bayani-poster'
    state.add(target,'html','CDX:shop.bluescholars.com',TARGET)
    client=Client(lambda url:Payload(VALID,url,200,{'Content-Type':'text/html'}))

    recover(state,client,max_files=1,host='shop.bluescholars.com')

    assert state.data['resources'][target]['status']=='recovered'
    assert unrelated['status']=='queued'
    assert len(client.calls)==1 and 'shop.bluescholars.com' in client.calls[0]

def test_fully_exhausted_failure_is_not_retried_ahead_of_new_pages(tmp_path):
    state=State(tmp_path)
    failed=state.add(HOME,'html','seed',TARGET)
    failed.update(status='failed',hints=[TARGET],captures=[],attempts=[
        {'requested_capture':TARGET,'result':'failed'}])
    state.data['index']['exact:'+HOME]={'complete':True,'pages':1,'rows':0}
    retry_url=HOME+'blog/other-capture'
    retry=state.add(retry_url,'html',HOME+'blog/',TARGET)
    retry.update(status='failed',hints=[TARGET],captures=[])
    state.data['index']['exact:'+retry_url]={'complete':True,'pages':1,'rows':1}
    client=Client(lambda url:Payload(VALID,url,200,{'Content-Type':'text/html'}))

    recover(state,client,max_files=1,retry_failed=True)

    assert state.data['resources'][retry_url]['status']=='recovered'
    assert len(client.calls)==1 and retry_url in client.calls[0]

def test_capture_date_attempts_resume_in_bounded_batches(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'html','seed',TARGET)
    record['captures']=[{'timestamp':stamp,'statuscode':'200'} for stamp in
                        ('20200101000000','20190101000000','20180101000000','20170101000000')]
    successful='20180101000000'
    def response(url):
        if '/cdx/search/cdx?' in url:return Payload(json.dumps([HEADER]).encode(),url,200,{})
        stamp=url.split('/web/')[1][:14]
        if stamp!=successful:raise OSError('capture unavailable')
        return Payload(VALID,url,200,{'Content-Type':'text/html'})
    client=Client(response)

    recover(state,client,max_files=1)

    assert state.data['resources'][HOME]['status']=='queued'
    first_attempts=[a['requested_capture'] for a in state.data['resources'][HOME]['attempts']]
    assert len(first_attempts)==3 and successful not in first_attempts
    recover(state,client,max_files=1,retry_failed=True)

    assert state.data['resources'][HOME]['status']=='recovered'
    assert [a['requested_capture'] for a in state.data['resources'][HOME]['attempts']]==first_attempts+[successful]

def test_recover_progress_reports_resumable_batch_boundaries(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    updates=[]
    client=Client(lambda u:Payload(VALID,u,200,{'Content-Type':'text/html'}))
    recover(state,client,max_files=2,progress=updates.append)
    assert updates
    assert updates[-1]['processed']==2 and updates[-1]['url']

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

def test_exact_capture_can_preserve_external_html_not_on_site_domain(tmp_path):
    state=State(tmp_path)
    url='http://bluescholars.livejournal.com/16954.html'
    client=Client(lambda replay:Payload(VALID,'https://web.archive.org/web/20090125012333id_/'+url,200,{'Content-Type':'text/html'}))
    result=capture_variant(state,client,url,'20090125012333',kind_override='html')
    record=state.data['resources'][result['source_key']]
    assert result['kind']=='html' and record['kind']=='html'
    assert (tmp_path/record['raw_path']).read_bytes()==VALID

def test_capture_era_selects_latest_valid_record_and_resumes(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'html','seed',TARGET)
    record['captures']=[{'timestamp':'20070701134606','statuscode':'200'},
                        {'timestamp':'20070724082915','statuscode':'200'},
                        {'timestamp':'20070929034602','statuscode':'404'}]
    state.save()
    client=Client(lambda u:Payload(VALID,'https://web.archive.org/web/20070724082915id_/'+HOME,200,{}))
    report=capture_era(state,client,'2007',max_files=10)
    assert report['eligible_urls']==1 and report['recovered']==1
    assert report['indexed_urls']==1 and report['remaining_urls']==0
    assert state.data['resources'][HOME+'@@wayback:20070724082915:'+__import__('hashlib').sha256(VALID).hexdigest()[:12]]['status']=='recovered'
    again=capture_era(state,client,'2007',max_files=10)
    assert again['attempted']==0
    assert again['already_recovered_urls']==1 and again['remaining_urls']==0

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

def test_capture_era_does_not_count_redirected_capture_outside_era(tmp_path):
    state=State(tmp_path);record=state.add(HOME,'html','seed',TARGET)
    timestamp='20070724082915'
    record['captures']=[{'timestamp':timestamp,'statuscode':'200'}]
    state.save()
    redirected='https://web.archive.org/web/20140101000000id_/'+HOME
    client=Client(lambda u:Payload(VALID,redirected,200,{}))

    report=capture_era(state,client,'2007',max_files=10)

    assert report['recovered']==0
    assert report['captures']==[]
    assert report['failures'][0]['error']=='ValueError: Resolved capture 20140101000000 is outside the 2007 era'
    assert report['remaining_urls']==1
    later=next(r for key,r in state.data['resources'].items() if key!=HOME and r.get('actual_capture')=='20140101000000')
    assert later['status']=='needs_review'

def test_download_failure_is_not_missing_forever(tmp_path):
    state=State(tmp_path);state.add(HOME,'html','seed',TARGET)
    def fail(u):
        if '/cdx/search/cdx?' in u:return Payload(json.dumps([HEADER]).encode(),u,200,{})
        raise OSError('Network unavailable')
    recover(state,Client(fail),max_files=1)
    record=State(tmp_path).data['resources'][HOME]
    assert record['status']=='failed'
    assert record['attempts'] and not record.get('raw_path')
    assert not state.data['index_complete']
