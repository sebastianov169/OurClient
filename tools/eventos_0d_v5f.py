# lista todos los eventos 0x0d y 0x1c: id, masa, posicion, val, dt
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import parse_clear

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

rows = []
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
        if ev.tipo in (0x0d, 0x1c, 0x0c):
            rows.append((e.get('dt'), ev.tipo, ev.id, ev.masa, ev.x, ev.z, ev.valor))

print('total rows:', len(rows))
# agrupar por id: cuantos de cada
from collections import Counter
by_id = Counter((t, i) for _, t, i, _, _, _, _ in rows)
print('por (tipo,id):', by_id.most_common(25))
print()
# 0x0d de cada id: primera y ultima masa
masas = {}
for dt, t, i, m, x, z, v in rows:
    if t == 0x0d and m is not None:
        masas.setdefault(i, []).append((dt, m))
print('0x0d masas por id:')
for i, lst in sorted(masas.items()):
    print('  id=%d: %d muestras, masa %s -> %s' % (i, len(lst), lst[0], lst[-1]))
