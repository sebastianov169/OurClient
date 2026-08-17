#!/usr/bin/env python3
"""Decompilacion MASIVA del binario via Ghidra MCP.

Recorre re/_all_functions_list.txt, decompila cada funcion que no tengamos
aun (paralelo, 16 hilos) y la guarda en re/_bulk/<func>.c.

Uso: python tools/bulk_decompile.py [--limit N] [--range 0x140600000-0x140800000]
"""
import os
import re
import sys
import time
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "re", "_all_functions_list.txt")
OUT = os.path.join(ROOT, "re", "_bulk")
API = "http://127.0.0.1:8089/decompile_function?address=0x{:x}"

os.makedirs(OUT, exist_ok=True)

# funciones ya decompiladas (para no repetir)
done = set()
for d in ("decomp_mov", "pc_analysis", "_scratch"):
    pass
import glob
for f in glob.glob(os.path.join(ROOT, "re", "decomp_mov", "*.c")) + \
         glob.glob(os.path.join(ROOT, "re", "pc_analysis", "_scratch", "*.c")) + \
         glob.glob(os.path.join(ROOT, "re", "_decomp_*.txt")) + \
         glob.glob(os.path.join(ROOT, "re", "_d_*.txt")):
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in re.finditer(r"FUN_([0-9a-f]{6,10})", txt):
        done.add(int(m.group(1), 16))

lock = threading.Lock()
stats = {"ok": 0, "fail": 0, "skip": 0}


def decompile(addr):
    name = "FUN_%x" % addr
    out_p = os.path.join(OUT, name + ".c")
    if os.path.exists(out_p):
        with lock:
            stats["skip"] += 1
        return
    try:
        req = urllib.request.Request(API.format(addr))
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
        if len(body) > 200:
            with open(out_p, "wb") as fh:
                fh.write(body)
            with lock:
                stats["ok"] += 1
        else:
            with lock:
                stats["fail"] += 1
    except Exception:
        with lock:
            stats["fail"] += 1


def main():
    limit = None
    rng = None
    args = sys.argv[1:]
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--range" in args:
        rng = args[args.index("--range") + 1]

    fns = []
    for l in open(LIST, encoding="utf-8", errors="replace"):
        m = re.match(r"FUN_([0-9a-f]{6,10})\s+at\s+([0-9a-f]+)", l.strip())
        if not m:
            continue
        addr = int(m.group(2), 16)
        if addr in done:
            continue
        if rng:
            lo_s, hi_s = rng.split("-")
            if not (int(lo_s, 16) <= addr < int(hi_s, 16)):
                continue
        fns.append(addr)
        if limit and len(fns) >= limit:
            break

    print("pendientes:", len(fns), flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(decompile, fns))
    dt = time.time() - t0
    print("OK=%d fail=%d skip=%d en %.0fs (%.1f/s)" % (
        stats["ok"], stats["fail"], stats["skip"], dt, stats["ok"] / max(dt, 0.1)), flush=True)


if __name__ == "__main__":
    main()
