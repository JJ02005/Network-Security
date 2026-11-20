import re
from scapy.all import rdpcap, IP, TCP, Raw

pkts = rdpcap("capture-3.pcap")

# Firma SYN per ogni stream 
sigs = {}
traces = {}
admin_sport = None

for p in pkts:
    if not (p.haslayer(IP) and p.haslayer(TCP)):
        continue

    ip, tcp = p[IP], p[TCP]

    # Pacchetto SYN dal client (198.51.100.7)
    if ip.src == "198.51.100.7" and tcp.flags == "S":
        opts = [o[0] for o in tcp.options]
        mss = next((o[1] for o in tcp.options if o[0] == "MSS"), None)
        ws = next((o[1] for o in tcp.options if o[0] == "WScale"), None)
        sigs[tcp.sport] = (ip.ttl, tcp.window, mss, ws, tuple(opts))

    # Payload HTTP dal client
    if ip.src == "198.51.100.7" and p.haslayer(Raw):
        data = p[Raw].load.decode(errors="ignore")
        if "POST /admin/login" in data:
            admin_sport = tcp.sport
        m = re.search(r"X-Trace:\s*(\d+)-([0-9a-fA-F]{6})", data)
        if m:
            traces[tcp.sport] = (int(m.group(1)), m.group(2))

target_sig = sigs[admin_sport]
print("Admin sport:", admin_sport)
print("Firma SYN:", target_sig)

# Prendo tutti gli stream con la stessa firma SYN
parts = {}
for sport, sig in sigs.items():
    if sig == target_sig and sport in traces:
        n, val = traces[sport]
        parts[n] = val
        print(f"Stream {sport} -> pezzo {n}: {val}")

token = "".join(parts[i] for i in sorted(parts))
print(f"\nFlag: netsec{{{token}}}")