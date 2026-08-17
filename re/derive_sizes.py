#!/usr/bin/env python3
"""Deriva tamaños de eventos por tipo via constraint solving sobre payloads reales."""
import re, struct, os
from collections import Counter, defaultdict

LOGDIR = r"C:\Users\ren\Desktop\og mito"
LOGS = ["mito_view36.log", "mito_view35.log", "mito_view34.log", "mito_view33.log", "mito_view32.log"]

def extract_payloads(path):
    out = {}
    with open(path, "r", errors="replace") as f:
        for line in f:
            m = re.search(r"\[CLEAR\] ([0-9a-fA-F]+)", line)
            if m:
                h = m.group(1)
                if len(h) >= 4:
                    out.setdefault(h, 0)
                    out[h] += 1
    return out

allp = {}
for lg in LOGS:
    p = os.path.join(LOGDIR, lg)
    if os.path.exists(p):
        allp.update(extract_payloads(p))

# payloads como bytes
payloads = []
for h in allp:
    try:
        b = bytes.fromhex(h)
    except ValueError:
        continue
    if b[0] == 0x64 and not (len(b) > 1 and b[1] == 0x04):
        payloads.append(b)

# tipos reales candidatos (del doc + observados limpiamente)
CAND = {t: set() for t in range(0x00, 0x30)}
# tamaños candidatos por tipo: (doc) 01:15, 03:7, 04:var, 05:7, 06:3, 07:3, 14:5, 2d:5, 2f:3
CAND[0x00] = {7}
CAND[0x01] = {7, 15, 14}
CAND[0x02] = {3, 7, 0}
CAND[0x03] = {7, 9}
CAND[0x04] = {3, 7, 9, 11, 13, 15, 17, 19, 21}
CAND[0x05] = {7}
CAND[0x06] = {3, 7}
CAND[0x07] = {3}
CAND[0x08] = {7, 10}
for t in range(0x09, 0x13):
    CAND[t] = {3, 5, 7, 9, 10, 14, 15}

def try_parse(b, sizes, max_tail=6):
    """Devuelve eventos o None si no cubre."""
    i = 1
    events = []
    while i < len(b):
        t = b[i]
        if t not in sizes:
            return None
        s = sizes[t]
        if s == 0:
            # tipo 0x02: buffer de posicion? probar 0 bytes -> siguiente byte es tipo
            i += 1
            continue
        if s is None:
            return None
        if i + s > len(b):
            # cola truncada permitida
            if len(b) - i <= max_tail:
                return events
            return None
        events.append((t, b[i:i+s]))
        i += s
    return events

# DFS: para cada payload, conjuntos de tamaños consistentes
def solve(b, sizes, idx=0):
    """Devuelve lista de tablas de tamaño consistentes (parciales)."""
    results = []
    def dfs(pos, table):
        if pos >= len(b):
            results.append(dict(table))
            return
        t = b[pos]
        if t not in CAND:
            return
        for s in CAND[t]:
            if s == 0:
                table[t] = 0
                dfs(pos + 1, table)
            elif pos + s <= len(b):
                table[t] = s
                dfs(pos + s, table)
            else:
                # cola truncada: permitir si queda poco
                if len(b) - pos <= 6:
                    table[t] = s
                    dfs(len(b), table)
    dfs(1, {})
    return results

# analizar payloads con tipos raros
rare = Counter()
for b in payloads:
    for t in range(1, len(b)):
        pass
    # primer tipo
    t0 = b[1] if len(b) > 1 else -1
    rare[t0] += 1

print("=== Primer tipo de evento por payload (top 25) ===")
for t, c in rare.most_common(25):
    print("  0x%02x: %d" % (t, c))

# Para payloads cuyo primer tipo es raro, mostrar soluciones
print("\n=== Soluciones de tamaños para payloads con tipos raros ===")
seen_types = set()
shown = 0
for b in payloads:
    t0 = b[1] if len(b) > 1 else -1
    if t0 in (0x00, 0x03, 0x05, 0x06, 0x07):
        continue
    if t0 in seen_types and shown > 40:
        continue
    sols = solve(b, CAND)
    if sols:
        seen_types.add(t0)
        shown += 1
        print("payload %s (%d B):" % (b.hex()[:50], len(b)))
        for s in sols[:4]:
            evs = [(t, s.get(t)) for t in sorted(set(x[0] for x in []))]
            print("   tabla:", {hex(k): v for k, v in sorted(s.items())})
    else:
        print("payload %s (%d B): SIN SOLUCION" % (b.hex()[:50], len(b)))

# verificar id 36104
print("\n=== id 36104 (0x8d08) en payloads ===")
cnt = 0
for b in payloads:
    i = 1
    while i + 7 <= len(b):
        if b[i] == 0x00:
            eid = (b[i+1] << 8) | b[i+2]
            if eid == 0x8d08:
                cnt += 1
                if cnt <= 3:
                    print("  ", b.hex()[:80])
        i += 7
print("total:", cnt)
