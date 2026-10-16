import hashlib, asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

# Define the ASGI application to handle incoming HTTP requests asynchronously
async def app(scp, ric, inv):
    if scp['type'] == 'http':
        # Extract request details like path, method, and protocol version from the ASGI scope
        p = scp['path']
        m = scp['method']
        v = scp['http_version']

        # Root endpoint: advertise HTTP/3 availability to TCP clients using the Alt-Svc header
        if m == 'GET' and p == '/':
            hdrs = []

            if v in ['1.0', '1.1', '2']:
                hdrs.append((b'alt-svc', b'h3=":4433"'))
            await inv({'type': 'http.response.start', 'status': 200, 'headers': hdrs})
            await inv({'type': 'http.response.body', 'body': b''})

        # Protocol endpoint: inspect the scope and return the negotiated HTTP version as plain text
        elif m == 'GET' and p == '/proto':

            if v == '3':
                risp = b'HTTP/3'
            elif v == '2':
                risp = b'HTTP/2'
            else:
                risp = b'HTTP/1.1'

            await inv({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
            await inv({'type': 'http.response.body', 'body': risp})

        # Hash endpoint: asynchronously read the request body in chunks to properly handle QUIC streams
        elif m == 'POST' and p == '/hash':
            dati = b''
            continua = True

            while continua:
                msg = await ric()
                dati += msg.get('body', b'')
                continua = msg.get('more_body', False)

            # Calculate and return the SHA-256 hash of the complete received payload
            h = hashlib.sha256(dati).hexdigest().encode()
            await inv({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
            await inv({'type': 'http.response.body', 'body': h})

        # Fallback for unknown routes, returning a 404 error
        else:
            await inv({'type': 'http.response.start', 'status': 404, 'headers': []})
            await inv({'type': 'http.response.body', 'body': b''})


# Configure Hypercorn to bind on port 4433 for both standard TCP and QUIC (UDP) traffic using our certificates
cfg = Config()
cfg = Config()
cfg.bind = ["0.0.0.0:4433"]
cfg.quic_bind = ["0.0.0.0:4433"]
cfg.certfile = "cert.pem"
cfg.keyfile = "chiave.pem"

# Run the asynchronous server
asyncio.run(serve(app, cfg))