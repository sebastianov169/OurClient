#!/usr/bin/env python3
"""
full_login_and_api.py - TODO en un solo archivo, sin imports de otros .py
M2XC + DTF + str_dest + Login + API payloads
"""
import json, hashlib, base64, struct, random, time, urllib.parse, os, sys
import requests, urllib3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ================================================================
# v5OH2 (AES-CBC) Decryption — loginifneeded/chattoken usan este
# cifrado en las respuestas tBB; sin el fallback el uid quedaba
# vacio y el mmm nunca se enviaba (CTF publico sin spawn)
# ================================================================
V5OH2_IV = bytes([
    0x20, 0x0b, 0x5d, 0x31, 0x79, 0x6f, 0x03, 0x2c,
    0x13, 0x23, 0x3b, 0x65, 0x54, 0x3a, 0x0b, 0x5f
])

def aes_key(secret):
    """Derive AES-128 key from a secret string (game-exact)."""
    v = [11] * 16
    e = secret.encode() if isinstance(secret, str) else secret
    for i in range(len(e)):
        slot = i % 16
        v[slot] = (v[slot] + e[slot] + e[i]) & 0xFF
    return bytes(v)

def decrypt_v5oh2(data, magic_key):
    """Decrypt v5OH2 (AES-CBC) encrypted data with aes_key(magic)."""
    key = aes_key(magic_key)
    cipher = Cipher(algorithms.AES(key), modes.CBC(V5OH2_IV))
    dec = cipher.decryptor()
    return dec.update(data) + dec.finalize()

urllib3.disable_warnings()

API = "https://app.mitos.is"
ENGINE = f"{API}/engine_beta.php"
VER = "10.1.8"
DESKTOP = "ASUSTeK COMPUTER INC.;1.0;Microsoft Windows 11 Enterprise LTSC;Windows;10.0.26100;x86;1920;1080"
CHARSET = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM0123456789"
M = 0xFFFFFFFF

def eb(s):
    return s.encode("ascii") if isinstance(s, str) else bytes(s)

def rndx():
    return f"{random.random():.15f}"

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
# MAIN
# ================================================================
def main():
    print("=" * 60)
    print("  MitosisOG - Login + API Payloads (100% M2XC)")
    print("=" * 60)

    did = load_device_id()
    ak = load_attest_key()
    s = requests.Session()
    s.headers["User-Agent"] = "libcurl-agent/1.0"

    # 1. KNOCK
    r = s.get(ENGINE + "?do=knock&rndx=" + rndx(), verify=False).json()
    assert r["result"] == "ok", "KNOCK: %s" % r
    token = r["data"]["token"]
    print("  [1] KNOCK  OK  token=%dc" % len(token))

    # 2. LIM
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
        print("  [2] LIM    FAIL  %s" % json.dumps(r)[:200])
        return
    dk_blob = parse_m2xc_blob(r["data"]["dk"])
    dm_blob = parse_m2xc_blob(r["data"]["dm"])
    dk_key = hashlib.md5((token + did).encode()).hexdigest()
    dm_key = hashlib.md5((did + token).encode()).hexdigest()
    sk = m2xc_decrypt_full(dk_blob, eb(dk_key)).decode()
    rk = m2xc_decrypt_full(dm_blob, eb(dm_key)).decode()
    print("  [2] LIM    OK  sk=%s...  rk=%db" % (sk[:20], len(rk)))

    # 3. EH
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
    tag = "OK  %s" % r.text[:80] if r.text else "(empty)"
    print("  [3] EH     %s" % tag)

    # 4. API helper
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

    # 5. PAYLOADS
    print("")
    print("-- API PAYLOADS --")
    r = api({"do": "news"})
    print("  do=news        -> %s" % json.dumps(r, ensure_ascii=False)[:200])
    r = api({"do": "chattoken"})
    print("  do=chattoken   -> %s" % json.dumps(r, ensure_ascii=False)[:200])
    r = api({"do": "connect", "invite": False, "defered": True,
             "i": 1, "gm": -1, "retrying": False, "locale": "es_CO"})
    print("  do=connect     -> %s" % json.dumps(r, ensure_ascii=False)[:200])
    r = api({"do": "inventory", "ingame": True, "slot": 3})
    print("  do=inventory   -> %s" % json.dumps(r, ensure_ascii=False)[:200])
    r = api({"do": "mmm", "begin": False, "serching": False,
             "add": "[-192895987,\"\",100,0]", "tag": 1,
             "abandon": False, "mode": -1, "stop": False})
    print("  do=mmm         -> %s" % json.dumps(r, ensure_ascii=False)[:200])
    r = api({"do": "i18n", "update": 1784749724, "locale": "es_CO"})
    print("  do=i18n        -> %s..." % json.dumps(r, ensure_ascii=False)[:200])
    print("")
    print("-- DONE --")

if __name__ == "__main__":
    main()
