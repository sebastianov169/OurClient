# MitosisOG.exe (PC) — Clasificación de entidades, radio, paleta, leaderboard y marca de jugador

> Fecha: 2026-08-14. Fuentes: GhidraMCP xebyte (http://127.0.0.1:8089, programa **MitosisOG.exe**, base 0x140000000) + documentación local verificada (`re/haxe_clear_parser.py`, `re/pc_analysis/protocolo_entrante_pc.md`, `re/_decomp_140789500.txt`, `re/_d_140677760.txt`, skill `mitosisog-tcp-protocol` refs) + captura real `capture_ctf.log` + Flash de referencia (`swf_scripts/.../fkengine/game/`).
> Cada hallazgo cita su fuente (dirección Ghidra o archivo local + línea). Nada inventado: lo no verificado se marca explícitamente.

---

## 1. Clasificación comida vs célula

### 1a. El binario tiene un `entityType` EXPLÍCITO (fábrica de entidades)
- El consumidor de eventos `FUN_140789500`, caso 4 (línea 1083-1090 de `re/_decomp_140789500.txt`), llama a **`FUN_14073b220`** = `buildEntityFromInfo` (fábrica).
- La fábrica lee el `entityType` de la info del frame y crea la clase correspondiente (tabla verificada):
  **1=FoodEntity, 2=PlayerEntity, 3=FloatingEntity, 4=VirusEntity, 5=CoinEntity, 6=FlagBaseEntity, 7=ChestEntity, 8=CustomEntity, 9=ImageEntity, 11=DiamondEntity, 12=ConquerableEntity, 13=SnakesPlayerEntity, 14=SkinnedPlayerEntity, 15=SpriteEntity** (clases globales DAT_1421c1718…DAT_1421cc3b0).
  - Fuente: `re/pc_analysis/entidades_gui_mapa_pc.md` §2 (tabla de 15 clases) y `re/pc_analysis/protocolo_entrante_pc.md` §7 (caso 4).
  - El campo `entityType` vive en la entidad en `ent+0x28` (int): `re/pc_analysis/entidades_gui_mapa_pc.md` §1.
  - Espejo en el Flash: `GameEntity.as` L23-77 define `ENTITY_TYPE_*` y `ENTITY_BASE_*` (FOOD=1, PLAYER=2, VIRUS=4…), y `build()` asigna `_entityType = param1[3]` (GameEntity.as L288).
- **Consecuencia**: el binario clasifica formalmente por un campo de TIPO en la info del frame, no por la masa. La masa es un atributo posterior (`setMassAndRadius`).

### 1b. En el protocolo CLEAR (wire), la heurística real es la MASA
- El protocolo CLEAR (45 tipos, todos numéricos) **no lleva un campo "virus/tipo" por entidad** en los eventos de posición/masa: `re/pc_analysis/protocolo_entrante_pc.md` §6 (tabla de 45 tipos) y `re/haxe_clear_parser.py` L35-52.
- La comida (FoodEntity) tiene `_size = 1` fijo y nunca recibe masa:
  - `FUN_14066e490` (__new de FoodEntity): `*(undefined4 *)(puVar6 + 0x12) = 1` (decompilado Ghidra, 0x14066e490) → `ent+0x90 = 1`, igual que el Flash `FoodEntity.as` L23 (`_size = 1`).
  - Las células reciben masa real vía `setMassAndRadius` (`FUN_140677760`: escribe `ent+0xc0` double y `ent+0x90` int; `re/binario-haxe-ghidra-funciones.md` ref L64-67).
- Por eso el parser del visor clasifica **masa == 0 → comida; masa > 0 → célula** y funciona: `re/haxe_clear_parser.py` L154-155 (`set_masa`: si masa>0 → `entityType = 0x14`), L143 (default `entityType = 1` comida); ref `entity-classification-viewer.md` L5-11.
  - **Veredicto sobre la pregunta 1**: el parser NO se corrige — "masa>0 = célula" es consistente con el binario (la comida nunca tiene masa propia). Pero es una simplificación: el tipo formal del binario es el `entityType` de la fábrica `FUN_14073b220` (ent+0x28), y existen más clases que "célula" (virus 4, coin 5, etc.) que el visor dibujaría como célula por tener masa > 0.
- El consumidor además distingue rutas de spawn: caso **0x2A = SPAWN FOOD** (L852-910 de `_decomp_140789500.txt` → `FUN_1407873b0` + `FUN_14078e190`) y caso **0x0A/0x0B = SPAWN/DIVISIÓN** (L932-990 → `FUN_14078e970`); ref `entity-processor-fun140789500.md` L35-37. `FUN_14078e190`/`FUN_14078e970` son los ctors estáticos de clase de la comida y de la célula respectivamente (patrón `_Init_thread_header`, decompilados Ghidra).

---

## 2. Fórmula del radio — CONFIRMADA con matiz (+1)

`FUN_140677760` (setMassAndRadius), decompilado crudo `re/_d_140677760.txt` L17-25:
```c
dVar2 = (double)FUN_141bf6990((double)iVar1);      // sqrt(masa)
dVar2 = floor(dVar2 * 10.0 + 0.5);                 // floor(sqrt*10+0.5)
iVar1 = (int)dVar2;
(**(code **)(*param_1 + 0x1c8))(param_1,(double)(iVar1 + 1));  // setRadius(radio + 1)
```
- **Radio final = `floor(sqrt(masa)*10 + 0.5) + 1`** (el +1 lo aplica la llamada a `setRadius`, slot vtable 0x1c8).
- Fuentes adicionales: `re/pc_analysis/entidades_gui_mapa_pc.md` §1 ("radio | vtable[0x1c8](radio+1), radio = floor(sqrt(m)*10+0.5)"), ref `mitosisog-renderer.md` L45, ref `binario-haxe-ghidra-funciones.md` L67-68 (que además cita el Flash: `radius = Math.round(Math.sqrt(_size)*10)+1`, GameEntity.as L252).
- ⚠️ **Discrepancia documentada**: `re/haxe_clear_parser.py` L166-171 (`radio_from_masa`) devuelve `floor(sqrt(masa)*10+0.5)` **sin el +1**. El visor lo compensa en `draw_map` (ref `entity-classification-viewer.md` L31: "radio = floor(sqrt(masa)*10 + 0.5) [+1 en draw_map, como el binario]"). La fórmula canónica del binario incluye el +1.

---

## 3. Paleta de colores real del binario — LOCALIZADA en .rdata (verificado por read_memory + xrefs)

Tres tablas de colores u32 (LE) en .rdata, idénticas a las del Flash:

| Paleta | Dirección .rdata (PC) | Valores (hex) | Se copia a | Init en el binario |
|---|---|---|---|---|
| **Células (8)** | `0x141d167c0` | 0x66CCFF, 0xFF66FF, 0x6666FF, 0x66CCFF, 0x66FF99, 0xFFFF66, 0xFFCC66, 0xFF6666 | `DAT_1421c0d28` | `FUN_1405928a0`: `FUN_1400dd110(&DAT_141d167c0, 8)` (decompilado Ghidra) |
| **Equipo (4)** | `0x141d16830` | 0xFF6666, 0x66CCFF, 0xFFCC66, 0x66FF99 | — (tabla vecina, misma zona) | — |
| **Comida (7)** | `0x141d16860` | 0xFF07CA, 0xFF071D, 0x1DFF3F, 0xFF8807, 0x5A07FF, 0x07F9FF, 0xBFFF07 | `DAT_1421c1710` | `FUN_14066fa50`: `FUN_1400dd110(&DAT_141d16860, 7)` (decompilado Ghidra) |

- Verificación: `read_memory` de las 3 direcciones (3 lecturas estables; sección .rdata) + `get_xrefs_to 0x141d167c0` → "From 1405928a6 in FUN_1405928a0 [DATA]" y `get_xrefs_to 0x141d16860` → "From 14066fa8a in FUN_14066fa50 [DATA]" (GhidraMCP, sesión 2026-08-14).
- **Selección de color** (patrón del Flash, mismo diseño en el port Haxe): `entityColor = _randomColors[_id % _randomColors.length]` — `GameEntity.as` L650-652; la comida lo usa en `buildMesh` (`FoodEntity.as` L82: `Image(_mesh).color = this.entityColor`, con su paleta de 7). En el binario, el setter de color por frame es el slot vtable **0x188** (caso 0x20 del consumidor, `_decomp_140789500.txt` L1298-1307; `protocolo_entrante_pc.md` §7 lo nombra "0x20 = color (vtable 0x188)"; el ref `entity-processor-fun140789500.md` L50 lo llama "SET X" — el nombre exacto del slot no está confirmado, pero ambos coinciden en el slot 0x188).
- Referencia Android (mismos símbolos): `re/android_analysis/symbols_entities.txt` L2457 (`GameEntity_obj::_randomColors` = 0x03477d10), L2489 (`_teamColors` = 0x03477d98), L2520 (`FoodEntity_obj::_randomColors` = 0x0347b780).
- ⚠️ Otra constante de color en el binario: función en `0x1406847c0-0x140684804` (disasm): `color = (flag ? 0x66CCFF : 0xFF6666)` — elección binaria de color (probablemente color de equipo/modo CTF), distinta de las paletas. No confundir.
- Nota: el visor `mito_view.py` L1245-1258 usa una `_PALETA` propia de 12 colores "neón" — NO es la paleta del binario (si se quiere fidelidad, usar las tablas de arriba).

---

## 4. Leaderboard — datos en los frames y campo "nombre"

- **El CLEAR NO lleva nombres ni strings**: los 45 tipos son todos numéricos (ids u16 opacos + valores); tabla completa en `re/pc_analysis/protocolo_entrante_pc.md` §6 y `re/haxe_clear_parser.py` L35-52. **No existe campo NOMBRE de entidad en CLEAR.**
- Los nombres/rank del jugador llegan por **AMF3**: case 3 (LOAD) del frame processor `FUN_140945f80` → carga de assets/players (`FUN_1409563a0`/`FUN_140956d00`/`FUN_140957630`; `protocolo_entrante_pc.md` §3). El objeto `_info` del jugador lleva `name`, `username`, `rank`, `lvl` (Flash `PlayerEntity.as` L345-443: `_parent._info.name`, `_info.username`, `_info.rank`, `_info.lvl`; `_info.ics` = iconos de equipo L135).
- **Masa**: actual por CLEAR (evento 0x0c con masa ×10, o campo y de 0x08/0x0e; `haxe_clear_parser.py` L275-285, L286-303); score/masa máxima por AMF3 op 51 (0x33) → IntMap +0x1a0 (`protocolo_entrante_pc.md` §3 L110; ref `binario-haxe-ghidra-funciones.md` L43-44; ref `clearing-masa-flujo-red-20260813.md` §1: op51 = masa máxima histórica, monótono).
- **Posición**: se calcula LOCALMENTE ordenando por masa. Flash `Leaderboard.as` L298-406: `updateLeaderboard()` cada 500 ms (L148), recorre `_data` (datos del server, L322), `sort(comparePlayers)` (L342) y asigna `position` (L406); `bestPlayer` = posición 1 (L245). El `_data` llega por AMF3 (`Instance.as` L1021: `new Leaderboard(this, _gameData.leaderboard)`; L2503 `displayDetails` con opData).
- **Refutación de un candidato**: el op AMF3 0x34 (52) NO es leaderboard — es SECURE_NONCE (idx1 string → AES `FUN_1403e94b0` → sendPacket `[0x2733, proof]`; `protocolo_entrante_pc.md` §3 L111). Verificado hoy: `FUN_140970050` construye un paquete de ENVÍO (writeInt opcode + writeByte + flush `FUN_140170af0`) con el byte de tipo `bVar2 & 0x3f` (decompilado Ghidra 0x140970050). La etiqueta "leaderboard-ish" de `binario-haxe-ghidra-funciones.md` L42 era una conjetura, ahora refutada.
- Único "leaderboard" con strings en el binario: SteamWorks (`LeaderboardOp`, `SteamWrap_FindLeaderboard`, `_all_strings.txt` L7339/7384/8614-8618) — no es el ranking de sala.

---

## 5. Marca de jugador 0x19/0x1a — CONFIRMADA como id del jugador activo

Decompilado del consumidor `FUN_140789500` (`re/_decomp_140789500.txt` L1061-1082), lógica real:
```c
// evento 0x1a: si el campo 0 del evento != 0x1a (FUN_1400d01d0 invertido) → 0x19
// 0x1a y 0x19 son eventos de 3 bytes: [tipo][u16 id] (tabla §6)
LAB_14078cc10:
  uVar11 = int(campo del evento);                        // el id (u16 BE)
  if (FUN_14005e120(set_jugadores + 0x358, uVar11)) {    // ¿el id está en el set de jugadores?
    ent = FUN_141766420(param_1 + 0x358, id);            // buscar entidad del jugador
    *(ent + 0x84) = (tipo_del_evento == 0x19);           // flag "jugador activo" (1 si 0x19, 0 si 0x1a)
  }
```
- **Semántica**: los eventos 0x19/0x1a traen el id (u16) de una entidad; si ese id pertenece al conjunto de jugadores del mundo (`param_1+0x358`), la entidad se marca como jugador activo en `ent+0x84` — `0x19` = activo (1), `0x1a` = inactivo (0). El id marcado es el del jugador local.
- Fuentes: decompilado Ghidra `re/_decomp_140789500.txt` L1061-1082; `re/pc_analysis/protocolo_entrante_pc.md` §6 L191 ("0x19/0x1a = u16 id (0x19/0x1a = marca de jugador activo)") y §7 (códigos 0x1A:1061, 0x19:1072).
- El parser lo refleja: `player_id_de_frame()` y `decode_clear_full()` (`haxe_clear_parser.py` L511-544) devuelven el id de 0x19/0x1a como `player_id`; la entidad se marca `entityType = 0x15` (jugador) en L530-531.
- ⚠️ **Honestidad sobre capturas**: en los logs reales locales (`mito_view36/41/42/38.log`, 111.273 frames CLEAR de eventos parseados con `parse_clear`, dump 19B excluido) la marca **no aparece (0 hits de 0x19/0x1a)**. El ejemplo `64190008` del parser (L708-709) es sintético. La verificación es del **decompilado del binario**, no de captura; el server solo la envía en ciertos momentos (probablemente al spawn/entrar a sala). Los "6419/641a" que aparecen en logs viejos (`mito_view15/16/...`) son falsos positivos: bytes coincidentes dentro de records del dump 19B (formato 19B/entidad, `haxe_clear_parser.py` L556-589), no la marca.
- **Correlación de captura (CTF)**: `capture_ctf.log` muestra el op AMF3 **19** con `[[351, 352], []]` cada ~500 ms (p.ej. líneas 84-103: `25921ms IN TCP [19, [[351, 352], []], ...]`), con 351 y 352 = ids de las células del jugador en la sala CTF. Es un mensaje de control distinto (op AMF3, no evento CLEAR; cae en el default del frame processor → reenvío a escena). Su semántica exacta NO está confirmada en el binario; se documenta como observación de la secuencia real.

---

## 6. Notas sobre `capture_ctf.log` (secuencia real del binario)

- El log es de hooks Frida sobre AMF3 descifrado: secuencia `IN TCP [1, ts, 0]` (ping), `[2, code, ts]` (server time), `"PING :talk003.mitos.is"`, `[19, [[351,352],[]], ts]`, `"undefined"` — 646 mensajes `IN TCP`.
- **No contiene frames CLEAR**: la ruta binaria (flag==1 del dispatcher, `FUN_140977a40` → `FUN_14076c400`) no pasa por el hook `frame_processor` (solo AMF3 flag≠1). Los CLEAR del mundo se ven en `mito_view*.log` (visor Python). Fuente: `protocolo_entrante_pc.md` §2 (rutas flag 1 vs 2) y el propio log (solo arrays AMF3).

---

## 7. Fuentes (índice)

| Tema | Fuente principal | Secundarias |
|---|---|---|
| Clasificación (entityType/fábrica) | `FUN_14073b220` (Ghidra) | `entidades_gui_mapa_pc.md` §1-§2; `protocolo_entrante_pc.md` §7; `entity-processor-fun140789500.md` L99; Flash `GameEntity.as` L23-77/L288 |
| Clasificación (masa en wire) | `haxe_clear_parser.py` L143/L154-155 | `entity-classification-viewer.md` L5-11; `FUN_14066e490` (Ghidra); Flash `FoodEntity.as` L23 |
| Radio `floor(sqrt(m)*10+0.5)+1` | `re/_d_140677760.txt` L17-25 (Ghidra `FUN_140677760`) | `binario-haxe-ghidra-funciones.md` L64-68; `mitosisog-renderer.md` L45; `entidades_gui_mapa_pc.md` §1; Flash `GameEntity.as` L252 |
| Paleta células/equipo/comida | `.rdata` `0x141d167c0`/`0x141d16830`/`0x141d16860` + `FUN_1405928a0`/`FUN_14066fa50` (Ghidra, read_memory + xrefs) | Flash `GameEntity.as` L83/L85/L650-652, `FoodEntity.as` L18/L82; `symbols_entities.txt` L2457/2489/2520 (Android) |
| Leaderboard / sin nombre en CLEAR | `protocolo_entrante_pc.md` §3/§6 | Flash `Leaderboard.as` L148/L322/L342/L406, `Instance.as` L1021/L2503, `PlayerEntity.as` L345-443; refutación 0x34 en `FUN_140970050` (Ghidra) |
| Marca 0x19/0x1a | `re/_decomp_140789500.txt` L1061-1082 (Ghidra) | `protocolo_entrante_pc.md` §6 L191; `haxe_clear_parser.py` L511-544; logs reales (0 hits) |
| Secuencia real CTF | `capture_ctf.log` | `protocolo_entrante_pc.md` §2 |
