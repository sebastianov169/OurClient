"""
OurClient/network.py — la sesion del binario: login -> joinroom -> TCP -> AUTH.

Reutiliza el flujo VERIFICADO de room_keepalive.run_session (login HTTP,
joinroom, gamemode, connect raw, GREETING, AUTH m2xc, PROOF) pero con hooks
que alimentan el WORLD de OurClient en vez del STATE del visor.

Patron: monkey-patch de T.recv_frame + T.Amf3Decoder + socket.create_connection
(exactamente como client.main.bot_session pero escribiendo en World).
"""
import os
import math
import socket
import struct
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_HERE, _PARENT, os.path.join(_PARENT, "mito_client"), os.path.join(_PARENT, "re")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tcp_full as T
import room_keepalive as RK
from full_login_and_api import load_device_id


def _f(v, d=0.0):
    """float seguro (coercion del visor): None/str -> d."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return d

# AMF3 COMPLETO (re/amf3_full.py): el keepalive decodifica los PINGs con
# TF.Amf3Decoder — el decoder COMPLETO los lee bien (verificado en la
# corrida DELTA=1737 que SI movio la celula: amf3_full + seed del MT
# avanzando -> PONGs correctos -> el server acepta los MOVEs). El decoder
# minimo de tcp_full pierde el stream cifrado post-AUTH y el server deja
# de mandar pings (solo 3 -> sin PONGs -> inactivo -> ignora MOVEs).
try:
    from amf3_full import Amf3Decoder as FullAmf3
    T.Amf3Decoder = FullAmf3
except Exception:
    FullAmf3 = None

_net_ref = [None]      # referencia al Network activo para el hook del decoder
_last_seed = [None]    # encoding_seed capturado del keepalive (MOVE AUTO)
_udp_prefix = [None]   # prefix UDP del keepalive (el que el server registra)


def _extract_names(node, depth, out):
    """Nombres de cuentas desde la estructura AMF3 (op16/op3): busca
    pares (id numerico, string nombre) hasta profundidad 4."""
    if depth > 4 or node is None:
        return
    if isinstance(node, dict):
        nid = node.get("id")
        if isinstance(nid, (int, float)) and not isinstance(nid, bool):
            nm = node.get("name") or node.get("username")
            if isinstance(nm, str) and nm.strip() and len(nm) < 24:
                out[int(nid)] = nm.strip()
        for v in node.values():
            _extract_names(v, depth + 1, out)
    elif isinstance(node, (list, tuple)):
        for v in node:
            _extract_names(v, depth + 1, out)


class Network:
    """La conexion del binario. Conecta y alimenta el World via hooks."""

    def __init__(self, world, args):
        self.world = world
        self.args = args
        self.sock_holder = {"sock": None, "host": None}
        self.udp = {"sock": None, "prefix": b"", "seq": 1,
                    "host": None, "sent": 0, "stop": False}
        self.stats = {"clear": 0, "dump": 0, "ents": 0, "last": 0.0, "t0": 0.0}
        self.running = False
        self._move_t0 = None     # acumulador move_first del MOVE TCP
        self.on_op = None        # callback(op, value, method) AMF3
        self.on_spawn = None     # callback(x, z)
        # cola de CLEARs: el parseo es COSTOSO (decode_clear_full, ~60
        # frames/s) y NO puede correr en el hilo de red — satura el loop
        # del keepalive y retrasa los PONGs -> el server corta (verificado
        # en vivo: sesiones de 20-60s con parseo sincrono, 150s+ sin).
        import queue as _q
        self._clear_queue = _q.Queue(maxsize=2048)
        self._worker = None

    def _start_clear_worker(self):
        """Hilo dedicado que procesa los CLEARs de la cola. El hilo de red
        SOLO recibe y encola (microsegundos) — los PONGs del keepalive
        salen a tiempo y el server no corta."""
        if self._worker is not None:
            return
        _diag_t = [0.0]
        def _loop():
            proc = 0
            while self.running:
                try:
                    payload = self._clear_queue.get(timeout=0.5)
                except Exception:
                    continue
                try:
                    self._process_clear(payload)
                    proc += 1
                except Exception:
                    pass
                now = time.time()
                if now - _diag_t[0] >= 10.0:
                    _diag_t[0] = now
                    w = self.world
                    print("[WORKER] proc=%d cola=%d ents=%d own=%s masa=%s cells=%d pos=(%s,%s) om=%s pj=%d mv=%d ops=%d ping=%d pong=%d lop=%s" % (
                        proc, self._clear_queue.qsize(), len(w.entities),
                        w.player_entity_id,
                        getattr(w.main_cell, "masa", None),
                        len(w.player_cells),
                        _f(w.own_x, -1), _f(w.own_z, -1),
                        _f(w.own_mass, 0.0),
                        self.stats.get("pj", 0),
                        self.udp.get("sent", 0),
                        self.stats.get("ops", 0),
                        self.stats.get("op_ping", 0),
                        self.stats.get("pong", 0),
                        self.stats.get("last_op", "-")), flush=True)
                    # sample: top 5 por masa (verificar que las entidades
                    # ajenas llegan con masa/radio REALES y no como puntitos)
                    try:
                        tops = sorted(w.entities.items(),
                                      key=lambda t: _f(t[1].masa, 0),
                                      reverse=True)[:5]
                        s = " | ".join("%s:m=%.1f r=%s" % (
                            eid, _f(e.masa, 0),
                            getattr(e, "radius", None)) for eid, e in tops)
                        print("[SAMPLE] %s" % s, flush=True)
                    except Exception:
                        pass
        self._worker = threading.Thread(target=_loop, daemon=True)
        self._worker.start()

    def udp_init(self, host):
        """Crea socket UDP + prefix UNA vez; reenvia el init en cada
        llamada.

        Configuracion que FUNCIONO en vivo: diag10/11 (socket+prefix una
        vez, init reenviado en cada create_connection) vivieron 100s con
        mundo completo. El prefix NUEVO por sesion (diag13-15) rompio la
        correlacion -> sesiones muertas a los 0-20s. El server registra el
        init por sesion TCP: reenviar el MISMO prefix alcanza (corrida
        DELTA=1737 reenviaba asi).
        """
        try:
            if self.udp["sock"] is None:
                us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                self.udp["sock"] = us
                self.udp["prefix"] = T.make_udp_prefix()
                self.udp["seq"] = 1
                us.settimeout(0.5)
                stop = self.udp
                def udp_reader():
                    while not stop.get("stop"):
                        try:
                            us.recvfrom(1024)
                        except socket.timeout:
                            pass
                        except Exception:
                            break
                threading.Thread(target=udp_reader, daemon=True).start()
            self.udp["host"] = host
            self.udp["sock"].sendto(T.make_udp_init_packet(self.udp["prefix"]),
                                    (host, T.UDP_PORT))
            print("[UDP] init -> %s:%d (prefix len=%d)" % (host, T.UDP_PORT,
                                                           len(self.udp["prefix"])), flush=True)
            return True
        except Exception:
            return False

    # ---- hooks ----
    def _install(self):
        orig_create = socket.create_connection

        def hooked_create(address, *a, **k):
            sock = orig_create(address, *a, **k)
            try:
                self.sock_holder["host"] = address[0]
                self.world.connected = True
                # UDP: reenviar el init en CADA conexion (la corrida que
                # VERIFICO el movimiento, DELTA=1737, reenviaba aqui). El
                # server registra el prefix por SESION TCP: al reconectar
                # (host nuevo del pool s1837X o sesion nueva en el mismo),
                # el init viejo no vale -> el server ignora los MOVEs ->
                # nunca correlaciona -> no manda flag=6 -> SIN identificacion
                # (reproducido: test_move7/8 con "UNA sola vez" = 0 flag6).
                # En AUTO no hay IRC (irc_sock=None) y las HTTP usan urllib3
                # (referencia propia de create_connection) -> el unico
                # create_connection hookeado es el del juego.
                self.udp_init(address[0])
            except Exception as e:
                print("[NET] hooked_create err: %s" % e, flush=True)
            return sock

        socket.create_connection = hooked_create
        self._orig_recv = T.recv_frame
        T.recv_frame = self._hooked_recv
        # AMF3: hook del decoder para capturar TODOS los ops (op4/16/19/20/25)
        if hasattr(T.Amf3Decoder, "read_value"):
            orig_read = T.Amf3Decoder.read_value

            # CAPTURA del encoding_seed: hook de make_pong_frame_cpp (el
            # keepalive lo llama en CADA PING con el seed ACTUAL del MT —
            # las versiones _auto NUNCA se llaman, verificado L1048/1503).
            # _last_seed alimenta request_entities_info (10002) y move_tcp.
            # Sin esto el seed queda None y el 10002 nunca se envia
            # (el dump del mundo nunca viene -> mundo vacio -> sin
            # identificacion posible; bug visto en diag1/2: dump=0).
            # OJO: hookear el MISMO objeto de modulo que usa el keepalive
            # (RK = import room_keepalive en L26; importar de nuevo como
            # mito_client.room_keepalive crea un SEGUNDO modulo con el
            # mismo archivo y el hook no afecta al que corre).
            try:
                RK_mod = RK
                _orig_pong = RK_mod.make_pong_frame_cpp
                def _hooked_pong(seed, now_ms):
                    _last_seed[0] = seed
                    _net_ref[0].stats["pong"] = _net_ref[0].stats.get("pong", 0) + 1
                    return _orig_pong(seed, now_ms)
                RK_mod.make_pong_frame_cpp = _hooked_pong
                _orig_ent = RK_mod.make_entity_info_frame_cpp
                def _hooked_ent(seed):
                    _last_seed[0] = seed
                    return _orig_ent(seed)
                RK_mod.make_entity_info_frame_cpp = _hooked_ent
            except Exception as e:
                print("[SEED-HOOK] error: %s" % e, flush=True)

            def hooked_read(self):
                v = orig_read(self)
                try:
                    if isinstance(v, list) and v and isinstance(v[0], (int, float)):
                        op = int(v[0])
                        self_net = _net_ref[0]
                        if self_net:
                            # diagnostico: cuantos AMF3 llegan y cuantos son
                            # PINGs del server (op==1) — pings=0 en el
                            # resumen del keepalive puede ser (a) el server
                            # NO manda PINGs (nunca correlaciona) o (b) el
                            # keepalive no los procesa. Solo contadores (el
                            # hilo de red no imprime).
                            self_net.stats["ops"] = self_net.stats.get("ops", 0) + 1
                            if op == 1:
                                self_net.stats["op_ping"] = self_net.stats.get("op_ping", 0) + 1
                                # RTT aproximada: ts del PING vs hora local.
                                # El PING del server llega como [1, ts] — ts
                                # es un timestamp ms relativo. La diferencia
                                # da la RTT del cliente.
                                try:
                                    ts = v[1] if len(v) >= 2 else 0
                                    local_ms = int(time.time() * 1000.0)
                                    if ts > 0:
                                        rtt = abs(local_ms - ts)
                                        # filtrar valores absurdos (>3s = clock skew)
                                        if 0 < rtt < 3000:
                                            self_net.stats["last_ping_ms"] = rtt
                                except Exception:
                                    pass
                            self_net.stats["last_op"] = op
                            self_net.process_amf3(op, v)
                            if self_net.on_op:
                                self_net.on_op(v, "amf3")
                except Exception:
                    pass
                return v

            T.Amf3Decoder.read_value = hooked_read

    def _uninstall(self):
        try:
            T.recv_frame = self._orig_recv
        except Exception:
            pass

    def _hooked_recv(self, sock, timeout=3):
        try:
            self.sock_holder["sock"] = sock
            try:
                host = sock.getpeername()[0]
                self.sock_holder["host"] = host
                if not self.udp.get("sock"):
                    self.udp_init(host)
            except Exception:
                pass
            res = self._orig_recv(sock, timeout)
            try:
                if res and res[0] is not None:
                    _len, flag, payload = res
                    if flag == 1 and payload and payload[0] == 0x64:
                        # ENCOLAR (no parsear aqui): el parseo bloquea el
                        # hilo de red y retrasa los PONGs -> server corta
                        try:
                            self._clear_queue.put_nowait(payload)
                        except Exception:
                            pass
            except Exception:
                pass
            return res
        except Exception:
            # socket cerrado (reconexion normal): devolver None como el original
            return (None, None, None)

    def _process_clear(self, payload):
        """Frames CLEAR: dump 0x04 + eventos -> World."""
        try:
            # SIEMPRE decode_clear_full (unico camino): el branch viejo con
            # decode_dump_19 para payload[1]==0x04 se DESINCRONIZABA (el
            # else 'i+=1' salta mal los eventos intercalados 0x00/0x07 ->
            # 35450 saltos >100u de pepitas/celulas en la captura v5f vs 36
            # con decode_clear_full). decode_clear_full maneja el bloque
            # 0x04 (flag=8 -> eid=owner) Y devuelve self_ids del 0x1c.
            from haxe_clear_parser import decode_clear_full as _dcf
            ents, pid, dead, pj, self_ids = _dcf(payload, return_pj=True)
            is_dump = len(payload) > 1 and payload[1] == 0x04
            # CONTADOR de tipos de evento (diag): ver si llegan celulas de
            # jugadores (0x04 flag=2) o solo comida (flag=1)
            try:
                t0 = payload[1]
                if t0 == 0x04:
                    self.stats["ev_04"] = self.stats.get("ev_04", 0) + 1
                elif t0 == 0x00:
                    self.stats["ev_00"] = self.stats.get("ev_00", 0) + 1
                elif t0 == 0x1c:
                    self.stats["ev_1c"] = self.stats.get("ev_1c", 0) + 1
                elif t0 == 0x07:
                    self.stats["ev_07"] = self.stats.get("ev_07", 0) + 1
                else:
                    self.stats["ev_otro"] = self.stats.get("ev_otro", 0) + 1
            except Exception:
                pass
            # el 0x1c viaja DENTRO del dump y del CLEAR (verificado v5f):
            # sin esto la identificacion de la propia falla en FFA (own=None
            # -> MASA 1 + camara fija). Los ids con 0x1c son las celulas
            # del jugador (correlacion 0.04-1.9 u contra los SETPOS del
            # binario). En FFA el [19] plano es leaderboard y el 0x19/0x1a
            # es account_id — el 0x1c es la identificacion REAL.
            # SIN PRINTS en el hilo de red.
            for sid in self_ids:
                w.player_cells.add(sid)
            # 0x2e = POSICION (x,z) del JUGADOR (FUN_140645d00): la
            # celula propia en FFA NO llega como entidad del mundo —
            # llega por este evento (u16 crudos, misma escala u16/4
            # del resto del CLEAR). Aplicarla al spawn_pos (la celula
            # virtual la usa) — es la fuente de movimiento real.
            if pj is not None:
                px, pz = pj[0] / 4.0, pj[1] / 4.0
                self.stats["pj"] = self.stats.get("pj", 0) + 1
                # posicion REAL del jugador: el MOVE/angulo la usan (cache
                # propio), nunca la celula virtual del spawn fijo
                w.own_x, w.own_z = px, pz
                if self.world.spawn_pos is not None:
                    old = self.world.spawn_pos
                    d = ((old[0] - px) ** 2 + (old[1] - pz) ** 2) ** 0.5
                    if d > 5.0:
                        self.world.spawn_pos = (px, pz)
                        self.world.spawned = True
                else:
                    self.world.spawn_pos = (px, pz)
                    self.world.spawned = True
            if dead:
                for did in dead:
                    self.world.remove(did)
            if ents:
                self._feed(ents)
            # elegir la celula propia de MAYOR masa como main (la
            # camara la sigue); no pisar una ya valida. DESPUES del
            # feed: las entidades ya existen en el World.
            if self_ids:
                with w.lock:
                    valid = [sid for sid in self_ids
                             if sid in w.entities
                             and w.entities[sid].grid_x is not None]
                if valid:
                    best = max(valid, key=lambda sid: w.entities[sid].masa)
                    if w.player_entity_id is None or \
                       w.player_entity_id not in self_ids:
                        w.player_entity_id = best
            if pid:
                # SOLO setear player_entity_id si el pid es una de las
                # celdas propias del op19 (en FFA el 0x19/0x1a trae
                # account_id, NO entity_id — pisar player_entity_id con
                # el account_id hace que la camara siga una entidad ajena).
                # SIN PRINT (hilo de red)
                if pid in w.player_cells:
                    w.player_entity_id = pid
            self.stats["clear"] += 1
            if is_dump:
                self.stats["dump"] += 1
            now = time.time()
            if now - self.stats["last"] >= 30.0:
                    self.stats["last"] = now
                    try:
                        print("[STATS30] ev_04=%s ev_00=%s ev_1c=%s ev_07=%s ev_otro=%s" % (
                            self.stats.get("ev_04", 0), self.stats.get("ev_00", 0),
                            self.stats.get("ev_1c", 0), self.stats.get("ev_07", 0),
                            self.stats.get("ev_otro", 0)), flush=True)
                    except Exception:
                        pass
                    t0 = self.stats.get("t0") or now
                    print("[STATS] %ds: clear=%d dump=%d entidades=%d own=%s" % (
                        int(now - t0), self.stats["clear"], self.stats["dump"],
                        self.stats["ents"], w.player_entity_id), flush=True)
        except Exception:
            pass

    def _feed(self, ents):
        """Aplica las entidades parseadas al World — replica EXACTA de
        feed_clear_entities del visor (client/main.py L518-600, calibrado
        contra el binario 2026-08-14): conserva campos que el frame no trae,
        interpola prev->cur con fixed-timestep, timeout 4s de culling y
        sincroniza el jugador (best_own de player_cells / marca 0x19)."""
        w = self.world
        now = time.time()
        with w.lock:
            for eid, ce in ents.items():
                old = w.entities.get(eid)
                e = w.upsert(eid, getattr(ce, "entityType", 0) or 0)
                # interpolacion: prev = posicion ANTERIOR antes de sobrescribir.
                # ID RECICLADO: el server reutiliza ids (una celula muere y el
                # id pasa a otra entidad en OTRO lugar). Si la masa cambia
                # drasticamente (celula->comida o viceversa) o la distancia es
                # enorme, NO interpolar — snap directo (si no, la entidad
                # "vuela" por la pantalla: 35450 saltos >100u en v5f con el
                # dump desincronizado; los pocos saltos reales son reciclaje).
                _reciclado = False
                if old is not None and old.grid_x is not None and old.grid_y is not None:
                    nx = old.grid_x if ce.x is None else ce.x
                    nz = old.grid_y if ce.z is None else ce.z
                    if nx != old.grid_x or nz != old.grid_y:
                        dx = nx - old.grid_x
                        dz = nz - old.grid_y
                        d2 = dx * dx + dz * dz
                        om = old.masa or 0
                        nm = ce.masa or 0
                        if d2 > 40000.0:  # >200u: reciclaje o spawn nuevo
                            _reciclado = True
                        elif om > 0 and nm > 0 and (om / nm > 20.0 or nm / om > 20.0):
                            _reciclado = True  # celula <-> comida: id reusado
                        if not _reciclado:
                            w._ent_prev[eid] = (old.grid_x, old.grid_y, now)
                if _reciclado:
                    # snap: sin prev -> lerp_pos dibuja directo en la nueva
                    w._ent_prev.pop(eid, None)
                # conservar campos que el frame no trae
                if ce.x is None:
                    ce.x = old.grid_x if old is not None else None
                if ce.z is None:
                    ce.z = old.grid_y if old is not None else None
                if (ce.masa is None or ce.masa <= 0) and old is not None:
                    ce.masa = old.masa
                    if not getattr(ce, "radio", 0):
                        ce.radio = old.radius
                # aplicar
                if ce.masa and ce.masa > 0:
                    e.masa = ce.masa
                if getattr(ce, "radio", 0):
                    e.radius = ce.radio
                # POSICION: el flag=6 (entityType 6 = FlagBase = frame de
                # celulas propias) trae la CELDA DEL GRID (multiplos de 256:
                # 2048, 3840 = celda 8x15 del mundo 16384), NO la posicion
                # fina del jugador. Pisar grid_x/grid_y con la celda congelaba
                # al jugador (DELTA=0 reproducido). La posicion fina real
                # viene del dump 0x04 (entidad normal del mundo).
                et = getattr(ce, "entityType", 0) or 0
                if et != 6 and ce.x is not None and ce.z is not None:
                    e.grid_x, e.grid_y = ce.x, ce.z
                    # posicion REAL de la propia (el 0x00 mueve TODAS las
                    # entidades, incluida la nuestra): el MOVE/angulo usan
                    # esta, nunca la celula virtual del spawn fijo
                    if eid == w.player_entity_id:
                        w.own_x, w.own_z = ce.x, ce.z
                        if ce.masa and ce.masa > 1.0:
                            w.update_own_mass(ce.masa)
                        w._t_last_own_seen = time.time()
                # OWNER: la celula cuya cuenta dueña == account_id (op4
                # player_id) ES la nuestra. En FFA el op19 NO trae celulas
                # propias (formato: [19,[1]] = id de cuenta, o lista plana
                # = leaderboard) y el flag=6 tampoco llega — el owner del
                # dump es la identificacion real (wire: [count][flag]
                # [owner][id][fc]).
                ow = getattr(ce, "owner", 0) or 0
                if ow and ow == w.account_id and ce.masa and ce.masa > 1.0:
                    # SIN PRINT: el hilo de red no imprime (ralentiza PONGs
                    # y el server corta la sesion)
                    e._owner_seen = ow
                    w.player_cells.add(eid)
                    w.update_own_mass(ce.masa)
                    w.own_id_real = eid
                    w._t_last_own_seen = time.time()
                    if w.player_entity_id is None:
                        w.player_entity_id = eid
                    # ACTUALIZAR spawn_pos con la posicion real de la celula
                    # del jugador (sin 0x2e en FFA, esta es la UNICA fuente
                    # de posicion real despues del spawn).
                    if ce.x is not None and ce.z is not None:
                        w.spawn_pos = (ce.x, ce.z)
                        # posicion REAL de la propia para el MOVE/angulo
                        w.own_x, w.own_z = ce.x, ce.z
                elif ow and ow != w.account_id and ow != 0 and ce.masa and ce.masa > 1.0:
                    e._owner_other = ow
                    e._owner_logged = ow
                if et == 6 and ce.masa and ce.masa > 1.0:
                    # flag=6 = frame de CELULAS PROPIAS (el server lo manda
                    # al correlacionar el MOVE con la cuenta; wire real: id
                    # + masa/radio REALES — 60 en CTF). Es la identificacion
                    # del jugador en el wire, igual de autoritativa que el
                    # op19 (que en FFA llega malformado [19,[1]] = id de
                    # CUENTA, no celula). Anadir a player_cells y adoptar
                    # como main si aun no hay identificacion.
                    # SIN PRINT (hilo de red)
                    w.player_cells.add(eid)
                    w.update_own_mass(ce.masa)
                    w.own_id_real = eid
                    w._t_last_own_seen = now
                    if w.player_entity_id is None:
                        w.player_entity_id = eid
                e._last_seen = now
            # timeout de culling: el server hace culling por frustrum y deja
            # de mandar lo que sale de vista. En CTF el dump 0x64 re-manda
            # TODO el mundo cada ~30s (culling 4s seguro). En FFA el server
            # NO manda el dump (verificado en vivo: dump=0 en sesiones de
            # 100s) — solo CLEARs delta — y 4s borraba TODO el mundo
            # (entidades=153 -> 2). Culling 30s: los deltas se acumulan y
            # las entidades vivas se refrescan; las muertas llegan como 0x07.
            stale = [eid for eid, e in w.entities.items()
                     if now - getattr(e, "_last_seen", 0) > 30.0
                     and eid not in w.player_cells
                     and eid != w.player_entity_id]
            for eid in stale:
                w.entities.pop(eid, None)
                w._ent_prev.pop(eid, None)
            # --- SINCRONIZAR el jugador (op19 autoritativo + marca 0x19) ---
            if w.player_entity_id is not None:
                pe = w.entities.get(w.player_entity_id)
                # INVALIDO solo si el id fue RECICLADO: la entidad existe
                # pero con masa de comida (<= 1.0) o sin posicion (own=3196
                # masa=64.75 -> masa=0.0 en vivo: el server reuso el id para
                # otra entidad tras la muerte). NO invalidar por pe is None:
                # el 0x07 dead de la propia llega por culling/recreacion del
                # server SIN muerte real (la entidad se re-manda con el mismo
                # id al frame siguiente) y el 0x1c es esporadico en vivo —
                # invalidar ahi cortaba la identificacion (own=3707 masa=35.0
                # -> own=None sin [MUERTE]).
                if (pe is not None
                        and (pe.grid_x is None
                             or getattr(pe, "masa", 0) is None
                             or getattr(pe, "masa", 0) <= 1.0)):
                    w.player_entity_id = None  # la marca murio: re-identificar
            # Re-identificar desde player_cells SIEMPRE (no solo con
            # _op19_seen): en FFA el op19 plano es leaderboard (nunca
            # lista-de-listas -> _op19_seen=False) y la identificacion
            # real son los self_ids del 0x1c (player_cells). Sin esto,
            # al morir la celula propia player_entity_id queda None para
            # siempre (verificado en vivo: own intermitente 3729/811/None).
            if w.player_entity_id is None and w.player_cells:
                # SOLO celulas REALES (masa > 1.0): el id reciclado queda en
                # player_cells (0x1c lo marco) pero el server lo reuso para
                # comida (masa 1.0) -> adoptarlo hacía que la camara siguiera
                # una pepita (own=1485 masa=1.0 en vivo: la celula se
                # teletransportaba, se quedaba quieta o desaparecia).
                valid = [eid for eid in w.player_cells
                         if eid in w.entities
                         and w.entities[eid].grid_x is not None
                         and (w.entities[eid].masa or 0) > 1.0]
                if valid:
                    w.player_entity_id = max(
                        valid, key=lambda eid: w.entities[eid].masa)
            # --- FFA: correlacion con el SPAWN del [20] ---
            # En FFA el server NO manda el dump 0x04 ni la marca 0x19 ni
            # flag=6 (verificado en vivo: sesion 100s, clear=229, dump=0,
            # 0 marcas). La unica via es el [20]: el jugador aparece EN el
            # spawn_pos -> la entidad mas cercana al spawn con masa > 1 es
            # la celula del jugador (el [20] da posicion EXACTA del spawn).
            if w.player_entity_id is None and w.spawn_pos is not None:
                sx, sz = w.spawn_pos
                best = None
                best_d = None
                for eid, e in w.entities.items():
                    if e.grid_x is None or e.grid_y is None:
                        continue
                    m = e.masa or 0
                    # SOLO masas realistas de una celula recien spawneada
                    # (25-40; max ~150 con suerte): un gigante de ~9000
                    # cerca del spawn NO puede ser la propia (bug en vivo:
                    # own=597 masa=9147.5 adoptado por esta correlacion →
                    # MASA 8519 en el HUD con la propia chica dibujada como
                    # ajena). La propia gigante llega por owner==account_id
                    # (autoritativo), no por cercania.
                    if not (1.0 < m < 200.0):
                        continue
                    # entidad con owner AJENO conocido: descartar
                    if getattr(e, "_owner_other", None):
                        continue
                    d = abs(e.grid_x - sx) + abs(e.grid_y - sz)
                    if best_d is None or d < best_d:
                        best_d = d
                        best = eid
                if best is not None and best_d < 2000:
                    w.player_entity_id = best
            w._t_last_clear = now
        self.stats["ents"] += len(ents)

    # ---- AMF3 (ops de juego) ----
    def process_amf3(self, op, value):
        """op4 player_id(cuenta), op16 nombres, op19 tus celulas, op20 spawn."""
        w = self.world
        if op == 4 and len(value) >= 2:
            # op4 = player_id de la CUENTA (NO la entidad del mundo). El
            # visor lo guarda aparte (_pid_holder); player_entity_id solo
            # se setea con la marca 0x19/0x1a del CLEAR o el best_own del
            # op19. (corregido 2026-08-14: antes la camara seguia una
            # entidad ajena porque op4 pisaba player_entity_id)
            # OJO: el op4 tambien llega como [4, {dict info cuenta}] (el
            # LOAD del jugador con ics/tiles). Con dict NO pisar account_id:
            # el [4, id_plano] del handshake ya lo seteo (captura real:
            # [4, 33, ts] plano + [4, {'id': 4, ...}] despues).
            if isinstance(value[1], (int, float)):
                w.account_id = int(value[1])
        elif op == 16 and len(value) >= 2:
            # info de jugadores: [16, [id, {username, name, color...}], ts]
            names = {}
            _extract_names(value, 0, names)
            if names:
                w.names.update(names)
                for eid, nm in names.items():
                    w.leaderboard.setdefault(eid, {})["name"] = nm
            info = value[1]
            if isinstance(info, list) and len(info) >= 2 and isinstance(info[1], dict):
                eid16 = info[0]
                w.player_info[eid16] = info[1]
                w.leaderboard.setdefault(eid16, {})["name"] = (
                    info[1].get("name") or info[1].get("username") or "")
        elif op == 19 and len(value) >= 2:
            ids = value[1]
            # Formato REAL (captura 2026-08-14, identico al visor
            # client/main.py L916-934): [19, [[id1, id2...], [flags]], ts].
            # SOLO la primera lista son celulas propias. Si ids[0] NO es
            # lista (ej. [19,[1]] en FFA = id de cuenta/flag, NO una
            # celula), NO identificar nada: un escalar como celula
            # "1" hacia main=1 masa=1.0 (comida) -> DELTA=0 (bug
            # reproducido en test_move6). El visor tampoco lo acepta.
            if isinstance(ids, list) and ids and isinstance(ids[0], list):
                cells_raw = ids[0]
                cells = [int(i) for i in cells_raw
                         if isinstance(i, (int, float))]
                w.player_cells = set(cells)
                w._op19_seen = True
                # op19 autoritativo: si el server NO marco la entidad con
                # 0x19/0x1a aun, adoptar la celula propia de MAS masa (como
                # feed_clear_entities del visor, client/main.py L592-600)
                if w.player_entity_id is None:
                    with w.lock:
                        valid = [eid for eid in w.player_cells
                                 if eid in w.entities
                                 and w.entities[eid].grid_x is not None
                                 and w.entities[eid].grid_y is not None]
                    if valid:
                        w.player_entity_id = max(
                            valid, key=lambda eid: w.entities[eid].masa)
        elif op == 20 and len(value) >= 2:
            pos = value[1]
            if isinstance(pos, list) and len(pos) >= 3:
                w.spawn_pos = (pos[0], pos[2])
                # posicion REAL del spawn para el MOVE/angulo inicial
                w.own_x, w.own_z = pos[0], pos[2]
                w.spawned = True
                # masa inicial del [20] si viene: en captura v5f el server
                # manda [pos, masa, ...] — si esta, guardala como masa
                # inicial del jugador (suele ser 10-30, nunca 0)
                try:
                    if len(pos) >= 4 and isinstance(pos[3], (int, float)) and pos[3] > 0:
                        w.mass = float(pos[3])
                        if w.mass > 1.0:
                            w.update_own_mass(w.mass)
                except Exception:
                    pass
                # respawn: re-identificar (el jugador reaparece en otra parte)
                w.player_entity_id = None
                if self.on_spawn:
                    self.on_spawn(pos[0], pos[2])
        elif op == 25 or (op == 16 and len(value) > 1
                          and isinstance(value[1], list) and value[1]
                          and value[1][0] == 25):
            # [25] / [16,[25,[]]] = el jugador MURIO (respawn-ready)
            w.spawned = False
            w.player_entity_id = None

    # ---- sesion ----
    def request_entities_info(self):
        """CLIENT_ENTITIES_INFO (10002): hace que el server mande el DUMP
        del mundo. FORMATO = make_entity_info_frame_cpp (m2xcTcp, el MISMO
        del keepalive L1322/L1678 — el que trajo dump=2671 en test_move9).
        NO usar make_client_frame (resturple): el server del modo 5 lo
        rechaza y CORTA la sesion a los 0.0s (reproducido en diag7: con
        resturple [SEED] ent -> [DEAD] 0.0s; sin 10002 -> sesion 100s)."""
        try:
            sock = self.sock_holder.get("sock")
            seed = _last_seed[0]
            if sock is None or seed is None:
                return False
            logical = T.amf_array([T.amf_int(10002), T.amf_array([T.amf_int(0)])])
            frame = RK.tcp_frame_from_logical(logical, seed)
            T.send_frame(sock, frame, log_it=False, label="ENT_INFO")
            self.stats["ent_info"] = self.stats.get("ent_info", 0) + 1
            return True
        except Exception:
            return False

    def move_tcp(self, angle, power):
        """MOVE REAL del binario — wire EXACTO (verificado con visor
        client/main.py udp_commands_thread L1060): make_move_frame que es
        TCP CLARO (sin cifrar) con formato make_tcp_clear_frame:
        [len:u32][len:u32][0x40][opcode:u32=10022][time:f32][angle:f32][power:f32]

        ANTES este metodo usaba make_client_frame (m2xc cifrado) — el
        server lo IGNORA en AUTO y la cuenta queda congelada en el mundo
        del otro jugador aunque el MOVE sale: "no se mueve en el mundo
        del server" (verificado). El canal real es TCP claro + 10022,
        y el UDP 3724 del visor es solo REFUERZO cada 100ms (mismo
        formato binario del wire 0x2726).
        """
        try:
            sock = self.sock_holder.get("sock")
            if sock is None:
                return False
            # time_accu: el visor usa time.time()%1000 (lo llama "time_accu"
            # pero es un float cualquiera). El server solo lo usa como
            # identificador/secuencia del MOVE; cualquier float sirve.
            import time as _t
            t_accu = (_t.time() % 1000.0)
            frame = T.make_move_frame(t_accu, float(angle), float(power))
            sock.sendall(frame)
            self.stats["move_tcp"] = self.stats.get("move_tcp", 0) + 1
            return True
        except Exception:
            return False

    def udp_move(self, tx, tz, px, pz, power=None):
        """MOVE UDP del binario (misma implementacion que el visor
        client/main.py udp_move, formato real: 0x002726 + 34.0 + angulo +
        power). El mouse del jugador dirige la celula hacia (tx,tz).

        BLINDADO: getaddrinfo/dns failsafe. El crash final de la corrida
        de 1292s fue [Errno 11001] getaddrinfo failed: el server cierra
        el TCP, el socket holder queda con host stale y el MOVE revienta
        el hilo principal. Aqui: si host es None o sendto falla por DNS,
        NO lanzar — devolver False y permitir que force_reconnect / el
        proximo create_connection re-resuelva el host.
        """
        us = self.udp.get("sock")
        host = self.udp.get("host")
        if us is None or host is None or not isinstance(host, str):
            return False
        dx, dz = tx - px, tz - pz
        dist = math.hypot(dx, dz)
        if dist < 1:
            return False
        angle = math.atan2(dz, dx)
        pw = power if power is not None else 1.0
        # prefix: SIEMPRE el propio (el visor que FUNCIONA usa el suyo
        # _udp_holder["prefix"] — el server acepta el init del hooked_create)
        prefix = self.udp["prefix"]
        # Wire EXACTO del binario (verificado con capturas Frida reales):
        # [prefix:9][flag:1=00][2B=0000][msgId:1][1B=00][opcode:16 BE=2726]
        # [float32 BE]*3 (velocidad, angulo, power) + ffffffff + padding 4
        pkt = bytearray(prefix)
        pkt += b"\x00\x00\x00"
        pkt += struct.pack('>B', self.udp["seq"] & 0xFF)
        pkt += b"\x00"
        self.udp["seq"] += 1
        pkt += bytes.fromhex("2726")
        pkt += struct.pack('>f', 34.0)
        pkt += struct.pack('>f', angle)
        pkt += struct.pack('>f', pw)
        pkt += bytes.fromhex("ffffffff00000000")
        try:
            us.sendto(bytes(pkt), (host, T.UDP_PORT))
        except (socket.gaierror, OSError):
            # host stale: invalidar y dejar que el proximo create_connection
            # re-resuelva (force_reconnect ya esta en camino)
            self.udp["host"] = None
            self.stats["udp_fail"] = self.stats.get("udp_fail", 0) + 1
            return False
        self.udp["sent"] = self.udp.get("sent", 0) + 1
        return True

    def run(self, stop_event):
        """Loop de sesion (reconecta solo, como bot_session del visor)."""
        global _net_ref
        _net_ref[0] = self
        self._install()
        self.running = True
        self._start_clear_worker()
        while self.running and not stop_event.is_set():
            try:
                args = self.args
                total = RK.run_session(args)
                print("[NET] sesion termino (%.0fs viva)" % total, flush=True)
            except Exception as e:
                print("[NET] error: %s" % e, flush=True)
            self.world.connected = False
            self.world.spawned = False
            time.sleep(4)
        self._uninstall()

    def stop(self):
        self.running = False
        sock = self.sock_holder.get("sock")
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

    def force_reconnect(self):
        """Cierra el socket activo: run_session retorna y el loop reconecta
        con los args NUEVOS (modo/servidor del lobby)."""
        sock = self.sock_holder.get("sock")
        if sock is not None:
            try:
                sock.close()
                print("[NET] reconectando con seleccion nueva", flush=True)
            except Exception:
                pass


def build_args(device, pem, room, server="europe", mode=0, autorespawn=False):
    import argparse
    return argparse.Namespace(
        device=device, pem=pem, accounts=0, exclude="", room=room,
        code="", duration=86400, spawn_wait=90, quiet=True,
        verbose=False, noreconnect=True,
        spawn_event=threading.Event(),
        autorespawn=autorespawn,
        server=server,
        mode=(5 if mode == 0 else mode),
        # REEVIO del 10002 ACTIVADO para el OurClient (medicalt): sin el
        # reenvio el server corta la sesion a los ~20s exactos (verificado
        # en vivo 2026-08-16: DEAD a 17.3-20.2s en TODAS las corridas con
        # no_resend_entities=True, con PONGs saliendo 1:1, identificacion
        # y celula moviendose). El reenvio periodico (cada 30s) es lo que
        # el server espera para mantener la sesion: el binario renueva el
        # dump con CLIENT_ENTITIES_INFO.
        no_resend_entities=False,
    )
