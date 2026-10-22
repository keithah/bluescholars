#!/usr/bin/env python3
"""Recover dated Wayback pages and linked image mementos from Seattle press leads.

All source pages and images are stored in recovery-only storage with the exact
CDX row, replay URL, CDX SHA-1 verification, local SHA-256, and source-page
reference preserved. This never promotes third-party media to the public site.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
from restore.archive import validate_payload

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery/other-archives/press-articles'
CDX='https://web.archive.org/cdx/search/cdx'
FIELDS='timestamp,original,statuscode,mimetype,digest,length'
PAGES=[
 # Contemporaneous 2006 Seattle Weekly review of the duo's Chop Suey shows.
 'https://www.seattleweekly.com/2006/10/09/blue-scholars-at-chop-suey/',
 # Sound Scene Revolution's 2006 interview page links its original podcast and
 # interview/show photographs; audio and images are checked separately.
 'https://soundscenerevolution.com/2006/12/interview-with-blue-scholars-podcast-42/',
 'http://soundscenerevolution.com/2006/12/05/interview-with-blue-scholars-podcast-42/',
 'https://soundscenerevolution.com/2006/12/05/interview-with-blue-scholars-podcast-42/',
 'https://soundscenerevolution.com/2006/12/',
 'https://www.flickr.com/photos/soundscenerevolution/sets/72157594407516203/',
 'http://flickr.com/photos/soundscenerevolution/sets/72157594407516203/',
 'https://embedr.flickr.com/photosets/72157594407516203',
 'http://vids.myspace.com/index.cfm?fuseaction=vids.individual&videoid=1522647925',
 'https://206up.com/2011/07/11/interview-blue-scholars-seattle-6-18-11/',
 'https://206up.com/2010/09/19/show-review-blue-scholars-the-bowery-ballroom-nyc-on-9-17-10/',
 'https://www.capitolhillseattle.com/2011/05/chs-pics-blue-scholars-on-broadway/',
 # Additional historical, image-rich Seattle coverage found during the
 # October 2026 source-link search. Keep each page in the same recovery-only
 # manifest so linked image histories can be checked with the same provenance.
 'https://www.seattleweekly.com/2010/10/21/all-photos-by-nick-feldmanwhen-i-predicted-blue-scholars-headlining-gig-last/',
 'http://www.seattleweekly.com/2010/10/21/all-photos-by-nick-feldmanwhen-i-predicted-blue-scholars-headlining-gig-last/',
 'https://seattleweekly.com/2010/10/21/all-photos-by-nick-feldmanwhen-i-predicted-blue-scholars-headlining-gig-last/',
 'http://seattleweekly.com/2010/10/21/all-photos-by-nick-feldmanwhen-i-predicted-blue-scholars-headlining-gig-last/',
 'https://www.seattlemet.com/arts-and-culture/2010/10/slideshow-blue-scholars-macklemore-hip-hop-at-the-paramount',
 'https://www.cityartsmagazine.com/issues-seattle-2013-02-rapper-camera/',
 'https://threeimaginarygirls.com/bluescholars-711/',
 'https://www.seattleweekly.com/2007/02/08/running-with-the-big-dogs/',
 'http://www.seattleweekly.com/2007/02/08/running-with-the-big-dogs/',
 'https://seattleweekly.com/2007/02/08/running-with-the-big-dogs/',
 'http://seattleweekly.com/2007/02/08/running-with-the-big-dogs/',
 'https://bumbershoot.com/festivals/2009',
 # Seattle P-I feature on the December 2007 Program showcase; archive result
 # includes source credit to Lanilee Photography and a photo lead.
 'https://www.seattlepi.com/entertainment/music/article/blue-scholars-bring-city-s-subculture-to-light-1258707.php',
 # 2008 Sasquatch! preview naming Blue Scholars as the 2006 local opener.
 'https://www.seattleweekly.com/2008/05/24/photo-by-renee-mcmahonits-become-sometime-of-a-tradition-for-sasquatch-to/',
 # Additional contemporaneous coverage and image-rich pages found through
 # search-result source links on October 22, 2026. Each exact source is tested
 # independently in Wayback before any page or image is retained.
 'https://www.seattlemet.com/2009/03/0507-green-scholars',
 'https://www.seattleweekly.com/2012/11/08/taking-place-last-night-at-the-theater-off-jackson-the-blue-scholars/',
 'https://www.concertarchives.org/bands/blue-scholars/photos',
 'https://www.seattlepi.com/entertainment/music/article/blue-scholars-are-back-with-more-humanity-driven-1237033.php',
 'https://www.seattlepi.com/entertainment/music/article/idol-star-boosts-blue-scholars-show-1237231.php',
 'https://www.seattlepi.com/entertainment/music/article/memorable-performances-that-were-music-to-our-ears-1259946.php',
 'https://www.seattlepi.com/entertainment/article/five-to-watch-in-2007-on-the-local-arts-scene-1223863.php',
 'https://www.seattlepi.com/entertainment/music/article/bumbershoot-hip-hop-s-hot-on-stage-but-if-you-1213243.php',
 'https://www.seattlepi.com/entertainment/music/article/club-scene-seattle-s-hip-hop-scene-steps-front-1213211.php',
 'https://www.seattlepi.com/entertainment/music/article/look-to-the-local-labels-for-proof-of-seattle-s-1241555.php',
 'https://www.seattlepi.com/entertainment/music/article/these-four-local-bands-are-on-the-cusp-of-bigness-1162832.php',
 # Photo and profile leads from a focused search for the 2006–2010 Bayani era.
 'https://s100.chasejarvis.com/people/bluescholars',
 'https://www.kalamu.com/bol/2008/02/04/blue-scholars-%E2%80%9Cloyalty%E2%80%9D/',
 'https://www.seattlemet.com/arts-and-culture/2010/12/so-many-concerts-so-little-time-december-2010',
 'https://www.seattleweekly.com/2007/11/09/last-nights-benefit-for-826-seattle-the-greenwood-writing-center-started-by/',
 'https://www.spinmagazine.com/2006/09/seattle-hip-hop-common-market-blue-scholars/',
 # KEXP's older Music Revolutionaries page is independently indexed by
 # Arquivo.pt with two labeled Blue Scholars images; check Wayback revisions
 # and all image URLs linked from its dated page bodies as a separate source.
 'http://www.kexp.org/learn/docu_music_revolutionaries.asp',
 # Cascade PBS's migrated 2018 Kuya Geo article embeds a PBS interview video;
 # keep the publisher's canonical page and its Crosscut series index as
 # separate source URLs so dated article and media references can be followed.
 'https://www.cascadepbs.org/culture/2018/11/generational-zigs-and-zags-immigrant-identity/',
 'https://crosscut.com/kuya-geo',
 'https://www.pbs.org/show/kuya-geo/',
 'https://www.kcts9.org/show/kuya-geo',
 'https://www.kcts9.org/show/kuya-geo/episodes',
 'https://www.kcts9.org/show/kuya-geo/episode/seattle-drivers-kuya-geo-has-a-rap-for-that-prhvxp',
 'https://www.kcts9.org/show/kuya-geo/episode/the-roots-of-seattles-filipino-community-ikqoqk',
 'https://www.kcts9.org/show/kuya-geo/episode/meet-kuya-geo-a-filipino-american-twist-on-seattle-culture-ytrkfn',
 'https://www.kcts9.org/video/kuya-geo-zig-zag-generations',
 'https://player.pbs.org/partnerplayer/vxO_dKG3eMqV5rC9qhUwbA==/?start=0&end=0&topbar=false&autoplay=true&endscreen=false',
 'https://player.pbs.org/partnerplayer/vxO_dKG3eMqV5rC9qhUwbA==/',
 'https://www.pbs.org/video/kuya-geo-zig-zag-generations-58um96/',
 'https://www.pbs.org/video/seattle-drivers-kuya-geo-has-a-rap-for-that-prhvxp/',
 'https://www.pbs.org/video/the-roots-of-seattles-filipino-community-ikqoqk/',
 'https://www.pbs.org/video/meet-kuya-geo-a-filipino-american-twist-on-seattle-culture-ytrkfn/',
 # Aileen Imperial's portfolio independently lists the missing 2018 Geo story
 # about Bruce Lee and links to PBS's canonical video slug. The Hundreds
 # interview is another first-person, image-rich source about Geo's Food & Sh*t
 # project and is preserved separately from the Blue Scholars site editions.
 'https://www.aileenimperial.com/Kuya%20Geo%3A%20How%20Bruce%20Lee%20destroyed%20the%20stereotype%20of%20the%20Asian%20male',
 'https://www.pbs.org/video/how-bruce-lee-destroyed-the-stereotype-of-the-asian-male-6e2tln/',
 'https://player.pbs.org/portalplayer/3012417773/',
 'https://player.pbs.org/viralplayer/3012417773/',
 'https://thehundreds.com/blogs/content/food-and-sh-t',
 # The archived interview links directly to Geo and Chera Amlag's Food & Sh*t
 # project site; preserve it as a separate source-linked related-site trail.
 'http://www.foodandsh-t.com/',
 # Routes discovered as same-site links in pre-takeover homepage mementos.
 'http://foodandsh-t.com/blog',
 'http://foodandsh-t.com/chee-menu',
 'http://foodandsh-t.com/monthly-pop-up',
 'http://www.foodandsh-t.com/?category=Pop-up',
 'http://www.foodandsh-t.com/?offset=1400712231795',
 'http://www.foodandsh-t.com/?offset=1405110685157',
 'http://www.foodandsh-t.com/?tag=Chee%21',
 'http://www.foodandsh-t.com/?tag=Inay%27s',
 'http://www.foodandsh-t.com/?tag=One+Year+Anniversary',
 'http://www.foodandsh-t.com/?tag=Pop-up',
 'http://www.foodandsh-t.com/about2018',
 'http://www.foodandsh-t.com/blog/2014/10/8/cornerstone-cafe-campaign-launch',
 'http://www.foodandsh-t.com/blog/2014/5/21/7q7mydm45oofvy48bnk95hpriqx0j0',
 'http://www.foodandsh-t.com/blog/2014/6/12/instagram-photos-from-hi',
 'http://www.foodandsh-t.com/blog/2014/6/12/video-making-of-the-food-sht-lil-woodys-adoboburger',
 'http://www.foodandsh-t.com/blog/2014/6/16/next-pop-up-in-seattle-kalsada-623',
 'http://www.foodandsh-t.com/blog/2014/6/23/kamayan-menu',
 'http://www.foodandsh-t.com/blog/2014/6/3/june-8th-pop-up-in-hawaii',
 'http://www.foodandsh-t.com/blog/2014/6/3/seattle-june-3-june-9-adoboburger-special-at-lil-woodys',
 'http://www.foodandsh-t.com/blog/2014/7/11/next-pop-up-murado-720-inays',
 'http://www.foodandsh-t.com/blog/2014/7/2/946c209qf10qxyp2ws4pemsmiemv2i',
 'http://www.foodandsh-t.com/blog/2014/8/12/food-sht-featuring-in-aaja-seattle-chefsshowcase-mon-aug-4',
 'http://www.foodandsh-t.com/blog/2014/8/12/sun-august-17-the-salo-series-comes-to-seattle',
 'http://www.foodandsh-t.com/blog/2014/9/11/salo-seattle-video-recap',
 'http://www.foodandsh-t.com/blog/2014/9/15/chee-one-year-anniversary-pop-up-dinner-sep-22',
 'http://www.foodandsh-t.com/blog/2014/9/22/chee-menu',
 'http://www.foodandsh-t.com/blog/2014/9/29/acrs-gala-2014-a-culinary-journey',
 'http://www.foodandsh-t.com/blog/2014/9/29/one-year-of-food-sht-a-retrospective',
 'http://www.foodandsh-t.com/blog/2014/9/29/one-year-of-food-sht-a-retrospective-part-ii',
 'http://www.foodandsh-t.com/contact',
 'http://www.foodandsh-t.com/events/',
 'http://www.foodandsh-t.com/food-sht-monthly-pop-up/',
 'https://www.foodandsh-t.com/events/2014/6/8/food-sht-honolulu',
 # XLR8R's dated September 2009 feature index exposes this linked interview
 # page and its named Blue Scholars portrait; preserve the detail page and
 # independently check its larger image variants.
 'http://www.xlr8r.com/features/2009/09/inbox-blue-scholars',
 'https://www.soompi.com/article/360354wpp/exclusive-interview-with-geo-of-blue-scholars',
 # A photographer's first-person account links both a Flickr set and a
 # SmugMug gallery for the June 2011 Cinemetropolis party, plus the Seattle
 # Weekly slideshow. These are source-linked image archives, not substitutes
 # for the original band's own site.
 'https://www.arminausejo.com/blue-scholars-kickstarter-vip-party/',
 'https://www.seattleweekly.com/slideshow/blue-scholars-vip-party-theater-off-jackson-33576391/',
 'https://www.flickr.com/photos/arminausejo/sets/72157626987127616/',
 'https://verdugo.smugmug.com/Events/Blue-Scholars-Cinemetropolis/',
 # Additional contemporary Seattle P-I articles surfaced in source-linked
 # searches; each URL is independently checked for dated Wayback revisions.
 'https://www.seattlepi.com/entertainment/music/article/blue-scholars-are-back-with-more-humanity-driven-1237033.php',
 'https://www.seattlepi.com/entertainment/music/article/now-that-they-have-some-footing-blue-scholars-1219990.php',
 'https://www.seattlepi.com/news/article/blue-scholars-present-the-program-night-four-1259838.php',
 'https://www.seattlepi.com/entertainment/music/article/blue-scholars-bring-city-s-subculture-to-light-1258707.php',
]
MAX_BYTES=25_000_000

def cdx_sha1(body:bytes)->str:
 return base64.b32encode(hashlib.sha1(body).digest()).decode().rstrip('=')

def _get(session,url,**kw):
 r=session.get(url,timeout=(10,50),**kw);r.raise_for_status();return r

def article_image_candidates(raw:bytes, base_url:str)->list[str]:
 """Return unique raster URLs from an article body, excluding page chrome."""
 soup=BeautifulSoup(raw,'html.parser')
 scopes=(soup.select('.entry-content') or soup.select('article') or
         soup.select('.post-content') or soup.select('[itemprop="articleBody"]'))
 explicit_asset_names=False
 if not scopes:
  # Early WordPress layouts often have no semantic article wrapper. In that
  # case keep only body images whose own filename/alt/title clearly identifies
  # the artist, avoiding the rest of the page chrome and unrelated posts.
  scopes=[soup.body] if soup.body else []
  explicit_asset_names=True
 found=[]
 for scope in scopes:
  for tag in scope.find_all(['img','source']):
   if explicit_asset_names:
    identity=' '.join(str(tag.get(k) or '') for k in ('src','data-src','alt','title')).casefold().replace('%20',' ')
    if not any(term in identity for term in ('blue scholar','bluescholar','geologic','sabzi','bayani')):continue
   vals=[tag.get('src'),tag.get('data-src'),tag.get('data-original')]
   for set_value in (tag.get('srcset'),tag.get('data-srcset')):
    if not set_value:continue
    choices=[]
    for candidate in set_value.split(','):
     parts=candidate.strip().split()
     if not parts:continue
     width=0
     if len(parts)>1:
      match=re.match(r'(\d+)(?:w|x)$',parts[1])
      if match:width=int(match.group(1))
     choices.append((width,parts[0]))
    if choices:vals.append(max(choices)[1])
   for val in vals:
    if not val or val.startswith('data:'):continue
    url=urljoin(base_url,val).split('#')[0]
    parsed=urlsplit(url)
    if parsed.scheme not in ('http','https'):continue
    lower=url.lower()
    if any(x in lower for x in ('gravatar','pixel','tracking','avatar','logo','icon','emoji','placeholder','blank-grid','instagram-feed','post-flair/sharing','loading.gif','statcounter','scorecardresearch','wp.com/wp-content/mu-plugins')):continue
    if url not in found:found.append(url)
 return found

def focus_image_candidates(candidates:dict, source_substring:str|None)->dict:
 """Keep only image leads exposed by the requested source page, if focused."""
 if not source_substring:return candidates
 return {url:[ref for ref in refs if source_substring in ref.get('page_url','')]
         for url,refs in candidates.items()
         if any(source_substring in ref.get('page_url','') for ref in refs)}

def select_page_targets(pages:list[str], only_page_url:str|None=None, only_source_page:str|None=None, only_image_url:str|None=None)->list[str]:
 """Select HTML sources without re-querying the whole inventory for image-only work."""
 if only_source_page or only_image_url:
  return []
 return [page for page in pages if only_page_url is None or only_page_url in page]

def page_capture_matches(record:dict, source_substring:str|None=None, before_timestamp:str|None=None)->bool:
 """Limit source-linked image extraction to compatible dated page captures."""
 if source_substring and source_substring not in record.get('original_url',''):
  return False
 if before_timestamp and record.get('timestamp','')>=before_timestamp:
  return False
 return True

def read_additional_page_urls(path:str|None)->list[str]:
 """Read source-linked page URLs from JSON (or one URL per text line)."""
 if not path:return []
 data=json.loads(Path(path).read_text(encoding='utf-8')) if path.lower().endswith('.json') else Path(path).read_text(encoding='utf-8').splitlines()
 if isinstance(data,dict):
  data=data.get('urls',data.get('pages',[]))
 result=[]
 for item in data:
  url=item if isinstance(item,str) else item.get('source_url',item.get('url')) if isinstance(item,dict) else None
  if isinstance(url,str) and url.startswith(('http://','https://')) and url not in result:result.append(url)
 return result

def recover(delay=.8, image_limit=100, only_image_url=None, only_source_page=None, retry_image_index_errors=False, only_page_url=None, pages_only=False, max_image_urls=100, image_page_before=None, additional_pages=None):
 page_sources=list(dict.fromkeys(PAGES+(additional_pages or [])))
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'pages').mkdir(exist_ok=True);(OUT/'images').mkdir(exist_ok=True)
 mp=OUT/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {'version':1,'sources':{},'page_captures':{},'image_urls':{},'image_captures':{}}
 s=requests.Session();s.headers['User-Agent']='BlueScholarsRestoration/0.1 (historical preservation research)'
 report={'archive':'Internet Archive Wayback','sources':len(page_sources),'queried_page_sources':0,'page_capture_rows':0,'page_payloads_recovered':0,'image_urls_discovered':0,'image_urls_queried':0,'image_capture_rows':0,'image_payloads_recovered':0,'failures':[],'limitations':['Exact URL histories and source-page-linked images only; this is not an archive-wide export.','Third-party press pages/images are recovery evidence, not original Blue Scholars site pages.','Image files remain local-only until rights and relevance review.']}
 if only_image_url:
  report['focused_image_url']=only_image_url
 if only_source_page:
  report['focused_source_page']=only_source_page
 if only_page_url:
  report['focused_page_url']=only_page_url
 page_targets=select_page_targets(page_sources,only_page_url,only_source_page,only_image_url)
 for page in page_targets:
  if page not in m['sources']:
   try:
    r=_get(s,CDX,params={'url':page,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':100})
    rows=r.json();rows=rows[1:] if rows else []
    m['sources'][page]={'source_url':page,'cdx_rows':rows,'queried_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
   except Exception as e:
    m['sources'][page]={'source_url':page,'cdx_rows':[],'query_error':f'{type(e).__name__}: {e}'}
    report['failures'].append({'stage':'page_cdx','url':page,'error':m['sources'][page]['query_error']})
   report['queried_page_sources']+=1
   mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
  for row in m['sources'][page].get('cdx_rows',[]):
   if len(row)<6 or row[2]!='200' or row[3].lower() not in ('text/html','application/xhtml+xml'):continue
   ts,orig,status,mime,cdxdigest,length=row[:6]; key=f'{orig}@@{ts}@@{cdxdigest}'
   if key in m['page_captures'] and (ROOT/m['page_captures'][key].get('raw_path','')).is_file():continue
   replay=f'https://web.archive.org/web/{ts}id_/{orig}'
   try:
    r=_get(s,replay);body=r.content
    if len(body)>MAX_BYTES:raise ValueError('page exceeds 25 MB limit')
    validate_payload(body,'html')
    got=cdx_sha1(body)
    if got!=cdxdigest:raise ValueError(f'CDX digest mismatch: {got} != {cdxdigest}')
    sha=hashlib.sha256(body).hexdigest();rel=f'recovery/other-archives/press-articles/pages/{ts}-{sha}.html';p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    m['page_captures'][key]={'source_page_url':page,'original_url':orig,'timestamp':ts,'replay_url':replay,'cdx_mime':mime,'cdx_digest':cdxdigest,'cdx_length':int(length),'cdx_sha1_verified':True,'bytes':len(body),'sha256':sha,'raw_path':rel}
    report['page_payloads_recovered']+=1
   except Exception as e:report['failures'].append({'stage':'page_replay','url':orig,'timestamp':ts,'error':f'{type(e).__name__}: {e}'})
   report['page_capture_rows']+=1;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
 if pages_only:
  report['page_capture_records_total']=len(m['page_captures'])
  report['unique_page_payloads_total']=len({x['sha256'] for x in m['page_captures'].values()})
  report['unique_linked_image_urls_total']=len(m['image_urls'])
  report['image_capture_records_total']=len(m['image_captures'])
  report['unique_image_payloads_total']=len({x['sha256'] for x in m['image_captures'].values()})
  report['unique_source_urls_queried_total']=len(m['sources'])
  review={}
  for capture in m['image_captures'].values():
   status=capture.get('relevance_status','pending visual review')
   review[status]=review.get(status,0)+1
  report['image_relevance_review']=review
  report['pending_visual_review_records']=review.get('pending visual review',0)
  m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
  (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
  return report
 # Discover image URLs present in saved mementos. Filter generic tracking and icons.
 candidates={}
 focused_source=only_source_page or only_page_url
 for key,record in m['page_captures'].items():
  if not page_capture_matches(record,focused_source,image_page_before):continue
  src=ROOT/record['raw_path']
  if not src.is_file():continue
  for u in article_image_candidates(src.read_bytes(),record['original_url']):
   candidates.setdefault(u,[]).append({'page_url':record['original_url'],'timestamp':record['timestamp'],'page_sha256':record['sha256']})
 report['image_urls_discovered']=len(candidates)
 # A focused page recovery must keep the image pass scoped to that page's
 # captured HTML. Otherwise a one-page run can silently reprocess every
 # source already present in the shared manifest.
 candidates=focus_image_candidates(candidates,focused_source)
 if only_image_url:
  if only_image_url in candidates:
   candidates={only_image_url:candidates[only_image_url]}
  else:
   # A focused exact-URL query can still be useful when a page exposed the
   # source URL but its capture is absent from the current page parser inputs.
   candidates={only_image_url:[{'page_url':'explicit focused recovery URL','timestamp':None,'page_sha256':None}]}
 indexed_this_run=0
 for image_url,referrers in candidates.items():
  if any(x in image_url.lower() for x in ('placeholder','blank-grid','instagram-feed','post-flair/sharing','loading.gif','statcounter','scorecardresearch','wp.com/wp-content/mu-plugins')):
   m['image_urls'].setdefault(image_url,{'source_image_url':image_url,'source_pages':referrers,'cdx_rows':[]})['relevance_status']='excluded_tracking_or_template_asset'
   continue
  retry_index=(retry_image_index_errors and image_url in m['image_urls']
               and bool(m['image_urls'][image_url].get('query_error')))
  if image_url not in m['image_urls'] or retry_index:
   if max_image_urls and indexed_this_run>=max_image_urls:
    continue
   try:
    r=_get(s,CDX,params={'url':image_url,'matchType':'exact','output':'json','fl':FIELDS,'filter':'statuscode:200','limit':100})
    rows=r.json();rows=rows[1:] if rows else []
    rows=[x for x in rows if len(x)>5 and x[2]=='200' and x[3].lower().startswith('image/')]
    m['image_urls'][image_url]={'source_image_url':image_url,'source_pages':referrers,'cdx_rows':rows}
   except Exception as e:
    m['image_urls'][image_url]={'source_image_url':image_url,'source_pages':referrers,'cdx_rows':[],'query_error':f'{type(e).__name__}: {e}'}
    report['failures'].append({'stage':'image_cdx','url':image_url,'error':m['image_urls'][image_url]['query_error']})
   report['image_urls_queried']+=1;indexed_this_run+=1;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
  # An earlier interrupted run captured a few widget loading GIF revisions
  # before the template-asset filter was tightened. Keep their provenance but
  # explicitly mark them irrelevant and exclude them from the media count.
  if any(x in image_url.lower() for x in ('placeholder','blank-grid','instagram-feed','post-flair/sharing','loading.gif','statcounter','scorecardresearch','wp.com/wp-content/mu-plugins')):
   m['image_urls'][image_url]['relevance_status']='excluded_template_loading_icon'
   for capture in m['image_captures'].values():
    if capture.get('source_image_url') == image_url:
     capture['relevance_status']='excluded_template_placeholder_or_loading_asset'
   continue
  for row in m['image_urls'][image_url].get('cdx_rows',[]):
   ts,orig,status,mime,dig,length=row[:6];key=f'{orig}@@{ts}@@{dig}'
   if key in m['image_captures'] and (ROOT/m['image_captures'][key].get('raw_path','')).is_file():continue
   if report['image_payloads_recovered']>=image_limit:break
   replay=f'https://web.archive.org/web/{ts}id_/{orig}'
   try:
    r=_get(s,replay);body=r.content
    if len(body)>MAX_BYTES:raise ValueError('image exceeds 25 MB limit')
    validate_payload(body,'image');got=cdx_sha1(body)
    if got!=dig:raise ValueError(f'CDX digest mismatch: {got} != {dig}')
    sha=hashlib.sha256(body).hexdigest();ext='.jpg' if body.startswith(b'\xff\xd8\xff') else '.png' if body.startswith(b'\x89PNG') else '.gif' if body.startswith((b'GIF87a',b'GIF89a')) else '.webp' if body.startswith(b'RIFF') else '.img'
    rel=f'recovery/other-archives/press-articles/images/{ts}-{sha}{ext}';p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    m['image_captures'][key]={'source_image_url':image_url,'original_url':orig,'timestamp':ts,'replay_url':replay,'cdx_mime':mime,'cdx_digest':dig,'cdx_length':int(length),'cdx_sha1_verified':True,'bytes':len(body),'sha256':sha,'raw_path':rel,'source_pages':referrers,'rights_status':'unreviewed; local-only','relevance_status':'pending visual review'}
    report['image_payloads_recovered']+=1
   except Exception as e:report['failures'].append({'stage':'image_replay','url':orig,'timestamp':ts,'error':f'{type(e).__name__}: {e}'})
   report['image_capture_rows']+=1;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');time.sleep(delay)
  if report['image_payloads_recovered']>=image_limit:break
 report['page_capture_records_total']=len(m['page_captures']);report['unique_page_payloads_total']=len({x['sha256'] for x in m['page_captures'].values()})
 report['unique_linked_image_urls_total']=len(m['image_urls']);report['image_capture_records_total']=len(m['image_captures']);report['unique_image_payloads_total']=len({x['sha256'] for x in m['image_captures'].values()})
 report['unique_source_urls_queried_total']=len(m['sources'])
 report['image_relevance_review']={}
 for capture in m['image_captures'].values():
  status=capture.get('relevance_status','pending visual review')
  report['image_relevance_review'][status]=report['image_relevance_review'].get(status,0)+1
 report['pending_visual_review_records']=report['image_relevance_review'].get('pending visual review',0)
 m['last_report']=report;mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');(OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 return report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--delay',type=float,default=.8);ap.add_argument('--image-limit',type=int,default=100);ap.add_argument('--max-image-urls',type=int,default=100,help='bound new exact-image CDX lookups per run; use 0 for no cap');ap.add_argument('--image-page-before',help='ignore image references from page captures at or after this YYYYMMDDhhmmss timestamp');ap.add_argument('--additional-page-urls',help='JSON list/object or newline-separated file of observed source URLs to add to the built-in inventory');ap.add_argument('--only-image-url',help='query and recover capture variants for one exact source image URL');ap.add_argument('--only-source-page',help='recover only source-linked images from this exact article URL');ap.add_argument('--only-page-url',help='query and recover page mementos only for this exact source URL');ap.add_argument('--pages-only',action='store_true',help='query/recover selected HTML mementos without indexing or replaying linked images');ap.add_argument('--retry-image-index-errors',action='store_true',help='retry saved image CDX lookup failures after archive cooldown');a=ap.parse_args();extra=read_additional_page_urls(a.additional_page_urls);print(json.dumps(recover(a.delay,a.image_limit,a.only_image_url,a.only_source_page,a.retry_image_index_errors,a.only_page_url,a.pages_only,a.max_image_urls,a.image_page_before,extra),indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
