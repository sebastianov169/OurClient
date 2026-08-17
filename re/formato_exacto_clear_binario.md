# Formato EXACTO del frame CLEAR 0x64 — MitosisOG.exe (verificado en binario)

> Verificado contra `_decomp_140789500.txt` (2011 líneas, FUN_140789500 completa),
> `_decomp_945f80.txt`, `_decomp_140795df0.txt`, `_decomp_14079d9b0.txt`,
> `_d_140677760.txt`, hojas de FUN_1401181c0/FUN_1400d01d0/FUN_14066e490/FUN_1407873b0,
> y capturas reales `traffic_full_capture.log` (dump 6651) y `clear_frame_dump.log`. 2026-08-13.

---

## 0. Resumen ejecutivo

1. **El frame CLEAR es una secuencia de ENTIDADES de 19 bytes exactos**: `1 + 350×19 = 6651` (dump completo verificado).
2. **El wire manda `[Z, X, rot]`** en el evento de posición (tipo 0x01 del parser): 1.er i32 → Z (+0xB0), 2.º → X (+0xA8), 3.º → rot (+0xB8, miliradianes). **El visor Python tenía X y Z intercambiados.**
3. **El cliente NUNCA divide las coordenadas**: opera en crudos u32; la única división es el grid (`floor(coord / GRID_SIZE)` con GRID_SIZE = DAT_1421b931c, runtime = 194165 calibrado). La constante 194165 NO existe en el binario (0 hits).
4. **Los field-codes reales** del procesador FUN_140789500: 0x2C = SIMPLE_VALUE/masa, 0x24 = POSITION_DATA, 0 = spawn con masa, 5 = set size, 0x0C = set masa int, 0x13 = remove particle, 0x1C = set gameTime, 3 = player física, 7 = entidad muerta/eliminada, 9 = marca muerto, 0x11 = set estado vivo, 0x10 = set estado 0...
5. **Límites**: el 21000 no es constante; el grid clamps a `dims-1` con `dims = worldSize/GRID_SIZE` → coordenada mundo ∈ [0, 20999].

---

## 1. Tabla campo → función → bytes → offsets (VERIFICADA)

**Mecánica del dispatch**: cascada if/else de checks de campos dinámicos de la entidad. Cada check: lee el nombre del campo (constructores FUN_14078xxx), invoca `(**(**local_e68+0xb8))(entity, nombre, 0)`, compara con `FUN_1401181c0` (==1 si int del campo == código, dispatch positivo) o `FUN_1400d01d0` (==0 si igual, dispatch por negación). Entidad = local_e68; ID = local_e58 = índice+1 (igual al u16BE del frame).

| Código | Línea .c | Función (handler) | Bytes/args leídos | Efecto verificado |
|---|---|---|---|---|
| 0x2C (44) | 739 | principal + FUN_14078d050 | 1 campo; valor int = id objetivo | SIMPLE_VALUE/MASA: recorre mapa param_1+0x308+0x10; si entidad muerta (0x158==1) procesa muerte/spawn; notifica listeners |
| 0x2B (43) | 797 | FUN_140648530(param_1+800) | 0 args | Limpia listener 0x2b8 |
| 0x1B (27) | 803 | FUN_1407873b0 → FUN_140647a70/FUN_140647e50 | id = índice | Lookup entidad por id en IntMap (0x3c0); asigna/limpia en mapa de escena (0x2b8/0x2e8) |
| 0x29 (41) | 840 | inline | 0 | Reset contador spawn: param_1+0x64c=0, +0x650=1 |
| 0x28 (40) | 847 | si ausente → 0x2A | 0 | Flag 'pausa spawn' |
| 0x2A (42) | 852-910 | FUN_1407873b0 + FUN_14078e190 + FUN_140647530 | 3 campos → ints | SPAWN FOOD: crea entidad en 'scene' (uVar33, uVar25, iVar10)+id |
| 0x2E (46) | 912-930 | FUN_140645d00(param_1+800, iVar13, iVar12) | 2 campos → 2 ints | Velocidad/posición (x,z) del jugador |
| 10 (0x0A) | 932-988 | FUN_1407873b0 + FUN_14078e970 + vtable 0x350 | 1 campo int + field idx1 int | SPAWN/DIVISIÓN: entidad nueva (uVar28, uVar33)+id |
| 0x0B (11) | 990 | → LAB_14078ccb7 (mismo spawn) | idem 10 | Split alternativo |
| 0x1F (31) | 994-1030 | FUN_1414e2900(param_1+0x630) | 4 campos → 4 ints | Escribe DAT_1421c2a08 +0x18/0x20/0x10/8 (punto/vector int) |
| 0x1E (30) | 1031-1060 | FUN_140686a70 + FUN_1406696b0 | 2 campos: idx1 int, idx2 int | Lookup/crear entidad por id; relaciona (target) |
| 0x1A (26) | 1061 | si ausente → 0x19 | 0 | Flag intermedio |
| 0x19 (25) | 1072-1082 | FUN_14005e120 + FUN_141766420 + FUN_1406695a0 | 1 campo int + 1 re-chequeado | Marca jugador activo (+0x84) |
| 4 | 1083-1090 | FUN_14073b220(param_1, uVar15) | 0 args | COMIDA COMIDA (eaten): regrowth/score |
| 0x14 (20) | 1091-1102 | FUN_1400347c0 + FUN_1406f5cd0 | 1 campo idx2 → int | Unassign flag (muerte parcial) |
| 6 | 1103 | si ausente → 9 | 0 | Guard: 'no está en spawn mode' |
| 9 | 1108-1131 | FUN_14005e120(param_1+0x5f0+8, valor) | 1 campo idx1 int | MARCA MUERTO (entity+0x30=0) |
| 0x1D (29) | 1132-1145 | FUN_140153780 + FUN_1400347c0 + FUN_14073b110 | 1 campo idx2 + idx0 int | Grid update (param_1+0x2a0) |
| 7 | 1165-1307 | FUN_1408xxx + FUN_14005e140 + vtable 0x218 + limpieza | 1 campo idx1 int; sub-campo 0x1C | ENTIDAD MUERTA/ELIMINADA: quita de param_1+0x640, anim, eventos de muerte |
| 5 | 1238-1297 | FUN_140677930(entity, uVar11) | 1 campo idx0 int; check idx1 | SET SIZE (int → +0x12); tamaño 0 → deja viva, si no destruye |
| 0x20 (32) | 1298-1307 | FUN_14004fd90 + vtable 0x188 | 1 campo idx0 | SET X (posición float via vtable+0x188) |
| 0x18 (24) | 1308-1320 | FUN_14004fd90 + vtable 0x180 | 1 campo idx3 | SET Y (vtable+0x180) |
| 0x16 (22) | 1321-1418 | FUN_140153780 + FUN_1400219d0 + loop pares → floats | 1+1 campo idx0 int (celda) + pares (x,y) | TRAIL/POS HISTORY: celda grid + array de pares (x,y) |
| 3 | 1419-1655 | FUN_1409254d0 + interpolación floats | 1 campo idx0 int = ID | PLAYER/ENTIDAD física: get entity por id, añade a mundo/colisiones, interpola posición, velocidad, applyParticle |
| 0x1C (28) | 1657-1667 | FUN_140685400(param_1+0x310, double) | 1 campo idx0 int | SET gameTime/clock (0x310) |
| 0 (0) | 1668-1715 | FUN_140679380(entity, x, z, rot) + FUN_140677760 | 3 campos idx4,1,0 → ints | SPAWN con masa: set (x,z,time); setSize(radio=floor(sqrt*10+0.5)); crea SI ID NO EXISTE |
| 0x0C (12) | 1734-1748 | FUN_140678b80(entity, uVar11) | 2 campos idx1, idx0 → ints | SET MASA INT (entity+0x34/0x38: particle id, valor) |
| 0x13 (19) | 1749-1754 | FUN_1406784e0(entity) | 0 args | Limpia flag partícula (entity+0x34/0x40=0) |
| 8 | 1755-1849 | FUN_1400d01d0 (campo==8 → MUERTE) | 0 args | GUARD 'no es entidad simple viva'; puede saltar a muerte |
| 0x0D (13) | 1794/1837 | → LAB_14078c77b: FUN_140679380 + FUN_140677760 | 2 campos idx1, idx0 + idx2 | MUERTE por colisión: limpia trail, setSize, marca visible 0 |
| 0x0E (14) | 1823/1841 | FUN_1400af7e0 + vtable 0x178 (0) | 1 campo idx3 | MUERTE alternativa: lee último y setea estado 0 |
| 0x0F (15) | 1813/1845 | → 0x10/0x11 o FUN_1406784e0 | 0 | Flag |
| 0x10 (16) | 1851-1862 | FUN_1400af7e0 + vtable 0x178 (0) | 1 campo idx0 | Set estado 0 (destruido) |
| 0x11 (17) | 1863-1876 | FUN_1400af7e0 + vtable 0x178 (1) | 1 campo idx0 | Set estado 1 (vivo) y CONTINÚA |

---

## 2. Formato del frame de entidades (dump 6651 bytes = 1 + 350×19)

```
[0]     0x64                -> prefijo/type CLEAR (1 byte)
Por cada entidad (19 BYTES EXACTOS):
[0:4]   04 00 08 00         -> header framing Haxe (u16BE 4, u16BE 8) fijo
[4:7]   01 00 00            -> constante 3 bytes
[7:9]   ID_hi ID_lo         -> ENTITY ID u16BE (identificador clave; ej 0002, 0003, 0006, 0802)
[9]     00                  -> separador
[10:14] 01 00 04 00         -> sub-header fijo Haxe (01 00 04 00 para valor simple)
[14]    FIELD-CODE          -> u8: 0x2C=44 SIMPLE_VALUE (masa), 0x24=36 POSITION_DATA, ...
[15:19] VAL_hi..VAL_lo      -> valor u32BE (int; en 0x2C es masa/seed)
-> 19 bytes/entidad. 1 + 350*19 = 6651 (dump completo confirmado)
```

**Sub-record POSITION (29 bytes)**: `64 + 04 00 08 00 + 01 00 00 + id u16BE + 00 + 00 05 00 24 00 + 14 bytes (x f32BE, y f32BE, dest_x f32BE, dest_y f32BE, gridX u16BE?, gridY u16BE?)`.

**Tick**: solo `0x64` (1 byte).

**Primitivas** (haxe.io.BytesInput, big-endian): u8=readByte, u16BE=readUInt16, i32BE=readInt32, f32BE=readFloat, u32BE para el valor de 4 bytes.

**Mapeo a objeto entidad**: id → FoodEntity_obj via IntMap param_1+0x3c0; creación FUN_14066e490 (clase 10 FoodEntity, _size=1); campo 0x2C → setSize: FUN_140677760(entity, (double)valor) escribe double en +0x18, int en +0x12, radio=floor(sqrt(abs(valor))*10+0.5) y notifica vtable+0x1c8/+0x140; FUN_140677930(entity, int) escribe +0x12 directo (size int).

---

## 3. Flujo completo bytes TCP → entidad

1. TCP 443 → socket raw. dataReceived → `FUN_14097ca60` (0x97ca60): valida objeto, contadores, llama dispatcher `FUN_140977a40(param_2)`.
2. `FUN_140977a40` (dispatcher): lee 1-2 bytes de cabecera via FUN_140406270/FUN_140406050; monta tipo u16 en param_1+0x28; flags 0x2c/0x2d (blob/length-prefixed); copia resto a buffer (param_1+0x10 → haxe.io.Bytes). Si es CLEAR (0x64) llama `FUN_140945f80(param_1, &frame)`.
3. `FUN_140945f80` (frame processor): case 10 = SPAWN de entidades: verifica campo 0x18, inicializa opciones via FUN_140955a40/FUN_140607430, registra handler FUN_140975250.
4. Los datos quedan como haxe.io.Bytes en el reader (param_1+0x3a0, BytesInput: +0x18=bytes, +0x10=longitud).
5. Game loop (60 FPS): `FUN_140795df0` acumula en param_1+0x4d0; cada 17ms llama al procesador de campos `FUN_140789500` (por entidad: lee field-codes y aplica handlers de la tabla).

---

## 4. Ejemplos hex reales decodificados (capturas)

- `64 04 00 08 00 01 00 00 02 00 01 00 04 00 2C 0A B4 13 F4` → id=2, campo 0x2C (masa), valor 0x0AB413F4 = 179948532.
- Serie inicial: ids 2,3,4,5,6,9,10,11,17,19,21,23,... max 1191 (271 entidades, todos sub-record `010004002c` = code 0x2C).
- Posiciones: `64 04 00 08 00 01 00 00 [id hi lo] 00 00 05 00 24 00` + 14 bytes payload = coordenadas (x f32BE, y f32BE, ...) code 0x24 (POSITION_DATA).
- Frames cortos: `64 00 04 37 3e 3e 3f fc` = tick/valor; `64 00 01 f8 32 56 3f fc 00 00 bb 17 b4 39 c0 06 00 01 c0 0b b0 02 03 00 b b0 43 11 01 40 70 43 11` = posición con destino x/z y grid.

**NOTA POSTMORTEM vs debug_entities.py**: el script antiguo parseaba '2C' como parte del sub-record fijo '010004002c'; el binario muestra que **2C es el FIELD-CODE (44)** del campo leído (SIMPLE_VALUE), **24=36 es POSITION_DATA** — el resto del sub-header (01000400 / 000500) es el encabezado de framing Haxe. El record de 19 bytes del dump 6651 = 64 + 4+3+2+1+5+4; 350 records exactos => 1 + 350*19 = 6651 (confirmado).
