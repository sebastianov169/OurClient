# correlacion: 0x00 id=4362 (wire) vs SETPOS binario et=1331 masa 127-147
import sys, json, re
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import parse_clear

log = open(r'C:/tmp/scanner_v5f.log', encoding='utf-8', errors='replace').read().splitlines()
raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

# SETPOS de la entidad principal (0x1524f88b784) - la que tiene masa 127-147
setpos_ent = []
for ln in log:
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=0x1524f88b784 x=([\d.]+) z=([\d.]+)', ln)
    if m:
        setpos_ent.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))

# 0x00 con id=4362 del wire
wire_4362 = []
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
        if ev.tipo == 0x00 and getattr(ev, 'id', None) == 4362 and ev.x is not None:
            wire_4362.append((e.get('dt'), ev.x, ev.z))

print('SETPOS ent principal:', len(setpos_ent), ' wire 0x00 id=4362:', len(wire_4362))
if setpos_ent and wire_4362:
    print('SETPOS:', setpos_ent[:3], '...', setpos_ent[-3:])
    print('WIRE  :', wire_4362[:3], '...', wire_4362[-3:])
    import bisect
    times = [s[0] for s in setpos_ent]
    ok = 0
    dists = []
    for wt, wx, wz in wire_4362:
        i = bisect.bisect_left(times, wt)
        best = None
        for j in (i-2, i-1, i, i+1, i+2):
            if 0 <= j < len(setpos_ent):
                sx, sz = setpos_ent[j][1], setpos_ent[j][2]
                d = ((sx-wx)**2 + (sz-wz)**2) ** 0.5
                if best is None or d < best[0]:
                    best = (d, abs(setpos_ent[j][0]-wt))
        if best and best[0] < 30:
            ok += 1
        if best:
            dists.append(best[0])
    print('coinciden <30u:', ok, '/', len(wire_4362))
    if dists:
        print('dist media: %.1f u' % (sum(dists)/len(dists)))
