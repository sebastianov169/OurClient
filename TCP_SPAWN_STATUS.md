# TCP Spawn Client — Current Status

## What Works
1. Login (KNOCK → LIM → EH) — 100% working
2. API calls (play, gamemode, connect) — 100% working
3. TCP connect to server:443 — working
4. Suffix extraction — working
5. Auth frame (AES-CBC + AMF3 + resturple) — server accepts
6. Player ID received — working
7. READY sent — server responds with CLEAR frames
8. httpPlay (play + gamemode API) — working
9. NATIVE_PLAY sent — working
10. Ping/pong exchange — working for first 2 pings via SEED_FIX
11. UDP init — working

## BLOCKER: No Position Data Received

After NATIVE_PLAY, the server either:
- **With httpPlay**: sends NO frames at all for 120+ seconds
- **Without httpPlay**: sends pings (decoded via SEED_FIX) + null frames, but NO position (opcode 20)

### Root Cause Analysis

The seed divergence issue (server uses different seeds than our MT) is partially solved by SEED_FIX (brute-force mod256). But even with SEED_FIX keeping pings alive, the server never sends position data.

**Possible explanations:**
1. Position data comes as flag=1 CLEAR frames (binary protocol, not AMF3) — we skip these
2. Server requires a specific client action before sending position
3. Server protocol has changed since the C++ reference was written
4. The CLEAR frame processing (AS3 `packetClearReceived`) is needed but not implemented

### The CLEAR Frame Clue

After READY, the server sends two large CLEAR frames:
- 6651 bytes (likely game state/map data)
- ~300 bytes (likely config)

These are flag=1 frames that the AS3 code processes via `packetClearReceived`. The C++ port skips them. But the AS3 code likely extracts player position from these binary frames.

**Next step: Parse the CLEAR frames to extract position data.**

## Files
- `tcp_full.py` — Main client (needs CLEAR frame parsing)
- `TCP_SPAWN_STATUS.md` — This file
- `full_login_and_api.py` — HTTP client (working)
- `m2xc_exact.py` — M2XC (working)

## Key Protocol Details

### TCP Frame Format
- SEND: `[4B BE: resturple_len][4B BE: orig_len][1B: checksum][resturple_data]`
- RECV: `[2B: length][1B: flag][payload]`
  - flag=0: AMF3 (desturple + decode)
  - flag=1: Binary (CLEAR, contains game state)

### Auth Frame
- `token + ";;::===ext:239;;::===mode:<mode>"`
- AES-CBC with key = host + suffix (128-byte pad)

### Seed Issue
- Server uses different seed than our MersenneTwister after first ping
- SEED_FIX (brute-force all 256 mod values) partially solves decoding
- Server's seed algorithm unknown — may not use MT at all
