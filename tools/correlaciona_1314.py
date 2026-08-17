# correlacion: SETPOS de et=1314 (binario) vs eventos 0x00 id=1314 (wire)
import sys, json, re
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import parse_clear

log = open(r'C:/tmp/scanner_v5f.log', encoding='utf-8', errors='replace').read().splitlines()
raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

setpos_1314 = []
for ln in log:
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=0x[0-9a-f]+ x=([\d.]+) z=([\d.]+) rot=[\d.]+ et=1314', ln)
    if m:
        setpos_1314.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))

wire_1314 = []
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
        if ev.tipo == 0x00 and getattr(ev, 'id', None) == 1314 and ev.x is not None:
            wire_1314.append((e.get('dt'), ev.x, ev.z))

print('SETPOS binario et=1314:', len(setpos_1314), '  wire 0x00 id=1314:', len(wire_1314))
if setpos_1314 and wire_1314:
    print('SETPOS:', setpos_1314[0], '...', setpos_1314[-1])
    print('WIRE  :', wire_1314[0], '...', wire_1314[-1])
    # buscar para cada wire el setpos mas cercano
    import bisect
    times = [s[0] for s in setpos_1314]
    ok = 0
    deltas = []
    for wt, wx, wz in wire_1314:
        i = bisect.bisect_left(times, wt)
        best = None
        for j in (i-1, i, i+1):
            if 0 <= j < len(setpos_1314):
                sx, sz = setpos_1314[j][1], setpos_1314[j][2]
                d = ((sx-wx)**2 + (sz-wz)**2) ** 0.5
                if best is None or d < best[0]:
                    best = (d, abs(setpos_1314[j][0]-wt))
        if best and best[0] < 50:
            ok += 1
        if best:
            deltas.append(best[0])
    print('wire 0x00 con SETPOS binario a <50u:', ok, '/', len(wire_1314))
    if deltas:
        print('distancia media wire->setpos: %.1f u' % (sum(deltas)/len(deltas)))
