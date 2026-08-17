"""
OurClient/main.py — el cliente NUEVO con la arquitectura del binario.

  Engine (fkengine.core.Engine)
    -> Network (login/joinroom/TCP/AUTH + hooks -> World)
    -> World (fkengine.game.Grid: entidades con fabrica FUN_14073b220)
    -> View (FUN_140795df0: camara, input updateMouse_core, render)
    -> HUD (Game lobby + CurrentPlayingView)

Independiente del visor (mito_view.py / client/main.py): solo usa
client/ (clases del binario) + mito_client (red verificada) + re/ (parser).
"""
import argparse
import math
import os
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for p in (_HERE, _PARENT, os.path.join(_PARENT, "mito_client"), os.path.join(_PARENT, "re")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pygame

from OurClient.engine import Engine
from OurClient.world import World
from OurClient.network import Network, build_args, load_device_id
from OurClient.view import View, _f
import OurClient.hud as hud

W, H = hud.W, hud.H
FPS = 60


def send_game_cmd(name):
    """split/eject: opcodes del binario verificados por el visor (cliente
    client/main.py L1016):
      - SPLIT: TCP claro make_split_frame() = [len][len][0x40][10010]
                (NO floats, NO cifrar, NO frame_from_op viejo).
      - EJECT: mismo formato con opcode 10011.
    ANTES el OurClient usaba frame_from_op(0x271a, []) que mandaba un
    frame equivocado — el server lo ignoraba y la celula no spliteaba.
    """
    import tcp_full as T
    import room_keepalive as RK
    sock = getattr(RK, "_current_sock", None)
    if sock is None:
        return
    try:
        if name == "split":
            sock.sendall(T.make_split_frame())
        elif name == "eject":
            sock.sendall(T.make_tcp_clear_frame(10011, []))
    except Exception:
        pass


def _send_move(angle, power, net=None, view=None):
    """MOVE REAL del binario: UDP 3724 con el prefix propio — el canal que
    FUNCIONO (verificado: DELTA=1737 en la corrida del harness). El MOVE
    TCP (claro o cifrado) NO funciona en flujo AUTO — solo estorba."""
    if net is None or view is None:
        return
    w = view.world
    # posicion REAL de la propia (own_x/own_z, actualizada por el 0x00):
    # NUNCA la celula virtual del spawn fijo (esquina del mapa) — el MOVE
    # desde el spawn hacia el target hacia que la celula "no respondiera"
    px, pz = w.own_x, w.own_z
    if px is None or pz is None:
        # fallback: spawn_pos del [20] — SIEMPRE mandar el MOVE (sin MOVEs
        # el server no correlaciona -> no manda el 0x1c -> identificacion
        # nunca llega -> own=None permanente)
        sp = w.spawn_pos
        if sp is not None:
            px, pz = _f(sp[0]), _f(sp[1])
        else:
            main = w.main_cell
            if main is None or main.grid_x is None or main.grid_y is None:
                return
            px, pz = _f(main.grid_x), _f(main.grid_y)
    px, pz = _f(px), _f(pz)
    dist = 800.0
    tx = px + math.cos(angle) * dist
    tz = pz + math.sin(angle) * dist
    net.udp_move(tx, tz, px, pz, power=power)


_last_udp_move = [0.0]  # ultimo MOVE TCP claro (~17ms = 60Hz)
_last_udp_only = [0.0]   # ultimo MOVE UDP refuerzo (~100ms)


def main():
    try:
        _main_inner()
    except Exception as e:
        import traceback as _tb
        print("=" * 60, flush=True)
        print("  FATAL OurClient:", e, flush=True)
        _tb.print_exc()
        print("=" * 60, flush=True)
        # dar 5s para que el usuario vea el trace, luego salir limpio
        import time as _t
        try:
            import pygame as _pg
            for _ in range(50):
                for _ in _pg.event.get():
                    pass
                _t.sleep(0.1)
        except Exception:
            pass


def _main_inner():
    ap = argparse.ArgumentParser(description="OurClient — MitosisOG en Python")
    ap.add_argument("--server", default="europe")
    ap.add_argument("--mode", type=int, default=0, help="0=SALAS 3=CTF 5=FFA 7=HVZ")
    ap.add_argument("--room", default="")
    ap.add_argument("--device", default=None)
    ap.add_argument("--pem", default=None)
    args = ap.parse_args()

    device = args.device or load_device_id()
    pem = args.pem or os.path.join(_PARENT, "embedded_rsa_private_14.pem")
    if not os.path.exists(pem):
        pem = os.path.join(_PARENT, "mito_client", "embedded_rsa_private_14.pem")

    # ---- arquitectura del binario ----
    world = World()
    view = View(world, W, H)
    net_args = build_args(device, pem, args.room, args.server, args.mode)
    # SINCRONIZAR el lobby con el modo real de la sesion: STATE.lobby_mode
    # se inicializa en 0 (SALAS) en client/main.py pero la sesion va a FFA
    # (--mode 5) — la GUI mostraba SALAS mientras el server asignaba FFA
    # ("switchea entre dos modos"). El modo del lobby = el de la sesion.
    import client.main as _C
    with _C.STATE.lock:
        _C.STATE.lobby_mode = args.mode
        _C.STATE.lobby_server = args.server
    net = Network(world, net_args)
    net.on_spawn = lambda x, z: setattr(world, "spawn_pos", (x, z))

    # AMF3 -> mundo (op4/16/19/20)
    def amf3_hook(v, method):
        if isinstance(v, list) and v and isinstance(v[0], (int, float)):
            net.process_amf3(int(v[0]), v)
    net.on_op = amf3_hook

    stop_event = threading.Event()
    net_thread = threading.Thread(target=net.run, args=(stop_event,), daemon=True)
    net_thread.start()

    # ---- pygame ----
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("OurClient — MitosisOG")
    font = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 24)
    font_tiny = pygame.font.Font(None, 18)
    clock = pygame.time.Clock()

    engine = Engine(on_tick=lambda dt: view.update_camera(dt))
    engine.start()

    _last_sel = [(args.mode, args.server)]  # (modo, servidor) de la sesion actual
    _last_ent_info = [0.0]  # ultima peticion de dump (5s min)
    # estado del input box de sala (modo SALAS): el click lo enfoca, las
    # teclas escriben, ENTER confirma, ESC cancela.
    _sala_edit = {
        "active": False,
        "text": args.room or "",
        "caret": 0,
    }
    # CONTADOR DE FPS: el clock.tick devuelve ms por frame; sample cada 0.5s
    _fps_state = {"frames": 0, "t0": time.time(), "fps": 0.0}
    # MEDICION DE LATENCIA: la ultima RTT de PING del keepalive
    _ping_state = {"last_rtt_ms": 0, "last_ts": 0.0}
    try:
        _orig_run_session = RK.run_session

        def _wrapped_run_session(_args):
            rtt = _ping_state
            return _orig_run_session(_args)
        # no wrappeamos: la RTT la sacamos del ultimo PONG enviado en
        # network.py (donde el hook ya lo cuenta) — dejamos _ping_state
        # como puente por si lo extendemos luego
    except Exception:
        pass

    running = True
    in_lobby = True
    muerto = False
    pausa = False
    _prev_spawned = False   # transicion de muerte (True->False) detectada 1 vez
    last_frame = time.time()

    while running:
        now = time.time()
        dt = min(now - last_frame, 0.1)
        last_frame = now
        engine.step()
        # AUTO-ENTRADA: el keepalive spawnea solo (SPAWNED [20]) — si el
        # mundo ya esta vivo, salir del lobby automaticamente (el usuario
        # veia "conectado" en el lobby sin poder entrar al juego)
        if in_lobby and net.world.spawned and net.world.spawn_pos is not None:
            in_lobby = False
            muerto = False
            print("[AUTO] spawn detectado -> entrando al juego", flush=True)
        # MUERTE: SOLO en la TRANSICION spawned True->False ([25] llega y
        # process_amf3 pone spawned=False). NO por estado continuo: mientras
        # el respawn esta en curso (REAPARECER -> spawn_event -> esperando
        # el [20]) spawned sigue False y el check continuo re-marcaba muerte
        # -> bucle lobby infinito (reproducido: spam [MUERTE] + "me manda
        # otra vez al lobby").
        if (_prev_spawned and not net.world.spawned
                and not in_lobby and not muerto):
            muerto = True
            in_lobby = True
            print("[MUERTE] -> lobby (REAPARECER para spawnear)", flush=True)
            # AUTO-RESPAWN RAPIDO: el respawn se dispara en 0.5s (no 1s)
            # para que la cuenta vuelva al juego sin esperar click. Si
            # AUTORESPAWN esta OFF, mostrar el lobby y esperar click/ENTER.
            try:
                if _C.STATE.autorespawn:
                    import threading as _th
                    def _autospawn():
                        _t_s = time.time()
                        while time.time() - _t_s < 0.5:
                            time.sleep(0.1)
                            if not net.world.connected:
                                break
                            if net.world.spawned:
                                return
                        net_args.spawn_event.set()
                        print("[AUTO-RESPAWN] spawn_event disparado (0.5s)", flush=True)
                    _th.Thread(target=_autospawn, daemon=True).start()
            except Exception:
                pass
        _prev_spawned = bool(net.world.spawned)
        # DETECCION DE MUERTE POR TIMEOUT: si llevamos >6s sin que el CLEAR
        # del server incluya a nuestra entidad (player_entity_id), asumimos
        # muerte silenciosa (sin [25] — el server no avisa). Esto evita que
        # la cuenta se quede "viva" en la GUI sin estarlo.
        if (not in_lobby and not pausa and not muerto
                and net.world.spawned and net.world._t_last_own_seen > 0
                and (now - net.world._t_last_own_seen) > 6.0):
            # detectar por timeout: forzar muerte
            muerto = True
            in_lobby = True
            print("[MUERTE-TIMEOUT] %.1fs sin CLEAR del propio -> lobby" %
                  (now - net.world._t_last_own_seen), flush=True)
            net.world.spawned = False
            net.world.player_entity_id = None
            if _C.STATE.autorespawn:
                import threading as _th
                def _autospawn_t():
                    time.sleep(0.5)
                    net_args.spawn_event.set()
                    print("[AUTO-RESPAWN] timeout -> spawn_event disparado",
                          flush=True)
                _th.Thread(target=_autospawn_t, daemon=True).start()
        # INTEGRACION LOCAL del MOVE (vis): el visor integra el MOVE en el hilo
        # UI para que la camara y la celula visible se muevan hacia donde
        # apunta el mouse en tiempo real. Si el server confirma la posicion
        # via CLEAR/owner, sobreescribe own_x/own_z. Si NO confirma
        # (cuenta fria), al menos la camara local se mueve y el usuario ve
        # respuesta al mouse (no se queda pegado en el spawn).
        #
        # RATE del MOVE: el TCP claro a 60Hz satura el socket y el server
        # corta la sesion a los 40s (reproducido en vivo). El binario real
        # envia ~5.5 MOVEs/s (820 en 150s) — uso 100ms = 10Hz que es
        # suficiente para que el server correlacione la cuenta y no sature.
        if not in_lobby and not pausa and not muerto:
            mx, my = pygame.mouse.get_pos()
            view.update_mouse(mx, my)
            lm = view.last_move
            now2 = time.time()
            if lm["t"] > 0:
                # 1) integrar LOCALMENTE CADA FRAME (dt = tiempo real desde
                # el ultimo frame). Esto mueve own_x/own_z hacia donde
                # apunta el mouse. La camara STUCK (update_camera) usa
                # own_x/own_z prioritariamente -> la celula visible va al
                # nuevo punto. Velocidad acotada para no escapar del mapa.
                view.world.integrate_move(dt, lm["angle"], lm["power"])
                # 2) MOVE TCP claro 10022: el canal real del movimiento.
                # 100ms = 10Hz (igual al binario: ~5.5/s, suficiente).
                if now2 - _last_udp_move[0] >= 0.10:
                    _last_udp_move[0] = now2
                    net.move_tcp(lm["angle"], lm["power"])
                # 3) UDP 3724 REFUERZO: ya no es necesario si el TCP
                # funciona; solo en caso de error. Misma cadencia.
                if now2 - _last_udp_only[0] >= 0.10:
                    _last_udp_only[0] = now2
                    _send_move(lm["angle"], lm["power"], net, view)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                # INPUT BOX de sala (modo SALAS): si esta activo, las teclas
                # van al campo y el evento se CONSUME. ESC sale del edit.
                import client.main as _Ck
                if (in_lobby or pausa or muerto) and _sala_edit["active"]:
                    if ev.key == pygame.K_ESCAPE:
                        _sala_edit["active"] = False
                    elif ev.key == pygame.K_RETURN:
                        args.room = _sala_edit["text"].strip()
                        net_args.room = args.room
                        _sala_edit["active"] = False
                        print("[LOBBY] sala='%s'" % args.room, flush=True)
                    elif ev.key == pygame.K_BACKSPACE:
                        t = _sala_edit["text"]
                        c = _sala_edit["caret"]
                        if c > 0:
                            _sala_edit["text"] = t[:c - 1] + t[c:]
                            _sala_edit["caret"] = c - 1
                    else:
                        ch = ev.unicode
                        if ch and ch.isprintable() and len(_sala_edit["text"]) < 24:
                            t = _sala_edit["text"]
                            c = _sala_edit["caret"]
                            _sala_edit["text"] = t[:c] + ch + t[c:]
                            _sala_edit["caret"] = c + 1
                    continue
                if ev.key == pygame.K_RETURN and (in_lobby or muerto):
                    in_lobby = False
                    muerto = False
                    net_args.spawn_event.set()
                elif ev.key == pygame.K_SPACE and not in_lobby:
                    view.send_split(send=send_game_cmd)
                elif ev.key == pygame.K_w and not in_lobby:
                    view.send_eject(send=send_game_cmd)
                elif ev.key == pygame.K_q:
                    running = False
                elif ev.key == pygame.K_ESCAPE:
                    if not in_lobby:
                        pausa = not pausa
                    in_lobby = True if pausa else in_lobby
            elif ev.type == pygame.MOUSEMOTION and not in_lobby and not pausa:
                # solo ACTUALIZA el angulo/power (last_move): el MOVE lo
                # manda el loop por frame con rate limit (0.18s) — mandar
                # aqui por evento (60+/s) duplicaba el flood que el server
                # corta a los ~40s
                view.update_mouse(ev.pos[0], ev.pos[1])
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                x, y = ev.pos
                if not (in_lobby or pausa or muerto):
                    # click en el mundo: dirige el movimiento (MOVE)
                    view.update_mouse(x, y, send_move=lambda a, p: _send_move(a, p, net, view))
                    continue
                # ---- lobby / pausa / muerto: botones ----
                from client.main import (MODOS, L_MODE_X0, L_MODE_Y, L_MODE_W,
                                         L_MODE_H, L_MODE_STEP, L_SALA,
                                         L_SRV_IZQ, L_SRV_DER, L_JUGAR,
                                         L_AUTORESP, SERVER_LIST)
                import client.main as _C
                clicked = False
                # MODO: SALAS / CTF / FFA / HVZ
                for i, (mname, mval) in enumerate(MODOS):
                    bx = L_MODE_X0 + i * L_MODE_STEP
                    if bx <= x <= bx + L_MODE_W and L_MODE_Y <= y <= L_MODE_Y + L_MODE_H:
                        with _C.STATE.lock:
                            _C.STATE.lobby_mode = mval
                        nuevo = (5 if mval == 0 else mval)
                        if nuevo != net_args.mode:
                            net_args.mode = nuevo
                            _last_sel[0] = (nuevo, net_args.server)
                            # RECONEXION INMEDIATA: el usuario cambio el modo
                            # -> cerrar la sesion actual para que el loop
                            # reconecte con el modo NUEVO (antes solo aplicaba
                            # al clickear JUGAR; la sesion vieja seguia en la
                            # sala anterior = cuenta en 2 salas a la vez)
                            net.force_reconnect()
                            print("[LOBBY] modo=%s (%d) -> reconectando" % (mname, mval), flush=True)
                        else:
                            print("[LOBBY] modo=%s (%d)" % (mname, mval), flush=True)
                        clicked = True
                        break
                if not clicked:
                    # SALA: campo de texto (solo modo SALAS) — entra en modo
                    # edicion para que las teclas escriban el nombre
                    if _C.STATE.lobby_mode == 0:
                        sx0, sy0, sw, sh = L_SALA
                        if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                            _sala_edit["active"] = True
                            clicked = True
                if not clicked:
                    # SERVIDOR: flechas ‹ ›
                    sx0, sy0, sw, sh = L_SRV_IZQ
                    if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                        with _C.STATE.lock:
                            i = SERVER_LIST.index(_C.STATE.lobby_server) if _C.STATE.lobby_server in SERVER_LIST else 0
                            _C.STATE.lobby_server = SERVER_LIST[(i - 1) % len(SERVER_LIST)]
                            nuevo_srv = _C.STATE.lobby_server
                        if nuevo_srv != net_args.server:
                            net_args.server = nuevo_srv
                            _last_sel[0] = (net_args.mode, nuevo_srv)
                            net.force_reconnect()
                            print("[LOBBY] server=%s -> reconectando" % nuevo_srv, flush=True)
                        else:
                            print("[LOBBY] server=%s" % nuevo_srv, flush=True)
                        clicked = True
                    else:
                        sx0, sy0, sw, sh = L_SRV_DER
                        if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                            with _C.STATE.lock:
                                i = SERVER_LIST.index(_C.STATE.lobby_server) if _C.STATE.lobby_server in SERVER_LIST else 0
                                _C.STATE.lobby_server = SERVER_LIST[(i + 1) % len(SERVER_LIST)]
                                nuevo_srv = _C.STATE.lobby_server
                            if nuevo_srv != net_args.server:
                                net_args.server = nuevo_srv
                                _last_sel[0] = (net_args.mode, nuevo_srv)
                                net.force_reconnect()
                                print("[LOBBY] server=%s -> reconectando" % nuevo_srv, flush=True)
                            else:
                                print("[LOBBY] server=%s" % nuevo_srv, flush=True)
                            clicked = True
                if not clicked:
                    # AUTORESPAWN toggle
                    ax, ay, aw, ah = L_AUTORESP
                    if ax <= x <= ax + aw and ay <= y <= ay + ah:
                        with _C.STATE.lock:
                            _C.STATE.autorespawn = not _C.STATE.autorespawn
                        print("[LOBBY] autorespawn=%s" % _C.STATE.autorespawn, flush=True)
                        clicked = True
                if not clicked:
                    # JUGAR / REAPARECER / CONTINUAR
                    jx, jy, jw, jh = L_JUGAR
                    if jx <= x <= jx + jw and jy <= y <= jy + jh:
                        in_lobby = False
                        muerto = False
                        pausa = False
                        net_args.spawn_event.set()
                        # aplicar modo/servidor nuevos: cerrar el socket
                        # para que el loop de sesion reconecte con ellos
                        with _C.STATE.lock:
                            sel = (_C.STATE.lobby_mode, _C.STATE.lobby_server)
                        if sel != _last_sel[0]:
                            _last_sel[0] = sel
                            net.force_reconnect()

        # FPS sample cada 0.5s (no por frame: costoso)
        _fps_state["frames"] += 1
        if now - _fps_state["t0"] >= 0.5:
            _fps_state["fps"] = _fps_state["frames"] / (now - _fps_state["t0"])
            _fps_state["frames"] = 0
            _fps_state["t0"] = now
        fps = _fps_state["fps"] if _fps_state["fps"] > 0 else 60.0
        # estado
        if world.spawned:
            in_lobby = False
        snap = world.snapshot()
        # pings desde el hook del PONG (network.py)
        pings_total = net.stats.get("pong", 0)
        if in_lobby or pausa or muerto:
            estado = "conectado" if world.connected else ("en sala" if world.spawned else "conectando...")
            hud.draw_lobby(screen, font, font_small, font_tiny,
                           estado, args.room, muerto=muerto, pausa=pausa,
                           sala_edit_state=_sala_edit,
                           fps=fps, ping_ms=net.stats.get("last_ping_ms", 0),
                           server=args.server, pings=pings_total)
        else:
            mx, my = pygame.mouse.get_pos()
            view.draw(screen, font_small, font_tiny, mouse=(mx, my))
            hud.draw_hud(screen, font, font_small, snap, view, font_tiny,
                        fps=fps, ping_ms=net.stats.get("last_ping_ms", 0),
                        server=args.server, pings=pings_total)
        pygame.display.flip()
        clock.tick(FPS)

    net.stop()
    stop_event.set()
    pygame.quit()


if __name__ == "__main__":
    main()
