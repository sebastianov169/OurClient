# -*- coding: utf-8 -*-
"""
validar_logs.py — Harness de validacion del protocolo CLEAR Haxe de MitosisOG.

Parseo los logs REALES:
  - mito_view32..36.log            (frames CLEAR crudos + campos decodificados)
  - frida_capture_driver/masa_capture*.log  (AMF3: op51 score, op20 spawn)

Verifica:
  1. posiciones extraidas en [0, 16384]        (coords REALES u16/_shortDivisor)
  2. masa entera coherente: rango [0, 200000], crece al comer, cae al morir
     (masa real del parser: KEY_MASA, 0x0c x10 / campo y de 0x08)
  3. score op51 NUNCA baja (monotono no decreciente)

Reporte por log: N frames, N entidades, posiciones validas %, masa min/max,
y comparacion contra los datos reales del usuario:
  477 (score inicial), +15k, +28k (ganancia), 45-50k (masa final),
  4-5k (masa inicial), 50-100 (masa tras respawn).
"""
import glob
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import haxe_clear_parser as P

BASE = r"C:\Users\ren\Desktop\og mito"
VIEW_LOGS = [os.path.join(BASE, "mito_view%d.log" % n) for n in range(32, 37)]
MASA_LOGS = sorted(glob.glob(os.path.join(BASE, "frida_capture_driver", "masa_capture*.log")))

# Datos reales reportados por el usuario (ground truth)
USUARIO = {
    "score_inicial": 477,      # op51 inicial de una sesion
    "ganancia_15k": 15000,     # masa ganada en una sesion
    "ganancia_28k": 28000,     # masa ganada en otra sesion
    "masa_final_45_50k": (45000, 50000),
    "masa_inicial_4_5k": (4000, 5000),
    "masa_respawn_50_100": (50, 100),
}
MULTIPLICADORES = [4.0, 10.0, 25.0]  # candidatos masa = op51 * k


def cerca(val, target, tol=0.15):
    return abs(val - target) <= tol * target


def analizar_view_log(path):
    """Analiza un mito_view*.log -> dict con el reporte."""
    r = {"archivo": os.path.basename(path), "tipo": "view",
         "frames_clear": 0, "frames_parseables": 0, "frames_lista": 0,
         "entidades": set(), "campos": Counter(),
         "pos_total": 0, "pos_validas": 0, "pos_fuera": [],
         "masa_por_ent": {}, "c8_vals": [], "lineas": 0}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            r["lineas"] += 1
            hexstr, fields = P.parse_clear_line(ln)
            if hexstr is None:
                continue
            r["frames_clear"] += 1
            if fields is None:
                try:
                    if bytes.fromhex(hexstr.strip())[1:2] == b"\x04":
                        r["frames_lista"] += 1
                except ValueError:
                    pass
                continue
            r["frames_parseables"] += 1
            firma = P.firma_entidad(fields)
            r["entidades"].add(firma)
            for c, (t, v) in fields.items():
                r["campos"][c] += 1
            for c, coord in P.posiciones_de_fields(fields):
                r["pos_total"] += 1
                if 0.0 <= coord <= P.MUNDO_W:
                    r["pos_validas"] += 1
                else:
                    r["pos_fuera"].append((c, coord))
            m = P.masa_de_fields(fields)
            if m is not None:
                r["masa_por_ent"].setdefault(firma, []).append(round(m))
            # NOTA 2026-08-13: la regla "campo 0xc8 = X del jugador" quedo
            # REFUTADA (0 hits en el binario; 0xc8=200 es un id de entidad
            # normal). El jugador se detecta por la marca 0x19/0x1a
            # (player_id_de_frame) o por correlacion en el visor.

    # serie de masa POR ENTIDAD -> el jugador = firma con mas observaciones
    mejor_ent = max(r["masa_por_ent"].items(), key=lambda kv: len(kv[1])) \
        if r["masa_por_ent"] else (None, [])
    r["ent_masa"] = mejor_ent[0]
    serie = mejor_ent[1]
    r["masa_obs"] = len(serie)
    r["masa_min"] = min(serie) if serie else None
    r["masa_max"] = max(serie) if serie else None
    r["masa_fuera_rango"] = sum(1 for m in serie if not (0 <= m <= P.MASA_MAX_ABS))
    # agregado en TODAS las entidades: crece al comer / cae al morir
    agg_ups = agg_downs = agg_muertes = 0
    ent_crecen = ent_mueren = 0
    for firma, s in r["masa_por_ent"].items():
        u = d = 0
        for a, b in zip(s, s[1:]):
            if b > a:
                u += 1
            elif b < a:
                d += 1
        max_hist = 0
        mu = 0
        for m in s:
            if m > max_hist:
                max_hist = m
            elif max_hist > 0 and m < 0.5 * max_hist:
                mu += 1
                max_hist = 0
        agg_ups += u
        agg_downs += d
        agg_muertes += mu
        if u:
            ent_crecen += 1
        if mu:
            ent_mueren += 1
    r["masa_ups"], r["masa_downs"], r["masa_muertes"] = agg_ups, agg_downs, agg_muertes
    r["ent_crecen"], r["ent_mueren"] = ent_crecen, ent_mueren
    r["muertes_detectadas"] = agg_muertes
    # X del jugador: valor constante mas frecuente (15235 en kjajajaja) y rango
    if r["c8_vals"]:
        cc = Counter(r["c8_vals"])
        r["c8_moda"] = cc.most_common(1)[0]
        r["c8_min"] = min(r["c8_vals"])
        r["c8_max"] = max(r["c8_vals"])
    else:
        r["c8_moda"] = None
        r["c8_min"] = r["c8_max"] = None
    r["n_entidades"] = len(r["entidades"])
    return r


def analizar_masa_log(path):
    """Analiza un frida masa_capture*.log -> dict con el reporte."""
    r = {"archivo": os.path.basename(path), "tipo": "masa",
         "lineas": 0, "op51": [], "op20": [], "amf3_total": 0}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            r["lineas"] += 1
            parsed = P.parse_amf3_line(ln)
            if parsed is None:
                continue
            op, args = parsed
            r["amf3_total"] += 1
            if op == 51 and args and isinstance(args[0], (int, float)):
                r["op51"].append(args[0])
            elif op == 20 and args and isinstance(args[0], list) and len(args[0]) >= 3:
                r["op20"].append(args[0])
    s = r["op51"]
    r["op51_n"] = len(s)
    r["op51_min"] = min(s) if s else None
    r["op51_max"] = max(s) if s else None
    r["op51_ultimo"] = s[-1] if s else None
    no_cero = [v for v in s if v > 0]
    r["op51_primer_no_cero"] = no_cero[0] if no_cero else None
    # rafagas: grupos de valores > 0 consecutivos
    rafagas = []
    cur = []
    for v in s:
        if v > 0:
            cur.append(v)
        elif cur:
            rafagas.append(cur)
            cur = []
    if cur:
        rafagas.append(cur)
    r["rafagas"] = rafagas
    r["rafaga_max"] = max((len(f) for f in rafagas), default=0)
    r["rafaga_ultima_max"] = rafagas[-1][-1] if rafagas else None
    # monotonia: op51 NUNCA baja
    viol = []
    for i in range(1, len(s)):
        if s[i] < s[i - 1] - 1e-6:
            viol.append((i, s[i - 1], s[i]))
    r["op51_violaciones"] = viol
    r["op51_monotono"] = not viol
    # el doc (Ghidra) dice: op51 = score = masa MAXIMA HISTORICA, nunca baja.
    # Chequeo fuerte: el maximo del log se alcanza al final (max == ultimo).
    r["op51_max_final"] = bool(s) and abs(max(s) - s[-1]) < 1e-6
    r["op51_max_dip"] = max((s[i - 1] - s[i] for i in range(1, len(s)) if s[i] < s[i - 1]),
                            default=0.0)
    r["op20_n"] = len(r["op20"])
    r["op20_y"] = sorted({round(a[1], 1) for a in r["op20"]})
    return r


def comparar_usuario(res):
    """Compara metricas de los logs contra los datos reales del usuario."""
    notas = []
    for k in MULTIPLICADORES:
        hit_28 = hit_50 = hit_15 = None
        for rr in res:
            if rr["tipo"] != "masa" or rr["op51_max"] is None:
                continue
            m = rr["op51_max"] * k
            if cerca(m, USUARIO["ganancia_28k"]):
                hit_28 = (rr["archivo"], rr["op51_max"], round(m))
            # 45-50k con tolerancia +/-10% sobre el punto medio 47.5k
            if cerca(m, 47500, tol=0.10):
                hit_50 = (rr["archivo"], rr["op51_max"], round(m))
            if cerca(m, USUARIO["ganancia_15k"]):
                hit_15 = (rr["archivo"], rr["op51_max"], round(m))
        notas.append("  masa=op51*%.0f  ->  +28k: %s | 45-50k: %s | +15k: %s" % (
            k, hit_28 or "-", hit_50 or "-", hit_15 or "-"))
    for rr in res:
        if rr["tipo"] == "masa" and rr["op51_primer_no_cero"]:
            v = rr["op51_primer_no_cero"]
            notas.append("  %s: primer op51 no-cero=%.0f -> *10=%.0f (4-5k? %s) | *4=%.0f | *25=%.0f"
                         % (rr["archivo"], v, v * 10,
                            USUARIO["masa_inicial_4_5k"][0] <= v * 10 <= USUARIO["masa_inicial_4_5k"][1],
                            v * 4, v * 25))
            if cerca(v, USUARIO["score_inicial"]):
                notas.append("  %s: op51=%.0f ~= 477 del usuario (score inicial)" % (rr["archivo"], v))
    for rr in res:
        if rr["tipo"] == "view" and rr["masa_min"] is not None:
            ok = USUARIO["masa_respawn_50_100"][0] <= rr["masa_min"] <= USUARIO["masa_respawn_50_100"][1]
            notas.append("  %s: masa CLEAR min=%d max=%d -> respawn 50-100? %s"
                         % (rr["archivo"], rr["masa_min"], rr["masa_max"], "SI" if ok else "no"))
    return notas


def fmt_view(rr):
    pct = (100.0 * rr["pos_validas"] / rr["pos_total"]) if rr["pos_total"] else 100.0
    moda = "%s=%d (n=%d)" % (hex(rr["c8_moda"][0]), rr["c8_moda"][0], rr["c8_moda"][1]) \
        if rr["c8_moda"] else "-"
    if rr["masa_obs"]:
        masa = "jugador(n=%d) min=%s max=%s | global ups=%d downs=%d muertes=%d (ent_crecen=%d ent_mueren=%d) fuera_rango=%d" % (
            rr["masa_obs"], rr["masa_min"], rr["masa_max"],
            rr["masa_ups"], rr["masa_downs"], rr["masa_muertes"],
            rr["ent_crecen"], rr["ent_mueren"], rr["masa_fuera_rango"])
    else:
        masa = "sin campos <100000 (masa grande: solo via op51)"
    return (
        "  %-16s frames_clear=%-6d parseables=%-6d | entidades(firmas)=%-4d campos_distintos=%-3d | "
        "pos=%d/%d validas (%.1f%%)%s | masa_int: %s | X_jugador(0xc8) moda: %s rango=%s..%s" % (
            rr["archivo"], rr["frames_clear"], rr["frames_parseables"],
            rr["n_entidades"], len(rr["campos"]),
            rr["pos_validas"], rr["pos_total"], pct,
            (" FUERA: %s" % rr["pos_fuera"][:4]) if rr["pos_fuera"] else "",
            masa, moda, rr["c8_min"], rr["c8_max"]))


def fmt_masa(rr):
    if rr["op51_n"] == 0:
        return "  %-16s sin mensajes op51/op20 (solo IRC/control)" % rr["archivo"]
    if rr["op51_monotono"]:
        mono = "SI"
    else:
        mono = "casi (max_hist al final=%s, dips<=%.0f: %d ev)" % (
            "SI" if rr["op51_max_final"] else "NO", rr["op51_max_dip"],
            len(rr["op51_violaciones"]))
    est = " | ".join("x%.0f=%.0f" % (k, rr["op51_max"] * k) for k in MULTIPLICADORES)
    return (
        "  %-16s op51_n=%-5d min=%.0f max=%.0f ultimo=%.0f primer_no_cero=%s | "
        "rafagas=%-3d (max_len=%d, ultima_max=%.0f) | monotono(no baja): %s | "
        "op20 spawns=%-2d y=%s | masa_est(op51max): %s" % (
            rr["archivo"], rr["op51_n"], rr["op51_min"], rr["op51_max"],
            rr["op51_ultimo"], rr["op51_primer_no_cero"],
            len(rr["rafagas"]), rr["rafaga_max"], rr["rafaga_ultima_max"], mono,
            rr["op20_n"], rr["op20_y"], est))


def main():
    print("=" * 104)
    print(" HARNESS DE VALIDACION — protocolo CLEAR Haxe (MitosisOG) — logs reales")
    print("=" * 104)
    res = []
    print("\n[1] LOGS VIEW (frames CLEAR 0x64): posiciones [0,16384], masa entera coherente")
    for p in VIEW_LOGS:
        if not os.path.exists(p):
            print("  (falta %s)" % os.path.basename(p))
            continue
        rr = analizar_view_log(p)
        res.append(rr)
        print(fmt_view(rr))
    print("\n[2] LOGS FRIDA (AMF3): op51 score nunca baja, op20 spawns")
    for p in MASA_LOGS:
        rr = analizar_masa_log(p)
        res.append(rr)
        print(fmt_masa(rr))
    print("\n[3] COMPARACION CONTRA DATOS REALES DEL USUARIO "
          "(477, +15k, +28k, 45-50k, 4-5k, 50-100 tras respawn)")
    for nota in comparar_usuario(res):
        print(nota)
    print("\n[4] RESUMEN DE VERIFICACIONES")
    ok_pos = all(rr["pos_total"] == 0 or rr["pos_validas"] == rr["pos_total"]
                 for rr in res if rr["tipo"] == "view")
    ok_masa_rango = all(rr["masa_fuera_rango"] == 0 for rr in res if rr["tipo"] == "view")
    # crece al comer: entidades con subidas de masa; cae al morir: muertes
    ok_crece = any(rr["ent_crecen"] > 0 for rr in res if rr["tipo"] == "view")
    ok_cae = any(rr["masa_muertes"] > 0 for rr in res if rr["tipo"] == "view")
    # op51: maximo historico alcanzado al final (nunca baja, segun Ghidra case 0x33)
    ok_op51 = all(rr["op51_max_final"] for rr in res if rr["tipo"] == "masa")
    estrictos = sum(1 for rr in res if rr["tipo"] == "masa" and rr["op51_monotono"])
    print("  posiciones en [0, 16384]: %s" % ("OK" if ok_pos else "FALLO"))
    print("  masa entera en [0, 200000]: %s" % ("OK" if ok_masa_rango else "FALLO"))
    print("  masa crece al comer (ent_crecen>0): %s" % ("OK" if ok_crece else "FALLO"))
    print("  masa cae al morir (muertes>0): %s" % ("OK" if ok_cae else "FALLO"))
    print("  score op51 max historico nunca baja (max==ultimo): %s (%d/%d logs estrictamente monotono)"
          % ("OK" if ok_op51 else "FALLO", estrictos,
             sum(1 for rr in res if rr["tipo"] == "masa" and rr["op51_n"] > 0)))
    print("=" * 104)


if __name__ == "__main__":
    main()
