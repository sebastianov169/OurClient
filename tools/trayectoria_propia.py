# trayectoria de la propia (ent=0x1524d261fb0 et=1287) y comparacion con [20]
import re

log = open(r'C:/tmp/scanner_v5e.log', encoding='utf-8', errors='replace').read().splitlines()

own = []  # (dt, x, z)
for ln in log:
    m = re.match(r'\s*(\d+)ms IN  SETPOS ent=0x1524d261fb0 x=([\d.]+) z=([\d.]+)', ln)
    if m:
        own.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))

print('SETPOS propia (ent 0x1524d261fb0):', len(own))
if own:
    print('primero:', own[0], ' ultimo:', own[-1])
    # muestreo cada ~10
    for i in range(0, len(own), max(1, len(own)//25)):
        print('  ', own[i])
    # velocidad promedio
    dts = [own[i+1][0] - own[i][0] for i in range(len(own)-1)]
    dists = [((own[i+1][1]-own[i][1])**2 + (own[i+1][2]-own[i][2])**2)**0.5 for i in range(len(own)-1)]
    if dts and sum(dts) > 0:
        print('vel media: %.1f u/s' % (sum(dists)/sum(dts)*1000))
