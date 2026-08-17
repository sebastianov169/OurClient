# MitosisOG TCP Protocol - Complete Reverse Engineering Documentation

## Executive Summary

MitosisOG uses a custom TCP-based game protocol with:
- **Desturple** encoding (XOR + byte-shuffle) for frame encryption
- **AMF3** (Action Message Format 3) for data serialization
- **Mersenne Twister (MT19937)** for encoding seed generation
- **AES-CBC** for TCP authentication handshake
- Raw TCP on port 443 (no TLS — M2XC provides encryption layer)
- UDP on port 3724 for real-time movement

---

## 1. TCP Frame Format

### Server → Client
```
[2B BE: payload_length] [1B: flag] [payload_length bytes: payload]
```

| Flag | Type | Description |
|------|------|-------------|
| 0 | AMF3 | Desturple-encoded AMF3 data |
| 1 | CLEAR | Raw binary (entity dumps, position updates) |
| Other | Unknown | Reserved for future use |

### Client → Server
```
[4B BE: restplen] [4B BE: original_len] [1B: checksum & 0x3F] [resturple_data]
```

Where:
- `restplen = original_len + 1` (always 1 more than original)
- `checksum = (get_byte_key(payload) & 0x3F + 8) & 0x3F`
- `resturple_data` = resturple-encoded AMF3 payload

---

## 2. Desturple Encoding

Desturple is a two-step encoding: **XOR shuffle** then **byte interleave**.

### Decode (desturple): `data → decoded`
1. XOR each byte: `v3[i] = data[i] ^ ((seed + i*i + (seed+i) % 16) % 256)`
2. Split `v3` into left/right halves
3. Interleave based on `parity = seed % 2`:
   - Walk from center outward (low/high pointers)
   - Swap a,b based on `parity ^ side`
4. Output = `left + right` (+ odd byte if length is odd)

### Encode (resturple): `decoded → data`
Reverse of desturple. Used by client for outgoing frames.

### Seed Selection
The encoding seed changes throughout the session:
- **Auth/READY frames**: seed = 0
- **After PING**: seed = `mt.next_val() % 99999`

---

## 3. Mersenne Twister (MT19937) Seed Management

### Initialization
```
str_key = get_str_key(suffix)    # suffix from server greeting
mt = MersenneTwister(str_key)
server_seed = mt.next_val() % 99999
encoding_seed = 0                 # starts at 0
```

### Seed Progression
```
On each PING (opcode=1):
    encoding_seed = mt.next_val() % 99999
```

### `get_str_key` Algorithm
```python
def get_str_key(text):
    value = 0
    for i in range(len(text)):
        value += (ord(text[i]) * (i * 2 - 1)) ^ 0x0EF8
    return value & 0xFFFFFFFF
```

### Decode Seed Candidates (in order of priority)
1. `0` — always try first
2. `server_seed` — from MT initialization
3. `encoding_seed` — current encoding seed
4. `mt.next_val() % 99999` — try next 10 MT values

---

## 4. AMF3 Serialization

AMF3 markers:
| Marker | Type |
|--------|------|
| 0x00 | undefined |
| 0x01 | null |
| 0x02 | false |
| 0x03 | true |
| 0x04 | integer (U29) |
| 0x05 | double (8B big-endian) |
| 0x06 | string (U29 length + UTF-8) |
| 0x08 | object |
| 0x09 | array |

### U29 Encoding
Variable-length integer, max 4 bytes:
```
< 0x80:        1 byte
< 0x4000:      2 bytes  [1nnnnnnn] [0nnnnnnn]
< 0x200000:    3 bytes
else:          4 bytes  [1nnnnnnn] [1nnnnnnn] [1nnnnnnn] [nnnnnnnn]
```

---

## 5. Server Opcodes (Server → Client)

| Opcode | Name | Data Format | Description |
|--------|------|-------------|-------------|
| 1 | PING | `[1, timestamp]` | Server ping, client replies with OP=10001 |
| 2 | LAG | `[2, ...]` | Lag measurement |
| 3 | LOAD | `[3, ...]` | Initial game state / world data |
| 4 | PLAYER_ID | `[4, player_id, timestamp]` | Assigns client player ID |
| 5 | BEGIN | `[5, ...]` | Game session start signal |
| 6 | MAP | `[6, ...]` | Map data |
| 7 | ENTITIES_INFO | `[7, ...]` | Entity information update |
| 8 | EVENT | `[8, ...]` | Game events |
| 9 | ENTITY_EVENT | `[9, ...]` | Entity-specific events |
| 10 | ERROR | `[10, ...]` | Error messages |
| 11 | PLAYER_STATUS | `[11, ...]` | Player status updates (name, stats) |
| 12 | ENTITIES_STATUS | `[12, ...]` | Bulk entity status |
| 13 | FRAME | `[13, ...]` | Game frame data (positions, states) |
| 14 | ROAD | `[14, ...]` | Path/road data |
| 15 | ENTITY | `[15, ...]` | Single entity update |
| 16 | PLAYER_UPDATE | `[16, ...]` | Player property update |
| 17 | TEAM_GAME_ENDED | `[17, ...]` | Team game end notification |
| 18 | INVITE_CODE | `[18, ...]` | Room invite code |
| 19 | CHART_DATA | `[19, ...]` | Chart/statistics data |
| 20 | CAMERA_POSITION | `[20, ...]` | Camera/spawn position |
| **21** | **EARN_COINS** | **`[21, delta_amount, ...]`** | **Coin delta (INCREMENTAL, not total)** |
| 22 | WIN_WITHIN | `[22, ...]` | Win countdown |
| 24 | EXPERIENCE_GAIN | `[24, ...]` | XP gain notification |
| 32 | MESSAGE | `[32, ...]` | Server message |
| 33 | UPDATE_NEWS | `[33, ...]` | News/feed update |
| 35 | CHAT_MESSAGE | `[35, message, sender]` | Chat message with sender name |
| 36 | MATCH_STARTED | `[36, ...]` | Match start notification |
| 40 | CONNECTION_RESUME_KEY | `[40, ...]` | Reconnection key |
| 52 | SECURE_CHALLENGE | `[52, ...]` | Auth challenge/blob |

---

## 6. Client Opcodes (Client → Server)

| Opcode | Name | Data Format | Description |
|--------|------|-------------|-------------|
| 10000 | READY | `[10000, [true, screenW, screenH, aspect, true]]` | Client ready signal |
| 10001 | PONG | `[10001, timestamp]` | Reply to PING |
| 10002 | CLIENT_ENTITIES_INFO | `[10002, [0]]` | Request entity info |
| 10005 | CLIENT_MOVE | `[10005, ...]` | Movement request |
| 10006 | CLIENT_CLICK | `[10006, x, y, button]` | Click event |
| 10014 | ABILITY_USE | `[10014, ability_id, x, y]` | Use ability |
| 10015 | WEAPON_FIRE | `[10015]` | Fire weapon |
| 10016 | USE_ITEM | `[10016, slot]` | Use item in slot |
| 10017 | ITEM_USE | `[10017, slot]` | Use item (alt) |
| 10018 | CHAT_SEND | `[10018, message]` | Send chat message |
| 10019 | INTERACT | `[10019, target_id, type]` | Interact with entity |
| 10020 | DISCONNECT | `[10020, null]` | Graceful disconnect |
| 10022 | MOVE | Clear frame: `[x, y, power]` | Position update |
| 10024 | JUMP | `[10024]` | Jump action |
| 10025 | DASH | `[10025, angle, power]` | Dash action |
| 10028 | WEAPON_ATTACK | `[10028, weapon_id, angle, power]` | Attack with weapon |
| 10030 | EQUIP | `[10030, slot]` | Equip item |
| 10031 | UNEQUIP | `[10031, slot]` | Unequip item |
| 10034 | CLEAR_FRAME | Empty clear frame | Keepalive/padding |
| 10035 | SECURE_PROOF | `[10035, proof_data]` | Security attestation |
| 10037 | EQUIPMENT_DATA | `[10037, [...]]` | Equipment configuration |

---

## 7. CLEAR Frames (Flag=1)

Binary frames sent alongside AMF3 frames. Used for high-frequency data.

### CLEAR Frame Format
```
[4B BE: body_length] [4B BE: body_length] [1B: 0x40] [4B BE: clear_opcode] [data...]
```

### Known CLEAR Opcodes
| Opcode | Name | Data |
|--------|------|------|
| 10022 | MOVE | 3x float32 (x, y, power) |
| 10034 | PADDING | Empty |

---

## 8. Entity System

### Entity Types
| ID | Type | Description |
|----|------|-------------|
| 0 | FOOD | Collectible food items |
| 1 | PLAYER | Player entities |
| 2 | VIRUS | Virus entities |
| 3 | MASS | Mass entities |
| 4 | COIN | Coin entities |
| 5 | FLAGBASE | CTF flag bases |
| 6 | CHEST | Treasure chests |

### Position Encoding (fp12.12)
3-byte fixed-point: `value = raw_24bit / 4096.0`

### Entity Dump Format
- Prefix byte: `0x64`
- 19-byte records: `[04 00 08 00][type:1B][counter:2B][entity_id:2B BE][sep:1B][sub_hdr:5B][value:4B]`
- Entity IDs are 16-bit big-endian

---

## 9. TCP Connection Flow

### Phase 0: HTTP API Authentication
```
1. GET /engine_beta.php?do=knock  → token
2. GET /engine_beta.php?do=lim    → sk (session key), rk (RSA public key)
3. GET /engine_beta.php?do=eh     → authentication complete
4. POST /engine_beta.php?do=connect → server:port + tcp_token
```

### Phase 1: TCP Connection
```
5. TCP connect to server:443 (NO TLS)
6. Client generates 8-byte random suffix
7. Send: AES-CBC_Encrypt(token + ";;::===ext:239;;::===mode:3", key=host+suffix)
8. Wrapped in AMF3 string, resturple-encoded, sent as first frame
```

### Phase 2: Server Greeting
```
9. Server sends AMF3 string containing suffix (last 8 bytes)
10. Client derives: str_key = get_str_key(suffix)
11. Client initializes: MT19937(str_key) → server_seed = mt.next() % 99999
12. encoding_seed = 0
```

### Phase 3: Auth Response
```
13. Client sends AUTH frame (AES-encrypted token + mode)
14. Server responds with PLAYER_ID (opcode=4)
15. Server may send SECURE_CHALLENGE (opcode=52)
```

### Phase 4: Ready
```
16. Client sends READY (opcode=10000) with screen dimensions
17. Client sends CLEAR_10034 padding
18. HTTP API: do=play, do=gamemode
19. Client sends NATIVE_PLAY (opcode=5)
20. Server sends game state (LOAD, MAP, ENTITIES_INFO, etc.)
```

### Phase 5: Gameplay
```
21. Client sends MOVE (CLEAR), PING (AMF3) for keepalive
22. Server sends PING → client advances encoding_seed, replies PONG
23. Server sends EARN_COINS (opcode=21) when coins change
24. Server sends CHAT_MESSAGE (opcode=35) for chat
25. Server sends FRAME (opcode=13) for entity updates
```

---

## 10. Coin System

### OP_EARN_COINS (opcode=21) — INCREMENTAL
```
[21, delta_amount, ...]
```
This is NOT the total balance. It's a **delta** — the amount earned/spent.

### Total Coin Balance
The total coin count is accumulated **client-side** from deltas.
The server never sends the absolute total via TCP.

### Finding the Balance
1. **Initial balance**: Might come in LOAD (opcode=3) or PLAYER_STATUS (opcode=11)
2. **During play**: Accumulated from EARN_COINS deltas
3. **HTTP API**: `do=stats` returns `previous_user` but NOT coin count
4. **Memory**: Game stores `_currentCoins` at offset `0x1eb6d00` (string reference)

### Known Coin Values
- Account has **1266 coins** (verified via HTTP API)
- Previous known value: **766 coins** (earlier session)

---

## 11. Username System

### Where Username Appears
1. **TCP CHAT_MESSAGE (opcode=35)**: `[35, message, sender_name]`
2. **TCP PLAYER_STATUS (opcode=11)**: May contain name field
3. **HTTP API**: `do=stats` → `previous_user` field
4. **Binary**: `get_username()` function at offset `0x1dc7fcc`

### Username Detection
The username is stored in the player object and returned by `get_username()`.
The player object pointer can be captured via Frida hook on `get_username`.

---

## 12. Encryption Layers

### Layer 1: Desturple (TCP frames)
- XOR + byte shuffle with seed
- Seed managed by MT19937
- Changes after each PING

### Layer 2: AES-CBC (TCP auth only)
- Key derived from `host + suffix` via `derive_aes_key()`
- Fixed IV: `20 0b 5d 31 79 6f 03 2c 13 23 3b 65 54 3a 0b 5f`
- Used only for initial handshake

### Layer 3: M2XC (HTTP API)
- Custom two-pass cipher (transform1 + transform2)
- Key: 64-byte random `magic` string
- Seeds H1, H2 embedded in blob header
- Used for all HTTP API communication

### Layer 4: v5OH2 (HTTP responses)
- AES-CBC with `aes_key(magic)` derivation
- Used for some HTTP API responses
- IV: same as TCP AES

---

## 13. MurmurHash2

Used as alternative decode method when desturple fails:
```c
uint32_t murmurhash2(const void* key, int len, uint32_t seed) {
    const uint32_t m = 0x5bd1e995;
    const int r = 24;
    uint32_t h = seed ^ len;
    while (len >= 4) { k *= m; k ^= k >> r; k *= m; h *= m; h ^= k; }
    h ^= h >> 13; h *= m; h ^= h >> 15;
    return h;
}
```
Decode: `out[i] = data[i] ^ (murmurhash2(&i, 4, seed) & 0xFF)`

---

## 14. Binary Offsets (MitosisOG.exe)

| Offset | Function | Description |
|--------|----------|-------------|
| `0x3df080` | `FUN_1403df080` | M2XC encrypt/decrypt |
| `0x3e94b0` | `FUN_1403e94b0` | KeyHash derivation |
| `0x1dc7fcc` | `get_username` | Returns player username |
| `0x1eb6d00` | `_currentCoins` string | String constant for field name |
| `0xa84b30` | `FUN_140a84b30` | HTTP request builder |
| `0xa80160` | `FUN_140a80160` | TPM proof wrapper |
| `0xa80080` | `FUN_140a80080` | Token storage |
| `0xae7690` | `FUN_140ae7690` | HTTP send function |

---

## 15. UDP Protocol

### Packet Format
```
[prefix: 9B] [seq: 4B BE] [opcode: 3B] [data...]
```

### Prefix
```
[0x80 | random_7bit] [8B random alphanumeric]
```

### Known UDP Opcodes
| Opcode | Name | Data |
|--------|------|------|
| 0x012731 | INIT | 24 bytes padding |
| 0x002726 | MOVE | float32 x, float32 angle, float32 power + 8B tail |

---

## 16. Server Addresses

| Server | IP | Purpose |
|--------|-----|---------|
| s.mitos.is | 172.67.15.80 | HTTP API (Cloudflare) |
| app.mitos.is | 172.67.151.80 | Game API |
| s18271.mitos.is | 216.128.143.188 | Game server (EU) |
| s18388.mitos.is | 45.32.206.109 | Game server |
| chat server | 178.63.30.69 | Chat |

---

## 17. Frame Decode Order (Priority)

When decoding a server frame, try these seeds in order:
1. `seed = 0` — always first
2. `seed = server_seed` — from MT init
3. `seed = encoding_seed` — current session seed
4. `seed = mt.next() % 99999` — try next 10 values
5. `murmurhash2(seed=100)` — fallback method
6. `brute force 0-255` — last resort

---

## 18. Key Security Findings

1. **Suffix sent in plaintext**: First 8 bytes of TCP connection
2. **No TLS**: Raw TCP on port 443
3. **MT19937 is deterministic**: Once suffix known, all future seeds predictable
4. **No forward secrecy**: Same key for entire session
5. **AES key derivation is weak**: Simple additive mixing
6. **Coin balance is incremental**: Server never sends total
7. **Username in chat frames**: Sender name is plaintext AMF3 string
