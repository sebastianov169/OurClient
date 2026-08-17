# correlaciona SETPOS de la propia (et en lista [19]) con los CLEARs
# y muestra los eids de eventos 0x00 que llegan
import re, sys
from collections import Counter

log = open(r'C:/tmp/scanner_v5e.log', encoding='utf-8', errors='replace').read().splitlines()

# ids de las celulas propias segun [19]
player_ids = {1313, 1321, 1285, 1188, 1297, 1323, 1318, 1287, 1281, 1294}

setpos = []  # (dt, ent, x, z, et)
clears = []  # (dt, tipos dict)

for ln in log:
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=(0x[0-9a-f]+) x=([\d.]+) z=([\d.]+) rot=[\d.]+ et=(\d+)', ln)
    if m:
        setpos.append((int(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4)), int(m.group(5))))
        continue
    m = re.match(r'\s*(\d+)ms IN  TCP  CLEAR len=\d+ (.*)$', ln)
    if m:
        tipos = {}
        for t, c in re.findall(r'0x([0-9a-f]{2}):(\d+)', m.group(2)):
            tipos[int(t, 16)] = int(c)
        clears.append((int(m.group(1)), tipos))

print('SETPOS totales:', len(setpos))
print('CLEAR totales:', len(clears))

# 1) SETPOS por et: cuantos de cada id del jugador
own_et = Counter()
for dt, ent, x, z, et in setpos:
    if et in player_ids:
        own_et[et] += 1
print('SETPOS de celulas propias (et en [19]):', dict(own_et))

# 2) eids en eventos 0x00 -> extraer ids del raw no es posible aqui (solo tipos)
#    pero podemos ver que tipos tienen los CLEARs que preceden a SETPOS propios
# 3) para cada SETPOS propio, buscar el CLEAR mas cercano anterior y ver sus tipos
from collections import defaultdict
clear_before_own = Counter()
last_clear = None
ci = 0
for dt, ent, x, z, et in setpos:
    if et not in player_ids:
        continue
    while ci < len(clears) and clears[ci][0] <= dt:
        last_clear = clears[ci]
        ci += 1
    if last_clear:
        for t, c in last_clear[1].items():
            clear_before_own[t] += c
print('Tipos de CLEAR justo antes de SETPOS propios:', dict(clear_before_own))

# 4) timeline: dt del primer y ultimo SETPOS propio
own_times = [dt for dt, ent, x, z, et in setpos if et in player_ids]
if own_times:
    print('SETPOS propios: primero %dms, ultimo %dms, total %d' % (own_times[0], own_times[-1], len(own_times)))

# 5) distribucion temporal de SETPOS propios por segundo
secs = Counter(dt // 1000 for dt, ent, x, z, et in setpos if et in player_ids)
print('SETPOS propios por segundo (primeros 20):', sorted(secs.items())[:20])
