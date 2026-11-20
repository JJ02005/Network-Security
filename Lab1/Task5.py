import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

tk = ""

class Gest_Tor(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.send_header('Connection', 'close')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.send_header('Connection', 'close')
            self.end_headers()

    def do_POST(self):
        global tk
        if self.path == '/claim':
            l = int(self.headers.get('Content-Length', 0))
            tk = self.rfile.read(l).decode()
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.send_header('Connection', 'close')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.send_header('Connection', 'close')
            self.end_headers()

class Gest_VPN(BaseHTTPRequestHandler):
    def do_GET(self):
        global tk
        if self.path == '/claim':
            r = tk.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(r)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(r)
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.send_header('Connection', 'close')
            self.end_headers()

def run_t():
    s = ThreadingHTTPServer(('127.0.0.1', 8080), Gest_Tor)
    s.serve_forever()

def run_v():
    s = ThreadingHTTPServer(('0.0.0.0', 8090), Gest_VPN)
    s.serve_forever()

threading.Thread(target=run_t, daemon=True).start()
run_v()