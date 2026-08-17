# timeline completo de v5e: cuando llega cada tipo de evento
import re
from collections import defaultdict

log = open(r'C:/tmp/scanner_v5e.log', encoding='utf-8', errors='replace').read().splitlines()

buckets = defaultdict(list)  # tipo -> [(dt, detalle)]
for ln in log:
    m = re.match(r'\s*(\d+)ms (IN|OUT) (.+)$', ln)
    if not m:
        continue
    dt = int(m.group(1))
    rest = m.group(3).strip()
    if rest.startswith('SETPOS'):
        buckets['SETPOS'].append(dt)
    elif rest.startswith('SETMASS'):
        buckets['SETMASS'].append(dt)
    elif rest.startswith('BUILD'):
        buckets['BUILD'].append(dt)
    elif rest.startswith('TCP  CLEAR'):
        buckets['CLEAR'].append(dt)
    elif rest.startswith('TCP  ['):
        # AMF3: extraer opcode
        m2 = re.match(r'TCP  \[(\d+)[,\]]', rest)
        op = m2.group(1) if m2 else '?'
        buckets['AMF3[' + op + ']'].append(dt)
    elif rest.startswith('UDP  udp_frame'):
        buckets['UDP_MOVE'].append(dt)
    elif rest.startswith('UDP  MOVE'):
        buckets['UDP_MOVE'].append(dt)

for k, v in sorted(buckets.items()):
    if not v:
        continue
    # rango por ventanas de 10s
    win = defaultdict(int)
    for dt in v:
        win[dt // 10000] += 1
    print('%-14s total=%5d  ventanas(10s): %s' % (k, len(v), dict(sorted(win.items()))))
