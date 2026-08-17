import sys, re, json, math

# Analisis del log del scanner v5: correlaciona SETPOS (posiciones reales
# aplicadas por el binario), SETMASS (masas reales) y op16 (ids con nombre)
log = open(r'C:/tmp/scanner_v5d.log', encoding='utf-8', errors='replace').read()

pos = {}      # ent -> (x, z, et, id16, ts_ms)
masa = {}     # ent -> masa
nombres = {}  # id op16 -> username
player_id = None

for line in log.splitlines():
    m = re.search(r'(\d+)ms IN  SETPOS ent=(\S+) x=([-\d.]+) z=([-\d.]+) rot=([-\d.]+) et=(\d+) id16=(\d+)', line)
    if m:
        ms, ent, x, z, rot, et, id16 = m.groups()
        pos[ent] = (float(x), float(z), int(et), int(id16), int(ms))
        continue
    m = re.search(r'(\d+)ms IN  SETMASS ent=(\S+) masa=([-\d.]+) et=(\d+) id16=(\d+)', line)
    if m:
        ms, ent, mm, et, id16 = m.groups()
        masa[ent] = float(mm)
        continue
    m = re.search(r'\[16, \[(\d+), \{[^]]*?"username": "([^"]+)"', line)
    if m:
        nombres[int(m.group(1))] = m.group(2)
        continue
    m = re.search(r'IN  TCP  \[4, (\d+)\]', line)
    if m:
        player_id = int(m.group(1))

print('PLAYER_ID:', player_id)
print('op16 jugadores:', len(nombres))
for nid in sorted(nombres):
    print('  id=%d %s' % (nid, nombres[nid]))

# entidades del binario: ultima posicion + masa
print()
print('Entidades del binario (ent | x z | masa | et):')
n = 0
for ent, (x, z, et, id16, ms) in sorted(pos.items(), key=lambda kv: -kv[1][3]):
    mm = masa.get(ent, 0)
    n += 1
    if n > 40:
        break
    print('  %s x=%8.2f z=%8.2f masa=%8.1f et=%d' % (ent, x, z, mm, et))