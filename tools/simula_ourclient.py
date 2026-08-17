# simula el flujo del OurClient sobre la captura v5f:
# decode_clear_full -> _feed (como network.py) -> player_entity_id + posicion
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\OurClient')
from haxe_clear_parser import decode_clear_full
from world import World

w = World()
raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

import time
n = 0
frozen = 0
positions = []
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
        ents, pid, dead, pj, self_ids = decode_clear_full(b, return_pj=True)
    except Exception:
        continue
    n += 1
    for sid in self_ids:
        w.player_cells.add(sid)
    if dead:
        for did in dead:
            w.remove(did)
    if ents:
        # mini-feed como network.py
        now = time.time()
        try:
            with w.lock:
                for eid, ce in ents.items():
                    old = w.entities.get(eid)
                    e = w.upsert(eid, getattr(ce, "entityType", 0) or 0)
                    if old is not None and old.grid_x is not None and old.grid_y is not None:
                        nx = old.grid_x if ce.x is None else ce.x
                        nz = old.grid_y if ce.z is None else ce.z
                        if nx != old.grid_x or nz != old.grid_y:
                            w._ent_prev[eid] = (old.grid_x, old.grid_y, now)
                    if ce.x is None:
                        ce.x = old.grid_x if old is not None else None
                    if ce.z is None:
                        ce.z = old.grid_y if old is not None else None
                    if (ce.masa is None or ce.masa <= 0) and old is not None:
                        ce.masa = old.masa
                    et = getattr(ce, "entityType", 0) or 0
                    if et != 6 and ce.x is not None and ce.z is not None:
                        e.grid_x, e.grid_y = ce.x, ce.z
                    if ce.masa and ce.masa > 0:
                        e.masa = ce.masa
                    e._last_seen = now
        except Exception:
            pass
        # elegir main de mayor masa
        if self_ids:
            with w.lock:
                valid = [sid for sid in self_ids
                         if sid in w.entities
                         and w.entities[sid].grid_x is not None]
            if valid:
                best = max(valid, key=lambda sid: w.entities[sid].masa)
                if w.player_entity_id is None or w.player_entity_id not in self_ids:
                    w.player_entity_id = best
    if w.player_entity_id is not None:
        pe = w.entities.get(w.player_entity_id)
        if pe and pe.grid_x is not None:
            positions.append((n, w.player_entity_id, pe.grid_x, pe.grid_y, pe.masa))

print('frames:', n, ' player_entity_id:', w.player_entity_id)
print('player_cells:', sorted(w.player_cells))
if positions:
    print('muestras de la propia:', len(positions))
    print('primera:', positions[0])
    print('ultima:', positions[-1])
    # cuantas posiciones distintas
    uniq = set((x, z) for _, _, x, z, _ in positions)
    print('posiciones distintas:', len(uniq))
    # se mueve?
    moved = sum(1 for i in range(1, len(positions)) if positions[i][2:4] != positions[i-1][2:4])
    print('cambios de posicion:', moved)
