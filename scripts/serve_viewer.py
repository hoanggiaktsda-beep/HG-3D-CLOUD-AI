"""Serve the sample viewer on loopback only; no deployment or external API."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'viewer'
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        super().end_headers()
print(f'HG viewer sample server: loopback port {a.port}',flush=True)
ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(ROOT))).serve_forever()
