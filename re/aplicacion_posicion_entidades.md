# Aplicación de posiciones a entidades en MitosisOG.exe (cliente Haxe)

> Documento de ingeniería inversa generado con Ghidra (base `0x140000000`) + capstone (disassembly directo del binario `MitosisOG.exe`, 36.5 MB, secciones `.text/.rdata/.data`) el 2026-08-13.
> Complementa `protocolo_haxe_clear.md`, `protocolo_haxe_fisica_movimiento.md` y `protocolo_haxe_mapa_fisica.md`.
> Visor de validación en vivo: `mito_view.py` (ESCALA = 194165.0, mundo 0–21000).

---

## 0. Resumen ejecutivo (hallazgos clave)

1. **La constante 194165 NO existe en el binario.** Escaneo completo del archivo (int32, float32, float64, recíproco float64/float32, ASCII): **0 hits**. `194165` es un valor **RUNTIME**: es el campo estático Haxe `fkengine.game.Grid.GRID_SIZE`, almacenado en el global mutable **`DAT_1421b931c`** (en `.data`, no alineado a constante). Default en el inicializador estático = `0x200` (512). Se sobrescribe en tiempo de ejecución (config del servidor vía `Reflect.setField` / constructor de `Grid`). El valor calibrado en vivo es 194165 (crudo/194165 = unidad de mundo, coincidente con la pantalla).
   - ⚠️ El `0x40f7b2a000000000` del contexto **NO es** 194165.0 (eso vale ≈569 953). El patrón real de 194165.0 como double es `0x4107B3A800000000` y como float `0x483D9D40` — y **ninguno aparece** en el binario.
2. **El cliente NUNCA divide las coordenadas crudas del CLEAR.** El evento de posición `0x01` del frame CLEAR (`FUN_14076c400`) lee `3× u32 BE` y los convierte a `(double)(float)raw` — **sin ninguna división** — y los encola tal cual. El mundo interno del cliente opera **en unidades crudas** (0 … ~4.08e9). El "crudo/194165 = mundo" existe solo en:
   - el **grid espacial** (`floor(coord / GRID_SIZE)` con GRID_SIZE=194165 → celda = 1 unidad-mundo), y
   - el **visor Python** (ESCALA = 194165.0, calibración de pantalla).
3. **Orden del wire del CLEAR 0x01 = `[Z, X, rot]`**: el 1.er i32 va a `+0xB0` (Z), el 2.º a `+0xA8` (X), el 3.º a `+0xB8` (rotación en miliradianes). (El visor Python asigna 1.er valor → x y 2.º → z, es decir, los tiene intercambiados respecto al binario.)
4. `setPosition` = `FUN_140679380`: escribe `+0xA8 = X (double)`, `+0xB0 = Z (double)`, `+0xB8 = rot (double)`; llama `vtable[0x1b8](rot/1000.0)` (setAngle); tail-call `FUN_140678360` (mueve meshes `+0x58`/`+0x60`) → `vtable[0x168]` (notify = `FUN_140678480` → actualización del grid).
5. **Grid espacial** `FUN_140924ff0`: `gridX = floor(x_mesh / GRID_SIZE)`, `gridZ = floor(z_mesh / GRID_SIZE)`; clamp int32 a [−2147483647, 2147483647] (Std.int de Haxe) y clamp superior a `dims−1`; si cambió respecto a `+0xdc`/`+0xe0` → remove de la celda vieja, escribir `+0xdc`/`+0xe0`, add a la celda nueva.
6. **Clamp a límites del mundo**: el "21000" tampoco es constante en el binario (0 hits como constante real; los hits de "21000" son displacements de instrucciones). El límite efectivo lo define el grid: `dims(+0x40/+0x44) = (int)(worldSize / GRID_SIZE)`, y la celda se clamp a `dims−1`. Con GRID_SIZE=194165 y worldSize=4 077 465 000 (21000×194165, cabe en u32) → dims = 21000 → coordenada de mundo ∈ [0, 20999].
7. **X vs Z**: en la entidad `+0xA8 = X`, `+0xB0 = Z` (destino); el mesh guarda la posición visual como floats: nodo `+0x10`/`+0x18` del mesh, `+0xc = X`, `+0x14 = Z`; `+0xdc = gridX`, `+0xe0 = gridZ`; `+0xb8 = rot (mrad)`. En pantalla (2D top-down) la cámara proyecta (X, Z) del mundo; el visor dibuja (x, z) → (pantalla_x, pantalla_y).

---

## 1. La división/transformación exacta de coordenadas (caza de 194165)

### 1.1 Búsqueda exhaustiva en el binario (verificado)

| Patrón buscado | Codificación | Resultado |
|---|---|---|
| 194165.0 double | `00 00 00 00 A8 B3 07 41` (LE) | **0 hits** |
| 194165.0 float | `40 9D 3D 48` | **0 hits** |
| 194165 int32 | `75 F6 02 00` | **0 hits** |
| 1/194165 (5.150258800504725e-06) double | `0x3ED59A0C5BFB4240` | **0 hits** |
| 1/194165 float | `0x36ACD063` | **0 hits** |
| ASCII "194165" | — | **0 hits** |
| 21000.0 double / float | `0x40D4880000000000` / `0x46A41000` | **0 hits** |
| 21000 int32 | `08 52 00 00` | 5 hits = **todos falsos positivos** (displacements `[rbp+0x5208]` etc.) |

**Conclusión**: no existe una división por constante en el binario. El divisor es el global mutable `DAT_1421b931c`.

### 1.2 `DAT_1421b931c` = `fkengine.game.Grid.GRID_SIZE` (campo estático Haxe)

Escrituras (xrefs verificados):
- `FUN_140928750` (inicializador estático de la clase): `DAT_1421b931c = 0x200;` → **default 512**.
- `FUN_140924140` (constructor del Grid): `DAT_1421b931c = param_4;` (el 3.er argumento de `Grid.new`).
- `FUN_140928100` (`Reflect.setField`, campo `"GRID_SIZE"` — string decodificado de los bytes `0x5A49535F44495247`="GRID_SIZ" + `0x45`='E'): `DAT_1421b931c = valor;`.

Lecturas (xrefs verificados): `FUN_140924ff0` (update del grid), `FUN_140924140`, `FUN_140927970` (`Reflect.getField("GRID_SIZE")`).

Registro de la clase (`FUN_1409284f0`): `DAT_1421b9328 = fkengine::game::Grid_obj::vftable;` y objeto `hx::Class` con nombre `"fkengine.game.Grid"` (len 0x12), slots `[8]=FUN_140924900` (ctor), `[0xb]=FUN_140927970` (getField), `[0xc]=FUN_140928100` (setField).

**Valor runtime calibrado = 194165** (evidencia en vivo: el visor valida que `crudo/194165` reproduce las posiciones en pantalla y el mundo llega a ~21000; el grid funciona con celdas de 1 unidad-mundo).

### 1.3 El evento de posición del CLEAR NO divide (verificado)

`FUN_14076c400` (parser del frame CLEAR 0x64), evento `local_ae8[0] == 1` (tipo 0x01, líneas 489–497 del decompilado):

```c
if (local_ae8[0] == 1) {                                  // evento 0x01 = POSICIÓN ENTIDAD
  local_res20[0] = FUN_140406320(*param_2);               // readUInt16 BE -> field code
  local_res18[0] = (float)FUN_140406050(*param_2);        // readUInt32 BE -> (float)raw   <- SIN DIVISIÓN
  local_ab8 = (double)local_res18[0];                     // d0 = (double)(float)rawZ      (1.er valor wire -> Z)
  local_res18[0] = (float)FUN_140406050(*param_2);        // 2.º u32
  local_ab0 = (double)local_res18[0];                     // d1 = (double)(float)rawX      (2.º valor wire -> X)
  local_res18[0] = (float)FUN_140406050(*param_2);        // 3.er u32
  local_970 = (double)local_res18[0];                     // d2 = (double)(float)rawRot    (3.er valor wire -> rot)
  // empaqueta [d0, d1, d2] en un array de doubles:
  //   arr[0]=local_ab8 (Z), arr[1]=local_ab0 (X), arr[2]=local_970 (rot)
  ...
  FUN_140225b00(local_ae0, ...);                          // encola el evento en el mundo
}
```

- `FUN_140406050` = **readUInt32 BE** (decompilado verificado: devuelve `uint`; si el flag allocator del reader `+0x20` == 1.0 hace byte-swap `(u4<<8|u3)<<8|u2<<8|u1`, i.e. little-endian). Por eso los crudos llegan hasta ~4.08e9 (u32).
- `FUN_140225b00(world, arr)` = dispatcher de eventos: `switch(*(world+0x10))` + `(**(code **)(**(longlong **)(world + 0x18) + 0x158))(world+0x18, &arr)` → encola `[Z, X, rot]` (crudos como doubles).
- El field processor `FUN_140789500` (llamado desde el update loop 60 fps `FUN_140795df0` / `FUN_140795600`) lee esos valores y llama `setPosition` directamente.

### 1.4 Fórmula exacta

```
coord_mundo  = raw / 194165        (SOLO en el visor Python, ESCALA=194165.0)
celda_grid   = floor(raw / GRID_SIZE)   donde GRID_SIZE = DAT_1421b931c (runtime = 194165)
                                        y raw = float32 del nodo del mesh (posición visual)
```

En el binario la única operación de "escala" es la división del grid. El resto del juego (física, interpolación, extrapolación) opera con crudos.

---

## 2. `setPosition` — FUN_140679380 (offset 0x679380)

### 2.1 Decompilado Ghidra (verificado)

```c
void FUN_140679380(longlong *param_1, longlong param_2, longlong param_3, double param_4)
{
  param_1[0x17] = (longlong)param_4;      // +0xB8 = rot (miliradianes, truncado en el C; en asm es double completo)
  param_1[0x15] = param_2;                // +0xA8 = X
  param_1[0x16] = param_3;                // +0xB0 = Z
  (**(code **)(*param_1 + 0x1b8))(param_1, SUB84(param_4 / 1000.0,0));  // vtable[0x1b8] = setAngle(rot/1000.0)
  FUN_140678360(param_1,(int)param_2,(int)param_3);                    // tail-call: mueve meshes (X, Z)
  return;
}
```

### 2.2 Disassembly exacto (verificado con capstone) — lo que REALMENTE hace

```asm
FUN_140679380:                 ; setPosition(this=rcx, X=xmm1, Z=xmm2, rot=xmm3)
  mov  rax, [rcx]              ; vtable
  movsd [rcx+0xb8], xmm3       ; +0xB8 = rot (DOUBLE completo, no truncado)
  divsd xmm3, [rip+0x18b605c]  ; rot / 1000.0   (constante = 0x141f2f3f8 = 1000.0)
  movsd [rcx+0xa8], xmm1       ; +0xA8 = X (DOUBLE)
  movsd [rcx+0xb0], xmm2       ; +0xB0 = Z (DOUBLE)
  movaps xmm1, xmm3            ; arg = rot/1000.0
  call [rax+0x1b8]             ; vtable[0x1b8](this, rot/1000.0)  -> setAngle (radianes)
  movaps xmm2, xmm6            ; Z
  movaps xmm1, xmm7            ; X
  mov  rcx, rbx                ; this
  jmp  0x140678360             ; tail-call FUN_140678360(this, X, Z)  (moveMeshes)
```

**Offsets escritos y orden:**
| Offset | Campo | Valor |
|---|---|---|
| `+0xA8` | X destino (double) | param_2 (xmm1) |
| `+0xB0` | Z destino (double) | param_3 (xmm2) |
| `+0xB8` | rot destino (double, miliradianes) | param_4 (xmm3) |
| vtable `0x1b8` | setAngle | `rot/1000.0` (radianes) |
| meshes `+0x58`/`+0x60` | posición visual | vía FUN_140678360 |

### 2.3 FUN_140678360 — mueve los meshes (offsets y orden exactos)

```asm
FUN_140678360:                 ; moveMeshes(this=rcx, X=xmm1, Z=xmm2)
  mov  rcx, [rcx+0x58]         ; mesh1 = this+0x58
  call 0x1413220b0             ; setX(mesh1, X)     -> escribe (float)X en (mesh+0x18)+0xc y (mesh+0x10)+0xc
  mov  rcx, [rbx+0x58]
  movaps xmm1, xmm6            ; Z
  call 0x1413222a0             ; setZ(mesh1, Z)     -> escribe (float)Z en (mesh+0x18)+0x14 y (mesh+0x10)+0x14
  mov  rcx, [rbx+0x60]         ; mesh2 = this+0x60
  test rcx, rcx
  je  skip
  movaps xmm1, xmm7            ; X
  call 0x1413220b0             ; setX(mesh2, X)
  mov  rcx, [rbx+0x60]
  movaps xmm1, xmm6            ; Z
  call 0x1413222a0             ; setZ(mesh2, Z)
skip:
  jmp [rax+0x168]              ; tail-call vtable[0x168] = notify = FUN_140678480 -> update del grid
```

- `FUN_1413220b0(mesh, x)` = **setX**: `*(float*)(*(mesh+0x18)+0xc) = (float)x; *(float*)(*(mesh+0x10)+0xc) = (float)x;` + actualiza sprite (`mesh+8`, vtable 0x1c8/0x1d0) y children (`mesh+0x78`).
- `FUN_1413222a0(mesh, z)` = **setZ**: mismo pero escribe en `+0x14`.
- Nodos del mesh: `mesh+0x10` y `mesh+0x18` (transform nodes); **`+0xc` = X (float), `+0x14` = Z (float)**.
- `vtable[0x168]` = `FUN_140678480` (notify):

```c
void FUN_140678480(undefined8 param_1) {
  FUN_140924ff0(*(undefined8 *)(DAT_1421c17a8 + 0x308), local_res8);  // grid = world(singleton)+0x308
}
```
→ **cada movimiento de mesh dispara el update del grid espacial.**

### 2.4 Cómo llama el field processor (CLEAR) a setPosition

`FUN_140789500` (FP), sitio de llamada 1 (disasm en `0x14078c342`–`0x14078c3a9`):

```asm
; lee 3 valores de la entidad (vtable[0xb8] = reader de campos; FUN_1400347c0 = unbox vtable[+0x40])
call [rax+0xb8]          ; read A (hint 4)  -> unbox -> xmm7
call [rax+0xb8]          ; read B (hint 1)  -> unbox -> xmm6
call [rax+0xb8]          ; read C (hint 0)  -> unbox -> xmm1
movaps xmm3, xmm7        ; param_3 (Z)  = A  = 1.er valor del wire
movaps xmm2, xmm6        ; param_2 (X)  = B  = 2.º valor del wire
mov  rcx, r14            ; entidad
call 0x140679380         ; setPosition(entidad, X=B, Z=A, rot=C)
```

Sitio de llamada 2 (`0x14078c813`): idéntico (param_3 = XMM10 = valor A leído antes; param_2 = read hint 1; param_4 = read hint 0).

**Conclusión X/Z del wire:** evento CLEAR 0x01 = `[u16 campo][i32 A][i32 B][i32 C]` → `+0xB0 (Z) = A`, `+0xA8 (X) = B`, `+0xB8 (rot) = C`. **El servidor manda Z primero.**

---

## 3. Actualización del grid espacial — FUN_140924ff0 / FUN_140925450

### 3.1 Wrapper Haxe

```c
undefined8 * FUN_140925450(undefined8 *param_1, undefined8 param_2, longlong *param_3) {
  // type-check del parámetro (hash 0xc1e758f) vía FUN_140052590
  FUN_140924ff0(param_2, local_res18);   // grid.update(entidad)
  *param_1 = 0;
  return param_1;
}
```

### 3.2 Update del grid (decompilado + disassembly verificado)

`FUN_140924ff0(grid, entity)`, parte clave del disasm (`0x140925044`–`0x140925275`):

```asm
movd  xmm8, dword ptr [0x1421b931c]   ; divisor = *(int*)GRID_SIZE  (runtime = 194165)
cvtdq2pd xmm8, xmm8                   ; (double)GRID_SIZE
mov  rdi, [rax+0x10]                  ; rdi = mesh(+0x58)->nodo(+0x10)
movss xmm0, dword ptr [rdi+0xc]       ; x = (float)nodo.X
cvtps2pd xmm0, xmm0
divsd xmm0, xmm8                      ; x / GRID_SIZE
call 0x141bf68e0                      ; floor()   -> gx
movsd xmm7, qword ptr [0x141f2f620]   ; lo = -2147483647.0
movsd xmm6, qword ptr [0x141f2f508]   ; hi =  2147483647.0
; clamp int32 de Haxe (Std.int): si lo<=v<=hi -> cvttsd2si ecx (32b) ; si no -> cvttsd2si rcx (64b)
mov  eax, dword ptr [r13+0x40]        ; gridW = grid+0x40
dec  eax                              ; gridW-1
; min(gx, gridW-1): if ((double)(gridW-1) <= (double)gx && !isnan) gx = gridW-1
; --- igual para Z ---
movss xmm0, dword ptr [rdi+0x14]      ; z = (float)nodo.Z
... divsd por GRID_SIZE, floor, clamp int32 ...
mov  eax, dword ptr [r13+0x44]        ; gridH = grid+0x44 ; min(gz, gridH-1)
mov  eax, dword ptr [rbx+0xdc]        ; oldGridX = entity+0xdc
cmp  eax, r15d                        ; ¿cambió gridX?
jnz  update
cmp  dword ptr [rbx+0xe0], esi        ; ¿cambió gridZ (entity+0xe0)?
jz   done                             ; sin cambios -> fin
update:
  ; remove de la celda vieja: IntMap(grid+0x30)[gridZ] -> IntMap[gridX] -> remove(entity)
  ... FUN_140028530 (IntMap.remove) ...
  mov  rax, [r12]
  mov  dword ptr [rax+0xdc], r15d     ; entity+0xdc = nuevo gridX
  mov  rax, [r12]
  mov  dword ptr [rax+0xe0], esi      ; entity+0xe0 = nuevo gridZ
  ; add a la celda nueva: IntMap(grid+0x30)[gridZ] -> IntMap[gridX] -> set(entity)
  ... FUN_1400286d0 (IntMap.set) ...
done:
```

**Fórmulas exactas:**
```
gx = min( floor( (double)(float)meshX / (double)GRID_SIZE ), gridW-1 )   ; gridW = *(grid+0x40)
gz = min( floor( (double)(float)meshZ / (double)GRID_SIZE ), gridH-1 )   ; gridH = *(grid+0x44)
si (entity+0xdc != gx) || (entity+0xe0 != gz):
    IntMap(grid+0x30)[entity+0xe0][entity+0xdc].remove(entity)
    entity+0xdc = gx ; entity+0xe0 = gz
    IntMap(grid+0x30)[gz][gx].set(entity)
```

**Estructura del grid** (objeto `fkengine.game.Grid`):
| Offset | Campo |
|---|---|
| `+0x30` | IntMap de filas (clave = gridZ) → cada fila es un IntMap (clave = gridX) → lista de entidades |
| `+0x40` | gridW (columnas) |
| `+0x44` | gridH (filas) |

Constantes de clamp int32: `0x141f2f508` = `2147483647.0` (0x41DFFFFFFC00000), `0x141f2f620` = `-2147483647.0` (0xC1DFFFFFFC00000) — ambas verificadas leyendo el .rdata.

### 3.3 Construcción del grid — `Grid.new` (FUN_140924900 → FUN_140924140)

```c
// FUN_140924900 (ctor de fkengine.game.Grid, vtable = fkengine::game::Grid_obj::vftable):
//   args = array de Haxe [..., worldSize, gridSize]
//   uVar3 = args[1].toInt()   -> param_3
//   puVar7 = args[2].toInt()  -> param_4  -> DAT_1421b931c (GRID_SIZE global)
//   FUN_140924140(grid, args, uVar3, puVar7);

// FUN_140924140 (inicialización del grid):
*(int *)(param_1 + 0x40) = (int)((double)param_3 / (double)DAT_1421b931c);  // gridW  = worldSize/GRID_SIZE
*(int *)(param_1 + 0x44) = (int)((double)param_3 / (double)DAT_1421b931c);  // gridH  = worldSize/GRID_SIZE
```

Con GRID_SIZE = 194165 (runtime) y worldSize = 4 077 465 000 (21000×194165, cabe en u32; el readInt32 del CLEAR es uint) → `gridW = gridH = 21000` → celdas de 1 unidad-mundo y límite efectivo del mundo en 20999.

---

## 4. Clamp a límites del mundo (21000 / worldSize)

- **No hay constante 21000 en el binario** (verificado: 0 hits como constante; los hits de `08 52 00 00` son displacements de `[rbp+0x5208]`).
- El límite del mundo es **runtime**: `worldSize` llega por config y entra en `Grid.new`; el grid lo convierte en `dims = worldSize/GRID_SIZE`.
- Clamp efectivo en el update del grid: `gx = min(floor(rawX/GRID_SIZE), gridW-1)`, `gz = min(floor(rawZ/GRID_SIZE), gridH-1)`.
- Clamp adicional de conversión a int (Std.int de Haxe): si el resultado de `floor` está fuera de `[-2147483647.0, 2147483647.0]` se convierte vía int64 (comportamiento de overflow de Haxe, `0x141f2f620`/`0x141f2f508`).
- No hay clamp de posición en `setPosition` ni en el CLEAR: las coordenadas crudas se aceptan tal cual; el mundo visual se limita por el grid (y el servidor nunca manda fuera de rango).

---

## 5. X vs Z (mundo vs pantalla)

| Concepto | Offset / campo | Detalle |
|---|---|---|
| X destino (entidad) | `+0xA8` (double) | 2.º valor i32 del evento CLEAR 0x01 |
| Z destino (entidad) | `+0xB0` (double) | 1.er valor i32 del evento CLEAR 0x01 |
| rot destino | `+0xB8` (double) | 3.er valor i32, **miliradianes** (0..~6283; setAngle = rot/1000 rad) |
| X visual (mesh) | `(mesh+0x10)+0xc` / `(mesh+0x18)+0xc` (float) | escrita por setX `FUN_1413220b0` |
| Z visual (mesh) | `(mesh+0x10)+0x14` / `(mesh+0x18)+0x14` (float) | escrita por setZ `FUN_1413222a0` |
| gridX | `+0xdc` (int) | = floor(X_mesh/GRID_SIZE), clave interna del IntMap de columnas |
| gridZ | `+0xe0` (int) | = floor(Z_mesh/GRID_SIZE), clave externa del IntMap de filas |
| mesh 1 / mesh 2 | `+0x58` / `+0x60` | objeto visual (sprite + nodos de transform) |

- En el **wire** el orden es `[Z, X, rot]` (Z primero).
- En **pantalla** (juego 2D top-down): la cámara proyecta (X, Z) del mundo → (screen_x, screen_y); el visor Python (`haxe_clear_parser.py`/`mito_view.py`) lee 1.er valor → `x` y 2.º → `z`, por lo que **su X/Z quedan intercambiados respecto al binario** (no afecta al dibujado, pero sí a cualquier comparación con offsets).
- En el mapa del Flash viejo (`Instance.as`), `applyPosition(x, z, rot/1000)` — mismo trío, rot en miliradianes.

---

## 6. Pipeline completo de aplicación de posición (verificado)

```
TCP -> dispatcher (FUN_140977a40) -> frame processor FUN_140945f80 (case 0x0A)
   -> FUN_14076c400 (parser de eventos CLEAR 0x64)
        evento 0x01: [u16 campo][u32 A][u32 B][u32 C]  (BE, uint)
        d0=(double)(float)A ; d1=(double)(float)B ; d2=(double)(float)C    // SIN división
        -> FUN_140225b00 -> cola del mundo  [Z=d0, X=d1, rot=d2]
   -> update loop 60 fps: FUN_140795df0 / FUN_140795600 -> FUN_140789500 (field processor)
        lee campos de la entidad (vtable[0xb8]) -> FUN_140679380 (setPosition)
   -> +0xA8=X, +0xB0=Z, +0xB8=rot ; vtable[0x1b8](rot/1000) ; FUN_140678360 (meshes)
   -> meshes +0x58/+0x60: setX(+0xc float), setZ(+0x14 float)
   -> vtable[0x168] notify = FUN_140678480 -> FUN_140924ff0 (grid update)
        gridX=floor(X/GRID_SIZE), gridZ=floor(Z/GRID_SIZE), clamp dims-1, +0xdc/+0xe0, IntMap remove/add
```

---

## 7. Complemento: interpolación y extrapolación

### 7.1 `applyPositionInterpolated` — FUN_140679290 (wrapper) → FUN_1406790f0 (real)

```c
void FUN_1406790f0(longlong *param_1, double x, double z, double rot, double alpha)
{
  dVar1 = (double)param_1[0x16];                    // +0xB0 = Z destino
  dVar2 = (double)param_1[0x15];                    // +0xA8 = X destino
  dVar3 = wrap2pi( (double)param_1[0x17] / 1000.0 );  // rot destino en radianes (wrap mod 2π)
  dVar4 = wrap2pi( rot / 1000.0 );                  // rot nueva en radianes
  // wrap de la diferencia a [-π, π]
  ...
  dVar3 = wrap2pi( (dVar4 - dVar3) * alpha + dVar3 );
  (**(code **)(*param_1 + 0x1b8))(param_1, dVar3);  // vtable[0x1b8] = setAngle
  FUN_140678360(param_1,
                (1.0 - alpha) * dVar2 + x * alpha,   // lerp X
                (1.0 - alpha) * dVar1 + z * alpha);  // lerp Z
}
```

Verificado en disasm: `divsd` por 1000.0 (`0x141f2f3f8`), `fmod` 2π vía `FUN_141bf552c`, `(1-α)·destino + α·nuevo` para X (desde `+0xA8`) y Z (desde `+0xB0`), tail-call a `FUN_140678360`.

### 7.2 `applyExtrapolation` — FUN_1414c7ec0 (guardado en `decomp_mov/PE_applyExtrapolation_REAL.c`)

```c
void FUN_1414c7ec0(longlong param_1, double dx, double dz)
{
  lVar1 = *(longlong *)(*(longlong *)(param_1 + 0x58) + 0x10);   // mesh1 -> nodo
  FUN_140678360(entity,
                (double)*(float *)(lVar1 + 0xc) + dx,            // mesh.X + dx
                (double)*(float *)(lVar1 + 0x14) + dz);          // mesh.Z + dz
}
```
→ extrapola la posición **visual** del mesh (sin tocar `+0xA8/+0xB0`), y el notify vuelve a actualizar el grid.

### 7.3 `applyForce` — FUN_1414c7e40 (guardado)

```c
void FUN_1414c7e40(longlong param_1, double fx, double fz, undefined8 param_4)
{
  lVar1 = *(longlong *)(param_1 + 0x100);       // objeto de fuerza
  *(undefined4 *)(lVar1 + 0x10) = 0;
  *(float *)(lVar1 + 0xc) = (float)fx;          // +0x100+0xc = fuerza X (float)
  *(float *)(lVar1 + 0x14) = (float)fz;         // +0x100+0x14 = fuerza Z (float)
  *(undefined8 *)(param_1 + 0x108) = param_4;
}
```

---

## 8. Referencias de direcciones (verificadas)

| Dirección | Qué es |
|---|---|
| `0x140679380` | `setPosition` (slots vtable de entidad: 0x194=wrapper applyPosition, 0x1a0=applyPositionInterpolated, 0x1a8=wrapper interpolado, 0x1b0=setPosition alias de 7B, 0x1b8=setPosition, 0x168=notify) |
| `0x140678360` | `moveMeshes(X, Z)` → setX/setZ en meshes `+0x58`/`+0x60` → vtable[0x168] |
| `0x1413220b0` | setX (nodos del mesh, float en `+0xc`) |
| `0x1413222a0` | setZ (nodos del mesh, float en `+0x14`) |
| `0x140678480` | notify (slot 0x168) → `FUN_140924ff0(world+0x308, entity)` |
| `0x140924ff0` | grid update (celda = floor(coord/GRID_SIZE), clamp, IntMap) |
| `0x140925450` | wrapper Haxe del grid update (type-check 0xc1e758f) |
| `0x140924900` | ctor `fkengine.game.Grid` (lee args → FUN_140924140) |
| `0x140924140` | init grid: `GRID_SIZE = param_4`, `gridW/gridH = param_3/GRID_SIZE` |
| `0x140928100` | `Reflect.setField("GRID_SIZE", v)` → `DAT_1421b931c = v` |
| `0x140927970` | `Reflect.getField("GRID_SIZE")` → devuelve `DAT_1421b931c` |
| `0x140928750` | static init: `DAT_1421b931c = 0x200` (512) |
| `0x1421b931c` | **GRID_SIZE global** (int32, runtime = 194165) |
| `0x1421c17a8` | singleton mundo; `+0x308` = grid |
| `0x141f2f508` | `2147483647.0` (clamp int32 Haxe) |
| `0x141f2f620` | `-2147483647.0` (clamp int32 Haxe) |
| `0x141f2f3f8` | `1000.0` (rot mrad→rad) |
| `0x141f2f450` | `6.283185307179586` (2π, wrap de ángulos) |
| `0x14076c400` | parser de eventos CLEAR (evento 0x01 = posición, SIN división) |
| `0x140789500` | field processor (llama setPosition en 0x14078c3a9 / 0x14078c813) |
| `0x140795df0` | update loop 60 fps (llama al FP) |
| `0x140406050` | readUInt32 BE (uint; swap si allocator==1.0) |
| `0x141bf68e0` | floor |

---

## 9. Pendientes / notas

- El valor exacto de `GRID_SIZE` en runtime (194165) está calibrado en vivo, no leído del binario; el binario solo tiene el default 512 y el mecanismo de sobrescritura (config del servidor → `Reflect.setField("GRID_SIZE", …)`). Para confirmarlo al 100% habría que hookear `FUN_140928100` (setField) o `FUN_140924ff0` en vivo.
- La vtable de las entidades se construye en runtime (el binario guarda el template con RVAs de 4 bytes; el layout estático intercala metadatos GC cada 12 bytes); los slots citados (`0xb8`, `0x168`, `0x1b8`, `0x1c8`, `0x40`) están verificados por los call-sites del FP y de `FUN_1406790f0`/`FUN_140679380`.
- El orden de lectura del FP (hints 4/1/0) y la cola `[Z, X, rot]` están verificados por disasm de registros en `0x14078c342`–`0x14078c3a9`.
