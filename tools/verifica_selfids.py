# verifica decode_clear_full con self_ids sobre la captura v5f
import sys, json
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito')
sys.path.insert(0, r'C:\Users\ren\Desktop\og mito\re')
from haxe_clear_parser import decode_clear_full

raw = open(r'C:/tmp/scanner_v5f.log.raw', encoding='utf-8', errors='replace').read().splitlines()

n_frames = 0
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
    try:
        ents, pid, dead, pj, self_ids = decode_clear_full(b, return_pj=True)
    except Exception as ex:
        print('ERR:', ex)
        continue
    n_frames += 1
    for sid in self_ids:
        all_self[sid] = all_self.get(sid, 0) + 1
        n_self += 1

print('frames:', n_frames, ' eventos self_ids:', n_self)
print('ids propios detectados:', sorted(all_self.items(), key=lambda kv: -kv[1])[:20])
print('total ids unicos:', len(all_self))
