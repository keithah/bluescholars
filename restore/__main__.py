"""Run with `python -m restore --help`; network and offline operations are separate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .archive import ArchiveClient
from .build import build,promote
from .arquivo import harvest as harvest_arquivo,harvest_domain as harvest_arquivo_domain
from .commoncrawl import harvest as harvest_commoncrawl,import_rows as import_commoncrawl_rows
from .merge import merge_artifact
from .check import check
from .recover import index,recover,summary,now,capture_variant,capture_era,index_seed_assets
from .state import State,write_json
from .urls import base_path
from .artist_sites import (index_artist_sites,recover_artist_sites,promote_artist_sites,
                           review_artist_capture)
from .massline import index_massline,index_massline_history,recover_massline

def serve(directory: Path,base: str,port: int):
    from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
    from urllib.parse import urlsplit
    base=base_path(base)
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kw): super().__init__(*args,directory=str(directory),**kw)
        def translate_path(self,path):
            return super().translate_path(path[len(base):] if base else path)
        def send_head(self):
            path=urlsplit(self.path).path
            if base and path=='/':
                self.send_response(302);self.send_header('Location',base+'/');self.end_headers();return None
            if base and not (path==base or path.startswith(base+'/')):
                self.send_error(404);return None
            return super().send_head()
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Preview: http://127.0.0.1:{port}{base}/',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='Blue Scholars archive recovery and offline static build')
    parser.add_argument('--root',type=Path,default=Path.cwd(),help='Project directory (place before command)')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('seed',help='Load previously observed archive URLs')
    commands.add_parser('status',help='Show acquisition counts without network access')
    p=commands.add_parser('commoncrawl',help='Search all published Common Crawl collections and preserve source WARC responses')
    p.add_argument('--max-records',type=int,default=1800);p.add_argument('--workers',type=int,default=4)
    p=commands.add_parser('arquivo',help='Search and preserve inventoried Blue Scholars page captures from Arquivo.pt')
    p.add_argument('--history-url',default='bluescholars.com',help='Domain inventory or exact URL history to enumerate')
    p.add_argument('--max-urls',type=int,default=200,help='Maximum exact page histories to query this resumable batch')
    p.add_argument('--delay',type=float,default=0.5,help='Delay between Arquivo.pt history requests')
    p=commands.add_parser('arquivo-domain',help='Enumerate Arquivo.pt domain CDX and preserve latest captures for every edition')
    p.add_argument('--max-records',type=int,default=500);p.add_argument('--delay',type=float,default=0.5)
    p=commands.add_parser('commoncrawl-import',help='Import saved Common Crawl CDX rows from a JSONL file')
    p.add_argument('--rows',type=Path,required=True);p.add_argument('--collection',required=True)
    p=commands.add_parser('artist-index',help='Index dated Internet Archive captures for Prometheus Brown and Sabzi')
    p.add_argument('--delay',type=float,default=0.2)
    p=commands.add_parser('artist-recover',help='Recover linked pages and local visual assets for each dated artist-site edition')
    p.add_argument('--max-files',type=int,default=1800);p.add_argument('--delay',type=float,default=0.6);p.add_argument('--retry-failed',action='store_true')
    p=commands.add_parser('artist-compatibility-review',help='Record an individual later-page compatibility decision')
    p.add_argument('--edition',required=True,help='Edition key, e.g. sabzi.co/2013')
    p.add_argument('--url',required=True);p.add_argument('--reason',required=True)
    p=commands.add_parser('artist-promote',help='Promote inspected artist-site sources; later captures need individual compatibility notes')
    p.add_argument('--reviewed',action='store_true')
    commands.add_parser('massline-index',help='Validate and summarize the saved masslinemedia.com Wayback CDX inventory')
    p=commands.add_parser('massline-history',help='Page and checkpoint uncollapsed Mass Line Wayback capture history')
    p.add_argument('--max-pages',type=int,default=1);p.add_argument('--delay',type=float,default=0.8);p.add_argument('--timeout',type=int,default=60)
    p=commands.add_parser('massline-recover',help='Resumably recover Mass Line Media pages, forum threads, and local assets')
    p.add_argument('--max-files',type=int,default=250);p.add_argument('--delay',type=float,default=0.6);p.add_argument('--retry-failed',action='store_true')
    p=commands.add_parser('merge-recovery',help='Safely merge a downloaded recovery artifact from a staging directory')
    p.add_argument('--artifact',type=Path,required=True);p.add_argument('--run-id',required=True)
    idx=commands.add_parser('index',help='Enumerate captures and persist the continuation cursor')
    idx.add_argument('--url',default='bluescholars.com');idx.add_argument('--match',choices=['domain','exact','prefix'],default='domain')
    idx.add_argument('--max-pages',type=int,default=20)
    assets=commands.add_parser('index-assets',help='Index exact image URLs in the expanded source inventory')
    assets.add_argument('--max-assets',type=int,default=100);assets.add_argument('--max-pages',type=int,default=3)
    rec=commands.add_parser('recover',help='Download original responses and discover dependencies')
    rec.add_argument('--max-files',type=int,default=150);rec.add_argument('--retry-failed',action='store_true')
    p=commands.add_parser('capture',help='Preserve an exact Wayback capture as a dated variant')
    p.add_argument('--url',required=True);p.add_argument('--timestamp',required=True)
    p.add_argument('--kind',choices=['html','css','image','font'],help='Override extension inference for source-linked external resources')
    capture=p
    p=commands.add_parser('capture-era',help='Preserve the last available capture per URL for a historical site era')
    p.add_argument('--era',choices=['2007','2009','2013'],required=True)
    p.add_argument('--max-files',type=int,default=2000)
    capture_era_command=p
    for p in (idx,rec,capture,capture_era_command):
        p.add_argument('--delay',type=float,default=1.2);p.add_argument('--timeout',type=int,default=30);p.add_argument('--retries',type=int,default=3)
    for name in ('build','check','serve'):
        p=commands.add_parser(name)
        p.add_argument('--candidate',action='store_true',help='Use unreviewed downloaded sources in _candidate')
        p.add_argument('--base-path',default='',help='Empty for domain root, /bluescholars for project Pages')
        if name=='build':p.add_argument('--release',action='store_true',help='Require explicit visual/publish approval and original homepage/CSS')
        if name=='serve':p.add_argument('--port',type=int,default=8080)
    p=commands.add_parser('promote',help='Copy inspected downloads into the reviewed source collection')
    p.add_argument('--reviewed',action='store_true')
    p.add_argument('--allow-later',action='store_true',help=argparse.SUPPRESS)
    p=commands.add_parser('compatibility-review',help='Record an individual later-capture compatibility decision')
    p.add_argument('--url',required=True);p.add_argument('--reason',required=True)
    p=commands.add_parser('approve',help='Record an explicit visual and publication review')
    p.add_argument('--visual-reviewed',action='store_true');p.add_argument('--publish-approved',action='store_true')
    args=parser.parse_args(argv);root=args.root.resolve()
    try:
        if args.command=='seed':
            s=State(root);s.seed();result=summary(s)
        elif args.command=='status':result=summary(State(root))
        elif args.command=='commoncrawl':
            if args.max_records<1 or args.workers<1:raise ValueError('Common Crawl limits must be positive')
            result=harvest_commoncrawl(root,args.max_records,args.workers)
        elif args.command=='arquivo': result=harvest_arquivo(root,args.history_url,args.max_urls,args.delay)
        elif args.command=='arquivo-domain':
            result=harvest_arquivo_domain(root,args.max_records,args.delay)
            print(json.dumps(result,indent=2));return 2 if result.get('index_error') else 0
        elif args.command=='commoncrawl-import':
            rows=[json.loads(line) for line in args.rows.read_text().splitlines() if line.strip()]
            result=import_commoncrawl_rows(root,args.collection,rows)
        elif args.command=='artist-index':
            if args.delay<0:raise ValueError('--delay must not be negative')
            result=index_artist_sites(root,args.delay)
        elif args.command=='artist-recover':
            if args.max_files<1 or args.delay<0:raise ValueError('Invalid artist-site recovery limits')
            result=recover_artist_sites(root,args.max_files,args.delay,
                progress=lambda p:print(json.dumps({'stage':'artist-recover','progress':p}),file=sys.stderr,flush=True),
                retry_failed=args.retry_failed)
        elif args.command=='artist-compatibility-review':
            result=review_artist_capture(root,args.edition,args.url,args.reason)
        elif args.command=='artist-promote':
            result=promote_artist_sites(root,args.reviewed)
        elif args.command=='massline-index':result=index_massline(root)
        elif args.command=='massline-history':
            result=index_massline_history(root,args.max_pages,args.delay,args.timeout)
            print(json.dumps(result,indent=2));return 2 if result.get('errors') else 0
        elif args.command=='massline-recover':
            if args.max_files<1 or args.delay<0:raise ValueError('Invalid Massline recovery limits')
            result=recover_massline(root,args.max_files,args.delay,args.retry_failed,
                progress=lambda p:print(json.dumps({'stage':'massline-recover','progress':p}),file=sys.stderr,flush=True))
        elif args.command=='merge-recovery': result=merge_artifact(root,args.artifact,args.run_id)
        elif args.command=='index-assets':
            if args.max_assets<1 or args.max_pages<1:raise ValueError('Asset index limits must be positive')
            client=ArchiveClient()
            result=index_seed_assets(State(root),client,args.max_assets,args.max_pages)
        elif args.command in ('index','recover','capture','capture-era'):
            if args.delay<0 or args.timeout<1 or args.retries<1: raise ValueError('Invalid network limits')
            client=ArchiveClient(delay=args.delay,timeout=args.timeout,retries=args.retries)
            s=State(root)
            if not s.data['resources']:s.seed()
            if args.command=='index':
                if args.max_pages<1:raise ValueError('--max-pages must be positive')
                result=index(s,client,args.max_pages,args.url,args.match)
                print(json.dumps(result,indent=2));return 2 if result.get('last_error') and not result.get('complete') else 0
            if args.command=='capture':
                result=capture_variant(s,client,args.url,args.timestamp,args.kind)
                print(json.dumps(result,indent=2));return 0
            if args.command=='capture-era':
                if args.max_files<1:raise ValueError('--max-files must be positive')
                result=capture_era(s,client,args.era,args.max_files)
                print(json.dumps(result,indent=2));return 0
            if args.max_files<1:raise ValueError('--max-files must be positive')
            result=recover(s,client,args.max_files,args.retry_failed,
                progress=lambda p:print(json.dumps({'stage':'recover','progress':p}),file=sys.stderr,flush=True))
            print(json.dumps(result,indent=2))
            return 2 if result['unique_downloaded_files']==0 and result['failed_attempts'] else 0
        elif args.command in ('build','check','serve'):
            output=root/('_candidate' if args.candidate else '_site')
            if args.command=='build':result=build(root,output,args.base_path,args.candidate,args.release)
            elif args.command=='check':
                if not (output/'index.html').is_file():raise ValueError('Build the site before checking it')
                errors=check(output,args.base_path)
                print(json.dumps({'ok':not errors,'errors':errors},indent=2));return 1 if errors else 0
            else:
                if not output.exists():raise ValueError('Build the site before serving it')
                if not 1<=args.port<=65535:raise ValueError('Invalid port')
                serve(output,args.base_path,args.port);return 0
        elif args.command=='promote': result=promote(root,args.reviewed,args.allow_later)
        elif args.command=='compatibility-review':
            state=State(root);record=state.data['resources'].get(args.url)
            if record is None: raise ValueError('URL is not in the recovery inventory')
            if record.get('status')!='needs_review': raise ValueError('Only a downloaded later capture can be reviewed')
            if record.get('compatibility_review'): raise ValueError('This resource already has a compatibility review')
            reason=args.reason.strip()
            if not reason: raise ValueError('A resource-specific evidence note is required')
            review={'actor':'Codex agent','reviewed_at':now(),'capture':record.get('actual_capture'),
                    'sha256':record.get('sha256'),'reason':reason}
            record['compatibility_review']=review;state.save();result={'url':args.url,**review}
        else:
            if not args.visual_reviewed or not args.publish_approved:
                raise ValueError('Both --visual-reviewed and --publish-approved are required')
            report=build(root,root/'_site')
            if report['recovered_pages']==0 or report['local_source_assets']==0:
                raise ValueError('Original pages and assets must be recovered before approval')
            result={'visual_reviewed':True,'publish_approved':True,'note':'Explicit owner review recorded through CLI.'}
            write_json(root/'source/review.json',result)
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,KeyError) as exc:
        print(f'Error: {exc}',file=sys.stderr);return 1

if __name__=='__main__': raise SystemExit(main())
