#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# room_keepalive.py - MITOSISOG: login HTTP + join a sala por nombre exacto +
# spawn TCP + keepalive, midiendo cuanto dura la conexion antes de morir.
#
# Uso:
#   python room_keepalive.py --device "<device_id>" --pem <ruta.pem> \
#       --room "SUDA GEAR COMP" [--duration 600] [--spawn-wait 60]
#
# Flujo (verificado contra server real):
#   1. login HTTP (knock/lim/eh) -> sk + magic
#   2. findrooms -> buscar la sala con code == --room (exacto, case-insensitive)
#   3. joinroom(code) -> invite_string
#   4. connect(invite=i) -> server + token TCP
#   5. TCP: greeting(suffix) -> AUTH(con invite) -> READY -> keepalive
# El script mantiene la conexion (ping 2s + move 1s + UDP 1s) y reporta
# cada 10s el tiempo vivo. Al morir (socket cerrado / timeout / pos=0) loguea
# los segundos totales de vida.
import argparse
import base64
import json
import os
import socket
import struct
import sys
import time
import threading as _th
import builtins as _bi

# print thread-safe con prefijo de cuenta (multi-cuenta en hilos)
_print_lock = _th.Lock()
_tlocal = _th.local()
_orig_print = _bi.print


def _safe_print(*a, **k):
    name = getattr(_tlocal, "account", None)
    with _print_lock:
        if name:
            _orig_print("[%s] " % name, *a, **k)
        else:
            _orig_print(*a, **k)


_bi.print = _safe_print

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import tcp_full as TF
import tcp_client as TC  # do_login / make_auth_frame helpers

M = 0xFFFFFFFF


# ===================== decode TCP post-AUTH (port de tcp_farm.cpp) ==========
def xorshift32(v):
    v &= M
    v ^= (v << 13) & M
    v ^= v >> 17
    v ^= (v << 5) & M
    return v & M


def m2xc_tcp_dec(data, seed, ts=100):
    """m2xcTcpDec del C++ (tcp_farm.cpp:477): keystream simple con seed."""
    n = len(data)
    so = (ts - 100) & M
    uvar10 = (seed - 0x59 + n) & 0xFF
    uvar20 = (n * 0x45d9f3b ^ so ^ seed ^ 0x6d2b79f5) & M
    uvar21 = 0
    out = bytearray(n)
    for i in range(n):
        uvar10 &= 0xFF
        uvar20 = (i + uvar10 + uvar20) & M
        uvar20 = xorshift32(uvar20)
        shift = (i & 3) << 3
        ks_byte = (uvar20 >> shift) & 0xFF
        add_byte = ((uvar20 >> 0xB) + uvar21 + seed) & 0xFF
        uvar4 = data[i]
        out[i] = (uvar4 ^ ks_byte ^ add_byte ^ uvar10) & 0xFF
        uvar10 = (uvar4 + 0x1F + i + uvar10)
        uvar21 = (uvar21 + 0x11) & M
    return bytes(out)


def xor_step(data, seed):
    out = bytearray(len(data))
    for i in range(len(data)):
        cvar1 = i & 0xFF
        uvar10 = (i + seed) & 0x0F
        keybyte = (cvar1 * cvar1 + uvar10 + (seed & 0xFF)) & 0xFF
        out[i] = data[i] ^ keybyte
    return bytes(out)


def interleave_inv(data, half, parity):
    if len(data) % 4 == 2:
        return data
    orig = bytearray(len(data))
    for i in range(half):
        swap = ((i & 1) != parity)
        pa = (half - 1 - i) if (i & 1) == 0 else (half + i)
        pb = (half - 2 - i) if (i & 1) == 0 else (half + i - 1)
        ra = data[pa]
        rb = data[pb]
        if swap:
            orig[i] = rb
            orig[2 * half - 1 - i] = ra
        else:
            orig[i] = ra
            orig[2 * half - 1 - i] = rb
    return bytes(orig)


def decode_tcp_frame(payload, seed):
    """decodeFrame del C++ (tcp_farm.cpp:1041): intento 1 m2xcTcp, intento 2
    desturple. Devuelve (amf_value, method) o (None, None)."""
    n = len(payload)
    if n < 4 or n % 2 != 0:
        return None, None
    half = n // 2
    # intento 1: m2xc path
    try:
        dec = m2xc_tcp_dec(payload, seed)
        dec = xor_step(dec, seed)
        dec = interleave_inv(dec, half, seed & 1)
        if len(dec) > 0 and dec[0] <= 0x09:
            d = TF.Amf3Decoder(dec)
            v = d.read_value()
            return v, "m2xctcp"
    except Exception:
        pass
    # intento 2: resturple
    try:
        dec = TF.bytearray_desturple(payload, seed)
        if len(dec) > 0 and dec[0] <= 0x09:
            d = TF.Amf3Decoder(dec)
            v = d.read_value()
            return v, "desturple"
    except Exception:
        pass
    return None, None


def interleave(data, half, parity):
    """interleave del C++ (tcp_farm.cpp:519) - direccion forward."""
    if len(data) % 4 == 2:
        return data
    res = bytearray(len(data))
    for i in range(half):
        swap = ((i & 1) != parity)
        a = data[i]
        b = data[2 * half - 1 - i]
        if swap:
            a, b = b, a
        if (i & 1) == 0:
            pa = half - 1 - i
            pb = half - 2 - i
        else:
            pa = half + i
            pb = half + i - 1
        res[pa] = a
        res[pb] = b
    return bytes(res)


def m2xc_tcp_enc(data, seed, ts=100):
    """m2xcTcpEnc del C++ (tcp_farm.cpp:452) - direccion forward."""
    n = len(data)
    so = (ts - 100) & M
    uvar10 = (seed - 0x59 + n) & 0xFF
    uvar20 = (n * 0x45d9f3b ^ so ^ seed ^ 0x6d2b79f5) & M
    uvar21 = 0
    out = bytearray(n)
    for i in range(n):
        uvar10 &= 0xFF
        uvar20 = (i + uvar10 + uvar20) & M
        uvar20 = xorshift32(uvar20)
        shift = (i & 3) << 3
        ks_byte = (uvar20 >> shift) & 0xFF
        add_byte = ((uvar20 >> 0xB) + uvar21 + seed) & 0xFF
        plain = data[i]
        out[i] = (plain ^ ks_byte ^ add_byte ^ uvar10) & 0xFF
        uvar10 = (out[i] + 0x1F + i + uvar10)
        uvar21 = (uvar21 + 0x11) & M
    return bytes(out)


def decrypt_challenge(challenge, suffix):
    """decryptChallenge del C++ (tcp_farm.cpp:822): quita el prefijo de 8
    digitos, decodifica base64 y descifra M2XC con la key = suffix."""
    c = challenge.strip()
    b64 = c
    if len(c) >= 8 and c[:8].isdigit() and int(c[:8]) != 0:
        b64 = c[8:]
    pad = (4 - (len(b64) % 4)) % 4
    b64 += "=" * pad
    blob = base64.b64decode(b64)
    if len(blob) < 4 or blob[:4] != b"M2XC":
        return ""
    dec = TC.m2xc_decrypt_full(blob, TC.eb(suffix))
    return dec.decode("utf-8", errors="replace")


def tcp_frame_from_logical(logical, seed):
    """Empaqueta un logical AMF como frame m2xcTcp (formato del C++
    makePongFrame/makeReadyFrame: m2xcTcpEnc(xorStep(interleave(...))))."""
    padded = logical + b"\x00"
    half = len(padded) // 2
    wire = m2xc_tcp_enc(xor_step(interleave(padded, half, seed & 1), seed), seed, 100)
    frame = struct.pack(">II", len(wire), len(logical)) + bytes([seed % 63]) + wire
    return frame


def make_pong_frame_cpp(seed, now_ms):
    """makePongFrame del C++ (tcp_farm.cpp:707): [10001.0, nowMs, seed%100]."""
    logical = TF.amf_array([TF.amf_double(10001.0), TF.amf_double(now_ms), TF.amf_int(seed % 100)])
    return tcp_frame_from_logical(logical, seed)


def make_ready_frame_cpp(seed):
    """makeReadyFrame del C++ (tcp_farm.cpp:728): [10000, [true,1920,1080,1,true]]."""
    logical = TF.amf_array([
        TF.amf_int(10000),
        TF.amf_array([TF.amf_bool(True), TF.amf_double(1920.0), TF.amf_double(1080.0),
                      TF.amf_int(1), TF.amf_bool(True)]),
    ])
    return tcp_frame_from_logical(logical, seed)


def make_entity_info_frame_cpp(seed):
    """makeEntityInfoFrame del C++ (tcp_farm.cpp:763): CLIENT_ENTITIES_INFO.

    [10002, [0]] + 1 cero, resturple. CRITICO (validado 2026-08-13 por subagente
    deleg_9c6a7655): el server SOLO envia el dump del mundo (6651 bytes, ~350
    entidades) cuando el cliente pide entidades explicitamente con este opcode.
    room_keepalive NUNCA lo enviaba -> el visor solo recibia '64' vacios y la X
    del jugador (0xc8). Evidencia: client_run.txt 'Sending CLIENT_ENTITIES_INFO
    (10002)...' -> 'ENTITY_DUMP: 6651 bytes, 350 records'; mito_bot2.log igual.
    """
    logical = TF.amf_array([TF.amf_int(10002), TF.amf_array([TF.amf_int(0)])])
    return tcp_frame_from_logical(logical, seed)


def make_entity_info_frame_auto(seed):
    """CLIENT_ENTITIES_INFO (10002) en resturple (flujo MODO AUTO, sin sala).
    Mismo opcode que make_entity_info_frame_cpp pero cifrado como tcp_full
    (make_client_frame -> bytearray_resturple), que es lo que acepta el server
    del modo AUTO (validado en vivo 2026-08-13 CTF)."""
    logical = TF.amf_array([TF.amf_int(10002), TF.amf_array([TF.amf_int(0)])])
    payload = logical + b"\x00"
    return TF.make_client_frame(payload, len(logical), seed % 63, seed)


def make_pong_frame_auto(seed, now_ms):
    """PONG del flujo AUTO en resturple: [10001.0, ts, seed%100].
    EXACTO del binario real (capture_ctf.log: 'OUT TCP ... seed=39570
    [10001.0, ts, 70]' -> 70 = 39570%100). El make_ping_frame de tcp_full
    manda [10001, ts] SIN el seed%100 y el server del modo lo corta."""
    logical = TF.amf_array([TF.amf_double(10001.0), TF.amf_double(now_ms),
                            TF.amf_int(seed % 100)])
    payload = logical + b"\x00\x00\x00"
    return TF.make_client_frame(payload, len(logical), seed % 63, seed)


def make_ready_frame_auto(seed):
    """READY del flujo AUTO en resturple: [10000, [true,1920,1080,1,true]].
    EXACTO del binario real (capture_ctf.log linea 643: [10000, [true, 1920.0,
    1080.0, 1, true]]). El make_ready_frame de tcp_full usa 2560x1440 y
    1.3333 -> el server del modo lo corta."""
    logical = TF.amf_array([
        TF.amf_int(10000),
        TF.amf_array([TF.amf_bool(True), TF.amf_double(1920.0), TF.amf_double(1080.0),
                      TF.amf_int(1), TF.amf_bool(True)]),
    ])
    payload = logical + b"\x00\x00"
    return TF.make_client_frame(payload, len(logical), seed % 63, seed)


def make_clear_10034_auto(seed):
    """CLEAR_10034 en resturple (flujo MODO AUTO). El del binario/control
    tcp_full: [10034] puro (sin argumentos) — hace que el server mande el
    [20] SPAWNED (validado: con 10034 llega el [20], sin el corta)."""
    logical = TF.amf_array([TF.amf_int(10034)])
    payload = logical + b"\x00\x00\x00"
    return TF.make_client_frame(payload, len(logical), seed % 63, seed)


def make_native_play_token_frame(seed, token):
    """NATIVE_PLAY [5, [token, false]] en resturple. EXACTO del binario real
    (capture_ctf.log: [5, ["00000008TTJYQwFLcPqvacfJGYxY7E728QFzaaeR", false]])
    — el token es el response del play HTTP. tcp_full manda [5, [false]] sin
    token y el server del modo NO spawnea."""
    logical = TF.amf_array([TF.amf_int(5),
                            TF.amf_array([TF.amf_string(token), TF.amf_bool(False)])])
    payload = logical + b"\x00\x00\x00"
    return TF.make_client_frame(payload, len(logical), seed % 63, seed)


def make_native_play_frame_cpp(seed, nonce, suffix, flag):
    """makeNativePlayFrameFlag del C++ (tcp_farm.cpp:799):
    [5, [m2xcFmt(m2xcEncrypt(nonce, suffix)), flag]]."""
    blob = TC.m2xc_encrypt_full(TC.eb(nonce), TC.eb(suffix), 0, 0)
    challenge = TC.m2xc_fmt(blob)
    logical = TF.amf_array([TF.amf_int(5), TF.amf_array([TF.amf_string(challenge), TF.amf_bool(flag)])])
    return tcp_frame_from_logical(logical, seed)


def random_nonce(n=8):
    import random as _r
    return "".join(_r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for _ in range(n))


def make_irc_frame(text):
    """makeIrcFrame del C++ (tcp_farm.cpp:876): amfString + pad a 4 + resturple."""
    logical = TF.amf_string(text)
    pad = (4 - (len(logical) % 4)) % 4
    payload = logical + b"\x00" * pad
    wire = TF.bytearray_resturple(payload, 0)
    chk = TF.get_byte_key(logical) & 0x3F
    return struct.pack(">II", len(wire), len(logical)) + bytes([chk]) + wire


def irc_handshake(irc_sock, ct_token):
    """Handshake IRC secuencial (tcp_farm.cpp:1539-1573). Devuelve bool."""
    irc_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789;_-"
    import random as _r

    def random48():
        return "".join(_r.choice(irc_chars) for _ in range(48))

    def send(t):
        irc_sock.sendall(make_irc_frame(t))

    def recv_until(needles, timeout_ms, buf=""):
        end = time.time() + timeout_ms / 1000.0
        acc = buf
        while time.time() < end:
            try:
                length, flag, payload = TF.recv_frame(irc_sock, 0.1)
            except Exception:
                length = None
            if length is not None and flag == 1 and payload and payload[0] <= 0x09:
                try:
                    d = TF.Amf3Decoder(payload)
                    v = d.read_value()
                    if isinstance(v, str):
                        acc += v
                except Exception:
                    pass
            for n in needles:
                if n in acc:
                    return True, acc
        return False, acc

    try:
        send("OPTIONS IRC")
        ok, got = recv_until(["AUTH RandomGate", "801 "], 4000)
        send("AUTH UserGate S :" + random48())
        ok, got = recv_until(["AUTH UserGate S :OK"], 6000)
        ggid = ct_token if ct_token else random48()
        send("AUTH UserGate GGID 0 S :" + ggid)
        ok, got = recv_until(["001 "], 6000)
        send("USERSTATUS ONLINE")
        print("[6i] IRC handshake OK (talk003)")
        return True
    except Exception as e:
        print("[6i] IRC handshake fallo: %s" % str(e)[:80])
        return False


def make_proof_frame(challenge, suffix, device_id, seed_mt, pem_path, nonce_override=""):
    """makeProofFrame del C++ (tcp_farm.cpp:916): firma el challenge con la
    clave de atestacion (PEM fake) y lo manda como [10035, proof]."""
    import hashlib
    if nonce_override:
        decrypted = nonce_override
    else:
        decrypted = decrypt_challenge(challenge, suffix)  # fallback local
    if not decrypted:
        raise RuntimeError("sin nonce (roundtrip HTTP + decryptChallenge fallaron)")
    msg = (decrypted + "|" + device_id + "|100").encode("ascii")
    # firmar: igual que rsaSignPkcs1Sha256 de crypto.cpp (firma el MSG crudo,
    # el signer hace el sha256 interno)
    key = _load_astro_pem(pem_path)
    sig = key.sign(msg, None, None)
    proof = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    logical = TF.amf_array([TF.amf_int(10035), TF.amf_string(proof)])
    return tcp_frame_from_logical(logical, seed_mt), proof


def make_auth_frame_invite(host, suffix, token, invite):
    """AUTH frame con invite: formato EXACTO del C++ (tcp_farm.cpp
    makeAuthFrame linea 687-705): m2xcEncryptFull(plaintext, key, 0, 0) ->
    m2xcFmt -> amfString -> payload=logical+0x00 ->
    checksum = getByteKey(LOGICAL) & 0x3F  (sin el 0x00, sin +8).
    Con checksum mal el server descarta el frame en silencio (0 frames)."""
    plain = token + "::i=" + invite + ";;::===ext:495"
    blob = TC.m2xc_encrypt_full(TC.eb(plain), TC.eb(host + suffix), 0, 0)
    s = TC.m2xc_fmt(blob)
    logical = TF.amf_string(s)
    payload = logical + b"\x00"
    checksum = TF.get_byte_key(logical) & 0x3F  # sobre LOGICAL, como el C++
    return TF.make_client_frame(payload, len(logical), checksum, 0)


def make_auth_frame_auto(host, suffix, token, mode):
    """AUTH sin invite del flujo MODO AUTO: EXACTO de astro (tcp_farm.cpp
    makeAuthFrame 709-727): plaintext
    'token;;::===ext:495;;::===mode:N' cifrado M2XC con host+suffix como key
    (m2xcEncryptFull + m2xcFmt, NO aes). Devuelve (frame, m2xc_string) — el
    string m2xc es TAMBIEN el body del AUTH HTTP del binario (astro lo manda
    por HTTP igual que por TCP)."""
    plain = token + ";;::===ext:495;;::===mode:%d" % mode
    blob = TC.m2xc_encrypt_full(TC.eb(plain), TC.eb(host + suffix), 0, 0)
    s = TC.m2xc_fmt(blob)
    logical = TF.amf_string(s)
    payload = logical + b"\x00"
    checksum = TF.get_byte_key(logical) & 0x3F
    return TF.make_client_frame(payload, len(logical), checksum, 0), s


def _der_read_len(buf, pos):
    b = buf[pos]; pos += 1
    if b < 0x80:
        return b, pos
    n = b & 0x7F
    length = 0
    for _ in range(n):
        length = (length << 8) | buf[pos]; pos += 1
    return length, pos


def _der_read_tlv(buf, pos):
    tag = buf[pos]; pos += 1
    length, pos = _der_read_len(buf, pos)
    return tag, buf[pos:pos + length], pos + length


def _der_read_int(buf, pos):
    tag, val, pos = _der_read_tlv(buf, pos)
    assert tag == 0x02, "no INTEGER"
    while len(val) > 1 and val[0] == 0:
        val = val[1:]
    return int.from_bytes(val, "big"), pos


def _load_astro_pem(pem_path):
    """Carga el PEM FAKE de Astro (formato propio, NO aceptado por
    cryptography porque los valores no cumplen las relaciones PKCS#1).
    Se parsea el DER a mano (igual que crypto.cpp parseRsaPrivateDer) y se
    devuelve una llave FAKE con la misma API que cryptography (sign() y
    private_numbers()) pero firmando con pow(m, d, n) puro, como hace la app."""
    import hashlib
    import base64 as _b64
    with open(pem_path, "rb") as f:
        pem = f.read()
    b64 = b"".join(l for l in pem.split(b"\n") if not l.startswith(b"-----"))
    der = _b64.b64decode(b64)
    pos = 0
    top_tag, top_val, pos = _der_read_tlv(der, pos)
    assert top_tag == 0x30, "not SEQUENCE"
    inner = 0
    ver, inner = _der_read_int(top_val, inner)
    n, inner = _der_read_int(top_val, inner)
    e, inner = _der_read_int(top_val, inner)
    d, inner = _der_read_int(top_val, inner)
    nums = {"n": n, "e": e, "d": d}
    bits = n.bit_length()

    class _FakeKey:
        key_size = bits

        def __init__(self, nn, ee, dd):
            self._nn = nn
            self._ee = ee
            self._dd = dd

        # sign(data, padding, algorithm): firma sha256(data) con PKCS#1 v1.5
        # usando pow(m, d, n) directo (sin validacion de los primos).
        def sign(self, data, padding, algorithm):
            import hashlib
            digest = hashlib.sha256(data).digest()
            prefix = bytes.fromhex("3031300d060960864801650304020105000420")
            em_len = (self._nn.bit_length() + 7) // 8
            t = prefix + digest
            ps = b"\xff" * (em_len - len(t) - 3)
            em = b"\x00\x01" + ps + b"\x00" + t
            s = pow(int.from_bytes(em, "big"), self._dd, self._nn)
            return s.to_bytes(em_len, "big")

        def private_numbers(self):
            class _PublicNumbers:
                def __init__(self, nn, ee):
                    self.n = nn
                    self.e = ee

            class _PrivateNumbers:
                def __init__(self, pub):
                    self.public_numbers = pub

            return _PrivateNumbers(_PublicNumbers(self._nn, self._ee))

    print("  [key] fake_tpm PEM (bits=%d) - signer manual" % bits)
    return _FakeKey(n, e, d)


# LOCK GLOBAL DE LOGIN: los loaders de tcp_client (load_device_id /
# load_attest_key) son VARIABLES DEL MODULO COMPARTIDO entre threads.
# do_login() los lee al inicio (tcp_client.py:370-371); si el thread A escribe
# sus loaders y antes de llegar a do_login() el thread B escribe los suyos, A
# usaria la clave/device de B (mid y proof INCORRECTOS). El lock serializa
# escritura+do_login como unidad atomica: cada cuenta usa SU device y SU PEM.
_LOGIN_LOCK = _th.Lock()


def login(device, pem_path):
    """Login HTTP con device + PEM explicitos (reescribe los loaders del
    modulo tcp_client para usar la cuenta indicada)."""
    with _LOGIN_LOCK:
        key = _load_astro_pem(pem_path)
        TC.load_device_id = lambda: device
        TC.load_attest_key = lambda: key
        return TC.do_login()  # (session, api, magic, sk)


def find_room(api, room_name):
    """findrooms -> devuelve el code EXACTO de la sala (o None).
    Nota: findrooms devuelve data=None hasta que hay sesion TCP al lobby;
    el joinroom directo por nombre funciona igual (verificado en vivo)."""
    try:
        r = api({"do": "findrooms"})
        lst = r.get("data", {}).get("list", []) if isinstance(r.get("data"), dict) else []
        if lst:
            target = room_name.strip().lower()
            exact = next((x for x in lst if str(x.get("code", "")).strip().lower() == target), None)
            if exact:
                return exact.get("code")
            sub = next((x for x in lst if target in str(x.get("code", "")).lower()), None)
            if sub:
                print("[room] sala exacta no encontrada, usando parecida: %r" % sub.get("code"))
                return sub.get("code")
    except Exception as e:
        print("[room] findrooms fallo (%s) - sigo con joinroom directo" % e)
    return None


def run_session(args):
    t0 = time.time()
    print("=" * 64)
    print("  ROOM KEEPALIVE: sala=%r device=%s..." % (args.room, args.device[:14]))
    print("=" * 64)

    # 1) login HTTP
    session, api, magic, sk = login(args.device, args.pem)
    print("[1] login OK (sk=%s...)" % sk[:16])

    # POST crudo del AUTH HTTP (mismo endpoint que api pero con body directo)
    def api_raw_post(body_str):
        import urllib.parse
        url = TC.ENGINE + "?_sid=" + urllib.parse.quote(sk, safe="") + "&rndx=" + TC.rndx()
        r = session.post(url, data=body_str,
                         headers={"User-Agent": "libcurl-agent/1.0",
                                  "Content-Type": "application/x-www-form-urlencoded"},
                         verify=False, timeout=15)
        t = r.text
        if not t:
            return ""
        if t.startswith("tBB,"):
            try:
                import base64 as _b
                blob = _b.b64decode(t[4 + 8:])
                if blob[:4] == b"M2XC":
                    dec = TC.m2xc_decrypt_full(blob, TC.eb(magic))
                    return dec.decode("utf-8", errors="replace")[:80]
            except Exception:
                pass
        return t[:80]

    # 1b) lobby: expulsar sala pegada + gamemode + servers + connect i=2.
    # (flujo validado en vivo HOY: el UNICO que llega al [20] SPAWNED en
    # modo AUTO — el flujo astro completo con i18n/loginifneeded/chattoken/
    # mmm llega al [53]+READY pero el server NUNCA manda el [20].)
    # SERVIDOR/MODO seleccionables en el lobby del visor (args.server/args.mode)
    room_val = (getattr(args, "room", "") or "").strip()
    modo_auto = room_val.lower() in ("", "auto", "automatico", "random")
    uid = ""
    ct_token = ""
    try:
        import time as _t
        now_ts = int(_t.time())
        # Expulsar la sala privada pegada (si la hay): joinroom a kjajajaja
        # (AHORA expirada -> room_code_invalid_or_expired, sin efecto, como
        # el flujo que SPAWNEA) + joinroom(__leave__) invalido. OJO: NO usar
        # una sala REAL aqui (p.ej. SUDA GEAR COMP): el joinroom valido mete
        # la cuenta en OTRA sala y el connect i=2 ya no devuelve la sala del
        # modo con [20] (validado en vivo: con SUDA GEAR COMP el [20] nunca
        # llega).
        try:
            api({"do": "joinroom", "code": "kjajajaja"})
            print("[1a] joinroom(kjajajaja) -> leave de sala previa")
        except Exception:
            pass
        try:
            api({"do": "joinroom", "code": "__leave__"})
            print("[1a] joinroom(__leave__) OK")
        except Exception as e:
            print("[1a] joinroom(__leave__) fallo (%s) - continuo" % e)
        gm_r = api({"do": "gamemode", "index": 1, "mode": getattr(args, "mode", 3)})
        print("[1b] gamemode HTTP -> %s" % json.dumps(gm_r)[:120])
        # region del servers change: astro usa kFarmRegions (europe,
        # central_america, south_america, australia) — las 4 salas CTF
        # PUBLICAS (user: "hay 4 conforme los servidores son").
        # "south_america" en este juego es SUDAFRICA.
        sv_r = api({"do": "servers", "change": getattr(args, "server", "europe")})
        print("[1b] servers change -> %s" % json.dumps(sv_r)[:120])
        if modo_auto:
            # EN MODO AUTO: NO loginifneeded/chattoken/i18n/mmm — el flujo
            # que SPAWNEA en vivo (2 corridas + el usuario jugando) no usa
            # nada de eso en AUTO.
            uid = ""
            ct_token = ""
        else:
            try:
                li = api({"do": "loginifneeded", "at": "", "wt": "",
                          "usertoken": None})
                uid = str(li.get("data", {}).get("uid", ""))
            except Exception:
                uid = ""
            try:
                r_ct = api({"do": "chattoken"})
                ct_token = r_ct.get("data", {}).get("token", "") if isinstance(r_ct.get("data"), dict) else ""
            except Exception:
                ct_token = ""
        if not modo_auto:
            c1 = api({"do": "connect", "invite": False, "defered": True,
                      "i": 1, "gm": -1, "retrying": False, "locale": "es_CO"})
            try:
                uid = str(c1.get("data", {}).get("uid", ""))
            except Exception:
                uid = ""
        if uid:
            api({"do": "mmm", "begin": False, "serching": False,
                 "add": "[%s,\"\",100,0]" % uid, "tag": 1,
                 "abandon": False, "mode": -1, "stop": False})
    except Exception as e:
        print("[1b] lobby setup fallo (%s) - continuo" % e)
        ct_token = ""

    # 2) SALA: si esta vacia/"AUTO" -> flujo por MODO (el server asigna la
    # sala segun el gamemode elegido: FFA->sala FFA, CTF->sala CTF...).
    # Si hay un nombre escrito -> joinroom por nombre (sala especifica).
    # (room_val/modo_auto ya se calcularon antes del lobby setup)
    invite = None
    if modo_auto:
        print("[2] sala AUTO: el server asigna la sala segun el modo (%d)" % getattr(args, "mode", 5))
        # connect i=2 SIN invite: el EXACTO del flujo que SPAWNEA en modo
        # AUTO hoy (validado en vivo: [20] llega a los ~2.6s del READY).
        # El i=1 da el server del modo pero el server no manda el [20].
        rc = api({"do": "connect", "invite": False, "defered": True,
                  "i": 2, "gm": -1, "retrying": False, "locale": "es_CO"})
        print("[2] connect raw: %s" % json.dumps(rc)[:400])
        token = rc.get("data", {}).get("token", "") if isinstance(rc.get("data"), dict) else ""
        if not token:
            print("[2] connect (modo) FALLO: %s" % json.dumps(rc)[:300])
            return 0
        srv = rc.get("data", {}).get("server", "") if isinstance(rc.get("data"), dict) else ""
        print("[2] server del modo: %s (m=%s) token=%r" % (srv, rc.get("data", {}).get("m", "?"), token))
        inv_host = srv
    else:
        # joinroom: por CODIGO privado (--code) o por nombre (--room)
        if getattr(args, "code", ""):
            room_code = args.code.strip()
            print("[2] joinroom por CODIGO privado: %r" % room_code)
        else:
            room_code = find_room(api, room_val) or room_val
            print("[2] joinroom: %r" % room_code)
        rj = api({"do": "joinroom", "code": room_code})
        invite = rj.get("data", {}).get("invite_string", "") if isinstance(rj.get("data"), dict) else ""
        if not invite:
            print("[3] joinroom FALLO: %s" % json.dumps(rj)[:300])
            return 0
        print("[3] invite: %s" % invite[:60])
        # mmm tag=2 tras joinroom (binario tcp_farm.cpp:2445)
        if uid:
            try:
                api({"do": "mmm", "begin": False, "serching": False,
                     "add": "[%s,\"\",100,0]" % uid, "tag": 2,
                     "abandon": False, "mode": -1, "stop": False})
            except Exception:
                pass
        # 4) connect con invite -> server+token. El binario (tcp_farm.cpp:2628-2636)
        # conecta el TCP al HOST DEL INVITE (inviteString.section('|',0,0));
        # el server del connect solo da el token.
        rc = api({"do": "connect", "invite": invite, "defered": True,
                  "i": 2, "gm": -1, "retrying": False, "locale": "es_CO"})
        token = rc.get("data", {}).get("token", "") if isinstance(rc.get("data"), dict) else ""
        print("[4] connect(invite) token=%r" % token)
        if not token:
            print("[4] connect FALLO: %s" % json.dumps(rc)[:300])
            return 0
        inv_host = invite.split("|")[0]
        # mmm tag=2 despues del connect con invite (tcp_farm.cpp:2443-2449)
        try:
            api({"do": "mmm", "begin": False, "serching": False,
                 "add": "[%s,\"\",100,0]" % uid, "tag": 2,
                 "abandon": False, "mode": -1, "stop": False})
        except Exception:
            pass
    host = inv_host.split(":")[0]
    port = int(inv_host.split(":")[1]) if ":" in inv_host else 443
    print("[4] server TCP: %s:%d" % (host, port))

    # 5) POST-CONNECT HTTP: SOLO en el flujo con sala (astro tcp_farm.cpp:
    # 2937-2944). En el AUTO el gamemode del post-connect REASIGNA el server
    # del connect y el server corta (validado: el test que llego al
    # PLAYER_ID — _tmp_auth_i2.py — no lo tenia). El play del canal
    # economia va DESPUES del [4]/[52] (timing del binario: do:play justo
    # antes del op10035).
    if invite:
        try:
            api({"do": "inventory", "ingame": True, "slot": 3})
            api({"do": "news"})
            api({"do": "play", "usertoken": None})
            api({"do": "gamemode", "index": 1, "mode": getattr(args, "mode", 3)})
            print("[5a] post-connect HTTP (inventory+news+play+gamemode) OK")
        except Exception as e:
            print("[5a] post-connect HTTP fallo (%s) - continuo" % e)
    if not modo_auto:
        try:
            api({"do": "news"})
            print("[4b] pre-TCP HTTP (news) OK")
        except Exception as e:
            print("[4b] news fallo (%s)" % e)

    sock = socket.create_connection((host, port), timeout=10)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print("[5] TCP conectado")
    # UDP init: SOLO en el flujo con sala (el flujo AUTO validado en vivo
    # no lo manda: 2 corridas con [20] + el usuario jugando).
    if not modo_auto:
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            udp_prefix = TF.make_udp_prefix()
            udp_sock.sendto(TF.make_udp_init_packet(udp_prefix), (host, 3724))
            print("[5b] UDP init enviado a %s:3724 prefix=%s" % (host, udp_prefix.hex()[:16]))
        except Exception as e:
            udp_sock = None
            print("[5b] UDP init fallo (%s)" % e)
    else:
        udp_sock = None
    # greeting -> suffix. El binario (tcp_farm.cpp:1486-1497) valida que los
    # PRIMEROS 8 chars del string sean digitos y toma los ULTIMOS 8 como
    # suffix (el suffix NO es numerico; ej captura: 'NoFj;jVs').
    suffix = None
    deadline = time.time() + 10
    while time.time() < deadline:
        length, flag, payload = TF.recv_frame(sock, 5)
        if length is None:
            break
        if flag == 1:
            continue
        try:
            dec = TF.bytearray_desturple(payload, 0)
            d = TF.Amf3Decoder(dec)
            v = d.read_value()
            if isinstance(v, str) and len(v) >= 8:
                head8 = v[:8]
                if head8.isdigit() and int(head8) != 0:
                    suffix = v[-8:]
                    print("[5b] GREETING COMPLETO=%r" % v)
                    print("[5b] SUFFIX=%r (head=%r)" % (suffix, head8))
                    break
                print("  [greet] head no-digito: %r" % head8)
        except Exception:
            pass
    if not suffix:
        print("[5] ERROR: sin greeting valido (head 8 digitos)")
        return 0

    # AUTH M2XC: frame TCP (formato exacto del C++)
    if invite:
        auth = make_auth_frame_invite(host, suffix, token, invite)
        print("[6] AUTH invite frame hex=%s" % auth.hex()[:100])
        TF.send_frame(sock, auth, log_it=False, label="AUTH")
        print("[6] AUTH enviado (invite)")
    else:
        # sala AUTO por modo: AUTH EXACTO del flujo validado en vivo
        # (2 corridas con [20] + el usuario jugando): AUTH TCP m2xc SIN
        # AUTH HTTP (el POST previo consume/rompe la sesion del token).
        auth_frame, auth_body = make_auth_frame_auto(host, suffix, token,
                                                     getattr(args, "mode", 3))
        TF.send_frame(sock, auth_frame, log_it=False, label="AUTH")
        print("[6] AUTH auto frame hex=%s" % auth_frame.hex()[:100])
        print("[6] AUTH TCP enviado (m2xc, modo=%d, sin invite)"
              % getattr(args, "mode", 3))

    # IRC: DESACTIVADO en el flujo AUTO (el handshake secuencial bloquea
    # 2-16s y el server del juego corta la sesion mientras nadie lee el
    # socket — el flujo que SPAWNEÓ no usaba IRC). El keepalive responde
    # PINGs del IRC solo si irc_sock no es None.
    irc_sock = None

    # LISTENER: DESACTIVADO en el flujo AUTO (el POST HTTP entre el AUTH y
    # la lectura de frames hace que el server del juego corte la sesion —
    # el flujo que daba UNDEC con el AUTH m2xc no lo usaba).
    # mmm tag=1 tras el listener (astro spawnSession 1796-1802, si uid)
    if uid:
        try:
            api({"do": "mmm", "begin": False, "serching": False,
                 "add": "[%s,\"\",100,0]" % uid, "tag": 1,
                 "abandon": False, "mode": -1, "stop": False})
        except Exception:
            pass

    # post-auth: esperar player_id / auth_token
    state = TF.GameState()
    state.host, state.port, state.sock, state.suffix = host, port, sock, suffix
    # MT setup: seed inicial 0; el MT consume next_val() #1 en el PRIMER ping
    # (el binario: enc_seed=85502 desde el ping 1 a los 44ms, y el PONG lleva
    # seed%100=2 -> 85502%100=2; 85502 es el valor #1 del MT, consumido EN el
    # ping 1, igual que hace este script con (ping_count-1)%10==0).
    state.str_key = TF.get_str_key(suffix)
    state.mt = TF.MersenneTwister(state.str_key)
    state.encoding_seed = 0
    client = TF.GameClient(state)

    # post-auth: procesar frames del handshake hasta SPAWNED [20].
    # DOS FLUJOS (2026-08-13, validado en vivo):
    # - CON SALA (joinroom): AUTH m2xc + [52] challenge -> PROOF -> [53/40] ->
    #   inventory+READY -> [20]. Seed avanza cada 10 PINGs.
    # - MODO AUTO (sin sala, tcp_farm makeAuthFrame sin invite): AUTH AES +
    #   player_id -> READY INMEDIATO (resturple) + CLEAR_10034 -> httpPlay ->
    #   [20]. El [52] es AUTH_TOKEN informativo. Seed avanza en CADA ping.
    auth_deadline = time.time() + 45
    got_id = False
    challenge_done = False
    ready_sent = False
    spawned = False
    seed = 0
    ping_count = 0
    auto_ping_count = 0
    proof_sent_at = 0
    nonce_local = ""
    undec_count = 0
    if modo_auto:
        # MODO AUTO (binario capture_ctf.log): el MT NO se consume antes del
        # AUTH. El PRIMER ping (traiga 0 o 1) consume el PRIMER valor del MT
        # (39570/82215 en las capturas) y el PONG ya va con ese. Despues solo
        # avanzan los pings con tercer campo=1 (cada ~10 pings: 20331, 22227).
        # tcp_full consumia server_seed ANTES y avanzaba en CADA ping -> el
        # PONG del primer ping iba con el SEGUNDO valor -> server corta.
        server_seed = 0
        encoding_seed = 0
    else:
        server_seed = 0
        encoding_seed = 0

    def decode_auto(payload):
        # decodeFrame del C++ (tcp_farm.cpp:1041): intento 1 m2xcTcp, intento
        # 2 desturple, con los 3 seeds. CRITICO para el AUTO: el server
        # responde los frames post-AUTH cifrados con el STREAM CIPHER m2xc
        # (solo desturple daba UNDEC -> 0 frames visibles; con el m2xc path
        # el [4] PLAYER_ID decodifica — validado en vivo _tmp_auth_i4.py).
        for s in (0, server_seed, encoding_seed):
            v, method = decode_tcp_frame(payload, s)
            if v is not None:
                return v, method
        return None, None

    def do_ready():
        # inventory ingame + espera 1500ms (respondiendo PONGs) + READY.
        nonlocal ready_sent
        ready_sent = True
        try:
            api({"do": "inventory", "ingame": True, "slot": 3})
        except Exception:
            pass
        # el C++ espera 1500ms entre el inventory y el READY (tcp_farm.cpp:2900)
        end_w = time.time() + 1.5
        while time.time() < end_w:
            try:
                wlen, wflag, wpayload = TF.recv_frame(sock, 0.05)
            except Exception:
                wlen = None
            if wlen is not None:
                wv = None
                if wflag == 1 and wpayload and wpayload[0] <= 0x09:
                    try:
                        d = TF.Amf3Decoder(wpayload)
                        wv = d.read_value()
                    except Exception:
                        pass
                else:
                    try:
                        wv, _wm = decode_tcp_frame(wpayload, seed)
                    except Exception:
                        pass
                if isinstance(wv, list) and wv and isinstance(wv[0], (int, float)) and int(wv[0]) == 1:
                    try:
                        pong = make_pong_frame_cpp(seed, wv[1] if len(wv) >= 2 else 0)
                        TF.send_frame(sock, pong, log_it=False, label="PONG")
                    except Exception:
                        pass
            time.sleep(0.005)
        TF.send_frame(sock, make_ready_frame_cpp(seed), log_it=False, label="READY")
        print("[6e] READY enviado")

    def do_ready_auto():
        # MODO AUTO: READY EXACTO del flujo que SPAWNEA (validado 2026-08-13,
        # 2 corridas seguidas con [20]): [53/40] -> inventory(ingame,slot=3)
        # HTTP -> espera 1500ms procesando frames (PONGs, seed cada 10) ->
        # READY [10000,[true,1920,1080,1,true]]. SIN CLEAR_10034.
        nonlocal ready_sent, encoding_seed, auto_ping_count
        ready_sent = True
        try:
            api({"do": "inventory", "ingame": True, "slot": 3})
        except Exception:
            pass
        end_w = time.time() + 1.5
        while time.time() < end_w:
            try:
                wlen, wflag, wpayload = TF.recv_frame(sock, 0.05)
            except Exception:
                wlen = None
            if wlen is not None:
                wv = None
                if wflag == 1 and wpayload and wpayload[0] <= 0x09:
                    try:
                        d = TF.Amf3Decoder(wpayload)
                        wv = d.read_value()
                    except Exception:
                        pass
                else:
                    try:
                        wv, _wm = decode_auto(wpayload)
                    except Exception:
                        pass
                if isinstance(wv, list) and wv and isinstance(wv[0], (int, float)) and int(wv[0]) == 1:
                    auto_ping_count += 1
                    if (auto_ping_count - 1) % 10 == 0:
                        encoding_seed = state.mt.next_val() % 99999
                    try:
                        pong = make_pong_frame_cpp(encoding_seed, wv[1] if len(wv) >= 2 else 0)
                        TF.send_frame(sock, pong, log_it=False, label="PONG")
                    except Exception:
                        pass
            time.sleep(0.005)
        TF.send_frame(sock, make_ready_frame_cpp(encoding_seed),
                      log_it=False, label="READY")
        print("[6e] READY (astro: inventory+1500ms+READY) enviado")
        # gamemode HTTP NO va aqui: el binario lo manda a 162810ms, DESPUES
        # del NATIVE_PLAY (postSpawn). Antes del [20] rompe la sesion.

    def do_proof_auto(challenge):
        # [52] secure nonce -> PROOF [10035] resturple. EXACTO de astro
        # (tcp_farm.cpp:1899-1927): challenge_roundtrip HTTP (POST del
        # challenge al engine -> 8 chars) y si el roundtrip no da 8 chars,
        # decrypt LOCAL con el suffix. El PROOF va con el seed ACTUAL.
        nonlocal proof_sent_at, nonce_local, encoding_seed
        nonce = ""
        # El PROOF va con el seed ACTUAL del MT: el binario manda el [10035]
        # con seed=82215 = el primer valor (consumido por el ping [1,ts,1]
        # que llega ANTES del [52] en el mismo paquete). Si el primer ping
        # aun no avanzo encoding_seed, consumir el primer valor AHORA.
        if encoding_seed == 0:
            encoding_seed = state.mt.next_val() % 99999
            print("[6c] PROOF: seed avanza al primer valor del MT (%d)" % encoding_seed)
        # roundtrip HTTP del challenge (astro lo hace SIEMPRE; el engine
        # responde en <200ms desde su red). Timeout corto: si el engine no
        # responde rapido, fallback a decrypt local (63ms como el binario).
        try:
            import time as _t
            rt = api_raw_post(challenge)
            t = str(rt).strip()
            if len(t) == 8:
                nonce = t
                print("[6c] challenge roundtrip HTTP OK: %r" % nonce)
        except Exception as e:
            print("[6c] roundtrip fallo: %s" % e)
        if not nonce:
            try:
                dec = decrypt_challenge(challenge, suffix)
                if dec:
                    nonce = dec
                    print("[6c] decryptChallenge local OK: %r" % nonce[:12])
            except Exception as e:
                print("[6c] decryptChallenge fallo: %s" % e)
        if nonce:
            nonce_local = nonce
            try:
                # make_proof_frame = m2xcTcp (tcp_frame_from_logical), el MISMO
                # cifrado que astro usa para TODO post-auth. El make_client_frame
                # (resturple) anterior hacia que el server ignorara el [10035]
                # y nunca respondiera el [53].
                pfrm, proof = make_proof_frame(challenge, suffix, args.device,
                                              encoding_seed, args.pem, nonce)
                TF.send_frame(sock, pfrm, log_it=False, label="PROOF")
                print("[6d] PROOF (10035, m2xcTcp) enviado (%s...)" % proof[:12])
                proof_sent_at = time.time()
            except Exception as e:
                print("[6d] PROOF error: %s" % e)

    while time.time() < auth_deadline and not spawned:
        length, flag, payload = TF.recv_frame(sock, 3)
        if length is None:
            break
        v = None
        method = ""
        if flag == 1 and payload and payload[0] <= 0x09:
            # handshake plano (AMF3 sin codificar) - tcp_farm.cpp:1653
            try:
                d = TF.Amf3Decoder(payload)
                v = d.read_value()
                method = "flat"
            except Exception:
                pass
        else:
            if modo_auto:
                v, method = decode_auto(payload)
            else:
                v, method = decode_tcp_frame(payload, seed)
        if v is None:
            if args.verbose and undec_count < 3:
                print("  [post-auth] UNDEC len=%d flag=%d hex=%s" % (length, flag, payload[:24].hex()))
            undec_count += 1
            continue
        if not (isinstance(v, list) and v and isinstance(v[0], (int, float))):
            if args.verbose:
                print("  [post-auth] non-op: %r" % (repr(v)[:60]))
            continue
        op = int(v[0])
        if args.verbose:
            print("  [post-auth] op=%d method=%s %r" % (op, method, repr(v)[:80]))
        if op == 1:  # PING
            if modo_auto:
                # MODO AUTO (astro tcp_farm.cpp:1878-1893): el MT avanza
                # CADA 10 PINGs (#1, #11, #21...), igual que con sala.
                # PONG [10001.0, ts, seed%100] con el ts del PING.
                auto_ping_count += 1
                if (auto_ping_count - 1) % 10 == 0:
                    encoding_seed = state.mt.next_val() % 99999
                ts = v[1] if len(v) >= 2 else 0
                pong = make_pong_frame_cpp(encoding_seed, ts)
            else:
                # CON SALA: el MT avanza SOLO cada 10 PINGs (#1, #11...) - tcp_farm.cpp:1692-1696
                ping_count += 1
                if (ping_count - 1) % 10 == 0:
                    seed = state.mt.next_val() % 99999
                ts = v[1] if len(v) >= 2 else 0
                pong = make_pong_frame_cpp(seed, ts)
            TF.send_frame(sock, pong, log_it=False, label="PONG")
        elif op == 4 and len(v) >= 2:
            state.player_id = int(v[1]) if isinstance(v[1], (int, float)) else -1
            got_id = True
            print("[6b] PLAYER_ID=%d" % state.player_id)
            # MODO AUTO: NO READY inmediato. El binario: [4] -> [52] -> PROOF
            # (63ms) -> [53] -> inventory+READY (161818ms) -> [40] -> [20].
            # (El intento "READY inmediato + ignorar [52]" spawneo pero el
            # server cortaba a los ~0.5s del [20].)
        elif op == 52 and len(v) >= 2 and isinstance(v[1], str) and not challenge_done:
            challenge_done = True
            if modo_auto:
                # [52] secure nonce -> PROOF [10035] INMEDIATO (decrypt local
                # + firma, ~63ms como el binario). El roundtrip HTTP NO va
                # (tarda ~300ms y el server corta antes del [53]).
                do_proof_auto(v[1])
                continue
            else:
                print("[6c] DESAFIO recibido, roundtrip HTTP...")
                # challenge_roundtrip HTTP: POST del challenge al engine -> 8 chars
                nonce = ""
                try:
                    rt = api_raw_post(v[1])
                    t = str(rt).strip()
                    if len(t) == 8:
                        nonce = t
                        print("[6c] roundtrip OK: %r" % nonce)
                    else:
                        print("[6c] roundtrip raro: %r" % str(rt)[:60])
                except Exception as e:
                    print("[6c] roundtrip fallo: %s" % e)
                if not nonce:
                    # fallback: descifrar el challenge localmente con el suffix
                    try:
                        dec = decrypt_challenge(v[1], suffix)
                        if dec:
                            nonce = dec
                            print("[6c] decryptChallenge local OK: %r" % nonce)
                    except Exception as e:
                        print("[6c] decryptChallenge fallo: %s" % e)
                if nonce:
                    try:
                        pfrm, proof = make_proof_frame(v[1], suffix, args.device, seed, args.pem, nonce)
                        TF.send_frame(sock, pfrm, log_it=False, label="PROOF")
                        print("[6d] PROOF enviado (%s...)" % proof[:12])
                        proof_sent_at = time.time()
                    except Exception as e:
                        print("[6d] PROOF error: %s" % e)
        elif op in (53, 40) and not ready_sent:
            if modo_auto:
                # [53] (binario 161519ms) -> inventory+READY a 161818ms
                do_ready_auto()
            else:
                do_ready()
        elif op == 20:
            spawned = True
            # [20, [x, y, z], ts] - guardar la posicion del spawn
            try:
                if len(v) >= 2 and isinstance(v[1], list) and len(v[1]) >= 3:
                    state.position = tuple(v[1][:3])
            except Exception:
                pass
            print("[6f] SPAWNED [20] - EN SALA pos=%s" % repr(state.position)[:30])
    if not got_id:
        print("[6] aviso: no player_id antes del deadline (continua igual)")

    # NOTA (validado v41/v46): el [20] SPAWNED puede NO llegar (sala kjajajaja
    # no lo manda: el jugador se detecta por correlacion con el MOVE). La
    # sesion sigue viva igual: el postSpawn + keepalive la mantienen (7624
    # CLEAR / 3741 DUMP / 243 SPLIT en v41 SIN [20]). NO retornar aqui.

    # READY ya se envio en el post-auth (op 53/40). Nada mas antes del spawn.

    # ================= POST-SPAWN SEQUENCE =====
    # Secuencia COMPLETA del C++ con gema (tcp_farm.cpp:1824-1878): inventory
    # slot=5 -> news -> play HTTP + NATIVE_PLAY[true/false] -> gamemode.
    # EVIDENCIA: en el run CON inventory/news DeRene respawneo OK (RESPAWNED #1
    # a los 197s); al quitarlos NINGUNA cuenta volvio a respawnear (el server
    # deja de respawnear si el respawn no se confirma con la secuencia completa).
    # Se usa TANTO en el spawn inicial como en el respawn tras muerte (op 20).
    # NOTA: los sleeps internos usan drain() (lee frames + responde PONGs) en
    # vez de time.sleep() puro — si varias cuentas mueren a la vez, el postSpawn
    # de cada una NO debe dejar de procesar los PINGs del server (como
    # processEvents del C++): sin PONGs el server corta el socket.
    # contador COMPARTIDO con el keepalive (nonlocal)
    # HEREDA el ping_count del post-auth: el MT ya avanzo durante el handshake
    # (ping_count pings procesados alla). Si seed_ping_count arrancara en 0,
    # el drain/keepalive RE-CONSUMIRIAN los mismos valores del MT -> seed
    # desincronizado -> los frames del server no decodifican (pings=0 frames=0)
    # -> sin PONGs -> el server corta la sesion (0.0s o timeout ~23s).
    seed_ping_count = ping_count
    # estado del respawn COMPARTIDO con el drain del postSpawn
    _deaths = 0
    _respawn_pending = False
    _respawn_wait_start = None
    _dead_waiting = False  # autorespawn OFF: murio y espera el Enter de la UI
    _spawned_at = time.time()

    def post_spawn(as_respawn=False):
        # SECUENCIA COMPLETA con HTTP en SPAWN y RESPAWN (config del run
        # proc_0112d0c8e24e, el MEJOR: 8 cuentas vivas 210s+ con RESPAWNED):
        # inventory slot=5 -> news -> play HTTP + NATIVE_PLAY x2 -> gamemode.
        # EVIDENCIA: con el spawn RAPIDO sin HTTP TODAS las cuentas eran
        # cortadas a los ~1.9s (incluso las antes estables); con HTTP completo
        # en el spawn las cuentas sobreviven la ventana inicial (DeRene/Deity/
        # Anisa 120-140s+). El usuario lo confirmo: "creo q si necesitas http".
        nonlocal seed, seed_ping_count, _deaths, _respawn_pending, _respawn_wait_start
        if modo_auto:
            nonlocal encoding_seed

        def drain(seconds):
            # Lee frames del socket durante `seconds` respondiendo PONG a los
            # PINGs, avanzando el seed (cada 10) y PROCESANDO muerte/respawn
            # (op 11 / 25 / 20) en vez de robar los frames — replica el
            # processEvents del C++ (tcp_farm.cpp:3060+). Devuelve True si el
            # socket se cerro (EOF).
            nonlocal seed, seed_ping_count, _deaths, _respawn_pending, _respawn_wait_start, _dead_waiting
            if modo_auto:
                nonlocal encoding_seed, auto_ping_count
            end = time.time() + seconds
            while time.time() < end:
                try:
                    import select as _sel
                    rlist, _, _ = _sel.select([sock], [], [], 0.1)
                    if not rlist:
                        continue
                    _len, _fl, _pl = TF.recv_frame(sock, 0.2)
                    if _len is None and _pl == b"":
                        return True  # EOF
                    if _len is None:
                        continue
                    _v = None
                    if _fl == 1 and _pl and _pl[0] <= 0x09:
                        try:
                            _d = TF.Amf3Decoder(_pl)
                            _v = _d.read_value()
                        except Exception:
                            pass
                    else:
                        try:
                            if modo_auto:
                                _v, _m = decode_auto(_pl)
                            else:
                                _v, _m = decode_tcp_frame(_pl, seed)
                        except Exception:
                            pass
                    if not (isinstance(_v, list) and _v and isinstance(_v[0], (int, float))):
                        continue
                    _op = int(_v[0])
                    if _op == 1:  # PING
                        if modo_auto:
                            # MODO AUTO (astro): MT avanza CADA 10 PINGs.
                            # PONG [10001, ts, seed%100] resturple.
                            auto_ping_count += 1
                            if (auto_ping_count - 1) % 10 == 0:
                                encoding_seed = state.mt.next_val() % 99999
                            try:
                                TF.send_frame(sock, make_pong_frame_cpp(encoding_seed, _v[1] if len(_v) >= 2 else 0),
                                              log_it=False, label="PONG")
                            except Exception:
                                pass
                        else:
                            seed_ping_count += 1
                            if (seed_ping_count - 1) % 10 == 0:
                                seed = state.mt.next_val() % 99999
                            try:
                                TF.send_frame(sock, make_pong_frame_cpp(seed, _v[1] if len(_v) >= 2 else 0),
                                              log_it=False, label="PONG")
                            except Exception:
                                pass
                    elif _op == 11:
                        # op 11 = BROADCAST de muerte de OTRO jugador (igual que
                        # en el keepalive): el binario NUNCA recibe op 11 propio
                        # (el server reporta la muerte propia con [25]+[20]
                        # directo). Las 9 cuentas spawnean juntas y se matan en
                        # cadena -> TODAS reciben el op 11 de cada muerte. NO
                        # marcar respawn_pending (causaba reintentos falsos).
                        if not getattr(args, "quiet", False):
                            print("  [evt] op 11 broadcast DURANTE postSpawn")
                    elif _op == 16:
                        # wrapper de eventos: [16, [25, []], ts] = respawn-ready.
                        # SOLO informativo: el [20] que sigue (1ms despues en el
                        # binario) es el que confirma. NO marcar pending: un
                        # [25] puede llegar sin su [20] (broadcast de otra
                        # cuenta) y dejaria el pending pegado -> reintentos
                        # infinitos (visto en el run v6).
                        _nested = None
                        if len(_v) >= 2 and isinstance(_v[1], list) and _v[1] and isinstance(_v[1][0], (int, float)):
                            _nested = int(_v[1][0])
                        if _nested == 25 and not getattr(args, "quiet", False):
                            print("  [evt] respawn-ready (16->[25]) DURANTE postSpawn")
                    elif _op == 25:
                        # [25] = respawn-ready. SOLO informativo (ver op 16).
                        if not getattr(args, "quiet", False):
                            print("  [evt] respawn-ready (op 25) DURANTE postSpawn")
                        _dead_waiting = True
                    elif _op == 20:
                        # [20] con posicion = SPAWN o RESPAWN de ESTA conexion
                        # (el frame llega por mi socket -> es para mi). En el
                        # drain del postSpawn (que corre DESPUES del [20]
                        # inicial del post-auth) todo [20] es un respawn ->
                        # confirmar SIEMPRE con la secuencia completa (el
                        # binario confirma en el handler del [20]). Con
                        # autorespawn OFF el respawn espera el Enter de la UI.
                        _deaths += 1
                        _respawn_pending = False
                        _respawn_wait_start = None
                        if not getattr(args, "autorespawn", True):
                            _dead_waiting = True
                            if not getattr(args, "quiet", False):
                                print("  [RS] autorespawn OFF: [20] DURANTE postSpawn - esperando Enter")
                            continue
                        _dead_waiting = False
                        if not getattr(args, "quiet", False):
                            print("  [RS] RESPAWNED (op 20) DURANTE postSpawn - confirmando secuencia")
                        try:
                            post_spawn(as_respawn=True)
                        except Exception:
                            pass
                except (ConnectionResetError, OSError, ValueError):
                    return True
            return False

        tag = "respawn" if as_respawn else "spawn"
        if modo_auto:
            # MODO AUTO: EXACTO de astro postSpawnSequence (tcp_farm.cpp:
            # 2184-2206): NATIVE_PLAY [5,[challenge,true]] INMEDIATO (usa
            # randomNonce(), NO el token del play) + drain 165ms +
            # NATIVE_PLAY [5,[challenge,false]] + drain 287ms + play HTTP
            # x2 + gamemode HTTP. El frame TCP es lo que confirma el spawn;
            # los HTTPs van best-effort DESPUES (si el play falla, el frame
            # ya confirmo).
            nonlocal nonce_local
            try:
                TF.send_frame(sock, make_native_play_frame_cpp(
                    encoding_seed, random_nonce(), suffix, True),
                    log_it=False, label="NATIVE_PLAY[true]")
            except Exception as e:
                print("[7b] NATIVE_PLAY true error: %s" % e)
            if drain(0.165):
                return
            try:
                TF.send_frame(sock, make_native_play_frame_cpp(
                    encoding_seed, random_nonce(), suffix, False),
                    log_it=False, label="NATIVE_PLAY[false]")
            except Exception as e:
                print("[7b] NATIVE_PLAY false error: %s" % e)
            if drain(0.287):
                return
            try:
                api({"do": "play", "usertoken": None})
            except Exception as e:
                print("[7b] play confirm fallo: %s" % e)
            try:
                api({"do": "play", "usertoken": None})
            except Exception as e:
                print("[7b] play confirm 2 fallo: %s" % e)
            try:
                api({"do": "gamemode", "index": 1,
                     "mode": getattr(args, "mode", 3)})
                print("[7b] gamemode HTTP OK")
            except Exception as e:
                print("[7b] gamemode error: %s" % e)
            if drain(0.3):
                return
            try:
                TF.send_frame(sock, make_entity_info_frame_cpp(encoding_seed),
                              log_it=False, label="ENTITIES_INFO")
                print("[7b] CLIENT_ENTITIES_INFO (10002, m2xcTcp) enviado")
            except Exception as e:
                print("[7b] ENTITIES_INFO error: %s" % e)
            return
        # RESPAWN: la captura del binario muestra play HTTP x2 puro, PERO el
        # binario es el juego real del usuario (ya en partida, con su sesion
        # HTTP y TPM real). Las cuentas fake-TPM del script necesitan la
        # SECUENCIA COMPLETA HTTP tambien en el respawn (memory: "confirmar
        # secuencia COMPLETA inventory->news->play->NATIVE_PLAY x2->gamemode
        # (user: 'si necesitas http'); TCP puro corta ~1.9s"). El run bueno
        # proc_0112d0c8e24e (8 cuentas vivas 210s+ con RESPAWNED) usaba la
        # secuencia completa en SPAWN y RESPAWN; al quitarla del respawn, las
        # cuentas morian y el server nunca les mandaba el [25]+[20] (quedaban
        # espectadoras: power~80 constante y reintentos sin [20]).
        try:
            api({"do": "inventory", "slot": 5})
        except Exception:
            pass
        if drain(0.57):
            return
        try:
            api({"do": "news"})
        except Exception:
            pass
        if drain(1.59):
            return
        try:
            api({"do": "play", "usertoken": None})
        except Exception:
            pass
        TF.send_frame(sock, make_native_play_frame_cpp(seed, random_nonce(), suffix, True),
                      log_it=False, label="NATIVE_PLAY[true] %s" % tag)
        if drain(0.165):
            return
        try:
            api({"do": "play", "usertoken": None})
        except Exception:
            pass
        TF.send_frame(sock, make_native_play_frame_cpp(seed, random_nonce(), suffix, False),
                      log_it=False, label="NATIVE_PLAY[false] %s (2do play HTTP)" % tag)
        if drain(0.287):
            return
        try:
            # mode=5 = FFA/partida real (el binario capturado en la sala
            # privada ahjkjakjaka usa gamemode(index=1, mode=5) a los 3954ms
            # del spawn). Con mode=3 el server deja la cuenta como ESPECTADOR
            # (power~80 constante, sin [25]+[20] de respawn al morir: nunca
            # respawnea). El modo elegido en el lobby del visor se confirma
            # aqui (FFA=5, CTF=4...).
            api({"do": "gamemode", "index": 1, "mode": getattr(args, "mode", 5)})
        except Exception:
            pass
        # CRITICO (validado 2026-08-13, subagente deleg_9c6a7655): el server
        # SOLO envia el dump del mundo (6651 bytes, ~350 entidades) cuando el
        # cliente pide entidades explicitamente con CLIENT_ENTITIES_INFO (10002)
        # [10002, [0]]. Sin esto el visor recibe solo frames '64' vacios y la X
        # del jugador (0xc8). Reenviar periodicamente en el keepalive mantiene
        # las entidades frescas (mitosis_client.py legacy lo re-enviaba cada 30s).
        try:
            TF.send_frame(sock, make_entity_info_frame_cpp(seed),
                          log_it=False, label="ENTITIES_INFO")
            print("[7b] CLIENT_ENTITIES_INFO (10002) enviado")
        except Exception as e:
            print("[7b] ENTITIES_INFO error: %s" % e)
        return

    post_spawn(as_respawn=False)
    print("[7] postSpawnSequence OK (inventory/news/play+NATIVE_PLAY+gamemode)")

    # ================= KEEPALIVE + TIMER =================
    spawned_at = time.time()
    last_pos = None
    death_t = None
    next_log = time.time() + 10
    end_t = time.time() + getattr(args, "duration", 90)
    # mmm periodico cada ~10.6s con tag++ (como el binario: tcp_farm.cpp:3064-3074).
    # El primer mmm sale a ~1s del keepalive (el binario lo manda a los 1463ms
    # del [20]; el postSpawn del script ya consumio ~2.6s, asi que +1s queda en
    # el mismo rango). tag=2: el tag=1 ya fue en el lobby HTTP.
    next_mmm = time.time() + 1000 / 1000.0
    mmm_tag = 2
    next_entities = time.time() + 30.0  # CLIENT_ENTITIES_INFO periodico (~30s)
    ping_count = 0
    # seed_ping_count / _deaths / _respawn_pending / _respawn_wait_start NO se
    # redeclaran aqui: comparten el binding con post_spawn (nonlocal, declarados
    # antes del closure) para que el drain del postSpawn y el keepalive usen el
    # MISMO estado.
    deaths = _deaths
    respawn_pending = _respawn_pending
    respawn_wait_start = _respawn_wait_start
    dead_waiting = _dead_waiting
    _spawned_at = spawned_at

    print("[8] sesion viva... (max %ds)" % getattr(args, "duration", 90))
    while time.time() < end_t:
        now = time.time()

        # recibir frames: select ANTES de leer (timeout != EOF). recv_frame
        # devuelve (None,None,b'') tanto en timeout como en EOF real; select
        # distingue sin consumir bytes.
        sock_eof = False
        length = flag = payload = None
        try:
            import select as _sel
            rlist, _, _ = _sel.select([sock], [], [], 0.1)
            if rlist:
                length, flag, payload = TF.recv_frame(sock, 0.2)
                if length is None and payload == b"":
                    sock_eof = True
        except (ConnectionResetError, OSError, ValueError):
            sock_eof = True
        except Exception:
            pass
        # IRC PING -> PONG (tcp_farm.cpp:2761-2769)
        if irc_sock is not None:
            try:
                ilen, iflag, ipayload = TF.recv_frame(irc_sock, 0.001)
                if ilen is not None and iflag == 1 and ipayload and ipayload[0] <= 0x09:
                    try:
                        d = TF.Amf3Decoder(ipayload)
                        iv = d.read_value()
                        if isinstance(iv, str) and iv.startswith("PING"):
                            target = iv[5:].strip()
                            irc_sock.sendall(make_irc_frame("PONG :" + target))
                    except Exception:
                        pass
            except Exception:
                pass
        if sock_eof:
            death_t = now
            print("[DEAD] socket cerrado por el server -> %.1fs de vida" % (now - spawned_at))
            break
        if length is not None:
            v = None
            if flag == 1 and payload and payload[0] <= 0x09:
                try:
                    d = TF.Amf3Decoder(payload)
                    v = d.read_value()
                except Exception:
                    pass
            else:
                if modo_auto:
                    v, _m = decode_auto(payload)
                else:
                    v, _m = decode_tcp_frame(payload, seed)
            if isinstance(v, list) and v and isinstance(v[0], (int, float)):
                op = int(v[0])
                state.frame_count += 1
                # DIAGNOSTICO respawn: loguear TODO lo que llega mientras el
                # jugador esta muerto esperando el [20] de respawn
                if respawn_pending and op not in (2, 19) and not getattr(args, "quiet", False):
                    print("  [respawn-wait] llego op=%d %r" % (op, repr(v)[:70]))
                # logging de actividad: muestra opcodes relevantes en vivo
                if op in (2, 3, 16, 19, 20, 24, 33, 35, 40, 51) and not getattr(args, "quiet", False):
                    ts = v[2] if len(v) >= 3 else 0
                    if op == 20:
                        print("  [evt] re-spawn [20] a los %.0fs pos=%s"
                              % (now - spawned_at, repr(v[1])[:40]))
                    elif op == 24:
                        print("  [evt] XP gain [24] a los %.0fs %r" % (now - spawned_at, repr(v)[:60]))
                    elif op == 33:
                        print("  [evt] MATCH END [33] a los %.0fs %r" % (now - spawned_at, repr(v)[:50]))
                    elif op == 35:
                        print("  [evt] chat/notif [35] a los %.0fs" % (now - spawned_at))
                    elif op == 51:
                        print("  [evt] tick server [51]=%r a los %.0fs" % (v[1] if len(v) > 1 else "?", now - spawned_at))
                    elif op == 2 and not getattr(args, "quiet", False):
                        print("  [vivo %.0fs] power=%s" % (now - spawned_at, repr(v[1])[:30]))
                    elif op == 19:
                        print("  [evt] entidades [19] a los %.0fs" % (now - spawned_at))
                if op == 1:  # PING del server: PONG + seed
                    if modo_auto:
                        # MODO AUTO (astro): MT avanza CADA 10 PINGs.
                        # PONG [10001, ts, seed%100] resturple.
                        auto_ping_count += 1
                        if (auto_ping_count - 1) % 10 == 0:
                            encoding_seed = state.mt.next_val() % 99999
                        ts = v[1] if len(v) >= 2 else 0
                        try:
                            pong = make_pong_frame_cpp(encoding_seed, ts)
                            TF.send_frame(sock, pong, log_it=False, label="PONG")
                        except Exception:
                            pass
                    else:
                        seed_ping_count += 1
                        if (seed_ping_count - 1) % 10 == 0:
                            seed = state.mt.next_val() % 99999
                        ts = v[1] if len(v) >= 2 else 0
                        try:
                            pong = make_pong_frame_cpp(seed, ts)
                            TF.send_frame(sock, pong, log_it=False, label="PONG")
                        except Exception:
                            pass
                elif op == 2:
                    # op 2 (power): llega TAMBIEN cuando el jugador esta MUERTO
                    # (power del mundo/espectador ~80). NO limpiar respawn_pending
                    # aqui: el run bueno (proc_0112d0c8e24e, 8 cuentas 210s+ con
                    # RESPAWNED) no tenia este detector. Con el, al morir (op 11)
                    # el op 2 siguiente limpiaba respawn_pending, el [25]/[20]
                    # del respawn llegaba sin confirmacion -> el server sacaba la
                    # cuenta ("se fueron casi todas las q mate").
                    pass
                elif op == 11:
                    # op 11 = BROADCAST de la muerte de OTRO jugador. El binario
                    # (scen_respawn.log, 8 muertes en 90s) NUNCA recibe op 11
                    # propio: el server reporta la muerte propia directo con
                    # [25]+[20] (sin op 11 previo). Por eso TODO op 11 que llega
                    # aqui es de otro jugador (arr vacio incluido) y NO debe
                    # marcar respawn_pending: las cuentas con pending falso
                    # esperaban un [20] que nunca llega (reintentos inutiles cada
                    # 5s con la secuencia completa por cada muerte ajena).
                    if not getattr(args, "quiet", False):
                        print("  [evt] op 11 (broadcast otro jugador) a los %.0fs" % (now - spawned_at))
                elif op == 16:
                    # El op 16->[25] ES el respawn-ready del jugador: las 9 cuentas
                    # spawnean/mueren sincronizadas por eso el timestamp coincide
                    # (NO es broadcast; verificado: con este trigger las cuentas
                    # quedaron vivas 210s+, sin el mueren a los 0.5s).
                    nested = None
                    if len(v) >= 2 and isinstance(v[1], list) and v[1] and isinstance(v[1][0], (int, float)):
                        nested = int(v[1][0])
                    if nested == 25:
                        # [25] = respawn-ready (el server avisa que va a
                        # respawnear). El binario espera el [20] que viene 1ms
                        # despues y confirma EN EL [20] (scen_respawn.log:
                        # [25] a 11203, [20] a 11204, play HTTP a 12250).
                        # El [25] SOLO marca pending y cuenta la muerte (el
                        # op 11 propio NO llega: el server reporta la muerte
                        # con [25]+[20] directo).
                        if not respawn_pending:
                            deaths += 1
                        respawn_pending = True
                        respawn_wait_start = now
                        if not getattr(args, "quiet", False):
                            print("  [RS] respawn-ready #%d (op 16->[25]) a los %.0fs - esperando [20]" % (deaths, now - spawned_at))
                elif op == 25:
                    # [25] = respawn-ready (scen_respawn.log: llega [25]+[20]
                    # juntos, mismo ms). Marcar pending; la confirmacion ocurre
                    # en el [20] que sigue (como el binario, que confirma en el
                    # handler del [20] con la secuencia completa).
                    if not respawn_pending:
                        deaths += 1
                    respawn_pending = True
                    respawn_wait_start = now
                    dead_waiting = True
                    if not getattr(args, "quiet", False):
                        print("  [RS] respawn-ready #%d (op 25) a los %.0fs - esperando [20]" % (deaths, now - spawned_at))
                elif op == 20:
                    # [20, [x, y, z], ts] - actualizar posicion (spawn o respawn)
                    try:
                        if len(v) >= 2 and isinstance(v[1], list) and len(v[1]) >= 3:
                            state.position = tuple(v[1][:3])
                    except Exception:
                        pass
                    # En el KEEPALIVE todo [20] es un re-spawn: el [20] del
                    # spawn inicial llega durante el post-auth (antes de este
                    # loop). El binario confirma la secuencia completa en el
                    # handler del [20] (scen_respawn.log: [25]+[20] juntos y
                    # el play HTTP sale ~1s despues). Sin la confirmacion el
                    # server deja de respawnear al jugador.
                    if not respawn_pending:
                        deaths += 1
                    respawn_pending = False
                    respawn_wait_start = None
                    if not getattr(args, "quiet", False):
                        print("  [RS] RESPAWNED #%d (op 20 pos=%s) a los %.0fs - secuencia completa" % (deaths, repr(state.position)[:25], now - spawned_at))
                    # AUTORESPAWN: si esta OFF (visor), el [20] del respawn se
                    # recibe pero NO se confirma: el jugador queda muerto en el
                    # lobby y el respawn lo dispara la UI (Enter -> spawn_event).
                    # Con autorespawn ON se confirma al instante como el binario.
                    if getattr(args, "autorespawn", True):
                        dead_waiting = False
                        try:
                            post_spawn(as_respawn=True)
                        except Exception as e:
                            if not getattr(args, "quiet", False):
                                print("  [RS] error confirmando respawn: %s" % str(e)[:60])
                    else:
                        dead_waiting = True
                        if not getattr(args, "quiet", False):
                            print("  [RS] autorespawn OFF: [20] recibido, esperando Enter de la UI")
                elif op == 24:
                    # XP gain: la cuenta sigue viva ganando XP
                    if not getattr(args, "quiet", False):
                        print("  [xp] +%s a los %.0fs" % (repr(v[1])[:20], now - spawned_at))
            # (muerte del jugador = op 11, normal; la posicion 0,0 no es fiable
            #  para detectar fin de sesion - solo el DEAD/EOF importa)
        else:
            # sin datos: podria ser cierre del socket
            pass

        # (sin chequeo recv(1): robaba bytes del stream y corrompia los frames)

        # REINTENTO DE RESPAWN: si el jugador murio (respawn_pending) y el [20]
        # de respawn no llego rapido, reenviar la secuencia post_spawn para
        # "despertar" al server. ANTES era 5s (demasiado lento, el server
        # sacaba la cuenta); el usuario queria "respawn rapido, sin
        # reconectar". 1.0s: entre la muerte y el [20] hay ~500-800ms en
        # el binario real. Si no llega a 1.5s, re-disparamos.
        if (getattr(args, "autorespawn", True) and respawn_pending
                and respawn_wait_start is not None and (now - respawn_wait_start) >= 1.0):
            if not getattr(args, "quiet", False):
                print("  [RS] reintento respawn #%d (sin [20] en 1s) - reenviando secuencia" % deaths)
            try:
                post_spawn(as_respawn=True)
            except Exception as e:
                if not getattr(args, "quiet", False):
                    print("  [RS] error reintento respawn: %s" % str(e)[:60])
            respawn_wait_start = now

        # RESPAWN MANUAL (autorespawn OFF): la UI (visor) setea spawn_event
        # con el Enter/Respawn del lobby de muerte -> confirmar el respawn
        # ahora (post_spawn con la secuencia completa). Solo si el jugador
        # esta muerto esperando (dead_waiting): el evento del lobby inicial
        # (spawn manual) NO debe confirmar un respawn inexistente.
        if (not getattr(args, "autorespawn", True) and dead_waiting
                and getattr(args, "spawn_event", None) is not None
                and args.spawn_event.is_set()):
            try:
                args.spawn_event.clear()
                dead_waiting = False
                if not getattr(args, "quiet", False):
                    print("  [RS] respawn MANUAL (Enter de la UI) - confirmando")
                post_spawn(as_respawn=True)
            except Exception as e:
                if not getattr(args, "quiet", False):
                    print("  [RS] error respawn manual: %s" % str(e)[:60])

        # MMM periodico ~10.6s con tag++ (params REALES del binario capturado
        # con frida 2026-08-09, scen_respawn.log): add es el numero FIJO
        # -192895987 (NO el uid), tags 2,3,4...10 durante 90s. El binario lo
        # manda durante TODA la sesion y el server NO lo kickea (8 respawns en
        # 90s con mmm activo). La creencia previa de que "mmm con el mismo
        # sk/magic kickea" venia del C++ y es ERRONEA — el problema era el add
        # con el uid en vez del valor fijo. Sin el mmm el server degrada la
        # cuenta a espectador (power~80) y NO le manda el [25]+[20] de respawn
        # al morir (evidencia: 9 cuentas vivas 300s pero 0 respawns post-spawn;
        # el binario recibe [25]+[20] en las 8 muertes).
        if now >= next_mmm:
            try:
                api({"do": "mmm", "begin": False, "serching": False,
                     "add": "[-192895987,\"\",100,0]", "tag": mmm_tag,
                     "abandon": False, "mode": -1, "stop": False})
                mmm_tag += 1
            except Exception:
                pass
            next_mmm = now + 10.6

        # Reenvio periodico de CLIENT_ENTITIES_INFO (10002) cada ~30s:
        # DESACTIVADO para el OurClient (flag no_resend_entities): el binario
        # real NUNCA reenvia el 10002 en FFA (captura v5f: solo 60x [10001
        # PINGs) y el reenvio corta la sesion a los 60-85s (verificado en
        # vivo 2026-08-16: sesiones con reenvio mueren a 60.6s/85.1s justo
        # despues del 10002; el dump inicial del postSpawn ya basta).
        if now >= next_entities and not getattr(args, "no_resend_entities", False):
            try:
                if modo_auto:
                    TF.send_frame(sock, make_entity_info_frame_cpp(encoding_seed),
                                  log_it=False, label="ENTITIES_INFO")
                else:
                    TF.send_frame(sock, make_entity_info_frame_cpp(seed),
                                  log_it=False, label="ENTITIES_INFO")
            except Exception:
                pass
            next_entities = now + 30.0

        if now >= next_log:
            print("  [vivo %.0fs] spawn_pos=%s pings=%d seed=%d"
                  % (now - spawned_at, last_pos, ping_count, seed))
            next_log = now + 10

        time.sleep(0.005)

    total = time.time() - spawned_at
    print("=" * 64)
    if death_t:
        print("  CONEXION PERDIDA (socket cerrado) a los %.1fs de spawn" % (death_t - spawned_at))
    else:
        print("  Sesion terminada por duration (%.1fs), conexion intacta" % total)
    print("  total vivo: %.1fs | pings=%d frames=%d | muertes=%d respawns_ok=%d" % (
        total, ping_count, state.frame_count, deaths, deaths - (1 if respawn_pending else 0)))
    print("=" * 64)
    try:
        sock.close()
    except Exception:
        pass
    if irc_sock is not None:
        try:
            irc_sock.close()
        except Exception:
            pass
    return total


def account_loop(device, pem, name, args):
    """Loop de reconexion de UNA cuenta (corre en su propio thread)."""
    _tlocal.account = name
    t_start = time.time()
    attempt = 0
    total_vivo = 0.0
    backoff = 4.0  # espera base entre reconexiones (s)
    while True:
        attempt += 1
        if attempt > 1:
            print("\n[rc] %s: sesion %d: reconectando en ~%.0fs (backoff %d)..."
                  % (name, attempt, backoff, int(backoff)))
            time.sleep(backoff)
        print("\n" + "#" * 64)
        print("  SESION %d [%s]  (total vivo acumulado: %.0fs)"
              % (attempt, name, total_vivo))
        print("#" * 64)
        ca = argparse.Namespace(**vars(args))
        ca.device = device
        ca.pem = pem
        total = run_session(ca)
        total_vivo += total
        # BACKOFF ADAPTATIVO: si el server rechazo la sesion casi de inmediato
        # (<2s vivo y el socket cerrado = cupo de la sala lleno), esperar mas la
        # proxima vez (4 -> 8 -> 16 -> 32 -> 60s max). Si la sesion duro >=10s,
        # la cuenta ENTRO bien -> resetear backoff a la base.
        if total < 2.0:
            backoff = min(backoff * 2, 60.0)
            print("[rc] %s: sesion muy corta (%.1fs) -> posible cupo lleno, backoff sube a %.0fs"
                  % (name, total, backoff))
        elif total >= 10.0:
            if backoff != 4.0:
                print("[rc] %s: sesion estable (%.1fs) -> backoff reset a 4s" % (name, total))
            backoff = 4.0
        if args.noreconnect:
            print("[rc] %s: --noreconnect: termino tras la sesion %d" % (name, attempt))
            break
        if time.time() - t_start >= getattr(args, "duration", 90):
            print("[rc] %s: duration total alcanzada (%.0fs)" % (name, time.time() - t_start))
            break


def main():
    ap = argparse.ArgumentParser(description="MitosisOG: spawn en sala por nombre + keepalive")
    ap.add_argument("--device", default=None, help="device id de la cuenta (una sola)")
    ap.add_argument("--pem", default=None, help="ruta al PEM de atestacion de la cuenta (una sola)")
    ap.add_argument("--accounts", type=int, default=0,
                    help="N cuentas de accounts.json de Astro (en hilos, cada una con su PEM fake)")
    ap.add_argument("--exclude", default="",
                    help="nombres de cuenta a EXCLUIR (separados por coma, ej. akardego,Post)")
    ap.add_argument("--room", default="SUDA GEAR COMP", help="nombre exacto de la sala")
    ap.add_argument("--code", default="", help="codigo de sala PRIVADA (joinroom directo por codigo)")
    ap.add_argument("--duration", type=int, default=86400,
                    help="tiempo MAXIMO TOTAL del proceso (s); 0 = ilimitado")
    ap.add_argument("--spawn-wait", type=int, default=90, help="timeout de spawn (s)")
    ap.add_argument("--quiet", action="store_true", help="menos logs")
    ap.add_argument("--verbose", action="store_true", help="loguea cada opcode del handshake")
    ap.add_argument("--noreconnect", action="store_true",
                    help="una sola sesion (sin reconexion al morir)")
    args = ap.parse_args()

    if args.duration == 0:
        args.duration = 10 ** 9  # ilimitado (el keepalive de cada sesion usa su propio tope)

    if args.accounts > 0:
        # multi-cuenta: leer accounts.json de Astro, usar los fake TPMs
        acct_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Astro", "accounts.json")
        tpm_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Astro", "fake_tpm")
        with open(acct_path, encoding="utf-8") as f:
            accts = json.load(f)
        excl = {x.strip().lower() for x in args.exclude.split(",") if x.strip()}
        if excl:
            antes = len(accts)
            accts = [a for a in accts if str(a.get("name") or a.get("user") or "").strip().lower() not in excl]
            print("[multi] excluyendo %d cuentas (%s): %d disponibles" % (antes - len(accts), ",".join(sorted(excl)), len(accts)))
        print("[multi] %d cuentas cargadas de %s" % (len(accts), acct_path))
        threads = []
        # STAGGER: espaciar el lanzamiento 2s por cuenta para no saturar el cupo
        # de la sala a la vez (las 9 simultaneas hacian que el server cortara a
        # casi todas a los ~1.5s; con espaciado entran las primeras y el backoff
        # adaptativo hace esperar a las demas).
        for i, a in enumerate(accts[:args.accounts]):
            if i > 0:
                time.sleep(2.0)
            name = str(a.get("name") or a.get("user") or ("acct%d" % i))
            dev = a.get("device")
            if not dev:
                print("[multi] %s: sin device, salto" % name)
                continue
            import hashlib
            h = hashlib.md5(dev.encode()).hexdigest()[:16]
            pem = os.path.join(tpm_dir, h + ".pem")
            if not os.path.exists(pem):
                print("[multi] %s: sin PEM fake (%s), salto" % (name, pem))
                continue
            print("[multi] lanzando %s (pem=%s)" % (name, os.path.basename(pem)))
            t = _th.Thread(target=account_loop, args=(dev, pem, name, args), daemon=True)
            t.start()
            threads.append(t)
        if not threads:
            print("[multi] ninguna cuenta valida para lanzar")
            return 1
        print("[multi] %d cuentas corriendo (Ctrl+C para parar)" % len(threads))
        try:
            while any(t.is_alive() for t in threads):
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[multi] Ctrl+C -> parando")
        return 0

    # una sola cuenta
    if not args.device or not args.pem:
        print("ERROR: necesita --device/--pem (una cuenta) o --accounts N (multi)")
        return 1
    _tlocal.account = "main"
    t_start = time.time()
    attempt = 0
    total_vivo = 0.0
    try:
        while True:
            attempt += 1
            if attempt > 1:
                print("\n[rc] sesion %d: reconectando en ~4s..." % attempt)
                time.sleep(4)
            print("\n" + "#" * 64)
            print("  SESION %d  (total vivo acumulado: %.0fs)" % (attempt, total_vivo))
            print("#" * 64)
            total = run_session(args)
            total_vivo += total
            if args.noreconnect:
                print("[rc] --noreconnect: termino tras la sesion %d" % attempt)
                break
            if time.time() - t_start >= getattr(args, "duration", 90):
                print("[rc] duration total alcanzada (%.0fs)" % (time.time() - t_start))
                break
    except KeyboardInterrupt:
        print("\n[rc] Ctrl+C -> parando (total vivo acumulado: %.0fs)" % total_vivo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
