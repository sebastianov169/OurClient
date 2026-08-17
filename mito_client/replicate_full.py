#!/usr/bin/env python3
"""
replicate_full.py - Replicates the COMPLETE game protocol
Based on captured DLL data and existing implementations.

Flow:
1. HTTP API: KNOCK → LIM → EH → connect → join_private_room
2. TCP: TLS handshake → desturple encoding → M2XC encryption
3. UDP: Real-time game input
"""

import json, hashlib, base64, struct, random, time, urllib.parse, os, sys
import socket, select, ssl, threading
import requests, urllib3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
urllib3.disable_warnings()

# ================================================================
# Configuration
# ================================================================
API = "https://app.mitos.is"
ENGINE = f"{API}/engine_beta.php"
VER = "10.1.8"
DESKTOP = "ASUSTeK COMPUTER INC.;1.0;Microsoft Windows 11 Enterprise LTSC;Windows;10.0.26100;x86;1920;1080"
CHARSET = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM0123456789"
M = 0xFFFFFFFF
EXT_ID = 495
MODE_ID = 63
TCP_SUFFIX_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# ================================================================
# M2XC Encryption/Decryption
# ================================================================
def eb(s):
    return s.encode("ascii") if isinstance(s, str) else bytes(s)

def rndx():
    return f"{random.random():.15f}"

def fmix(x):
    x &= M
    x = ((x ^ (x >> 16)) * 0x45d9f3b) & M
    x = ((x ^ (x >> 16)) * 0x45d9f3b) & M
    return (x ^ (x >> 16)) & M

def fmix2(x):
    x &= M
    x = ((x ^ (x >> 16)) * 0x45d9f3b) & M
    f2i = ((x ^ (x >> 16)) * 0x45d9f3b) & M
    final = (f2i ^ (f2i >> 16)) & M
    return f2i, final

def ror(x, r):
    x &= M; r &= 31
    return ((x >> r) | (x << (32 - r))) & M

def rol(x, r):
    return ror(x, 32 - r)

def keystate_xxtea(key_bytes, state, SUM, counter_offset=0, pass_b=False):
    w0, w1, w2, w3 = state
    c = 0
    for i in range(len(key_bytes)):
        b_val = key_bytes[i] & 0xFF
        t = (rol(w3, 3) + b_val + i + w0) & M
        w0 = fmix(t)
        t = (rol((b_val + i + w0) & M, 7) ^ w1) & M
        w1 = fmix(t)
        t = (w2 + rol((b_val ^ w1) & M, 11) + c) & M
        w2 = fmix(t)
        t = (rol((b_val + SUM) & M, 17) ^ w3 ^ w2) & M
        w3 = fmix(t)
        c = (c + 0x45d9f3b) & M
    return [w0, w1, w2, w3]

def swfinalize_passa(s):
    w0, w1, w2, w3 = s
    f2i_0, w0f = fmix2(w0 ^ 0xa5a5a5a5)
    f2i_1, w1f = fmix2((w1 + 0x3c6ef372) & M)
    w2f = fmix(((f2i_0 >> 19) | (w0f << 13)) ^ w2)
    w3f = fmix(((w1f << 9) | (f2i_1 >> 23)) + w3)
    return [w0f, w1f, w2f, w3f]

def transform1(data, state, H, pass_b=False):
    w0, w1, w2, w3 = state
    out = bytearray(len(data))
    for pos in range(len(data)):
        inp_byte = data[pos] & 0xFF
        p0, p1, p2, p3 = w0, w1, w2, w3
        val1 = (rol(p1, 5) + p0 + 0x9e3779b9 + pos) & M
        f2i_0, w0_new = fmix2(val1)
        val2 = (rol(p2, 7) ^ p1 ^ w0_new) & M
        w1_new = fmix(val2)
        val3 = (rol(p3, 11) + p2 + w1_new) & M
        f2i_3, w2_new = fmix2(val3)
        game_term = ((f2i_0 >> 19) | (w0_new << 13)) & M
        val4 = (game_term ^ p3 ^ w2_new ^ pos) & M
        f2i_w3, w3_new = fmix2(val4)
        term_c = ror(w1_new, 29)
        if pass_b:
            term_b = ((w2_new << 9) | (w2_new >> 23)) & M
        else:
            term_b = ((f2i_3 >> 23) | (w2_new << 9)) & M
        term_d = ((w3_new >> 15) | (w3_new << 17)) & M
        idx = (pos >> 2) & 3
        sel_word = (w0_new, w1_new, w2_new, w3_new)[idx]
        xor_val = (term_d ^ term_b ^ term_c ^ w0_new) & M
        shift = (pos & 3) << 3
        xor_shift = (xor_val >> shift) & 0xFF
        sel_shift = (sel_word >> shift) & 0xFF
        out[pos] = ((inp_byte + sel_shift + (H & 0xFF) + (pos & 0xFF)) & 0xFF) ^ xor_shift
        w0, w1, w2, w3 = w0_new, w1_new, w2_new, w3_new
    return bytes(out)

def inverse_transform1(encrypted, state, H, pass_b=False):
    w0, w1, w2, w3 = state
    out = bytearray(len(encrypted))
    for pos in range(len(encrypted)):
        byte_val = encrypted[pos] & 0xFF
        p0, p1, p2, p3 = w0, w1, w2, w3
        val1 = (rol(p1, 5) + p0 + 0x9e3779b9 + pos) & M
        f2i_0, w0_new = fmix2(val1)
        val2 = (rol(p2, 7) ^ p1 ^ w0_new) & M
        w1_new = fmix(val2)
        val3 = (rol(p3, 11) + p2 + w1_new) & M
        f2i_3, w2_new = fmix2(val3)
        game_term = ((f2i_0 >> 19) | (w0_new << 13)) & M
        val4 = (game_term ^ p3 ^ w2_new ^ pos) & M
        f2i_w3, w3_new = fmix2(val4)
        term_c = ror(w1_new, 29)
        if pass_b:
            term_b = ((w2_new << 9) | (w2_new >> 23)) & M
        else:
            term_b = ((f2i_3 >> 23) | (w2_new << 9)) & M
        term_d = ((w3_new >> 15) | (w3_new << 17)) & M
        idx = (pos >> 2) & 3
        sel_word = (w0_new, w1_new, w2_new, w3_new)[idx]
        xor_val = (term_d ^ term_b ^ term_c ^ w0_new) & M
        shift = (pos & 3) << 3
        xor_shift = (xor_val >> shift) & 0xFF
        sel_shift = (sel_word >> shift) & 0xFF
        inp_byte = ((byte_val - sel_shift - (H & 0xFF) - (pos & 0xFF)) & 0xFF) ^ xor_shift
        out[pos] = inp_byte & 0xFF
        w0, w1, w2, w3 = w0_new, w1_new, w2_new, w3_new
    return bytes(out)

def inverse_transform2(encrypted, ha, hb, counter_offset=0):
    prev = hb & 0xFF
    out = bytearray(len(encrypted))
    for i in range(len(encrypted)):
        pos = i + counter_offset
        shift = (i & 3) << 3
        ha_shift = (ha >> shift) & M
        mix = ((ha_shift + prev + pos) & 0xFF)
        enc_byte = encrypted[i]
        val = (enc_byte ^ mix ^ prev) & 0xFF
        out[i] = val
        prev = enc_byte
    return bytes(out)

def m2xc_encrypt_full(data, key_bytes, H1, H2):
    KEY = bytes(key_bytes)
    len_data = len(data); len_key = len(KEY)
    s1 = [
        fmix((len_data ^ H1 ^ 0x243f6a88) & M),
        fmix((H2 ^ 0x85a308d3) & M),
        fmix((len_key ^ rol(H1, 7) ^ 0x13198a2e) & M),
        fmix((rol(H2, 11) ^ 0x3707344) & M),
    ]
    s1 = keystate_xxtea(KEY, s1, (H1 + H2) & M, 0, pass_b=False)
    s1 = swfinalize_passa(s1)
    round1 = transform1(data, s1, H1, pass_b=False)
    round2 = bytearray(len(round1))
    prev = H2 & 0xFF
    for i in range(len(round1)):
        pos = i
        shift = (i & 3) << 3
        ha_shift = (H1 >> shift) & M
        mix = ((ha_shift + prev + pos) & 0xFF)
        round2[i] = (round1[i] ^ mix ^ prev) & 0xFF
        prev = round2[i]
    H3 = fmix((len_data ^ H1 ^ H2) & M)
    blob = b'M2XC' + struct.pack('>I', H1) + struct.pack('>I', H2) + struct.pack('>I', H3) + bytes(round2)
    return blob

def m2xc_decrypt_full(blob, key_bytes):
    if blob[:4] != b'M2XC':
        raise ValueError("Not M2XC blob")
    H1 = struct.unpack('>I', blob[4:8])[0] & M
    H2 = struct.unpack('>I', blob[8:12])[0] & M
    payload = blob[16:]
    KEY = bytes(key_bytes)
    len_data = len(payload); len_key = len(KEY)
    s1 = [
        fmix((len_data ^ H1 ^ 0x243f6a88) & M),
        fmix((H2 ^ 0x85a308d3) & M),
        fmix((len_key ^ rol(H1, 7) ^ 0x13198a2e) & M),
        fmix((rol(H2, 11) ^ 0x3707344) & M),
    ]
    s1 = keystate_xxtea(KEY, s1, (H1 + H2) & M, 0, pass_b=False)
    s1 = swfinalize_passa(s1)
    round1 = inverse_transform2(payload, H1, H2, counter_offset=0)
    plaintext = inverse_transform1(round1, s1, H1, pass_b=False)
    return plaintext

def m2xc_fmt(blob):
    return f"{len(blob) - 16:08d}" + base64.b64encode(blob).decode()

def parse_m2xc_blob(s):
    return base64.b64decode(s[8:])

# ================================================================
# Desturple Encoding (TCP)
# ================================================================
def get_str_key(text):
    value = 0
    for i in range(len(text)):
        value += (ord(text[i]) * (i * 2 - 1)) ^ 0x0EF8
    return value & 0xFFFFFFFF

class MersenneTwister:
    def __init__(self, seed):
        self.state = [0] * 624
        self.index = 624
        self.state[0] = seed & 0xFFFFFFFF
        for i in range(1, 624):
            self.state[i] = (1812433253 * (self.state[i-1] ^ (self.state[i-1] >> 30) + i)) & 0xFFFFFFFF
    
    def next_val(self):
        if self.index >= 624:
            for i in range(624):
                y = (self.state[i] & 0x80000000) + (self.state[(i+1) % 624] & 0x7FFFFFFF)
                self.state[i] = self.state[(i + 397) % 624] ^ (y >> 1)
                if y & 1:
                    self.state[i] ^= 0x9908b0df
            self.index = 0
        y = self.state[self.index]
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= (y >> 18)
        self.index += 1
        return y

def desturple_decode(data, seed):
    out = bytearray(len(data))
    for i in range(len(data)):
        v3 = (data[i] ^ ((seed + i*i + (seed+i) % 16) % 256)) & 0xFF
        out[i] = v3
    # Byte interleave
    parity = seed % 2
    left = bytearray()
    right = bytearray()
    mid = len(out) // 2
    low = mid - 1
    high = mid
    side = 0
    for i in range(len(out)):
        if side == 0:
            left.append(out[low] if low >= 0 else 0)
            low -= 1
        else:
            right.append(out[high] if high < len(out) else 0)
            high += 1
        side = 1 - side if (parity ^ side) else side
    result = bytearray()
    for b in left: result.append(b)
    for b in right: result.append(b)
    return bytes(result)

# ================================================================
# DTF (Device Trust Factor)
# ================================================================
def _dtf_mix(data, key_string):
    def sar32(v, s):
        return (v >> s) | (((1 << s) - 1) << (32 - s)) if v & 0x80000000 else v >> s
    len_a = len(data)
    len_b = len(key_string)
    ebx = ((len_a << 16) ^ len_b) ^ 0x9E3779B9
    ebx &= M
    out = bytearray()
    out.extend((ebx ^ 0xA5F00F5A).to_bytes(4, 'big'))
    out.extend((((ebx >> 16) ^ len_a) & 0xFFFF).to_bytes(2, 'big'))
    out.extend(((ebx ^ len_b) & 0xFFFF).to_bytes(2, 'big'))
    for i in range(max(len_a, len_b)):
        eax = (ebx << 13) & M; ebx ^= eax
        eax = sar32(ebx, 17); ebx ^= eax
        eax = (ebx << 5) & M; ebx ^= eax; ebx &= M
        r14d = ebx & 0xF
        edi = sar32(ebx, 4) & 0xF
        p_char = ord(data[i]) if i < len_a else sar32(ebx, 8) & 0xFF
        m_char = ord(key_string[i]) if i < len_b else sar32(ebx, 16) & 0xFF
        r15d = (p_char + r14d) & 0xFF
        r12d = (m_char + edi) & 0xFF
        r15d ^= edi
        r12d ^= r14d
        if ebx & 0x80:
            out.append(r12d & 0xFF)
            out.append(r15d & 0xFF)
        else:
            out.append(r15d & 0xFF)
            out.append(r12d & 0xFF)
    return base64.b64encode(bytes(out)).decode('ascii')

def build_dtf(sk):
    _H1 = random.randint(0, M)
    _H2 = random.randint(0, M)
    raw = m2xc_encrypt_full(eb("-1457143643"), eb(sk), _H1, _H2)
    sf = '%08d%s' % (11, base64.b64encode(raw).decode())
    while len(sf) < 64:
        sf += chr(random.randint(33, 126))
    sf = sf[:44] + '#' + sf[45:]
    return _dtf_mix(sf, sk)

# ================================================================
# Attestation
# ================================================================
def load_attest_key():
    for fn in ["tpm_attestation.pem", "embedded_rsa_private_14.pem",
               "embedded_rsa_private_16.pem"]:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), fn)
        if not os.path.exists(fp):
            fp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), fn)
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                k = serialization.load_pem_private_key(f.read(), password=None)
            print("  [key] %s (%d bits)" % (fn, k.key_size))
            return k
    raise FileNotFoundError("No attestation key found")

def build_proof(key, dtf, did):
    ch = (dtf + "|" + did + "|100").encode("ascii")
    sig = key.sign(hashlib.sha256(ch).digest(), padding.PKCS1v15(), hashes.SHA256())
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()

def build_mid(key):
    nums = key.private_numbers()
    n, e = nums.public_numbers.n, nums.public_numbers.e
    kb = (key.key_size + 7) // 8
    nb = n.to_bytes(kb, "big")
    eb_ = e.to_bytes((e.bit_length() + 7) // 8, "big")
    rsa1 = b"RSA1" + struct.pack("<IIIII", key.key_size, len(eb_), len(nb), 0, 0) + eb_ + nb
    frame = b"MID2" + bytes([1, 1]) + len(rsa1).to_bytes(2, "big") + rsa1
    frame += hashlib.sha256(bytes([1]) + rsa1).digest()
    return "M2." + base64.urlsafe_b64encode(frame).rstrip(b"=").decode()

# ================================================================
# Device ID
# ================================================================
def load_device_id():
    for qw_path in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "qw.sol"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qw.sol"),
        os.path.expandvars(r"%APPDATA%\Freakinware\MitosisOG\qw.sol"),
    ]:
        if os.path.exists(qw_path):
            with open(qw_path, encoding="utf-8", errors="replace") as f:
                txt = f.read()
            i = txt.find("y8:deviceIdy")
            if i < 0:
                continue
            after = txt[i + len("y8:deviceIdy"):]
            m = __import__("re").search(r"y(\d+):", after)
            if m:
                n = int(m.group(1))
                return after[m.end():m.end()+n]
    return None

# ================================================================
# str_dest
# ================================================================
def str_dest(token):
    s1 = s2 = ""; f = 0
    p1 = len(token) / 4.0; p2 = p1
    for _ in range(len(token) // 2):
        pos = int((p1 - 0.5) * 2.0 - 1.0) if f == 0 else int((p2 + 0.5) * 2.0 - 1.0)
        if pos < 0 or pos + 1 >= len(token): break
        a, b = token[pos], token[pos + 1]
        s1 += b if f == 0 else a
        s2 += a if f == 0 else b
        f = 1 - f
        p1 -= 1.0 if f == 1 else 0
        p2 += 1.0 if f == 0 else 0
    return s1, s2

# ================================================================
# TCP Protocol
# ================================================================
class MitosisTCP:
    def __init__(self, server_host, suffix):
        self.host = server_host
        self.suffix = suffix
        self.str_key = get_str_key(suffix)
        self.mt = MersenneTwister(self.str_key)
        self.server_seed = self.mt.next_val() % 99999
        self.encoding_seed = 0
        self.sock = None
        self.connected = False
    
    def connect(self, port=443):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        try:
            self.sock.connect((self.host, port))
            self.connected = True
            print("[TCP] Connected to %s:%d" % (self.host, port))
            return True
        except Exception as e:
            print("[TCP] Connection failed: %s" % e)
            return False
    
    def send_raw(self, data):
        if self.sock:
            self.sock.send(data)
    
    def recv_raw(self, size=4096):
        if self.sock:
            return self.sock.recv(size)
        return b""
    
    def close(self):
        if self.sock:
            self.sock.close()
            self.connected = False

# ================================================================
# Main Game Client
# ================================================================
class MitosisClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "libcurl-agent/1.0"
        self.did = load_device_id()
        self.ak = load_attest_key()
        self.token = None
        self.sk = None
        self.rk = None
        self.magic = None
        self.tcp = None
    
    def knock(self):
        print("\n[1] KNOCK")
        r = self.session.get(ENGINE + "?do=knock&rndx=" + rndx(), verify=False).json()
        assert r["result"] == "ok", "KNOCK failed: %s" % r
        self.token = r["data"]["token"]
        print("  OK token=%dc" % len(self.token))
        return r
    
    def lim(self):
        print("\n[2] LIM")
        p0, _ = str_dest(self.token)
        edid = m2xc_fmt(m2xc_encrypt_full(eb(self.did), eb(p0), 0xBC461A49, 0x7C2359AB))
        chk = hashlib.md5(("_chk91822" + self.did + "l.o.x").encode()).hexdigest()
        qs = urllib.parse.urlencode([
            ("rus", "1"), ("loc", "es_CO"), ("ver", VER), ("dds", "1920x1080"),
            ("do", "lim"), ("t", self.token), ("ddd", DESKTOP), ("fmt", "tbt"),
            ("chk", chk), ("did", edid), ("rndx", rndx()),
        ])
        r = self.session.get(ENGINE + "?" + qs, verify=False).json()
        if r["result"] != "ok":
            print("  FAIL: %s" % json.dumps(r)[:200])
            return False
        dk_blob = parse_m2xc_blob(r["data"]["dk"])
        dm_blob = parse_m2xc_blob(r["data"]["dm"])
        dk_key = hashlib.md5((self.token + self.did).encode()).hexdigest()
        dm_key = hashlib.md5((self.did + self.token).encode()).hexdigest()
        self.sk = m2xc_decrypt_full(dk_blob, eb(dk_key)).decode()
        self.rk = m2xc_decrypt_full(dm_blob, eb(dm_key)).decode()
        print("  OK sk=%s..." % self.sk[:20])
        return True
    
    def eh(self):
        print("\n[3] EH")
        self.magic = "".join(random.choices(CHARSET, k=64))
        dtf = build_dtf(self.sk)
        pf = build_proof(self.ak, dtf, self.did)
        mid = build_mid(self.ak)
        dd_json = json.dumps({"proof": pf, "mid": mid, "ver": VER, "host": "app.mitos.is"},
                             separators=(",", ":"))
        R10 = (int(time.time() * 1000) ^ random.randint(0, M)) & M
        dd_raw = m2xc_encrypt_full(eb(dd_json), eb(self.magic), R10, random.randint(0, M))
        dd = m2xc_fmt(dd_raw)
        pub = serialization.load_pem_public_key(self.rk.encode())
        ms = base64.b64encode(pub.encrypt(self.magic.encode(), padding.PKCS1v15())).decode()
        params = [
            ("go", "0"), ("dd", dd), ("de", "desktop"), ("gi", "0"),
            ("ver", VER), ("it", "1"), ("do", "eh"), ("im", "0"),
            ("di", DESKTOP), ("dtf", dtf), ("ms", ms), ("rndx", rndx()),
        ]
        r = self.session.get(ENGINE + "?" + urllib.parse.urlencode(params), verify=False)
        print("  OK %s" % r.text[:80] if r.text else "(empty)")
        return True
    
    def api(self, payload):
        body_json = json.dumps(payload, separators=(",", ":"))
        enc = m2xc_encrypt_full(eb(body_json), eb(self.magic), 0, 0)
        body = m2xc_fmt(enc)
        url = ENGINE + "?_sid=" + urllib.parse.quote(self.sk, safe="") + "&rndx=" + rndx()
        r = self.session.post(url, data=body, verify=False, timeout=15)
        t = r.text
        if not t: return {}
        if t.startswith("tBB,"):
            blob = base64.b64decode(t[4 + 8:])
            if blob[:4] == b"M2XC":
                dec = m2xc_decrypt_full(blob, eb(self.magic))
                try: return json.loads(dec)
                except: return {"_raw": dec.decode("utf-8", errors="replace")[:200]}
            return {"_raw": t[:200]}
        try: return json.loads(t)
        except: return {"_raw": t[:200]}
    
    def connect_server(self):
        print("\n[4] CONNECT")
        r = self.api({"do": "connect", "invite": False, "defered": True,
                      "i": 1, "gm": -1, "retrying": False, "locale": "es_CO"})
        print("  OK %s" % json.dumps(r, ensure_ascii=False)[:200])
        
        if "data" in r and "server" in r["data"]:
            server = r["data"]["server"]
            token = r["data"]["token"]
            print("  Server: %s" % server)
            print("  Token: %s" % token[:20])
            
            # Parse server address
            if ":" in server:
                host, port = server.split(":")
                port = int(port)
            else:
                host = server
                port = 443
            
            # TCP connection
            self.tcp = MitosisTCP(host, token[:8])
            if self.tcp.connect(port):
                print("  TCP connected!")
                # Send initial handshake
                handshake = b"MTX" + bytes([0] * 22)
                self.tcp.send_raw(handshake)
                print("  Sent MTX handshake")
        
        return r
    
    def join_private_room(self, room_name):
        print("\n[5] JOIN PRIVATE ROOM: %s" % room_name)
        r = self.api({"do": "join_private_room", "room": room_name})
        print("  OK %s" % json.dumps(r, ensure_ascii=False)[:200])
        return r
    
    def spawn(self):
        print("\n[6] SPAWN")
        # Send spawn command
        r = self.api({"do": "spawn"})
        print("  OK %s" % json.dumps(r, ensure_ascii=False)[:200])
        return r
    
    def run(self):
        print("=" * 60)
        print("  MitosisOG Full Protocol Replication")
        print("=" * 60)
        
        if not self.did:
            print("ERROR: Device ID not found")
            return
        
        try:
            self.knock()
            self.lim()
            self.eh()
            self.connect_server()
            
            # Join private room "asjakka"
            self.join_private_room("asjakka")
            
            # Spawn
            self.spawn()
            
            # Keep alive
            print("\n[7] KEEPING ALIVE (30 seconds)")
            for i in range(30):
                time.sleep(1)
                if i % 5 == 0:
                    print("  %ds..." % (30 - i))
            
            print("\n" + "=" * 60)
            print("  DONE - Full protocol replicated!")
            print("=" * 60)
            
        except Exception as e:
            print("\nERROR: %s" % e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    client = MitosisClient()
    client.run()
