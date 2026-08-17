# PROTOCOLO ABSOLUTO — MitosisOG (PC + Android, verificado en ambos binarios)

> Consolidado 2026-08-13 tras el enjambre de 7 subagentes (4 Android + 3 PC) con GhidraMCP.
> Binarios: PC `MitosisOG.exe` (x86:LE:64, base 0x140000000, proyecto og 1.1.8) y Android `libApplicationMain.so` (AARCH64, base 0x00100000, proyecto new android version mitosis).
> Detalles por tema: `re/android_analysis/` (entidades.md, opcodes_frames_entrada.md, frames_salida.md, clear_parser_android.md, cruce_android_desktop.md) y `re/pc_analysis/` (protocolo_entrante_pc.md, protocolo_saliente_pc.md, entidades_gui_mapa_pc.md).
> Skill: mitosisog-tcp-protocol/references/pc-android-clear-format-20260813.md

## VEREDICTO CENTRAL: PC y Android comparten el protocolo 1:1

Salvo 3 diferencias menores (keystream desturple, 2 opcodes extra del PC, M2XC real en PC para 0x2724), **ambos clientes usan exactamente el mismo protocolo**. Las reglas empíricas antiguas (id u8, v:i32, /194165, /500, 21000, id 0xc8=X) quedan **REFUTADAS** (0 hits de esas constantes en ambos parsers).

## 1. Frame TCP entrante (S→C) — IDÉNTICO PC/Android

```
[len: u16 BE][flag: u8][payload: len bytes]     (0xFFFF → +u32 extra para len > 65535)
flag == 1 → CLEAR binario crudo (sin desturple/M2XC/AMF3)
flag == 2 → payload comprimido (uncompress → AMF3)
flag != 1 → AMF3 de control
```
- PC: dispatcher `FUN_140977a40`, dataReceived `FUN_14097ca60`, packetReceived AMF3 `FUN_140945f80`, packetReceivedClear `FUN_1409662f0` → escena+0x50 → `FUN_14076c400`.
- Android: dispatcher `0x01c2ef84`, dataReceived `0x01c2f978`, packetReceived `0x01c253c8`.
- Hash de callback común: `0xfd5399ed` = "packetReceived".
- Endianness: **big-endian** en todo (readUInt16/readInt32 BE; writeInt BE >>24 primero).

## 2. Control AMF3 (S→C) — IDÉNTICO

| Op | Significado | Acción |
|---|---|---|
| 1 | PING | replyToPing (0x2711) |
| 2 | LAG | _lag + _serverTime |
| 3 | LOAD | assets/players/textures |
| 4 | PLAYERID | _playerId (PC: DAT_1421b9364) |
| 10 | EVENT / SPAWN | PC: campo0==0x18 → dump mundo (FUN_140975250); si no invite |
| 40 | CONFIRM_UDP | habilita UDP |
| 51 (0x33) | **SCORE** | IntMap +0x1a0 — **el score NUNCA va por CLEAR** |
| 52 | SECURE_NONCE | responder 0x2733 con proof |
| 53 | SECURE_CHALLENGE | guarda challenge |
| default | — | reenvío a hash 0xfd5399ed (escena) |

## 3. CLEAR (0x64) — formato de eventos (45 tipos PC / 44 Android)

```
[0x64: u8] + eventos: [tipo: u8][campos...] hasta fin de payload
Ids: SIEMPRE u16 BE (readUnsignedShort)
Valores: 2 modos según config del server (flag escena+0x3f0, key "float"):
  SHORT (default): u16 BE / _shortDivisor   (PC default 1.0, Android default 10.0; key "shortdivisor")
  FLOAT: i32 BE → (float)
Escalas reales: ×10 en masa (0x0c) y en 0x0a/0x0b/0x0d/0x0f/0x2e/0x28; nada más.
Clamp de posición: clamp(v, 0, Grid::_boundaries[i]−1) — IDÉNTICO en ambos.
194165 = GRID_SIZE del grid espacial (runtime DAT_1421b931c), NO divisor de valores.
```

Tipos (PC == Android salvo 0x2a solo PC; 0x12 y 0x30+ no existen):
0/0x15/0x17/0x27 = posición (u16 id + V x + V z [+y][+rot][+v], interpola N frames, clamp grid)
1 = coords i32×3, 3/5 = id+v1+V, 4 = lista floats, 6/7/9/0x13/0x19/0x1a/0x1d/0x2f = id solo (3B),
8/0x0e/0x0d/0x0f = id + x/z/y (+extra), 0x0a/0x0b/0x2e = a+b×10+c, 0x0c = id+v+masa×10,
0x10/0x11/0x14/0x1c/0x2d = id+V, 0x16/0x1f/0x23/0x28 = 3-4 u16 (0x28: d−1),
0x18 = a+b+c+V, 0x1b = id+bool, 0x1e = a+b+n+vals, 0x20 = a + lista u16 ids,
0x21/0x22 = a+b, 0x24/0x25/0x26 = a+b+V, 0x29/0x2b/0x2c = sin campos (1B), 0x2a = solo PC.
Tabla completa con líneas de evidencia: `pc_analysis/protocolo_entrante_pc.md` §6 y `android_analysis/clear_parser_android.md` §4.

Consumidor: cola escena+0x3a0, contador frames +0x5c4, InterpolationHistory +0x5f0, array +0x5d8/+0x5e0, multiplicador +0x5f8, flags +0x48c/0x48d/0x48f, hashset visto +0x640.

## 4. Entidades — layout IDÉNTICO PC/Android

| Campo | Offset | Nota |
|---|---|---|
| masa int (_size) | +0x90 | setMassAndRadius (PC FUN_140677760) |
| **masa double** | **+0xc0** | CORRECCIÓN: el "+0x18" era artefacto del decompilador (longlong* [0x18] = 0xc0). PC == Android |
| id | +0x2c | clave de grid.addEntity |
| meshes | +0x58/+0x60 | Base2D: +0x10 → +0xc x, +0x14 z (floats) |
| destino x/z | +0xa8/+0xb0 | doubles, escritos por setPosition (PC FUN_140679380) |
| rotación | +0xb8 | miliradianes, setAngle = rot/1000.0, wrap ±π |
| gridX/gridY | +0xdc/+0xe0 | int32, init −1 |
| radio | vtable[0x1c8] | radio = floor(sqrt(masa)*10+0.5), pasa radio+1 |
| zOrder | vtable[0x140] | |
| objeto | 0xf8 bytes | GameEntity |

Fábrica: PC `FUN_14073b220` (wrapper FUN_14073ea00) / Android `HqJ8Md::buildEntityFromInfo` 0x29bd580.
entityType→clase: 1=Food, 2=Player, 3=Floating, 4=Virus, 5=Coin, 6=FlagBase, 7=Chest, 8=Custom, 9=Image, 11=Diamond (extra PC), 12=Conquerable, 13=Snakes, 14=Skinned/Diamond, 15=Sprite. FoodCache reuse. 

## 5. Frames salientes (C→S) — IDÉNTICOS salvo keystream

TCP raw (writeClear): `[len:4 BE][len:4 BE][0x40][opcode:i32 BE][arg:float32 BE]*N` — byte-idéntico (PC FUN_14096fa80 / Android 0x01c2d424).
UDP/websocket: `[magic][token:4][msgId:4][flag][opcode:16][arg:float32]*N` (PC FUN_14096df30 / Android 0x01c2c9f0).
AMF3 (sendPacket): Amf3Writer → checksum V1 `acc=(b*mult^0xef8)+acc, mult+=2` → header byte `acc&0x3f` (V2: opcode%63) → resturple(seed=opcode) → header `[len:4][len:4][byte&0x3f]` → writeBytes×2 + flush (PC FUN_140970050 / Android 0x01c294b4).
Flag extra canal: `(conn+0xc4>>8)&1`; flag=1 → TCP, flag=0 → UDP/websocket con reenvío.

**CRÍTICO — ByteArrayResturple keystream difiere:**
- Android (0x1b45cb4): `out[i] = (sig + 0x9c + (V3[i] ^ (seed + i + i² + ((seed+i)&0xF0)))) & 0xFF`
- **PC (FUN_1403cf5d0, modo simple): `out[i] = V3[i] ^ ((seed+i)&0xF + seed + i²) + sig − 100`** (máscara 0xF, −100)
- PC modo cifrado (flag bit8): state-mixing fmix2 (0x6d2b79f5) — no documentado en Android.
Interleave por mitades con paridad: idéntico en ambos.

Firma de sesión (equiv. h1/h2/sk/magic): PC `signatureAdd FUN_140232ee0` (_sigC ^= time^0x6d2b79f5^v; rotl11; _sigB=_sigC^v^0x85ebca6b; rotl5; _sigA=rotl(_sigB,7)^rotl(_sigC,13)^v), `getSig FUN_140232fe0` ((rotl(_sigC,13)^rotl(_sigB,7)^_sigA) ^ (>>16)). Init familia FUN_140231f30 (fmix2 + "M2PS" 0x4d325053). Globals PC 0x1421ce510/514/518. Android: 0x1b40854/0x1b40bac con 0x6d2b7991/0x85ebca0f.

Opcodes salientes (38 en PC, 36 en Android): READY=10000 (AMF3 5 args [x,y,z,w,flag]), PING_REPLY=0x2711 [time, nonce=mt()%99999+sig−100], MOVE=0x2715 [timeAccu,0,dirX,dirZ,force], MOVE_SHORT=0x2726 [17,angulo,force], MOVE_LOOK_AT=0x272e, BEGIN/END_SHOOTING=0x271b/0x271c, SHOOTING_RADIANS=0x272d [ángulo], BEGIN/END_CTRL=0x272b/0x272c, BEGIN/END_SPEEDUP=0x2729/0x272a, **SPLIT=0x271a (10010) sin args TCP**, USE_ITEM=0x2720, CALL_PET=0x2727, REQUEST_INVITE=0x271d, REFRESH=0x271e, RELEASE=0x271f, CHAT=0x2722, REPORT_ABUSE=0x2723, TOGGLE_BAN=0x2721, PLAYER_UPDATE=0x2724 (PC: writeWithNonce M2XC), CONTROL_SETUP=0x272f, UDP_NOT_AVAILABLE=0x2732 (writeClear), SECURE_PROOF=0x2733, CONFIRM_UDP=0x2731 (UDP), 0x2734/0x2735 solo PC.

## 6. GUI / Mapa (PC)

Flujo: CLEAR parser `FUN_14076c400` → cola [Z,X,rot] → field processor `FUN_140789500` (presupuesto 17/tick) → `setPosition FUN_140679380` (+0xa8/+0xb0/+0xb8 + meshes + notify vtable[0x168]→grid) + setMassAndRadius + flags → interpolación `FUN_1407959e0` → `applyPositionInterpolated FUN_1406790f0` (lerp X/Z, wrap rot ±π, setMassAndRadiusInterpolado FUN_1406775f0) → pantalla: `x = stageW/2 − camX·scale` (FUN_14077c150), zoom V2 `min(h·(W/H)/fov.x, h/fov.z)`, culling ±10/20.

Mapa: Grid (tabla 0x141dcc460): GRID_SIZE = DAT_1421b931c (runtime 194165), dims +0x40/+0x44 = worldSize/GRID_SIZE, boundaries = DAT_1421c2a08 (Vector4 doubles [X máx, Z máx, X mín, Z mín]), update FUN_140924ff0 con clamp de celda a dims−1. Mapa físico = 4 muros reposicionados por FUN_1414e2900 con el config (campo 0x1f). Clamp de posición idéntico a Android.

## 7. Impacto en el cliente Python (parches pendientes)

1. **Parser CLEAR** (mito_view.py / tcp_full.py): migrar de [id u8][v:i32]+rangos a **u16 BE + shortdivisor (config) o i32→float**, 45 tipos, ×10 masa, clamp grid, score solo por AMF3.
2. **ByteArrayResturple PC**: usar keystream PC `V3[i] ^ ((seed+i)&0xF + seed + i²) + sig − 100` (el cliente se conecta al server con clientes PC; el server puede usar la variante según cliente).
3. **Masa double +0xc0** (no +0x18) si el cliente lee memoria (Frida/hooks).
4. **Frame entrante**: `[len u16 BE][flag][payload]` — el "opcode" del header es longitud; el opcode real va en AMF3 item 0 o es CLEAR 0x64.
5. Opcodes extra PC 0x2734/0x2735, M2XC solo para 0x2724/op5.
