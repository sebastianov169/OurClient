# Protocolo SALIENTE (C→S) del PC — MitosisOG.exe — ANÁLISIS DEFINITIVO

> Fuente: GhidraMCP xebyte v5.14.2 (http://127.0.0.1:8089), MitosisOG.exe x86:LE:64 base 0x140000000
> Fecha: 2026-08-13. Comparativa 1:1 vs Android (libApplicationMain.so) — `android_analysis/frames_salida.md`
> Decompilados crudos: `_scratch/d_pc_*.txt` (44 archivos)

## 1. Funciones de envío del PC (descompiladas, con direcciones)

| Rol | PC | = Android | Evidencia |
|---|---|---|---|
| Sender central `(conn, flag:byte, opcode:u32, args)` | `FUN_14096e330` | writeClearWithUdp 0x01c2d0a8 | retransmite cola UDP (conn+0x1a0, timeout) y elige canal: websocket (`DAT_1421b8a84==1` && conn+0x168) → `FUN_14096dc40`; si no → `FUN_14096fa80` |
| TCP raw "clear" | `FUN_14096fa80` | writeClear 0x01c2d424 | **`[len:4][len:4][0x40][opcode:i32][arg:float32]*N`** — frame `00000004 00000004 40 0000271A` byte-idéntico |
| UDP/websocket | `FUN_14096dc40` (msgId=conn+0x198++) → `FUN_14096df30` | writeUdpPacket/buildUdpPacket 0x01c2b820/0x01c2c9f0 | **`[magic:1][token:4][msgId:4][flag:1][opcode:16][arg:float32]*N`** + `0xffffffff` si cabe + padding 0x00 hasta conn+0x16c |
| sendPacket AMF3 dispatcher | `FUN_1409644c0` | 0x01c294b4 | `[opcode,args]`; **solo 0x2724 y op5** van por `FUN_1409639d0` (writeWithNonce → **M2XC**: keyhash `FUN_1403e94b0` + encrypt `FUN_1403df080`) |
| sendPacket AMF3 core | `FUN_140970050` | 0x01c294b4 | serializa Amf3Writer, checksum, resturple, header, writeBytes×2+flush |
| writeInt/writeFloat | `FUN_140406ce0` / `FUN_140406bd0` | openfl ByteArrayData | **BE nativo** (>>24,>>16,>>8,bajo; se invierte solo si el flag endian del buffer lo pide). Confirma `0000271A` BE |
| replyToPing | `FUN_140965c10` | 0x01c29b44 | 1ª vez CONFIRM_UDP 0x2731; AMF3 `[0x2711, time_ms, nonce]` con `nonce = (mt.next()%99999) + sig − 100` (constante 0x40f869f000000000=100000.0) |
| READY 10000 | `FUN_14072d930` | — | **sendPacket AMF3 con 5 args** `[x,y,z,flag]` (globals 0x1421b8d60/0xd80/0xd98/0xbb7c8); luego UDP_NOT_AVAILABLE 0x2732 por writeClear si no hay websocket |

## 2. Checksum / encoding / firma (confirmados)

- **Checksum V1 = `FUN_14093ad00`**: `mult=-1; por byte: mult+=2; acc += (b*mult ^ 0xef8)` → header byte `acc&0x3f`. Constante **0xef8** en 0x14093ac42/0x14093ad8c. V2 = `(conn+0x30 % 63)` (disasm 0x140970267). Flag extra = `(conn+0xc4>>8)&1` (disasm 0x14097026b-0x140970273). **Idéntico a Android.**
- **ByteArrayResturple = `FUN_1403cf5d0`**, llamada con **seed = conn+0x30** (disasm 0x140970267: `MOV R15D,[RSI+0x30]` → `[RBP+0x83]`) y flag = bit8. Interleave con paridad **idéntico a Android**; pero la XOR final difiere:
  - Android: `out[i] = (sig + 0x9c + (V3[i] ^ (seed + i + i*i + ((seed+i)&0xF0)))) & 0xFF`
  - **PC (modo simple, flag=0): `out[i] = V3[i] ^ ((seed+i)&0xF + seed + i*i) + sig − 100`** — máscara **0xF (bajo)** en vez de 0xF0 y **−100** en vez de +0x9c. Mismo interleave, keystream distinta.
  - PC tiene además un **modo "cifrado"** (flag=1) con state-mixing XOR (fmix2: `u20 ^= u20*0x2000; >>0x11; <<5^`, constante 0x6d2b79f5) — no documentado en Android.
- **Firma de sesión**: `signatureAdd = FUN_140232ee0` — `_sigC ^= time ^ 0x6d2b79f5 ^ v; rotl11; _sigB = _sigC^v^0x85ebca6b; rotl5; _sigA = rotl(_sigB,7)^rotl(_sigC,13)^v` (globals 0x1421ce510/514/518). `getSig = FUN_140232fe0`: `(rotl(_sigC,13)^rotl(_sigB,7)^_sigA) ^ (>>16)` — usada en resturple (`+sig−100`) y en el nonce del ping. Init = familia `FUN_140231f30/231fd0/2320a0` (fmix2 + **0x4d325053 = "M2PS"**) y contadores `FUN_140231780/231a80 (0x1201)`. **Las constantes base Android 0x6d2b7991/0x85ebca0f NO existen en el PC**; solo las variantes 0x6d2b79f5/0x85ebca6b. Las strings `h1/h2/sk/X-Client-Key` no aparecen en `_all_strings.txt` (archivo parcial, corta en 0x141c8xxxx) y `search_strings` del server ignora el filtro — **h1/h2/sk/magic no localizadas con strings**, pero la maquinaria M2PS/fmix2 es la misma familia que el cliente Python ya implementa.

## 3. Tabla de opcodes salientes del PC (Opcodes.__boot = `FUN_140680a20`)

Entrantes 0x1–0x36; **salientes 0x2710–0x2735 = 10000–10037 (38 valores)**. El PC tiene **2 opcodes extra vs Android: 0x2734 (10036) y 0x2735 (10037)**.

| Opcode | Emisor PC | Args | Canal | vs Android |
|---|---|---|---|---|
| READY 10000 | FUN_14072d930 | `[x,y,z,w,flag]` 5 args | AMF3 | = (Android args sin detallar) |
| PING_REPLY 0x2711 | FUN_140965c10 | `[10001, time, nonce mt()%99999+sig−100]` | AMF3 | **= idéntico** |
| MOVE 0x2715 | `FUN_140795df0` (frame 60fps) | `[timeAccu, 0, dirX, dirZ, force]` | flag=0 (UDP/TCP) | = |
| MOVE_SHORT 0x2726 | `FUN_140780510` (udp_move, 0x780510 ✓ hook), `FUN_140795df0` | `[17, angulo, force]` | flag=0 | = |
| MOVE_LOOK_AT 0x272e | `FUN_140780510`, `FUN_140795df0` | `[17, dirX, dirZ, force, atan2]` | flag=0 | = |
| BEGIN_SHOOTING 0x271b | `FUN_140780510` (tras cada move) | `[]` | flag=1 | = |
| END_SHOOTING 0x271c | `FUN_1407814a0` (+0x628=0) | `[]` | flag=1 | = |
| SHOOTING_RADIANS 0x272d | `FUN_140780350`, `FUN_140780400` | `[ángulo]` | flag=1 | = |
| BEGIN_CTRL 0x272b / END_CTRL 0x272c | `FUN_140780120` / `FUN_140780170` | `[]` | flag=1 | = |
| BEGIN_SPEEDUP 0x2729 / END 0x272a | `FUN_1407801f0`+`140780240` / `1407802a0`+`1407802f0` | `[]` | flag=1 | = |
| **SPLIT 0x271a (10010)** | `FUN_1407815b0`/`FUN_140781600` | `[]` | flag=1 **TCP** | = |
| USE_ITEM 0x2720 | `FUN_140789490`/`1407894c0` | `[]` | flag=1 | = |
| CALL_PET 0x2727 | `FUN_140789420`/`140789450` | `[]` | flag=1 | = |
| REQUEST_INVITE 0x271d / REFRESH 0x271e / RELEASE 0x271f | `FUN_14072e630` / `14076c200`+`14076c260` / `14076c300`+`14076c360` | `[param]` | AMF3 | = |
| CHAT 0x2722 / REPORT_ABUSE 0x2723 / TOGGLE_BAN 0x2721 | `FUN_140721960` / `140721610` / `140752cf0` | `[string]` | AMF3 | = |
| PLAYER_UPDATE 0x2724 | `FUN_14072f180` (+ 1409644c0) | args | **writeWithNonce M2XC** (Android: stub) | **≠ (PC cifra)** |
| CONTROL_SETUP 0x272f | `FUN_140795680`/`140795750`/`140795880` | `[1 valor]` | AMF3 | = |
| UDP_NOT_AVAILABLE 0x2732 | `FUN_14072d930`, `FUN_14072f180` | `[]` | **writeClear 0x40** | = |
| SECURE_PROOF 0x2733 | `FUN_140945f80` (case iVar7==10) | `[0x2733, challenge+sig]` | AMF3 | = |
| CONFIRM_UDP 0x2731 | `FUN_140965c10` | `[]` | buildUdpPacket flag=1 | = |
| **0x2734 (10036)** | `FUN_140721ad0` | `[]` | AMF3 | **NO en Android** |
| **0x2735 (10037)** | `FUN_1413c3430` | `[nombre-nivel, DAT_141d44330]` | AMF3 | **NO en Android** |
| CLICK/ROAD/CLEAR_ROAD/FOCUS/TEST_MERSENNE/SET_PARENTAL/RESIZE_FRUSTRUM | hits existen (0x2716→0x140d1d29c, 0x2730→FUN_14079ba80 guardado) | — | — | no decompilados por límite de iteraciones |

## 4. Endianness: **CONFIRMADO big-endian** (writeInt escribe >>24 primero; solo se invierte si el flag endian del buffer ByteArrayData está activo — los buffers de header se crean fresh → BE).

## 5. Conclusión

**PC y Android comparten el protocolo saliente: mismo layout TCP (`[len][len][0x40][op]` y `[len][len][byte&0x3f]`+resturple), misma checksum V1 (0xef8, mult+=2)/V2 (op%63), mismo flag bit8, misma firma de sesión (rotl 11/5, sig^>>16, nonce mt%99999+sig−100), mismos opcodes 10000–10035 y mismo comportamientos de canal (flag=1 TCP, flag=0 UDP/websocket con reenvío).** Diferencias encontradas:
1. el PC tiene 2 opcodes extra (0x2734/0x2735);
2. **la keystream final del desturple difiere** — máscara `0xF`+`sig−100` vs Android `0xF0`+`0x9c` (el interleave y la conexión con la firma son idénticos; **el cliente Python debe usar la variante PC**);
3. el PC implementa writeWithNonce real (M2XC) para 0x2724/op5 mientras Android lo tiene como stub;
4. el PC tiene un modo resturple "cifrado" adicional (state-mixing fmix2, flag bit8) no documentado en el Android.
