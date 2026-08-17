#!/usr/bin/env python3
"""Generador masivo: decompilados C de Ghidra -> Python (client/_generated/).

Clasifica cada FUN_*.c en:
  1. CLASSREG (registra clase: asigna vtable, strings de clase) -> clase Python
  2. DISPATCHER (switch(*param_3) + memcmp de nombres) -> tabla de campos
  3. CTOR (alloc + vftable) -> constructor
  4. LOGICA (ningun patron) -> funcion esqueleto con docstring del C

Uso: python tools/gen_translate.py [--limit N] [--only CLASSREG]
"""
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BULK = os.path.join(ROOT, "re", "_bulk")
OUT = os.path.join(ROOT, "client", "_generated")
os.makedirs(OUT, exist_ok=True)


def classify(src):
    if '"fkengine.' in src and 'vftable' in src and 'Class_obj' in src:
        return "CLASSREG"
    if 'switch(*param_3)' in src or 'switch(*param_4)' in src:
        return "DISPATCHER"
    if '_malloc_base' in src or 'hx::Class_obj::vftable' in src:
        return "CTOR"
    return "LOGICA"


def gen_classreg(src, fun):
    cls = re.search(r'"fkengine\.([^"]+)"', src)
    vtable = re.search(r'(\w+::\w+_obj::vftable)', src)
    ctor = re.search(r'\[1\] = (FUN_[0-9a-f]+)', src)
    name = cls.group(1).replace(".", "_") if cls else fun
    out = []
    out.append('"""%s - classreg %s (generado)."""' % (name, fun))
    out.append("")
    out.append("")
    out.append("class %s:" % name.split("_")[-1].capitalize() or name)
    if cls:
        out.append('    """fkengine.%s"""' % cls.group(1))
    if vtable:
        out.append("    VTABLE = %r" % vtable.group(1))
    if ctor:
        out.append("    CTOR = %r" % ctor.group(1))
    out.append("")
    out.append("    def __init__(self):")
    out.append("        pass")
    out.append("")
    return "\n".join(out)


def gen_dispatcher(src, fun):
    fields = {}
    for m in re.finditer(r'"((?:get|set)_?[A-Za-z_][A-Za-z0-9_]*)"', src):
        fields[m.group(1)] = None
    offs = re.findall(r"\*\((?:param_1|param_2|puVar\d+)\s*\+\s*(0x[0-9a-f]+)\)\s*=", src)
    out = []
    out.append('"""%s - dispatcher de campos (generado)."""' % fun)
    out.append("")
    out.append("")
    out.append("FIELD_TABLE = %r" % fields)
    out.append("")
    out.append("# offsets escritos: %s" % ", ".join(offs[:20]))
    out.append("")
    return "\n".join(out)


def gen_ctor(src, fun):
    vtable = re.search(r'(\w+_obj::vftable)', src)
    alloc = re.search(r'_malloc_base\(0x([0-9a-f]+)\)', src)
    out = []
    out.append('"""%s - constructor (generado)."""' % fun)
    out.append("")
    out.append("")
    out.append("class %s:" % fun)
    if vtable:
        out.append("    VTABLE = %r" % vtable.group(1))
    if alloc:
        out.append("    SIZE = 0x%s" % alloc.group(1))
    out.append("")
    out.append("    def __init__(self):")
    out.append("        pass")
    out.append("")
    return "\n".join(out)


def gen_logica(src, fun):
    sig = src.split("{", 1)[0].strip().replace("\n", " ")[:200]
    sig = sig.replace('"', "'")
    out = []
    out.append('"""%s - logica (generado, pendiente de traduccion manual).' % fun)
    out.append("")
    out.append("    %s" % sig)
    out.append('"""')
    out.append("")
    out.append("")
    out.append("def %s():  # PENDIENTE: traducir del C en re/_bulk/%s.c" % (fun, fun))
    out.append("    raise NotImplementedError")
    out.append("")
    return "\n".join(out)


def main():
    limit = None
    only = None
    args = sys.argv[1:]
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--only" in args:
        only = args[args.index("--only") + 1]

    stats = {"CLASSREG": 0, "DISPATCHER": 0, "CTOR": 0, "LOGICA": 0}
    n = 0
    for f in sorted(glob.glob(os.path.join(BULK, "FUN_*.c"))):
        fun = os.path.basename(f).replace(".c", "")
        src = open(f, encoding="utf-8", errors="replace").read()
        kind = classify(src)
        if only and kind != only:
            continue
        if kind == "CLASSREG":
            code = gen_classreg(src, fun)
        elif kind == "DISPATCHER":
            code = gen_dispatcher(src, fun)
        elif kind == "CTOR":
            code = gen_ctor(src, fun)
        else:
            code = gen_logica(src, fun)
        with open(os.path.join(OUT, fun + ".py"), "w", encoding="utf-8", newline="") as fh:
            fh.write(code)
        stats[kind] += 1
        n += 1
        if limit and n >= limit:
            break
    print("generados: %d | %s" % (n, stats), flush=True)


if __name__ == "__main__":
    main()
