import socket
import threading


store = {}

store_lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[+] Con stab con {addr}")
    buffer = ""

    try:
        # Keep receiving data until the client disconnects
        while True:

            data = conn.recv(1024)
            if not data:
                break


            buffer += data.decode('ascii')

            # Process incoming data line by line
            while '\n' in buffer:

                line, buffer = buffer.split('\n', 1)


                line = line.strip()
                if not line:
                    continue

                # Split the command from its arguments
                parts = line.split(' ', 1)
                command = parts[0].upper()

                response = "ERR\n"

                # Simple ping-pong mechanism
                if command == "PING":
                    response = "PONG\n"

                # Return the exact same message back to the client
                elif command == "ECHO":
                    if len(parts) > 1:
                        response = f"{parts[1]}\n"
                    else:
                        response = "ERR\n"

                # Save key-value pairs safely using the thread lock
                elif command == "SET":

                    set_parts = line.split(' ', 2)
                    if len(set_parts) == 3:
                        key = set_parts[1]
                        value = set_parts[2]


                        with store_lock:
                            store[key] = value
                        response = "OK\n"
                    else:
                        response = "ERR\n"

                # Fetch the value from the store, return NOT_FOUND if missing
                elif command == "GET":
                    if len(parts) > 1:
                        key = parts[1]


                        with store_lock:
                            val = store.get(key)

                        if val is not None:
                            response = f"{val}\n"
                        else:
                            response = "NOT_FOUND\n"
                    else:
                        response = "ERR\n"

                # Send the response back to the client
                conn.sendall(response.encode('ascii'))

    except Exception as e:
        print(f"[-] Errore con {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Connessione chiusa con {addr}")


def main():
    host = '0.0.0.0'
    port = 9001

    # Initialize and bind the TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    print(f"[*] Server in ascolto sulla porta {port}...")

    # Listen for new connections and handle them concurrently
    try:
        while True:

            conn, addr = server.accept()

            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[*] Spegnimento del server.")
    finally:
        server.close()


if __name__ == "__main__":
    main()