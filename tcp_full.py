#!/usr/bin/env python3
"""
MitosisOG Spawn Client - COMPLETE TRAFFIC CAPTURE + ACTION TOOLKIT
Full decode of ALL TCP/UDP frames, verbose logging, and action functions.
"""

import socket, struct, time, random, json, hashlib, base64, sys, os, math, threading
import importlib.util, requests, urllib.parse, warnings

warnings.filterwarnings('ignore')

script_dir = os.path.dirname(os.path.abspath(__file__))
spec_api = importlib.util.spec_from_file_location("api_full", os.path.join(script_dir, "full_login_and_api.py"))
api_full = importlib.util.module_from_spec(spec_api)
spec_api.loader.exec_module(api_full)

eb = api_full.eb
rndx_fn = api_full.rndx
m2xc_encrypt_full = api_full.m2xc_encrypt_full
m2xc_decrypt_full = api_full.m2xc_decrypt_full
m2xc_fmt = api_full.m2xc_fmt
parse_m2xc_blob = api_full.parse_m2xc_blob
build_dtf = api_full.build_dtf
build_proof = api_full.build_proof
build_mid = api_full.build_mid
str_dest = api_full.str_dest
load_attest_key = api_full.load_attest_key
load_device_id = api_full.load_device_id
decrypt_v5oh2 = api_full.decrypt_v5oh2

ENGINE = "https://app.mitos.is/engine_beta.php"
VER = "10.1.8"
CHARSET = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM0123456789"
M = 0xFFFFFFFF
DESKTOP = "ASUSTeK COMPUTER INC.;1.0;Microsoft Windows 11 Enterprise LTSC;Windows;10.0.26100;x86;1920;1080"

REGIONS = ["europe", "australia", "central_america", "south_america"]
MODES = [("FFA", 0, 1)]

# ================================================================
# TRAFFIC LOGGER
# ================================================================
class TrafficLogger:
    def __init__(self, logfile=None):
        self.logfile = logfile or os.path.join(script_dir, "traffic_capture.log")
        self.counter = 0
        self.lock = threading.Lock()
        self.packets = []
        self._header()
        # opcode catalog (nombres REALES del binario via Ghidra, ver PROTOCOLO_OPCODES.md)
        self.opcode_names = {
            1: "OP_PING", 2: "TIME_SYNC", 3: "KEEPALIVE", 4: "OP_PLAYERID",
            5: "OP_BEGIN", 6: "ENTITY_CREATE", 7: "ENTITY_DESTROY",
            8: "ENTITY_UPDATE", 9: "HEALTH", 10: "ENTITY_DATA",
            11: "DAMAGE", 12: "SCORE", 13: "KILL", 14: "DEATH",
            15: "RESPAWN", 16: "ENTITY_LIST", 17: "TEAM",
            18: "INVENTORY", 19: "POSITION", 20: "OP_ENTITIES_INFO",
            21: "VELOCITY", 22: "ROTATION", 23: "ANIMATION",
            24: "EFFECT", 25: "SOUND", 26: "PARTICLE",
            27: "WEAPON", 28: "ITEM", 29: "PICKUP",
            30: "DROP", 31: "USE", 32: "EQUIP",
            33: "UNEQUIP", 34: "ABILITIES", 35: "OP_CHAT_MESSAGE",
            36: "COMMAND", 37: "OP_EVENT", 38: "NOTIFICATION",
            39: "UI_UPDATE", 40: "OP_CONFIRM_UDP", 41: "REGION_INFO",
            42: "PLAYER_LIST", 43: "LEADERBOARD", 44: "SETTINGS",
            45: "OP_MAP", 46: "OBJECTIVE", 47: "ROUND",
            48: "MATCH", 49: "REPLAY", 50: "SPECTATE",
            51: "MODERATION", 52: "OP_SECURE_NONCE", 53: "CAPTCHA",
            54: "BATTLE_PASS", 55: "DAILY_REWARD", 56: "ACHIEVEMENT",
            57: "FRIEND", 58: "PARTY", 59: "CLAN",
            60: "LEADERBOARD_GLOBAL", 61: "SEASON", 62: "REWARD",
            63: "SHOP", 64: "PURCHASE", 65: "CRAFT",
            66: "TRADE", 67: "MAIL", 68: "OP_CLIENT_REPORT_ABUSE",
            69: "BAN", 70: "MOTD", 71: "PATCH",
            72: "VERSION", 73: "HEARTBEAT", 74: "SYNC",
            75: "TELEPORT", 76: "WARP", 77: "SPAWN",
            78: "DESPAWN", 79: "TRANSFORM", 80: "SCALE",
            81: "OPACITY", 82: "COLOR", 83: "NAME",
            84: "TITLE", 85: "AVATAR", 86: "OP_CLIENT_EMOTE",
            87: "GESTURE", 88: "ACTION", 89: "EMOTE_LIST",
            90: "REACTION", 91: "VOICE", 92: "TIP",
            93: "DONATION", 94: "VOTE", 95: "POLL",
            96: "QUIZ", 97: "MINIGAME", 98: "TUTORIAL",
            99: "HELP", 100: "DEBUG",
            10000: "OP_CLIENT_READY", 10001: "OP_CLIENT_PING_REPLY", 10002: "TIME_REQUEST",
            10010: "MOVE_REQUEST", 10011: "LOOK_REQUEST",
            10012: "JUMP_REQUEST", 10013: "DASH_REQUEST",
            10014: "ABILITY_USE", 10015: "WEAPON_FIRE",
            10016: "WEAPON_RELOAD", 10017: "ITEM_USE",
            10018: "ITEM_DROP", 10019: "INTERACT",
            10020: "DISCONNECT", 10021: "RECONNECT",
            10022: "OP_CLIENT_MOVE", 10023: "LOOK",
            10024: "JUMP", 10025: "DASH",
            10026: "ABILITY_ACTIVATE", 10027: "ABILITY_DEACTIVATE",
            10028: "WEAPON_ATTACK", 10029: "WEAPON_SPECIAL",
            10030: "ITEM_EQUIP", 10031: "ITEM_UNEQUIP",
            10032: "INTERACT_OBJECT", 10033: "INTERACT_NPC",
            10034: "OP_CLIENT_CLEAR_ROAD", 10035: "PING_RESPONSE",
            10036: "LATENCY", 10037: "SYNC_REQUEST",
            10038: "POSITION_UPDATE", 10039: "ROTATION_UPDATE",
            10040: "VELOCITY_UPDATE", 10041: "SCALE_UPDATE",
            10042: "NAME_UPDATE", 10043: "TITLE_UPDATE",
            10044: "AVATAR_UPDATE", 10045: "STATUS_UPDATE",
            10046: "TEAM_UPDATE", 10047: "SCORE_UPDATE",
            10048: "HEALTH_UPDATE", 10049: "ENERGY_UPDATE",
            10050: "INVENTORY_UPDATE", 10051: "EQUIPMENT_UPDATE",
            10052: "QUEST_UPDATE", 10053: "OBJECTIVE_UPDATE",
            10054: "ACHIEVEMENT_UPDATE", 10055: "STATS_UPDATE",
            10056: "CHAT_MESSAGE", 10057: "SYSTEM_MESSAGE",
            10058: "EMOTE_SEND", 10059: "VOICE_SEND",
        }

    def _header(self):
        with open(self.logfile, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("  MitosisOG Traffic Capture - %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            f.write("=" * 80 + "\n\n")

    def log(self, msg):
        ts = time.strftime("%H:%M:%S.") + "%03d" % (time.time() * 1000 % 1000)
        line = "[%s] %s" % (ts, msg)
        with self.lock:
            self.counter += 1
            try:
                print(line, flush=True)
            except:
                print(line.encode('ascii', errors='replace').decode('ascii'), flush=True)
            try:
                with open(self.logfile, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except:
                pass

    def log_hex(self, direction, data, label=""):
        hex_str = data.hex() if data else ""
        if len(hex_str) > 200:
            hex_str = hex_str[:200] + "..."
        self.log("  %s %s [%d bytes] %s" % (direction, label, len(data) if data else 0, hex_str))

    def log_frame(self, direction, opcode, values, raw_bytes=None, sock_id=0, seed=None, extra=""):
        name = self.opcode_names.get(opcode, "OP_%d" % opcode)
        seed_info = " seed=%d" % seed if seed is not None else ""
        val_repr = repr(values)[:200] if values else "None"
        self.log("  %s [%s] OP=%d (%s)%s sock=%d %s" % (
            direction, name, opcode, val_repr, seed_info, sock_id, extra))
        if raw_bytes:
            self.log_hex(direction, raw_bytes, "RAW")

    def log_udp(self, direction, data, addr="", opcode=None):
        hex_str = data.hex() if data else ""
        if len(hex_str) > 160:
            hex_str = hex_str[:160] + "..."
        op_info = " OP=%d" % opcode if opcode is not None else ""
        self.log("  %s UDP [%d bytes] to=%s%s %s" % (
            direction, len(data) if data else 0, addr, op_info, hex_str))

    def save_packet(self, direction, protocol, data, decoded=None, opcode=None, addr=None):
        with self.lock:
            entry = {
                "time": time.time(),
                "dir": direction,
                "proto": protocol,
                "raw": data.hex() if data else "",
                "decoded": decoded,
                "opcode": opcode,
                "addr": addr,
            }
            self.packets.append(entry)


# Global traffic logger
TL = TrafficLogger()

# ================================================================
# AES-CBC
# ================================================================
IV = bytes([0x20, 0x0b, 0x5d, 0x31, 0x79, 0x6f, 0x03, 0x2c,
            0x13, 0x23, 0x3b, 0x65, 0x54, 0x3a, 0x0b, 0x5f])

def derive_aes_key(secret):
    values = [11] * 16
    for i in range(len(secret)):
        slot = i % 16
        values[slot] += ord(secret[slot]) + ord(secret[i])
    return bytes(v & 0xFF for v in values)

def aes_cbc_crypt(data, key, encrypt=True):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    cipher = Cipher(algorithms.AES(key), modes.CBC(IV))
    if encrypt:
        return cipher.encryptor().update(data) + cipher.encryptor().finalize()
    return cipher.decryptor().update(data) + cipher.decryptor().finalize()

def aes_encrypt_tcp(payload, secret, pad_to=128):
    raw = payload.encode('ascii')
    pad = (pad_to - (len(raw) % pad_to)) % pad_to
    padded = raw + b'\x00' * pad
    key = derive_aes_key(secret)
    encrypted = aes_cbc_crypt(padded, key, True)
    return "%08d%s" % (len(padded), base64.b64encode(encrypted).decode('ascii'))

# ================================================================
# MersenneTwister
# ================================================================
class MersenneTwister:
    def __init__(self, seed):
        self.mt = [0] * 624
        self.index = 624
        self.mt[0] = seed & 0xFFFFFFFF
        for i in range(1, 624):
            x = self.mt[i-1] ^ (self.mt[i-1] >> 30)
            self.mt[i] = ((((x & 0xFFFF0000) >> 16) * 1812433253) << 16) & 0xFFFFFFFF
            self.mt[i] = (self.mt[i] + (x & 0xFFFF) * 1812433253 + i) & 0xFFFFFFFF

    def next_val(self):
        if self.index >= 624:
            for i in range(624):
                y = (self.mt[i] & 0x80000000) | (self.mt[(i+1) % 624] & 0x7FFFFFFF)
                self.mt[i] = self.mt[(i+397) % 624] ^ (y >> 1)
                if y & 1:
                    self.mt[i] = (self.mt[i] ^ 0x9908B0DF) & 0xFFFFFFFF
            self.index = 0
        y = self.mt[self.index]
        self.index += 1
        y ^= y >> 11
        y = (y ^ ((y << 7) & 0x9D2C5680)) & 0xFFFFFFFF
        y = (y ^ ((y << 15) & 0xEFC60000)) & 0xFFFFFFFF
        y ^= y >> 18
        return y

def get_str_key(text):
    value = 0
    for i in range(len(text)):
        value += (ord(text[i]) * (i * 2 - 1)) ^ 0x0EF8
    return value & 0xFFFFFFFF

def get_byte_key(data):
    total = 0
    for i in range(len(data)):
        b = data[i]
        sb = b if b < 128 else b - 256
        total += (sb * (i * 2 - 1)) ^ 0x0EF8
    return total

# ================================================================
# Desturple / Resturple
# ================================================================
def bytearray_resturple(decoded, seed):
    n = len(decoded)
    if n == 0: return b''
    half = n // 2
    parity = seed % 2
    left = list(decoded[:half])
    right = list(decoded[half:])
    v3 = [0] * n
    side = 0
    low = half // 2
    high = half // 2
    for i in range(half):
        if not side:
            index = 2 * low - 2
            low -= 1
        else:
            index = 2 * high
            high += 1
        a = left[i]
        b = right[half - 1 - i]
        if not (parity ^ side):
            a, b = b, a
        v3[index] = a
        v3[index + 1] = b
        side ^= 1
    if n % 2 != 0:
        v3[-1] = decoded[-1]
    out = bytearray(n)
    for i in range(n):
        out[i] = (v3[i] ^ ((seed + i * i + (seed + i) % 16) % 256)) & 0xFF
    return bytes(out)

def bytearray_desturple(data, seed):
    n = len(data)
    if n == 0: return b''
    half = n // 2
    parity = seed % 2
    v3 = bytearray(n)
    for i in range(n):
        v3[i] = data[i] ^ ((seed + i * i + (seed + i) % 16) % 256) & 0xFF
    left = bytearray()
    right = bytearray()
    side = 0
    low = half // 2
    high = half // 2
    for i in range(half):
        if not side:
            index = 2 * low - 2
            low -= 1
        else:
            index = 2 * high
            high += 1
        a = v3[index]
        b = v3[index + 1]
        if not (parity ^ side):
            a, b = b, a
        left.append(a)
        right.insert(0, b)
        side ^= 1
    out = left + right
    if n % 2 != 0:
        out += bytes([v3[-1]])
    return bytes(out)

# ================================================================
# AMF3 Encoder/Decoder
# ================================================================
def write_u29(value):
    value &= 0x1FFFFFFF
    if value < 0x80: return bytes([value])
    if value < 0x4000: return bytes([(value >> 7) | 0x80, value & 0x7F])
    if value < 0x200000: return bytes([(value >> 14) | 0x80, ((value >> 7) & 0x7F) | 0x80, value & 0x7F])
    return bytes([(value >> 22) | 0x80, ((value >> 15) & 0x7F) | 0x80, ((value >> 8) & 0x7F) | 0x80, value & 0xFF])

def amf_string(v):
    d = v.encode('utf-8')
    return b'\x06' + write_u29((len(d) << 1) | 1) + d

def amf_int(v):
    return b'\x04' + write_u29(v & 0x1FFFFFFF)

def amf_double(v):
    return b'\x05' + struct.pack('>d', v)

def amf_bool(v):
    return b'\x03' if v else b'\x02'

def amf_null():
    return b'\x01'

def amf_array(values):
    out = b'\x09' + write_u29((len(values) << 1) | 1) + b'\x01'
    for v in values:
        out += v
    return out

class Amf3Decoder:
    def __init__(self, data):
        self.data = data; self.pos = 0; self.string_refs = []
    def read_u8(self):
        if self.pos >= len(self.data): raise Exception("AMF3 end")
        b = self.data[self.pos]; self.pos += 1; return b
    def read_bytes(self, n):
        out = self.data[self.pos:self.pos+n]; self.pos += n; return out
    def read_u29(self):
        result = 0
        for i in range(4):
            b = self.read_u8()
            if i < 3:
                result = (result << 7) | (b & 0x7F)
                if not (b & 0x80): return result
            else: return (result << 8) | b
        return result
    def read_double(self):
        return struct.unpack('>d', self.read_bytes(8))[0]
    def read_string_data(self):
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.string_refs[idx] if 0 <= idx < len(self.string_refs) else ""
        length = handle >> 1
        if length == 0: return ""
        text = self.read_bytes(length).decode('utf-8', errors='replace')
        self.string_refs.append(text)
        return text
    def read_value(self):
        marker = self.read_u8()
        if marker == 0x00: return "undefined"
        if marker == 0x01: return None
        if marker == 0x02: return False
        if marker == 0x03: return True
        if marker == 0x04:
            v = self.read_u29()
            if v & 0x10000000: v -= 0x20000000
            return v
        if marker == 0x05: return self.read_double()
        if marker == 0x06: return self.read_string_data()
        if marker == 0x09: return self.read_array()
        raise Exception("unsupported AMF3 marker: 0x%02x" % marker)
    def read_array(self):
        handle = self.read_u29()
        if not (handle & 1): return []
        dense_count = handle >> 1
        while True:
            key = self.read_string_data()
            if not key: break
            self.read_value()
        return [self.read_value() for _ in range(dense_count)]

# ================================================================
# Frame builders
# ================================================================
def make_client_frame(amf_payload, original_len, checksum, seed):
    resturple = bytearray_resturple(amf_payload, seed)
    frame = struct.pack('>I', len(resturple)) + struct.pack('>I', original_len)
    frame += bytes([checksum & 0x3F]) + resturple
    return bytes(frame)

def make_auth_frame(host, suffix, token, mode, ext_id=239):
    plain = token + ";;::===ext:%d;;::===mode:%d" % (ext_id, mode)
    encrypted = aes_encrypt_tcp(plain, host + suffix, 128)
    logical = amf_string(encrypted)
    payload = logical + b'\x00'
    checksum = ((get_byte_key(payload) & 0x3F) + 8) & 0x3F
    return make_client_frame(payload, len(logical), checksum, 0)

def make_ping_frame(seed, now_value):
    logical = amf_array([amf_int(10001), amf_double(now_value)])
    payload = logical + b'\x00\x00\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_ready_frame(seed):
    logical = amf_array([
        amf_int(10000),
        amf_array([amf_bool(True), amf_double(2560.0), amf_double(1440.0),
                    amf_double(1.3333333333333333), amf_bool(True)]),
    ])
    payload = logical + b'\x00\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_native_play_frame(seed):
    logical = amf_array([amf_int(5), amf_array([amf_bool(False)])])
    payload = logical + b'\x00\x00\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_disconnect_flush_frame(seed):
    logical = amf_array([amf_int(10020), amf_null()])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_tcp_clear_frame(opcode, floats):
    body_len = 4 + 4 * len(floats)
    frame = struct.pack('>I', body_len) + struct.pack('>I', body_len)
    frame += bytes([0x40]) + struct.pack('>I', opcode)
    for f in floats:
        frame += struct.pack('>f', f)
    return bytes(frame)

def make_move_frame(move_first, angle, power):
    return make_tcp_clear_frame(10022, [move_first, angle, power])

def make_clear_10034_frame():
    return make_tcp_clear_frame(10034, [])


def make_split_frame():
    """Split (dividir celula): opcode 0x271A=10010, NO 10023.
    Validado en vivo (hook 0x96e330, 5 hits al presionar espacio):
    FUN_1407815b0/FUN_140781600 -> FUN_14096e330(socket, 1, 0x271a, [0])
    chan=1 (TCP), sin argumentos. Frame CLEAR estandar [len][len][0x40][10010]."""
    return make_tcp_clear_frame(10010, [])

# ================================================================
# ACTION BUILDERS (Amf3-encoded actions)
# ================================================================
def make_chat_frame(seed, message):
    logical = amf_array([amf_int(35), amf_string(message)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_emote_frame(seed, emote_id):
    logical = amf_array([amf_int(86), amf_int(emote_id)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_interact_frame(seed, target_id, interaction_type=0):
    logical = amf_array([amf_int(10019), amf_int(target_id), amf_int(interaction_type)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_ability_use_frame(seed, ability_id, target_x=0, target_y=0):
    logical = amf_array([amf_int(10014), amf_int(ability_id), amf_double(target_x), amf_double(target_y)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_weapon_attack_frame(seed, weapon_id, angle, power):
    logical = amf_array([amf_int(10028), amf_int(weapon_id), amf_double(angle), amf_double(power)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_item_use_frame(seed, slot):
    logical = amf_array([amf_int(10017), amf_int(slot)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_item_drop_frame(seed, slot):
    logical = amf_array([amf_int(10018), amf_int(slot)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_equip_frame(seed, slot):
    logical = amf_array([amf_int(10030), amf_int(slot)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_unequip_frame(seed, slot):
    logical = amf_array([amf_int(10031), amf_int(slot)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_jump_frame(seed):
    logical = amf_array([amf_int(10024)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_dash_frame(seed, angle, power):
    logical = amf_array([amf_int(10025), amf_double(angle), amf_double(power)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_respawn_frame(seed):
    logical = amf_array([amf_int(10015)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_team_frame(seed, team_id):
    logical = amf_array([amf_int(46), amf_int(team_id)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_buy_frame(seed, item_id, quantity=1):
    logical = amf_array([amf_int(64), amf_int(item_id), amf_int(quantity)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_trade_frame(seed, target_id, offer_items):
    arr = [amf_int(66), amf_int(target_id)]
    for item in offer_items:
        arr.append(amf_int(item))
    logical = amf_array(arr)
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_report_frame(seed, target_id, reason):
    logical = amf_array([amf_int(68), amf_int(target_id), amf_string(reason)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

def make_vote_frame(seed, poll_id, choice):
    logical = amf_array([amf_int(94), amf_int(poll_id), amf_int(choice)])
    payload = logical + b'\x00'
    return make_client_frame(payload, len(logical), seed % 63, seed)

# ================================================================
# UDP
# ================================================================
UDP_PORT = 3724

def make_udp_prefix():
    chars = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM;:_-.,0987654321^"
    return bytes([0x80 | random.randint(0, 0x7F)]) + ''.join(random.choice(chars) for _ in range(8)).encode('ascii')

def make_udp_init_packet(prefix):
    return prefix + bytes.fromhex("00000000012731ffffffff00000000000000000000000000000000")

def make_udp_afk_packet(prefix, seq, move_first, angle, power):
    out = bytearray(prefix)
    out += struct.pack('>I', seq) + bytes.fromhex("002726")
    out += struct.pack('>f', move_first) + struct.pack('>f', angle) + struct.pack('>f', power)
    out += bytes.fromhex("ffffffff00000000")
    return bytes(out)

def make_udp_move_packet(prefix, seq, x, y, angle=0, power=0):
    out = bytearray(prefix)
    out += struct.pack('>I', seq) + bytes.fromhex("002726")
    out += struct.pack('>f', x) + struct.pack('>f', angle) + struct.pack('>f', power)
    out += bytes.fromhex("ffffffff00000000")
    return bytes(out)

def decode_udp_packet(data):
    """Decode a UDP game packet and return info dict."""
    if len(data) < 12:
        return {"type": "unknown", "size": len(data)}
    prefix_len = 9
    if len(data) <= prefix_len:
        return {"type": "prefix_only", "size": len(data), "prefix": data.hex()}
    body = data[prefix_len:]
    if len(body) >= 4:
        seq = struct.unpack('>I', body[0:4])[0]
    else:
        seq = 0
    if len(body) >= 7:
        op_bytes = body[4:7].hex()
        opcode = int(op_bytes, 16)
    else:
        opcode = 0
    decoded = {"type": "game", "seq": seq, "opcode": opcode, "opcode_hex": "0x%06x" % opcode,
               "size": len(data), "body_hex": body.hex()}
    if opcode == 0x012731:
        decoded["type"] = "init"
    elif opcode == 0x002726:
        decoded["type"] = "move"
        if len(body) >= 19:
            x, angle, power = struct.unpack('>fff', body[7:19])
            decoded["x"] = x
            decoded["angle"] = angle
            decoded["power"] = power
    return decoded

# ================================================================
# Position Detection
# ================================================================
def try_extract_position(decoded_bytes):
    if len(decoded_bytes) < 13: return None
    if decoded_bytes[0] != 0x08: return None
    try:
        x = struct.unpack('>f', decoded_bytes[5:9])[0]
        y = struct.unpack('>f', decoded_bytes[9:13])[0]
        if abs(x) < 100000 and abs(y) < 100000 and not math.isnan(x) and not math.isnan(y):
            return (x, y)
    except: pass
    for off in range(1, min(len(decoded_bytes) - 8, 20)):
        try:
            x = struct.unpack('>f', decoded_bytes[off:off+4])[0]
            y = struct.unpack('>f', decoded_bytes[off+4:off+8])[0]
            if 0 < abs(x) < 10000 and abs(y) < 10000 and not math.isnan(x) and not math.isnan(y):
                return (x, y)
        except: pass
    return None

# ================================================================
# TCP helpers
# ================================================================
def recv_frame(sock, timeout=3):
    sock.settimeout(timeout)
    hdr = b''
    while len(hdr) < 3:
        try:
            chunk = sock.recv(3 - len(hdr))
            if not chunk: return None, None, b''
            hdr += chunk
        except socket.timeout:
            return None, None, b''
    length = (hdr[0] << 8) | hdr[1]
    flag = hdr[2]
    payload = b''
    while len(payload) < length:
        try:
            chunk = sock.recv(length - len(payload))
            if not chunk: return length, flag, payload
            payload += chunk
        except socket.timeout:
            return length, flag, payload
    return length, flag, payload

def send_frame(sock, data, log_it=True, label=""):
    try:
        if log_it:
            TL.log_hex("SEND", data, label)
            TL.save_packet("SEND", "TCP", data)
        sock.sendall(data)
    except (ConnectionAbortedError, ConnectionResetError, OSError):
        pass

# ================================================================
# Decode server frame using destpurple with candidate seeds
# ================================================================
def try_decode_destpurple(payload, seeds):
    """Try destpurple with a list of candidate seeds. Return (value, decoded_bytes, seed) or (None, None, None)."""
    for seed in seeds:
        try:
            dec = bytearray_desturple(payload, seed)
            if len(dec) > 0 and dec[0] <= 0x09:
                d = Amf3Decoder(dec)
                v = d.read_value()
                if v is not None:
                    return v, dec, seed
        except:
            pass
    return None, None, None

# ================================================================
# FULL DECODE - try multiple methods
# ================================================================
def full_decode_frame(payload, length, seeds):
    """Decode frame using all known methods. Return (value, decoded, seed_used, method)."""
    flag_guess = 0
    if len(payload) > 0:
        if payload[0] == 0x06 or payload[0] == 0x09 or payload[0] == 0x04:
            flag_guess = 0
        else:
            flag_guess = 0

    # Try desturple with all candidate seeds
    v, dec, seed = try_decode_destpurple(payload, seeds)
    if v is not None:
        return v, dec, seed, "desturple"

    # Try raw (no encoding)
    if len(payload) > 0 and payload[0] <= 0x09:
        try:
            d = Amf3Decoder(payload)
            v = d.read_value()
            if v is not None:
                return v, payload, 0, "raw"
        except:
            pass

    # Try brute force desturple (limited range)
    for s in range(0, 256):
        try:
            dec = bytearray_desturple(payload, s)
            if len(dec) > 0 and dec[0] <= 0x09:
                d = Amf3Decoder(dec)
                v = d.read_value()
                if v is not None:
                    return v, dec, s, "desturple_brute_%d" % s
        except:
            pass

    return None, None, None, "failed"

# ================================================================
# GAME CLIENT STATE
# ================================================================
class GameState:
    def __init__(self):
        self.player_id = -1
        self.position = None
        self.spawned = False
        self.encoding_seed = 0
        self.server_seed = 0
        self.suffix = ""
        self.str_key = 0
        self.mt = None
        self.entity_list = []
        self.entities = {}        # id -> {ts,x,y,z,...} (frames CLEAR)
        self.last_clear = None
        self.chat_log = []
        self.stats = {}
        self.inventory = []
        self.ping_count = 0
        self.move_count = 0
        self.frame_count = 0
        self.sock_id = 0
        self.host = ""
        self.port = 0
        self.udp_seq = 1
        self.udp_prefix = None
        self.running = False

    def advance_seed(self):
        old = self.encoding_seed
        if self.mt:
            self.encoding_seed = self.mt.next_val() % 99999
        TL.log("  SEED: %d -> %d (MT next)" % (old, self.encoding_seed))
        return old, self.encoding_seed

    def get_decode_seeds(self):
        return [0, self.server_seed, self.encoding_seed]

# ================================================================
# ACTION TOOLKIT
# ================================================================
class GameClient:
    def __init__(self, state):
        self.state = state

    def send_chat(self, message):
        TL.log("ACTION: send_chat('%s')" % message[:50])
        frame = make_chat_frame(self.state.encoding_seed, message)
        send_frame(self.state.sock, frame, label="CHAT")

    def send_emote(self, emote_id):
        TL.log("ACTION: send_emote(%d)" % emote_id)
        frame = make_emote_frame(self.state.encoding_seed, emote_id)
        send_frame(self.state.sock, frame, label="EMOTE_%d" % emote_id)

    def move_to(self, x, y, power=0.9309):
        TL.log("ACTION: move_to(%.1f, %.1f)" % (x, y))
        frame = make_move_frame(x, y, power)
        send_frame(self.state.sock, frame, label="MOVE")

    def jump(self):
        TL.log("ACTION: jump")
        frame = make_jump_frame(self.state.encoding_seed)
        send_frame(self.state.sock, frame, label="JUMP")

    def dash(self, angle=0, power=1.0):
        TL.log("ACTION: dash(angle=%.2f, power=%.2f)" % (angle, power))
        frame = make_dash_frame(self.state.encoding_seed, angle, power)
        send_frame(self.state.sock, frame, label="DASH")

    def use_item(self, slot):
        TL.log("ACTION: use_item(%d)" % slot)
        frame = make_item_use_frame(self.state.encoding_seed, slot)
        send_frame(self.state.sock, frame, label="USE_ITEM_%d" % slot)

    def drop_item(self, slot):
        TL.log("ACTION: drop_item(%d)" % slot)
        frame = make_item_drop_frame(self.state.encoding_seed, slot)
        send_frame(self.state.sock, frame, label="DROP_ITEM_%d" % slot)

    def equip(self, slot):
        TL.log("ACTION: equip(%d)" % slot)
        frame = make_equip_frame(self.state.encoding_seed, slot)
        send_frame(self.state.sock, frame, label="EQUIP_%d" % slot)

    def unequip(self, slot):
        TL.log("ACTION: unequip(%d)" % slot)
        frame = make_unequip_frame(self.state.encoding_seed, slot)
        send_frame(self.state.sock, frame, label="UNEQUIP_%d" % slot)

    def attack(self, target_id, weapon_id=0, angle=0, power=1.0):
        TL.log("ACTION: attack(target=%d, weapon=%d)" % (target_id, weapon_id))
        frame = make_weapon_attack_frame(self.state.encoding_seed, weapon_id, angle, power)
        send_frame(self.state.sock, frame, label="ATTACK")

    def use_ability(self, ability_id, target_x=0, target_y=0):
        TL.log("ACTION: use_ability(%d)" % ability_id)
        frame = make_ability_use_frame(self.state.encoding_seed, ability_id, target_x, target_y)
        send_frame(self.state.sock, frame, label="ABILITY_%d" % ability_id)

    def interact(self, target_id, interaction_type=0):
        TL.log("ACTION: interact(target=%d, type=%d)" % (target_id, interaction_type))
        frame = make_interact_frame(self.state.encoding_seed, target_id, interaction_type)
        send_frame(self.state.sock, frame, label="INTERACT")

    def buy_item(self, item_id, quantity=1):
        TL.log("ACTION: buy_item(%d, qty=%d)" % (item_id, quantity))
        frame = make_buy_frame(self.state.encoding_seed, item_id, quantity)
        send_frame(self.state.sock, frame, label="BUY_%d" % item_id)

    def set_team(self, team_id):
        TL.log("ACTION: set_team(%d)" % team_id)
        frame = make_team_frame(self.state.encoding_seed, team_id)
        send_frame(self.state.sock, frame, label="TEAM_%d" % team_id)

    def report(self, target_id, reason=""):
        TL.log("ACTION: report(%d, '%s')" % (target_id, reason))
        frame = make_report_frame(self.state.encoding_seed, target_id, reason)
        send_frame(self.state.sock, frame, label="REPORT")

    def vote(self, poll_id, choice):
        TL.log("ACTION: vote(%d, %d)" % (poll_id, choice))
        frame = make_vote_frame(self.state.encoding_seed, poll_id, choice)
        send_frame(self.state.sock, frame, label="VOTE")

    def respawn(self):
        TL.log("ACTION: respawn")
        frame = make_respawn_frame(self.state.encoding_seed)
        send_frame(self.state.sock, frame, label="RESPAWN")

    def keepalive_move(self, x=34.0, angle=-3.084, power=0.9309):
        frame = make_move_frame(x, angle, power)
        send_frame(self.state.sock, frame, log_it=False)
        self.state.move_count += 1

    def keepalive_ping(self):
        now_value = float(time.time() * 1000)
        frame = make_ping_frame(self.state.encoding_seed, now_value)
        send_frame(self.state.sock, frame, log_it=False)
        self.state.ping_count += 1

    def send_udp_move(self, x=34.0, angle=-3.084, power=0.9309):
        if self.state.udp_sock:
            pkt = make_udp_afk_packet(self.state.udp_prefix, self.state.udp_seq, x, angle, power)
            try:
                self.state.udp_sock.sendto(pkt, (self.state.host, UDP_PORT))
                TL.log_udp("SEND", pkt, "%s:%d" % (self.state.host, UDP_PORT))
                TL.save_packet("SEND", "UDP", pkt)
                self.state.udp_seq += 1
            except Exception as e:
                TL.log("  UDP SEND ERROR: %s" % e)

    def get_player_info(self, player_id):
        TL.log("ACTION: get_player_info(%d) [via chat]" % player_id)
        self.send_chat("/who %d" % player_id)

    def get_stats(self):
        TL.log("ACTION: get_stats [via chat]")
        self.send_chat("/stats")

    def get_inventory(self):
        TL.log("ACTION: get_inventory [via chat]")
        self.send_chat("/inventory")

# ================================================================
# VERBOSE FRAME PROCESSOR
# ================================================================
# ================================================================
# CLEAR FRAME DECODER (flag=1, serializacion binaria custom)
# ================================================================
# Formato real observado: 64 + [00 TT CC V:u32 BE] repetido (7 bytes/par)
#   TT = tipo de dato (01=int, 02, 03, 00), CC = campo
# Campos conocidos (entidad jugador): 0x62=ts, 0x6d=X, 0x79=Y, 0xa7=Z/angulo
CLEAR_FIELD_NAMES = {
    0x62: "ts", 0x6d: "x", 0x79: "y", 0xa7: "z",
    0x0b: "f0xb", 0x68: "f0x68", 0x48: "f0x48",
    0xad: "f0xad", 0x86: "f0x86",
}

def decode_clear_frame(payload):
    """Decodifica frames CLEAR del server (empiezan con 0x64).

    Formato pares: 64 + [00 TT CC V:u32 BE] repetido (7 bytes/par).
    Tambien lista de entidades: 64 04 0008 0001 [id:4] 0001 0004 002c [val:4] ...
    Ver PROTOCOLO_OPCODES.md
    """
    if not payload or payload[0] != 0x64:
        return None
    d = payload
    if len(d) == 1:
        return {"type": "empty"}

    # Lista de entidades: 64 + por entidad [04 00 08 00 01][id:4][0001 0004 002c][val:4]
    # = 19 bytes/entidad, el 04 del primer bloque es el "04" de "64 04".
    # Validado con hex real: 64 04 00 08 00 01 000001c0 00010004002c 1f508178
    # -> id=448, val=525205368/194165=2704.9 (coordenada X)
    if len(d) >= 5 and d[1] == 0x04:
        entities = []
        i = 1
        while i + 19 <= len(d):
            if d[i] == 0x04 and d[i+1] == 0x00 and d[i+2] == 0x08 and d[i+3] == 0x00 and d[i+4] == 0x01:
                ent_id = struct.unpack('>I', d[i+5:i+9])[0]
                val = struct.unpack('>I', d[i+15:i+19])[0]
                entities.append({"id": ent_id, "val": val})
                i += 19
            else:
                i += 1
        if entities:
            return {"type": "entities", "count": len(entities), "entities": entities[:50]}

    # Pares: 64 + [00 TT CC V:u32] repetido (7 bytes/par)
    if len(d) >= 8 and (len(d) - 1) % 7 == 0:
        fields = {}
        i = 1
        while i + 7 <= len(d):
            if d[i] != 0x00:
                break
            tipo = d[i+1]
            campo = d[i+2]
            valor = struct.unpack('>I', d[i+3:i+7])[0]
            fields[CLEAR_FIELD_NAMES.get(campo, "t%d_f0x%02x" % (tipo, campo))] = valor
            i += 7
        if fields:
            return {"type": "entity_pos", "fields": fields}

    return {"type": "unknown", "hex": d[:40].hex()}

def process_server_frame(state, length, flag, payload, client):
    """Process a server frame with full verbose logging."""
    TL.save_packet("RECV", "TCP", payload)

    if flag == 1:
        TL.log("  RECV [CLEAR] len=%d hex=%s" % (length, payload[:40].hex()))
        # Decode CLEAR frames (serializacion binaria custom, ver PROTOCOLO_OPCODES.md)
        decoded = decode_clear_frame(payload)
        if decoded:
            TL.log("    CLEAR decode: %s" % json.dumps(decoded)[:300])
            state.last_clear = decoded
            if decoded.get("type") == "entities":
                ents = decoded.get("entities", [])
                state.entity_list = [e["id"] for e in ents]
                TL.log("    *** ENTITIES: %d in room ***" % len(ents))
            elif decoded.get("type") == "entity_pos":
                f = decoded.get("fields", {})
                # Guardar el frame de posicion (sin convertir: valores crudos)
                state.entities[len(state.entities)] = f
        return None, None

    if flag != 0:
        TL.log("  RECV [FLAG=%d] len=%d hex=%s" % (flag, length, payload[:40].hex()))
        return None, None

    # Full decode attempt
    v, dec, seed_used, method = full_decode_frame(payload, length, state.get_decode_seeds())

    if v is None:
        TL.log("  RECV [UNDECODABLE] len=%d method=%s hex=%s" % (length, method, payload[:40].hex()))
        # Try position extraction from raw
        pos = try_extract_position(payload)
        if pos:
            TL.log("    *** POSITION from raw: (%.1f, %.1f) ***" % pos)
            state.position = pos
            state.spawned = True
        return None, None

    state.frame_count += 1

    if isinstance(v, list) and len(v) >= 1 and isinstance(v[0], int):
        opcode = v[0]
        name = TL.opcode_names.get(opcode, "UNKNOWN")
        TL.log_frame("RECV", opcode, v, raw_bytes=payload, sock_id=state.sock_id, seed=seed_used,
                      extra="method=%s" % method)
        TL.save_packet("RECV", "TCP", payload, decoded=v, opcode=opcode)

        # Handle specific opcodes
        if opcode == 1:  # PING
            ts = v[1] if len(v) >= 2 else 0
            TL.log("    -> PING ts=%s, responding with PONG" % repr(ts))
            old_seed, new_seed = state.advance_seed()
            pong = make_ping_frame(state.encoding_seed, ts)
            send_frame(state.sock, pong, label="PONG")

        elif opcode == 4:  # PLAYER_ID
            state.player_id = v[1] if isinstance(v[1], int) else -1
            TL.log("    *** PLAYER_ID = %d ***" % state.player_id)

        elif opcode == 5:  # NATIVE_PLAY
            TL.log("    NATIVE_PLAY from server: %s" % repr(v)[:120])

        elif opcode == 10:  # ENTITY_DATA
            TL.log("    ENTITY_DATA: %s" % repr(v)[:200])

        elif opcode == 16:  # ENTITY_LIST
            if len(v) >= 2 and isinstance(v[1], list):
                state.entity_list = v[1]
                TL.log("    ENTITY_LIST: %d entities" % len(v[1]))

        elif opcode == 19:  # POSITION
            TL.log("    POSITION_UPDATE: %s" % repr(v)[:200])

        elif opcode == 20:  # SPAWN_POSITION
            if len(v) >= 2 and isinstance(v[1], list) and len(v[1]) >= 2:
                state.position = (v[1][0], v[1][1])
                state.spawned = True
                TL.log("    *** SPAWNED! pos=(%.1f, %.1f) ***" % state.position)
            else:
                TL.log("    SPAWN_POSITION: %s" % repr(v)[:200])

        elif opcode == 35:  # CHAT
            text = str(v[1]) if len(v) >= 2 else ""
            sender = str(v[2]) if len(v) >= 3 else "?"
            TL.log("    CHAT from=%s msg=%s" % (sender, text[:100]))
            state.chat_log.append({"sender": sender, "msg": text, "time": time.time()})

        elif opcode == 40:  # SERVER_ACK
            TL.log("    SERVER_ACK: %s" % repr(v)[:120])

        elif opcode == 52:  # AUTH_TOKEN
            TL.log("    AUTH_TOKEN: %s" % repr(v)[:120])

        elif opcode == 10000:  # READY
            TL.log("    READY from server: %s" % repr(v)[:120])

        elif opcode == 10001:  # PONG
            TL.log("    PONG from server: %s" % repr(v)[:120])

        elif opcode == 10020:  # DISCONNECT
            TL.log("    *** DISCONNECT from server ***")

        elif opcode == 10034:  # CLEAR_FRAME
            pass  # silent

        else:
            TL.log("    UNHANDLED OP=%d: %s" % (opcode, repr(v)[:200]))

        return opcode, v

    elif isinstance(v, str):
        TL.log("  RECV [STRING] '%s'" % v[:100])
        if len(v) >= 8:
            state.suffix = v[-8:]
            TL.log("    SUFFIX = %s" % state.suffix)
        return -1, v

    else:
        TL.log("  RECV [OTHER] type=%s val=%s" % (type(v).__name__, repr(v)[:200]))
        return -2, v

# ================================================================
# TCP SESSION (Enhanced)
# ================================================================
def run_tcp_session(host, port, token, mode=3, duration=600,
                    http_play_fn=None, spawn_wait=180,
                    native_repeats=2, stay_static=True,
                    action_fn=None, test_mode=False):
    """Full TCP session with traffic capture and action toolkit."""

    state = GameState()
    state.host = host
    state.port = port

    TL.log("=" * 70)
    TL.log("  TCP SESSION START: %s:%d  mode=%d" % (host, port, mode))
    TL.log("=" * 70)

    # Connect TCP
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        state.sock = sock
        state.sock_id = int(sock.fileno())
        TL.log("[1] TCP Connected sock=%d" % state.sock_id)
    except Exception as e:
        TL.log("[1] TCP CONNECT FAILED: %s" % e)
        return False

    # Setup UDP
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    state.udp_sock = udp_sock
    state.udp_prefix = make_udp_prefix()
    try:
        udp_sock.sendto(make_udp_init_packet(state.udp_prefix), (host, UDP_PORT))
        TL.log("[1b] UDP init sent to %s:%d prefix=%s" % (host, UDP_PORT, state.udp_prefix.hex()))
        TL.log_udp("SEND", make_udp_init_packet(state.udp_prefix), "%s:%d" % (host, UDP_PORT))
    except Exception as e:
        TL.log("[1b] UDP init FAILED: %s" % e)

    # Read greeting for suffix
    TL.log("[2] Waiting for server greeting (suffix)...")
    while True:
        length, flag, payload = recv_frame(sock, 5)
        if length is None:
            TL.log("    No greeting received!")
            break
        TL.log_hex("RECV", payload, "GREETING len=%d flag=%d" % (length, flag))
        TL.save_packet("RECV", "TCP", payload)
        if flag == 1: continue
        try:
            dec = bytearray_desturple(payload, 0)
            d = Amf3Decoder(dec)
            v = d.read_value()
            if isinstance(v, str) and len(v) >= 8:
                state.suffix = v[-8:]
                TL.log("    SUFFIX = '%s'" % state.suffix)
                break
        except Exception as e:
            TL.log("    Greeting decode error: %s" % e)

    if not state.suffix:
        TL.log("    ERROR: No suffix received!")
        sock.close(); udp_sock.close()
        return False

    # MT setup
    state.str_key = get_str_key(state.suffix)
    state.mt = MersenneTwister(state.str_key)
    state.server_seed = state.mt.next_val() % 99999
    TL.log("    str_key=%d  server_seed=%d" % (state.str_key, state.server_seed))
    state.encoding_seed = 0

    # Send AUTH
    TL.log("[3] Sending AUTH...")
    auth_frame = make_auth_frame(host, state.suffix, token, mode, ext_id=239)
    send_frame(sock, auth_frame, label="AUTH")

    # Read post-auth frames
    TL.log("[4] Reading post-auth frames...")
    auth_timeout = time.time() + 15
    while time.time() < auth_timeout:
        length, flag, payload = recv_frame(sock, 3)
        if length is None: break
        TL.log_hex("RECV", payload, "POST_AUTH len=%d flag=%d" % (length, flag))
        TL.save_packet("RECV", "TCP", payload)
        if flag == 1: continue

        v, dec, seed_used = try_decode_destpurple(payload, [0, state.server_seed, state.encoding_seed])
        if v is None:
            TL.log("    POST_AUTH UNDEC len=%d hex=%s" % (length, payload[:20].hex()))
            continue

        opcode, val = process_server_frame(state, length, flag, payload, GameClient(state))
        if opcode == 4:
            TL.log("    Got PLAYER_ID, proceeding...")
            break
        elif opcode == 52:
            TL.log("    Got AUTH_TOKEN, continuing...")
        elif isinstance(v, str):
            TL.log("    Got string (suffix update?), continuing...")

    TL.log("    Post-auth: player_id=%d encoding_seed=%d" % (state.player_id, state.encoding_seed))

    # Send READY
    TL.log("[5] Sending READY (seed=%d)..." % state.encoding_seed)
    send_frame(sock, make_ready_frame(state.encoding_seed), label="READY")
    send_frame(sock, make_clear_10034_frame(), label="CLEAR_10034")
    time.sleep(0.3)

    # Start httpPlay BEFORE reading frames — some servers need the
    # httpPlay request to arrive before they will send entity frames.
    http_play_done = False
    http_play_started = False
    http_play_thread = None
    client = GameClient(state)

    if http_play_fn:
        def do_http_play():
            try: http_play_fn()
            except Exception as e: TL.log("    httpPlay error: %s" % e)
        http_play_thread = threading.Thread(target=do_http_play, daemon=True)
        http_play_thread.start()
        http_play_started = True
        TL.log("[5b] httpPlay started (before frame read)...")

    # Read frames after READY (httpPlay running in parallel)
    TL.log("[5c] Reading frames after READY...")
    for _ in range(30):
        length, flag, payload = recv_frame(sock, 0.5)
        if length is None: break
        TL.log_hex("RECV", payload, "POST_READY len=%d flag=%d" % (length, flag))
        TL.save_packet("RECV", "TCP", payload)
        if flag == 1: continue
        opcode, val = process_server_frame(state, length, flag, payload, client)
        if state.spawned:
            break

    # Wait for httpPlay to finish
    while http_play_started and not http_play_done:
        if http_play_thread and not http_play_thread.is_alive():
            http_play_done = True
        time.sleep(0.05)
    if http_play_started:
        TL.log("    httpPlay done!")

    # Send NATIVE_PLAY
    if not state.spawned:
        TL.log("[7] Sending NATIVE_PLAY...")
        for _ in range(max(1, native_repeats)):
            send_frame(sock, make_clear_10034_frame(), label="CLEAR")
            send_frame(sock, make_native_play_frame(0), label="NATIVE_PLAY")
            send_frame(sock, make_clear_10034_frame(), label="CLEAR")
        TL.log("    NATIVE_PLAY sent!")
    else:
        TL.log("[7] Already spawned, skipping NATIVE_PLAY")

    # Main loop
    TL.log("[8] Main loop (spawned=%s pos=%s id=%d)" % (state.spawned, state.position, state.player_id))
    spawn_deadline = time.time() + spawn_wait
    session_deadline = time.time() + duration
    next_move = time.time() + 1
    next_log = time.time() + 5
    next_udp = time.time() + 1
    next_ping = time.time() + 1
    move_count = 0
    spawned = state.spawned
    frames_total = 0

    state.running = True

    # Run action_fn if provided (test mode)
    action_thread = None
    if action_fn and test_mode:
        def run_actions():
            try:
                time.sleep(2)  # wait for spawn
                action_fn(client, state)
            except Exception as e:
                TL.log("  ACTION ERROR: %s" % e)
        action_thread = threading.Thread(target=run_actions, daemon=True)
        action_thread.start()

    while state.running:
        now = time.time()

        if spawned and now >= session_deadline:
            TL.log("[9] Session duration reached.")
            break

        if not spawned and now >= spawn_deadline:
            TL.log("[9] Spawn timeout! pos=%s id=%d frames=%d" % (state.position, state.player_id, frames_total))
            break

        # Read frames
        for _ in range(50):
            try:
                length, flag, payload = recv_frame(sock, 0.3 if frames_total < 5 else 0.05)
            except:
                length = None

            if length is None: break
            frames_total += 1

            opcode, val = process_server_frame(state, length, flag, payload, client)

            if state.spawned and not spawned:
                spawned = True
                TL.log("    *** SPAWNED in main loop ***")

        now = time.time()

        # Keepalive pings
        if now >= next_ping:
            client.keepalive_ping()
            next_ping = now + 2

        # UDP keepalive
        if state.player_id >= 0 and now >= next_udp:
            client.send_udp_move(34.0, -3.084, 0.9309)
            next_udp = now + 1

        # TCP keepalive move
        if state.player_id >= 0 and now >= next_move:
            client.keepalive_move(34.0, -3.084, 0.9309)
            move_count += 1
            if move_count <= 3 or move_count % 10 == 0:
                TL.log("    MOVE #%d (seed=%d)" % (move_count, state.encoding_seed))
            next_move = now + 1

        # UDP receive check
        try:
            udp_sock.settimeout(0.01)
            udp_data, udp_addr = udp_sock.recvfrom(1024)
            udp_decoded = decode_udp_packet(udp_data)
            TL.log_udp("RECV", udp_data, str(udp_addr))
            TL.save_packet("RECV", "UDP", udp_data, decoded=udp_decoded, addr=udp_addr)
        except:
            pass

        if now >= next_log:
            if spawned:
                TL.log("    [alive] spawned=%.1f frames=%d moves=%d pings=%d seed=%d" % (
                    time.time() - (session_deadline - duration), frames_total, move_count,
                    state.ping_count, state.encoding_seed))
            else:
                TL.log("    [waiting] frames=%d id=%d seed=%d pos=%s" % (
                    frames_total, state.player_id, state.encoding_seed, state.position))
            next_log = now + 10

        time.sleep(0.005)

    # Disconnect
    TL.log("[10] Disconnecting...")
    try:
        disc_frame = make_disconnect_flush_frame(state.encoding_seed)
        send_frame(sock, disc_frame, label="DISCONNECT")
    except: pass
    try: sock.close()
    except: pass
    try: udp_sock.close()
    except: pass

    state.running = False

    TL.log("=" * 70)
    TL.log("  SESSION COMPLETE: spawned=%s player_id=%d frames=%d pings=%d moves=%d" % (
        spawned, state.player_id, frames_total, state.ping_count, move_count))
    TL.log("  Chat messages: %d" % len(state.chat_log))
    TL.log("  Entity list: %d entities" % len(state.entity_list))
    TL.log("=" * 70)

    # Save traffic summary
    save_traffic_summary(state)

    return spawned

# ================================================================
# TRAFFIC SUMMARY
# ================================================================
def save_traffic_summary(state):
    summary = {
        "player_id": state.player_id,
        "suffix": state.suffix,
        "str_key": state.str_key,
        "server_seed": state.server_seed,
        "final_encoding_seed": state.encoding_seed,
        "position": state.position,
        "spawned": state.spawned,
        "total_pings": state.ping_count,
        "total_moves": state.move_count,
        "total_frames": state.frame_count,
        "chat_log": state.chat_log,
        "entity_count": len(state.entity_list),
        "total_packets": len(TL.packets),
    }
    summary_file = os.path.join(script_dir, "traffic_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    TL.log("  Summary saved to %s" % summary_file)

    # Save full packet log
    packets_file = os.path.join(script_dir, "traffic_packets.json")
    with open(packets_file, "w", encoding="utf-8") as f:
        json.dump(TL.packets, f, indent=2, ensure_ascii=False, default=str)
    TL.log("  Packets saved to %s (%d packets)" % (packets_file, len(TL.packets)))

# ================================================================
# HTTP Login
# ================================================================
def do_login():
    did = load_device_id()
    ak = load_attest_key()
    s = requests.Session()
    s.headers["User-Agent"] = "libcurl-agent/1.0"
    r = s.get(ENGINE + "?do=knock&rndx=" + rndx_fn(), verify=False).json()
    assert r["result"] == "ok"
    token = r["data"]["token"]
    print("  KNOCK OK")
    p0, _ = str_dest(token)
    edid = m2xc_fmt(m2xc_encrypt_full(eb(did), eb(p0), 0xBC461A49, 0x7C2359AB))
    chk = hashlib.md5(("_chk91822" + did + "l.o.x").encode()).hexdigest()
    qs = urllib.parse.urlencode([
        ("rus", "1"), ("loc", "es_CO"), ("ver", VER), ("dds", "1920x1080"),
        ("do", "lim"), ("t", token), ("ddd", DESKTOP), ("fmt", "tbt"),
        ("chk", chk), ("did", edid), ("rndx", rndx_fn()),
    ])
    r = s.get(ENGINE + "?" + qs, verify=False).json()
    assert r["result"] == "ok"
    dk_blob = parse_m2xc_blob(r["data"]["dk"])
    dm_blob = parse_m2xc_blob(r["data"]["dm"])
    dk_key = hashlib.md5((token + did).encode()).hexdigest()
    dm_key = hashlib.md5((did + token).encode()).hexdigest()
    sk = m2xc_decrypt_full(dk_blob, eb(dk_key)).decode()
    rk = m2xc_decrypt_full(dm_blob, eb(dm_key)).decode()
    print("  LIM   OK")
    magic = "".join(random.choices(CHARSET, k=64))
    dtf = build_dtf(sk)
    pf = build_proof(ak, dtf, did)
    mid = build_mid(ak)
    dd_json = json.dumps({"proof": pf, "mid": mid, "ver": VER, "host": "app.mitos.is"}, separators=(",", ":"))
    R10 = (int(time.time() * 1000) ^ random.randint(0, M)) & M
    dd_raw = m2xc_encrypt_full(eb(dd_json), eb(magic), R10, random.randint(0, M))
    dd = m2xc_fmt(dd_raw)
    pub = api_full.serialization.load_pem_public_key(rk.encode())
    ms = base64.b64encode(pub.encrypt(magic.encode(), padding=api_full.padding.PKCS1v15())).decode()
    params = [
        ("go", "0"), ("dd", dd), ("de", "desktop"), ("gi", "0"),
        ("ver", VER), ("it", "1"), ("do", "eh"), ("im", "0"),
        ("di", DESKTOP), ("dtf", dtf), ("ms", ms), ("rndx", rndx_fn()),
    ]
    r = s.get(ENGINE + "?" + urllib.parse.urlencode(params), verify=False)
    print("  EH    OK")
    return sk, magic, s

def make_api_call(session, sk, magic, payload):
    body_json = json.dumps(payload, separators=(",", ":"))
    enc = m2xc_encrypt_full(eb(body_json), eb(magic), 0, 0)
    body = m2xc_fmt(enc)
    url = ENGINE + "?_sid=" + urllib.parse.quote(sk, safe="") + "&rndx=" + rndx_fn()
    r = session.post(url, data=body, verify=False, timeout=15)
    t = r.text
    if not t: return {}
    if t.startswith("tBB,"):
        b64 = t[12:]  # skip "tBB," + 8 hex digits
        padded = b64 + '=' * (4 - len(b64) % 4) if len(b64) % 4 else b64
        blob = base64.b64decode(padded)
        if blob[:4] == b"M2XC":
            dec = m2xc_decrypt_full(blob, eb(magic))
            try: return json.loads(dec)
            except: return {"_raw": dec.decode("utf-8", errors="replace")[:200]}
        # v5OH2: AES-CBC with aes_key(magic)
        try:
            dec = decrypt_v5oh2(blob, magic)
            text = dec.decode("utf-8", errors="replace").rstrip('\x00')
            try: return json.loads(text)
            except: return {"_raw": text[:200]}
        except: return {"_raw": t[:200]}
    try: return json.loads(t)
    except: return {"_raw": t[:200]}

def do_connect(session, sk, magic, region, mode_index, mode_val, locale="es_CO"):
    make_api_call(session, sk, magic, {"do": "gamemode", "index": mode_index, "mode": mode_val})
    make_api_call(session, sk, magic, {"do": "servers", "change": region})
    return make_api_call(session, sk, magic, {
        "do": "connect", "invite": False, "defered": True,
        "i": mode_index, "gm": -1, "retrying": False, "locale": locale,
    })

def make_http_play_fn(session, sk, magic, mode_index, mode_val):
    def http_play():
        r1 = make_api_call(session, sk, magic, {"do": "play", "usertoken": None})
        TL.log("    httpPlay: play -> %s" % json.dumps(r1)[:200])
        r2 = make_api_call(session, sk, magic, {"do": "gamemode", "index": mode_index, "mode": mode_val})
        TL.log("    httpPlay: gamemode -> %s" % json.dumps(r2)[:200])
    return http_play

def spawn_account(session, sk, magic, region, mode_index=1, mode_val=3,
                  duration=600, spawn_wait=180, account_name="acc",
                  native_repeats=2, no_http_play=False, test_mode=False,
                  action_fn=None):
    print("\n[%s] Connecting to %s (mode=%d)..." % (account_name, region, mode_val))
    result = do_connect(session, sk, magic, region, mode_index, mode_val)
    server = result.get("data", {}).get("server", "")
    token = result.get("data", {}).get("token", "")
    if not server or not token:
        print("[%s] No server/token!" % account_name); return False
    parts = server.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 443
    print("[%s] Server: %s:%d" % (account_name, host, port))
    http_play = None if no_http_play else make_http_play_fn(session, sk, magic, mode_index, mode_val)
    spawned = run_tcp_session(
        host, port, token, mode=mode_val, duration=duration,
        http_play_fn=http_play, spawn_wait=spawn_wait,
        native_repeats=native_repeats,
        test_mode=test_mode, action_fn=action_fn,
    )
    return spawned

def spawn_all_regions(sk, magic, session, duration=120, spawn_wait=90):
    results = {}
    for region in REGIONS:
        for mode_name, mode_index, mode_val in MODES:
            key = "%s_%s" % (region, mode_name)
            print("\n" + "=" * 60)
            print("  SPAWN: %s  mode=%s (%d/%d)" % (region, mode_name, mode_index, mode_val))
            print("=" * 60)
            try:
                spawned = spawn_account(session, sk, magic, region=region,
                    mode_index=mode_index, mode_val=mode_val,
                    duration=duration, spawn_wait=spawn_wait, account_name=key)
                results[key] = spawned
            except Exception as e:
                print("  ERROR: %s" % e)
                results[key] = False
            time.sleep(1)
    return results

# ================================================================
# COMMAND REFERENCE
# ================================================================
def print_command_reference():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                  MITOSISOG COMMAND REFERENCE                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  TCP OPCODES (AMF3-encoded):                                     ║
║  ─────────────────────────                                       ║
║  OP=1      PING (server→client)     → Reply with OP=10001       ║
║  OP=2      TIME_SYNC (server→client)                            ║
║  OP=3      KEEPALIVE (server→client)                            ║
║  OP=4      PLAYER_ID [4, player_id, timestamp]                  ║
║  OP=5      NATIVE_PLAY [5, [false]]                             ║
║  OP=10     ENTITY_DATA                                         ║
║  OP=16     ENTITY_LIST [16, [entity_ids...]]                   ║
║  OP=19     POSITION_UPDATE [19, x, y, ...]                     ║
║  OP=20     SPAWN_POSITION [20, [x, y, z], timestamp]           ║
║  OP=35     CHAT [35, message, sender]                           ║
║  OP=40     SERVER_ACK                                           ║
║  OP=52     AUTH_TOKEN [52, ...]                                 ║
║                                                                  ║
║  CLIENT OPCODES:                                                 ║
║  ─────────────                                                   ║
║  OP=10000  READY [10000, [true, 2560, 1440, 1.333, true]]     ║
║  OP=10001  PONG [10001, timestamp]                              ║
║  OP=10014  ABILITY_USE [10014, ability_id, x, y]               ║
║  OP=10015  WEAPON_FIRE                                          ║
║  OP=10017  ITEM_USE [10017, slot]                               ║
║  OP=10018  ITEM_DROP [10018, slot]                              ║
║  OP=10019  INTERACT [10019, target_id, type]                    ║
║  OP=10020  DISCONNECT [10020, null]                             ║
║  OP=10022  MOVE [10022, x, y, power] (CLEAR frame)             ║
║  OP=10024  JUMP [10024]                                         ║
║  OP=10025  DASH [10025, angle, power]                           ║
║  OP=10028  WEAPON_ATTACK [10028, weapon_id, angle, power]      ║
║  OP=10030  EQUIP [10030, slot]                                  ║
║  OP=10031  UNEQUIP [10031, slot]                                ║
║  OP=10034  CLEAR_FRAME (empty clear)                            ║
║  OP=35     CHAT_SEND [35, message]                              ║
║  OP=46     TEAM_SELECT [46, team_id]                            ║
║  OP=64     BUY_ITEM [64, item_id, quantity]                     ║
║  OP=66     TRADE [66, target_id, item_ids...]                   ║
║  OP=68     REPORT [68, target_id, reason]                       ║
║  OP=86     EMOTE [86, emote_id]                                 ║
║  OP=94     VOTE [94, poll_id, choice]                           ║
║                                                                  ║
║  UDP PACKETS:                                                    ║
║  ────────────                                                    ║
║  Init:  [prefix][00000000012731][padding]                       ║
║  Move:  [prefix][seq:4B][002726][x:f][angle:f][power:f]        ║
║         [ffffffff00000000]                                       ║
║                                                                  ║
║  TCP FRAME FORMAT:                                               ║
║  ───────────────                                                 ║
║  SEND: [4B:end][4B:origlen][1B:checksum][resturple_data]        ║
║  RECV: [2B:length][1B:flag][payload]                             ║
║    flag=0: AMF3 (desturple, seed from MT)                        ║
║    flag=1: CLEAR (raw binary)                                    ║
║                                                                  ║
║  MT SEED PROGRESSION:                                            ║
║  ───────────────────                                             ║
║  1. Init with get_str_key(suffix)                                ║
║  2. server_seed = mt.next() % 99999                              ║
║  3. encoding_seed = 0 (auth/READY use seed=0)                    ║
║  4. On each PING: encoding_seed = mt.next() % 99999             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

# ================================================================
# TEST SESSION
# ================================================================
def run_test_session(sk, magic, session, account_name="test"):
    """Run a complete test session: login, connect, spawn, chat, move, keep alive."""

    def test_actions(client, state):
        """Actions to run after spawn."""
        TL.log("  [TEST] Waiting 3s for full spawn...")
        time.sleep(3)

        TL.log("  [TEST] === SENDING CHAT ===")
        client.send_chat("Hello from traffic capture!")

        TL.log("  [TEST] === SENDING EMOTE ===")
        client.send_emote(1)

        TL.log("  [TEST] === MOVING TO POSITION ===")
        client.move_to(100.0, 50.0, 0.9309)

        TL.log("  [TEST] === JUMPING ===")
        client.jump()

        TL.log("  [TEST] === SENDING DASH ===")
        client.dash(45.0, 1.5)

        TL.log("  [TEST] === MORE CHAT ===")
        client.send_chat("Testing all commands!")

        TL.log("  [TEST] === ALL ACTIONS COMPLETE ===")

    print("\n" + "=" * 70)
    print("  TEST SESSION — Full Traffic Capture")
    print("=" * 70)

    spawned = spawn_account(
        session, sk, magic, region="europe", mode_index=1, mode_val=3,
        duration=60, spawn_wait=60, account_name=account_name,
        test_mode=True, action_fn=test_actions,
    )

    print("\n" + "=" * 70)
    print("  TEST RESULT: %s" % ("SPAWNED!" if spawned else "FAILED"))
    print("=" * 70)

    return spawned

# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    import sys as _sys
    print("=" * 70)
    print("  MitosisOG — Full Traffic Capture + Action Toolkit")
    print("=" * 70)

    if "--help" in _sys.argv or "-h" in _sys.argv:
        print_command_reference()
        sys.exit(0)

    print("\n[LOGIN]")
    sk, magic, session = do_login()

    stats = make_api_call(session, sk, magic, {"do": "stats"})
    account_name = "?"
    for item in stats.get("data", []):
        if item[0] == "previous_user":
            account_name = item[1]
            break
    print("  Account: %s" % account_name)
    print("  Session key: %s..." % sk[:20])

    if "--ref" in _sys.argv:
        print_command_reference()
        sys.exit(0)

    if "--test" in _sys.argv:
        run_test_session(sk, magic, session, account_name)
    elif "--all" in _sys.argv:
        results = spawn_all_regions(sk, magic, session, duration=120, spawn_wait=90)
        print("\n" + "=" * 70)
        print("  RESULTS — Account: %s" % account_name)
        for k, v in results.items():
            print("    %s: %s" % (k, "SPAWNED" if v else "FAILED"))
        spawned_count = sum(1 for v in results.values() if v)
        print("  Total: %d/%d spawned" % (spawned_count, len(results)))
        print("=" * 70)
    else:
        spawned = spawn_account(
            session, sk, magic, region="europe", mode_index=1, mode_val=3,
            duration=120, spawn_wait=90, account_name=account_name,
        )
        print("\n" + "=" * 70)
        print("  Account: %s | RESULT: %s" % (account_name, "SPAWNED!" if spawned else "FAILED"))
        print("=" * 70)
