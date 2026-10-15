"""Run with `python -m restore --help`; network and offline operations are separate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .archive import ArchiveClient
from .build import build,promote
from .check import check
from .recover import index,recover,summary
from .state import State,write_json
from .urls import base_path

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
    idx=commands.add_parser('index',help='Enumerate captures and persist the continuation cursor')
    idx.add_argument('--url',default='bluescholars.com');idx.add_argument('--match',choices=['domain','exact','prefix'],default='domain')
    idx.add_argument('--max-pages',type=int,default=20)
    rec=commands.add_parser('recover',help='Download original responses and discover dependencies')
    rec.add_argument('--max-files',type=int,default=150);rec.add_argument('--retry-failed',action='store_true')
    for p in (idx,rec):
        p.add_argument('--delay',type=float,default=1.2);p.add_argument('--timeout',type=int,default=30);p.add_argument('--retries',type=int,default=3)
    for name in ('build','check','serve'):
        p=commands.add_parser(name)
        p.add_argument('--candidate',action='store_true',help='Use unreviewed downloaded sources in _candidate')
        p.add_argument('--base-path',default='',help='Empty for domain root, /bluescholars for project Pages')
        if name=='build':p.add_argument('--release',action='store_true',help='Require explicit visual/publish approval and original homepage/CSS')
        if name=='serve':p.add_argument('--port',type=int,default=8080)
    p=commands.add_parser('promote',help='Copy inspected downloads into the reviewed source collection')
    p.add_argument('--reviewed',action='store_true');p.add_argument('--allow-later',action='store_true')
    p=commands.add_parser('approve',help='Record an explicit visual and publication review')
    p.add_argument('--visual-reviewed',action='store_true');p.add_argument('--publish-approved',action='store_true')
    args=parser.parse_args(argv);root=args.root.resolve()
    try:
        if args.command=='seed':
            s=State(root);s.seed();result=summary(s)
        elif args.command=='status':result=summary(State(root))
        elif args.command in ('index','recover'):
            if args.delay<0 or args.timeout<1 or args.retries<1: raise ValueError('Invalid network limits')
            client=ArchiveClient(delay=args.delay,timeout=args.timeout,retries=args.retries)
            s=State(root)
            if not s.data['resources']:s.seed()
            if args.command=='index':
                if args.max_pages<1:raise ValueError('--max-pages must be positive')
                result=index(s,client,args.max_pages,args.url,args.match)
                print(json.dumps(result,indent=2));return 2 if result.get('last_error') and not result.get('complete') else 0
            if args.max_files<1:raise ValueError('--max-files must be positive')
            result=recover(s,client,args.max_files,args.retry_failed)
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
