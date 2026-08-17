# TCP Protocol Investigation Plan

## Executive Summary

The TCP protocol has 3 critical unknowns:
1. **Server greeting parsing** - How the 131-byte greeting is processed to derive session state
2. **First message format** - The exact wire format of the client's first TCP message (suffix + encrypted blob)
3. **Subsequent message framing** - Whether later messages use text-format (`000000NN` + base64) or raw binary

**Root cause of Python TCP failure**: The `tcp_test.py` uses wrong frame format. Ghidra shows the game uses `FUN_140970050` which constructs messages via Haxe runtime buffers, NOT the simple 4-byte-LE format we assumed.

---

## Phase 1: Ghidra Analysis (Priority - Do First)

### 1A. Decompile FUN_140945f80 - Protocol Negotiation Handler
**Address**: `0x140945f80` (1020 lines)
**Purpose**: Main TCP protocol state machine. Handles server greeting, derives keys, builds handshake.

**Critical section** (when `param_1 + 0x38 == 0`, i.e., first call = greeting received):
```
Line ~860-900 (offset ~860):
- FUN_141841210(local_af0, &local_a08)  // Parse raw TCP data
- FUN_14093ab60(param_1, local_970)      // Process parsed response
- FUN_1403e94b0(local_320, uVar12, local_950)  // Key derivation from server data
- FUN_1412fb950(local_720, pvVar10, uVar12)    // Create connection state
- FUN_1412fa0b0(*puVar11, &local_b90)          // Get result object
```

**Action**: Decompile and understand:
- What `FUN_141841210` does with raw TCP bytes (greeting parser)
- What fields are extracted from the greeting (server version, session ID, capabilities)
- How `FUN_14093ab60` processes the parsed greeting
- What data flows into `FUN_1403e94b0` for key derivation

### 1B. Decompile FUN_14093ab60 - Greeting Processor
**Purpose**: Processes the parsed server greeting to extract session parameters.

**Action**: Full decompile. Look for:
- Session ID extraction
- Server capability flags
- Version negotiation
- Any server-provided salt/key material

### 1C. Decompile FUN_141841210 - Raw TCP Data Parser
**Purpose**: Parses raw TCP bytes into structured data.

**Action**: Full decompile. Look for:
- Length-prefix parsing (the 4-byte headers)
- Message type extraction
- How the 131-byte greeting is structured internally

### 1D. Decompile FUN_1412fb950 and FUN_1412fa0b0 - Connection State
**Purpose**: Creates and accesses the TCP connection state object.

**Action**: Full decompile. Look for:
- What fields are stored (server version, protocol version, capabilities)
- How the handshake data is assembled

### 1E. Decompile FUN_140970050 - TCP Message Sender (Full)
**Address**: `0x140970050` (148 lines)
**Purpose**: Sends messages over TCP. This is the KEY function for understanding wire format.

**Action**: Decompile lines 100-148. Look for:
- How the message buffer is constructed
- Whether it uses 4-byte BE length prefix or something else
- How suffix is prepended to first message
- The exact byte layout of sent messages

### 1F. Decompile FUN_1409644c0 - Message Type Dispatcher
**Address**: `0x1409644c0` (39 lines)
**Purpose**: Routes messages by type. Calls `FUN_1409639d0` for types 0x2724 and 5.

**Action**: Understand:
- What message types exist
- How type 0x2724 relates to TCP
- What type 5 is (gameplay messages?)

### 1G. Decompile FUN_14096dc40 - Feature Negotiation
**Called from**: FUN_140965c10 with code 0x2731
**Purpose**: Sends feature/capability negotiation after greeting.

**Action**: Understand what features are negotiated and how.

---

## Phase 2: Frida Capture (After Ghidra Analysis)

### Problem: Frida Crashes After ~1 Second
The current `frida_capture_tcp.js` hooks M2XC at `0x3df080` which triggers anti-tamper.

### Solution: Minimal Hook Strategy

**Strategy 1: Socket-only capture (SAFE)**
- Hook ONLY `ws2_32.dll` functions: `connect`, `send`, `WSASend`, `recv`, `WSARecv`
- Do NOT hook M2XC or any game code
- Capture raw bytes before encryption (game-side) and after (network-side)
- This is 100% safe - no code modification

**Strategy 2: Memory-read-only monitoring (SAFE)**
- After login, scan specific memory regions for the TCP key string (contains `.mitos.is`)
- Read the suffix from memory at known offsets
- No hooks needed, just periodic memory reads

**Strategy 3: Call-site hook (MODERATE RISK)**
- Instead of hooking M2XC directly, hook at specific CALL sites
- The game has integrity checks at the function prologue
- Hooking AFTER the call returns (at the instruction following CALL) is safer

### Frida Script: `frida_tcp_safe.js`

```javascript
// MINIMAL TCP capture - socket hooks only, no game code hooks
'use strict';

var mod = Process.findModuleByName('MitosisOG.exe');
if (!mod) { console.log('[!] Module not found'); return; }
console.log('[OK] base=' + mod.base + ' size=' + mod.size);

// Track game server sockets
var gameSockets = {};
var msgCount = 0;

function parseSockaddr(addr) {
    var family = addr.readU16();
    if (family === 2) {
        var port = (addr.add(2).readU8() << 8) | addr.add(3).readU8();
        var ip = [4,5,6,7].map(function(i){return addr.add(i).readU8();}).join(".");
        return {family: family, ip: ip, port: port};
    }
    return null;
}

// Hook connect
var connectAddr = Module.findExportByName('ws2_32.dll', 'connect');
Interceptor.attach(connectAddr, {
    onEnter: function(args) {
        this.info = parseSockaddr(args[1]);
        this.fd = args[0].toInt32();
    },
    onLeave: function(retval) {
        if (this.info && this.info.ip) {
            var isGame = this.info.ip.startsWith('45.') || this.info.ip.startsWith('216.');
            if (isGame) {
                gameSockets[this.fd] = this.info;
                console.log('\n[CONNECT] GAME SERVER: ' + this.info.ip + ':' + this.info.port + ' fd=' + this.fd);
            }
        }
    }
});

// Hook send
var sendAddr = Module.findExportByName('ws2_32.dll', 'send');
Interceptor.attach(sendAddr, {
    onEnter: function(args) {
        this.fd = args[0].toInt32();
        this.buf = args[1];
        this.len = args[2].toInt32();
    },
    onLeave: function(retval) {
        if (!gameSockets[this.fd]) return;
        var sent = retval.toInt32();
        if (sent <= 0) return;
        var data = this.buf.readByteArray(Math.min(sent, 4096));
        var hex = Array.from(new Uint8Array(data)).map(function(b){return ('0'+b.toString(16)).slice(-2);}).join(' ');
        console.log('\n[SEND] fd=' + this.fd + ' len=' + sent);
        console.log('  hex: ' + hex);
        // Check for suffix (first 8 bytes of first game message)
        if (sent >= 8) {
            var arr = new Uint8Array(data);
            var suffix = '';
            for (var i = 0; i < 8; i++) suffix += String.fromCharCode(arr[i]);
            if (/^[a-zA-Z0-9]{8}$/.test(suffix)) {
                console.log('  SUFFIX: ' + suffix);
                console.log('  M2XC KEY: ' + gameSockets[this.fd].ip + suffix);
            }
        }
        msgCount++;
    }
});

// Hook recv
var recvAddr = Module.findExportByName('ws2_32.dll', 'recv');
Interceptor.attach(recvAddr, {
    onEnter: function(args) {
        this.fd = args[0].toInt32();
        this.buf = args[1];
    },
    onLeave: function(retval) {
        if (!gameSockets[this.fd]) return;
        var n = retval.toInt32();
        if (n <= 0) return;
        var data = this.buf.readByteArray(Math.min(n, 4096));
        var hex = Array.from(new Uint8Array(data)).map(function(b){return ('0'+b.toString(16)).slice(-2);}).join(' ');
        console.log('\n[RECV] fd=' + this.fd + ' len=' + n);
        console.log('  hex: ' + hex);
        // Check for M2XC magic
        if (n >= 4) {
            var arr = new Uint8Array(data);
            if (arr[0] === 0x4D && arr[1] === 0x32 && arr[2] === 0x58 && arr[3] === 0x43) {
                console.log('  M2XC BLOB detected!');
            }
        }
        msgCount++;
    }
});

console.log('[*] Safe TCP capture active. No game code hooks.');
```

### Usage:
```bash
frida -f MitosisOG.exe -l frida_tcp_safe.js --no-pause
```

---

## Phase 3: Python TCP Client (After Capturing Real Traffic)

### Current Issues in tcp_test.py:
1. **Wrong frame format**: Uses `struct.pack('<I', len(msg))` but game may use different framing
2. **Missing greeting processing**: Doesn't parse the 131-byte greeting at all
3. **Wrong message structure**: Assumes simple format but game uses Haxe runtime buffers

### What to Fix After Ghidra Analysis:

Based on what we learn from Phase 1, update the TCP client:

1. **Greeting parser**: Parse the 131-byte server greeting to extract session parameters
2. **First message builder**: Construct the exact byte format from FUN_140970050
3. **Response parser**: Handle the server's response format (text vs binary)
4. **Message loop**: Send game actions and parse responses

### Expected Corrections (from Ghidra + Frida analysis):

**SERVER FORMAT** (from TCP_PROTOCOL_INVESTIGATION.md):
```
Greeting (131 bytes): [2B BE: type=0x0080] [2B BE: ???=0x0039] [127B payload]
Regular response:     [2B BE: type] [2B BE: ???] [payload_bytes]
```

Message types observed:
- 0x0080 = Greeting (131 bytes total)
- 0x0010 = Regular response
- 0x0018 = Another response type
- 0x0034 = Another response type

**CLIENT FORMAT** (from Frida capture):
```
First message:  [4B BE: N+1] [4B BE: N] [2B prefix] [suffix(8B)] [M2XC blob]
Subsequent:     [4B BE: N+1] [4B BE: N] [2B prefix] [M2XC blob]
```

Where N = encrypted_payload_length, and N+1 = total_encrypted_length.

**CRITICAL**: The current `tcp_test.py` uses `struct.pack('<I', len)` (4-byte LE) but the game uses 4-byte **BE** (big-endian). This is the most likely reason for connection failure.

**CORRECTED tcp_test.py format**:
```python
# WRONG (current):
header = struct.pack('<I', len(first_msg))  # LE length

# CORRECT:
total_len = len(m2xc_blob) + 8 + 2 + 4 + 4  # suffix + 2B prefix + 2x4B headers
header = struct.pack('>I', total_len)         # BE total length
header += struct.pack('>I', len(m2xc_blob))   # BE payload length
header += struct.pack('>H', 0x2066)           # 2B type/prefix
msg = header + suffix.encode('ascii') + m2xc_blob
```

---

## Execution Checklist

### Step 1: Ghidra Analysis (DONE - Key findings above)
- [x] FUN_1409639d0 (TCP encryption wrapper) - 57 lines, calls M2XC
- [x] FUN_1403e94b0 (key derivation) - 848 lines, complex Haxe logic
- [x] FUN_140945f80 (protocol handler) - 1020 lines, state machine
- [x] FUN_140970050 (TCP sender) - 148 lines, writes to Haxe buffer
- [x] FUN_14093ab60 (checksum) - 59 lines, XOR 0xef8 hash
- [x] FUN_140170af0 (Haxe socket write) - 47 lines, buffer write
- [x] FUN_14016f690 (Haxe socket flush) - 76 lines, calls ws2_32.send

### Step 2: Frida Capture (DO NEXT)
- [ ] Use `frida_tcp_safe.js` (socket-only hooks, NO game code hooks)
- [ ] Start game, login, let it connect to TCP server
- [ ] Capture first 10 messages sent/received
- [ ] Save hex dumps to `tcp_capture_<date>.txt`

### Step 3: Wire Format Analysis
- [ ] Parse server greeting (131 bytes, type 0x0080)
- [ ] Identify client first message format (suffix + M2XC blob)
- [ ] Verify 4-byte BE length prefix
- [ ] Identify message type/prefix field

### Step 4: Python TCP Client
- [ ] Fix frame format (4-byte BE, not LE)
- [ ] Add greeting parser
- [ ] Fix first message construction
- [ ] Test against live server
- [ ] Send test actions (news, inventory, chat)

---

## Key Functions Reference

| Function | Address | Lines | Purpose |
|----------|---------|-------|---------|
| FUN_140945f80 | 0x140945f80 | 1020 | Protocol negotiation state machine |
| FUN_1409639d0 | 0x1409639d0 | 57 | TCP encryption wrapper (calls M2XC) |
| FUN_1409644c0 | 0x1409644c0 | 39 | Message type dispatcher |
| FUN_140970050 | 0x140970050 | 148 | TCP message sender (writes to Haxe buffer) |
| FUN_1403e94b0 | 0x1403e94b0 | 848 | Key derivation (magic -> key) |
| FUN_1403df080 | 0x1403df080 | - | M2XC encrypt |
| FUN_14093ab60 | 0x14093ab60 | 59 | Checksum/hash (XOR 0xef8) |
| FUN_140170af0 | 0x140170af0 | 47 | Haxe socket write (writes to output buffer) |
| FUN_14016f690 | 0x14016f690 | 76 | Haxe socket flush (calls ws2_32.send) |
| FUN_1404069b0 | 0x1404069b0 | 28 | Buffer write helper |
| FUN_140405a00 | 0x140405a00 | 18 | Buffer reset |
| FUN_1404073c0 | 0x1404073c0 | ? | Buffer ensure capacity |

### Data Flow (FUN_140970050):
```
1. FUN_140405a00(buffer)          // Reset output buffer
2. pbVar8 = FUN_1400281e0(...)    // Get buffer pointer
3. *pbVar8 = bVar2 & 0x3f        // Write type/flags byte (1 byte)
4. FUN_140170af0(header)          // Write header data
5. FUN_140170af0(payload)         // Write payload (M2XC blob)
6. FUN_14016f690(socket)          // Flush buffer to ws2_32.send
```

**CRITICAL INSIGHT**: The game uses Haxe's `sys.net.Socket` which has its own internal buffering. The wire format is determined by what bytes are written to the buffer before flushing. The first byte is a type/flags byte (`bVar2 & 0x3f`), NOT a 4-byte length prefix.

---

## Known Protocol Details (Confirmed)

| Aspect | Value |
|--------|-------|
| Transport | Raw TCP port 443, NO TLS |
| Encryption | M2XC (custom two-pass cipher) |
| TCP Key | server_hostname + 8_byte_suffix |
| Suffix | Client-generated, 8 alphanumeric chars |
| Suffix transmission | First 8 bytes of first TCP message (PLAINTEXT) |
| Handshake data | token + ";;::===ext:495;;::===mode:63" |
| Server greeting | 131 bytes, starts with 0x00 0x80 |
| Message content | M2XC-encrypted JSON |
| Nonce per message | H1/H2 in M2XC header (time-based) |
| Key lifetime | Per-connection (new suffix each connect) |
| Forward secrecy | None |

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Frida crashes game | Use socket-only hooks (no game code) |
| Wrong frame format | Ghidra analysis first, then capture |
| Server rejects connection | Capture real traffic first, then replicate |
| Anti-debug detection | Socket hooks don't trigger detection |
| Rate limiting | Use slow, manual testing |

## Expected Outcomes

### After Step 2 (Frida Capture):
- Complete hex dump of first TCP conversation (greeting + handshake + response)
- Confirmed server greeting format
- Confirmed client first message format
- Suffix and M2XC key captured

### After Step 3 (Analysis):
- Documented wire protocol with exact byte layouts
- Understanding of greeting fields (server version, session ID, capabilities)
- Understanding of handshake fields (ext, mode, token)

### After Step 4 (Python Client):
- Working TCP client that connects to game server
- Can send/receive M2XC-encrypted JSON messages
- Can send game actions (news, inventory, chat)
- Can receive and decrypt server responses

## Success Criteria
1. Python client connects to game server
2. Server accepts handshake (no disconnect)
3. Can send `{"do":"news"}` and receive JSON response
4. Can send `{"do":"inventory","ingame":true,"slot":3}` and receive inventory data
5. Can send chat messages and receive responses

## Files to Create
1. `frida_tcp_safe.js` - Safe Frida capture script (socket-only)
2. `tcp_capture_<date>.txt` - Raw hex dumps from Frida
3. `tcp_protocol_v2.py` - Updated Python client with correct wire format
