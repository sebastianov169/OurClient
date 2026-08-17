# Protocolo Haxe de MitosisOG.exe — Frame CLEAR binario (0x64)

> Documento de ingeniería inversa generado con Ghidra (base `0x140000000`, cliente Haxe ACTUAL de MitosisOG.exe).
> Todas las direcciones y decompilados verificados vía GhidraMCP (`http://127.0.0.1:8089`) el 2026-08-13.
> Contraparte de referencia Flash (viejo): `C:\Users\ren\Downloads\mito\mito\swf_scripts\scripts\fkengine\game\Instance.as` (`packetClearReceived` 2815-3296).
> Visor de validación en vivo: `C:\Users\ren\Desktop\og mito\mito_view.py` (escala calibrada **ESCALA = 194165.0**, mundo 0–21000).

---

## 0. Resumen ejecutivo

El frame CLEAR (`0x64`) del Haxe es el canal binario que transporta **todas las entidades** (células, comida, jugadores) con sus posiciones, masas, radios y partículas. NO pasa por el decode AMF3 (`FUN_1403cf030`): viaja con flag==1 (payload crudo) y se procesa en la **sección binaria del frame processor `FUN_140945f80`** (case `iVar7 == 10` del switch externo), que construye el descriptor con `FUN_140955a40` → empaqueta entidades con `FUN_140607430` → aplica con `FUN_140975250` → `FUN_140789500` (procesador de campos por entidad, ~89 KB).

**Flujo completo S→C:**

```
TCP bytes
  → FUN_14097ca60 (socket callback dataReceived, consume param_2+0x98)
  → FUN_140977a40 (dispatcher: opcode u16 en param_1+0x28; flags bool param_1+0x2c (==1), param_1+0x2d (==2))
      ├─ flag 0x2d == 1 → decode AMF3 FUN_1403cf030 (mensajes de control: ping, playerid, chat, score...)
      └─ flag 0x2d == 0 (binario) → callback 0xfd5399ed (param_1+0x50) o FUN_140945f80 (frame processor)
  → FUN_140945f80: case iVar7==10 (0x0A) → FUN_140955a40 (descriptor) → FUN_140607430 (empaqueta)
      → FUN_140975250 → FUN_140789500 (por entidad: lee field-codes y aplica)
```

**Estructura del frame que ve el visor Python (`decode_entity_frame`):**
```
64 + [00 tipo campo valor:u32] repetido   (7 bytes por campo)
```
- `payload[0] == 0x64` → frame de entidades (flag TCP = 1).
- `payload[1] == 0x04` → frame de LISTA (`64 04`): bloques `[04 00 08 00 01][id:u32][00 01 00 04 00 2c][val:u32]`, cada bloque = una partícula.
- Frames CLEAR de 2 campos con valores > 1e6: `x = V / 194165`, `z = V / 194165`.
- Campos con valor < 100000: masa = `v/500` (heurística del visor; el binario usa el campo `0x1C` para masa).
- AMF3 op51 (case 0x33 del FP): masa real = `op51 * 25` (score/masa máxima histórica; NO baja nunca).

---

## 1. Parser de eventos del frame CLEAR (verificado)

El parser de eventos es `FUN_14076c400` (en la tabla de handlers del hash: `FUN_1406f4f70`, `return &PTR_FUN_142062b38` para `-0x2ac6613 == 0xfd5399ed`; tabla en `0x142062b38` = `[FUN_140752e80, FUN_14076c400]`):

1. `readByte` (`FUN_140406270`, cursor `+0x1c`) == 100 (`0x64`) → frame CLEAR.
2. Bucle `while (bytes restantes >= 1)`: cada evento = `[byte tipo][campos...]`.

**Primitivas de lectura (todas en el dispatcher/FP):**
| Primitiva | Función | Lectura |
|---|---|---|
| readByte | `FUN_140406270` | 1 byte, cursor `+0x1c` |
| readUInt16 BE | `FUN_140406320` | 2 bytes `iVar1<<8 | uVar2` (swap si flag allocator == 1.0) |
| readInt32 BE | `FUN_140406050` | 4 bytes |

**Tabla de tipos de evento verificada:**
| Tipo wire | Significado | Campos |
|---|---|---|
| `0x01` (1) | **POSICIÓN ENTIDAD** | 1x u16 (field) + 3x i32 BE (`FUN_140406050`) → doubles x,y,z; crudo/194165 = coord mundo |
| `0x02` (2) | sin lectura explícita en loop (buffer de posición — presente en payloads `64 00 02` del visor) | — |
| `0x03` (3) | evento entidad | 2x u16 (valor + id entidad vía `FUN_1406f6300`) |
| `0x04` (4) | **SPAWN/BLOQUE** | 1x u16 (count-4) + 4x u16 (id,x,z,?) + count iteraciones de `FUN_1406f6300` (ids entidades) |
| `0x05` (5) | evento entidad | 2x u16 + id entidad vía `FUN_1406f6300` |
| `0x06` (6) | **partícula** | 1x u16 (valor) |
| `0x07` (7) | **partícula** | 1x u16 (valor) + float (valor de partícula) |
| `0x14` (20) | evento entidad move/player | 1x u16 + id entidad vía `FUN_1406f6300` |
| `0x2d` (45) | valor comprimido | 2x u16 → u32 = low + high<<16 |
| `0x2f` (47) | push valor | 1x u16 (lee y empuja al mundo) |

> El visor valida en vivo: frames CLEAR de 2 campos (>1e6) → posiciones /194165; la lista `64 04` → partículas (id ~ Z, val/194165 = X; ids 448–3277, vals 2704–13942).

---

## 2. MASA (verificado)

**El setter real de masa es `FUN_140677760` (offset `0x677760`)** — antes se intentó hookear `0x141dc6d28`, que es la **cadena "setMassAndRadius" en .rdata** (por eso `unable to intercept`):

```c
void FUN_140677760(longlong *param_1, double param_2) {   // (Entity*, double masa)
    if ((double)(int)param_1[0x12] != param_2) {           // si cambió
        param_1[0x18] = (longlong)param_2;                 // +0x18 = masa double
        *(int *)(param_1 + 0x12) = iVar1;                  // +0x90 = masa int
        dVar2 = (double)FUN_141bf6990((double)iVar1);      // sqrt
        dVar2 = floor(dVar2 * 10.0 + 0.5);                 // radio = floor(sqrt*10+0.5)
        (**(code **)(*param_1 + 0x1c8))(param_1, (double)(iVar1 + 1));  // +1
        (**(code **)(*param_1 + 0x140))(param_1);          // notify
    }
}
```

| Concepto | Offset / función | Detalle |
|---|---|---|
| Masa (double) | `entity + 0x18` (escrito por 0x677760) | masa real de la entidad |
| Masa (int) | `entity + 0x12` (offset 0x90) | masa como int (`_size`) |
| Radio | `floor(sqrt(masa)*10 + 0.5)` (sqrt = `FUN_141bf6990`) | mismo cálculo que Flash: `round(sqrt(size)*10)+1` |
| Wrapper Haxe | `FUN_140677830` (0x677830) | setMassAndRadius (lee double de arg vía vtable+0x40) |
| Interpolado | `FUN_1406775f0` (0x6775f0) | setMassAndRadiusInterpolado: `(1-alpha)*vieja + nueva*alpha` |
| Masa total jugador | `player + 0x08` (double acumulador) | Σ `_size` de células |
| pushMass | `FUN_140684cd0` | = Σ cell._size (+0x90) al campo +0x28 |
| addExp / campo `0x1C` (28) | `FUN_140685400` | suma masa al jugador con **bonus x2 bajo umbral exp2** (crecimiento al comer) |
| AMF3 op51 | case `0x33` del FP `FUN_140945f80` | **score = masa máxima histórica** (op51*25; nunca baja) |
| Masa en CLEAR (visor) | campos < 100000 | masa = v/500 (heurística validada: 0x3a=45052 → 90; 0x35=35320 → 71) |

**IMPORTANTE (anti-debug):** hookear con Frida la ruta de procesamiento de CLEAR S→C (dispatcher `0x977a40`, clear processor `0x975250`, dump de punteros en `0x945f80`) **crashea MitosisOG.exe** ~1s tras el spawn (verificado 3 veces). Los hooks SEGUROS son: decode AMF3 `0x3cf030`, frame_seed ligero (`0x945f80` solo lectura de seed), y los setters de masa `0x677760`/`0x677830`/`0x6775f0` (no disparan porque la masa del jugador va directo por el CLEAR, no por setMassAndRadius). La vía correcta para la masa actual es el **visor Python** que decodifica los CLEAR del socket TLS directamente.

---

## 3. Estructura de la entidad (offsets verificados)

| Offset | Campo |
|---|---|
| `+0x28` | x (coordenada) |
| `+0x2c` | id de entidad |
| `+0x30` | entityType (1 = comida; 0x14/0x15 = célula jugador) |
| `+0x34` | particle id activo (0 si no hay) |
| `+0x38` | valor de la partícula |
| `+0x58` / `+0x60` | mesh/objeto visual 1 y 2 |
| `+0x88` | radius |
| `+0x90` | _size (masa int) |
| `+0xa8` / `+0xb0` | x2 / z2 (destino interpolado) |
| `+0xb8` | tiempo de movimiento |
| `+0xc0` | _size destino |
| `+0xdc` / `+0xe0` | gridX / gridY |
| `+0x148` | objeto jugador (en el frame processor) |
| `+0x700` | IntMap de entidades |
| `+0x144`/`+0x150`/`+0x16c` | datos de spawn |

---

## 4. Identificación del jugador local

- El id del jugador llega por el **opcode 4 (OP_PLAYERID)** (AMF3; en el Flash viejo `_gameData.playerId`).
- En el CLEAR, las entidades con `entityType == 0x14/0x15` son células; el jugador local es el que coincide con el id del opcode 4 (o, empíricamente en el visor, la célula que spawnea con el opcode 20).
- En el frame processor, el objeto jugador se guarda en `param_1 + 0x148` (x en `+0xc` del objeto).

---

## 5. Interpolación / extrapolación

- Clase `Extrapolation` (RTTI `0x141ed2ed0`, `__get = FUN_1414ecf10`, `__new = FUN_1414ed500`): campos x(+8), z(+0x10), entityId(+0x18), marker(+0x1c), previousMarker(+0x20), frames(+0x24), ranForFrames(+0x28). El cliente extrapola x/z por frames con markers.
- En el FP: interpolación de masa `dVar32 = dVar32 - (dVar32 - dVar23) / 3.0` (offset `+0x158`), ticks de 16.666 ms (60 fps) en `FUN_140795df0` (`param_1+0x4c8`).
- Constantes de interpolación en el CLEAR: `0.32f` (0x47ae147b) y `0.25` (0x3fd0000000000000).
- En el Flash viejo: `_loc46_ = _usePacketInterpolation` eventos interpolados con `InterpolationHistory` (Instance.as:3099-3174); el Haxe hace lo mismo pero server-authoritative (solo pinta).

---

## 6. Envío (C→S)

- Router: `FUN_14096e330` (0x96e330) → `FUN_14096dc40` (encrypted) o `FUN_14096fa80` (plain; escribe header `0x40` + opcode param_2 + payload).
- Opcodes cliente (constantes del init `FUN_140680a20`): `DAT_1421b9020=10000`, `DAT_1421b8fec=0x2711`, **`DAT_1421b8fc8=0x271a` (10010 = SPLIT)**, `DAT_1421b8fc4=0x2727`, `DAT_1421b8f80=0x2733`, `DAT_1421b8f6c=0x2732`.
- MOVE: opcode 10022 MOVE_SHORT `[timeAccu, ángulo, force]` (Flash: `Instance.as:3493,4783`); 10005 MOVE `[timeAccu, 0, dirX, dirZ, force]` (Flash: `4789,4819`).
- Socket: `LpF4Sz` (RTTI `0x141dcc890`) expone `write = FUN_1409645e0`, `writeWithNonce = FUN_140964470` (envío MOVE con nonce).
- `FUN_140795df0` envía por TCP con `FUN_14096e330(socket, 0, op, args)` (op `0x271a`=10010 split, `0x2715`=10005).
- Checksum de integridad: `FUN_14093ab60` (suma XOR 0xef8) + `FUN_1403df080` (MurmurHash3).

---

## 7. Pendientes (no alcanzados por límite de iteraciones)

- Extraer el decompilado exacto del case `0x14` (spawn, opcode 20) y `0x271a` (split) del handler genérico `FUN_140752e80` (línea 864 del decompilado para 0x14; 0x1e=30 en línea 665).
- Verificar si el 2º valor del opcode 20 (`[x, y, z]`, y ∈ {1, 702, 814, 1184, 1954}) es masa de spawn o altura (evidencia empírica: correlaciona con la masa al respawn del usuario — 1954 ≈ "va por 1900").
- La función de velocidad/fricción (PlayerEntity/InputManager, procesado MOVE_10022/10005) — ver `protocolo_haxe_mapa_fisica.md`.
