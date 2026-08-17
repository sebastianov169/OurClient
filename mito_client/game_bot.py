#!/usr/bin/env python3
"""
game_bot.py - MitosisOG game connection bot
Logs in via HTTP, connects via TCP, stays connected with keepalives.
"""

import json, hashlib, base64, struct, random, time, urllib.parse, os, sys
import socket, select, ssl
import requests, urllib3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
urllib3.disable_warnings()

API = "https://app.mitos.is"
ENGINE = f"{API}/engine_beta.php"
VER = "10.1.8"
DESKTOP = "ASUSTeK COMPUTER INC.;1.0;Microsoft Windows 11 Enterprise LTSC;Windows;10.0.26100;x86;1920;1080"
CHARSET = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM0123456789"
M = 0xFFFFFFFF
EXT_ID = 495
MODE_ID = 63
TCP_SUFFIX_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def eb(s):
    return s.encode("ascii") if isinstance(s, str) else bytes(s)

def rndx():
    return f"{random.random():.15f}"

def generate_suffix(length=8):
    return "".join(random.choices(TCP_SUFFIX_CHARS, k=length))

# ================================================================
# M2XC
# ================================================================
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

def keystream_xxtea(key_bytes, state, SUM, counter_offset=0, pass_b=False):
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

def swfinalize_passb(s):
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
        byte_out = (((xor_val >> shift) & 0xFF) ^ inp_byte)
        byte_out += ((sel_word >> shift) & 0xFF)
        byte_out += (H & 0xFF)
        byte_out += (pos & 0xFF)
        out[pos] = byte_out & 0xFF
        w0, w1, w2, w3 = w0_new, w1_new, w2_new, w3_new
    return bytes(out)

def transform2(data, ha, hb, counter_offset=0):
    prev = hb & 0xFF
    out = bytearray(len(data))
    for i in range(len(data)):
        pos = i + counter_offset
        shift = (i & 3) << 3
        ha_shift = (ha >> shift) & M
        val = (data[i] ^ ((ha_shift + prev + pos) & 0xFF) ^ prev) & 0xFF
        out[i] = val
        prev = val
    return bytes(out)

def m2xc_encrypt_full(data_bytes, key_bytes, H1, H2, tls_value="0x0", counter_offset=0):
    H1 &= M; H2 &= M
    DATA = bytes(data_bytes); KEY = bytes(key_bytes)
    len_data = len(DATA); len_key = len(KEY)
    s1 = [
        fmix((len_data ^ H1 ^ 0x243f6a88) & M),
        fmix((H2 ^ 0x85a308d3) & M),
        fmix((len_key ^ rol(H1, 7) ^ 0x13198a2e) & M),
        fmix((rol(H2, 11) ^ 0x3707344) & M),
    ]
    s1 = keystream_xxtea(KEY, s1, (H1 + H2) & M, 0, pass_b=False)
    s1 = swfinalize_passa(s1)
    round1 = transform1(DATA, s1, H1, pass_b=False)
    round2 = transform2(round1, H1, H2, counter_offset=0)
    seed_a = H1 ^ 0x6a09e667
    seed_b = H2 ^ 0xbb67ae85
    KS2 = struct.pack('>IIIII', 0x19731f72, H1, H2, len_data, len(round2)) + round2
    s2 = [
        fmix((len(KS2) ^ seed_a ^ 0x243f6a88) & M),
        fmix((H2 ^ 0x3ec4a656) & M),
        fmix((len_key ^ rol(seed_a, 7) ^ 0x13198a2e) & M),
        fmix((rol(seed_b, 11) ^ 0x3707344) & M),
    ]
    s2 = keystream_xxtea(KEY, s2, (seed_a + seed_b) & M, 0, pass_b=True)
    s2 = swfinalize_passb(s2)
    round3 = transform1(KS2, s2, seed_a, pass_b=True)
    round4 = transform2(round3, seed_a, seed_b, counter_offset=0)
    H3 = struct.unpack('>I', round4[:4].ljust(4, b'\x00'))[0]
    blob = b'M2XC' + struct.pack('>I', H1) + struct.pack('>I', H2) + struct.pack('>I', H3) + round2
    return blob

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
    s1 = keystream_xxtea(KEY, s1, (H1 + H2) & M, 0, pass_b=False)
    s1 = swfinalize_passa(s1)
    round1 = inverse_transform2(payload, H1, H2, counter_offset=0)
    plaintext = inverse_transform1(round1, s1, H1, pass_b=False)
    return plaintext

# ================================================================
# M2XC blob format
# ================================================================
def m2xc_fmt(blob):
    return f"{len(blob) - 16:08d}" + base64.b64encode(blob).decode()

def parse_m2xc_blob(s):
    return base64.b64decode(s[8:])

# ================================================================
# DTF mix (game-exact)
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
# Attestation
# ================================================================
def load_attest_key():
    for fn in ["tpm_attestation.pem", "embedded_rsa_private_14.pem",
               "embedded_rsa_private_16.pem"]:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), fn)
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
    qw = os.path.expandvars(r"%APPDATA%\Freakinware\MitosisOG\qw.sol")
    with open(qw, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    i = txt.find("y8:deviceIdy")
    after = txt[i + len("y8:deviceIdy"):]
    c = after.find(":"); n = int(after[:c])
    return urllib.parse.unquote(after[c + 1:c + 1 + n])

# ================================================================
# Login (HTTP)
# ================================================================
def do_login():
    did = load_device_id()
    ak = load_attest_key()
    s = requests.Session()
    s.headers["User-Agent"] = "libcurl-agent/1.0"

    print("  [1] KNOCK...")
    r = s.get(ENGINE + "?do=knock&rndx=" + rndx(), verify=False).json()
    assert r["result"] == "ok", "KNOCK: %s" % r
    token = r["data"]["token"]
    print("  [1] KNOCK  OK  token=%dc" % len(token))

    print("  [2] LIM...")
    p0, _ = str_dest(token)
    edid = m2xc_fmt(m2xc_encrypt_full(eb(did), eb(p0), 0xBC461A49, 0x7C2359AB))
    chk = hashlib.md5(("_chk91822" + did + "l.o.x").encode()).hexdigest()
    qs = urllib.parse.urlencode([
        ("rus", "1"), ("loc", "es_CO"), ("ver", VER), ("dds", "1920x1080"),
        ("do", "lim"), ("t", token), ("ddd", DESKTOP), ("fmt", "tbt"),
        ("chk", chk), ("did", edid), ("rndx", rndx()),
    ])
    r = s.get(ENGINE + "?" + qs, verify=False).json()
    if r["result"] != "ok":
        raise RuntimeError("LIM failed: %s" % json.dumps(r)[:300])
    dk_blob = parse_m2xc_blob(r["data"]["dk"])
    dm_blob = parse_m2xc_blob(r["data"]["dm"])
    dk_key = hashlib.md5((token + did).encode()).hexdigest()
    dm_key = hashlib.md5((did + token).encode()).hexdigest()
    sk = m2xc_decrypt_full(dk_blob, eb(dk_key)).decode()
    rk = m2xc_decrypt_full(dm_blob, eb(dm_key)).decode()
    print("  [2] LIM    OK  sk=%s...  rk=%db" % (sk[:20], len(rk)))

    print("  [3] EH...")
    magic = "".join(random.choices(CHARSET, k=64))
    dtf = build_dtf(sk)
    pf = build_proof(ak, dtf, did)
    mid = build_mid(ak)
    dd_json = json.dumps({"proof": pf, "mid": mid, "ver": VER, "host": "app.mitos.is"},
                         separators=(",", ":"))
    R10 = (int(time.time() * 1000) ^ random.randint(0, M)) & M
    dd_raw = m2xc_encrypt_full(eb(dd_json), eb(magic), R10, random.randint(0, M))
    dd = m2xc_fmt(dd_raw)
    pub = serialization.load_pem_public_key(rk.encode())
    ms = base64.b64encode(pub.encrypt(magic.encode(), padding.PKCS1v15())).decode()
    params = [
        ("go", "0"), ("dd", dd), ("de", "desktop"), ("gi", "0"),
        ("ver", VER), ("it", "1"), ("do", "eh"), ("im", "0"),
        ("di", DESKTOP), ("dtf", dtf), ("ms", ms), ("rndx", rndx()),
    ]
    r = s.get(ENGINE + "?" + urllib.parse.urlencode(params), verify=False)
    print("  [3] EH     OK  (%s)" % r.text[:60] if r.text else "(empty)")

    def api(payload):
        body_json = json.dumps(payload, separators=(",", ":"))
        enc = m2xc_encrypt_full(eb(body_json), eb(magic), 0, 0)
        body = m2xc_fmt(enc)
        url = ENGINE + "?_sid=" + urllib.parse.quote(sk, safe="") + "&rndx=" + rndx()
        r = s.post(url, data=body, verify=False, timeout=15)
        t = r.text
        if not t: return {}
        if t.startswith("tBB,"):
            blob = base64.b64decode(t[4 + 8:])
            if blob[:4] == b"M2XC":
                dec = m2xc_decrypt_full(blob, eb(magic))
                try: return json.loads(dec)
                except: return {"_raw": dec.decode("utf-8", errors="replace")[:200]}
            return {"_raw": t[:200]}
        try: return json.loads(t)
        except: return {"_raw": t[:200]}

    return s, api, magic, sk

# ================================================================
# TCP helpers
# ================================================================
def m2xc_encrypt_tcp(data_str, key_str):
    h1 = random.randint(0, M)
    h2 = random.randint(0, M)
    return m2xc_encrypt_full(eb(data_str), eb(key_str), h1, h2)

def tcp_send_msg(sock, data_str, key_str):
    blob = m2xc_encrypt_tcp(data_str, key_str)
    text = m2xc_fmt(blob)
    print("  >>> SEND (%d bytes): %s" % (len(text), data_str[:120]))
    sock.sendall(text.encode("ascii"))

def hex_dump(data, max_bytes=256):
    for i in range(0, min(len(data), max_bytes), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join('%02x' % b for b in chunk)
        asc_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print("    %04x: %-48s %s" % (i, hex_str, asc_str))
    if len(data) > max_bytes:
        print("    ... (%d more bytes)" % (len(data) - max_bytes))

def parse_text_msg(data, offset=0):
    if len(data) - offset < 8:
        return None, 0
    header = data[offset:offset+8]
    if not all(c in b'0123456789' for c in header):
        return None, 0
    payload_len = int(header)
    blob_len = payload_len + 16
    b64_len = ((blob_len + 2) // 3) * 4
    total = 8 + b64_len
    if len(data) - offset < total:
        return None, 0
    b64_str = data[offset+8:offset+total]
    try:
        blob = base64.b64decode(b64_str)
        return blob, total
    except Exception:
        return None, 0

def try_decrypt_blob(blob, key_str, label=""):
    try:
        if blob[:4] == b'M2XC':
            dec = m2xc_decrypt_full(blob, eb(key_str))
            text = dec.decode("utf-8", errors="replace")
            print("  <<< DECRYPT%s: %s" % (label, text[:500]))
            try:
                return json.loads(text)
            except Exception:
                return {"_raw": text[:300]}
        return None
    except Exception as e:
        print("  <<< DECRYPT FAILED%s: %s" % (label, e))
        return None

def process_buffer(buf, key_str):
    processed = 0
    while processed < len(buf):
        remaining = buf[processed:]
        if len(remaining) < 4:
            break

        # Try text format first
        if len(remaining) >= 8 and all(c in b'0123456789' for c in remaining[:8]):
            blob, consumed = parse_text_msg(remaining)
            if blob and consumed > 0:
                try_decrypt_blob(blob, key_str)
                processed += consumed
                continue
            else:
                break

        # Try M2XC binary
        if remaining[:4] == b'M2XC':
            next_m2xc = remaining.find(b'M2XC', 4)
            if next_m2xc > 0:
                chunk = remaining[:next_m2xc]
            else:
                chunk = remaining
            try_decrypt_blob(chunk, key_str, " [binary]")
            processed += len(chunk)
            continue

        # Try to find M2XC anywhere
        idx = remaining.find(b'M2XC')
        if idx > 0:
            processed += idx
            continue

        # Skip unknown byte
        processed += 1

    return buf[processed:]

# ================================================================
# MAIN BOT
# ================================================================
def main():
    print("=" * 60)
    print("  MitosisOG Game Bot")
    print("=" * 60)

    while True:
        try:
            # --- LOGIN ---
            print("\n" + "=" * 60)
            print("  PHASE 1: HTTP LOGIN")
            print("=" * 60)
            s, api, magic, sk = do_login()

            # --- GET SERVER ---
            print("\n" + "=" * 60)
            print("  PHASE 2: GET SERVER")
            print("=" * 60)
            connect_resp = api({"do": "connect", "invite": False, "defered": True,
                                "i": 1, "gm": -1, "retrying": False, "locale": "es_CO"})
            print("  do=connect -> %s" % json.dumps(connect_resp, ensure_ascii=False)[:400])

            connect_data = connect_resp.get("data", {})
            server_str = connect_data.get("server", "")
            game_token = connect_data.get("token", "")

            if not server_str or not game_token:
                print("  ! No server/token from do=connect, retrying in 5s...")
                time.sleep(5)
                continue

            parts = server_str.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 443

            suffix = generate_suffix(8)
            tcp_key = host + suffix

            print("  server   = %s:%d" % (host, port))
            print("  token    = %s" % game_token[:60])
            print("  suffix   = %s" % suffix)
            print("  tcp_key  = %s" % tcp_key)

            # --- TCP CONNECT ---
            print("\n" + "=" * 60)
            print("  PHASE 3: TCP CONNECTION")
            print("=" * 60)

            sock = None
            use_tls = False

            # Try raw TCP first
            try:
                print("  Trying raw TCP to %s:%d..." % (host, port))
                sock = socket.create_connection((host, port), timeout=10)
                print("  Raw TCP connected!")
            except Exception as e:
                print("  Raw TCP failed: %s" % e)

            # Try TLS if raw failed
            if not sock:
                try:
                    print("  Trying TLS to %s:%d..." % (host, port))
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    raw = socket.create_connection((host, port), timeout=10)
                    sock = ctx.wrap_socket(raw, server_hostname=host)
                    use_tls = True
                    print("  TLS connected! Protocol: %s" % sock.version())
                except Exception as e:
                    print("  TLS failed: %s" % e)

            if not sock:
                print("  ! All connection attempts failed, retrying in 5s...")
                time.sleep(5)
                continue

            # --- READ GREETING ---
            print("\n-- Server Greeting --")
            sock.settimeout(5)
            greeting = b""
            try:
                greeting = sock.recv(8192)
            except socket.timeout:
                print("  (no greeting received, timeout)")
            except Exception as e:
                print("  Greeting error: %s" % e)

            print("  Greeting: %d bytes" % len(greeting))
            if greeting:
                hex_dump(greeting, 256)

                # Check if it's actually TLS wrapping
                if greeting[:2] == b'\x16\x03':
                    print("  ! Looks like TLS ServerHello, reconnecting with TLS...")
                    sock.close()
                    try:
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        raw = socket.create_connection((host, port), timeout=10)
                        sock = ctx.wrap_socket(raw, server_hostname=host)
                        use_tls = True
                        print("  TLS connected!")
                        greeting = sock.recv(8192)
                        print("  New greeting: %d bytes" % len(greeting))
                        if greeting:
                            hex_dump(greeting, 256)
                    except Exception as e:
                        print("  TLS reconnect failed: %s" % e)
                        sock.close()
                        time.sleep(5)
                        continue

                # Try to decrypt greeting
                if greeting[:4] == b'M2XC':
                    print("  Greeting is raw M2XC blob")
                    try_decrypt_blob(greeting, tcp_key, " [greeting]")
                elif len(greeting) >= 8 and all(c in b'0123456789' for c in greeting[:8]):
                    print("  Greeting is text format")
                    blob, consumed = parse_text_msg(greeting)
                    if blob:
                        try_decrypt_blob(blob, tcp_key, " [greeting]")
                else:
                    # Binary protocol header - try to find M2XC inside
                    idx = greeting.find(b'M2XC')
                    if idx >= 0:
                        print("  M2XC found at offset %d in greeting" % idx)
                        try_decrypt_blob(greeting[idx:], tcp_key, " [greeting]")
                    else:
                        print("  Unknown format, first bytes: %s" % greeting[:16].hex())
                        # Try interpreting as binary with 2-byte BE length
                        if len(greeting) >= 2:
                            be_len = struct.unpack('>H', greeting[:2])[0]
                            print("  If 2-byte BE length: %d (0x%04x)" % (be_len, be_len))

            # --- SEND HANDSHAKE ---
            print("\n-- Handshake --")
            handshake_plain = "%s;;::===ext:%d;;::===mode:%d" % (game_token, EXT_ID, MODE_ID)
            print("  Plaintext: %s" % handshake_plain[:100])

            blob = m2xc_encrypt_tcp(handshake_plain, tcp_key)
            text_msg = m2xc_fmt(blob)
            first_msg = suffix.encode("ascii") + text_msg.encode("ascii")
            print("  Sending: suffix(%d) + text_msg(%d) = %d bytes" % (
                len(suffix), len(text_msg), len(first_msg)))
            sock.sendall(first_msg)

            # --- READ RESPONSE ---
            print("\n-- Server Response --")
            sock.settimeout(10)
            resp = b""
            try:
                resp = sock.recv(8192)
            except socket.timeout:
                print("  (no response, timeout)")
            except Exception as e:
                print("  Response error: %s" % e)

            print("  Response: %d bytes" % len(resp))
            if resp:
                hex_dump(resp, 512)

                if resp[:4] == b'M2XC':
                    print("  Response is raw M2XC blob")
                    try_decrypt_blob(resp, tcp_key, " [response]")
                elif len(resp) >= 8 and all(c in b'0123456789' for c in resp[:8]):
                    print("  Response is text format")
                    blob, consumed = parse_text_msg(resp)
                    if blob:
                        try_decrypt_blob(blob, tcp_key, " [response]")
                else:
                    idx = resp.find(b'M2XC')
                    if idx >= 0:
                        print("  M2XC at offset %d in response" % idx)
                        try_decrypt_blob(resp[idx:], tcp_key, " [response]")
                    else:
                        print("  Unknown format, first bytes: %s" % resp[:16].hex())

            # --- SEND INITIAL MESSAGES ---
            print("\n-- Initial Game Messages --")
            time.sleep(0.3)

            tcp_send_msg(sock, json.dumps({
                "do": "loginifneeded", "at": "", "wt": "",
                "usertoken": "steam::76561198813465200"
            }, separators=(",", ":")), tcp_key)

            time.sleep(0.3)

            tcp_send_msg(sock, json.dumps({
                "do": "inventory", "ingame": True, "slot": 3
            }, separators=(",", ":")), tcp_key)

            time.sleep(0.3)

            tcp_send_msg(sock, json.dumps({
                "do": "news"
            }, separators=(",", ":")), tcp_key)

            # --- MAIN LOOP ---
            print("\n" + "=" * 60)
            print("  PHASE 4: MAIN LOOP (keepalive every 5s)")
            print("=" * 60)
            last_keepalive = time.time()
            last_recv_time = time.time()
            buffer = b""
            msg_count = 0

            while True:
                try:
                    ready = select.select([sock], [], [], 0.5)
                    if ready[0]:
                        data = sock.recv(8192)
                        if not data:
                            print("\n  ! Connection closed by server")
                            break

                        last_recv_time = time.time()
                        msg_count += 1
                        print("\n  [msg #%d] RECV %d bytes:" % (msg_count, len(data)))
                        hex_dump(data, 512)

                        buffer += data
                        buffer = process_buffer(buffer, tcp_key)

                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                    print("\n  ! Connection error: %s" % e)
                    break
                except Exception as e:
                    print("\n  ! Read error: %s" % e)
                    break

                # Keepalive every 5 seconds
                now = time.time()
                if now - last_keepalive >= 5:
                    try:
                        tcp_send_msg(sock, json.dumps({"do": "ka"}, separators=(",", ":")), tcp_key)
                        last_keepalive = now
                    except Exception as e:
                        print("  ! Keepalive send error: %s" % e)
                        break

                # Timeout: no data for 60 seconds
                if now - last_recv_time > 60:
                    print("\n  ! No data for 60s, reconnecting...")
                    break

            # --- CLEANUP ---
            try:
                sock.close()
            except Exception:
                pass
            print("  Connection closed, reconnecting in 3s...")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\n\n  Ctrl+C - exiting.")
            break
        except Exception as e:
            print("\n  ! FATAL ERROR: %s" % e)
            import traceback
            traceback.print_exc()
            print("  Retrying in 5s...")
            time.sleep(5)

    print("\n  Bot stopped.")


if __name__ == "__main__":
    main()
