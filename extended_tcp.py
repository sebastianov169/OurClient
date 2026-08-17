#!/usr/bin/env python3
"""
Extended TCP client - sends more client frames to trigger server responses.
Goal: find coin balance and account name in TCP frames.
"""
import sys, os, socket, struct, time, json, hashlib, base64, random, math
import importlib.util, requests, urllib.parse, warnings
warnings.filterwarnings('ignore')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from tcp_full import *

def main():
    print("=" * 70)
    print("  EXTENDED TCP CLIENT - Search for coins & username")
    print("=" * 70)
    
    # Login
    sk, magic, session = do_login()
    
    # API calls
    make_api = lambda p: make_api_call(session, sk, magic, p)
    make_api({'do': 'gamemode', 'index': 1, 'mode': 3})
    make_api({'do': 'servers', 'change': 'south_america'})
    r = make_api({'do': 'connect', 'invite': False, 'defered': True, 'i': 1, 'gm': -1, 'retrying': False, 'locale': 'es_CO'})
    server = r['data']['server']
    token = r['data']['token']
    host, port = server.split(':')
    print("Server:", server)
    
    # TCP connect
    sock = socket.create_connection((host, int(port)), timeout=10)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    # UDP
    us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    chars = "abcdefghilmnopqrstuwjkxyzQWERTYUIOPASDFGHJKLZXCVBNM;:_-.,0987654321^"
    pfx = bytes([0x80 | random.randint(0, 0x7F)]) + ''.join(random.choice(chars) for _ in range(8)).encode()
    try:
        us.sendto(pfx + bytes.fromhex("00000000012731ffffffff00000000000000000000000000000000"), (host, 3724))
    except: pass
    
    # Greeting
    ln, fl, pl = recv_frame(sock, 5)
    v, dec, sd = try_decode_destpurple(pl, [0])
    suffix = v[-8:]
    str_k = get_str_key(suffix)
    mt = MersenneTwister(str_k)
    ss = mt.next_val() % 99999
    es = 0
    print("Suffix:", suffix, "server_seed:", ss)
    
    # Auth
    send_frame(sock, make_auth_frame(host, suffix, token, 3, ext_id=239))
    
    # Read PLAYER_ID
    ln, fl, pl = recv_frame(sock, 5)
    v, dec, sd2 = try_decode_destpurple(pl, [0, ss])
    pid = v[1] if v and isinstance(v, list) and v[0] == 4 else -1
    print("PLAYER_ID:", pid)
    
    # httpPlay in background
    import threading
    t = threading.Thread(target=lambda: (time.sleep(0.3), make_api({'do': 'play', 'usertoken': None})), daemon=True)
    t.start()
    
    # Send READY
    send_frame(sock, make_ready_frame(0))
    send_frame(sock, make_tcp_clear_frame(10034, []))
    
    # Read initial frames
    print("\n=== INITIAL FRAMES ===")
    all_amf3 = []
    all_clear = []
    for i in range(50):
        ln, fl, pl = recv_frame(sock, 2)
        if ln is None:
            es = mt.next_val() % 99999
            send_frame(sock, make_ping_frame(es, 0))
            time.sleep(0.05)
            continue
        if fl == 1:
            all_clear.append((len(pl), pl))
            if len(pl) == 6651:
                print("ENTITY DUMP %d bytes" % len(pl))
            elif len(pl) > 4:
                second = pl[1]
                print("CLEAR size=%d type=0x%02x" % (len(pl), second))
            continue
        v, dec, sd2 = try_decode_destpurple(pl, [0, ss, es])
        if v is None:
            for b in range(256):
                try:
                    d2 = bytearray_destpurple(pl, b)
                    if len(d2) > 0 and d2[0] <= 0x09:
                        v = Amf3Decoder(d2).rv()
                        if v is not None: break
                except: pass
        if v is not None and isinstance(v, list) and len(v) > 0:
            op = v[0] if isinstance(v[0], int) else -1
            all_amf3.append((op, v))
            if op == 1:
                es = mt.next_val() % 99999
                send_frame(sock, make_ping_frame(es, v[1] if len(v) > 1 else 0))
            else:
                print("AMF3 OP=%d: %s" % (op, repr(v)[:500]))
    
    # Now try sending MORE client frames
    print("\n=== SENDING CLIENT FRAMES ===")
    
    # OP_CLIENT_ENTITIES_INFO (10002)
    print("Sending OP_CLIENT_ENTITIES_INFO (10002)...")
    logical = amf_array([amf_int(10002), amf_array([amf_int(pid)])])
    payload = logical + b'\x00\x00'
    frame = make_client_frame(payload, len(logical), 0, es)
    send_frame(sock, frame)
    time.sleep(0.5)
    
    # Read response
    for i in range(10):
        ln, fl, pl = recv_frame(sock, 0.5)
        if ln is None: break
        if fl == 1:
            if len(pl) > 4:
                print("  CLEAR size=%d" % len(pl))
            continue
        v, dec, sd2 = try_decode_destpurple(pl, [0, ss, es])
        if v is None:
            for b in range(256):
                try:
                    d2 = bytearray_destpurple(pl, b)
                    if len(d2) > 0 and d2[0] <= 0x09:
                        v = Amf3Decoder(d2).rv()
                        if v is not None: break
                except: pass
        if v is not None and isinstance(v, list) and len(v) > 0:
            op = v[0] if isinstance(v[0], int) else -1
            print("  AMF3 OP=%d: %s" % (op, repr(v)[:500]))
            if op == 1:
                es = mt.next_val() % 99999
                send_frame(sock, make_ping_frame(es, v[1] if len(v) > 1 else 0))
    
    # OP_CLIENT_PLAYER_UPDATE (10020)  
    print("\nSending OP_CLIENT_PLAYER_UPDATE (10020)...")
    logical = amf_array([amf_int(10020), amf_array([
        amf_int(pid), amf_string("dhihghkajlk")
    ])])
    payload = logical + b'\x00\x00'
    frame = make_client_frame(payload, len(logical), 0, es)
    send_frame(sock, frame)
    time.sleep(0.5)
    
    for i in range(10):
        ln, fl, pl = recv_frame(sock, 0.5)
        if ln is None: break
        if fl == 1:
            if len(pl) > 4:
                print("  CLEAR size=%d" % len(pl))
            continue
        v, dec, sd2 = try_decode_destpurple(pl, [0, ss, es])
        if v is None:
            for b in range(256):
                try:
                    d2 = bytearray_destpurple(pl, b)
                    if len(d2) > 0 and d2[0] <= 0x09:
                        v = Amf3Decoder(d2).rv()
                        if v is not None: break
                except: pass
        if v is not None and isinstance(v, list) and len(v) > 0:
            op = v[0] if isinstance(v[0], int) else -1
            print("  AMF3 OP=%d: %s" % (op, repr(v)[:500]))
            if op == 1:
                es = mt.next_val() % 99999
                send_frame(sock, make_ping_frame(es, v[1] if len(v) > 1 else 0))
    
    # OP_CLIENT_CONTROL_SETUP (10031)
    print("\nSending OP_CLIENT_CONTROL_SETUP (10031)...")
    logical = amf_array([amf_int(10031)])
    payload = logical + b'\x00'
    frame = make_client_frame(payload, len(logical), 0, es)
    send_frame(sock, frame)
    time.sleep(0.5)
    
    for i in range(10):
        ln, fl, pl = recv_frame(sock, 0.5)
        if ln is None: break
        if fl == 1:
            if len(pl) > 4:
                print("  CLEAR size=%d" % len(pl))
            continue
        v, dec, sd2 = try_decode_destpurple(pl, [0, ss, es])
        if v is None:
            for b in range(256):
                try:
                    d2 = bytearray_destpurple(pl, b)
                    if len(d2) > 0 and d2[0] <= 0x09:
                        v = Amf3Decoder(d2).rv()
                        if v is not None: break
                except: pass
        if v is not None and isinstance(v, list) and len(v) > 0:
            op = v[0] if isinstance(v[0], int) else -1
            print("  AMF3 OP=%d: %s" % (op, repr(v)[:500]))
            if op == 1:
                es = mt.next_val() % 99999
                send_frame(sock, make_ping_frame(es, v[1] if len(v) > 1 else 0))
    
    # Send MOVE to trigger game state updates
    print("\nSending MOVES to trigger entity updates...")
    for i in range(20):
        es = mt.next_val() % 99999
        send_frame(sock, make_ping_frame(es, float(time.time() * 1000)))
        # Send a CLEAR move frame
        angle = (i * 0.3) % (2 * math.pi)
        mx = math.cos(angle) * 100
        my = math.sin(angle) * 100
        move_body = struct.pack('>I', 12) + struct.pack('>I', 12) + b'\x40' + struct.pack('>If', 10022, mx) + struct.pack('>f', my) + struct.pack('>f', angle) + struct.pack('>f', 0.93)
        send_frame(sock, move_body)
        
        # Read responses
        for j in range(5):
            ln, fl, pl = recv_frame(sock, 0.1)
            if ln is None: break
            if fl == 1:
                if len(pl) > 4 and len(pl) not in (1, 8, 15):
                    print("  CLEAR size=%d" % len(pl))
                continue
            v, dec, sd2 = try_decode_destpurple(pl, [0, ss, es])
            if v is None:
                for b in range(256):
                    try:
                        d2 = bytearray_destpurple(pl, b)
                        if len(d2) > 0 and d2[0] <= 0x09:
                            v = Amf3Decoder(d2).rv()
                            if v is not None: break
                    except: pass
            if v is not None and isinstance(v, list) and len(v) > 0:
                op = v[0] if isinstance(v[0], int) else -1
                if op == 1:
                    es = mt.next_val() % 99999
                    send_frame(sock, make_ping_frame(es, v[1] if len(v) > 1 else 0))
                elif op not in (1,):
                    print("  AMF3 OP=%d: %s" % (op, repr(v)[:500]))
        
        time.sleep(0.1)
    
    # Disconnect
    send_frame(sock, make_disconnect_flush_frame(es))
    sock.close()
    us.close()
    
    print("\n=== SUMMARY ===")
    print("AMF3 frames:", len(all_amf3))
    for op, v in all_amf3:
        print("  OP=%d: %s" % (op, repr(v)[:300]))
    print("CLEAR frames:", len(all_clear))
    for sz, data in all_clear:
        if sz > 4:
            print("  size=%d hex=%s" % (sz, data.hex()[:80]))
    print("DONE")

if __name__ == "__main__":
    main()
