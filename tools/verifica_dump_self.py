# verifica: decode_dump_19 ahora devuelve self_ids del 0x1c en dumps reales
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import decode_dump_19

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

n_dump = 0
n_self = 0
all_self = {}
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
        continue  # solo dumps (branch payload[1]==0x04)
    try:
        ents, self_ids = decode_dump_19(b)
    except Exception as ex:
        print('ERR:', ex)
        continue
    n_dump += 1
    for sid in self_ids:
        all_self[sid] = all_self.get(sid, 0) + 1
        n_self += 1

print('dumps:', n_dump, ' eventos self_ids en dumps:', n_self)
print('ids propios en dumps:', sorted(all_self.items(), key=lambda kv: -kv[1])[:20])
