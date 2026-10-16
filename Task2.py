import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


dizionario_note = {}
prossimo_id = 1


class MioServerHTTP(BaseHTTPRequestHandler):

    # Helper method to send HTTP responses with an optional JSON body
    def invia_risposta(self, codice, corpo_json=None):

        self.send_response(codice)
        if corpo_json != None:
            self.send_header('Content-Type', 'application/json')

            byte_corpo = corpo_json.encode('utf-8')
            self.send_header('Content-Length', str(len(byte_corpo)))
            self.end_headers()
            self.wfile.write(byte_corpo)
        else:
            self.end_headers()

    # Handle incoming GET requests based on the URL path
    def do_GET(self):
        url_diviso = urlparse(self.path)
        percorso = url_diviso.path


        print(f"DEBUG: Ricevuta richiesta GET per il percorso -> {percorso}")

        if percorso == '/':
            # Root endpoint, just return 200 OK
            self.invia_risposta(200)

        # Extract the 'msg' parameter from the query string and return it as JSON
        elif percorso == '/echo':
            parametri = parse_qs(url_diviso.query)

            if 'msg' in parametri:
                messaggio = parametri['msg'][0]
            else:
                messaggio = ""

            diz_risposta = {"msg": messaggio}
            self.invia_risposta(200, json.dumps(diz_risposta))

        # Retrieve a specific note by extracting its ID from the URL
        elif percorso.startswith('/notes/'):

            pezzi_path = percorso.split('/')
            id_testo = pezzi_path[-1]

            try:
                id_nota = int(id_testo)
            except ValueError:
                print("DEBUG: Errore, l'id inserito non è un numero!")
                self.invia_risposta(404)
                return

            # Return the note if it exists, otherwise 404
            if id_nota in dizionario_note:
                testo_salvato = dizionario_note[id_nota]
                risposta_json = {"id": id_nota, "text": testo_salvato}
                self.invia_risposta(200, json.dumps(risposta_json))
            else:
                self.invia_risposta(404)

        elif percorso == '/notes':

            # GET on the collection itself is not supported
            self.invia_risposta(405)

        else:
            # Fallback for unknown paths
            self.invia_risposta(404)

    # Handle POST requests to create new notes
    def do_POST(self):
        url_diviso = urlparse(self.path)
        percorso = url_diviso.path

        if percorso == '/notes':
            tipo_contenuto = self.headers.get('Content-Type', '')
            print(f"DEBUG: Tipo di contenuto ricevuto = {tipo_contenuto}")

            # Enforce the application/json content type
            if 'application/json' not in tipo_contenuto:
                self.invia_risposta(415)
                return

            lunghezza = self.headers.get('Content-Length', '0')
            lunghezza_int = int(lunghezza)

            if lunghezza_int == 0:
                self.invia_risposta(400)
                return

            corpo_richiesta = self.rfile.read(lunghezza_int)

            # Parse and validate the incoming JSON payload
            try:
                dati_json = json.loads(corpo_richiesta)
            except Exception as e:
                print("DEBUG: Il JSON è malformato", e)
                self.invia_risposta(400)
                return

            # Ensure the 'text' field is present and is a string
            if "text" not in dati_json:
                self.invia_risposta(400)
                return


            if type(dati_json["text"]) != str:
                self.invia_risposta(400)
                return

            # Save the new note and increment the global ID counter
            global prossimo_id
            mio_id = prossimo_id
            dizionario_note[mio_id] = dati_json["text"]
            prossimo_id = prossimo_id + 1

            # Return the newly created note's ID
            risposta = {"id": mio_id}
            self.invia_risposta(201, json.dumps(risposta))

        elif percorso.startswith('/notes/'):

            # POST on specific items is not allowed
            self.invia_risposta(405)
        else:
            self.invia_risposta(404)

    # Handle DELETE requests to remove a specific note by ID
    def do_DELETE(self):
        url_diviso = urlparse(self.path)
        percorso = url_diviso.path

        if percorso.startswith('/notes/'):
            pezzi_path = percorso.split('/')
            id_testo = pezzi_path[-1]

            try:
                id_nota = int(id_testo)
            except ValueError:
                self.invia_risposta(404)
                return

            # Delete the note if found and return 204 No Content
            if id_nota in dizionario_note:

                del dizionario_note[id_nota]
                self.invia_risposta(204)
            else:
                self.invia_risposta(404)

        elif percorso == '/notes':
            self.invia_risposta(405)
        else:
            self.invia_risposta(404)

    # Reject any PUT requests with a 405 Method Not Allowed
    def do_PUT(self):

        if self.path == '/notes' or self.path.startswith('/notes/'):
            self.invia_risposta(405)
        else:
            self.invia_risposta(404)


# Initialize and start the HTTP server on port 8080
def avvia_server():
    indirizzo = ('0.0.0.0', 8080)
    mio_server = HTTPServer(indirizzo, MioServerHTTP)
    print("=== Server HTTP in ascolto sulla porta 8080 ===")

    try:

        mio_server.serve_forever()
    except KeyboardInterrupt:
        print("\nChiusura server...")

    mio_server.server_close()


if __name__ == '__main__':
    avvia_server()