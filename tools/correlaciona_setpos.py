#!/usr/bin/env python3
"""Correlacion temporal: para cada SETPOS del binario (posicion real aplicada),
buscar el evento del wire en el mismo instante y ver cual coincide."""
import sys, json, re
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
if 'haxe_clear_parser' in sys.modules:
    del sys.modules['haxe_clear_parser']
from haxe_clear_parser import parse_clear

# SETPOS del binario: (ms, ent, x, z)
setpos = []
for line in open(r'C:/tmp/scanner_v5d.log', encoding='utf-8', errors='replace'):
    m = re.search(r'(\d+)ms IN  SETPOS ent=(\S+) x=([-\d.]+) z=([-\d.]+)', line)
    if m:
        setpos.append((int(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))))

# eventos del wire agrupados por CLEAR con su dt
clears = []  # (dt, [(tipo, eid, x, z, vals)])
for line in open(r'C:/tmp/scanner_v5d.log.raw', encoding='utf-8', errors='replace'):
    if 'recv_clear' not in line:
        continue
    try:
        ev = json.loads(line)
    except Exception:
        continue
    hx = ev.get('hex', '').replace(' ', '')
    if not hx:
        continue
    b = bytes.fromhex(hx)
    if not b or b[0] != 0x64:
        continue
    dt = ev.get('dt', 0)
    events = parse_clear(b)
    evs = []
    for e in events:
        x = z = None
        if e.x is not None:
            x = e.x
        if e.z is not None:
            z = e.z
        evs.append((e.tipo, e.id, x, z))
    clears.append((dt, evs))

# para cada SETPOS, buscar el CLEAR mas cercano y los eventos con posicion parecida
matches = 0
for ms, ent, sx, sz in setpos[:2000]:
    # CLEAR mas cercano dentro de 40ms
    best = None
    best_dt = 999999
    for dt, evs in clears:
        if abs(dt - ms) < best_dt:
            best_dt = abs(dt - ms)
            best = (dt, evs)
    if best is None or best_dt > 40:
        continue
    dt, evs = best
    for tipo, eid, ex, ez in evs:
        if ex is not None and ez is not None:
            d = abs(ex - sx) + abs(ez - sz)
            if d < 2.0:  # coincidencia exacta
                matches += 1
                if matches <= 15:
                    print('SETPOS %dms ent=%s x=%.1f z=%.1f -> CLEAR %dms evento tipo=0x%02x eid=%s x=%.1f z=%.1f' % (
                        ms, ent, sx, sz, dt, tipo, eid, ex, ez))
                break

print('total coincidencias SETPOS<->evento:', matches)