# busca eventos 0x19/0x1a y 0x1c en los CLEARs de v5f: contenido
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import parse_clear

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

counts = {}
for ln in raw:
    if not ln.startswith('{'):
        continue
    try:
        e = json.loads(ln)
    except Exception:
        continue
    if e.get('what') != 'recv_clear':
        continue
    hx = e.get('hex', '')
    try:
        b = bytes.fromhex(hx.replace(' ', ''))
    except Exception:
        continue
    if not b or b[0] != 0x64:
        continue
    try:
        evs = parse_clear(b)
    except Exception:
        continue
    for ev in (evs or []):
        if ev.tipo in (0x19, 0x1a, 0x1c, 0x1e, 0x1f, 0x28, 0x2a, 0x0d, 0x0c):
            key = (ev.tipo, ev.id, ev.x, ev.z, ev.masa, ev.valor)
            counts[key] = counts.get(key, 0) + 1

for (t, eid, x, z, masa, val), c in sorted(counts.items(), key=lambda kv: -kv[1])[:40]:
    print('tipo=0x%02x id=%s x=%s z=%s masa=%s val=%s x%d' % (t, eid, x, z, masa, val, c))
