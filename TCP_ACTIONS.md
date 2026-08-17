# MitosisOG TCP Actions - Complete Client Opcode Reference

## Account: dhihghkajlk | 1266 coins | 80 equipment items

---

## Client Opcode Table (Client → Server)

All client opcodes are AMF3-encoded arrays unless marked as CLEAR.
Frame format: `[4B BE restplen][4B BE origlen][1B checksum][resturple_data]`

### Core Session Opcodes

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10000 | READY | `[10000, [true, screenW, screenH, aspect, true]]` | YES | Client ready signal. Sent after AUTH. Default: 2560x1440, aspect 1.333 |
| 10001 | PONG | `[10001, timestamp_ms]` | YES | Reply to server PING. Must advance encoding_seed via MT. |
| 10002 | CLIENT_ENTITIES_INFO | `[10002, [0]]` | YES | Request entity info dump from server. Safe to send anytime. |
| 10020 | DISCONNECT | `[10020, null]` | KILLS | Graceful disconnect. Server closes connection. |
| 10034 | CLEAR_FRAME | Empty CLEAR frame (no data) | YES | Keepalive/padding. Used between other frames. |
| 10035 | SECURE_PROOF | `[10035, proof_string]` | YES | TPM attestation proof. Sent after SECURE_CHALLENGE. |
| 10037 | CLIENT_EQUIPMENT_DATA | `[10037, [...equipment_array...]]` | YES | Equipment configuration data. |
| 10038 | REQUEST_CHANGE_NONCE | `[10038, reason]` | SAFE | Request nonce rotation from server. |
| 10039 | CONFIRM_UDP | `[10039, ...]` | SAFE | Confirm UDP binding with server. |

### Movement Opcodes (CLEAR frames - no AMF3)

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10005 | CLIENT_MOVE | CLEAR: `[x:f32, y:f32, power:f32]` | YES | Full movement with position + power |
| 10022 | MOVE | CLEAR: `[x:f32, y:f32, power:f32]` | YES | Standard position update. Most used movement frame. |
| 10030 | MOVE_LOOK_AT | CLEAR: `[targetX:f32, targetY:f32]` | SAFE | Move while looking at target position |

### Combat Opcodes

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10006 | CLICK | `[10006, x, y, button]` | SAFE | Click event at screen coordinates |
| 10009 | FOCUS | `[10009, target_id]` | SAFE | Focus/target an entity |
| 10011 | BEGIN_SHOOTING | `[10011, ...]` | DANGER | Start shooting. May trigger server anti-cheat. |
| 10012 | END_SHOOTING | `[10012]` | SAFE | Stop shooting |
| 10028 | WEAPON_ATTACK | `[10028, weapon_id, angle, power]` | DANGER | Attack with weapon. Requires active weapon. |
| 10029 | BEGIN_SHOOTING_RADIANS | `[10029, angle_radians, ...]` | DANGER | Start shooting with radian angle |

### Entity Interaction Opcodes

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10004 | ENTITY_COMMAND | `[10004, entity_id, command, ...]` | SAFE | Send command to entity |
| 10007 | ROAD | `[10007, ...]` | SAFE | Set path/road for entity |
| 10008 | CLEAR_ROAD | `[10008]` | SAFE | Clear current path |
| 10010 | DOUBLE_TAP | `[10010, target_id]` | SAFE | Double-tap interaction |

### Inventory & Items

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10016 | USE_ITEM | `[10016, slot_id]` | SAFE | Use item from inventory slot |
| 10017 | TOGGLE_BAN | `[10017, target_id]` | SAFE | Toggle ban on player |

### Social Opcodes

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10013 | REQUEST_INVITE | `[10013, ...]` | SAFE | Request room invite |
| 10014 | REFRESH_INVITE | `[10014, ...]` | SAFE | Refresh invite data |
| 10015 | RELEASE_INVITE | `[10015]` | SAFE | Release/deny invite |
| 10018 | CHAT_MESSAGE | `[10018, message_string]` | YES | Send chat message |
| 10019 | REPORT_ABUSE | `[10019, target_id, reason]` | SAFE | Report player abuse |

### Player & Character

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10020 | PLAYER_UPDATE | `[10020, ...]` | SAFE | Update player data |
| 10021 | TEST_MERSENNE | `[10021, test_value]` | SAFE | MT19937 verification test |
| 10023 | CALL_PET | `[10023]` | SAFE | Call/summon pet |
| 10024 | SET_PARENTAL | `[10024, ...]` | SAFE | Set parental controls |

### Movement Special

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10025 | MOVE_SHORT | `[10025, x, y]` | SAFE | Short-form movement (2 floats) |
| 10030 | MOVE_LOOK_AT | CLEAR: `[targetX, targetY]` | SAFE | Move to look at position |

### Speed & Control

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10026 | BEGIN_SPEEDUP | `[10026, ...]` | SAFE | Begin speed boost |
| 10027 | END_SPEEDUP | `[10027]` | SAFE | End speed boost |
| 10028 | BEGIN_CTRL | `[10028, ...]` | SAFE | Begin control mode |
| 10029 | END_CTRL | `[10029]` | SAFE | End control mode |

### Viewport

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10031 | CONTROL_SETUP | `[10031, ...]` | SAFE | Setup control configuration |
| 10032 | RESIZE_FRUSTRUM | `[10032, width, height]` | SAFE | Resize viewport/camera |

### UDP

| Opcode | Name | Format | Safe? | Description |
|--------|------|--------|-------|-------------|
| 10033 | CONFIRM_UDP | `[10033, ...]` | SAFE | Confirm UDP availability |
| 10034 | UDP_NOT_AVAILABLE | Empty CLEAR | SAFE | Signal UDP not available |

---

## Server Opcode Table (Server → Client)

| Opcode | Name | Format | Description |
|--------|------|--------|-------------|
| 1 | PING | `[1, timestamp, counter]` | Server ping. Client MUST reply with 10001. |
| 2 | LAG | `[2, ...]` | Lag measurement |
| 3 | LOAD | `[3, ...]` | Initial game state / world data |
| 4 | PLAYER_ID | `[4, player_id, timestamp]` | Assigns client player ID |
| 5 | BEGIN | `[5, ...]` | Game session start signal |
| 6 | MAP | `[6, ...]` | Map data |
| 7 | ENTITIES_INFO | `[7, ...]` | Entity information update |
| 8 | EVENT | `[8, ...]` | Game events |
| 9 | ENTITY_EVENT | `[9, ...]` | Entity-specific events |
| 10 | ERROR | `[10, error_code, message]` | Error messages |
| 11 | PLAYER_STATUS | `[11, ...]` | Player status updates (name, stats) |
| 12 | ENTITIES_STATUS | `[12, ...]` | Bulk entity status |
| 13 | FRAME | `[13, ...]` | Game frame data (positions, states) |
| 14 | ROAD | `[14, ...]` | Path/road data |
| 15 | ENTITY | `[15, ...]` | Single entity update |
| 16 | PLAYER_UPDATE | `[16, ...]` | Player property update |
| 17 | TEAM_GAME_ENDED | `[17, ...]` | Team game end notification |
| 18 | INVITE_CODE | `[18, ...]` | Room invite code |
| 19 | CHART_DATA | `[19, [[x,y],[w,h]], timestamp]` | Leaderboard/chart coordinates |
| 20 | CAMERA_POSITION | `[20, [x,y,z], timestamp]` | Camera/spawn position |
| 21 | EARN_COINS | `[21, delta_amount, ...]` | Coin delta (INCREMENTAL, not total) |
| 22 | WIN_WITHIN | `[22, seconds]` | Win countdown |
| 24 | EXPERIENCE_GAIN | `[24, xp_amount]` | XP gain notification |
| 32 | MESSAGE | `[32, message_text]` | Server message |
| 33 | UPDATE_NEWS | `[33, ...]` | News/feed update |
| 35 | CHAT_MESSAGE | `[35, message, sender]` | Chat message with sender name |
| 36 | MATCH_STARTED | `[36, ...]` | Match start notification |
| 40 | CONNECTION_RESUME_KEY | `[40, 'key', timestamp]` | Reconnection token |
| 51 | CONFIRM_UDP | `[51, ...]` | UDP binding confirmation |
| 52 | SECURE_CHALLENGE | `[52, 'hex_blob', 0]` | Auth challenge blob |
| 53 | SECURE_NONCE | `[53, nonce_data, timestamp]` | New nonce delivery |
| 54 | CHANGE_NONCE | `[54, new_nonce, reason]` | Nonce rotation |

---

## CLEAR Frame Format

Binary frames (flag=1) used for high-frequency data:

```
[4B BE: body_length] [4B BE: body_length] [1B: 0x40] [payload...]
```

For AMF3-encoded CLEAR frames (MOVE):
```
[4B BE: body_length] [4B BE: body_length] [1B: 0x40] [4B BE: clear_opcode] [float32 data...]
```

### Known CLEAR Opcodes

| Opcode | Name | Data |
|--------|------|------|
| 10005 | CLIENT_MOVE | 3x float32 (x, y, power) |
| 10022 | MOVE | 3x float32 (x, y, power) |
| 10030 | MOVE_LOOK_AT | 2x float32 (targetX, targetY) |
| 10034 | PADDING | Empty |

---

## Safety Classification

### SAFE to test (no session impact):
- 10000 (READY) - already sent during normal flow
- 10001 (PONG) - already sent during normal flow
- 10002 (CLIENT_ENTITIES_INFO) - already sent during normal flow
- 10018 (CHAT_MESSAGE) - sends chat, server may broadcast
- 10034 (CLEAR_FRAME) - empty padding, always safe
- 10035 (SECURE_PROOF) - sent during auth flow
- 10037 (CLIENT_EQUIPMENT_DATA) - equipment config

### REQUIRES specific game state:
- 10004 (ENTITY_COMMAND) - needs valid entity_id
- 10006 (CLICK) - needs valid coordinates
- 10007 (ROAD) - needs path data
- 10009 (FOCUS) - needs valid target_id
- 10016 (USE_ITEM) - needs valid slot_id
- 10028 (WEAPON_ATTACK) - needs active weapon
- 10029 (BEGIN_SHOOTING_RADIANS) - needs weapon state

### DANGER (may trigger anti-cheat or kick):
- 10011 (BEGIN_SHOOTING) - shooting without weapon
- 10028 (WEAPON_ATTACK) - attack without valid context
- 10029 (BEGIN_SHOOTING_RADIANS) - shooting without weapon

### SESSION TERMINATING:
- 10020 (DISCONNECT) - closes connection
