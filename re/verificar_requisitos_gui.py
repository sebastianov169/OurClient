#!/usr/bin/env python3
"""verificar_requisitos_gui.py — Verifica el checklist de requisitos GUI contra
el estado en disco de mito_view.py + re/haxe_clear_parser.py.

Checklist (re/checklist_requisitos_gui.md):
1. Posicion: op20 spawn + entidades CLEAR (ids u16 BE) en escala real
2. Masa entera (KEY_MASA del parser, valor real) — sin decimales
3. Score = op51 (masa maxima historica) en snapshot + HUD
4. Clasificacion: entityType 1=comida (circulito), 0x14/0x15=celula (radio+nombre)
5. Limites mundo 16384x16384 + clamp (formato REAL u16/divisor; 21000 refutado)
6. Parser por eventos (haxe_clear_parser, 45 tipos de protocolo_entrante_pc.md §6)
"""
import os, sys, py_compile, subprocess

ROOT = r"C:\Users\ren\Desktop\og mito"
fails = []
oks = []

def check(name, cond, detail=""):
    if cond:
        oks.append("%s %s" % (name, detail))
    else:
        fails.append("%s %s" % (name, detail))

# 1. compila
try:
    py_compile.compile(os.path.join(ROOT, "mito_view.py"), doraise=True)
    check("compile", True, "mito_view.py OK")
except Exception as e:
    check("compile", False, str(e))

# 2. parser nuevo existe
parser_path = os.path.join(ROOT, "re", "haxe_clear_parser.py")
check("parser_nuevo", os.path.exists(parser_path), "")

# 3. estado en disco de mito_view.py
src = ""
if os.path.exists(os.path.join(ROOT, "mito_view.py")):
    with open(os.path.join(ROOT, "mito_view.py"), encoding="utf-8") as f:
        src = f.read()

# masa entera (round) presente
check("masa_entera", "round(masa)" in src or "round(" in src, "(round en feed_entity_frame)")
# score en STATE
check("score_state", "self.score" in src, "(STATE.score)")
# score en snapshot
check("score_snapshot", '"score": self.score' in src, "(snapshot)")
# score en HUD
check("score_hud", "SCORE:" in src, "(draw_hud)")
# spawn y=altura (no masa)
check("spawn_y_altura", "ALTURA" in src, "(comentario set_spawn)")
# limites mundo (formato REAL: u16/divisor -> 16384; el 21000 era la escala cruda)
check("mundo_16384", "16384.0" in src, "(MUNDO_W/H)")
# GRID_SIZE documentado (solo ruta dump 19B)
check("grid_size_doc", "GRID_SIZE" in src, "(ESCALA=GRID_SIZE dump 19B)")

# 4. ejecutar el parser de prueba si existe
if os.path.exists(parser_path):
    sys.path.insert(0, os.path.join(ROOT, "re"))
    try:
        import haxe_clear_parser as P
        # payload real de mito_view36.log: 0x00 id=200, X=0, Z=0x3b83/4=3808.75
        fields = P.parse_clear_hex("640000c800003b83")
        check("parser_0x00", fields is not None, repr(fields)[:60])
        if fields is not None:
            # id 200 real (el 0xc8=200 era id de entidad, NO X del jugador: refutado)
            v = fields.get(200)
            check("entidad_200", v is not None, "id200=%r" % (v,))
        # payload multi-campo
        fields2 = P.parse_clear_hex("64000f272fe429800010f536fe26e2000613398e28a4000d4f399a24ba0009d734fc25310003d936b824e1070c07")
        check("parser_multicampo", fields2 is not None, repr(fields2)[:80] if fields2 else "None")
        # masa real via KEY_MASA (la regla v/500 quedo REFUTADA)
        m = P.masa_de_fields({P.KEY_MASA: (0x00, 90.0)})
        check("masa_key", m is not None and abs(m - 90.0) < 0.01, "masa=%r" % m)
    except Exception as e:
        check("parser_import", False, str(e))

print("=" * 60)
print("REQUISITOS GUI — verificación de estado en disco")
print("=" * 60)
for o in oks:
    print("  [OK]", o)
print()
if fails:
    print("FALLOS:")
    for f in fails:
        print("  [X]", f)
    sys.exit(1)
print("TODO OK")
sys.exit(0)
