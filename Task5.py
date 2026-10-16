import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

tk = ""

# Handler for the Tor Hidden Service listening on local port 8080
class Gest_Tor(BaseHTTPRequestHandler):
    def do_GET(self):
        # Simple health check endpoint for Tor
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global tk
        # Receive the ownership token from the university via Tor and save it globally
        if self.path == '/claim':
            l = int(self.headers.get('Content-Length', 0))
            tk = self.rfile.read(l).decode()
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

# Handler exposed on the VPN network to prove ownership
class Gest_VPN(BaseHTTPRequestHandler):
    def do_GET(self):
        global tk
        # Return the previously saved token to pass the verification step
        if self.path == '/claim':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(tk.encode())
        else:
            self.send_response(404)
            self.end_headers()

# Start the Tor-facing server strictly on localhost
def run_t():
    s = HTTPServer(('127.0.0.1', 8080), Gest_Tor)
    s.serve_forever()


def run_v():
    # Start the VPN-facing server on all interfaces to allow external checks
    s = HTTPServer(('0.0.0.0', 8090), Gest_VPN)
    s.serve_forever()

# Run both servers concurrently using a separate thread for the Tor one
threading.Thread(target=run_t).start()
run_v()