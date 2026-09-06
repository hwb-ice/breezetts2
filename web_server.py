"""Local streaming UI, standard library only."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.request, urllib.error, json, re, time, socket
LOCAL_HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def split_text(text, budget):
    # Preserve punctuation and vocal-event brackets. First phrase is short;
    # later phrases are larger to amortize text-encoder overhead.
    units=re.findall(r'\[[^\]]*\]|\([^)]*\)|[^\[\(，。！？；,.!?;]+[，。！？；,.!?;]?|.',text)
    chunks=[]; current=''
    for unit in units:
        limit=min(budget,16) if not chunks else budget
        if current and len(current)+len(unit)>limit:
            chunks.append(current.strip());current=''
        current+=unit
    if current.strip(): chunks.append(current.strip())
    return chunks

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    def do_GET(self):
        if self.path not in ('/', '/app.js'):
            self.send_error(404); return
        filename = 'index.html' if self.path == '/' else 'app.js'
        data=(Path(__file__).parent/'web'/filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if filename.endswith('html') else 'text/javascript; charset=utf-8')
        self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        if self.path != '/speech': self.send_error(404); return
        size=int(self.headers.get('Content-Length',0))
        if size > 1024*1024: self.send_error(413); return
        try:
            payload=json.loads(self.rfile.read(size))
            budget=max(10,min(600,int(payload.get('options',{}).get('text_chunk_size',40))))
            # Native runtime now emits acoustic frames while generating a sentence.
            # Keep full text context and let the native long-text chunker handle it.
            chunks=[payload['input'].strip()] if payload['input'].strip() else []
            if not chunks: raise ValueError('Empty input')
        except (ValueError,KeyError) as e:
            self.send_error(400,str(e)); return
        self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.send_header('Cache-Control','no-cache'); self.end_headers()
        started=time.perf_counter();first=None
        try:
            for chunk in chunks:
                request_body={**payload,'input':chunk,'stream_format':'sse','response_format':'pcm'}
                req=urllib.request.Request('http://127.0.0.1:7860/v1/audio/speech',data=json.dumps(request_body).encode(),headers={'Content-Type':'application/json'})
                with LOCAL_HTTP.open(req,timeout=600) as response:
                    for line in response:
                        if not line.startswith(b'data: '): continue
                        raw=line[6:].strip()
                        if raw==b'[DONE]': continue
                        event=json.loads(raw)
                        if event.get('type')=='speech.audio.done': continue
                        if event.get('type')=='speech.audio.delta' and first is None: first=time.perf_counter()-started
                        self.wfile.write(b'data: '+raw+b'\n\n');self.wfile.flush()
            self.wfile.write(('data: '+json.dumps({'type':'speech.audio.done','timing':{'ttft_ms':first*1000 if first else None}})+'\n\ndata: [DONE]\n\n').encode());self.wfile.flush()
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception as e:
            self.wfile.write(('data: '+json.dumps({'type':'error','message':str(e)})+'\n\n').encode());self.wfile.flush()

if __name__=='__main__':
    print('Realtime UI: http://127.0.0.1:7861',flush=True)
    ThreadingHTTPServer(('127.0.0.1',7861),Handler).serve_forever()
