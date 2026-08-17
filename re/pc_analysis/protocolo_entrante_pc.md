# Protocolo ENTRANTE (S→C) del PC — MitosisOG.exe — ANÁLISIS DEFINITIVO

> Fuente: GhidraMCP xebyte v5.14.2 (http://127.0.0.1:8089), MitosisOG.exe x86:LE:64 base 0x140000000
> Fecha: 2026-08-13. Sesión SOLO LECTURA. Decompilados crudos en `pc_analysis/_scratch/d_pc_*.c`
> Comparativa 1:1 vs Android (libApplicationMain.so 1.10.0): `android_analysis/opcodes_frames_entrada.md` + `android_analysis/clear_parser_android.md`

## 0. VEREDICTO (resumen ejecutivo)

**SÍ — el PC y el Android comparten el MISMO formato CLEAR.** El formato empírico antiguo
(id u8 + v:i32 con 194165/500/21000) queda **REFUTADO**:

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿Ids u8 o u16? | **u16 BIG-ENDIAN** (readUInt16 `FUN_140406320`) | parser eventos L406-1220 (todos los ids) |
| ¿Config "float"/"shortdivisor"? | **SÍ**, mecánica idéntica a Android (strings ofuscadas) | `FUN_1406f6300`: flag `+0x3f0` → i32→(float); si no → `u16 / DAT_1421b9278` (shortDivisor) |
| ¿194165 en el parser? | **NO** (0 hits en FUN_140789500 y FUN_14076c400) | grep 0x2f6dd = 0 |
| ¿500/100000/21000/1000000? | **NO** (0 hits: 0x1f4/0x186a0/0x5208/0xf4240) | grep = 0 |
| ¿Evento 0x0c masa ×10? | **SÍ** (`local_a78 * 10.0`, L1092) | igual que Android |
| ¿Score (op51/0x33) por AMF3? | **SÍ, por AMF3** (case 0x33 de FUN_140945f80 → IntMap +0x1a0, vtable 0x170/0x168) | 0 hits de 0x33 en parsers CLEAR |
| ¿Framing Haxe (u16BE len + u16BE 8)? | **NI en dispatcher NI en el parser de eventos**: el frame TCP es `[len u16 BE][flag u8][payload len bytes]`; el `04 00 08 00` es del formato de DUMP del mundo (19B/entidad, ruta case 10 → FUN_140975250) | dispatcher L80-128 |
| ¿Nº de tipos de evento? | **45** (los 44 del Android + **0x2a**) | tabla §6 |

---

## 1. Cadena de recepción (PC vs Android)

| Etapa | PC (MitosisOG.exe) | Android | Rol |
|---|---|---|---|
| Receptor TCP | `FUN_14097ca60` (0x14097ca60) | `LpF4Sz::dataReceived` 0x01c2f978 | Socket::readBytes → acumula en +0x10 → dispatcher |
| Dispatcher | `FUN_140977a40` (0x140977a40) | `processIncomingData` 0x01c2ef84 | header + routing CLEAR/AMF3 |
| callback registro | `FUN_14097e160` (0x14097e160) L839/L1054 | — | `"packetReceived"`→FUN_140963990; `"packetReceivedClear"`→FUN_1409662f0 |
| packetReceived (AMF3) | `FUN_140963990` → **`FUN_140945f80`** (0x140945f80) | `packetReceived` 0x01c253c8 | switch control AMF3 (1/2/3/4/10/40/51/52/53) + reenvío default |
| packetReceivedClear | `FUN_1409662f0` (0x1409662f0) | `packetReceivedClear` 0x01c2c36c | verifica Bytes (hash 0x20f64c9a) → reenvía al objeto escena `+0x50` por hash `0xfd5399ed` |
| Wrapper escena | `FUN_14076eed0` (0x14076eed0) | handler escena | convierte Dynamic→BytesInput → parser de eventos |
| Parser de eventos | **`FUN_14076c400`** (0x14076c400, 1245 líneas) | `HqJ8Md::packetClearReceived` 0x029d1148 (6211 líneas) | `[0x64 u8][tipo u8][campos]` → cola de eventos `+0x3a0` |
| Lector de valores | **`FUN_1406f6300`** (double) / `FUN_1406f6350` (Dynamic) | readUnsignedShort/_shortDivisor o readInt→float | `+0x3f0`=0 → `u16 BE / shortDivisor`; ≠0 → `i32 BE → (float)` |
| Consumidor de eventos | **`FUN_140789500`** (0x140789500, 2011 líneas, game loop `FUN_140795df0`/`FUN_140795600`) | `processFrame` 0x029e37ec | despacha por tipo de evento y aplica a entidades |
| Handler hash→tabla | `FUN_1406f4f70` → tabla `0x142062b38` = [0x140752e80, 0x14076c400] | — | registro del hash 0xfd5399ed |

**Hash de callback: el MISMO en ambos: `0xfd5399ed`** (= "packetReceived"). Uso verificado en:
FUN_1406f4f70 (CMP EDX,0xfd5399ed), FUN_140928d60 (invocador), FUN_1409336f0, FUN_1409662f0,
FUN_140966390, FUN_140975250, FUN_140977a40 (dispatcher), FUN_14097ca60 (dataReceived).

---

## 2. Dispatcher `FUN_140977a40` — formato EXACTO del frame TCP (verificado)

```c
// L80-128 del decompilado (d_pc_FUN_140977a40_dispatcher.c)
if (*(char *)(param_1 + 0x7c) != '\x01') return;        // loop mientras hay datos
iVar3 = *(int *)(param_1 + 0x28);                        // opcode/longitud actual (-1 = leer header)
if (iVar3 == -1) {
    if (2 < *(int *)(lVar7 + 8)) {                       // >= 3 bytes disponibles
        iVar3 = FUN_140406270(lVar7);                    // readByte (hi)
        uVar4  = FUN_140406270(lVar7);                   // readByte (lo)
        // endian: vtable+0x40 del objeto +0x20; == 1.0 → LITTLE; si no → BIG
        uVar4 = uVar4 | iVar3 << 8;                      // BIG-ENDIAN (default)
        *(uint *)(param_1 + 0x28) = uVar4;               // [opcode: u16 BE] = LONGITUD del payload
        if (uVar4 == 0xffff) {
            iVar3 = FUN_140406050(...);                  // readInt32 (4B extra)
            *(int *)(param_1 + 0x28) = iVar3 + 0xffff;   // opcodes/longitudes > 65535
        }
        iVar3 = FUN_140406270(...);                      // [flag: u8]
        if ((char)iVar3 < '\0') iVar3 += -0x100;         // sign-extend
        *(bool *)(param_1 + 0x2c) = iVar3 == 1;          // flag==1 → CLEAR (crudo)
        *(bool *)(param_1 + 0x2d) = iVar3 == 2;          // flag==2 → comprimido
    }
}
if (len - pos < iVar3) return;                           // esperar payload completo (iVar3 = longitud)
// ... copia payload a Bytes nuevo (FUN_140405dd0), checksum local_res24 = sig - 100, reset +0x28 = -1
if (*(char *)(param_1 + 0x2c) == '\0') goto AMF3;        // flag != 1 → ruta control
// ── RUTA flag==1 (CLEAR): payload EN CLARO, sin desturple ni AMF3 ──
plVar10 = *(longlong **)(param_1 + 0x50);                // objeto escena (callback)
lVar7 = (**(code **)(*plVar10 + 0x70))(plVar10, 0xfd5399ed);  // lookup hash
(**(code **)(lVar7 + 8))(plVar10, &local_1b8);           // → packetReceivedClear → FUN_14076c400
// ── RUTA flag != 1 (control) ──
FUN_1403cf030(&local_1e8, &local_1a8, ...);              // decode AMF3 (igual Android)
if (*(char *)(param_1 + 0x2d) != '\0') FUN_1404066c0(...); // flag==2 → uncompress
// ... Amf3Reader ... → FUN_140945f80(param_1, &valor)   // packetReceived (control)
```

**Formato EXACTO: `[opcode: u16 BE][flag: u8][payload: opcode bytes]`**
- El "opcode" del header es en realidad la **longitud del payload** (el opcode real va dentro del AMF3, item 0).
- `0xFFFF` → +u32 extra (longitudes > 65535). Endianness **BE por defecto**; swap a LE solo si el flag de endianness del ByteArrayData == 1.0 (nunca en la práctica).
- `flag == 1` → CLEAR binario crudo (0x64 + eventos), NO pasa por M2XC ni desturple.
- `flag == 2` → payload comprimido (uncompress antes del AMF3).
- `flag != 1` → AMF3 de control → `FUN_140945f80`.
- Loop `while (param_1+0x7c == 1)`: múltiples frames por read.
- **Idéntico al Android 0x01c2ef84** (`[opcode u16 BE][flag][payload]`, 0xFFFF→u32, flag==1 CLEAR, flag==2 comprimido).

**Primitivas de lectura** (haxe.io.BytesInput, BIG-ENDIAN default; swap si endian==1.0):
| Primitiva | Función | Fórmula |
|---|---|---|
| readByte | `FUN_140406270` | 1 byte, cursor +0x1c |
| readUInt16 | `FUN_140406320` | BE: `b1<<8\|b2`; LE (endian==1.0): `b1 + b2<<8` |
| readInt32 | `FUN_140406050` | BE: `((b1<<8\|b2)<<8\|b3)<<8\|b4`; LE si endian==1.0 |

---

## 3. `FUN_140945f80` — packetReceived AMF3 (control S→C) — casos verificados

| Opcode AMF3 | PC | Android | Formato leído |
|---|---|---|---|
| 1 (PING) | L456 `replyToPing` FUN_140965c10 | case 1 | idx2 flag, idx1 = timestamp double |
| 2 (LAG) | L512 → DAT_1421b9378/_lag, DAT_1421b9380/_serverTime | case 2 | idx1 int, idx2 double |
| 3 (LOAD) | L527 assets/players (FUN_1409563a0/956d00/957630) | case 3 | idx1 objeto |
| 4 (PLAYERID) | L744 → **DAT_1421b9364 = _playerId** | case 4 | idx1 int |
| 10 (SPAWN/world) | L475: idx1 objeto, campo0==0x18, FUN_140955a40/140607430 → **FUN_140975250** | case 10 (invite) | ruta del DUMP de entidades |
| 40 (CONFIRM_UDP) | L413 → `+0xc2`=1, idx1 string → FUN_140928dc0 | case 0x28 | this[0xC2]=1 |
| **51 (SCORE)** | L374 → **IntMap `+0x1a0`, vtable 0x170/0x168** | case 0x33 | idx1 int (score = masa máx. histórica) |
| 52 (SECURE_NONCE) | L428: idx1 string → AesDecrypt FUN_1403e94b0 → **sendPacket [0x2733, proof]** | case 0x34 | → 0x2733 |
| 53 (SECURE_CHALLENGE) | L419 → +0xe0/+0xe8 | case 0x35 | idx0/idx1 |
| **default** | L751: `FUN_140928d60(param_1+0x50, valor)` = **REENVÍO a hash 0xfd5399ed** (escena) | default | — |

**El score (op51/0x33) llega por AMF3, NUNCA por CLEAR** (0 hits de 0x33 en ambos parsers CLEAR). ✓

---

## 4. Lector de valores — config "float"/"shortdivisor" (clave del formato)

```c
// FUN_1406f6300 (0x1406f6300) — lee UN valor del stream (d_pc_FUN_1406f6300_value_reader.c)
double FUN_1406f6300(longlong param_1, undefined8 *param_2) {
  if (*(char *)(param_1 + 0x3f0) != '\0') {          // flag "float" (config del server)
    fVar1 = (float)FUN_140406050();                  // i32 BE → (float) → double   [modo FLOAT]
    return (double)fVar1;
  }
  iVar2 = FUN_140406320(*param_2);                   // u16 BE
  return (double)iVar2 / DAT_1421b9278;              // u16 / _shortDivisor          [modo SHORT]
}
// FUN_1406f6350: misma mecánica, escribe Dynamic (vía FUN_14002f570)
```

- **Offset del flag = `param_1 + 0x3f0` — el MISMO del Android** (`this[0x3f0]`). `0` = modo SHORT (u16/divisor), `≠0` = modo FLOAT (i32→float).
- **`DAT_1421b9278` = `_shortDivisor`** (doble global): init estático `FUN_140923070` → **`0x3ff0000000000000` = 1.0** (el Android usa default 10.0; ⚠️ ver §8). Lo sobrescribe la config del server: `FUN_1407be550` case 4, key `FUN_1407b43e0` → `DAT_1421b9278 = double` (el equivalente del key "shortdivisor" Android, con strings ofuscadas fkengine). Otro writer: `FUN_140690bd0`.
- Strings `"shortdivisor"` / `"smallfloat"` / `"float"` (config): **0 hits en claro** en el PC (los keys de config están ofuscados; el Android sí los tiene en claro a 0x00ee771c/0x00ee772a/0x00ee77c3).
- `FUN_140406320`/`FUN_140406050` usados aquí son los mismos del dispatcher (BE default).

**Los campos "valor" del CLEAR son `u16 BE / shortDivisor` (modo SHORT, default) o `i32 BE → (float)` (modo FLOAT)** — EXACTAMENTE el formato Android. No existe división por 194165/500 ni rangos.

---

## 5. Parser de eventos `FUN_14076c400` — mecánica (verificada, 1245 líneas)

```c
iVar6 = FUN_140406270(*param_2);                    // readByte
if (iVar6 == 100) {                                 // 0x64 = frame CLEAR
  *(int *)(param_1 + 0x5c4) += 1;                   // contador de frames CLEAR (mismo offset Android)
  while (len - pos >= 1) {                          // loop de eventos
    tipo = FUN_140406270(...);                      // [tipo: u8]
    ... switch por tipo (45 casos, tabla §6) ...
  }
  FUN_140225b00(*(param_1 + 0x3a0), &cola);         // push de la cola de eventos (mismo offset +0x3a0)
}
```

- **Ids de entidad: SIEMPRE `u16 BE`** (readUInt16 directo, no pasa por el divisor).
- **Valores: vía `FUN_1406f6300`/`FUN_1406f6350`** (§4): u16/divisor o i32/float.
- Cada evento se construye como array `[tipo, campos...]` (los valores suelen anidarse en índice 2: `[tipo, id, [vals...]]`) y se encola en **`param_1+0x3a0`** (cola de la escena). El game loop (`FUN_140795df0`/`FUN_140795600`, 60 fps) la consume con **`FUN_140789500`** (presupuesto 0x11=17 por tick, `param_1+0x3b8`).
- Posición (tipo 0/0x15/0x17/0x27): interpola con el mapa `param_1+0x5f0` (InterpolationHistory por id), array `+0x5d8`, count `+0x5e0`, multiplicador `+0x5f8`; clamp X/Z a `[0, DAT_1421c2a08+8 − 1]` / `[0, +0x10 − 1]` (boundaries del grid — el 21000 es runtime, no constante); rot con wrap ±2π en miliradianes (3141.592653589793 = π×1000, 6283.185307179586 = 2π×1000); altura ±50; flag "visto" en el IntHashSet `param_1+0x640`; flags de config `+0x48c`/`+0x48d`/`+0x48f` — **los mismos offsets que Android**.

---

## 6. TABLA COMPLETA DE TIPOS DE EVENTO — PC (45 tipos) vs Android (44)

"V" = valor leído con FUN_1406f6300 (SHORT: u16 BE / divisor [2B] | FLOAT: i32 BE→float [4B]).
"u16" = raw u16 BE directo. Tamaños: bytes totales del evento (incl. byte tipo), SHORT|FLOAT.
Columna Android = doc `clear_parser_android.md` (44 tipos: 0,1,3,4,5,6,7,8,9,a,b,c,d,e,f,10,11,13,14,15,16,17,18,19,1a,1b,1c,1d,1e,1f,20,21,22,23,24,25,26,27,28,29,2b,2c,2d,2e,2f).

| Tipo | Tamaño PC | Campos en orden (PC) | Evento emitido (PC) | Android (doc) | ¿Igual? |
|---|---|---|---|---|---|
| **0x00** | 7\|11 + var | `u16 id` + V x + V z (+ V y si 0x48c&&0x48f) (+ V rot si 0x15) (+ V v si 0x17/0x27/0x48d) | interpola y emite N×`[0, id, x_i, z_i, rot_i, ...]` con clamp a boundaries | 0x00: u16 id + x + z (+y) (+rot) (+v) | ✅ IGUAL |
| **0x01** | 15 | `u16 id` + 3×i32 BE (→float): x, y, z | `[1, id, [x,y,z]]` | 0x01: u16 id + i32×3 | ✅ IGUAL (doc Android dice 14 = typo, son 15) |
| **0x03** | 7\|9 | `u16 id` + u16 v1 + V v2 | `[3, id, [v1, ent]]` | 0x03: id + v1 + v2 | ✅ IGUAL |
| **0x04** | 11 + n×(2\|4) | `u16 count` + 4×u16 (a,b,c,d) + (count−4)×V | `[4, [a,b,c,d], [vals]]` | 0x04: a + b + c + d + n + n×vals (a = count−4) | ✅ IGUAL |
| **0x05** | 7\|9 | `u16 id` + u16 v1 + V v2 | `[5, id, [v1, ent]]` | 0x05: id + v1 + v2 | ✅ IGUAL |
| **0x06** | 3 | `u16 v` | `[6, v]` | 0x06: u16 id | ✅ IGUAL |
| **0x07** | 3 | `u16 id` | `[7, id]` | 0x07: u16 id | ✅ IGUAL |
| **0x08** | 9\|15 (+3 si 0xe) | `u16 id` + V x + V z + V y (+ u16 extra si 0xe) | `[8, id, [x,z,y,extra?]]` | 0x08: id + x + z + y (+extra si 0x0e) | ✅ IGUAL |
| **0x09** | 3 | `u16 id` | `[9, id]` | 0x09: u16 id | ✅ IGUAL |
| **0x0a/0x0b** | 7 | `u16 id` + u16 b + u16 c | `[tipo, id, [b', c]]` con **b' = (b−1), ×10 si >0** | 0x0a/0x0b: b×10 ((b−1)*10) | ✅ IGUAL (nuance: PC solo ×10 si (b−1)>0) |
| **0x0c** | 7\|9 | `u16 id` + u16 v + V masa | `[0xc, id, [v, masa]]` con **masa ×10.0** (L1092) | 0x0c: id + v + masa, **masa ×10.0** | ✅ **IGUAL (masa ×10 existe)** |
| **0x0d/0x0f** | 9\|15 + 3\|5 | `u16 id` + V x + V z + V y (+ u16 extra si 0xf) + u16 a + V v | `[tipo, id, [x,z,y,extra?,a,v]]` con **v ×10.0** (L1056) | 0x0d/0x0f: mismos campos, sin ×10 documentado | ⚠️ PC: v×10.0 (doc Android no lo muestra) |
| **0x0e** | 9\|15 | `u16 id` + V x + V z + V y | `[0xe, id, [x,z,y]]` | 0x0e: id + x + z + y | ✅ IGUAL |
| **0x10/0x11** | 5 | `u16 id` + u16 v | `[tipo, id, [v]]` | 0x10/0x11: id + v | ✅ IGUAL |
| **0x13** | 3 | `u16 id` | `[0x13, id]` | 0x13: u16 id | ✅ IGUAL |
| **0x14** | 4\|6 | `u16 v` + V ent | `[0x14, v, ent]` | 0x14: id + v | ✅ IGUAL |
| **0x15/0x17/0x27** | 7\|11 + var | igual que 0x00 (posiciones con rot/v/y) | emite `[0, id, ...]` | 0x15/0x17/0x27: bloque 0x00 | ✅ IGUAL |
| **0x16** | 5 + 2×n | `u16 id` + u16 n + n×u16 (raw) | `[0x16, id, [vals]]` | 0x16: **fijo** a+b+c (3×u16, 7B) | ⚠️ **PC variable (count), Android fijo 7B** |
| **0x18** | 7 + n×(2\|4) | `u16 id` + u16 v + u16 n + n×V | `[0x18, id, v, [vals]]` | 0x18: a + b + c + v (8\|10B) | ✅ IGUAL si n=1 (c = count) |
| **0x19/0x1a** | 3 | `u16 id` | `[tipo, id]` | 0x19/0x1a: u16 id | ✅ IGUAL |
| **0x1b** | 5 | `u16 id` + u16 bool | `[0x1b, id, bool]` | 0x1b: id + bool | ✅ IGUAL |
| **0x1c** | 5 | `u16 id` + u16 v | `[0x1c, id, [v]]` | 0x1c: id + v | ✅ IGUAL |
| **0x1d** | 3 | `u16 v` | `[0x1d, 0, [v]]` | 0x1d: u16 id | ✅ IGUAL (wire) |
| **0x1e** | 7 + n×(2\|4) | `u16 a` + u16 b + u16 n + n×V | `[0x1e, a, b, [vals]]` | 0x1e: a + b + n + n×vals | ✅ IGUAL |
| **0x1f** | 9 | 4×u16 | `[0x1f, a, b, c, d]` | 0x1f: 4×u16 | ✅ IGUAL |
| **0x20** | 5 + 2×n | `u16 id` + u16 n + n×u16 (raw) | `[0x20, id, [ids]]` | 0x20: id + n + n×u16 | ✅ IGUAL |
| **0x21** | 5 | `u16 id` + u16 v1 | **emite `[0x20, id, [v1]]`** | 0x21: a + b → [0x21, a, b] | ✅ wire IGUAL; ⚠️ PC re-emite como 0x20 |
| **0x22** | **7** | `u16 id` + u16 v1 + **u16 v2** | emite `[0x20, id, [v1,v2]]` | 0x22: **5B** a + b | ⚠️ **PC 3×u16 (7B) vs doc Android 2×u16 (5B)** |
| **0x23** | 9 | `u16 id` + 3×u16 | emite `[0x20, id, [v1,v2,v3]]` | 0x23: 4×u16 → [0x23, a,b,c,d] | ✅ wire IGUAL; ⚠️ PC re-emite como 0x20 |
| **0x24/0x25/0x26** | 5 + (0\|1\|2)×(2\|4) | `u16 id` + u16 v + (0\|1\|2)×V | **emite `[0x18, id, v, [ents]]`** | 0x24/25/26: id + b + (u16\|i32 v) 6\|8B | ⚠️ **PC: count de valores 0/1/2; doc Android: 1 valor 2\|4B** (ver §8) |
| **0x28** | 9 | `u16 id` + u16 b + u16 c + u16 d | `[0x28, id, [b', c, d−1(float)]]`; b'=(b−1) ×10 si >0; **d−1** | 0x28: a,b,c,d → d−1 | ✅ IGUAL |
| **0x29** | 1 | (sin campos) | `[0x29]` | 0x29: sin campos | ✅ IGUAL |
| **0x2a** | 9 | igual que 0x28 | `[0x2a, id, [b', c, d−1]]` | **NO EXISTE en Android** (default) | ⚠️ **SOLO PC** |
| **0x2b** | 1 | (sin campos) | `[0x2b, 0, []]` | 0x2b: sin campos | ✅ IGUAL |
| **0x2c** | 1 | (sin campos) | `[0x2c, 0, []]` | 0x2c: sin campos | ✅ IGUAL |
| **0x2d** | 5 | 2×u16 → **u32 = low + high<<16** | **emite `[0x1d, 0, u32]`** | 0x2d: id + v → [0x2d, id, v] | ✅ wire IGUAL (5B); ⚠️ PC lo comprime a u32 y re-emite como 0x1d |
| **0x2e** | 5 | `u16 a` + u16 b | `[0x2e, a, [b']]` con **b' = b×10** (int) | 0x2e: a + b, **b×10** | ✅ IGUAL |
| **0x2f** | 3 | `u16 id` | **sin evento**: `FUN_14005dcf0(+0x640, id, id)` marca id visto | 0x2f: [0x2f, id] + hash set +0x640 | ✅ IGUAL (PC no encola evento) |

**Total PC: 45 tipos** (0,1,3,4,5,6,7,8,9,a,b,c,d,e,f,10,11,13,14,15,16,17,18,19,1a,1b,1c,1d,1e,1f,20,21,22,23,24,25,26,27,28,29,**2a**,2b,2c,2d,2e,2f).
No existen 0x12 ni 0x30+ (caen en default sin acción). **Android: 44 — la única diferencia de cobertura es 0x2a (solo PC).**

---

## 7. Consumidor `FUN_140789500` — dispatch por tipo (36 códigos verificados)

Lee la cola `param_1+0x3a0` (`FUN_14004f600`), presupuesto `+0x3b8` ≥ 0x11 por evento; para cada evento
lee el campo 0 (`(**(**local_e68+0xb8))(local_e68, buf, 0)`) y compara con `FUN_1401181c0` (==) /
`FUN_1400d01d0` (invertido). Códigos (línea .c): 0x2C:739, 0x2B:797, 0x1B:803, 0x29:840, 0x28:847,
0x2A:852, 0x2E:912, 0x0A:932, 0x0B:990, 0x1F:994, 0x1E:1031, 0x1A:1061, 0x19:1072, 4:1083, 0x14:1091,
6:1103, 9:1108, 0x1D:1132, 7:1165, 5:1238, 0x20:1298, 0x18:1308, 0x16:1321, 3:1419, 0x1C:1657,
0:1668, 0x0C:1734, 0x13:1749, 8:1755, 0x0D:1794, 0x0E:1823, 0x0F:1813, 0x10:1851, 0x11:1863, **1:1218**,
0xffffffff:1686. Efectos clave (verificados en sesiones previas, `entity-processor-fun140789500.md`):
0x2C = SIMPLE_VALUE/masa (recorre mapa +0x308, muerte/spawn, foodCache DAT_1421c1700); 0x1C = addExp
(FUN_140685400, bonus x2); 0 = spawn con masa (setPosition FUN_140679380 + setMassAndRadius FUN_140677760);
5 = set size (FUN_140677930); 0x0C = applyParticle (FUN_140678b80); 0x13 = removeParticle; 3 = física de
entidad (FUN_1409254d0); 7/9 = muerte/limpieza; 0x10/0x11 = estado 0/1 (vtable 0x178); 0x20 = color
(vtable 0x188); 0x18 = rotación (vtable 0x180); 0x16 = trail/historial (FUN_140676b20); 0x2A = spawn food
(FUN_14078e190); 4 = comida comida (FUN_14073b220).

El parser emite exactamente 36 códigos tras unificar (0x15/0x17/0x27→0; 0x21/0x22/0x23→0x20;
0x24/0x25/0x26→0x18; 0x2d→0x1d; 0x2f→sin evento) = los 36 que consume. **Arquitectura cerrada 1:1 con Android.**

---

## 8. Diferencias PC vs Android (todo lo que difiere, con honestidad)

1. **Cobertura de tipos**: PC maneja **0x2a** (mismo handler que 0x28); Android no (cae en default).
2. **0x22**: PC lee **3×u16 (7B)**; el doc Android dice 2×u16 (5B). ⚠️ (posible simplificación del doc Android; verificar con su decompilado).
3. **0x16**: PC lee `id + count + count×u16` (variable); doc Android dice 3×u16 fijos (7B). ⚠️
4. **0x24/0x25/0x26**: PC lee `id + v + (0|1|2)×V` (el 0x26 lee 2 valores adicionales); doc Android dice `id + b + (u16|i32 v)` (1 valor). ⚠️ — ambos emiten al consumidor como 0x18; el caso n=1 del PC (0x25, 7|9B) es el que mejor encaja con el doc Android (6|8B + byte tipo). Posible doc Android impreciso.
5. **0x0d/0x0f**: PC multiplica **v ×10.0** (L1056); el doc Android no documenta ×10 para estos (solo 0x0c/0x0a/0x2e). ⚠️
6. **0x2d**: PC combina 2×u16 en **u32 (low + high<<16)** y lo re-emite como evento 0x1d; doc Android: `[0x2d, id, v]`. Wire igual (5B).
7. **Re-emisión**: PC unifica 0x21/0x22/0x23 → tipo 0x20, 0x24/25/26 → 0x18, 0x2d → 0x1d (el consumidor no necesita los códigos originales). El doc Android muestra cada tipo emitiéndose con su propio código.
8. **0x2f**: PC solo marca el hash set +0x640 (no encola evento); Android además encolaba `[0x2f, id]`.
9. **Default de `_shortDivisor`**: PC init estático = **1.0** (`FUN_140923070`: DAT_1421b9278 = 0x3ff0000000000000); Android ctor = 10.0. En la práctica el server manda el valor en config (setter `FUN_1407be550` case 4), así que ambos usan el del server.
10. **Anidamiento de arrays**: PC emite `[tipo, id, [vals...]]` (vals anidados en índice 2); doc Android muestra planos `[tipo, id, v1, v2...]`. Cosmético (consumidores distintos).
11. **Strings de config ofuscadas** en PC ("shortdivisor"/"float"/"smallfloat" no existen en claro); Android las tiene en claro.
12. **Case 10 del FP**: PC = SPAWN/entidades (→ FUN_140975250, dump 19B); Android = EVENT/invite. (Distinto, pero fuera del CLEAR.)

**Todo lo demás — formato de frame, endianness BE, ids u16 BE, valores u16/divisor o i32/float,
flags +0x3f0/+0x48c/+0x48d/+0x48f, cola +0x3a0, contador +0x5c4, hash set +0x640, interpolación
+0x5d8/+0x5e0/+0x5f0/+0x5f8, wrap rot ±2π mrad, clamp a boundaries, hash callback 0xfd5399ed,
score AMF3 case 0x33, nonce/challenge 0x2733, PLAYERID case 4 — es IDÉNTICO.**

---

## 9. Confirmaciones/refutaciones de las reglas antiguas (empíricas del visor)

| Regla empírica antigua | Veredicto | Evidencia |
|---|---|---|
| "ids u8" | ❌ **REFUTADA** | todos los ids son u16 BE (FUN_140406320) |
| "v:i32 con /194165" | ❌ **REFUTADA** | 0 hits de 0x2f6dd; el único divisor es `_shortDivisor` (DAT_1421b9278, config) |
| "masa = v/500 (21000<v<100000)" | ❌ **REFUTADA** | 0 hits de 0x1f4/0x5208/0x186a0; la masa se escala ×10 (0x0c/0x0d/0x0f) o por divisor |
| "coord directa v<=21000" | ❌ **REFUTADA** | el 21000 no es constante en el parser; clamp a boundaries runtime (DAT_1421c2a08) |
| "eventos de 7 bytes [00 TT CC V]" | ❌ **REFUTADA** | el parser lee `[tipo u8][campos según tipo]`; el 0x00 es el TIPO 0 (posición), no un separador |
| "0xc8 (id 200) = X del jugador" | ⚠️ no aplica al parser | 0 hits de 0xc8; los ids son opacos (u16) |
| "op51 = score/masa máx" | ✅ **CONFIRMADO** | case 0x33 AMF3 → IntMap +0x1a0 (vtable 0x170/0x168) |
| "dump 19B con field-codes 0x2C/0x24" | ✅ formato de DUMP (ruta case 10 → FUN_140975250) | el parser de eventos NO consume el dump 19B (los records no alinean como eventos) |
| "194165 = GRID_SIZE runtime" | ✅ (sesión previa) | no está en el parser; DAT_1421b931c, calibrado 194165 |

## 10. Archivos

- `pc_analysis/protocolo_entrante_pc.md` — este documento.
- `pc_analysis/_scratch/d_pc_FUN_140977a40_dispatcher.c` (247 líneas)
- `pc_analysis/_scratch/d_pc_FUN_140945f80_frame_processor.c` (1020 líneas)
- `pc_analysis/_scratch/d_pc_FUN_140963990_packetReceived.c`, `d_pc_FUN_14097ca60_dataReceived.c`
- `pc_analysis/_scratch/d_pc_FUN_14076c400_event_parser.c` (1245 líneas, COMPLETO)
- `pc_analysis/_scratch/d_pc_FUN_1406f6300_value_reader.c`, `d_pc_FUN_1406f6350_value_reader2.c`
- `pc_analysis/_scratch/d_pc_FUN_140789500_field_processor.c` (2011 líneas, copia de re/_decomp_140789500.txt)
- `pc_analysis/_scratch/d_pc_FUN_1409662f0_packetReceivedClear.c`, `d_pc_FUN_14076eed0_clear_wrapper.c`
- `pc_analysis/_scratch/d_pc_FUN_14097e160_setup.c` (registros packetReceived/packetReceivedClear)
- `pc_analysis/_scratch/d_pc_FUN_140406320_readUInt16.c`, `d_pc_FUN_140406050_readInt32.c`
- `pc_analysis/_scratch/d_pc_FUN_140923070_shortdiv_init.c`, `d_pc_FUN_1407be550_config.c`
