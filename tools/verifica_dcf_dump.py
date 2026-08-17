# decode_clear_full sobre dumps reales: devuelve self_ids y owners?
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import decode_clear_full

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

n = 0
self_total = {}
owners = {}
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
    if len(b) <= 1 or b[1] != 0x04:
        continue  # solo dumps
    try:
        ents, pid, dead, pj, self_ids = decode_clear_full(b, return_pj=True)
    except Exception as ex:
        print('ERR', ex)
        continue
    n += 1
    for sid in self_ids:
        self_total[sid] = self_total.get(sid, 0) + 1
    for eid, ce in ents.items():
        ow = getattr(ce, 'owner', 0) or 0
        if ow:
            owners.setdefault(ow, set()).add(eid)

print('dumps:', n)
print('self_ids totales:', sum(self_total.values()), 'unicos:', len(self_total))
print('top self_ids:', sorted(self_total.items(), key=lambda kv: -kv[1])[:20])
# owners: cuantos owners distintos y sus entidades
print('owners distintos:', len(owners))
top_o = sorted(owners.items(), key=lambda kv: -len(kv[1]))[:8]
for ow, eids in top_o:
    print('  owner=%s (%d entidades): %s' % (ow, len(eids), sorted(eids)[:6]))
