# analisis en vivo de v5f: identificar la propia por [19] y sus SETPOS
import re
from collections import Counter, defaultdict

log = open(r'C:/tmp/scanner_v5f.log', encoding='utf-8', errors='replace').read().splitlines()

player_ids = None
setpos = []  # (dt, ent, x, z, et)
clears = []
moves = []

for ln in log:
    m = re.match(r'\s*(\d+)ms IN  TCP  \[19, \[([^\]]+)\],', ln)
    if m:
        ids = [int(x) for x in m.group(2).split(',')]
        if player_ids is None or ids != player_ids:
            player_ids = ids
            print('dt=%sms [19] ids=%s' % (m.group(1), ids))
        continue
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=(0x[0-9a-f]+) x=([\d.]+) z=([\d.]+) rot=[\d.]+ et=(\d+)', ln)
    if m:
        setpos.append((int(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4)), int(m.group(5))))
        continue
    m = re.match(r'\s*(\d+)ms OUT UDP  udp_frame len=\d+ op=0x2726', ln)
    if m:
        moves.append(int(m.group(1)))

print('total SETPOS:', len(setpos), ' MOVEs:', len(moves))
if player_ids:
    own = [s for s in setpos if s[4] in player_ids]
    print('SETPOS de celulas propias:', len(own))
    by_et = Counter(s[4] for s in own)
    print('por et:', dict(by_et))
    # trayectoria de la primera celula propia
    if own:
        et0 = own[0][4]
        tr = [s for s in own if s[4] == et0]
        print('trayectoria et=%d: %d puntos, %s -> %s' % (et0, len(tr), tr[0][:4], tr[-1][:4]))
        for s in tr[::max(1, len(tr)//20)][:20]:
            print('  ', s)
