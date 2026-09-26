from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


class Handler(BaseHTTPRequestHandler):
    requests=[]
    def do_GET(self):
        type(self).requests.append((self.path,self.headers.get("content-type",""),b""))
        payload=b'{"ok":true,"result":{"message_id":42,"username":"fake_bot"}}'
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(payload)
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get("content-length","0")))
        type(self).requests.append((self.path,self.headers.get("content-type",""),body))
        payload=b'{"ok":true,"result":{"message_id":42,"username":"fake_bot"}}'
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(payload)
    def log_message(self,*args): pass


class FakeTelegram:
    def __enter__(self):
        Handler.requests=[]; self.server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        self.thread=Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"; return self
    def __exit__(self,*args): self.server.shutdown(); self.thread.join(); self.server.server_close()
    @property
    def requests(self): return Handler.requests
