# Protocolo Haxe de MitosisOG.exe — Mapa (límites) y Física

> Documento de ingeniería inversa generado con Ghidra (base `0x140000000`, cliente Haxe ACTUAL de MitosisOG.exe).
> Verificado vía GhidraMCP (`http://127.0.0.1:8089`) el 2026-08-13 (parcial: el subagente alcanzó el límite de iteraciones; los puntos pendientes están marcados).
> Contraparte Flash vieja: `C:\Users\ren\Downloads\mito\mito\swf_scripts\scripts\fkengine\game\` (Instance.as, Grid.as, Player.as, GameEntity.as).
> Visor: `C:\Users\ren\Desktop\og mito\mito_view.py` (mundo 0–21000, ESCALA = 194165.0).

---

## 0. Resumen ejecutivo

- El **mundo es 21000×21000** (validado empíricamente en el visor; el grid espacial del cliente usa `cellSize = 512`).
- El **grid espacial** (`fkengine::game::Grid_obj`) particiona el mundo en segmentos `worldSize/cellSize` (≈ 41×41 con 21000/512) para broad-phase de colisiones.
- El **movimiento es server-authoritative + interpolado**: el cliente recibe posiciones por el CLEAR y las extrapola con markers (`Extrapolation`), no simula física propia de velocidad/fricción (la función de aceleración quedó pendiente de verificar).
- El **radio = floor(sqrt(masa)*10+0.5)** (sqrt = `FUN_141bf6990`), idéntico al Flash (`round(sqrt(size)*10)+1`).
- El **SPLIT (10010 = 0x271a)** se envía por TCP con `FUN_14096e330(socket, 0, 0x271a, args)`.
- El **spawn (opcode 20)** es `[x, y, z]` floats; x/z = coordenadas mundo; y ∈ {1, 702, 814, 1184, 1954} observado — candidato a MASA de spawn (pendiente de confirmar en el decompilado del case 0x14).

---

## 1. Límites del mapa (VERIFICADO)

### 1.1 Clase Grid
- `fkengine::game::Grid_obj` — RTTI `0x141dcc460`; `__new = FUN_140928270`, `__get = FUN_140926620`, `__set = FUN_140927a40`.
- **Campos** (offsets):
  - `+0x08` = **worldSize**
  - `+0x0c` = **worldOffset** (por defecto `0x200` = 512)
  - `+0x10` = `_entities`
  - `+0x18` = `_moveableEntities`
  - `+0x28` = `_overlapping`
  - `+0x40` = `_segmentW` (= worldSize/cellSize)
  - `+0x44` = `_segmentH` (= worldSize/cellSize)
- **Constructor** `FUN_140924140`: `*(p+0xc) = 0x200` (worldOffset por defecto = 512), `*(p+8) = param_3` (worldSize), `DAT_1421b931c = param_4` (cellSize), segmentos = `(int)(worldSize/cellSize)` en `+0x40`/`+0x44`.
- **Static init** `FUN_140928750`: `DAT_1421b931c = 0x200` (**512 = GRID_SIZE**) y construye el array estático `_boundaries` (4 elementos `[0, 1, -1, 0xffffffff]`, `DAT_1421bacf8`).
- **Factory** `FUN_140924900`: `new Grid(boundaries[1], boundaries[2])` — worldSize y cellSize vienen del **CONFIG del server** vía `_boundaries`.
- **`__isset`** `FUN_140928100` reconoce las keys `'GRID_SIZE'`, `'boundaries'`, `'CONNECTION_MECHANISM'`.

### 1.2 Grid espacial (broad-phase colisiones)
- `FUN_140924ff0` (core de update): clamp de celdas, re-insert, offsets de entidad `+0xdc`/`+0xe0` (gridX/gridY).
- `FUN_140925450` (updateEntityPosition).
- Las listas `_moveableEntities(+0x18)` + `FUN_140924ff0` son la base del broad-phase.

### 1.3 Constantes del mundo
| Constante | Valor | Dónde |
|---|---|---|
| cellSize / GRID_SIZE | **512** | `DAT_1421b931c` |
| worldOffset por defecto | 512 (0x200) | Grid+0x0c, constructor |
| worldSize | **del server** (config `_boundaries`) | Grid+0x08 — empíricamente **21000** |
| segmentos | worldSize/512 ≈ 41×41 | Grid+0x40/+0x44 |

> Para el visor: mantener **mundo 21000×21000** y clamp del jugador a [0, 21000] (validado en vivo: spawns (11263,1,1672), (9657,1,6086), (5249,1,3045), (3001,1,1698), (5556,1,13589) — todos dentro).

---

## 2. Física de movimiento (PARCIAL)

### 2.1 Verificado
- El **movimiento es interpolado/extrapolado, no simulado** en el cliente: clase `Extrapolation` (RTTI `0x141ed2ed0`, `__get = FUN_1414ecf10`, `__new = FUN_1414ed500`) con campos x(+8), z(+0x10), entityId(+0x18), marker(+0x1c), previousMarker(+0x20), frames(+0x24), ranForFrames(+0x28) — extrapolación x/z por frames con markers (el cliente solo pinta posiciones).
- El socket `LpF4Sz` (RTTI `0x141dcc890`) expone `write = FUN_1409645e0` y `writeWithNonce = FUN_140964470` (envío MOVE).
- Ruteo de red: `processFrame = HqJ8Md::FUN_140795600`; `packetReceived` de Game = `FUN_140769000` → `FUN_140752e80` (handler genérico de 64 KB, contiene los cases de opcode; opcode 0x14 spawn en línea 864, 0x1e (=30) en línea 665).
- En el frame processor `FUN_140795df0` (0x140795df0, ~47 KB): interpolación de masa `dVar32 = dVar32 - (dVar32 - dVar23) / 3.0` (offset `+0x158`); ticks de 16.666 ms (60 fps) con `dVar23 = *(double*)(param_1+0x4c8); if (16.0 <= dVar23)`.

### 2.2 Referencia Flash (cliente viejo — mismos MOVE)
- MOVE_SHORT 10022: `[timeAccu, ángulo, force]` (Instance.as:3493, 4783).
- MOVE 10005: `[timeAccu, 0, dirX, dirZ, force]` (Instance.as:4789, 4819).
- MOVE_LOOK_AT 10030: `[timeAccu, dirZ, dirX, force, atan2(lookAt)]` (3488, 4778).
- Envío cada 17 ms con acumulador `_icSendTimeAccu` (4768-4792) o `directionPacket` (4794-4823).
- El op2 AMF3 (93-113) = **power** (fuerza del mouse, sube con el uso) — ya confirmado en el Haxe.

### 2.3 PENDIENTE (próxima iteración)
- La función de **velocidad/fricción/aceleración** (PlayerEntity/InputManager, procesado de MOVE_10022/MOVE_10005 en el cliente) NO se pudo verificar (límite de iteraciones). Candidatos: `__get` de PlayerEntity/Game; buscar strings 'speed', 'friction', 'accel', 'velocity' en `re/_all_strings.txt`.

---

## 3. Radio desde masa (VERIFICADO)

- `FUN_141bf6990` = **sqrt** (verificado).
- `FUN_140677760` (setMassAndRadius): `dVar2 = floor(sqrt(masa)*10 + 0.5)`; notifica vtable `+0x1c8` con `(masa + 1)` y `+0x140`.
- Igual que Flash: `GameEntity.as:252 radius = Math.round(Math.sqrt(_size)*10)+1`; `_radius2 = _radius*_radius` (GameEntity.as:693-731).
- Para el visor: `radius = floor(sqrt(mass)*10 + 0.5)` → el +1 del Flash es el "borde" de la notificación; usar `radius = int(sqrt(mass)*10) + 1` como referencia visual.

---

## 4. SPLIT (10010 = 0x271a) (PARCIAL)

- Constante: `DAT_1421b8fc8 = 0x271a` (init `FUN_140680a20`).
- Envío: `FUN_140795df0` → `FUN_14096e330(socket, 0, 0x271a, args)`.
- **PENDIENTE**: el case 0x271a del switch de `FUN_140752e80` (handler genérico) no se extrajo por límite de iteraciones. En Flash viejo: `OP_CLIENT_DOUBLE_TAP` (10010) → `doDoubleTap` → split de células (Instance.as:3523). El server responde con las nuevas células por CLEAR.
- Empírico: SPLIT = 10010 TCP chan=1 (validado en tcp_full.py: `make_split_frame`).

---

## 5. Spawn — opcode 20 (PARCIAL)

- El handler genérico `FUN_140752e80` contiene `if (iVar5 == 0x14)` (opcode 20 decimal = 0x14) en la línea 864 del decompilado.
- **Formato empírico** (validado en vivo, capturas Frida): `[20, [x, y, z]]` floats:
  - Spawns: (11263, 1, 1672.6), (9657.5, 1, 6086), (6480.77, 1, 9124.89), (5249.12, 1, 3045.68), (3001, 1, 1698), (3023, 702, 7377), (11263, 1, 792.29), (5556, 1, 13589), (7424, 0, 7424), (0, 1184, 10124), (6076, 1, 3755), (11063, 1, 11245).
  - **x/z = coordenadas del mundo** (casi siempre Y=1, el plano).
  - **y ∈ {1, 702, 814, 1184, 1954}** — el 1 = recién nacido; los grandes correlacionan con la masa del usuario al respawn (1954 ≈ "va por 1900"; 814 y 1184 en respawns posteriores). **Hipótesis: y = MASA al spawn/respawn** (como el viejo Agario `[id, x, y, mass]`). PENDIENTE: confirmar en el decompilado del case 0x14.
- En el frame processor: spawn → `param_1+0x144`/`+0x150`/`+0x16c` + `FUN_140928f80`; status → `param_1+0xc4`.
- Flash viejo (referencia): evento 8/13/14/15 spawn → applyPosition + setMassAndRadius(masa) + alive + applyParticle + executeCmd (Instance.as:4586-4643).

---

## 6. Colisiones (PARCIAL)

- Broad-phase: grid espacial 41×41 (segmentW/segmentH = worldSize/512) con `_moveableEntities` + `FUN_140924ff0` (clamp celdas, re-insert).
- `FUN_140925450` (updateEntityPosition) actualiza la celda del grid al moverse.
- **PENDIENTE**: narrow-phase (solape entre células, EAT por contacto) no verificado; en Flash el evento 3 EAT es server-authoritative (`_loc6_.size += _loc39_.getEatSizeFor(_loc6_)`, Instance.as:4496-4499) — el Haxe no calcula EAT en cliente (server-authoritative; ver protocolo_haxe_particulas.md).

---

## 7. Pendientes globales (próxima subagente)

1. Extraer el decompilado del case `0x14` (spawn opcode 20) de `FUN_140752e80` → confirmar si `y` es masa.
2. Extraer el case `0x271a` (split) del mismo handler.
3. Función de velocidad/fricción: strings 'speed'/'friction'/'accel' en `re/_all_strings.txt`, xrefs desde PlayerEntity.
4. Escribir el motor del visor: clamp 0-21000, radio = sqrt*10, spawn y = masa.
