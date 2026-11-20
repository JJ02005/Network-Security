import ssl
import json
import uuid
import threading

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

sess = {}


class Gestore(BaseHTTPRequestHandler):
    def do_GET(self):
        pt = self.server.server_port


        if pt == 8443:
            if self.path == '/':
                self.send_response(200)
                self.end_headers()
            elif self.path == '/me':
                h_c = self.headers.get('Cookie')

                ck = SimpleCookie(h_c) if h_c else SimpleCookie()

                if 'id_sess' in ck and ck['id_sess'].value in sess:
                    ut = sess[ck['id_sess'].value]
                    risposta = json.dumps({"user": ut}).encode()

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(risposta)))
                    self.end_headers()
                    self.wfile.write(risposta)
                else:
                    self.send_response(401)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()


        elif pt == 8444:
            if self.path == '/whoami':
                crt = self.connection.getpeercert()
                cn = ""


                if crt and 'subject' in crt:
                    for cp in crt['subject']:
                        if cp[0][0] == 'commonName':
                            cn = cp[0][1]

                risposta = cn.encode()

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', str(len(risposta)))
                self.end_headers()
                self.wfile.write(risposta)
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        if self.server.server_port == 8443 and self.path == '/login':
            lung = int(self.headers.get('Content-Length', 0))
            dati = json.loads(self.rfile.read(lung))

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

    srv = ThreadingHTTPServer(('0.0.0.0', 8443), Gestore)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile='cert.pem', keyfile='chiave.pem')
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    srv.serve_forever()


def avvia_2():

    srv = ThreadingHTTPServer(('0.0.0.0', 8444), Gestore)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile='cert.pem', keyfile='chiave.pem')
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations('ca.crt')
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    srv.serve_forever()



threading.Thread(target=avvia_1, daemon=True).start()
avvia_2()