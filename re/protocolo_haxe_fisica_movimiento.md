# Protocolo Haxe de MitosisOG.exe — Física de Movimiento y Spawn/Split

> Documento de ingeniería inversa generado con Ghidra (base `0x140000000`, cliente Haxe ACTUAL de MitosisOG.exe).
> Verificado vía GhidraMCP (`http://127.0.0.1:8089`) el 2026-08-13. Decompilados crudos en `re/decomp_mov/`.
> Fuentes: `_decomp_752e80.txt` (handler de paquetes), `_strings_movimiento.txt` (strings de movimiento), `re/_decomp/` (sesiones previas).

---

## 0. Resumen ejecutivo

1. **EL CLIENTE HAXE NO SIMULA FÍSICA PROPIA**: es **server-authoritative**. El jugador convierte
   input del mouse en dirección + fuerza, envía MOVE por TCP, y **solo interpola/extrapola** las
   posiciones recibidas. No hay fricción por frame ni aceleración newtoniana: el "freno" es un
   **lerp exponencial ×0.25** y el clamp de fuerza; la velocidad real la decide el servidor.
2. **El opcode 20 (spawn) NO trae masa**: `[x, y, z]` floats donde `y` es la **altura del terreno**
   (1 = nivel base; 702/814/1184/1954 = alturas observadas). La masa del jugador llega por el CLEAR
   (campo 0x1C) y el opcode 51 (score).
3. **SPLIT (10010 = 0x271a)**: mensaje de SALIDA sin argumentos: `[10010]` vía
   `FUN_14096e330(conn, flag=1, 0x271a, [])`.
4. **Power (op2 AMF3 93-113)**: ES la "force" del MOVE — fuerza mayor → el server mueve más lejos por tick.

---

## 1. Spawn — opcode 20 / case 0x14 (VERIFICADO, refutó la hipótesis de masa)

### 1.1 Ubicación
- Handler genérico de paquetes: `FUN_140752e80` (0x140752e80, 64 KB).
- Case `0x14` (opcode 20 decimal) en las **líneas 864-874** de `re/_decomp_752e80.txt`.
- Router: `packetReceived@Game = FUN_140769000` → `FUN_140752e80`.

### 1.2 Estructura exacta leída
```
case 0x14:
    lee EXACTAMENTE 3 campos del array [x, y, z] via accessor vtable+0xb8 (índices 2, 1, 0)
    cada uno convertido a FLOAT de 4 bytes con FUN_14007f3e0 (Number Haxe -> double -> float)
    los escribe via FUN_141806cb0 (setter trivial de 3 campos):
        obj+0x0c = param2   (z)
        obj+0x10 = param3   (y)
        obj+0x14 = param4   (x)
    en el objeto *(Game+0x4a8)
```

**Estructura destino** (objeto de coordenadas):
```
+0x00 vtable
+0x08 tipo
+0x0c z   (float32)
+0x10 y   (float32)
+0x14 x   (float32)
```

### 1.3 ¿Es `y` la masa? — NO, REFUTADO
- grep de `FUN_140677760` (setMassAndRadius) en el decompilado completo del handler: **0 coincidencias**
  (tampoco `FUN_140685400`/addExp ni `FUN_140678c80`/applyParticle).
- El valor se escribe como float32 en `+0x10` de un objeto de 3 coordenadas, no en los campos de masa
  (setMass escribe en Entity+0xC0 double y +0x48 int, y solo se llama desde `FUN_140677830` y `FUN_140789500`).
- Los valores empíricos {1, 702, 814, 1184, 1954} son **alturas/posición Y del terreno** (1 = nivel base).
- **Conclusión: la masa NO viaja en el spawn.** El visor debe mantener `y = altura` (o ignorarla) y
  la masa actual viene del CLEAR (campo 0x1C) y del op51 (score/masa máxima).

### 1.4 Case 0x1e (opcode 30)
- Presente en línea 665 del decompilado (no se extrajo el cuerpo completo — contexto: opcode 30
  relacionado con efectos/entidades, menos crítico).

---

## 2. SPLIT — 0x271a / 10010 (VERIFICADO)

- **NO está en `FUN_140752e80`** (grep: 0 coincidencias) — es mensaje de **SALIDA** (cliente → server).
- Se envía desde:
  - `FUN_1407815b0` (0x1407815b0)
  - `FUN_140781600` (0x140781600)
- Guard: jugador local (Game+0x310 → cells, count != 0) y llaman:
  ```
  FUN_14096e330(conn = Game+0x340, flag = 1, opcode = 0x271a, args = [])
  ```
  → **SIN argumentos: paquete `[10010]`** (flag 1 = canal TCP binario).
- Cadena de envío: `FUN_14096e330` (sender genérico conn/flag:byte/opcode:u32/args):
  - si websocket (`DAT_1421b8a84 == 1` y conn+0x168): `FUN_14096dc40` (asigna msgId en conn+0x198
    y serializa via `FUN_14096df30`)
  - si no: `FUN_14096fa80` (TCP plain, header 0x40)
- La constante `0x271a` como DWORD en .text aparece solo en: `0x140680ca6`, `0x1407815d8`
  (FUN_1407815b0), `0x140781630` (FUN_140781600), `0x140dd5140`, `0x140e52895`.

**Para el visor**: SPLIT = `send_tcp([10010])` (sin args), canal flag=1 — coincide con
`make_split_frame` de `tcp_full.py`.

---

## 3. Física de movimiento (VERIFICADO)

### 3.1 Modelo global: server-authoritative + interpolación
Cadena completa verificada:
1. `MouseInputManager.updateMouse = FUN_1414a8d20` (via trampolín `FUN_1414a91a0`, closure 'updateMouse'):
   - calcula vector dirección = `mousePos − centerPos` (campos `_joystickContainer+0x368`,
     `_stopJoystickContainer+0x3a0` en MouseInputManager)
   - **normaliza**: `dir = v/|v|` con `|v| = sqrt(x²+y²+z²)` (`FUN_141bf6990` = sqrt)
2. **'force' escalar** = `sqrt(clamp(dist/maxSpeed, 0.0, 1.0))` guardado en el jugador en `+0x298`
   (líneas 138-144 de updateMouse core).
3. Si `dist <= maxSpeed`: llama `FUN_1414a94a0` (interp); si no:
   `dVar7 = clamp(dist, maxSpeed, maxSpeed*3.0)` y velocidad:
   ```
   vX = (dirX_norm * dVar7) / (size * 2)
   vZ = (dirZ_norm * dVar7) / (size * 2)
   ```
   aplicada via slots vtable `+0x1c8`/`+0x1d0` (setPosition).
4. **Suavizado exponencial** (la "fricción" del cliente):
   ```
   pos += (target − pos) * 0.25
   ```
   (líneas 128-136: `plVar3[2] − (plVar3[2] − (dirX*maxSpeed + offsetX)) * 0.25`).
5. **ángulo** = `atan2(dirZ, dirX)` = `FUN_141c05178` (en el frame processor).
6. **get_speed de GameEntity = constante 0.2** (`FUN_140677ff0` → `FUN_14002f570(param, 0x3fc999999999999a)` = 0.2)
   — factor fijo de velocidad de animación/entidad.
7. **Interpolación de masa** en frame 60fps (`FUN_140795df0`):
   ```
   dVar32 = dVar32 − (dVar32 − dVar23) / 3.0     (offset +0x158)
   ```
   ticks de 16.666 ms (`+0x4c8`).
8. **Extrapolation**: `x += dx, z += dz` puro (`applyExtrapolation = FUN_1414c7ec0`: `pos += param_2`).
9. **applyPositionInterpolated = FUN_1406790f0**: `rot = wrap2pi(angleTarget)`,
   `x/z = lerp(x0, x1, alpha)` con `alpha = param_5`; wrap de ángulos con `±6.283185307179586`.

**NO hay fricción por frame ni aceleración newtoniana** — el "freno" es el lerp exponencial ×0.25
y el clamp de fuerza. El server decide la velocidad real; el cliente solo pinta.

### 3.2 Funciones clave (direcciones)
| Función | Dirección | Rol |
|---|---|---|
| `updateMouse` core REAL | `FUN_1414a8d20` | mates: normalización, clamp dist/maxSpeed, fuerza +0x298, velocidad dir*clamp/(size*2), lerp ×0.25 |
| trampolín 'updateMouse' | `FUN_1414a91a0` | → FUN_1414a8d20 |
| trampolín 'process' (slot +0x100) | `FUN_140a11d00` | process del MouseInputManager |
| `PlayerEntity.applyForce` REAL (slot +0x1a8) | `FUN_1414c7e40` | guarda dirX/dirZ en obj+0x100 (+0xc/+0x14 floats) y force en +0x108 |
| `PlayerEntity.applyExtrapolation` REAL (slot +0x1b0) | `FUN_1414c7ec0` | pos += delta (extrapolación pura) |
| `PlayerEntity.update` REAL (slot +0x1c0) | `FUN_140662930` | tick de la entidad (partículas, status, resetea timer +0x44) |
| `applyPositionInterpolated` | `FUN_1406790f0` | interp pos/rot con wrap 2π; lerp x/z con alpha |
| `get_speed` | `FUN_140677ff0` | devuelve **0.2** constante (0x3fc999999999999a) |
| trampolín applyForce base (GameEntity, slot +0x1a8) | `FUN_140678f90` | — |
| frame processor 60fps | `FUN_140795df0` | **ENVÍA LOS MOVEs** con FUN_14096e330: opcode `0x2715` (MOVE 10005) `[timeAccu, 0, dirX, dirZ, force]`, `0x2726` (MOVE_SHORT 10022) `[timeAccu, angulo, force]`, `0x272e` (MOVE_LOOK_AT 10030) `[timeAccu, dirZ, dirX, force, atan2]`; force leído de jugador+0x298; acumulador +0x4f8 cada 17ms |
| `MouseInputManager.__set` | `FUN_1414a6700` | campos: `_force +0x3b0`, `_lookAtForce +0x3b8`, `_mousePosition +0x378`, `_doubleTapTime +0x380`, `_doubleTapLocation +0x388`, etc. |
| `GenericInputManager.__set` | `FUN_1414a0520` | p1/p2/p4 botones, `_range +0x368`, `_radius +0x370`, `_joystick +0x390` |
| `MoveableEntity/PlayerEntity.__get` | `FUN_1414c8820` | closures: applyForce→FUN_140678f90, updatePosition→FUN_1406784b0, applyExtrapolation→FUN_140679060, moveTo→FUN_1414c7d80, set_radius→FUN_1406797c0 |
| `Extrapolation.__set` | `FUN_1414ed100` | x+8, z+0x10, entityId+0x18, marker+0x1c, previousMarker+0x20, frames+0x24, ranForFrames+0x28 |
| startSpeedup / endSpeedup / checkSpeedup | `FUN_140646040` / `FUN_1406460d0` / `FUN_140646910` | speedup tool: llama slot +0x70 del botón power |
| PlayerEntity vftable | `0x141dc53d8` | slots de 8 bytes (RVA_4B + flag_4B=1) |
| MouseInputManager class table | `0x141ecb830` | __new=FUN_1414a7150: _center, _direction, _mousePosition, _doubleTapTime, _taps, _doubleTapLocation, _lastForce, +0x3b8 _lookAtForce |
| GameEntity class table | `0x141dc7d10` | __new=FUN_14067dad0: speed, direction, _directionNormalized, _lastRealPositionX/Z, gridX/gridY, v1/v2 |

### 3.3 Power (op2 AMF3, bytes 93-113) — VERIFICADO
- Strings: `OP_POWER_READY` (0x141dc84a8), `OP_POWER` (0x141dc84c0), `OP_CLIENT_MOVE` (0x141dc8818),
  `OP_CLIENT_MOVE_SHORT` (0x141dc89f8), `OP_CLIENT_BEGIN_SPEEDUP` (0x141dc8a98),
  `OP_CLIENT_END_SPEEDUP` (0x141dc8af8), `OP_CLIENT_MOVE_LOOK_AT` (0x141dc8af8+).
- `PlayerEntity.applyForce` guarda el 3er arg (force) en `+0x108` — **ese force es el power**.
- En el frame processor: MOVE_SHORT `0x2726` envía `[timeAccu, angulo, force]` donde
  `force = *(jugador+0x298)` (el valor calculado por updateMouse como `sqrt(clamp(ratio))`).
- **El power afecta a la velocidad porque ES la 'force' del MOVE**: fuerza mayor → el server mueve
  más lejos por tick.
- Clamp de velocidad lado gráfico: `dVar7 = clamp(dist, maxSpeed, maxSpeed*3)` (maxSpeed en `+0x388`,
  bonus ×3.0 con `_bonusCooldown +0x3c8`) y la interp usa ×0.25 de easing.

---

## 4. Implicaciones para el visor Python (mito_view.py)

1. **Movimiento**: el visor YA envía MOVE por mouse (formato binario) — correcto. El servidor mueve;
   el visor interpola. Mantener el envío cada ~17ms con `[timeAccu, angulo, force]` (10022) y
   `[timeAccu, 0, dirX, dirZ, force]` (10005). La velocidad VISUAL del cliente real:
   `v = dir_norm * clamp(dist, maxSpeed, 3*maxSpeed) / (size*2)` con `dist = |mouse−centro|`,
   `maxSpeed ≈ +0x388` (config), y suavizado `pos += (target−pos)*0.25`.
2. **Spawn op20**: `y` = altura, NO masa. No usar el op20 para la masa (corregir comentario en visor).
3. **Masa**: CLEAR campo 0x1C (addExp, bonus x2 bajo exp2) + op51 score. Visor: campos < 100000 → /500 ✓.
4. **SPLIT**: `[10010]` sin args, canal flag=1 — ya implementado en `make_split_frame`.
5. **get_speed = 0.2** constante para animaciones (no para el movimiento real).

---

## 5. Pendientes menores (no críticos)

- Cuerpo completo del case 0x1e (opcode 30) en FUN_140752e80 (línea 665) — efectos de entidad.
- Valor exacto de `maxSpeed` (+0x388) desde la config del server (el cliente lo recibe en el LOAD).
