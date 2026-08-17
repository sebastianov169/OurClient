#!/usr/bin/env python3
"""Completa la decompilacion hasta el 100%: reintenta los fails (timeouts)
con 3 intentos y timeout mas generoso.

Uso: python tools/bulk_decompile_final.py
"""
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "re", "_all_functions_list.txt")
OUT = os.path.join(ROOT, "re", "_bulk")
API = "http://127.0.0.1:8089/decompile_function?address=0x{:x}"

# funciones pendientes = todas las del listado sin archivo en _bulk
fns = []
for l in open(LIST, encoding="utf-8", errors="replace"):
    m = re.match(r"FUN_([0-9a-f]{6,10})\s+at\s+([0-9a-f]+)", l.strip())
    if not m:
        continue
    addr = int(m.group(2), 16)
    if not os.path.exists(os.path.join(OUT, "FUN_%x.c" % addr)):
        fns.append(addr)

print("pendientes:", len(fns), flush=True)

stats = {"ok": 0, "fail": 0}


def decompile(addr):
    name = "FUN_%x" % addr
    for attempt in range(3):
        try:
            req = urllib.request.Request(API.format(addr))
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read()
            if len(body) > 200:
                with open(os.path.join(OUT, name + ".c"), "wb") as fh:
                    fh.write(body)
                stats["ok"] += 1
                return
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    stats["fail"] += 1
    if stats["fail"] % 200 == 0:
        print("  ...fails:", stats["fail"], flush=True)


t0 = time.time()
with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(decompile, fns))
dt = time.time() - t0
print("FINAL OK=%d fail=%d en %.0fs (%.1f/s)" % (
    stats["ok"], stats["fail"], dt, stats["ok"] / max(dt, 0.1)), flush=True)
