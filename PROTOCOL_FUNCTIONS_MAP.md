# MitosisOG Protocol Functions Map — HTTP / TCP / UDP

> Generado con análisis Ghidra (GhidraMCP 5.14.2, Ghidra 12.1.2) sobre MitosisOG.exe
> Base de imágenes: `0x140000000` (Ghidra), runtime ASLR: `base = Process.enumerateModules()[0].base`

---

## 1. HTTP Layer (API app.mitos.is)

| RVA | Función Ghidra | Rol | Firma (x64) |
|-----|----------------|-----|-------------|
| `0xafee00` | `FUN_140afee00` | **url_builder** — construye la URL de la petición y llama a http_sender | `void f(rcx=this, rdx=*url_string)` |
| `0xae7690` | `FUN_140ae7690` | **http_sender** — envía la petición HTTP (dispatch síncrono/async) | `void f(rcx=obj, rdx=params, r8=body...)` |
| `0xa84b30` | `FUN_140a84b30` | **HTTP request builder (worker)** — ensambla body JSON + **cifra M2XC** antes de enviar | worker HXCPP, frame >0x2000 |
| `0x11398e0` | `FUN_14011398e0` | **HTTP loader** — procesa la respuesta HTTP entrante | `rcx = data_ptr` |
| `0xb29080` | `FUN_140b29080` | **config getter** — strings de configuración/endpoints | retorna string |
| `0x2312a0` | `FUN_1402312a0` | **string builder** — construcción de strings Haxe | — |

### Flujo HTTP (confirmado por xrefs + capturas)
```
game logic → url_builder(0xafee00) → http_sender(0xae7690)
   → HTTP request builder(0xa84b30) → M2XC encrypt(0x3df080) + key hash(0x3e94b0)
   → mbedTLS ssl_write (TLS) → ws2_32 send
respuesta: ws2_32 recv → mbedTLS ssl_decrypt_buf(0x1b86490) → plaintext HTTP
   → HTTP loader(0x11398e0) → M2XC decrypt(0x3e94b0) → JSON parse
```

---

## 2. mbedTLS Layer (TLS 1.3, todos los HTTP van por TLS)

| RVA | Función | Rol | Estructura clave |
|-----|---------|-----|------------------|
| `0x1b86490` | `ssl_decrypt_buf` | Descifra records TLS → **plaintext disponible aquí** | `ssl_ctx[0xC8]`=in_msg ptr, `[0xD8]`=msgtype (0x17=app data), `[0xE0]`=in_msglen |
| `0x1b83990` | `ssl_read_record_layer` | Lee records de la red | mismo ssl_ctx |
| `0x1b88500` | `ssl_handle_message_type` | Despacha tipos de record | — |
| `0x1b80eb0` | `ssl_fetch_input` | Fetch de buffer de entrada | — |

**Punto de hook óptimo para HTTP plaintext**: `ssl_decrypt_buf` (onLeave, leer `ssl_ctx[0xC8]` + `[0xE0]`).

---

## 3. M2XC Cipher Layer (HTTP + handshake TCP)

| RVA | Función | Rol | Firma |
|-----|---------|-----|-------|
| `0x3df080` | `FUN_1403df080` | **M2XC encrypt** — dos pasadas (keystream+emit+transform2) | `rcx=out_blob, rdx=DATA, r8=KEY` |
| `0x3e94b0` | `FUN_1403e94b0` | **Key hash / M2XC decrypt** | `rcx=out, rdx=input, r8=key` |
| `0x3cf030` | `FUN_1403cf030` | Cipher MurmurHash (alternativa desturple) | — |
| `0x3cf5d0` | `FUN_1403cf5d0` | Helper cipher (usado por send worker TCP) | — |
| `0x232fe0` | `FUN_140232fe0` | **PRNG** — retorna 100 (timestamp fijo) | retorna uint |

**Detalles M2XC** (ver `analysis_frida.md`): blob = `M2XC` + H1(4) + H2(4) + H3(4) + round2. Clave = magic de 64 chars para HTTP; `host+suffix` para TCP.

---

## 4. TCP Game Protocol Layer (socket raw, puerto 443)

| RVA | Función | Rol | Notas |
|-----|---------|-----|-------|
| `0x945f80` | `FUN_140945f80` | **Dispatcher central de mensajes TCP** — lee header 8B, parsea tipo (0x93ab60), descifra M2XC, despacha por opcode, cifra y envía respuesta | worker HXCPP; **mejor punto de hook: ve el mensaje ya descifrado** |
| `0x970050` | `FUN_140970050` | **Send worker** — escribe frames al socket: `[4B restplen][4B origlen][1B checksum][resturple_data]` | `param_2` = objeto de mensaje |
| `0x9703e0` | `FUN_1409703e0` | Wrapper de envío (`*param_3` → `FUN_140970050`) | — |
| `0x965c10` | `FUN_140965c10` | **Constructor de mensajes salientes** — arma array AMF3 `[opcode, data...]`, calcula checksum, llama a send worker | llamada con `0x2731` (10033?) al inicio |
| `0x93ab60` | `FUN_14093ab60` | Parseo de tipo de mensaje | — |
| `0x93ad00` | `FUN_14093ad00` | Helper de cifrado/parseo | — |
| `0x947d50` | `FUN_140947d50` | Parseo de sub-buffer de mensaje | — |
| `0x963990` / `0x977a40` | callers de dispatcher | Callers de FUN_140945f80 (loops de red) | — |

### Flujo TCP (confirmado por docs + Ghidra)
```
Server→Client: [2B BE len][1B flag][payload]   flag=0: AMF3 desturple, flag=1: CLEAR binario
Client→Server: [4B BE restplen][4B BE origlen][1B checksum&0x3F][resturple_data]
Encode: AMF3 → resturple(seed) → frame
Decode: frame → desturple(seed) → AMF3
Seed: MT19937(get_str_key(suffix)) → server_seed = mt.next()%99999 → encoding_seed=0 → tras cada PING avanza
```

---

## 5. UDP Layer (puerto 3724, movimiento en tiempo real)

### Hallazgo Ghidra (verificado 2026-08-02)
**El juego NO usa sendto/recvfrom estáticamente para su UDP.** Análisis de xrefs del binario:

| Import | Callers estáticos | Qué son |
|--------|-------------------|---------|
| `sendto` | `FUN_141b40c70`, `FUN_141b40930`, `FUN_141b41510` | **TODO stack TFTP** ("tftp_send_first", "tftp_rx", "tftp_tx", "netascii/octet/tsize/blksize") — SDK de actualizaciones |
| `recvfrom` | `FUN_141b40720` | TFTP (mismo stack) |
| `send`/`recv` | mbedTLS `0x141b89xxx`, lwIP `FUN_141a721a0`, TFTP | TLS BIO + SDK embebido |

La región `0x141b4xxxx` es **lwIP embebido del SDK** (wrapper `FUN_141a721a0` con buffers circulares en `+0x238/+0x240/+0x280/+0x2a0`, "Send failure: %s"; TFTP en `FUN_141b40c70/141b40930/141b41510`). No es el juego.

**Consecuencia**: el UDP del juego se resuelve dinámicamente (GetProcAddress — ya cubierto por el hook de GetProcAddress del DLL `capture_all_v18.c`) o usa `connect()+send()` en socket DGRAM. Los hooks IAT de `sendto`/`recvfrom` SEGUEN SIENDO el punto de captura correcto (la evidencia previa: "UDP hooks funcionan, pero no hay tráfico UDP en el lobby" — solo aparece en partida).

| Función | Rol | Firma x64 |
|---------|-----|-----------|
| `ws2_32!sendto` | Envío UDP | `rcx=socket, rdx=buf, r8=len, r9=flags, [rsp+0x28]=sockaddr*` |
| `ws2_32!recvfrom` | Recepción UDP | `rcx=socket, rdx=buf, r8=len, r9=flags, [rsp+0x28]=sockaddr*` |

### Formato de paquete UDP (de TCP_PROTOCOL.md §15)
```
[prefix: 9B][seq: 4B BE][opcode: 3B][data...]
prefix = [0x80|random_7bit][8B alfanumérico aleatorio]
opcode 0x012731 INIT  → 24B padding
opcode 0x002726 MOVE  → float32 x, float32 angle, float32 power + 8B tail
```
Binding: servidor manda OP_CONFIRM_UDP (51) por TCP → cliente responde OP_CLIENT_CONFIRM_UDP (10039).

---

## 6. Tabla de Opcodes TCP (Cliente → Servidor)

| Opcode | Nombre | Formato AMF3 | Riesgo |
|--------|--------|--------------|--------|
| 10000 | READY | `[10000,[true,W,H,aspect,true]]` | safe |
| 10001 | PONG | `[10001, ts_ms]` | safe (avanza seed MT) |
| 10002 | CLIENT_ENTITIES_INFO | `[10002,[0]]` | safe |
| 10005 | CLIENT_MOVE | CLEAR `[x,y,power]` | safe |
| 10006 | CLICK | `[10006,x,y,btn]` | safe |
| 10009 | FOCUS | `[10009,target]` | safe |
| 10014 | ABILITY_USE | `[10014,id,x,y]` | safe |
| 10016 | USE_ITEM | `[10016,slot]` | safe |
| 10018 | CHAT_MESSAGE | `[10018,msg]` | safe |
| 10020 | DISCONNECT | `[10020,null]` | KILLS |
| 10022 | MOVE | CLEAR `[x,y,power]` | safe (más usado) |
| 10024 | JUMP | `[10024]` | safe |
| 10025 | DASH | `[10025,angle,power]` | safe |
| 10028 | WEAPON_ATTACK | `[10028,weapon,angle,power]` | DANGER |
| 10030 | EQUIP | `[10030,slot]` | safe |
| 10035 | SECURE_PROOF | `[10035,proof]` | safe |
| 10039 | CONFIRM_UDP | `[10039,...]` | safe |

---

## 7. Estrategia de Hook Frida (todas las capas, desencriptado)

| Capa | Hook | Qué captura |
|------|------|-------------|
| TLS | `base+0x1b86490` (ssl_decrypt_buf) | HTTP/JSON **plaintext** antes de M2XC |
| M2XC | `base+0x3df080` (encrypt) / `base+0x3e94b0` (decrypt) | Datos **antes/después** de cifrar: JSON, keys |
| HTTP | `base+0xafee00` (url_builder) + `base+0xae7690` (http_sender) | URLs y bodies |
| TCP dispatcher | `base+0x945f80` | Mensajes TCP **ya descifrados** (entrantes y salientes) |
| TCP send | `base+0x970050` / `base+0x965c10` | Frames salientes (opcode + AMF3) |
| UDP | `ws2_32!sendto` / `recvfrom` | Paquetes UDP crudos |

**Ventaja clave**: hookear `0x945f80` y `0x3df080` da el contenido **ya descifrado** — no hace falta reimplementar desturple/AMF3 en Frida para capturar.
