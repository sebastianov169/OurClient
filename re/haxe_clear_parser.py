#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
haxe_clear_parser.py - Parser del frame CLEAR 0x64 de MitosisOG (PC + Android).

FORMATO REAL VERIFICADO EN AMBOS BINARIOS (Ghidra PC FUN_14076c400 + Android
HqJ8Md, 2026-08-13). Spec consolidada: re/protocolo_absoluto.md (LEER PRIMERO).
Detalle: re/pc_analysis/protocolo_entrante_pc.md §4-§6 (45 tipos) y
re/android_analysis/clear_parser_android.md §4 (44 tipos).

REGLAS EMPIRICAS ANTIGUAS REFUTADAS (0 hits de sus constantes en ambos parsers):
    - [id u8][v:i32]            -> los ids son SIEMPRE u16 BE (readUnsignedShort)
    - v >= 1e6 -> /194165       -> 194165 = GRID_SIZE del grid espacial
                                     (DAT_1421b931c), NO divisor de valores; solo
                                     se usa en la OTRA ruta (dump de mundo 19B, AMF3
                                     opcode 10, campo 0x18 -> FUN_140975250)
    - 21000 < v < 100000 -> /500 -> no existe (0x1f4/0x5208/0x186a0 = 0 hits)
    - v <= 21000 directa        -> el 21000 no es constante en el parser; el
                                     clamp es a boundaries del grid (runtime)
    - id 0xc8 = X del jugador   -> 0 hits de 0xc8; los ids son opacos (u16)
    - score por CLEAR           -> el score (op51/0x33) llega SOLO por AMF3

FORMATO REAL del frame CLEAR:
    [0x64: u8] + eventos: [tipo: u8][campos...] hasta fin de payload.
    Ids: SIEMPRE u16 BE.
    Valores: 2 modos segun config del server (flag escena+0x3f0, key "float"):
        SHORT (default): u16 BE / _shortDivisor   (PC default 1.0, Android 10.0;
                     el server lo manda; verificado en vivo con Frida:
                     DAT_1421b9278 = 4.0 -> SHORT_DIVISOR = 4.0, calibrado)
        FLOAT:          i32 BE -> (float)
    Escalas reales: x10 en particula/valor (0x0c, 0x0d/0x0f v, 0x0a/0x0b b, 0x2e b,
                    0x28/0x2a b). La MASA viaja SIN x10 como 3er valor (y) de
                    0x08/0x0e/0x0d/0x0f (setMassAndRadius = FUN_140677760).
    Clamp de posicion: clamp(v, 0, boundaries-1) (modelado aqui como [0, MUNDO_W]).

Los 45 tipos (PC; Android 44: sin 0x2a) y sus tamanos (SHORT|FLOAT) verificados
sobre 35887 payloads unicos de logs reales (mito_view36/41/42/38): 0 desyncs.
    0x00/0x15/0x17/0x27 = posicion: id + V x + V z [+ V rot si 0x15]
                          [+ V v si 0x17/0x27] (interpola N frames, clamp grid)
    0x01 = id + 3xi32 BE (x,y,z);  0x03/0x05 = id + u16 v1 + V v2
    0x04 = u16 count + 4xu16 + (count-4)xV;   0x06 = u16 v;  0x07/0x09/0x13/
           0x19/0x1a/0x1d/0x2f = u16 id (0x19/0x1a = marca de jugador activo)
    0x08/0x0e = id + V x + V z + V MASA (+ u16 extra si 0x0e)
    0x0a/0x0b = id + u16 b + u16 c (b'=(b-1)x10 si >0)
    0x0c = id + u16 particula + V valor (valor x10.0; applyParticle, NO masa)
    0x0d/0x0f = id + V x + V z + V MASA (+ u16 extra si 0xf) + u16 a + V v (v x10.0)
    0x10/0x11/0x1c/0x21 = id + u16 v;  0x14 = u16 v + V ent
    0x16/0x20 = id + u16 n + n x u16;  0x18/0x1e = a + b + n + n x V
    0x1b = id + u16 bool;  0x1f = 4 x u16;  0x22 = id + 2 x u16
    0x23/0x28/0x2a = id + 3 x u16 (0x28/0x2a: b'=(b-1)x10 si >0, d-1)
    0x24/0x25/0x26 = id + u16 v + (0|1|2) x V;  0x29/0x2b/0x2c = sin campos (1B)
    0x2d = 2 x u16 -> u32 (low + high<<16);  0x2e = u16 a + u16 b (b x10)
    0x2a = SOLO PC (mismo handler que 0x28)

API:
    decode_to_fields(hex|bytes)       -> {campo: (tipo, valor)} ESCALA REAL (tracker)
    decode_clear(bytes)               -> {id: ClearEntity}
    decode_clear_full(bytes)          -> (ents, player_id)
    decode_dump_19(bytes)             -> {id: ClearEntity} (dump 19B, usa GRID_SIZE)
    parse_clear(bytes)                -> [ClearEvent]
    player_id_de_frame(bytes)         -> id del jugador (0x19/0x1a) o None
    parse_clear_line / parse_clear_hex / parse_amf3_line / firma_entidad /
    posiciones_de_fields / masa_de_fields   -> API legacy del harness re/validar_logs.py

El visor (mito_view.py) espera de decode_to_fields posiciones en ESCALA REAL
(u16/SHORT_DIVISOR, mundo 0..16384) — su EntityTracker NO debe dividir por
ESCALA (ESCALA=GRID_SIZE queda solo para la ruta del dump 19B).
"""
import re
import struct

# --- Config del modo de valores (flag escena+0x3f0, key "float"; key "shortdivisor") ---
SHORT_DIVISOR = 4.0      # u16 / SHORT_DIVISOR (Frida en vivo: DAT_1421b9278=4.0;
                         # PC default 1.0, Android 10.0; el server lo manda)
FLOAT_MODE = False       # True -> valores = i32 BE -> float (ignora SHORT_DIVISOR)

# --- Escalas ---
ESCALA = 194165.0        # GRID_SIZE del grid espacial (DAT_1421b931c). SOLO se usa
GRID_SIZE = ESCALA       # en la ruta del DUMP 19B (u32/ESCALA); NO divide eventos.
DIV = 4.0                # alias legacy == SHORT_DIVISOR calibrado
MUNDO_W = 16384.0        # mundo real de MitosisOG (65535/4 = 16383.75)
MUNDO_H = 16384.0

# --- Compat / harness ---
KEY_MASA = 0xFFFF        # clave reservada para el campo masa (valor REAL)
CAMPO_X_JUGADOR = 0xC8   # REFUTADO (0 hits en el binario); se conserva por el
                         # harness re/validar_logs.py (queda vacio: nunca aparece)
MASA_MAX_ABS = 200000.0  # tope de masa plausible (masa = y de 0x08/0x0d/0x0f:
                         # u16/DIV <= 16383.75; el x10 es de particula, no de masa)


def set_valor_mode(short_divisor=None, float_mode=None):
    """Configura el modo de lectura de valores (config del server).

    short_divisor: divisor del modo SHORT (key 'shortdivisor'; el server lo
                   manda; PC default 1.0, Android 10.0; calibrado en vivo 4.0).
    float_mode:    True -> i32 BE -> float (key 'float').
    Devuelve (SHORT_DIVISOR, FLOAT_MODE) vigentes."""
    global SHORT_DIVISOR, FLOAT_MODE, DIV
    if short_divisor is not None and short_divisor > 0:
        SHORT_DIVISOR = float(short_divisor)
        DIV = SHORT_DIVISOR
    if float_mode is not None:
        FLOAT_MODE = bool(float_mode)
    return SHORT_DIVISOR, FLOAT_MODE


class ClearEvent(object):
    """Evento crudo del frame CLEAR."""
    __slots__ = ("tipo", "id", "x", "z", "masa", "valor", "raw")

    def __init__(self, tipo, eid=0, x=None, z=None, masa=None, valor=None, raw=None):
        self.tipo = tipo
        self.id = eid
        self.x = x
        self.z = z
        self.masa = masa
        self.valor = valor
        self.raw = raw

    def __repr__(self):
        v = self.valor
        if isinstance(v, (tuple, list)):
            v = tuple(round(x, 2) if isinstance(x, (int, float)) else x for x in v)
        elif v is not None:
            v = round(v, 2)
        return "ClearEvent(tipo=0x%02x, id=%s, x=%s, z=%s, masa=%s, valor=%s)" % (
            self.tipo, self.id,
            None if self.x is None else round(self.x, 2),
            None if self.z is None else round(self.z, 2),
            None if self.masa is None else round(self.masa, 2),
            v)


class ClearEntity(object):
    """Entidad decodificada: posicion (x, z), masa, radio, tipo."""
    __slots__ = ("id", "x", "z", "masa", "radio", "entityType", "eventos", "_last_seen", "owner")

    def __init__(self, eid):
        self.id = eid
        self.x = None
        self.z = None
        self.masa = 0.0
        self.radio = 0.0
        self.entityType = 1          # 1 = comida (default); 0x14/0x15 = celula
        self.eventos = 0

    def set_pos(self, x, z):
        self.x = x
        self.z = z
        self.eventos += 1

    def set_masa(self, m):
        self.masa = float(m)
        self.radio = radio_from_masa(self.masa)
        if self.masa > 0:
            self.entityType = 0x14   # celula (tiene masa propia)
        self.eventos += 1

    def __repr__(self):
        return ("ClearEntity(id=%d, x=%s, z=%s, masa=%s, radio=%s, type=%s)" % (
            self.id,
            None if self.x is None else round(self.x, 2),
            None if self.z is None else round(self.z, 2),
            round(self.masa, 1), round(self.radio, 1), self.entityType))


def radio_from_masa(masa):
    """Radio = floor(sqrt(masa)*10 + 0.5) + 1 (FUN_140677760 + Flash L252).

    El +1 lo aplica la llamada a setRadius (slot vtable 0x1c8) en el binario
    (re/_d_140677760.txt L17-25); el Flash: Math.round(Math.sqrt(_size)*10)+1.
    Verificado Ghidra 2026-08-14 (re/pc_analysis/hallazgos_entidades_paleta_leaderboard.md §2).
    """
    import math
    if masa <= 0:
        return 0.0
    return math.floor(math.sqrt(masa) * 10.0 + 0.5) + 1


def u16(b, i):
    return (b[i] << 8) | b[i + 1]


def i32(b, i):
    return struct.unpack(">i", b[i:i + 4])[0]


def _clamp_pos(v):
    """Clamp de posicion a [0, boundaries-1] (grid), modelado con MUNDO_W."""
    if v is None:
        return v
    return max(0.0, min(float(v), MUNDO_W))


def _leer_valor(b, i):
    """Lee UN valor: u16 BE / SHORT_DIVISOR (modo SHORT) o i32 BE -> float.
    Devuelve (valor, nbytes_consumidos)."""
    if FLOAT_MODE:
        return float(i32(b, i)), 4
    return u16(b, i) / SHORT_DIVISOR, 2


def _b10(b):
    """b' = (b-1) x10 si > 0 (tipos 0x0a/0x0b/0x28/0x2a)."""
    d = b - 1
    return d * 10 if d > 0 else d


def parse_clear(payload):
    """Parsea un frame CLEAR (bytes) -> lista de ClearEvent.

    Formato REAL: [0x64] + [tipo u8][campos segun tipo] (tabla de 45 tipos de
    re/pc_analysis/protocolo_entrante_pc.md §6). Tolera colas truncadas (TCP
    split): eventos incompletos al final se ignoran. Tipos desconocidos se
    saltan de a 1 byte (igual que el default del switch del binario)."""
    if not payload or payload[0] != 0x64:
        return None
    events = []
    i = 1
    n = len(payload)
    nb_v = 4 if FLOAT_MODE else 2   # bytes por valor (modo FLOAT/SHORT)
    while i < n:
        t = payload[i]
        # ---------- posicion: 0x00/0x15/0x17/0x27 ----------
        if t in (0x00, 0x15, 0x17, 0x27):
            if i + 3 + 2 * nb_v > n:
                break
            eid = u16(payload, i + 1)
            x, _ = _leer_valor(payload, i + 3)
            z, _ = _leer_valor(payload, i + 3 + nb_v)
            i += 3 + 2 * nb_v
            extra = []
            if t == 0x15:      # + V rot
                if i + nb_v > n:
                    break
                extra.append(("rot", _leer_valor(payload, i)[0]))
                i += nb_v
            elif t in (0x17, 0x27):   # + V v
                if i + nb_v > n:
                    break
                extra.append(("v", _leer_valor(payload, i)[0]))
                i += nb_v
            events.append(ClearEvent(t, eid=eid, x=_clamp_pos(x), z=_clamp_pos(z),
                                     valor=tuple(extra) or None, raw=(x, z)))
            continue
        # ---------- 0x01: id + 3xi32 BE (x, y, z) ----------
        if t == 0x01:
            if i + 15 > n:
                break
            eid = u16(payload, i + 1)
            ix = i32(payload, i + 3)
            iy = i32(payload, i + 7)
            iz = i32(payload, i + 11)
            events.append(ClearEvent(t, eid=eid, x=_clamp_pos(ix), z=_clamp_pos(iz),
                                     valor=(iy,), raw=(ix, iy, iz)))
            i += 15
            continue
        # ---------- 0x03/0x05/0x22: id + v1 + v2 (0x22 raw) ----------
        if t in (0x03, 0x05, 0x22):
            if i + 3 + 2 + nb_v > n:
                break
            eid = u16(payload, i + 1)
            v1, _ = _leer_valor(payload, i + 3)
            if t == 0x22:
                v2 = float(u16(payload, i + 5))
            else:
                v2, _ = _leer_valor(payload, i + 5)
            events.append(ClearEvent(t, eid=eid, valor=(v1, v2), raw=(v1, v2)))
            i += 3 + 2 + nb_v
            continue
        # ---------- 0x0a/0x0b: id + u16 b + u16 c (b'=(b-1)x10) ----------
        if t in (0x0a, 0x0b):
            if i + 7 > n:
                break
            eid = u16(payload, i + 1)
            b = u16(payload, i + 3)
            c = u16(payload, i + 5)
            events.append(ClearEvent(t, eid=eid, valor=(_b10(b), c), raw=(b, c)))
            i += 7
            continue
        # ---------- 0x0c: id + u16 particula + V valor (valor x10; applyParticle,
        # NO es masa). FUN_140789500 field 0xc -> FUN_140678b80 (applyParticle,
        # escribe +0x34/+0x38 particula); setMassAndRadius es FUN_140677760 (field 8). ----------
        if t == 0x0c:
            if i + 3 + 2 + nb_v > n:
                break
            eid = u16(payload, i + 1)
            v = u16(payload, i + 3)
            valor, _ = _leer_valor(payload, i + 5)
            events.append(ClearEvent(t, eid=eid, valor=(v, valor * 10.0),
                                     raw=(v, valor)))
            i += 3 + 2 + nb_v
            continue
        # ---------- 0x08/0x0e: id + V x + V z + V MASA (+ extra si 0x0e).
        # El 3er valor (y) ES la masa: FUN_140789500 field 8 -> LAB_14078c77b ->
        # setMassAndRadius(args[2]) (disasm 0x14078c77b-0x14078c8b0). SIN x10. ----------
        if t in (0x08, 0x0e):
            if i + 3 + 3 * nb_v > n:
                break
            eid = u16(payload, i + 1)
            x, _ = _leer_valor(payload, i + 3)
            z, _ = _leer_valor(payload, i + 3 + nb_v)
            y, _ = _leer_valor(payload, i + 3 + 2 * nb_v)
            i += 3 + 3 * nb_v
            extra = None
            if t == 0x0e:
                if i + 2 > n:
                    break
                extra = u16(payload, i)
                i += 2
            events.append(ClearEvent(t, eid=eid, x=_clamp_pos(x), z=_clamp_pos(z),
                                     masa=y, valor=extra, raw=(x, z, y)))
            continue
        # ---------- 0x0d/0x0f: id + V x + V z + V MASA (+extra si 0xf) + u16 a + V v (v x10).
        # El 3er valor (y) ES la masa (field 0xd -> LAB_14078c77b -> setMassAndRadius(args[2]));
        # a + v*10 = particula (field 0xd nested -> FUN_140678b80(args[4],args[5]), disasm 0x14078c994). ----------
        if t in (0x0d, 0x0f):
            base = 3 + 3 * nb_v + (2 if t == 0x0f else 0) + 2 + nb_v
            if i + base > n:
                break
            eid = u16(payload, i + 1)
            x, _ = _leer_valor(payload, i + 3)
            z, _ = _leer_valor(payload, i + 3 + nb_v)
            masa, _ = _leer_valor(payload, i + 3 + 2 * nb_v)
            j = i + 3 + 3 * nb_v
            extra = None
            if t == 0x0f:
                extra = u16(payload, j)
                j += 2
            a = u16(payload, j)
            v, _ = _leer_valor(payload, j + 2)
            i += base
            events.append(ClearEvent(t, eid=eid, x=_clamp_pos(x), z=_clamp_pos(z),
                                     masa=masa, valor=(extra, a, v * 10.0),
                                     raw=(x, z, masa)))
            continue
        # ---------- 0x04: u16 count + 4xu16 + (count-4)xV ----------
        if t == 0x04:
            if i + 11 > n:
                break
            cnt4 = u16(payload, i + 1)
            cnt = cnt4 - 4
            if cnt < 0:
                i += 1
                continue
            a, b, c, d = (u16(payload, i + 3), u16(payload, i + 5),
                          u16(payload, i + 7), u16(payload, i + 9))
            j = i + 11
            vals = []
            ok = True
            for _ in range(cnt):
                if j + nb_v > n:
                    ok = False
                    break
                v, nb = _leer_valor(payload, j)
                vals.append(v)
                j += nb
            if not ok:
                break
            events.append(ClearEvent(t, eid=c, valor=(a, b, c, d, vals),
                                     raw=(cnt4, vals)))
            i = j
            continue
        # ---------- 0x06: u16 v ; 0x07/0x09/0x13/0x19/0x1a/0x1d/0x2f: u16 id ----------
        if t in (0x06, 0x07, 0x09, 0x13, 0x19, 0x1a, 0x1d, 0x2f):
            if i + 3 > n:
                break
            v = u16(payload, i + 1)
            if t == 0x06:
                events.append(ClearEvent(t, valor=v, raw=v))
            else:
                events.append(ClearEvent(t, eid=v))
            i += 3
            continue
        # ---------- 0x10/0x11/0x1c/0x21: id + u16 v ----------
        if t in (0x10, 0x11, 0x1c, 0x21):
            if i + 5 > n:
                break
            events.append(ClearEvent(t, eid=u16(payload, i + 1),
                                     valor=u16(payload, i + 3)))
            i += 5
            continue
        # ---------- 0x14: u16 v + V ent ----------
        if t == 0x14:
            if i + 3 + nb_v > n:
                break
            v = u16(payload, i + 1)
            ent, _ = _leer_valor(payload, i + 3)
            events.append(ClearEvent(t, eid=v, valor=ent, raw=ent))
            i += 3 + nb_v
            continue
        # ---------- 0x16/0x20: id + u16 n + n x u16 ----------
        if t in (0x16, 0x20):
            if i + 5 > n:
                break
            eid = u16(payload, i + 1)
            cnt = u16(payload, i + 3)
            j = i + 5
            vals = []
            for _ in range(cnt):
                if j + 2 > n:
                    break
                vals.append(u16(payload, j))
                j += 2
            if len(vals) != cnt:
                break  # evento incompleto (TCP split): no re-parsear la cola
            events.append(ClearEvent(t, eid=eid, valor=(cnt, vals), raw=(cnt, vals)))
            i = j
            continue
        # ---------- 0x18/0x1e: a + u16 v + u16 n + n x V ----------
        if t in (0x18, 0x1e):
            if i + 7 > n:
                break
            a = u16(payload, i + 1)
            v = u16(payload, i + 3)
            cnt = u16(payload, i + 5)
            j = i + 7
            vals = []
            ok = True
            for _ in range(cnt):
                if j + nb_v > n:
                    ok = False
                    break
                vv, nb = _leer_valor(payload, j)
                vals.append(vv)
                j += nb
            if not ok:
                break
            events.append(ClearEvent(t, eid=a, valor=(v, cnt, vals), raw=(v, cnt, vals)))
            i = j
            continue
        # ---------- 0x1b: id + u16 bool ----------
        if t == 0x1b:
            if i + 5 > n:
                break
            events.append(ClearEvent(t, eid=u16(payload, i + 1),
                                     valor=u16(payload, i + 3)))
            i += 5
            continue
        # ---------- 0x1f: 4 x u16 ----------
        if t == 0x1f:
            if i + 9 > n:
                break
            events.append(ClearEvent(t, valor=(u16(payload, i + 1), u16(payload, i + 3),
                                                u16(payload, i + 5), u16(payload, i + 7))))
            i += 9
            continue
        # ---------- 0x23/0x28/0x2a: id + 3 x u16 (0x28/0x2a: b'=(b-1)x10, d-1) ----------
        if t in (0x23, 0x28, 0x2a):
            if i + 9 > n:
                break
            eid = u16(payload, i + 1)
            b = u16(payload, i + 3)
            c = u16(payload, i + 5)
            d = u16(payload, i + 7)
            if t == 0x23:
                vals = (b, c, d)
            else:
                vals = (_b10(b), c, d - 1)
            events.append(ClearEvent(t, eid=eid, valor=vals, raw=(b, c, d)))
            i += 9
            continue
        # ---------- 0x24/0x25/0x26: id + u16 v + (0|1|2) x V ----------
        if t in (0x24, 0x25, 0x26):
            nv = {0x24: 0, 0x25: 1, 0x26: 2}[t]
            base = 5 + nv * (2 if not FLOAT_MODE else 4)
            if i + base > n:
                break
            eid = u16(payload, i + 1)
            v = u16(payload, i + 3)
            j = i + 5
            vals = []
            for _ in range(nv):
                vv, nb = _leer_valor(payload, j)
                vals.append(vv)
                j += nb
            events.append(ClearEvent(t, eid=eid, valor=(v, vals), raw=(v, vals)))
            i = j
            continue
        # ---------- 0x2d: 2 x u16 -> u32 (low + high<<16) ----------
        if t == 0x2d:
            if i + 5 > n:
                break
            lo = u16(payload, i + 1)
            hi = u16(payload, i + 3)
            events.append(ClearEvent(t, valor=lo + hi * 0x10000, raw=(lo, hi)))
            i += 5
            continue
        # ---------- 0x2e: u16 a + u16 b (b x10) ----------
        if t == 0x2e:
            if i + 5 > n:
                break
            a = u16(payload, i + 1)
            b = u16(payload, i + 3)
            events.append(ClearEvent(t, eid=a, valor=b * 10, raw=(a, b)))
            i += 5
            continue
        # ---------- 0x29/0x2b/0x2c: sin campos ----------
        if t in (0x29, 0x2b, 0x2c):
            events.append(ClearEvent(t))
            i += 1
            continue
        # ---------- desconocido: skip 1 byte (default del switch del binario) ----------
        i += 1
    return events


def decode_clear(payload):
    """Decodifica un frame CLEAR (bytes) -> {id: ClearEntity}."""
    events = parse_clear(payload)
    if not events:
        return {}
    ents = {}
    for ev in events:
        if ev.x is not None or ev.z is not None:
            ent = ents.setdefault(ev.id, ClearEntity(ev.id))
            ent.set_pos(ev.x, ev.z)
        if ev.masa is not None and ev.masa > 0:
            ent = ents.setdefault(ev.id, ClearEntity(ev.id))
            ent.set_masa(ev.masa)
    return ents


def decode_clear_full(payload, return_pj=False):
    """(ents, player_id, dead_ids, [pj_pos]): decodifica el frame UNA sola vez y
    devuelve las entidades + la marca de jugador activo (case 0x19/0x1a) +
    los ids de entidades MUERTAS (evento 0x07 SOLO: consumidor FUN_140789500
    case 7 = quita del IntHashSet +0x640 + destroy vtable 0x218; el case 9
    solo resetea la interpolacion +0x5f0 y 0x13 es removeParticle — NO son
    muerte). El binario elimina las celulas comidas AL INSTANTE; el visor
    las borra con esto (antes: timeout de 15s -> celulas fantasma).

    return_pj=True ademas devuelve la posicion del JUGADOR del evento 0x2e
    (FUN_140645d00: "Velocidad/posicion (x,z) del jugador", 2 campos u16 —
    la celula propia en FFA llega por este canal, NO como entidad del
    mundo). Formato: (a, b) crudos o None.

    self_ids: ids de las CELULAS PROPIAS marcados por el evento 0x1c
    (valor=1). Verificado en vivo 2026-08-16 (captura v5f): los 16 ids con
    0x1c son las celulas del jugador y TODOS correlacionan con los SETPOS
    del binario (dist media 0.04-1.9 u); el [19] plano de FFA NO son
    celulas propias (es leaderboard), el 0x19/0x1a es account_id y el
    flag=6 no llega — el 0x1c es la identificacion REAL en FFA.
    """
    events = parse_clear(payload)
    if not events:
        return ({}, None, [], None, []) if return_pj else ({}, None, [])
    ents = {}
    pid = None
    dead = []
    pj = None
    self_ids = []
    for ev in events:
        if ev.tipo in (0x19, 0x1a) and ev.id:
            pid = ev.id
        if ev.tipo == 0x1c and ev.id:
            # 0x1c = marca de celula propia (id + u16 v). NO filtrar por el
            # valor: en la captura v5f los reales tenian v=1 y v=2 (4399,
            # celula propia REAL con correlacion 1809/1809) y en vivo el
            # valor puede ser 0 — filtrar por valor descartaba TODOS los
            # self_ids en vivo (cells=0 con el mundo lleno). decode_clear_full
            # usa parse_clear con longitudes exactas -> no hay falsos
            # positivos por desincronizacion (eso era decode_dump_19).
            self_ids.append(ev.id)
        if ev.tipo == 0x2e and ev.raw:
            pj = (ev.raw[0], ev.raw[1])   # (a, b) crudos del 0x2e
        if ev.tipo == 0x04:
            # bloque de dump: valor = (flag, owner, id, field_count, vals)
            # parse_clear usa eid=field_count (campo d) — el id real es el
            # campo c. Los valores: vals[0]=masa, vals[1]=radio, vals[2]=x,
            # vals[3]=z (decode_dump_19, verificado 2026-08-14).
            # Para flag=8 (células), el id real está en owner (campo b).
            v = ev.valor
            if isinstance(v, (list, tuple)) and len(v) >= 5:
                flag, owner, eid_from_wire, fc, vals = v[0], v[1], v[2], v[3], v[4]
                # Determinar el id real según el flag
                if flag == 8:
                    eid_real = owner   # en flag=8, owner es el id real
                    real_owner = 0
                else:
                    eid_real = eid_from_wire
                    real_owner = owner
                ent = ents.setdefault(eid_real, ClearEntity(eid_real))
                ent.owner = real_owner
                if isinstance(vals, (list, tuple)):
                    if len(vals) >= 4:
                        ent.set_pos(_clamp_pos(vals[2]), _clamp_pos(vals[3]))
                    if vals and vals[0] > 0:
                        ent.set_masa(vals[0])
                    if len(vals) >= 2 and vals[1] > 0:
                        ent.radio = vals[1]
                if flag:
                    ent.entityType = flag
        if ev.tipo == 0x07 and ev.id:
            dead.append(ev.id)
        if ev.tipo == 0x05 and ev.valor:
            # 0x05 = setSize (FUN_140677930: escribe +0x90 = campo masa/size y
            # update mesh slot 0x140). [5, id, [size, flag]]: el consumidor
            # case 5 (lineas 1238-1275) con flag==0 ademas llama setRadius
            # (slot 0x1c8); con flag!=0 -> destroy vtable 0x218 (muerte).
            v1, v2 = (ev.valor + (0,))[:2]
            if v1 and v1 > 0:
                ent = ents.setdefault(ev.id, ClearEntity(ev.id))
                ent.set_masa(v1)   # recalcula radio como el binario
            if v2:
                dead.append(ev.id)
        if ev.x is not None or ev.z is not None:
            ent = ents.setdefault(ev.id, ClearEntity(ev.id))
            ent.set_pos(ev.x, ev.z)
        if ev.masa is not None and ev.masa > 0:
            ent = ents.setdefault(ev.id, ClearEntity(ev.id))
            ent.set_masa(ev.masa)
    # el id marcado por el server (0x19/0x1a) ES el jugador activo
    if pid is not None and pid in ents:
        ents[pid].entityType = 0x15   # jugador
    if return_pj:
        return ents, pid, dead, pj, self_ids
    return ents, pid, dead


def player_id_de_frame(payload):
    """Devuelve el id de la entidad del jugador si el frame trae la marca
    de jugador activo (case 0x19/0x1a del binario), o None."""
    events = parse_clear(payload)
    if not events:
        return None
    for ev in events:
        if ev.tipo in (0x19, 0x1a) and ev.id:
            return ev.id
    return None


def decode_payload_hex(hexstr):
    """Decodifica un payload CLEAR hex -> {id_entidad: ClearEntity}."""
    try:
        payload = bytes.fromhex(hexstr)
    except ValueError:
        return {}
    return decode_clear(payload)


def decode_dump_19(payload):
    """Decodifica el DUMP DEL MUNDO (frame CLEAR 0x64) con subtipos.

    Devuelve (ents, self_ids): self_ids son los ids de las CELULAS PROPIAS
    marcados por el evento 0x1c (valor=1) que viaja DENTRO del dump (el
    server FFA lo manda intercalado con los bloques 0x04 — la captura v5f
    lo confirmo: 16 ids unicos con 0x1c, correlacion 0.04-1.9 u contra los
    SETPOS del binario). decode_clear_full ya los devuelve para los frames
    no-dump; este camino los pierde -> own=None -> MASA 1 y camara fija.

    Formato REAL (Ghidra FUN_14076c400 case 4, disasm 0x14076c86f-0x14076c978;
    ver re/dump_19b_formato_real.md). El dump NO es de bloques fijos de 19B:
    es una secuencia de eventos CLEAR. El "bloque de dump" es el evento 0x04:

        [0x04][count u16][flag u16][id u32 BE][field_count u16][(count-4) valores]

    count  = total de u16 del bloque (8 comida/pos, 13 celula). Los 4 primeros
             u16 tras count son fijos (flag, id_hi, id_lo, field_count); el resto
             (count-4) se leen con FUN_1406f6300 == u16/SHORT_DIVISOR (o i32 float
             en FLOAT_MODE) -> mismo _leer_valor() que parse_clear.
    flag   = 1 (comida/posicion) | 8 (celula con masa).
    id     = id_hi<<16 | id_lo (u32 BE).
    valores (count-4):
        comida/pos: [tipo, fc, x, z]                       -> posicion (x, z)
        celula:     [tipo, fc, x, z, masa, v5, v6, v7, v8] -> posicion + masa

    SUBTIPOS:
      - comida   (flag=1, field_count=1): [0x04][00 08][00 01][id][00 01][00 04 00 2c][x z]
                 -> entidad con posicion (x=val[2], z=val[3]); sin masa.
      - pos 0x24 (flag=1, field_count=5): [0x04][00 08][00 01][id][00 05][00 24 00 7c][x z]
                 + evento 0x08 (id + x + z + y) de confirmacion.
      - celula   (flag=8, field_count=11): [0x04][00 0d][00 08][id][00 0b][00 4c 00 b4][x z] + 5 u16
                 -> entidad con masa (masa=val[4]) y posicion.
      - lista ids: evento 0x09 = id u16 (registra entidad).

    Las entidades quedan en escala real (u16/SHORT_DIVISOR, igual que el resto
    del protocolo CLEAR; NO se divide por GRID_SIZE/194165: ese valor es el
    tamano de celda del grid espacial DAT_1421b931c, usado en FUN_140924ff0,
    no en el dump)."""
    if not payload or payload[0] != 0x64:
        return {}, []
    ents = {}
    self_ids = []
    i = 1
    n = len(payload)
    nb_v = 4 if FLOAT_MODE else 2   # bytes por valor (modo FLOAT/SHORT)
    while i < n:
        t = payload[i]
        if t == 0x1c:
            # ---- 0x1c: MARCA DE CELULA PROPIA (id + u16 v; v=1 real) ----
            # identico a parse_clear: id + u16 valor, 5 bytes. SOLO v==1
            # marca celula propia (verificado v5f: 4362 val=1 x38); los
            # v!=1 son falsos positivos de desincronizacion (ids basura
            # 57347/58371 en el dump).
            if i + 5 > n:
                break
            sid = u16(payload, i + 1)
            vv = u16(payload, i + 3)
            if vv >= 0 and sid > 0:
                self_ids.append(sid)
            i += 5
            continue
        if t == 0x04:
            # ---- bloque de dump (evento 0x04) ----
            # Formato REAL (frame 332B, pares 0x04/0x08): el id es u16 en
            # i+7:i+9. Los 2 bytes en i+5:i+7 son otro campo (0x0000 en
            # comida flag=1, 0x0007 en celulas de otro jugador flag=2 =
            # probablemente owner_id). El u32 completo daba ids fantasma
            # (459293) duplicados del u16 real (541 = 459293 & 0xFFFF).
            if i + 11 > n:
                break
            count = u16(payload, i + 1)
            flag = u16(payload, i + 3)
            owner = u16(payload, i + 5)   # owner_id: 0 en comida, id de la
                                          # CUENTA dueña en células (captura
                                          # real: 0x0007 en célula ajena; el
                                          # op4 player_id coincide en las
                                          # propias — wire [count][flag][owner][id][fc])
            eid = u16(payload, i + 7)
            # field_count = u16(payload, i + 9)  (informativo: 1 comida/5 pos/11 celula)
            # Para flag=8 (células), el formato es [count][flag=8][id][fc][vals...]
            # donde i+5 es el id real (no owner). Para flag=1 (comida), i+7 es el id.
            if flag == 8:
                real_eid = owner   # en flag=8, owner es el id real
                real_owner = 0
            else:
                real_eid = eid
                real_owner = owner
            nvals = count - 4
            if nvals < 0 or nvals > 64:      # protege contra datos corruptos
                i += 1
                continue
            j = i + 11
            vals = []
            ok = True
            for _ in range(nvals):
                if j + nb_v > n:
                    ok = False
                    break
                v, nb = _leer_valor(payload, j)
                vals.append(v)
                j += nb
            if not ok:
                break
            ent = ents.setdefault(real_eid, ClearEntity(real_eid))
            ent.owner = real_owner
            if len(vals) >= 4:
                ent.set_pos(_clamp_pos(vals[2]), _clamp_pos(vals[3]))
            # MASA = vals[0] para TODOS los subtipos (verificado data-driven
            # 2026-08-14 con el dump de 332B: el evento 0x08 que sigue a cada
            # bloque 0x04 repite id + x + z + y, y y == vals[0]. Comida:
            # vals[0]=4/4=1 == FoodEntity._size=1 fijo del binario. Celula
            # flag=8: vals[0]=76/4=19. El subagente anterior uso vals[4] con
            # una sola muestra; vals[0] esta verificado contra N pares 0x04/0x08).
            if len(vals) >= 1 and vals[0] > 0:
                ent.set_masa(vals[0])
            # RADIO = vals[1] (descubierto 2026-08-14: el server lo manda
            # EXPLICITO en el dump 0x04; verificado en captura real: masa 60 ->
            # vals[1]=312/4=78 == floor(sqrt(60)*10+0.5)+1; comida masa 1 ->
            # vals[1]=44/4=11 == radio formula. Antes se interpretaba como
            # "tipo de campo" (0x2c/0x24) — era el radio escalado.)
            if len(vals) >= 2 and vals[1] > 0:
                ent.radio = vals[1]
            # entityType = FLAG del dump (campo 0 del array que recibe la
            # fabrica FUN_14073b220, verificado Ghidra 2026-08-14):
            #   1=Food 2=Player 4=Virus 5=Coin 6=FlagBase 7=Chest 8=Custom
            #   9=Image 0xc=Conquerable 0xd=Snakes 0xe=Skinned 0xf=Sprite
            # OJO: se asigna DESPUES de set_masa (que pone 0x14 por masa>0);
            # el flag es el tipo real del server.
            if flag != 0:
                ent.entityType = flag
            ent.eventos += 1
            i = j
        elif t == 0x08:
            # ---- posicion (evento 0x08): id u16 + x + z + y ----
            # y = masa (subagente 2: field 0x08 -> setMassAndRadius con args[2];
            # el dump de 332B lo confirma: id 360 -> 0x08 y=36, y vals[0] del
            # bloque 0x04 = 36. Mismo escalado u16/DIV).
            if i + 3 + 3 * nb_v > n:
                break
            eid = u16(payload, i + 1)
            x, _ = _leer_valor(payload, i + 3)
            z, _ = _leer_valor(payload, i + 3 + nb_v)
            y, _ = _leer_valor(payload, i + 3 + 2 * nb_v)
            ent = ents.setdefault(eid, ClearEntity(eid))
            ent.set_pos(_clamp_pos(x), _clamp_pos(z))
            if y > 0:
                ent.set_masa(y)
            i += 3 + 3 * nb_v
        elif t == 0x09:
            # ---- lista de ids (evento 0x09): id u16 ----
            if i + 3 > n:
                break
            eid = u16(payload, i + 1)
            ents.setdefault(eid, ClearEntity(eid))
            i += 3
        else:
            # evento regular: lo salta el dump (lo maneja parse_clear)
            i += 1
    return ({eid: e for eid, e in ents.items() if e.masa > 0 or e.x is not None},
            self_ids)


def decode_to_fields(payload_or_hex):
    """Compat: {campo: (tipo, valor)} para EntityTracker/feed_entity_frame.

    FORMATO NUEVO (2026-08-13, spec re/protocolo_absoluto.md): valores en
    ESCALA REAL (u16/SHORT_DIVISOR o i32 float; mundo 0..MUNDO_W). Sin reglas
    194165/500/21000 ni id 0xc8. El EntityTracker del visor NO debe dividir por
    ESCALA (ESCALA=GRID_SIZE queda solo para la ruta del dump 19B).

    Campos:  entidad      -> (0x00, x)   posicion X real
             entidad|0x80000000 -> (0x00, z)   posicion Z real
             KEY_MASA     -> (0x00, masa)  masa real (0x0c x10 / campo y de 0x08)
    Devuelve None si no es CLEAR o no hay campos de entidad."""
    if isinstance(payload_or_hex, str):
        try:
            payload = bytes.fromhex(payload_or_hex)
        except ValueError:
            return None
    else:
        payload = payload_or_hex
    if not payload or payload[0] != 0x64:
        return None
    if len(payload) > 1 and payload[1] == 0x04:
        return None  # dump 19B -> va por decode_dump_19
    ents = decode_clear(payload)
    if not ents:
        return None
    fields = {}
    for ent in ents.values():
        if ent.x is not None:
            fields[ent.id] = (0x00, round(ent.x, 3))
        if ent.z is not None:
            fields[ent.id | 0x80000000] = (0x00, round(ent.z, 3))
        if ent.masa > 0:
            fields[KEY_MASA] = (0x00, round(ent.masa))
    return fields


# =====================================================================
# API de compatibilidad con el harness re/validar_logs.py
# =====================================================================

_RE_CLEAR = re.compile(r"\[CLEAR\] ([0-9a-fA-F]{2,})")
_RE_AMF3 = re.compile(r"IN\s+TCP\s+(\[[^\]\r\n]*\])")


def parse_clear_line(line):
    """Linea de mito_view*.log -> (hexstr, fields_legacy) o (None, None)."""
    m = _RE_CLEAR.search(line)
    if not m:
        return (None, None)
    h = m.group(1)
    return (h, parse_clear_hex(h))


def parse_clear_hex(hexstr):
    """Compat: payload CLEAR hex -> fields {campo: (tipo, valor)} en ESCALA REAL
    (misma semantica que decode_to_fields)."""
    try:
        payload = bytes.fromhex(hexstr)
    except ValueError:
        return None
    if not payload or payload[0] != 0x64:
        return None
    if len(payload) > 1 and payload[1] == 0x04:
        return None
    return decode_to_fields(payload)


def firma_entidad(fields):
    """Firma de campos de un frame (para agrupar entidades)."""
    return tuple(sorted(fields.keys()))


def posiciones_de_fields(fields):
    """Itera (campo, coord) sobre los campos de POSICION (X/Z en escala real).
    El campo masa (KEY_MASA) no es una posicion."""
    for c, (t, v) in fields.items():
        if c == KEY_MASA:
            continue
        yield (c, float(v))


def masa_de_fields(fields):
    """Devuelve la masa real del frame (campo KEY_MASA) o None."""
    if not fields:
        return None
    m = fields.get(KEY_MASA)
    if m is None:
        return None
    return float(m[1])


def parse_amf3_line(line):
    """Linea de frida masa_capture*.log -> (op, args) o None."""
    m = _RE_AMF3.search(line)
    if not m:
        return None
    try:
        arr = __import__("ast").literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        return None
    if not isinstance(arr, list) or not arr:
        return None
    try:
        op = int(float(arr[0]))
    except (TypeError, ValueError):
        return None
    return (op, list(arr[1:]))


if __name__ == "__main__":
    import sys
    ejemplos = [
        "64080c2a0000affc0202",          # 0x08: id 3114, x=0, z=11263, masa=128.5
        "64000c2a0966affc",              # 0x00: id 3114, x=601.5, z=11263
        "640a02b3000100b91b00000000",    # 0x0a + 0x1b
        "64190008",                      # 0x19: marca de jugador id=8
        "641a0008",                      # 0x1a: marca de jugador id=8
    ]
    for h in ejemplos:
        print("payload:", h)
        for eid, ent in sorted(decode_payload_hex(h).items()):
            print("   ", ent)
        evs = parse_clear(bytes.fromhex(h))
        if evs:
            print("   eventos:", evs)
        print()
    if len(sys.argv) > 1:
        h = sys.argv[1]
        print("payload:", h)
        for eid, ent in sorted(decode_payload_hex(h).items()):
            print("   ", ent)
        print("   eventos:", parse_clear(bytes.fromhex(h)))
