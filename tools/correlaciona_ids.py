# correlacion multiple: ids 4362, 1314, 4399, 1345 vs SETPOS binario
# y: el [19] (1345...) recibe 0x1c?  el 0x1c es la marca de propia?
import sys, json, re, bisect
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import parse_clear

log = open(r'C:/tmp/scanner_v5f.log', encoding='utf-8', errors='replace').read().splitlines()
raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

# SETPOS por entidad -> (dt, x, z)
setpos_by_ent = {}
for ln in log:
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=(0x[0-9a-f]+) x=([\d.]+) z=([\d.]+)', ln)
    if m:
        setpos_by_ent.setdefault(m.group(2), []).append((int(m.group(1)), float(m.group(3)), float(m.group(4))))

# wire: 0x00 por id, 0x1c por id
wire_00 = {}
wire_1c = {}
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
        if ev.tipo == 0x00 and ev.x is not None:
            wire_00.setdefault(ev.id, []).append((e.get('dt'), ev.x, ev.z))
        if ev.tipo == 0x1c:
            wire_1c.setdefault(ev.id, []).append(e.get('dt'))

# ids a probar: los del 0x1c y los del [19]
candidates = set(wire_1c.keys())
print('ids con 0x1c:', sorted(candidates))
print('ids con 0x00:', len(wire_00))

def best_match(wire_list, setpos_list):
    if not wire_list or not setpos_list:
        return None
    times = [s[0] for s in setpos_list]
    ok = 0
    dists = []
    for wt, wx, wz in wire_list:
        i = bisect.bisect_left(times, wt)
        best = None
        for j in (i-2, i-1, i, i+1, i+2):
            if 0 <= j < len(setpos_list):
                sx, sz = setpos_list[j][1], setpos_list[j][2]
                d = ((sx-wx)**2 + (sz-wz)**2) ** 0.5
                if best is None or d < best[0]:
                    best = (d, abs(setpos_list[j][0]-wt))
        if best and best[0] < 30:
            ok += 1
        if best:
            dists.append(best[0])
    return ok, len(wire_list), (sum(dists)/len(dists) if dists else 0)

for eid in sorted(candidates)[:14]:
    # encontrar la entidad binaria cuyo setpos coincide mejor
    results = []
    for ent, sl in setpos_by_ent.items():
        r = best_match(wire_00.get(eid, []), sl)
        if r and r[0] > 20:
            results.append((r[0], ent, r[1], r[2]))
    results.sort(reverse=True)
    n1c = len(wire_1c.get(eid, []))
    print('id=%s 0x1c=%d 0x00=%d -> %s' % (eid, n1c, len(wire_00.get(eid, [])), results[:2]))
