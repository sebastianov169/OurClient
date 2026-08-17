# Entidades, GUI y Mapa — MitosisOG.exe (PC/desktop) vs Android

> Análisis GhidraMCP (xebyte v5.14.2, http://127.0.0.1:8089). Programa: MitosisOG.exe (x86:LE:64, PE, base 0x140000000, 65.150 funciones, sin símbolos).
> Fecha: 2026-08-13. Cruce final con Android (`android_analysis/entidades.md`, libApplicationMain.so ARM64).
> Decompilados de respaldo en `_scratch/d_pc_*.c` (42 archivos). Docs base ya verificados: `aplicacion_posicion_entidades.md`, `renderer_y_camara.md`, `mitosisog-renderer.md`, `ghidra-haxe-mapa-fisica.md`.

---

## 0. Resumen ejecutivo

1. **El layout de entidades del PC es IDÉNTICO al Android** — incluida la masa double en **+0xc0** (la creencia previa de "+0x18" era un artefacto del decompilador: `param_1[0x18]` con `longlong*` = byte offset 0xc0; el disasm muestra `MOVSD qword ptr [RCX + 0xc0]`).
2. **La fábrica de entidades del PC** = `buildEntityFromInfo` @ **FUN_14073b220** (wrapper FUN_14073ea00, name-builder FUN_14073ea40) con **14 entityTypes: 1-9, 11-15** (Android tiene los mismos 13 + PC añade **11 = DiamondEntity**; Android lo fusionaba en 14).
3. **Flujo GUI completo verificado**: CLEAR parser (FUN_14076c400) → cola de eventos → field processor (FUN_140789500) → `setPosition` FUN_140679380 (+0xa8 X, +0xb0 Z, +0xb8 rot mrad; meshes +0x58/+0x60; notify grid vtable[0x168]) + `setMassAndRadius` FUN_140677760 (+0xc0 masa, +0x90 _size, radio = floor(sqrt(m)*10+0.5), vtable[0x1c8](radio+1), vtable[0x140] zOrder) → cámara `FUN_14077c150` (x = stageW/2 − camX·scale).
4. **El clamp del PC es EL MISMO que Android**: `clamp(v, 0, boundaries[i]−1)` en el parser CLEAR (FUN_14076c400, rama interpolada, flag mundo+0x5e8), con `boundaries` = Vector de 4 en **DAT_1421c2a08** ([0]=X máx, [1]=Z máx, [2]/[3]=esquinas min).
5. **Grid espacial**: `fkengine.game.Grid` (vtable 0x141dcc460), `GRID_SIZE` global **DAT_1421b931c** (default 512, runtime 194165), dims `+0x40/+0x44 = worldSize/GRID_SIZE`, celdas `+0xdc/+0xe0` en la entidad, update `FUN_140924ff0` con clamp de CELDA a dims−1 (no de posición).
6. **InterpolationHistory**: clase `fkengine.game.InterpolationHistory` (vtable 0x1421bacf0, instancia 0x38 B, class obj DAT_1421cc460); la instancia vive en **mundo+0x3a0** (pase `applyEntitiesInterpolations` FUN_1407959e0 → `applyPositionInterpolated` FUN_1406790f0). El estado de interpolación por entidad (del CLEAR) está en **mundo+0x5f0** (mapa id→estado, cast hash 0x171822e9). Android lo tenía en this+0x5f0 (mismo slot para el estado CLEAR; el pase de interpolación del PC usa +0x3a0).

---

## 1. Tabla de offsets de entidad — PC vs Android

Fuente PC: disasm `d_pc_disasm_setMassAndRadius.c`, `d_pc_setPosition_FUN_140679380.c`, `d_pc_moveMeshes_FUN_140678360.c`, `d_pc_grid_update_FUN_140924ff0.c`, factory `d_pc_factory_real.c`. Fuente Android: `entidades.md` + `mitosisog-android-arm64-entities.md`.

| Campo | PC (verificado HOY) | Android | Estado |
|---|---|---|---|
| masa double | **+0xc0** (`MOVSD [RCX+0xc0]` en FUN_140677760) | +0xc0 | **IGUAL** (el "+0x18" previo era índice longlong del C: `param_1[0x18]` = 0xc0) |
| masa int (_size) | **+0x90** (`MOVD XMM0,[RCX+0x90]` → `*(int*)(param_1+0x12)` = +0x90) | +0x90 | **IGUAL** |
| id | **+0x2c** (clave del IntMap entitiesById en grid.addEntity FUN_140926460: `*(undefined4*)(ent+0x2c)`) | +0x2c | **IGUAL** |
| entityType | **+0x28** (factory: `(int)plVar12[5]` = +0x28; vtable[0x220] lo devuelve) | +0x28 (param_1 del ctor) | **IGUAL** |
| mesh1 / mesh2 | **+0x58 / +0x60** (factory: `plVar12[0xb]`/`plVar12[0xc]`; setPosition los mueve vía FUN_140678360) | +0x58/+0x60 | **IGUAL** |
| destino X | **+0xa8** (double; `movsd [rcx+0xa8],xmm1` en setPosition) | +0xa8 (Android: NO lo escribe setPosition, solo meshes+notify — pendiente Android) | PC verificado |
| destino Z | **+0xb0** (double) | +0xb0 (ídem) | PC verificado |
| rot destino | **+0xb8** (double, **miliradianes**; setAngle = rot/1000.0 rad) | +0xb8 (mrad) | **IGUAL** (fórmula /1000.0) |
| gridX / gridZ | **+0xdc / +0xe0** (int; grid update FUN_140924ff0) | +0xdc (qword −1 en ctor) | **IGUAL** (8B) |
| radio | no campo: **vtable[0x1c8] = setRadius(radio+1)**; radio = floor(sqrt(masa)*10+0.5) | vtable[0x1c8], mismo +1 | **IGUAL** (fórmula y +1) |
| zOrder | **= _size (masa)**, notify vtable[0x140] (FUN_1406778b0 = setZOrder wrapper → vtable[0x140]) | vtable[0x140] | **IGUAL** |
| flag visible | byte **+0x14** (parser CLEAR: `*(ent+0x14)=1` tras setPosition+setMass) + sprite mesh1+8+0x161 | +0xf0 (tick) | **DIFERENTE** (layout de flags distinto; no hay +0xf0 verificado en PC) |
| tamaño objeto | **0xf8 B** (FoodEntity `__new` FUN_14066e490: `alloc(0xf8)`) | 0xf8 B | **IGUAL** |
| particle id/timer | +0x34/+0x38 (no reverificado hoy; doc previo) | +0x34/+0x38 | igual (doc previo) |

**Vtable de entidad (slots verificados por call-sites HOY):** 0x40 = get_entityType (double), 0xb8 = leer campo del info, 0x140 = setZOrder/notify, 0x150 = applyInfo, 0x168 = notify (grid update), 0x170 = cleanup/init, 0x1b8 = setAngle, 0x1c8 = setRadius, 0x220 = getEntityType (int). GameEntity vtable = **0x1421c1748** (slots [1]=FUN_14067e740 instanceof, [8]=FUN_140676960, [9]=FUN_140676860, [0xb]=FUN_14067c100, [0xc]=FUN_14067d9b0, [0xd]=FUN_14067e250, [0xe]=FUN_14067e2b0). Hash de clase GameEntity = **0xc1e758f** (cast en factory, grid.getEntityById, grid update wrapper).

---

## 2. Fábrica de entidades — `HqJ8Md.buildEntityFromInfo` = FUN_14073b220

Cadena name-builder → wrapper → real:
```
string "buildEntityFromInfo" @ 0x141dcb148
  └─ FUN_14073ea40 (name-builder: FUN_140030210(param_2,"buildEntityFromInfo",param_1,FUN_14073ea00))
       └─ FUN_14073ea00 (wrapper: FUN_14073b220(param_2, param_3))
            └─ FUN_14073b220 (REAL, 356 líneas — d_pc_factory_real.c)
```
El 1.er check: `FUN_1409254d0(grid=mundo+0x308, out, id)` = **grid.getEntityById(id)**; si ya existe → return (no duplicar). Luego lee el entityType del info (reader vtable[0xb8] + unbox vtable[0x40]) y selecciona la clase (objeto `hx::Class` global):

| entityType | Clase PC | hx::Class global | Registro (WRITE) | Android |
|---|---|---|---|---|
| 1 | FoodEntity | DAT_1421c1718 | FUN_14066f800 | 1 = Food ✓ |
| 2 | PlayerEntity | DAT_1421c16f0 | FUN_140669350 | 2 = Player ✓ |
| 3 | FloatingEntity | DAT_1421cc388 | FUN_1414be590 | 3 = Floating ✓ |
| 4 | VirusEntity | DAT_1421c16b0 | FUN_14064fb30 | 4 = Virus ✓ |
| 5 | CoinEntity | DAT_1421cc3a8 | FUN_1414c3cd0 | 5 = Coin ✓ |
| 6 | FlagBaseEntity | DAT_1421cc390 | FUN_1414c08e0 | 6 = FlagBase ✓ |
| 7 | ChestEntity | DAT_1421cc3b0 | FUN_1414c4ee0 | 7 = Chest ✓ |
| 8 | CustomEntity | DAT_1421c1728 | FUN_140673560 | 8 = Custom ✓ |
| 9 | ImageEntity | DAT_1421c16f8 | FUN_14066e0e0 | 9 = Image ✓ |
| 11 | **DiamondEntity** | DAT_1421cc3a0 | FUN_1414c2f40 | (Android: 14 = Diamond/Skinned — **PC los separa: 11=Diamond, 14=Skinned**) |
| 12 | ConquerableEntity | DAT_1421c1730 | FUN_1406762f0 | 12 = Conquerable ✓ |
| 13 | SnakesPlayerEntity | DAT_1421c16d8 | FUN_14065d9a0 | 13 = Snakes ✓ |
| 14 | SkinnedPlayerEntity | DAT_1421c16e8 | FUN_140661400 | 14 = Diamond/Skinned ✓ (mitad) |
| 15 | SpriteEntity | DAT_1421c16c8 | FUN_140659510 | 15 = Sprite ✓ |

Nota: la cadena de ifs lee el type con hints de campo distintos (3 y 0) — la fábrica soporta 2 formatos de info (14/11/5 vía hint 3; el resto vía hint 0). Orden de checks del C: `!=14 → !=11 → !=5 → (hint3) !=5 → 7 → 9 → 8 → 1`, después `13 → 14 → 2 → 4 → 3 → 6 → 12 → 15`.

**Creación**: `FUN_14183d390(out, &claseObj, args)` = `Type.createInstance`: `(**(code **)(*clase + 0x108))(clase, out, args)` — slot 0x108 del objeto de clase = `__new`. Luego `FUN_14067e6e0` = cast a GameEntity (hash 0xc1e758f), después `vtable[0x150]` = **applyInfo** con `FUN_14004fd90(out, info)` (lee info del stream).

**Detalles del resto de la fábrica** (evidencia en d_pc_factory_real.c):
- **FoodCache**: si clase == FoodEntity (check `FUN_140b79010` + `FUN_1400fd950(&clase,&DAT_1421c1718)`) y `*(DAT_1421c1700+0x10) > 0` → `FUN_140028670(DAT_1421c1700, out)` = **FoodCache.get(id)** (DAT_1421c1700 = FoodCache, confirmado por el __get de FoodEntity FUN_14066f370 que devuelve ese global para "FoodCache") → si el cacheado sirve (FUN_1406773d0) → applyInfo y `goto done` (reuso, igual que Android).
- **Meshes al lens**: `local_260 = ent[0xb]` (+0x58) → `FUN_1413204a0(lens=mundo+0x2b8, out, getEntityType())` + `FUN_141320d50(out, &mesh)` = **lens.add(mesh1)**; idem mesh2 (+0x60) si `ent[0xc] != 0`.
- **Player**: si `(int)ent[0x28] != 0` → crea el objeto Player (`FUN_14068a470(...)`, con entityType, flags mundo+0x5c0/+0x651), `FUN_140685870(player, cells)` = setCells, `*(player+0x7c)=1`, add a mundo+0x350, `FUN_1417663a0(mundo+0x358, *(player+0x18), ...)` (players map por id) y a mundo+0x490.
- **Grid add**: `FUN_140926460(grid=mundo+0x308, &ent)` = addEntity: `ent[0x28]` (type) != 0 → también a moveableEntities (+0x18); siempre a entities (+0x10) y a entitiesById (+0x20) con clave `*(ent+0x2c)` = **id**.
- `vtable[0x170]` al final (cleanup/init post-creación).
- Check final `getEntityType() ∈ {1, 0xb, 8, 9, 10}` → mundo+0x2b8 (lens): si `container+0x80` → `FUN_140a229f0(container+8, ent[0xb]+8)` (add mesh sprite a container por tipo). OJO: **entityType 10 existe como valor de getEntityType** en PC (manejo especial de mesh), aunque la fábrica no lo crea.

---

## 3. Flujo completo parser → entidad → mesh → pantalla (verificado)

```
TCP → dispatcher FUN_140977a40 → frame processor FUN_140945f80 (case 0x0A)
  → FUN_14076c400 (parser frame CLEAR 0x64, d_pc_clear_parser.c, 1245 líneas)
       evento 0x01: [u16 campo][u32 A][u32 B][u32 C] BE → d0=(double)(float)A (Z), d1=..B (X), d2=..C (rot)
                    SIN división (crudos) → encola [Z, X, rot]
       evento interpolado (flag mundo+0x5e8==1): estado por entidad en mundo+0x5f0 (mapa id→estado),
                    calcula por frame i: X = dX*i + X0, Z = dZ*i + Z0, rot lerp con wrap ±π (mrad),
                    masa = dm*i + m0 → CLAMP a [0, boundaries-1] → encola [Z, X, rot, masa]
  → update loop 60 fps FUN_140795df0 / FUN_140795600 → FUN_140789500 (field processor, d_pc_parser_fun140789500.c)
       - campo 4  → FUN_14073b220 (buildEntityFromInfo = CREAR entidad)
       - campos pos/masa → FUN_140679380 (setPosition) + FUN_140677760 (setMassAndRadius) + flags
       - `*(ent+0x14)=1` (visible); `*(*(ent[0xb]+8)+0x161)=1` (sprite visible)
       - campo 0x1f (31) → escribe boundaries (DAT_1421c2a08) y FUN_1414e2900 (actualiza muros)
```

### 3.1 setPosition — FUN_140679380 (disasm verificado)
```asm
movsd [rcx+0xb8], xmm3     ; +0xB8 = rot (miliradianes, double completo)
divsd xmm3, [1000.0]       ; rot/1000.0
movsd [rcx+0xa8], xmm1     ; +0xA8 = X (double)
movsd [rcx+0xb0], xmm2     ; +0xB0 = Z (double)
call [rax+0x1b8]           ; vtable[0x1b8] = setAngle(rot/1000.0 rad)
jmp  FUN_140678360         ; tail-call moveMeshes(X, Z)
```
Orden del wire: **[Z, X, rot]** (1.er u32 → +0xb0, 2.º → +0xa8, 3.º → +0xb8).

### 3.2 moveMeshes — FUN_140678360
- `setX(mesh1=ent+0x58, X)` = FUN_1413220b0 → escribe `(float)X` en `(mesh+0x18)+0xc` y `(mesh+0x10)+0xc`; `setZ` = FUN_1413222a0 → `+0x14`. Idem mesh2 (+0x60) si existe.
- Tail-call **vtable[0x168]** = notify = FUN_140678480 → `FUN_140924ff0(grid=mundo+0x308, ent)` = **grid update** (celda = floor(meshX/GRID_SIZE), clamp dims−1, +0xdc/+0xe0, IntMap remove/add).

### 3.3 setMassAndRadius — FUN_140677760 (decompilado + disasm)
```c
if ((double)(int)param_1[0x12] != param_2) {        // _size int (+0x90) != masa nueva
  param_1[0x18] = (longlong)param_2;               // ← +0xC0 = masa double (índice longlong ×8)
  *(int *)(param_1 + 0x12) = (int)param_2;         // +0x90 = _size int
  dVar2 = floor( sqrt((double)iVar1) * 10.0 + 0.5 );  // sqrt = FUN_141bf6990
  (**(code **)(*param_1 + 0x1c8))(param_1, (double)(iVar1 + 1));  // vtable[0x1c8] = setRadius(radio+1)
  (**(code **)(*param_1 + 0x140))(param_1);        // vtable[0x140] = setZOrder (zOrder = _size)
}
```
Disasm: `MOVSD qword ptr [RCX + 0xc0], XMM1` — **+0xc0 confirmado** (corrige los docs previos que decían +0x18).
- `setMassAndRadiusInterpolado` = FUN_1406775f0: `(1-α)*vieja + nueva*α` (α = 2.º arg int).
- `radiusAnimated` = FUN_140678f50.

### 3.4 Interpolación — applyEntitiesInterpolations
- Name-builder FUN_140795dc0 ("applyEntitiesInterpolations") → real **FUN_140795d70** → **FUN_1407959e0(world, entityType)** (d_pc_interp_pass.c):
  - Itera `*(mundo+0x3a0) + 0x18` = lista de entradas del **InterpolationHistory** (instancia en mundo+0x3a0; clase vtable 0x1421bacf0, instancia 0x38 B, class obj DAT_1421cc460, `__new` = FUN_1414ec540).
  - Por entrada: campo[1] = entityId → `FUN_1409254d0(grid, out, id)` (getEntityById); lee X, Z, rot (campos hint 2/4/1/0) → **FUN_1406790f0(ent, X, Z, rot, α=param_2)** = applyPositionInterpolated REAL:
    ```c
    X = (1-α)*destX(+0xa8) + x*α ;  Z = (1-α)*destZ(+0xb0) + z*α
    rot: wrap de la diferencia a [-π, π] (fmod 2π), setAngle vtable[0x1b8]
    tail-call FUN_140678360 (meshes + notify grid)
    ```
  - Si el campo masa != −1.0 → **FUN_1406775f0(ent, masa, α)** (setMassAndRadiusInterpolado).
- Estado de interpolación por entidad (del CLEAR): mundo+0x5f0 = mapa id→estado (get FUN_141766420, cast hash 0x171822e9); layout del estado: +0x8 = Z prev, +0x10 = X prev, +0x18 = rot prev (mrad), +0x20 = flag/threshold (50.0), +0x28 = masa prev; detección de teleport: |Δ| > 0.5*(int)(mundo+0x5f8)*frames. Android: this+0x5f0 (mismo slot).

### 3.5 Mundo → pantalla (cámara, ya verificado — mitosisog-renderer.md)
```c
// FUN_14077c150 (setCameraPosition):
container.x = stageW*0.5 - camX * lensZoom;   // DAT_1421b8d98 = stageW, DAT_1421b8d80 = stageH
container.y = stageH*0.5 - camZ * lensZoom;   // camX = camPos+0xc, camZ = camPos+0x14
// lensZoom = scale*gameScale  (FUN_140780000 setCameraScale: lens+0x50 y mundo+0x38; gameScale = DAT_1421b8d60 = 1.0)
// screen_x = (worldX - camX) * scale + W/2 ;  screen_y = (worldZ - camZ) * scale + H/2
```
- **Zoom V2** (FUN_140795df0 líneas 883-1124): `zoom = min(h*(stageW/stageH)/fov.x, h/fov.z)`; `h = max(100, 2*radio_jugador) + attr[8]`; `newScale = zoom*(stageH/h)*viewportScale/gameScale`; clamp `[zoomParams[1], zoomParams[2]]`; lerp `/10` por frame (current en +0x3f8).
- **Radio visual** = `floor(sqrt(masa)*10+0.5)`; px = radio * scale.
- **Culling**: rect mundo `[camX-(W/scale)/2-10, camZ-(H/scale)/2-10, W/scale+20, H/scale+20]` por frame.
- **zOrder**: sortByZOrder FUN_140a24c70 ascendente por `_size` (pequeños detrás); getter zOrder FUN_1406529a0 devuelve size.

---

## 4. Mapa — Grid, boundaries y mapa físico

### 4.1 Grid (`fkengine.game.Grid`)
- Clase: tabla 0x141dcc460 (name-builder 141dcc480), `__get` FUN_140926620, `__set` FUN_140927a40, `__new` FUN_140928270. Campos registrados: boundaries, worldSize, worldOffet, entities, _entities, _moveableEntities, _entitiesById, _overlapping, _grid, _temp, _segmentW, _segmentH.
- **`Grid.new` = FUN_140924900** (factory): lee args[1] y args[2] → `FUN_140924140(grid, args, worldSize=args[1], cellSize=args[2])`.
- **Ctor FUN_140924140** (d_pc_grid_ctor.c):
  - `+0x8 = worldSize` (int); `+0xc = 0x200` (worldOffset default 512)
  - `+0x10 = entities` (Vector), `+0x18 = moveableEntities`, `+0x20 = entitiesById` (IntMap), `+0x30 = _grid` (IntMap espacial filas→columnas), `+0x38 = temp`, `+0x40/+0x44 = segmentW/segmentH = (int)(worldSize / GRID_SIZE)`
  - `DAT_1421b931c = param_4` (**GRID_SIZE/cellSize global**, default 512, runtime 194165)
  - **boundaries**: `DAT_1421c2a08 = Vector de 4 doubles` = args[0..3] (FUN_140f59610). Con runtime GRID_SIZE=194165 y worldSize=4.077.465.000 (21000×194165) → segmentW=segmentH=21000 → celdas de 1 unidad-mundo; mundo efectivo [0, 20999].
- **get_boundaries** = FUN_140924bb0 (lee DAT_1421c2a08); `get_worldOffet` = FUN_140924bc0 (+0xc).
- **Update espacial FUN_140924ff0** (grid.update(entity), d_pc_grid_update_FUN_140924ff0.c):
  ```
  gx = min( floor((double)(float)meshX / (double)GRID_SIZE), gridW-1 )   // meshX = (ent+0x58 → nodo+0x10)+0xc
  gz = min( floor((double)(float)meshZ / (double)GRID_SIZE), gridH-1 )   // +0x14
  con clamp int32 Haxe [-2147483647.0, 2147483647.0] (0x141f2f508 / 0x141f2f620)
  si ent+0xdc != gx || ent+0xe0 != gz → IntMap remove vieja, ent+0xdc=gx, ent+0xe0=gz, IntMap set nueva
  ```
- **getEntityById** = FUN_1409254d0: `IntMap(+0x20).get(id)` (vtable[0x170] exists + vtable[0x110] get) + cast GameEntity.
- **addEntity** = FUN_140926460: si vtable[0x190] (isMoveable) == 0 → moveableEntities.add; siempre entities.add + entitiesById.set(id=ent+0x2c).

### 4.2 Boundaries (límites del mundo)
- Global **DAT_1421c2a08** = Vector<Float> de 4 (elementos en +8, +0x10, +0x18, +0x20).
- **Se escriben desde el server**: parser FUN_140789500, campo 0x1f (31): lee 4 valores (hints 4,3,2,1) → `+8 = v(hint4)`, `+0x10 = v(hint3)`, `+0x18 = v(hint1)`, `+0x20 = v(hint2)`; luego `FUN_1414e2900(mundo+0x630)` (mundo+0x630 = objeto view con los muros).
- **Clamp de posiciones (PC == Android)**: FUN_14076c400 (CLEAR), rama interpolada (mundo+0x5e8 == 1):
  ```c
  if (0.0 <= vX) { m = *(double*)(DAT_1421c2a08 + 8) - 1.0;   // boundaries[0]-1
                   vX = (vX <= m) ? vX : m; } else vX = 0.0;   // = clamp(vX, 0, boundaries[0]-1)
  // idem vZ con DAT_1421c2a08 + 0x10 (boundaries[1]-1)
  ```
  → `clamp(v, 0, boundaries[i]-1)` **idéntico al Android** (`min(max(v,0),boundaries-1)`).
- La rama NO interpolada (mundo+0x5e8 != 1) NO clampea (usa el estado local_ac8+0x10..0x28 directo).
- Nota: el evento 0x01 simple (posición sin interpolar) tampoco clampea; setPosition no clampea.

### 4.3 Mapa físico (muros/limites de sala)
- **FUN_1414e2900** (d_pc_boundaries_update_FUN_1414e2900.c) = al llegar boundaries, reposiciona **4 objetos marcadores de borde** en la view (mundo+0x630): `+0x288, +0x290, +0x298, +0x2a0` con setters vtable 0x1b0/0x1c0/0x1c8/0x1d0:
  - `dVar8 = camX + boundaries[2]` (esquina min X), `dVar4 = camX + boundaries[3]` (esquina min Z),
  - `dVar7 = boundaries[1] − 2·camX` (max Z), `dVar5 = boundaries[0] − 2·camX` (max X)
  → boundaries = [X máx, Z máx, X mín, Z mín]; 4 líneas/esquinas dibujan la sala. Con mín = 0 y máx = 21000×194165 crudos.
- **Sala/mundo**: no hay string "room"/"sala" relevante en el binario; el mundo es un cuadrado definido por boundaries (mundo 21000×21000 unidades → 4.077.465.000 crudos). No hay obstáculos físicos en el cliente (el "mapa físico" = límites de sala + grid espacial; la física de movimiento es extrapolación por markers, ver ghidra-haxe-fisica-movimiento.md).

---

## 5. Evidencia (decompilados abreviados)

### setMassAndRadius FUN_140677760 (decomp + disasm clave)
```c
if ((double)(int)param_1[0x12] != param_2) {   // +0x90 = _size
  param_1[0x18] = (longlong)param_2;           // +0xC0 = masa double (índice longlong ×8)
  *(int *)(param_1 + 0x12) = (int)param_2;     // +0x90
  dVar2 = floor(FUN_141bf6990((double)iVar1) * 10.0 + 0.5);
  (**(code **)(*param_1 + 0x1c8))(param_1,(double)(iVar1 + 1));  // setRadius(radio+1)
  (**(code **)(*param_1 + 0x140))(param_1);                       // setZOrder
}
```
```asm
140677766: MOVD XMM0,dword ptr [RCX + 0x90]      ; _size int
140677792: MOVSD qword ptr [RCX + 0xc0],XMM1     ; masa double → +0xC0
```

### buildEntityFromInfo FUN_14073b220 (fragmentos)
```c
plVar7 = reader(vtable[0xb8], campo 2);  uVar3 = unbox int;
FUN_1409254d0(grid(mundo+0x308), &out, uVar3);   // getEntityById; si existe → return
dVar14 = get_entityType(vtable[0x40]);
if (type != 14.0) { if (type != 11.0) { if (type != 5.0) { ... uVar10 = clase... } } }
// checks finales: 13→DAT_1421c16d8 (Snakes), 14→DAT_1421c16e8 (Skinned), 2→c16f0 (Player),
//                 4→c16b0 (Virus), 3→cc388 (Floating), 6→cc390 (FlagBase), 12→c1730 (Conquerable), 15→c16c8 (Sprite)
local_270 = uVar10;                                  // clase seleccionada
... FUN_14183d390(out, &clase, args)                 // Type.createInstance: clase[0x108] = __new
plVar12 = cast GameEntity (FUN_14067e6e0, hash 0xc1e758f)
vtable[0x150](ent, FUN_14004fd90(out, info))         // applyInfo
local_260 = ent[0xb];                                // mesh1 +0x58
FUN_1413204a0(lens=mundo+0x2b8, out, getEntityType()); FUN_141320d50(out, &mesh1);  // lens.add(mesh1)
if (ent[0xc]) { ... lens.add(mesh2) }                // mesh2 +0x60
if ((int)ent[0x28] != 0) { ... crear Player (FUN_14068a470), setCells, add a mundo+0x350/+0x358/+0x490 ... }
vtable[0x170](ent);
FUN_140926460(grid, &ent);                           // grid.addEntity (id = ent+0x2c)
```

### setPosition FUN_140679380 (decomp)
```c
param_1[0x17] = (longlong)param_4;   // +0xB8 = rot mrad
param_1[0x15] = param_2;             // +0xA8 = X
param_1[0x16] = param_3;             // +0xB0 = Z
vtable[0x1b8](param_1, rot/1000.0);  // setAngle
FUN_140678360(param_1, X, Z);        // moveMeshes → vtable[0x168] notify → grid update
```

### Clamp del CLEAR FUN_14076c400 (líneas 887-907)
```c
dVar20 = dVar2 * dVar22 + local_ab0;        // X interpolada
if (0.0 <= dVar20) {
  local_8a0 = *(double *)(DAT_1421c2a08 + 8) - 1.0;   // boundaries[0]-1
  if (dVar20 <= local_8a0) local_8a0 = dVar20;         // min(v, max)
} else local_8a0 = 0.0;                                // max(v, 0)
// idem dVar22 (Z) con DAT_1421c2a08 + 0x10 → boundaries[1]-1
// → empaqueta [Z, X, rot, masa] y encola
```

### Grid ctor FUN_140924140 (fragmentos)
```c
*(longlong *)(param_1 + 0x10) = entities;     *(longlong *)(param_1 + 0x18) = moveableEntities;
*(longlong *)(param_1 + 0x20) = entitiesById; *(longlong *)(param_1 + 0x30) = _grid;
*(int *)(param_1 + 8) = param_3;              // worldSize
*(undefined4 *)(param_1 + 0xc) = 0x200;       // worldOffset default
DAT_1421b931c = param_4;                      // GRID_SIZE/cellSize
DAT_1421c2a08 = Vector4(args[0..3]);          // boundaries
*(int *)(param_1 + 0x40) = (int)(worldSize / GRID_SIZE);   // segmentW
*(int *)(param_1 + 0x44) = (int)(worldSize / GRID_SIZE);   // segmentH
```

### applyEntitiesInterpolations FUN_1407959e0 (fragmento)
```c
plVar8 = *(mundo + 0x3a0) + 0x18;            // InterpolationHistory.entradas
for (i = 0; i < entradas.length; i++) {
  entrada = ...;  id = campo[1];
  if (FUN_1409254d0(mundo+0x308, &ent, id)) {       // grid.getEntityById
    x = campo(hint2→hint4); z = campo(hint2→hint1); rot = campo(hint2→hint0);
    FUN_1406790f0(ent, x, z, rot, alpha);           // applyPositionInterpolated
    if (campo(hint2→hint2) != -1.0) FUN_1406775f0(ent, masa, alpha);  // setMassAndRadiusInterpolado
  }
}
```

---

## 6. Referencias rápidas

| Rol | Dirección |
|---|---|
| setMassAndRadius (masa +0xc0, _size +0x90, radio, zOrder) | FUN_140677760 |
| setMassAndRadiusInterpolado | FUN_1406775f0 |
| setPosition (+0xa8/+0xb0/+0xb8, setAngle, meshes) | FUN_140679380 |
| moveMeshes (setX/setZ en +0x58/+0x60 → notify 0x168) | FUN_140678360 |
| applyPositionInterpolated (lerp + wrap rot) | FUN_1406790f0 (wrapper FUN_140679290) |
| setX / setZ (nodos mesh, float +0xc/+0x14) | FUN_1413220b0 / FUN_1413222a0 |
| notify → grid update | FUN_140678480 (vtable[0x168]) |
| grid.update (celda, +0xdc/+0xe0, clamp dims−1) | FUN_140924ff0 |
| grid.getEntityById | FUN_1409254d0 |
| grid.addEntity (id = ent+0x2c) | FUN_140926460 |
| Grid.new / Grid ctor | FUN_140924900 / FUN_140924140 |
| get_boundaries | FUN_140924bb0 |
| **buildEntityFromInfo (fábrica)** | FUN_14073b220 (name-builder FUN_14073ea40) |
| Type.createInstance (clase[0x108]=__new) | FUN_14183d390 |
| applyEntitiesInterpolations (pase 60fps) | FUN_140795d70 → FUN_1407959e0 |
| InterpolationHistory __new (0x38 B) / class obj | FUN_1414ec540 / DAT_1421cc460 |
| parser CLEAR 0x64 (clamp, eventos) | FUN_14076c400 |
| field processor (setPosition/setMass/factory/boundaries) | FUN_140789500 |
| update loop 60 fps (cámara+zoom+FP) | FUN_140795df0 |
| setCameraScale / setCameraPosition | FUN_140780000 / FUN_14077c150 |
| boundaries global (Vector 4 doubles) | DAT_1421c2a08 |
| GRID_SIZE global (runtime 194165, default 512) | DAT_1421b931c |
| GameEntity vtable | 0x1421c1748 (hash clase 0xc1e758f) |
| FoodCache / _foodScale | DAT_1421c1700 / DAT_1421b8e98 |
| mundo singleton (grid en +0x308, lens +0x2b8, InterpHist +0x3a0, estado interp +0x5f0, view +0x630) | DAT_1421c17a8 |
| clamp int32 Haxe (±2147483647.0) / 1000.0 / 2π | 0x141f2f508 / 0x141f2f620 / 0x141f2f3f8 / 0x141f2f450 |

## 7. Pendientes / notas
- entityType 10: getEntityType puede devolverlo (manejo especial de mesh en lens container +0x80); la fábrica no crea tipo 10. Android no lo lista — verificar si existe en el Android.
- Android: verificar si `setPosition` escribe +0xa8/+0xb0/+0xb8 (en Android la tabla quedó "pendiente de cerrar"; en PC SÍ se escriben).
- Los flags +0x14 (entidad) y +0x161 (sprite) del PC no tienen equivalente confirmado en Android (+0xf0 allá).
- El valor runtime de GRID_SIZE (194165) y de boundaries (21000×194165) está calibrado en vivo (docs `aplicacion_posicion_entidades.md` / visor Python), no es constante en el binario.
