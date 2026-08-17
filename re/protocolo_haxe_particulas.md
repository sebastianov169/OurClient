# Protocolo Haxe de MitosisOG.exe — Partículas / Comida (Food)

> Documento de ingeniería inversa generado con Ghidra (base `0x140000000`, cliente Haxe ACTUAL de MitosisOG.exe).
> Todas las direcciones y decompilados fueron verificados vía GhidraMCP (`http://127.0.0.1:8089`).
> Contraparte de referencia Flash (viejo): `C:\Users\ren\Downloads\mito\mito\swf_scripts\scripts\fkengine\game\Instance.as`.
> Visor de validación en vivo: `C:\Users\ren\Desktop\og mito\mito_view.py` (escala calibrada **ESCALA = 194165.0**, mundo 0–21000).

---

## 0. Resumen ejecutivo

En el cliente Haxe la comida ya **no** llega como "evento 12 / evento 3 / evento 44" al estilo Flash.
Todo llega dentro de los **frames CLEAR de entidades** (`0x64`), donde cada entidad trae una lista de
**campos** (field-codes) que el procesador `FUN_140789500` interpreta:

| Campo (field-code) | Significado verificado |
|---|---|
| `0x0C` (12) | `applyParticle(id, valor)` — crea/actualiza partícula de comida |
| `0x0D` (13) | `applyParticle(id, valor)` — ídem (segunda variante) |
| `0x13` (19) | `removeParticle()` — elimina la partícula de la entidad |
| `9` | Limpia la partícula (`FUN_1406784e0`) — equivalente al "evento 44" por entidad |
| `0x1C` (28) | `addExp/masa` — `FUN_140685400`: suma masa al jugador (crecimiento al comer) |
| `0x2C` (44) | Lista de comida (frame `64 04`): recicla/reinserta partículas vía `foodCache` + grid espacial |
| `0x2B` (43), `0x2A` (42), `0x2E` (46), `0x28/0x29`, `0x1B`, `0x16`, `0x18`, `0x20`, `8`, `0x0F`, `0x0E`, `0x10`, `0x11` | Otros campos de entidad (spawn, nombres, color, alive, etc.) |

**Comer es server-authoritative**: el cliente no calcula el crecimiento por "EAT + eatSize" como Flash.
El servidor (a) manda `applyParticle` con el valor de la partícula, (b) cuando se come la partícula la
elimina con `removeParticle`/campo `9`, y (c) manda la masa nueva en el campo `0x1C` (y en AMF3 op51,
masa/25). El cliente solo aplica la masa recibida (con un bonus x2 si está por debajo del umbral `exp2`)
y recalcula la masa total como Σ del `_size` de sus células (`get_mass`/`pushMass`).

**Comida vs células (entityType)**: en el wire, `entityType == 1` = comida (igual que Flash).
Las células jugador son tipos `0x14`/`0x15` (20/21). Internamente `FoodEntity` es la clase Haxe **id 10**
(`FUN_14066e370`), y `get_entityType` devuelve el int en el offset `+0x30` de la entidad.

---

## 1. Clases Haxe y sus dispatchers (verificados)

### 1.1 FoodEntity — registro de clase
- `FUN_14066e370` (0x14066e370): registra la clase con **id numérico 10**:
  ```c
  undefined4 * FUN_14066e370(undefined8 param_1, undefined4 *param_2) {
      *param_2 = 10;                       // <- tipo de clase Haxe = 10 (Flash usaba entityType 1)
      *(char **)(param_2 + 2) = "FoodEntity";
      return param_2;
  }
  ```
- `FUN_14066f800` (0x14066f800): constructor del objeto de clase Haxe (`fkengine.game.entities.FoodEntity`
  en `141dc5cd0`): vftable `hx::Class_obj`, métodos de clase `FUN_14066e390` (new), `FUN_14066e490` (create),
  `FUN_14066f370` (getProperty estático), `FUN_14066f590` (setProperty estático), `FUN_14066f700`, `FUN_14066f780`,
  `FUN_14066fac0`.
- Strings de clase: `"FoodEntity"` @ `141dc5bf8`/`141dc5cd0`, `"_foodScale"` @ `141dc5c38`/`141dc5c88`,
  `"foodCache"` @ `141dc5c48`/`141dc5ca0`, `"textureCache"`, `"_randomColors"`; RTTI `.?AVFoodEntity_obj@...` @ `14214eae8`.

### 1.2 FoodEntity — constructor y factory
- `FUN_14066e390` (0x14066e390): `new FoodEntity()` — asigna **0xF8 (248) bytes**, limpia campos,
  vftable `fkengine::game::entities::FoodEntity_obj::vftable`.
- `FUN_14066e490` (0x14066e490): `FoodEntity.create(x, z)` — asigna, lee `x`/`z` de los args y llama
  `FUN_1406765a0(ent, x, z)`; **deja `_size = 1`** (`*(undefined4 *)(ent + 0x12) = 1`, offset `+0x90`):
  la comida se crea con tamaño 1 (el mismo check "type==1 && size==1" del procesador CLEAR).
- `FUN_1406765a0` (0x1406765a0): init de entidad: resetea campos, `gridX/gridY` (`+0xdc`) = -1,
  `+0x28` = x, `+0x2c` = id, crea los meshes (objeto en `+0x58`, segundo objeto en `+0x60`, texturas `+0x70`/`+0x78`).

### 1.3 FoodEntity — dispatcher de instancia (métodos/campos)
`FUN_14067a160` (0x14067a160) es el dispatcher Haxe (getProperty/setProperty/callMethod) de FoodEntity.
Bindings verificados (líneas del decompilado):

| Nombre Haxe | Implementación | Rol |
|---|---|---|
| `applyParticle` | `FUN_140678c80` → `FUN_140678b80` | crear/actualizar partícula |
| `removeParticle` | `FUN_140678580` → `FUN_1406784e0` | eliminar partícula |
| `get_eatSize` | `FUN_140676d40` | tamaño que aporta al comer (vtable `0x118`) |
| `update` | `FUN_140679550` | update por frame |
| `remove` | `FUN_140679e20` | quitar del padre (vtable `0x218`) |
| `insert` | `FUN_1406779b0` | insertar en el mundo (grid de colores/texturas) |
| `reuse` | `FUN_140677460` → `FUN_1406773d0` | reusar en (x,z) |
| `get_id` | `FUN_140677f90` | devuelve `*(ent+0x2c)` |
| `get_entityType` | `FUN_1400f1b80` | devuelve `*(ent+0x30)` |
| `get_entityBase` | `FUN_140677fc0` | base de entidad |
| `get_size` | `FUN_140125220` | _size |
| `get_radius` | `FUN_140679e50` | radio |
| `setPosition` | `FUN_1406783d0` | posicionar |
| `updatePosition` | `FUN_1406784b0` | actualizar posición |
| `get_position` | `LAB_140650920` | posición |
| `radiusAnimated` | `FUN_140678f50` | radio animado |
| `validate` / `invalidate` / `get_visible` / `get_points` / `showExp` / `get_exp` / `buildMesh` / `setZOrder` / `executeCmd` | varios | utilidades de entidad |

Campos de instancia (offsets verificados):
- `+0x28` = x (coordenada), `+0x2c` = id de entidad, `+0x30` = entityType,
- `+0x34` = **particle id activo** (0 si no hay partícula), `+0x38` = **valor de la partícula**,
- `+0x58` = mesh/objeto 1, `+0x60` = objeto 2, `+0x88` = radius, `+0x90` = _size,
- `+0xa8` = x2 (destino), `+0xb0` = z2, `+0xb8` = tiempo de movimiento, `+0xc0` = _size destino,
- `+0xdc` = gridX, `+0xe0` = gridY.

### 1.4 FoodEntity — estáticas de clase
- `FUN_14066fa50` (0x14066fa50): init estático: `foodCache = new Map()` → `DAT_1421c1700`,
  `_foodScale = 0` → `DAT_1421b8e98`, `textureCache = new Map()` → `DAT_1421c1708`,
  `_randomColors` → `DAT_1421c1710`.
- `FUN_14066e660` (0x14066e660): getter lazy de `_foodScale`:
  ```c
  double FUN_14066e660(void) {
      if (DAT_1421b8e98 != 0.0) return DAT_1421b8e98;   // cache
      ... // lee un valor de config (lookup por clave en DAT_141dc5c20)
      dVar2 = (double)(...vtable 0x130...)();            // valor de config
      DAT_1421b8e98 = dVar2 * 0.5;                       // ¡¡escala = config * 0.5!!
      return dVar2 * 0.5;
  }
  ```
  **`_foodScale = valorConfig * 0.5`** — es el multiplicador de escala visual de la comida.
  (`resetCache` → `FUN_14066ebf0` pone `DAT_1421b8e98 = 0` para forzar recálculo.)
- `FUN_14066f370`/`FUN_14066f590` (0x14066f370/0x14066f590): get/set estático (`foodCache`, `_foodScale`,
  `textureCache`, `_randomColors`, `resetCache` → `FUN_14066ebf0`).

---

## 2. Recepción de frames (red → entidades)

### 2.1 Cadena verificada
1. `FUN_14092ca30` (0x14092ca30) y `FUN_14092c9d0` (0x14092c9d0): poll del socket/búfer de frames
   (llamadas desde el procesador principal de red).
2. `FUN_140795df0` (0x140795df0, ~47 KB): **procesador de red principal del juego**
   (registrado como handler: xrefs DATA en `141dcb9b0`, `141fadb00`, `141fadb70`, `142274358`).
   - Envía por TCP con `FUN_14096e330(socket, 0, op, args)` (op `0x271a`=10010 split, `0x2715`=10005).
   - Interpola la masa del jugador: `dVar32 = dVar32 - (dVar32 - dVar23) / 3.0` (offset `+0x158`).
   - Ticks de 16.666 ms (60 fps): `dVar23 = *(double*)(param_1+0x4c8); if (16.0 <= dVar23) { ... FUN_140789500(...) ... }`.
   - Por cada frame de entidad llama `FUN_140789500(param_1, code, parseResult)`.
3. `FUN_140795600` (0x140795600): wrapper → `FUN_140789500(param_2, uVar2, uVar4)`.
4. `FUN_140789500` (0x140789500, ~89 KB): **procesador de campos de entidad (CLEAR)** — detalle abajo.
5. `FUN_140975250` (0x140975250): dispatcher de mensajes registrados (varios handlers con callbacks,
   p.ej. `FUN_140975530`, `FUN_140975e60`, `FUN_140976790`, `FUN_1409770c0`) — sistema de mensajes Haxe.

### 2.2 Estructura del frame CLEAR (como la ve el visor Python)
Formato por el visor (`mito_view.py`, `decode_entity_frame`):
```
64 + [00 tipo campo valor:u32] repetido   (7 bytes por campo)
```
- `payload[0] == 0x64` → frame de entidades (flag de TCP = 1).
- `payload[1] == 0x04` → frame de LISTA (`64 04`): bloques `[04 00 08 00 01][id:u32][00 01 00 04 00 2c][val:u32]`,
  cada bloque = una partícula (`id` ~ coordenada Z, `val/194165` = X; validado en vivo: ids 448–3277, vals 2704–13942).
- Frames CLEAR de 2 campos con valores > 1e6: `x = V / 194165`, `z = V / 194165` (escala calibrada ESCALA=194165).
- Campos con valor < 100000: masa = `v/500` (heurística del visor; el binario usa el campo `0x1C` para masa).
- AMF3 op51 (`case 0x33` del frame processor `FUN_140945f80` @ 0x140945f80): masa real = `op51 * 25`.

---

## 3. Procesador de campos CLEAR: `FUN_140789500` (0x140789500)

Para cada entidad del frame (`(**(code **)(*parser + 0xb8))(parser, &ent, idx)`), lee campos por su
field-code y aplica:

### 3.1 applyParticle — campos `0x0C` (12) y `0x0D` (13)
```c
local_cd8 = 0xc;   // field-code 12
... if (campo presente) {
    uVar15 = leer(tipo 1);  uVar11 = FUN_1400219d0(...);   // id / valor
    FUN_140678b80(ent, uVar11);                            // applyParticle(ent, ...)
}
local_cbc = 0xd;   // field-code 13
... if (campo presente) {
    uVar15 = leer(tipo 5);  uVar11 = FUN_1400219d0(...);   // id / valor
    FUN_140678b80(ent, uVar11);
}
```
Implementación (verificada, `FUN_140678c80` → `FUN_140678b80` @ 0x140678b80):
```c
void FUN_140678b80(longlong ent, int size, int value) {
    plVar1 = *(longlong **)(DAT_1421c3bf8 + 8);            // manager de partículas
    if (plVar1 && (**(code **)(*plVar1 + 0x170))(plVar1, DAT_1421b8844 + size)) {
        iVar3 = (int)DAT_1421b9278;                        // masa/valor global actual
        if (65530.0 <= (double)(iVar3 * size) / 10.0)      // ¡umbral de tamaño!
            size = -1;                                     // partícula "demasiado grande" -> borrar
        if (*(int *)(ent + 0x34) == size) {                // ya tengo esta partícula
            *(int *)(ent + 0x38) = value;                  // actualizar valor
            return;
        }
        FUN_1406784e0(ent);                                // limpiar partícula anterior
        if ((0 < size && FUN_140a2a5c0(DAT_1421b8844 + size) == -1.0) || size == -1)
        { *(int *)(ent + 0x34) = size; *(int *)(ent + 0x38) = value; }  // guardar id+valor
        FUN_1406786f0(ent, size);                          // aplicar visual (escala del sprite)
    }
}
```
Semántica (equivalente Haxe del Flash `applyParticle [id, size, particle*10]`):
- `size` = id/tipo de partícula (índice en `DAT_1421b8844`), `value` = valor/masa de la partícula.
- Si `(masaActual * size) / 10 >= 65530` → la partícula se descarta (size = -1): comida que ya no se
  puede comer/ver por tamaño.
- `size == -1` o lookup de config = -1.0 → partícula marcada para borrar.
- El id activo queda en `ent+0x34` y el valor en `ent+0x38`.

### 3.2 removeParticle — campo `0x13` (19) y limpieza — campo `9`
```c
local_cd4 = 0x13;   // field-code 19
... if (campo presente) FUN_1406784e0(ent);               // removeParticle
...
local_cdc = 9;      // field-code 9
... if (campo presente) {
    *(undefined1 *)(ent + 0x14) = 0;                      // alive = false
    ... objetos ocultos ...
    if (*(int *)((longlong)ent + 0x34) != 0) FUN_1406784e0();   // limpiar partícula
}
```
`FUN_1406784e0` (0x1406784e0) = **limpieza de partícula** (el "evento 44" del Flash, pero por entidad):
```c
void FUN_1406784e0(longlong ent) {
    if (*(int *)(ent + 0x34) != 0) *(undefined8 *)(ent + 0x34) = 0;   // id = 0
    if (*(longlong *)(ent + 0x40) != 0) {                             // lista de partículas
        ... libera cada elemento ...
        *(undefined8 *)(ent + 0x40) = 0;
    }
}
```

### 3.3 Masa / crecimiento — campo `0x1C` (28)
```c
local_cec = 0x1c;   // field-code 28
... if (campo presente) {
    iVar10 = FUN_1400219d0(leer(...));                    // delta de masa
    FUN_140685400(jugador, (double)iVar10);               // sumar masa al jugador
}
```
`FUN_140685400` (0x140685400) = **addExp / ganar masa**:
```c
void FUN_140685400(longlong player, double param_2, ...) {
    ... lee "registered" (si está registrado, return) ...
    uVar8 = lee("exp");                                    // exp acumulado actual
    uVar3 = lee("exp2");                                   // umbral exp2
    dVar9 = (double)(int)uVar8 + param_2;
    if (dVar9 < (double)(int)uVar3)
        param_2 = param_2 + param_2;                       // ¡¡dobla la ganancia si exp+delta < exp2!!
    ... escribe exp ...
    param_2 = param_2 + *(double *)(player + 8);           // acumulador de masa en +0x08
    *(double *)(player + 8) = param_2;
    FUN_140676e00(entity, (int)param_2, ...);              // popup de EXP (throttle exp_show_millis)
}
```
- La masa del jugador se acumula en el **double de `+0x08`** (`get_mass` → `FUN_140685390` devuelve ese offset;
  `_accExp` es el mismo offset).
- `pushMass` → `FUN_140684cd0` (0x140684cd0): recalcula la masa total como **Σ del `_size` (+0x90) de todas
  las células** de `+0x10` (array de células) y la guarda en `+0x28`.
- `get_mass` → `FUN_140685390` (0x140685390): misma Σ → double. **La masa del jugador = Σ cell._size.**

### 3.4 Lista de comida `64 04` — campo `0x2C` (44): reciclaje foodCache + grid
```c
local_c94 = 0x2c;   // field-code 44
... si el sub-frame tiene campo 0x2c {
    // itera la lista de partículas visibles (array en el mundo, param_1+0x308+0x10)
    for (cada partícula en la lista) {
        iVar10 = (**(code **)(*p + 0x158))();             // getEntityType()
        if (iVar10 == 1) {                                // ¡¡type 1 == FOOD!!
            if (!esComidaValida) {                         // no food o _size != 1
                quitar del grid espacial (param_1+0x2b8, hash por id via 0x220)
            } else {
                // reusar: sacar del foodCache y reinsertar
                FUN_1409238c0(&e, p, 0);
                FUN_1400286d0(DAT_1421c1700, e);          // foodCache.put(id, entidad)
                grid re-insert (param_1+0x2b8, clave local_320)
                reset de meshes (vtable 0x1c8/0x1d0)
            }
        }
    }
}
```
Este es el equivalente Haxe de la lista `64 04` del visor: el servidor manda `(id, val)` de cada
partícula visible y el cliente **recicla las entidades FoodEntity desde el `foodCache`
(`DAT_1421c1700`)** reinsertándolas en el grid espacial (`param_1+0x2b8`). Las que ya no son
comida (`type != 1` o `_size != 1`) se sacan del grid (partículas comidas/desaparecidas).

### 3.5 Otros campos de entidad (contexto)
- `0x2B` (43) y `0x2A` (42): spawn/posición de entidad (`FUN_1407873b0` + `FUN_140647530(x, z, ...)` en `param_1+0x320`).
- `0x2E` (46): `FUN_140645d00(...)` con dos valores.
- `0x28` (40) / `0x29` (41): flags de estado (`+0x64c`, `+0x650`).
- `0x20` (32): vtable `0x188` (color).
- `0x18` (24): vtable `0x180` + double (rotación).
- `0x16` (22): lista de nombres (username via `FUN_1406850b0`, name via `FUN_140685190`).
- `0x0F` (15) / `0x0E` (14): dobles → vtable `0x178`.
- `8`: alive (visible).
- Tipos de entidad en el frame: `(int)ent[6]` (offset `+0x30`); `0x14`/`0x15` (20/21) = jugadores
  (se saltan la lógica de partícula); `1` = comida (insert en grid solo si `type==1 && _size==1`).

---

## 4. Posicionamiento y escala

- **Escala del mundo**: el visor calibró `ESCALA = 194165.0` (`crudo / 194165 = coord mundo`); mundo real
  0–21000. Los campos de posición del CLEAR viajan como u32 crudos (> 1e6) y se dividen por 194165.
  (En el binario, las posiciones se aplican vía `FUN_140679380` (setPosition: `+0xa8`/`+0xb0` + tiempo en
  `+0xb8`, llamada a vtable `0x1b8` con `t/1000` y `FUN_140678360` que mueve los meshes `+0x58`/`+0x60`)
  y `updatePosition` `FUN_1406784b0`.)
- **Escala visual de la comida**: `_foodScale = valorConfig * 0.5` (`FUN_14066e660`, global `DAT_1421b8e98`,
  cacheado; `resetCache` `FUN_14066ebf0` lo invalida). Se aplica en el build del mesh de FoodEntity.
- **Radio visual de células** (`FUN_140677760` setSizeInterpolado): `radio = sqrt(_size) * 10 + 1`
  (`FUN_141bf6990` = `sqrt`; `floor(dVar2 * 10.0 + 0.5)`, luego vtable `0x1c8` con `(int)+1`).
- **Interpolación de cámara/posición**: constante float `0x47ae147b` (= 0.32) en `FUN_140c08030`
  (lerp) y `0x3fd0000000000000` (= 0.25) en el procesador CLEAR.
- **FoodEntity creada con `_size = 1`** (`FUN_14066e490`: `*(ent + 0x12) = 1`) — coincide con el check
  "food = type 1 && size 1" del procesador.

---

## 5. Comer (EAT) y crecimiento — flujo completo verificado

1. El servidor manda la comida con `applyParticle` (campos `0x0C`/`0x0D` del CLEAR) →
   `FUN_140678b80`: guarda `id` en `+0x34` y `valor` en `+0x38`; si `(masa * size)/10 >= 65530` la descarta.
2. Al comerla, el servidor la elimina → campo `0x13` (removeParticle) o campo `9` (limpieza) →
   `FUN_1406784e0` (id = 0, libera lista de partículas de `+0x40`), y la entidad se saca del grid
   (sección `0x2C`).
3. El crecimiento NO lo calcula el cliente: la masa nueva llega en el campo `0x1C` →
   `FUN_140685400` (addExp): `masa += delta` en el double de `+0x08`, con **bonus x2** si
   `exp + delta < exp2`; y en AMF3 op51 (`case 0x33` de `FUN_140945f80`): `masa = op51 * 25`.
4. `get_eatSize` (`FUN_140676d40`, binding en los dispatchers de FoodEntity/Player/Virus:
   `14067a160`, `140670c50`, `14064f060`, `1414bf240`, `1414c4330`, `1414c33e0`, `1414c2580`)
   devuelve `(double)(vtable 0x118)()` = el `_size` de la entidad — el "cuánto aporta" (usado para
   HUD/lógica; el aumento efectivo de masa lo manda el servidor).
5. La masa total del jugador se recalcula con `pushMass` (`FUN_140684cd0`): Σ `_size` de las células.

**Respuesta a "cuánto crece la célula depredadora":** en el Haxe actual la célula crece exactamente lo
que el servidor diga (campo `0x1C` / op51); el cliente aplica el delta con el bonus x2 bajo el umbral
`exp2`, actualiza `+0x08`, recalcula Σ `_size` y reescala el mesh con `radio = sqrt(masa)*10+1`.

---

## 6. Comida vs células (entityType) — verificado

- **Wire entityType**: offset `+0x30` de la entidad (`get_entityType` = `FUN_1400f1b80` devuelve
  `*(uint*)(ent+0x30)`). El procesador CLEAR usa vtable `0x158` (= getEntityType) para clasificar:
  - `== 1` → **comida (food)**: reciclaje vía `foodCache` (`DAT_1421c1700`) + grid espacial
    (`param_1+0x2b8`, hash por id).
  - `0x14`/`0x15` (20/21) → jugadores/skin (sin lógica de partícula).
  - otros → células/virus/etc.
- **Clase Haxe**: `FoodEntity` registrada con id **10** (`FUN_14066e370`); strings de constantes
  `"ENTITY_TYPE_FOOD"` @ `141dc7908`, `"ENTITY_BASE_FOOD"` @ `141dc7a48`, y hermanas
  (`ENTITY_TYPE_MASS` @ `141dc78a8`, `ENTITY_TYPE_VIRUS` @ `141dc78c8`, `ENTITY_TYPE_PLAYER` @
  `141dc78e8`, `ENTITY_BASE_PLAYER` @ `141dc7a28`, etc.) — sin xrefs directos: se referencian por
  tabla de códigos (`"ENTITY_CODE_TABLE"` @ `141de2270`/`141de2ce0`).
- **Masa vs comida**: las células tienen `_size` variable (0x90) y radios `sqrt(masa)*10+1`; la comida
  se crea con `_size = 1` y su valor real (cuánto aporta) va en el `applyParticle`.

---

## 7. Constantes de masa/crecimiento (verificadas)

| Constante | Valor | Dónde |
|---|---|---|
| Umbral applyParticle | `(masa * size) / 10 >= 65530 → descartar` | `FUN_140678b80` @ 0x140678b80 (líneas ~19) |
| `VIRUS_MASS_INCREASE_LIMIT` | propiedad estática de VirusEntity → `DAT_1421b8e28` | strings `141dc2918`/`141dc29e8`; get/set `FUN_14064f8c0`/`FUN_14064fa20` |
| `_foodScale` | `config * 0.5` (global `DAT_1421b8e98`) | `FUN_14066e660` @ 0x14066e660 |
| Radio visual | `floor(sqrt(_size)*10+0.5)+1` | `FUN_140677760` @ 0x140677760 |
| Bonus masa | x2 si `exp + delta < exp2` | `FUN_140685400` @ 0x140685400 |
| Masa jugador | Σ cell._size (offset +0x90) en `+0x28`/`+0x08` | `FUN_140684cd0`/`FUN_140685390` |
| Masa AMF3 op51 | `masa = op51 * 25` | `FUN_140945f80` (case 0x33) |
| Escala mundo (visor) | 194165.0 (crudo→mundo) | `mito_view.py` ESCALA |
| Tick de red | 16.666 ms (60 fps) | `FUN_140795df0` @ 0x140795df0 |
| Lerp cámara | 0.32f (`0x47ae147b`) | `FUN_140c08030` en CLEAR |
| Tamaño instancia FoodEntity | 0xF8 bytes | `FUN_14066e390` |
| `_size` inicial comida | 1 | `FUN_14066e490` |

---

## 8. Mapa de direcciones verificado

| Dirección | Rol |
|---|---|
| `0x14066e370` | Registro clase FoodEntity (id 10) |
| `0x14066e390` / `0x14066e490` | new / create(x,z) de FoodEntity (0xF8 bytes, _size=1) |
| `0x1406765a0` | init de entidad comida (x→+0x28, id→+0x2c, meshes) |
| `0x14067a160` | Dispatcher de instancia FoodEntity (applyParticle/removeParticle/get_eatSize/...) |
| `0x140678c80` / `0x140678b80` | applyParticle wrapper / núcleo (umbral 65530, +0x34/+0x38) |
| `0x140678580` / `0x1406784e0` | removeParticle / limpieza (evento 44 equivalente) |
| `0x140676d40` | get_eatSize (vtable 0x118 → _size) |
| `0x140677930` / `0x140677760` | setSize / setSizeInterpolado (radio = sqrt*10+1) |
| `0x140679380` / `0x140678360` | setPosition / aplicar a meshes |
| `0x14066e660` / `0x14066fa50` / `0x14066ebf0` | _foodScale lazy (=config*0.5) / estáticas / resetCache |
| `0x14066f370` / `0x14066f590` | get/set estático FoodEntity |
| `0x140789500` | **Procesador CLEAR de entidades** (campos 0x0C/0x0D/0x13/9/0x1C/0x2C/...) |
| `0x140795df0` / `0x140795600` | Procesador de red principal / wrapper |
| `0x14092ca30` / `0x14092c9d0` | Poll de frames del socket |
| `0x140975250` | Dispatcher de mensajes registrados |
| `0x140945f80` | Frame processor AMF3 (case 0x33 = op51 masa/25) |
| `0x140685400` / `0x140685650` | addExp / masa (bonus x2) |
| `0x140684cd0` / `0x140685390` | pushMass / get_mass (Σ _size) |
| `0x14064f8c0` / `0x14064fa20` | get/set VIRUS_MASS_INCREASE_LIMIT (VirusEntity) |
| `0x1400f1b80` | get_entityType (offset +0x30) |
| `141dc5bf8`…`141dc5cd0` | Strings FoodEntity / _foodScale / foodCache / clase completa |
| `141dc7908` / `141dc7a48` | ENTITY_TYPE_FOOD / ENTITY_BASE_FOOD |
| `141dc2918` / `141dc29e8` | VIRUS_MASS_INCREASE_LIMIT |
| `1421c1700` / `1421b8e98` / `1421c1708` | foodCache (Map) / _foodScale / textureCache (globals) |

---

## 9. Pendientes / notas

- La correspondencia byte-a-byte entre los "campos 0x43/0x62" que ve el visor en frames CLEAR de 2
  campos y los field-codes del binario (0x2B/0x2C/0x2A/0x2E) no está 100% cerrada: el visor parsea
  tripletas `[00 tipo campo valor]` y el binario consulta campos por índice (0x2B=43, 0x2C=44);
  los valores >1e6/194165 siguen siendo la heurística fiable del visor para posiciones.
- El `foodCache` (`DAT_1421c1700`) es un `Map` Haxe (id → FoodEntity) usado para reciclar partículas
  en los frames `64 04` (campo 0x2C).
- No existe un handler "EAT" explícito (evento 3 del Flash) en el Haxe: la eliminación de comida y el
  incremento de masa llegan por separado (removeParticle + campo 0x1C/op51).
