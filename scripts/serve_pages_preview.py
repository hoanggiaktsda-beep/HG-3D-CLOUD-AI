"""Preview only packaged public site at project subpath; loopback, no deployment."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]/'viewer/dist'
BASE='/HG-3D-CLOUD-AI'
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);a=p.parse_args()
if not (ROOT/'build-manifest.json').exists():raise SystemExit('Run npm run build in viewer first')
class Handler(SimpleHTTPRequestHandler):
    def route(self):
        path=urlsplit(self.path).path
        if path==BASE:
            self.send_response(301);self.send_header('Location',BASE+'/');self.end_headers();return False
        if not path.startswith(BASE+'/'):
            self.send_error(404);return False
        self.path=self.path[len(BASE):]
        return True
    def do_GET(self):
        if self.route():super().do_GET()
    def do_HEAD(self):
        if self.route():super().do_HEAD()
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
print('Static Pages preview: loopback port '+str(a.port)+'; path '+BASE+'/',flush=True)
ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(ROOT))).serve_forever()
