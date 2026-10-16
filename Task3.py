import ssl, json, uuid, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

sess = {}


class Gestore(BaseHTTPRequestHandler):
    def do_GET(self):
        pt = self.server.server_port

        # Standard HTTPS server on port 8443
        if pt == 8443:
            if self.path == '/':
                self.send_response(200)
                self.end_headers()
            elif self.path == '/me':
                # Read the cookie header to check if the user is authenticated
                h_c = self.headers.get('Cookie')
                ck = SimpleCookie(h_c)

                # Return the username if the session ID is valid and exists in our dictionary
                if 'id_sess' in ck and ck['id_sess'].value in sess:
                    ut = sess[ck['id_sess'].value]
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"user": ut}).encode())
                else:
                    # Block access if the session cookie is missing or invalid
                    self.send_response(401)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        # mTLS server on port 8444
        elif pt == 8444:
            if self.path == '/whoami':
                # Extract the client's certificate and loop through the subject fields to find the Common Name (CN)
                crt = self.connection.getpeercert()
                cn = ""
                for cp in crt['subject']:
                    if cp[0][0] == 'commonName':
                        cn = cp[0][1]

                # Send back the extracted Common Name as plain text
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(cn.encode())
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        # Handle the login process on port 8443
        if self.server.server_port == 8443 and self.path == '/login':
            lung = int(self.headers.get('Content-Length', 0))
            dati = json.loads(self.rfile.read(lung))

            # Check the credentials and generate a secure session cookie if the password is correct
            if dati.get('password') == 'netsec':
                id_s = str(uuid.uuid4())
                sess[id_s] = dati.get('user')
                self.send_response(200)
                self.send_header('Set-Cookie', f'id_sess={id_s}; Secure; HttpOnly')
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()


def avvia_1():
    # Setup and start the standard HTTPS server with our self-signed certificate
    srv = HTTPServer(('0.0.0.0', 8443), Gestore)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile='cert.pem', keyfile='chiave.pem')
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    srv.serve_forever()


def avvia_2():
    # Setup and start the mTLS server, strictly requiring a client certificate signed by the course CA
    srv = HTTPServer(('0.0.0.0', 8444), Gestore)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile='cert.pem', keyfile='chiave.pem')
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations('ca.crt')
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    srv.serve_forever()

# Run both servers concurrently using threads
threading.Thread(target=avvia_1).start()
avvia_2()