# encuentra saltos >100u en la captura v5f y que evento los causa
import sys, json
from collections import defaultdict
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import decode_clear_full, decode_dump_19

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

pos = {}  # eid -> (dt, x, z, tipo_evento, masa)
saltos = []
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
    dt = e.get('dt')
    try:
        if len(b) > 1 and b[1] == 0x04:
            ents, _s = decode_dump_19(b)
            origen = 'dump'
        else:
            ents, _p, _d, _pj, _s = decode_clear_full(b, return_pj=True)
            origen = 'clear'
    except Exception:
        continue
    for eid, ce in ents.items():
        if ce.x is None or ce.z is None:
            continue
        if eid in pos:
            odt, ox, oz, otipo, omasa = pos[eid]
            d = ((ox - ce.x) ** 2 + (oz - ce.z) ** 2) ** 0.5
            if d > 100.0:
                saltos.append((dt, eid, d, origen, otipo, omasa, ce.masa, ox, oz, ce.x, ce.z))
        pos[eid] = (dt, ce.x, ce.z, origen, ce.masa)

print('saltos >100u:', len(saltos))
# clasificar por masa anterior y origen
from collections import Counter
print('por origen:', Counter(s[3] for s in saltos))
peq = [s for s in saltos if (s[5] or 0) <= 5]
gra = [s for s in saltos if (s[5] or 0) > 5]
print('saltos de masa<=5 (pepitas):', len(peq), ' masa>5 (celulas):', len(gra))
for s in saltos[:12]:
    print('  dt=%d eid=%d d=%.0f origen=%s masa %s->%s pos (%s,%s)->(%s,%s)' % (
        s[0], s[1], s[2], s[3], s[5], s[6], s[7], s[8], s[9], s[10]))
