import os
import subprocess



# estraggo stream, SNI e fingerprint JA4 dai ClientHello usando tshark
pcap_file = "capture-3 (task2).pcap"
tshark = r"C:\Program Files\Wireshark\tshark.exe"
if not os.path.exists(tshark):
    tshark = r"C:\Program Files (x86)\Wireshark\tshark.exe"

cmd = [
    tshark, "-r", pcap_file,
    "-Y", "tls.handshake.type == 1",
    "-T", "fields",
    "-e", "tcp.stream",
    "-e", "tls.handshake.extensions_server_name",
    "-e", "tls.handshake.ja4"
]

res = subprocess.run(cmd, capture_output=True, text=True, check=True)
print("STDERR:", res.stderr)
print("PRIME 5 RIGHE:\n", "\n".join(res.stdout.splitlines()[:5]))

rows = []
malware_ja4 = None

# leggo riga per riga e cerco il JA4 associato a syncbridge.example
for line in res.stdout.strip().splitlines():
    parts = line.split("\t")
    if len(parts) < 3:
        continue
    stream, sni, ja4 = parts[0], parts[1], parts[2]
    rows.append((stream, sni, ja4))
    if "syncbridge.example" in sni:
        malware_ja4 = ja4
        print("Trovato C2:", stream, sni, ja4)

# prendo tutti i domini contattati con lo stesso JA4 (escluso il C2)
hex_parts = []
for stream, sni, ja4 in rows:
    if ja4 == malware_ja4:
        first_label = sni.split(".")[0]
        print(f"Stream {stream} -> {sni} ({first_label})")
        hex_parts.append(first_label)

flag = "netsec{" + "".join(hex_parts) + "}"
print("\nFlag:", flag)