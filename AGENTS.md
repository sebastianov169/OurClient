# AGENTS.md — MitosisOG Reverse Engineering

## What This Repo Is

Reverse engineering of **MitosisOG.exe** (Haxe/OpenFL game). Primary goals:
- Capture and decode HTTP API traffic (app.mitos.is)
- Reverse the TCP game protocol (desturple encoding, AMF3 serialization)
- Reconstruct encryption (M2XC, AES-CBC, TPM attestation)

## Critical Files

| Path | Purpose |
|------|---------|
| `http_json_capture/mitosis_capture_all.cpp` | Main capture DLL (IAT hooks for ws2_32) |
| `http_json_capture/build_unified.bat` | **Build the DLL** — MSVC x64 |
| `http_json_capture/Loader.exe` | C# injector (injects DLL into game) |
| `capture_all/capture_all.c` | Older capture DLL (TCP-focused, MinHook) |
| `tcp_full.py` | Python TCP client with full protocol implementation |
| `mito_client/full_login_and_api.py` | Complete login flow + M2XC encryption |
| `mito_client/tcp_client.py` | TCP client with desturple/AMF3 |
| `mitosis_capture_all.jsonl` | Output log from DLL capture |

## Build & Run

### Build the DLL
```batch
cd http_json_capture
build_unified.bat
```
Requires: Visual Studio 2026 (MSVC vcvars64). Output: `mitosis_capture_all.dll`

### Inject & Capture
```batch
taskkill /F /IM MitosisOG.exe
Loader.exe
:: Wait 15 seconds for login capture
type mitosis_capture_all.jsonl
```

### Frida Alternative
```powershell
$p = (Get-Process -Name "MitosisOG").Id
frida -p $p -l "http_json_capture\frida_capture_all.js"
```

### Frida Scripts Available
| Script | Purpose |
|--------|---------|
| `frida_capture_all.js` | TLS decrypted + HTTP + JSON capture |
| `frida_m2xc_hook.js` | M2XC encrypt/decrypt capture |
| `frida_scan_json.js` | Memory scanner for HTTP/JSON patterns |

### x64dbg
Use the x64dbg MCP tools for live debugging sessions.

## Mandatory Rules

### 1. systematic-debugging (always)
Before any fix, complete 4 phases:
1. Verify target (RVA, bytes)
2. Verify hook (pattern installed)
3. Verify execution (breakpoint fired)
4. Verify data (valid read)

**No skipping phases. No changing offsets without completing all 4.**

### 2. verification-before-completion (always)
Never say "done" without showing:
- Compiled .dll size
- Build output (0 errors)
- Frida output with hook_count > 0
- JSONL with events > 0
- Hex/ASCII preview of captured data

### 3. writing-plans (complex tasks)
- 2-5 min micro-tasks with exact commands
- Max 10 steps per plan
- Verify each step before proceeding

### 4. stop-slop
No greetings, no apologies, no filler. Show code and evidence only.

## Protocol Quick Reference

- **TCP**: Raw socket port 443, NO TLS after initial handshake
- **Desturple**: XOR + byte-interleave encoding (seed changes on PING)
- **AMF3**: Action Message Format 3 (variable-length ints, string table)
- **M2XC**: Two-pass cipher with fmix2 state mixing
- **AES-CBC**: For TCP auth handshake
- **MT19937**: Seeded from server greeting suffix → encoding seeds
- **Base address**: 0x140000000 (Ghidra), runtime ASLR

## Key Offsets (Binary)

| Offset | Function |
|--------|----------|
| `base + 0x3df080` | M2XC encrypt (FUN_1403df080) |
| `base + 0x3e94b0` | Key hash (FUN_1403e94b0) |
| `0x1eb6d00` | `_currentCoins` field |
| `0x1dc7fcc` | `get_username()` |
| `0x1dc69e8` | OP_ string table start |

## DLL Hook Architecture

### What Works ✅
- **IAT hooks for ws2_32**: send, recv, connect, closesocket, sendto, recvfrom
- **GetProcAddress interception**: Catches late-bound ws2_32 resolution
- **Game stability**: IAT hooks don't crash the game

### What Doesn't Work ❌
- **INT3 breakpoints**: Game detects and crashes (anti-debug)
- **Inline hooks (code patching)**: Game detects and crashes
- **VEH handler**: Triggers anti-debug detection

### Why Inline Hooks Fail
The game has anti-debugging that detects:
1. INT3 (0xCC) breakpoints in code
2. Code section modifications (VirtualProtect + write)
3. VEH handler installation

### Working Approach
Use **IAT hooking only** (modifies import table, not code):
- Parse PE headers → find ws2_32 imports → patch function pointers
- Hook GetProcAddress to intercept dynamic resolution
- This approach doesn't modify code sections, so anti-debug doesn't trigger

## Skills to Load

- **frida-skills**: For all Frida hooking work (frida-native-hooks, frida-tracing-discovery, frida-troubleshooting)
- **reverse-engineering-assistant**: For Ghidra analysis (deep-analysis, binary-triage, pyghidra-scripting)

## Score System (Data Quality)

Score >= 90: HTTP_JSON_PLAINTEXT | 40-89: CANDIDATE | < 40: NOT_PLAINTEXT

Top markers: `loginifneeded`(+80), `deviceid`(+70), `wh/hk/dk/dm`(+65), `HTTP/1.1`(+60), `application/json`(+55)

## Frida Hook Status

| Hook | Status | Evidence |
|------|--------|----------|
| mbedTLS ssl_decrypt_buf | ✅ Working | Captures decrypted TLS records |
| mbedTLS ssl_read_record_layer | ✅ Working | Captures TLS records |
| M2XC encrypt (0x3df080) | ✅ Working | Captures encrypted data |
| M2XC decrypt (0x3e94b0) | ✅ Working | Captures decrypted data |
| ws2_32 recv/send | ✅ Working | Via DLL IAT hooks |
| Heap scanner | ✅ Working | Scans for HTTP/JSON patterns |

### Key Findings
1. **IAT hooks work** - DLL captures TCP traffic without crashing
2. **Frida hooks work** - Can hook mbedTLS and M2XC functions
3. **Data is encrypted** - HTTP API responses are M2XC-encrypted after TLS decryption
4. **Game idle** - No API calls captured during idle session
5. **Anti-debug** - Game detects INT3 breakpoints and inline hooks

### Next Steps for 100%
1. Hook at **Haxe HTTP client layer** (higher than mbedTLS)
2. Hook **JSON parser** after M2XC decryption
3. Use **Frida Stalker** to trace data flow
4. Capture **login flow** (requires game to make API calls)

## Anti-Debug Analysis

### What We Found
The game has **sophisticated anti-debug** that detects:
1. **PEB patching** - Even when patched before game starts
2. **Function hooking** - IAT hooks work, but inline hooks crash
3. **DLL injection** - Some injection methods trigger detection
4. **INT3 breakpoints** - Game detects and crashes
5. **VEH handler** - Triggers detection

### What Works
- **IAT hooking only** - Modifies import table, not code sections
- **Frida Interceptor** - Doesn't trigger anti-debug (different mechanism)
- **antidebug_bypass.dll v8** - Dynamic INT3 scanner + DebugBreak hook + IAT hooks + memory spoofing

### What Doesn't Work
- **PEB.BeingDebugged patching** - Detected by game
- **NtGlobalFlag patching** - Detected by game
- **Inline hooks (code patching)** - Detected by game
- **INT3 breakpoints** - Detected by game
- **Hardcoded INT3 RVAs** - Only 2/13 matched at runtime (replaced with dynamic scanner)

### Why Anti-Debug Bypass DLLs Crash
The game detects:
1. PEB modifications (BeingDebugged, NtGlobalFlag)
2. Function prologue modifications (VirtualProtect + write)
3. DLL injection patterns

### Root Cause: HXCPP Thread Registration
MinHook's internal thread is NOT registered with HXCPP's GC allocator.
When MinHook calls ws2_32 functions, the game's wrapper functions check
if the current thread is registered with HXCPP. If not → INT3 → CRASH.

v8 fix: Dynamic INT3 scanner finds ALL assertion INT3s (0xCC bytes
preceded by conditional jumps) in the game's .text section and NOPs them.

## Capture System Status

| Component | Status | Evidence |
|-----------|--------|----------|
| DLL IAT hooks (ws2_32) | ✅ 100% | 6 functions patched, game stable |
| MinHook inline hooks | ✅ 100% | 14 ws2_32 functions hooked (v8 anti-debug) |
| Frida mbedTLS hooks | ✅ 100% | ssl_decrypt_buf, ssl_read_record_layer |
| Frida M2XC hooks | ✅ 100% | encrypt/decrypt functions |
| Frida Haxe hooks | ✅ 100% | url_builder, http_sender, http_response |
| TLS handshake capture | ✅ 100% | Google Trust Services, mitos.is certs |
| TLS encrypted data | ✅ 100% | 700+ events captured |
| Game stability | ✅ 100% | Game runs with DLL IAT hooks + MinHook |
| Anti-debug bypass | ✅ 100% | v8: dynamic INT3 scanner + 5 more layers |

### What's Missing for 100%
1. **Login flow capture** - Game must make API calls (currently idle)
2. **JSON API responses** - Need to hook after M2XC decryption
3. **M2XC decrypted data** - Hook works but output is binary

### Key Insight
The game is **idle** after login. To capture JSON API responses:
1. Restart game fresh
2. Capture first 5-10 seconds (login flow)
3. Hook at Haxe layer where JSON is parsed

## Secret Redaction

For reports: token→[REDACTED_TOKEN], dk→[REDACTED_DK], dm→[REDACTED_DM], deviceid→[REDACTED_DEVICEID], uid→[REDACTED_UID]

## Loop Protocol

```
TRY → FAIL → 4-phase debug → REPEAT
```

Only break the loop with: correct offset/RVA, score >= 40, JSONL evidence, DLL compiled clean.
Never break with: "not found", "try manually", "function doesn't exist".
