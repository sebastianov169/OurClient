#!/usr/bin/env python3
"""
mito_view.py - Visor/cliente grafico MitosisOG (pygame) para SALA ESPECIFICA.

Conecta a la sala por nombre (default "SUDA GEAR COMP") usando el flujo
login+joinroom de room_keepalive, spawna TCP, y muestra en el mapa:
- El jugador (posicion real del opcode 20)
- TODAS las entidades decodificadas de los frames CLEAR entity_pos,
  agrupadas por firma de campos (cada firma = una entidad), con
  auto-deteccion de los campos de coordenadas (escala 194165 calibrada)
- Mini-mapa, HUD, log, fisica WASD -> MOVE real

Uso:
  python mito_view.py                     # sala "SUDA GEAR COMP"
  python mito_view.py --room "OTRA SALA"
"""
import os, sys, time, json, math, random, threading, queue, argparse, struct, socket

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_PARENT = os.path.dirname(ROOT)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if os.path.join(_PARENT, "mito_client") not in sys.path:
    sys.path.insert(0, os.path.join(_PARENT, "mito_client"))
if os.path.join(_PARENT, "re") not in sys.path:
    sys.path.insert(0, os.path.join(_PARENT, "re"))
import tcp_full as T
import room_keepalive as RK
from full_login_and_api import load_device_id
# ENGINE del binario replicado en Python (client/): clases de entidades,
# fabrica FUN_14073b220, paletas reales, radio, fisica updateMouse.
from client.entities import (CELL_RGB, FOOD_RGB, TEAM_RGB, radio_from_masa,
                             build_entity, entity_color, ET_FOOD, ET_PLAYER,
                             ET_VIRUS, ET_COIN, ET_FLAG_BASE)
from client.engine.update_mouse import updateMouse_core as _updateMouse_core
from client.engine.timing import Timer, Tickable, Defer
from client.engine.animator import Animator2D, AnimatorFunctionLinear
from client.engine.utils import MersenneTwister
from client.engine.core import Engine, Layer2D, Stats
from client.engine.mouse_input_manager import MouseInputManager
from client.engine.sound import SpatialSoundsManager
from client.engine.themes import ThemeManager, MetalWorksMobileTheme
from client.engine.messenger import Messenger
from client.engine.wasd_input import WASDKeyView, WASDView
from client.engine.input_extra import JoystickInputManager, GuildWarManager
from client.world.grid import Grid
from client.world.player import Player
from client.gameplay.opcodes import Opcodes
from client.gameplay.chat import InGameChat
from client.gameplay.leaderboards import Leaderboard, LeaderboardSlot
from client.gameplay.inventory import InventoryCache
from client.gameplay.player_effects import (PlayerEffectBase,
    PlayerEffectAlphaAnimation, PlayerEffectBorderPoisonedAnimation)
from client.gameplay.score_label import ScoreLabel
from client.gameplay.input_chat import GenericInputManager, GamepadButtons
from client.rendering import CircleGraphics, PointSet, BatchedCircleGraphics
from client.resources.files import Reader, ByteArrayWrapper
from client.ui import Button, Popup, ModalPopup, NavigationController
from client.ui.components import Checkbox, LoaderBar
from client.effects import ParticleManager

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

# ============================================================
# CONSTANTES
# ============================================================
# ESCALA = GRID_SIZE del grid espacial (DAT_1421b931c = 194165). Se usa SOLO en
# la ruta del DUMP 19B (decode_dump_19 / feed_particle_list: u32/ESCALA, spec
# re/protocolo_absoluto.md §10). Los eventos CLEAR llevan coords en ESCALA REAL
# (u16/_shortDivisor, mundo 0..16384) — el EntityTracker NO divide por ESCALA
# (ver decode_to_fields en re/haxe_clear_parser.py).
GRID_SIZE = 194165.0
ESCALA = GRID_SIZE         # alias (dump 19B)
DIV = 4.0                  # _shortDivisor calibrado en vivo (DAT_1421b9278=4.0);
                           # default del parser (config 'shortdivisor' del server)
MUNDO_W = 16384.0          # mundo real de MitosisOG (65535/4 = 16383.75)
MUNDO_H = 16384.0
KEY_MASA = 0xFFFF          # clave del campo masa en decode_to_fields (parser)

W, H = 1280, 720
FPS = 60

BG_TOP = (8, 8, 12)          # #08080C — fondo profundo azulado
BG_BOT = (14, 16, 22)       # #0E1016 — gradiente sutil
BG_PANEL = (12, 14, 20, 200) # panel translúcido
ACCENT = (0, 200, 255)      # #00C8FF — cyan neón (primario)
ACCENT2 = (0, 245, 255)     # #00F5FF — cyan brillante
ACCENT3 = (255, 48, 113)    # #FF3071 — magenta (muerte/peligro)
GOLD = (255, 215, 0)        # #FFD700 — amarillo dorado
GREEN = (124, 255, 104)     # #7CFF68 — verde neón (conectado)
TEXT = (255, 255, 255)       # #FFFFFF — texto principal
DIM = (140, 155, 170)       # #8C9BAA — texto secundario
GRID_COLOR = (18, 22, 32)   # grid sutil sobre fondo oscuro
FOOD_COLOR = (80, 200, 255)  # partículas comida: cyan suave
CELL_BORDER = (0, 0, 0)     # borde de célula

# mundo FIJO: los limites reales del mapa de MitosisOG
def world_bounds(snap):
    """Devuelve (w, h) del mundo: limite REAL de MitosisOG (16384)."""
    return MUNDO_W, MUNDO_H

# ============================================================
# DECODIFICADOR DE ENTIDADES (frames CLEAR)
# ============================================================
def decode_entity_frame(payload):
    """Decodifica un frame CLEAR 0x64 -> dict {campo: (tipo, valor)}.

    Formato REAL del Haxe (POR EVENTOS, ver re/protocolo_absoluto.md y
    re/haxe_clear_parser.py): 0x64 + [tipo:byte][campos segun tipo] con
    primitivas u16 BE / i32 BE (readUInt16BE=FUN_140406320 / readInt32BE=
    FUN_140406050), NO el formato fijo de 7 bytes [00 tipo campo valor:u32]
    antiguo (que devolvia 'no parseable' para casi todo).

    Los 45 tipos estan en re/pc_analysis/protocolo_entrante_pc.md §6 (verificado
    en el binario, 0 desyncs sobre 35887 payloads reales). Valores = u16 BE /
    _shortDivisor (SHORT_DIVISOR=4.0 calibrado con Frida, config 'shortdivisor'
    del server) o i32 BE->float (config 'float'). Escalas x10: masa (0x0c) y
    0x0a/0x0b/0x0d/0x0f/0x2e/0x28. Las reglas empiricas viejas (>=1e6 -> /194165,
    (21000,1e5) -> /500, <=21000 directa, id 0xc8) estan REFUTADAS (0 hits).

    Las posiciones se devuelven en ESCALA REAL (mundo 0..16384) para que el
    EntityTracker las use DIRECTAS (no divide por ESCALA; ESCALA=GRID_SIZE queda
    solo para la ruta del dump 19B); la masa va en la clave KEY_MASA (0xFFFF)
    con valor REAL, que feed_entity_frame redondea a entero.
    Devuelve None si no es entity_pos."""
    try:
        from haxe_clear_parser import decode_to_fields
    except Exception:
        return None
    return decode_to_fields(payload)


class EntityTracker:
    """Agrupa frames entity_pos por firma de campos -> entidades estables."""

    def __init__(self):
        self.entities = {}       # firma -> {x, y, color, campos, last, count}
        self.by_field = {}       # campo -> nombre probable (x/y/z/ts)

    @staticmethod
    def firma(fields):
        return tuple(sorted(fields.keys()))

    @staticmethod
    def _find_clock(hist):
        """Identifica el campo 'reloj' (timestamp): el que avanza con delta
        mas regular (menor std relativa del delta por frame)."""
        best, best_score = None, None
        for c, vals in hist.items():
            if len(vals) < 4:
                continue
            deltas = [vals[i+1] - vals[i] for i in range(len(vals) - 1)]
            if not deltas:
                continue
            mean = sum(abs(d) for d in deltas) / len(deltas)
            if mean < 1:
                continue
            var = sum((abs(d) - mean) ** 2 for d in deltas) / len(deltas)
            score = (var ** 0.5) / mean  # coeficiente de variacion del delta
            if best_score is None or score < best_score:
                best, best_score = c, score
        return best

    def update(self, fields):
        """Registra un frame; devuelve (firma, x, y) o None."""
        f = self.firma(fields)
        ent = self.entities.setdefault(f, {
            "x": None, "y": None, "color": None, "campos": f,
            "last": time.time(), "count": 0, "hist": {},
        })
        ent["count"] += 1
        ent["last"] = time.time()
        # historial por campo para detectar coordenadas
        for c, (tipo, val) in fields.items():
            ent["hist"].setdefault(c, []).append(val)
            ent["hist"][c] = ent["hist"][c][-30:]
        if ent["count"] >= 4:
            clock = self._find_clock(ent["hist"])
            # coords = campos que NO son el reloj; x = mayor rango, y = el 2do
            coords = [c for c in ent["hist"] if c != clock]
            if len(coords) >= 2:
                def rng(c):
                    v = ent["hist"][c]
                    return max(v) - min(v)
                coords.sort(key=rng, reverse=True)
                c1, c2 = coords[0], coords[1]
                # usar el ultimo valor (suavizado con los 3 ultimos)
                def smooth(c):
                    v = ent["hist"][c][-3:]
                    return sum(v) / len(v)
                x = smooth(c1)
                y = smooth(c2)
                # coords del parser en ESCALA REAL (u16/_shortDivisor, mundo
                # 0..16384): NO dividir por ESCALA. Solo la ruta dump 19B
                # (u32/GRID_SIZE) llega cruda (>1e6) y se divide aca.
                if abs(x) > 1_000_000:
                    x = x / ESCALA
                if abs(y) > 1_000_000:
                    y = y / ESCALA
                if 0 <= x <= 50000 and 0 <= y <= 50000:
                    ent["x"], ent["y"] = x, y
                    ent["clock"] = clock
                    if ent["color"] is None:
                        rnd = random.Random(hash(f) & 0xFFFF)
                        ent["color"] = (rnd.randint(70, 255), rnd.randint(70, 255), rnd.randint(70, 255))
                    return f, x, y
            # Sala kjajajaja: el CLEAR del jugador trae UN solo campo (0xca,
            # tipo 13) cuyo valor YA esta en escala real (11254 == spawn X
            # 11263), NO crudo. El detector de reloj puede marcarlo como
            # "reloj" por deltas regulares, asi que con una firma de 1 campo
            # se usa el campo directo (sin filtro de reloj). Heuristica de
            # escala por magnitud: >1e6 -> crudo /ESCALA; si no, ya es real.
            if len(ent["hist"]) == 1:
                c = list(ent["hist"].keys())[0]
                v = ent["hist"][c][-1]
                if abs(v) > 1_000_000:
                    x = v / ESCALA
                else:
                    x = v
                y = ent.get("y") or 0.0
                if 0 <= x <= 50000:
                    ent["x"] = x
                    ent["y"] = y
                    ent["clock"] = clock
                    if ent["color"] is None:
                        rnd = random.Random(hash(f) & 0xFFFF)
                        ent["color"] = (rnd.randint(70, 255), rnd.randint(70, 255), rnd.randint(70, 255))
                    return f, x, y
        return None


# ============================================================
# ESTADO COMPARTIDO
# ============================================================
# Servidores reales de la API (consultado 2026-08-13: {"do":"servers"} ->
# data.list). El orden es el del server.
SERVER_LIST = ["auto", "australia", "canada", "west_canada", "central_america",
               "china", "europe", "japan", "middle_east", "russia",
               "south_america", "southeast_asia", "central_us", "east_us",
               "west_us"]
# Modos del juego (gamemode index=1). mode=0 = SALAS (joinroom por nombre,
# campo de sala editable); 4=CTF, 5=FFA, 7=HVZ (modo automatico: el server
# asigna la sala segun el modo; validado en vivo 2026-08-13: CTF -> s18394,
# FFA -> s18394, HVZ -> s18376, todos con m=modo).
MODOS = [("SALAS", 0), ("CTF", 3), ("FFA", 5), ("HVZ", 7)]

# ============================================================
# GEOMETRIA DEL LOBBY (compartida entre draw_lobby y el handler
# de clics — SIEMPRE deben coincidir o los inputs fallan)
# ============================================================
L_MODE_X0 = W // 2 - 210   # x del primer boton de modo
L_MODE_STEP = 110          # separacion entre botones de modo
L_MODE_Y, L_MODE_W, L_MODE_H = 222, 98, 34
L_SALA = (W // 2 - 220, 286, 440, 38)        # campo de sala (SALAS)
L_SRV_IZQ = (W // 2 - 130, 338, 22, 24)      # flecha izquierda servidor
L_SRV_DER = (W // 2 + 108, 338, 22, 24)      # flecha derecha servidor
L_JUGAR = (W // 2 - 130, 380, 260, 52)       # boton JUGAR/Respawn/Continuar
L_AUTORESP = (W // 2 - 130, 462, 260, 34)    # toggle AUTORESPAWN

class MitoState:
    def __init__(self):
        self.lock = threading.Lock()
        self.connected = False
        self.spawned = False
        self.player_id = -1
        self.position = None
        self.target = None
        self.tracker = EntityTracker()
        self.entities_clear = {}   # id -> ClearEntity (entidades reales del parser)
        self._dump_logged = False
        self.particles = {}    # clave -> (x, y) partículas del mapa (food)
        self.mass = 0.0        # masa ACTUAL (campo KEY_MASA del parser CLEAR)
        self._mass_display = 0.0  # masa SUAVIZADA (interpolacion del binario,
                                  # Ghidra +0x158: dVar32 -= (dVar32 - dVar23)/3.0
                                  # cada frame 60fps; self.mass queda intacta)
        self.score = 0.0       # SCORE = masa maxima historica (opcode 51 AMF3)
        self.chat = []
        self.status = "offline"
        self.server = ""
        self.log = []
        self.command_queue = queue.Queue()
        self.fisica = {"vel": 0.0, "ang": 0.0}
        self._player_ent = None
        self.player_entity_id = None
        self.player_cells = set()     # TODAS las celulas del jugador (split)
        self._op19_seen = False       # el server mando op 19 (ids reales)
        self.leaderboard = {}         # entity_id -> nombre (AMF3 op 16)
        self.player_info = {}         # entity_id -> {color, team, lvl...} (op 16)
        self.spawn_pos = None
        self._masa_counts = {}        # eid -> frames de masa vistos (persistente)
        self._hist_pos = {}           # eid -> [(x, z, t)] historial reciente
        self._t_last_clear = 0.0      # timestamp del ultimo CLEAR procesado
                                       # (fixed-timestep de interpolacion del
                                       # binario: alpha = dt_desde_ultimo_CLEAR
                                       # / 16.66ms, FUN_140795df0 linea 553)
        self._ent_prev = {}           # eid -> (x_prev, z_prev, t) pos ANTERIOR (interpolacion)
        # ---- INTEGRACION del engine completo (client/) ----
        self.world = Grid()           # fkengine.game.Grid (el mundo real)
        self.player = Player()        # fkengine.game.Player (contenedor de celulas)
        self.engine = Engine()        # fkengine.core.Engine (main loop)
        self.stats = Stats()          # fkengine.core.Stats (fps)
        self.timer = Timer(0.0)       # fkengine.game.data.Timer
        self.defer = Defer()          # fkengine.game.data.Defer
        self.animator = Animator2D()  # fkengine.animator.Animator2D
        self.mersenne = MersenneTwister()  # fkengine.utils.MersenneTwister (RNG)
        self.mim = MouseInputManager()    # fkengine.game.input.MouseInputManager
        self.messenger = Messenger()      # fkengine.messenger.Messenger
        self.sounds = SpatialSoundsManager()  # fkengine.game.sounds.*
        self.themes = ThemeManager()      # fkengine.sound.theme.ThemeManager
        self.themes.register(MetalWorksMobileTheme())
        self.chat_sys = InGameChat()      # fkengine.game.chat.InGameChat
        self.leaderboard_sys = Leaderboard()  # fkengine.game.leaderboards.Leaderboard
        self.inventory = InventoryCache()     # fkengine.gui.inventory.InventoryCache
        self.particles_sys = ParticleManager()  # fkengine.effects.particles.*
        self.nav = NavigationController()   # fkengine.gui.NavigationController
        self.buttons = {}                   # botones de la UI (Button del binario)
        self.wasd = WASDKeyView()           # fkengine.game.input.WASDKeyView
        self.joystick = JoystickInputManager()
        self.guilds = GuildWarManager()
        self.score_labels = []              # ScoreLabel flotantes
        self.last_move_angle = None   # angulo del ultimo MOVE enviado (rad)
        self.phase = "lobby"          # lobby | game | dead | paused
        self.dead_at = None
        self.mouse = {"angle": 0.0, "power": 0.0, "active": False}
        self.spawn_event = threading.Event()  # Enter en el lobby -> READY diferido
        self.ready_for_spawn = False  # op 53/40 recibido: en sala esperando Enter
        # Seleccion del lobby (editable en la GUI): servidor, modo, sala
        self.lobby_server = "europe"
        self.lobby_mode = 0          # 0=SALAS (joinroom por nombre), 4=CTF, 5=FFA, 7=HVZ
        self.lobby_room = ""         # solo se usa en modo SALAS
        self.lobby_room_edit = False  # campo de texto de sala enfocado
        self.autorespawn = True      # ON por defecto (OurClient): al morir el
                                     # cliente dispara el respawn en 1s;
                                     # el usuario puede desactivarlo desde el
                                     # lobby si prefiere confirmar manual.
        self.session_sel = None       # (server, mode, room) de la sesion ACTIVA

    def set_mouse(self, angle, power):
        with self.lock:
            self.mouse["angle"] = angle
            self.mouse["power"] = power
            self.mouse["active"] = power > 0.05

    def mouse_snapshot(self):
        with self.lock:
            return dict(self.mouse)

    def integrate_dir(self, angle, step):
        """Mueve la posicion local en la direccion del angulo (control mouse)."""
        with self.lock:
            if not self.position:
                return
            p = self.position
            dx = math.cos(angle) * step
            dz = math.sin(angle) * step
            if len(p) > 2:
                self.position = (p[0] + dx, p[1], p[2] + dz)
            else:
                self.position = (p[0] + dx, p[1] + dz)
            self.fisica = {"vel": step / max(0.016, 1.0) * 0.05, "ang": math.degrees(angle)}

    def snapshot(self):
        with self.lock:
            ents = {}
            for f, e in self.tracker.entities.items():
                if e["x"] is not None:
                    ents[f] = {"x": e["x"], "y": e["y"], "color": e["color"],
                               "count": e.get("count", 0),
                               "n_campos": len(e.get("campos", f) if isinstance(e.get("campos", f), (tuple, list)) else f)}
            # entidades REALES del parser (binario): id, x/z, masa, radio
            ents_clear = {}
            for eid, e in self.entities_clear.items():
                if e.x is not None or e.z is not None:
                    ents_clear[eid] = {"x": e.x, "z": e.z, "masa": e.masa,
                                       "radio": e.radio, "type": e.entityType}
                    pv = self._ent_prev.get(eid)
                    if pv is not None:
                        ents_clear[eid]["x_prev"] = pv[0]
                        ents_clear[eid]["z_prev"] = pv[1]
            # MASA SUAVIZADA (binario, Ghidra +0x158: dVar32 = dVar32 -
            # (dVar32 - dVar23) / 3.0 cada frame 60fps): la masa mostrada
            # converge hacia la masa REAL del server (self.mass se mantiene
            # intacta como valor real; se recalcula en cada snapshot = frame).
            if self._mass_display == 0.0 or self.mass <= 0:
                self._mass_display = self.mass
            else:
                self._mass_display += (self.mass - self._mass_display) / 3.0
            return {
                "connected": self.connected, "spawned": self.spawned,
                "player_id": self.player_id, "position": self.position,
                "player_ent_id": self.player_entity_id,
                "player_cells": set(self.player_cells),
                "leaderboard": dict(self.leaderboard),
                "player_info": dict(self.player_info),
                "target": self.target, "entities": ents,
                "entities_clear": ents_clear,
                "particles": dict(self.particles), "mass": self.mass,
                "mass_display": int(round(self._mass_display)),
                "score": self.score,
                "chat": list(self.chat), "status": self.status,
                "server": self.server, "log": list(self.log),
                "fisica": dict(self.fisica),
                "ready_for_spawn": self.ready_for_spawn,
                "lobby_sel": {"mode": self.lobby_mode, "room": self.lobby_room,
                              "server": self.lobby_server,
                              "edit": self.lobby_room_edit,
                              "autorespawn": self.autorespawn},
            }

    def log_msg(self, msg):
        with self.lock:
            self.log.append((time.time(), msg))
            if len(self.log) > 120:
                self.log = self.log[-120:]

    def set_spawn(self, pos, pid):
        # opcode 20 = [x, y, z] floats; y = ALTURA del terreno (1 = nivel base;
        # 702/814/1184/1954 observados), NO es masa (verificado Ghidra 2026-08-13:
        # case 0x14 de FUN_140752e80 no llama a setMassAndRadius). La masa actual
        # llega por CLEAR (KEY_MASA: 0x0c x10 / campo y de 0x08); score por op51.
        with self.lock:
            self.position = tuple(_f(v) for v in pos) if pos else None
            self.player_id = _norm_pid(pid)
            self.spawned = True
            self.spawn_pos = tuple(pos) if pos else None
            self._player_ent = None
            self.player_entity_id = None
            self.player_cells.clear()
            self._op19_seen = False
            self.entities_clear.clear()
            self._ent_prev.clear()
            self._hist_pos.clear()
            self._masa_counts.clear()
            self.particles.clear()
            cam = globals().get("_cam_state")
            if isinstance(cam, dict):
                cam["x"], cam["z"], cam["zoom"] = None, None, None
            # SPAWN MANUAL (2026-08-13): la transicion de fase la decide SOLO
            # la UI (Enter en el lobby). El [20] del server actualiza posicion
            # y marca spawned, pero si el usuario esta en el lobby de muerte o
            # en pausa, NO salta a game solo: espera el Enter del usuario
            # ("en el lobby al presionar el boton que namas spawne").
            self.fisica = {"vel": 0.0, "ang": 0.0}

    def pos2d(self):
        with self.lock:
            if not self.position:
                return None
            p = self.position
            return (p[0], p[2]) if len(p) >= 3 else (p[0], p[1])

    def set_target(self, tx, tz):
        with self.lock:
            self.target = (tx, tz)

    def feed_particle_list(self, entities):
        """Alimenta partículas desde el frame de lista 64 04:
        cada bloque [04 00 08 00 01][id:4][00 01 00 04 00 2c][val:4]
        es UNA particula donde id = coordenada Z y val/ESCALA = X.
        (Validado con logs reales: ids 448-3277, vals 2704-13942, todos
        dentro del mundo 0-21000.)"""
        with self.lock:
            for e in entities:
                z = e.get("id", 0)
                x = e.get("val", 0)
                if abs(x) > 1_000_000:
                    x = x / ESCALA
                if 0 <= x <= MUNDO_W and 0 <= z <= MUNDO_H:
                    self.particles[("L", z)] = (x, z)

    def feed_entity_frame(self, fields):
        msg = None
        with self.lock:
            # CLAVE (2026-08-13, spec re/protocolo_absoluto.md — reglas viejas
            # REFUTADAS: no existe masa = v/500 ni posicion = crudo/194165 en
            # los eventos CLEAR):
            # - MASA ACTUAL: el parser la entrega en KEY_MASA (0xFFFF) con
            #   valor REAL (0x0c masa x10 / campo y de 0x08, u16/divisor).
            # - POSICIONES: coords en ESCALA REAL (u16/_shortDivisor, mundo
            #   0..16384) — el tracker NO divide por ESCALA (solo la ruta del
            #   dump 19B usa ESCALA=GRID_SIZE).
            # - SCORE/masa maxima historica: opcode 51 AMF3 (case 0x33 del
            #   frame_processor 0x140945f80) — nunca por CLEAR.
            masa = None
            crudos = {}
            for c, (t, v) in fields.items():
                if c == KEY_MASA:
                    masa = float(v)
                else:
                    crudos[c] = (t, v)
            if masa is not None:
                # masa actual del jugador (crece al comer, cae al morir).
                # El HUD del juego muestra ENTEROS: redondear.
                self.mass = round(masa)
            if not crudos:
                return None
            # campos de posicion (escala real) -> tracker (divide solo si >1e6)
            res = self.tracker.update(crudos)
            if res:
                f, x, y = res
                # ADOPTAR posicion del jugador si no hay spawn formal (op20):
                # x > 100 ya dividido = posicion real (los campos de masa
                # directa no llegan aqui: van a la rama anterior).
                if self.position is None and x > 100.0 and len(f) == 1:
                    ent = self.tracker.entities.get(f)
                    if ent and ent.get("count", 0) >= 4:
                        self.position = (_f(x), 1.0, _f(y))
                        self.spawned = True
                        self._player_ent = f
                        msg = "posicion adoptada via CLEAR: (%.0f, %.0f)" % (x, y)
                return res
        if msg:
            self.log_msg(msg)
        return None

    def feed_clear_entities(self, ents):
        """Alimenta las entidades REALES decodificadas (ClearEntity por id,
        con x/z/masa/radio como las maneja el binario). Complementa al tracker
        heurístico: aqui cada entidad conserva su id y su masa propia.

        SINCRONIZAR con el jugador REAL (verificado Ghidra 2026-08-13 +
        Frida DIV=4.0 en vivo): el frame 0x08 trae [id][X u16][Z u16][masa u16]
        con coord = u16/4. El jugador es la entidad CON MASA PROPIA que el
        server actualiza con frames 0x08 (la masa baja al splittear, sube al
        comer). Otras entidades grandes (281) tambien tienen masa: la nuestra
        es la que llega en el frame 0x08 del MISMO paquete que el op20 (spawn)
        o la de mayor frecuencia de frames 0x08 recientes."""
        with self.lock:
            now = time.time()
            for eid, e in ents.items():
                old = self.entities_clear.get(eid)
                if old is not None:
                    # INTERPOLACION (2026-08-14, ver re/protocolo_haxe_fisica_
                    # movimiento.md): guardar la posicion ANTERIOR antes de
                    # sobrescribir. El binario interpola igual en
                    # applyPositionInterpolated (FUN_1406790f0): lerp x/z con
                    # alpha -> el visor dibuja pos = prev + (nueva - prev)*a.
                    if old.x is not None and old.z is not None:
                        nx = old.x if e.x is None else e.x
                        nz = old.z if e.z is None else e.z
                        if nx != old.x or nz != old.z:
                            self._ent_prev[eid] = (old.x, old.z, now)
                    # conservar campos que el frame no trae
                    if e.x is None:
                        e.x = old.x
                    if e.z is None:
                        e.z = old.z
                    if e.masa <= 0:
                        e.masa = old.masa
                        e.radio = old.radio
                e._last_seen = now
                self.entities_clear[eid] = e
                # historial de posicion (para correlacion con el mouse)
                if e.x is not None and e.z is not None:
                    h = self._hist_pos.setdefault(eid, [])
                    h.append((e.x, e.z, now))
                    if len(h) > 6:
                        del h[:-6]
            self._t_last_clear = now  # fixed-timestep del binario: el CLEAR
                                       # resetea el acumulador de interpolacion
            # limpieza: quitar entidades que ya no llegan (timeout corto:
            # el server hace culling por frustrum y deja de mandar lo que
            # sale de vista; el binario las elimina al instante con 0x07,
            # asi que el timeout es solo red de seguridad -> 4s, antes 15s
            # dejaba celulas fantasma que "aparecian/desaparecian de la nada")
            stale = [eid for eid, e in self.entities_clear.items()
                     if now - getattr(e, "_last_seen", 0) > 4.0]
            for eid in stale:
                self.entities_clear.pop(eid, None)
                self._hist_pos.pop(eid, None)
                self._ent_prev.pop(eid, None)
            # --- SINCRONIZAR el jugador ---
            # 1) si el server marco el id del jugador (frame 0x19/0x1a), usar ese
            if self.player_entity_id is not None:
                pe = self.entities_clear.get(self.player_entity_id)
                if pe is not None and (pe.x is not None or pe.z is not None):
                    self._sync_player(pe)
                    return
            # Si todavia no llego op19, NO adoptar ninguna entidad por
            # proximidad/frecuencia/mouse. El op20 ya dio la posicion del
            # jugador; los CLEAR iniciales incluyen muchas entidades ajenas y
            # cualquier fallback mueve la camara a jugadores aleatorios.
            # Esperar op19 es exactamente lo que hace el cliente real para
            # conocer las celulas propias.
            if not self._op19_seen:
                return

            # Si el server ya envio op19, NO usar heuristicas para reemplazar
            # player_entity_id por otra entidad ajena. op19 es autoritativo.
            valid_own = [eid for eid in self.player_cells
                         if eid in self.entities_clear
                         and self.entities_clear[eid].x is not None
                         and self.entities_clear[eid].z is not None]
            if valid_own:
                best_own = max(valid_own,
                               key=lambda eid: self.entities_clear[eid].masa)
                self.player_entity_id = best_own
                self._sync_player(self.entities_clear[best_own])
            return

            return

    def _sync_player(self, pe):
        """Aplica la entidad del jugador al estado (posicion + masa + camara).

        Modelo del binario (Ghidra, re/protocolo_haxe_fisica_movimiento.md
        seccion 3.1): la posicion LOGICA es SIEMPRE la del server (CLEAR),
        directa — el cliente NO predice localmente (integrate_dir causaba el
        bug de los circulos: la prediccion peleaba con la correccion del
        server). La suavizacion VISUAL la hace draw_map con _lerp_pos +
        fixed-timestep (alpha = dt_desde_CLEAR / 16.66ms); aqui solo se
        adopta la posicion real del CLEAR (SNAP si salto grande = respawn).
        """
        self._player_ent = pe.id
        if pe.x is not None and pe.z is not None:
            pex, pez = _f(pe.x), _f(pe.z)
            if self.position is None:
                self.position = (pex, 1.0, pez)
            else:
                p = self.position
                px = _f(p[0])
                pz = _f(p[2]) if len(p) > 2 else (_f(p[1]) if len(p) > 1 else 0.0)
                dist_real = math.hypot(pex - px, pez - pz)
                if dist_real > 1500.0:
                    # spawn/respawn o salto de identificacion: SNAP (sin viaje)
                    self.position = (pex, 1.0, pez)
                else:
                    # posicion LOGICA = la REAL del server, SIN lerp: la
                    # suavizacion visual vive en draw_map (_lerp_pos con el
                    # fixed-timestep). Lerpear aqui desfasaba la posicion del
                    # angulo del mouse contra la celula dibujada.
                    self.position = (pex, 1.0, pez)
            self.spawned = True
        if pe.masa > 0:
            # HUD del juego real muestra ENTEROS (el usuario: "wtf no pueden
            # ser decimales") -> redondear
            self.mass = round(pe.masa)

    def integrate_move(self, tx, tz, power, dt):
        with self.lock:
            if not self.position:
                return
            p = self.position
            px = p[0]
            pz = p[2] if len(p) > 2 else (p[1] if len(p) > 1 else 0)
            dx, dz = tx - px, tz - pz
            dist = math.hypot(dx, dz)
            if dist < 1:
                return
            vel = power * 320.0
            step = min(vel * dt, dist)
            nx = px + dx / dist * step
            nz = pz + dz / dist * step
            self.position = (nx, pz, nz) if len(p) > 2 else (nx, nz)
            self.fisica = {"vel": vel, "ang": math.degrees(math.atan2(dz, dx))}


STATE = MitoState()

# ============================================================
# HILO BOT: login + joinroom(sala) + TCP spawn (flujo room_keepalive)
# ============================================================
_pid_holder = {"pid": -1}
_sock_holder = {"sock": None, "host": None}
_udp_holder = {"sock": None, "prefix": None, "seq": 1, "ready": False,
               "sent": 0, "last_angle": 0.0, "last_power": 0.0}

def udp_init(host):
    """Crea el socket UDP + prefix + init packet (formato binario real)."""
    try:
        if _udp_holder["sock"] is None:
            us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            _udp_holder["sock"] = us
            _udp_holder["prefix"] = T.make_udp_prefix()
            _udp_holder["seq"] = 1
            us.sendto(T.make_udp_init_packet(_udp_holder["prefix"]), (host, T.UDP_PORT))
            STATE.log_msg("UDP init -> %s:%d" % (host, T.UDP_PORT))
            print("[UDP] init sent -> %s:%d prefix=%s" % (host, T.UDP_PORT, _udp_holder["prefix"].hex()), flush=True)
            # Hilo de recepcion: prueba de que el canal UDP esta vivo
            def udp_reader():
                us.settimeout(0.5)
                while not _udp_holder.get("stop"):
                    try:
                        data, addr = us.recvfrom(1024)
                        print("[UDP] RECV %d bytes de %s: %s" % (len(data), addr, data.hex()[:60]), flush=True)
                        _udp_holder["recv_count"] = _udp_holder.get("recv_count", 0) + 1
                    except socket.timeout:
                        pass
                    except Exception as e:
                        if not _udp_holder.get("stop"):
                            print("[UDP] recv err: %s" % e, flush=True)
                        break
            threading.Thread(target=udp_reader, daemon=True).start()
        _udp_holder["host"] = host
        return True
    except Exception as e:
        STATE.log_msg("UDP init err: %s" % e)
        print("[UDP] init ERROR: %s" % e, flush=True)
        return False

def udp_move(tx, tz, px, pz, power=None):
    """Envia MOVE UDP con angulo calculado hacia (tx,tz): formato binario real
    (34.0, angle_rad, power). power=None -> 1.0 (compat)."""
    try:
        us = _udp_holder.get("sock")
        host = _udp_holder.get("host")
        if us is None or host is None:
            return False
        dx, dz = tx - px, tz - pz
        dist = math.hypot(dx, dz)
        if dist < 1:
            return False
        angle = math.atan2(dz, dx)   # 0=derecha, -90=arriba, ±180=izq, 90=abajo
        pw = power if power is not None else 1.0
        pkt = bytearray(_udp_holder["prefix"])
        pkt += struct.pack('>I', _udp_holder["seq"])
        _udp_holder["seq"] += 1
        pkt += bytes.fromhex("002726")
        pkt += struct.pack('>f', 34.0)
        pkt += struct.pack('>f', angle)
        pkt += struct.pack('>f', pw)
        pkt += bytes.fromhex("ffffffff00000000")
        us.sendto(bytes(pkt), (host, T.UDP_PORT))
        _udp_holder["sent"] = _udp_holder.get("sent", 0) + 1
        _udp_holder["last_angle"] = angle
        _udp_holder["last_power"] = pw
        return True
    except Exception as e:
        STATE.log_msg("UDP move err: %s" % e)
        return False

def bot_session(stop_event, device, pem, room):
    """Usa RK.run_session (flujo COMPLETO: login->joinroom->invite->
    connect->TCP host del invite->AUTH con invite->spawn) con hooks
    que alimentan el visor."""
    # --- Hooks hacia el visor ---
    # 0) UDP init: TAN PRONTO como se conecta el TCP (antes del greeting/AUTH,
    #    como tcp_full linea 1091). El server solo acepta el UDP init en la
    #    ventana del handshake; si llega despues del AUTH lo ignora.
    orig_create = socket.create_connection
    def hooked_create(address, *a, **k):
        sock = orig_create(address, *a, **k)
        try:
            host = address[0]
            _sock_holder["host"] = host
            with STATE.lock:
                STATE.connected = True
            if not _udp_holder["ready"]:
                _udp_holder["ready"] = udp_init(host)
        except Exception:
            pass
        return sock
    socket.create_connection = hooked_create

    # 1) Frames CLEAR (flag=1, 0x64): posiciones de entidades
    orig_recv = T.recv_frame
    _hook_stats = {"clear": 0, "dump": 0, "last": 0.0, "ents": 0}
    def hooked_recv(sock, timeout=3):
        _sock_holder["sock"] = sock
        try:
            host = sock.getpeername()[0]
            _sock_holder["host"] = host
            if not _udp_holder["ready"]:
                _udp_holder["ready"] = udp_init(host)
        except Exception:
            pass
        res = orig_recv(sock, timeout)
        try:
            if res and res[0] is not None:
                _len, flag, payload = res
                if flag == 1 and payload and payload[0] == 0x64:
                    # DUMP DEL MUNDO = secuencia de eventos CLEAR que EMPIEZA
                    # con el evento 0x04 (case 4 de FUN_14076c400, disasm
                    # 0x14076c86f-0x14076c978). decode_dump_19 maneja TODOS los
                    # subtipos (comida flag=1, celula flag=8/6, posicion 0x24).
                    # Un frame de eventos normales puede contener 0x04 en el
                    # medio, pero SIEMPRE empieza con otro tipo (0x00/0x05...).
                    if len(payload) > 1 and payload[1] == 0x04:
                        try:
                            from haxe_clear_parser import decode_dump_19 as _dd
                            ents, _self = _dd(payload)
                            if ents:
                                STATE.feed_clear_entities(ents)
                                _hook_stats["dump"] += 1
                                _hook_stats["ents"] += len(ents)
                        except Exception:
                            pass
                    else:
                        # parser REAL del binario (FUN_14076c400, DIV=4):
                        # una sola pasada -> entidades + marca de jugador
                        from haxe_clear_parser import decode_clear_full as _dcf
                        ents, pid, dead = _dcf(payload)
                        if ents or dead:
                            if dead:
                                # MUERTE inmediata (evento 0x07 SOLO del
                                # consumidor FUN_140789500: case 7 = quita
                                # del hash set + destroy vtable 0x218; el
                                # 0x09 resetea interpolacion y 0x13 es
                                # removeParticle — no son muerte): las
                                # celulas comidas desaparecen AL INSTANTE,
                                # como en el binario (antes: timeout 15s ->
                                # celulas fantasma).
                                with STATE.lock:
                                    for did in dead:
                                        STATE.entities_clear.pop(did, None)
                                        STATE._hist_pos.pop(did, None)
                                        STATE._ent_prev.pop(did, None)
                                        STATE.player_cells.discard(did)
                            STATE.feed_clear_entities(ents)
                            with STATE.lock:
                                for eid, e in ents.items():
                                    if e.masa > 0:
                                        STATE._masa_counts[eid] = STATE._masa_counts.get(eid, 0) + 1
                            if pid:
                                with STATE.lock:
                                    STATE.player_entity_id = pid
                                print("[JUGADOR] marca 0x19/0x1a: entidad id=%d" % pid, flush=True)
                            _hook_stats["clear"] += 1
                            _hook_stats["ents"] += len(ents)
                            # resumen periodico (1x/5s, no por frame)
                            now5 = time.time()
                            if now5 - _hook_stats["last"] >= 5.0:
                                _hook_stats["last"] = now5
                                print("[STATS] %ds: clear=%d dump=%d entidades=%d" % (
                                    int(now5 - _hook_stats.get("t0", now5)),
                                    _hook_stats["clear"], _hook_stats["dump"],
                                    _hook_stats["ents"]), flush=True)
                        _hook_stats.setdefault("t0", time.time())
        except Exception:
            pass
        return res
    T.recv_frame = hooked_recv

    # 2) AMF3 decodificado: op4 (player id), op20 (spawn pos), op19 (entidades)
    # El Amf3Decoder MINIMO de tcp_full pierde los objetos/arrays asociativos:
    # el op 16 (info de jugador con username/name) se decodificaba como
    # [16, [7, []], ts] perdiendo el dict. Se reemplaza por el decoder
    # COMPLETO (re/amf3_full.py) que soporta objetos, arrays asociativos,
    # vectores y dictionaries (captura real 2026-08-14: username='Pikachu18').
    try:
        from amf3_full import Amf3Decoder as _FullAmf3
        T.Amf3Decoder = _FullAmf3
    except Exception:
        pass
    # Extraccion defensiva de nombres de cuentas desde la estructura AMF3 del
    # op 3 (LOAD): el wire CLEAR no lleva nombres (solo ids u16 opacos); los
    # nombres llegan por AMF3 en _info.name/_info.username (Flash PlayerEntity).
    # Busca recursivamente pares (id numerico, string-nombre) hasta prof 4.
    def _extract_names(node, depth):
        if depth > 4 or node is None:
            return
        if isinstance(node, dict):
            nid = node.get("id")
            if isinstance(nid, (int, float)) and not isinstance(nid, bool):
                nm = node.get("name") or node.get("username")
                if isinstance(nm, str) and nm.strip() and len(nm) < 24:
                    with STATE.lock:
                        STATE.leaderboard[int(nid)] = nm.strip()
            for val in node.values():
                _extract_names(val, depth + 1)
        elif isinstance(node, (list, tuple)):
            # pares [id, "nombre"] / ["nombre", id] en listas planas
            if len(node) == 2:
                a, b = node
                if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, str) and b.strip() and len(b) < 24:
                    with STATE.lock:
                        STATE.leaderboard[int(a)] = b.strip()
                elif isinstance(b, (int, float)) and not isinstance(b, bool) and isinstance(a, str) and a.strip() and len(a) < 24:
                    with STATE.lock:
                        STATE.leaderboard[int(b)] = a.strip()
            for val in node:
                _extract_names(val, depth + 1)
    orig_read = T.Amf3Decoder.read_value
    def hooked_read(self):
        v = orig_read(self)
        try:
            if isinstance(v, list) and v and isinstance(v[0], (int, float)):
                op = int(v[0])
                if op == 4 and len(v) > 1:
                    with STATE.lock:
                        _pid_holder["pid"] = _norm_pid(v[1])
                        STATE.player_id = _norm_pid(v[1])
                    print("[AMF3] op4 player_id=%s" % _norm_pid(v[1]), flush=True)
                elif op == 20 and len(v) > 1:
                    STATE.set_spawn(v[1], _pid_holder["pid"])
                    STATE.status = "EN SALA: " + room
                    STATE.log_msg("SPAWNED pos=%s" % (repr(v[1])[:40]))
                    print("[AMF3] op20 SPAWN pos=%s" % (repr(v[1])[:50]), flush=True)
                    # respawn: el jugador reaparece -> re-identificar entidad
                    with STATE.lock:
                        STATE.player_entity_id = None
                        STATE.ready_for_spawn = True
                elif op == 25 or (op == 16 and isinstance(v, list) and len(v) > 1
                                  and isinstance(v[1], list) and v[1]
                                  and _norm_pid(v[1][0]) == 25):
                    # [25] / [16,[25,[]]] = respawn-ready del binario: el
                    # jugador MURIO. Volver al lobby de muerte INMEDIATO
                    # (el respawn del bot sigue en background; la UI espera
                    # el Enter/Respawn del usuario, igual que el spawn).
                    with STATE.lock:
                        if STATE.phase == "game":
                            STATE.phase = "dead"
                            STATE.dead_at = None
                            STATE.player_entity_id = None
                    STATE.set_mouse(0.0, 0.0)
                    STATE.log_msg("has muerto - ENTER para respawnear")
                    print("[MUERTE] op25 -> lobby de muerte", flush=True)
                elif op in (53, 40):
                    # el server confirmo el handshake: en sala, esperando el
                    # Enter del usuario para el READY (spawn manual)
                    with STATE.lock:
                        STATE.ready_for_spawn = True
                    print("[AMF3] op %d: EN SALA - esperando Enter (spawn manual)" % op, flush=True)
                elif op == 19 and len(v) > 1 and isinstance(v[1], list):
                    # op 19: [19, [[id1, id2...], [flags]], ts] — los ids de
                    # las CELULAS DEL JUGADOR (captura real 2026-08-14:
                    # [351, 352] -> [466, 352] tras split -> [[], [1]] al morir).
                    # Esto ES la identificacion real del jugador (nada de
                    # correlacion heuristica por mouse): el server dice cuales
                    # celulas son tuyas. Se guarda en player_cells.
                    try:
                        cells_raw = v[1][0]
                        if isinstance(cells_raw, list):
                            with STATE.lock:
                                STATE.player_cells = set(int(c) for c in cells_raw if isinstance(c, (int, float)))
                                STATE._op19_seen = True
                                if STATE.player_cells:
                                    if STATE.player_entity_id not in STATE.player_cells:
                                        STATE.player_entity_id = max(STATE.player_cells)
                        STATE.log_msg("op19 celulas: %s" % (repr(cells_raw)[:40]))
                    except Exception:
                        pass
                elif op == 16 and len(v) > 1 and isinstance(v[1], list) and len(v[1]) > 1:
                    # op 16: [16, [entity_id, {info}], ts] — info del jugador
                    # con username/name/color/lvl/team (captura real: id 7 =
                    # 'Pikachu18'). El entity_id es el MISMO id de las
                    # entidades CLEAR: permite dibujar el NOMBRE sobre la
                    # celula y llenar el leaderboard. [16, [25, []]] = muerte
                    # (ya tratada arriba con el [25]).
                    try:
                        eid16 = _norm_pid(v[1][0])
                        info = v[1][1]
                        if isinstance(info, dict):
                            nm = info.get("name") or info.get("username")
                            if isinstance(nm, str) and nm.strip() and len(nm) < 24:
                                with STATE.lock:
                                    STATE.leaderboard[eid16] = nm.strip()
                                print("[NOMBRE] entidad %d = '%s'" % (eid16, nm.strip()), flush=True)
                            # color del jugador (0xRRGGBB del op 16) -> tupla RGB
                            col = info.get("color")
                            if isinstance(col, (int, float)) and col:
                                col = int(col)
                                with STATE.lock:
                                    STATE.player_info[eid16] = {
                                        "color": ((col >> 16) & 0xFF, (col >> 8) & 0xFF, col & 0xFF),
                                        "team": info.get("team", 0),
                                        "lvl": info.get("lvl", 0),
                                    }
                    except Exception:
                        pass
                elif op == 51 and len(v) > 1:
                    # op 51 = SCORE = masa maxima historica (case 0x33 del
                    # frame_processor 0x140945f80, verificado Ghidra 2026-08-13
                    # + confirmado por el usuario: "el score es la masa maxima
                    # que se hubo"). NO baja nunca; sube en rafagas al comer.
                    # El valor llega por AMF3 (IntMap +0x1a0, vtable 0x170/0x168),
                    # NUNCA por CLEAR. La masa ACTUAL viene de los CLEAR via
                    # KEY_MASA (0x0c masa x10 / campo y de 0x08, u16/divisor).
                    try:
                        # factor 25 = calibracion empirica del HUD (no del
                        # protocolo); el binario usa el valor directo
                        STATE.score = float(v[1]) * 25.0
                        print("[SCORE] op51=%.0f -> score %.0f" % (float(v[1]), STATE.score), flush=True)
                    except (TypeError, ValueError):
                        pass
                elif op == 3 and len(v) > 1:
                    # op 3 (LOAD): assets/players — llegan los NOMBRES de las
                    # cuentas (case 3 de FUN_140945f80 -> FUN_1409563a0,
                    # _info.name/_info.username del Flash PlayerEntity.as).
                    # El CLEAR NO lleva nombres (solo ids opacos u16); este es
                    # el unico lugar del wire donde aparecen. Extraccion
                    # defensiva: buscar pares (id numerico, nombre string).
                    try:
                        _extract_names(v[1], 0)
                    except Exception:
                        pass
        except Exception:
            pass
        return v
    T.Amf3Decoder.read_value = hooked_read

    # --- Hilo de comandos UI (MOVE por MOUSE, formato binario) ---
    def ui_commands():
        last_move = 0
        last_move_udp = 0
        last_udp = 0
        # acumulador de tiempo del MOVE (replica del +0x4f8 del binario:
        # crece 0.017 por envio ~17ms, igual que el frame processor 60fps)
        time_accu = 0.0
        while not stop_event.is_set():
            # comandos de botones (SPAWN/QUIT)
            try:
                cmd = STATE.command_queue.get_nowait()
                if cmd == "SPAWN":
                    STATE.log_msg("spawn manual: ya gestionado por run_session")
                elif cmd == "SPLIT":
                    sock = _sock_holder.get("sock")
                    # Split real del binario (validado en vivo con hook 0x96e330):
                    # FUN_14096e330(socket, 1, 0x271a=10010, [0]) -> TCP, sin floats.
                    tcp_ok = False
                    if sock is not None:
                        try:
                            frame = T.make_split_frame()  # [len][len][0x40][10010]
                            T.send_frame(sock, frame, log_it=False, label="SPLIT")
                            tcp_ok = True
                        except Exception as e:
                            STATE.log_msg("SPLIT err: %s" % e)
                    STATE.log_msg("SPLIT enviado (10010 TCP:%s)" % tcp_ok)
                    print("[SPLIT] tcp=%s op=10010" % tcp_ok, flush=True)
                elif cmd == "QUIT":
                    return
            except queue.Empty:
                pass
            now = time.time()
            # MOVE continuo: SOLO en fase game (en pausa/lobby el jugador
            # queda quieto; la sesion sigue viva con los PONGs del keepalive).
            # EVIDENCIA DE LA CAPTURA REAL DEL BINARIO (instant_capture.log):
            # post-spawn el binario NO envia MOVE por TCP (solo PONGs de
            # 51 bytes cada ~2s). El MOVE va por UDP 3724 (formato del
            # visor viejo que funcionaba: prefix+seq+002726+[34.0, angulo,
            # power]+ffffffff00000000). Se manda SOLO el MOVE UDP con el
            # angulo/power reales del mouse — el MOVE TCP queda como
            # refuerzo cada 17ms (no estorba) pero el canal real es UDP.
            m = STATE.mouse_snapshot()
            if STATE.phase == "game" and m["active"] and now - last_move > 0.017:
                sock = _sock_holder.get("sock")
                if sock is not None:
                    try:
                        time_accu += 0.017
                        frame = T.make_move_frame(time_accu, m["angle"], m["power"])
                        T.send_frame(sock, frame, log_it=False, label="MOVE-UI")
                        with STATE.lock:
                            STATE.last_move_angle = m["angle"]
                        last_move = now
                        # target visual: punto en la direccion del mouse
                        pos2d = STATE.pos2d()
                        if pos2d:
                            STATE.set_target(pos2d[0] + math.cos(m["angle"]) * 300,
                                             pos2d[1] + math.sin(m["angle"]) * 300)
                    except Exception as e:
                        STATE.log_msg("MOVE send err: %s" % e)
                # UDP move de refuerzo (misma direccion, formato binario real):
                # el canal REAL del movimiento es UDP 3724 (la captura del
                # binario muestra que por TCP solo van PONGs). Se envia a
                # ~100ms con el power real del mouse, no a 17ms con 1.0 fijo.
                pos2d = STATE.pos2d()
                if pos2d and now - last_move_udp > 0.1:
                    udp_move(pos2d[0] + math.cos(m["angle"]) * 300,
                             pos2d[1] + math.sin(m["angle"]) * 300,
                             pos2d[0], pos2d[1], power=m["power"])
                    last_move_udp = now
            # keepalive UDP AFK cada 1s: el visor VIEJO mandaba un MOVE
            # UDP por segundo con el ANGULO ACTUAL del mouse (no un angulo
            # fijo — el angulo fijo -3.084/0.9309 EMPUJABA al jugador en
            # una direccion constante cada 1s y mataba el control). Con
            # mouse activo el MOVE-UDP de arriba ya cubre; este keepalive
            # solo mantiene la sesion viva con el ULTIMO angulo del mouse.
            if STATE.phase == "game" and _udp_holder["ready"] and now - last_udp > 1.0:
                try:
                    us = _udp_holder["sock"]
                    host = _udp_holder["host"]
                    if us and host:
                        ms = STATE.mouse_snapshot()
                        pkt = bytearray(_udp_holder["prefix"])
                        pkt += struct.pack('>I', _udp_holder["seq"])
                        _udp_holder["seq"] += 1
                        pkt += bytes.fromhex("002726")
                        pkt += struct.pack('>f', 34.0)
                        pkt += struct.pack('>f', ms["angle"] if ms["active"] else 0.0)
                        pkt += struct.pack('>f', ms["power"] if ms["active"] else 0.0)
                        pkt += bytes.fromhex("ffffffff00000000")
                        us.sendto(bytes(pkt), (host, T.UDP_PORT))
                        last_udp = now
                except Exception:
                    pass
            time.sleep(0.02)
    threading.Thread(target=ui_commands, daemon=True).start()

    # --- Loop de sesion con reintento ---
    attempt = 0
    while not stop_event.is_set():
        attempt += 1
        # leer la seleccion ACTUAL del lobby (servidor/modo/sala): si el
        # usuario cambio algo en la GUI, la proxima sesion usa lo nuevo
        with STATE.lock:
            cur_server = STATE.lobby_server
            cur_mode = STATE.lobby_mode
            # modo SALAS (0): joinroom por nombre escrito. CTF/FFA/HVZ:
            # sala vacia -> el server asigna la sala del modo (AUTO)
            if cur_mode == 0:
                cur_room = STATE.lobby_room.strip()
            else:
                cur_room = ""
            STATE.session_sel = (cur_server, cur_mode, cur_room)
        STATE.log_msg("sesion %d: login+joinroom (server=%s mode=%d sala=%s)..." % (
            attempt, cur_server, cur_mode, cur_room))
        try:
            # Watchdog de spawn: si no hay SPAWNED en 90s, abortar el socket
            # para que run_session retorne y reintentemos (sala llena/espera).
            # Con spawn manual (Enter en el lobby) el watchdog NO se arma
            # hasta que el usuario dispara el evento: quedarse "en sala"
            # esperando Enter no debe matar la conexion. Y el jugador se
            # considera "spawneado" TAMBIEN si ya fue identificado por
            # correlacion (la sala kjajajaja no manda [20] nunca).
            watchdog = {"armed": False}
            def spawn_watchdog():
                deadline = None
                while not stop_event.is_set():
                    time.sleep(5)
                    if STATE.spawned or STATE._player_ent is not None:
                        return
                    if not STATE.spawn_event.is_set():
                        continue  # aun en lobby esperando Enter: sin deadline
                    if deadline is None:
                        deadline = time.time() + 90
                    if time.time() > deadline:
                        STATE.log_msg("sin spawn en 90s - reiniciando sesion")
                        sock = _sock_holder.get("sock")
                        if sock is not None:
                            try:
                                sock.close()
                            except Exception:
                                pass
                        return
            threading.Thread(target=spawn_watchdog, daemon=True).start()
            args = argparse.Namespace(
                device=device, pem=pem, accounts=0, exclude="", room=cur_room,
                code="", duration=86400, spawn_wait=90, quiet=True,
                verbose=False, noreconnect=True,
                spawn_event=STATE.spawn_event,
                autorespawn=STATE.autorespawn,
                server=cur_server,
                # modo SALAS (0): el gamemode HTTP usa 5 (FFA, el validado con
                # respawn); CTF/FFA/HVZ: el modo real que asigna la sala.
                mode=(5 if cur_mode == 0 else cur_mode),
            )
            total = RK.run_session(args)
            STATE.log_msg("sesion termino (%.0fs viva)" % total)
            # SIEMPRE reintentar: el usuario puede estar en pausa (lobby con
            # sesion viva) o queriendo seguir jugando. El loop termina solo
            # con stop_event (cierre de la app). Con spawn manual, una sesion
            # que muere en pausa debe reconectarse sola.
            STATE.status = "reconectando..."
            STATE.log_msg("reintentando sesion")
            # limpiar socket muerto para que SPLIT/MOVE no vayan a un fd cerrado
            with STATE.lock:
                _sock_holder["sock"] = None
                STATE.connected = False
                STATE.ready_for_spawn = False
            time.sleep(4)
        except Exception as e:
            STATE.status = "error, reintentando..."
            STATE.log_msg("bot error: %s" % e)
            time.sleep(3)


# ============================================================
# UI
# ============================================================
_text_cache = {}
def render_cached(font, text, antialias, color):
    """font.render con caché LRU simple: renderizar texto cada frame es
    carísimo en pygame (crea superficie + blit interno)."""
    key = (id(font), text, color)
    s = _text_cache.get(key)
    if s is None:
        s = font.render(text, antialias, color)
        if len(_text_cache) > 600:
            _text_cache.clear()
        _text_cache[key] = s
    return s


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


_gradient_cache = None  # Surface cacheada del gradiente (el fondo no cambia)


def draw_gradient(surf):
    """Fondo del binario: oscuro plano con grid del mundo (GameBg/GameBorders).
    El visor tenia gradiente neon + estrellas; el juego real (fkengine.game.bg
    .GameBg) usa fondo oscuro solido con grid de celdas sutil."""
    global _gradient_cache
    theme = STATE.themes.get() if STATE.themes.get() else None
    bg = theme.color("bg") if theme else (18, 20, 28)
    if _gradient_cache is None or _gradient_cache.get_size() != surf.get_size():
        _gradient_cache = pygame.Surface(surf.get_size())
        _gradient_cache.fill(bg)
        # grid del mundo (GameGrid): lineas cada 512 unidades de mundo,
        # alpha bajo — visible al hacer zoom out como en el juego real
        cam_x = _f(_cam_state["x"]) if _cam_state["x"] is not None else 0.0
        cam_z = _f(_cam_state["z"]) if _cam_state["z"] is not None else 0.0
        zoom = _f(_cam_state["zoom"]) or 0.05
        w, h = surf.get_size()
        step_world = 512.0
        step_px = max(2, int(step_world * zoom))
        grid_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        # origen de la camara en pantalla = centro
        ox = w / 2 - (cam_x * zoom)
        oz = h / 2 - (cam_z * zoom)
        first_x = int((0 - ox) // step_px) * step_px
        for gx in range(first_x, w + step_px, step_px):
            pygame.draw.line(grid_surf, (40, 44, 56, 70), (gx, 0), (gx, h))
        first_z = int((0 - oz) // step_px) * step_px
        for gz in range(first_z, h + step_px, step_px):
            pygame.draw.line(grid_surf, (40, 44, 56, 70), (0, gz), (w, gz))
        _gradient_cache.blit(grid_surf, (0, 0))
    surf.blit(_gradient_cache, (0, 0))


def world_to_screen(wx, wy, cam_x, cam_y, zoom=0.05):
    """Proyeccion robusta mundo -> pantalla.

    Los CLEAR pueden traer una entidad parcialmente actualizada durante un
    frame. Nunca permitir None/NaN en pygame: se descarta como punto invalido
    en vez de tumbar todo el visor.
    """
    vals = (wx, wy, cam_x, cam_y, zoom)
    if any(v is None for v in vals):
        return (-100000, -100000)
    try:
        vals = tuple(float(v) for v in vals)
    except (TypeError, ValueError):
        return (-100000, -100000)
    if not all(math.isfinite(v) for v in vals) or vals[4] <= 0:
        return (-100000, -100000)
    wx, wy, cam_x, cam_y, zoom = vals
    return (W // 2 + int((wx - cam_x) * zoom),
            H // 2 + int((wy - cam_y) * zoom))


def draw_hud(surf, snap, font, font_small):
    """HUD estilo agar.io moderno: barra superior translúcida, leaderboard lateral."""
    # --- Barra superior translúcida ---
    bar_hud = pygame.Surface((W, 50), pygame.SRCALPHA)
    bar_hud.fill((8, 10, 16, 220))
    surf.blit(bar_hud, (0, 0))
    pygame.draw.line(surf, ACCENT, (0, 49), (W, 49), 1)

    # Logo MITOSIS
    logo = render_cached(font, "MITOSIS", True, TEXT)
    surf.blit(logo, (18, 6))
    ox = 18 + font.size("MITOSI")[0] + 4
    pygame.draw.circle(surf, ACCENT2, (ox, 22), 6)

    # Estado de conexion (derecha de la barra)
    status_color = GREEN if snap["spawned"] else (GOLD if snap["connected"] else DIM)
    stxt = "EN SALA" if snap["spawned"] else ("CONECTANDO" if snap["connected"] else "OFFLINE")
    s = render_cached(font_small, stxt, True, status_color)
    surf.blit(s, (W - 170, 14))
    if snap["server"]:
        s2 = render_cached(font_small, snap["server"], True, DIM)
        surf.blit(s2, (W - 330, 16))

    # Info del jugador (centro-izquierda)
    pos = snap["position"]
    pos_txt = "-"
    if isinstance(pos, (list, tuple)) and len(pos) > 2:
        pos_txt = "(%.0f, %.0f)" % (pos[0], pos[2])
    elif isinstance(pos, (list, tuple)) and len(pos) > 1:
        pos_txt = "(%.0f, %.0f)" % (pos[0], pos[1])
    n_ent = len(snap.get("entities_clear", {}))
    info = "ID: %s  ent: %d" % (_norm_pid(snap["player_id"]), n_ent)
    i = render_cached(font_small, info, True, DIM)
    surf.blit(i, (150, 16))

    # MASA GRANDE y SCORE (debajo de la barra, fuera del minimapa).
    # MASA usa la masa SUAVIZADA (interpolacion del binario +0x158) si el
    # snapshot la trae; si no, la masa real.
    masa_val = int(snap.get("mass_display", snap.get("mass", 0)))
    masa_lbl = render_cached(font, "MASA: %d" % masa_val, True, TEXT)
    score_lbl = render_cached(font_small, "SCORE: %d" % int(snap.get("score", 0)), True, DIM)
    surf.blit(masa_lbl, (210, 52))
    surf.blit(score_lbl, (210, 76))

    # --- Leaderboard lateral (arriba-derecha, sin pisar LOG/CHAT) ---
    # En CTF (mode 3) NO hay leaderboard (el usuario lo confirmo: el binario
    # no lo muestra en CTF). Los nombres reales de cuentas llegan por AMF3
    # op3 (LOAD); si aun no llegaron, se muestran los top por masa con nombre
    # si lo hay, o sin nombre.
    sel_mode = snap.get("lobby_sel", {}).get("mode", 0)
    lb_names = snap.get("leaderboard", {})
    if sel_mode != 3:
        lb_panel = pygame.Surface((300, 200), pygame.SRCALPHA)
        lb_panel.fill((10, 12, 18, 180))
        pygame.draw.rect(lb_panel, (0, 200, 255, 80), lb_panel.get_rect(), 1, border_radius=6)
        surf.blit(lb_panel, (W - 330, 54))

        lb_title = render_cached(font_small, "LEADERBOARD", True, ACCENT)
        surf.blit(lb_title, (W - 322, 60))
        # Top jugadores por masa (entities_clear con masa > 0)
        # OJO: el ">" del jugador se compara contra player_ent_id (entity id del
        # CLEAR, marca 0x19/0x1a o correlacion) — player_id (op4 AMF3) es el id de
        # sesion y NO coincide con los entity ids del leaderboard.
        me_ent = snap.get("player_ent_id") or _norm_pid(snap["player_id"])
        players = []
        for eid, ec in snap.get("entities_clear", {}).items():
            masa = ec.get("masa", 0.0)
            if masa > 0:
                players.append((masa, eid))
        players.sort(reverse=True)
        y_lb = 82
        for rank, (masa_e, eid) in enumerate(players[:8], 1):
            is_me = (eid == me_ent)
            c = ACCENT2 if is_me else (TEXT if rank <= 3 else DIM)
            prefix = ">" if is_me else " "
            nombre = lb_names.get(eid)
            if nombre:
                txt = render_cached(font_small, "%s%d. %s  %.0f" % (prefix, rank, nombre, masa_e), True, c)
            else:
                txt = render_cached(font_small, "%s%d. %.0f" % (prefix, rank, masa_e), True, c)
            surf.blit(txt, (W - 322, y_lb))
            y_lb += 18

    # --- Barra inferior ---
    bar_inf = pygame.Surface((W, 54), pygame.SRCALPHA)
    bar_inf.fill((8, 10, 16, 220))
    surf.blit(bar_inf, (0, H - 54))
    pygame.draw.line(surf, ACCENT, (0, H - 54), (W, H - 54), 1)

    mx, my = pygame.mouse.get_pos()
    bx, by, bw, bh = 20, H - 44, 150, 36
    over = bx <= mx <= bx + bw and by <= my <= by + bh
    pygame.draw.rect(surf, ACCENT2 if over else (20, 50, 60), (bx, by, bw, bh), border_radius=8)
    btxt = render_cached(font_small, "PAUSA  (ESC)", True, TEXT)
    surf.blit(btxt, (bx + 28, by + 9))

    qx, qy, qw, qh = W - 130, H - 44, 110, 36
    pygame.draw.rect(surf, (40, 20, 30), (qx, qy, qw, qh), border_radius=8)
    qtxt = render_cached(font_small, "[Q] SALIR", True, ACCENT3)
    surf.blit(qtxt, (qx + 20, qy + 9))

    h1 = render_cached(font_small, "MOUSE: mover   [SPACE] split   [ESC] pausa   [Q] salir", True, DIM)
    surf.blit(h1, (190, H - 32))


# estado de camara suavizada (renderer del binario: lerp 0.125, zoom /10)
_cam_state = {"x": None, "z": None, "zoom": None}
_last_frame_t = None      # para dt de interpolacion (alpha = min(1, dt*8))
_mm_last_t = None         # idem para el minimapa (timer propio de draw_minimap)


def _lerp_pos(c, alpha):
    """Posicion interpolada (x, z) de una entidad del snapshot entre frames
    CLEAR (el binario interpola igual, applyPositionInterpolated FUN_1406790f0):
    pos = prev + (nueva - prev) * alpha. Sin prev -> posicion directa."""
    x, z = c.get("x"), c.get("z")
    if x is None or z is None:
        return None, None
    if alpha < 1.0 and c.get("x_prev") is not None and c.get("z_prev") is not None:
        xp, zp = c["x_prev"], c["z_prev"]
        if xp is not None and zp is not None:
            return (xp + (x - xp) * alpha,
                    zp + (z - zp) * alpha)
    return x, z

# zoom fit-to-size REAL del binario (Ghidra: re/renderer_y_camara.md y
# re/_decomp_140795df0_full.txt):
#   sizePx = radio_world * scale_actual        (si sizePx <= 0 -> sizePx = 100)
#   t = clamp((sizePx - minSize)/(maxSize - minSize), 0, 1)   [min 100, max 300]
#   scale = (minSize*H)/(W*sizePx) * (1 - factor*(1-t))       [W=1280, H=720, factor 0.5]
#   clamp final 0.02..1.5
def _fit_zoom(radio_world, zoom_actual):
    size_px = radio_world * (zoom_actual if zoom_actual is not None else 1.0)
    if size_px <= 0:
        size_px = 100.0
    t = max(0.0, min(1.0, (size_px - 100.0) / 200.0))
    scale = (100.0 * 720.0) / (1280.0 * size_px) * (1.0 - 0.5 * (1.0 - t))
    return max(0.02, min(1.5, scale))

# Cache GLOBAL de surfaces por radio: los radios en pantalla son discretos
# (int(r_w * zoom)) y los colores salen de la paleta fija, asi que hay pocas
# claves unicas. Antes se creaban 2 surfaces SRCALPHA por celula y 1 por
# particula CADA frame -> lag severo con 200+ celulas a 60fps.
_glow_cache = {}  # (radio, color) -> Surface SRCALPHA con el glow
_fill_cache = {}  # (radio, color) -> Surface SRCALPHA con el relleno semi


def draw_map(surf, snap, font_small, font_tiny):
    """Mundo estilo agar.io moderno: fondo oscuro, grid neón, células con glow."""
    # INTERPOLACION de posiciones: replica EXACTA del binario
    # (FUN_140795df0 linea 553: FUN_1407959e0(param_1, dVar23 / 16.6667) con
    # fixed-timestep de 16.66ms — alpha = tiempo desde el ultimo CLEAR /
    # 16.66ms, en [0,1). El CLEAR resetea el acumulador (STATE._t_last_clear);
    # con red >= render alpha llega rapido a 1 -> posicion directa (la
    # fluidez real viene de la cadencia de CLEAR, no de un lerp fuerte).
    global _last_frame_t
    now_t = time.time()
    dt = now_t - _last_frame_t if _last_frame_t else 0.0
    _last_frame_t = now_t
    t_clear = getattr(STATE, "_t_last_clear", 0.0)
    if t_clear > 0.0:
        # alpha = dt_desde_ultimo_CLEAR / tick_red(16.66ms), clamp [0,1]
        alpha = max(0.0, min(1.0, (now_t - t_clear) / 0.0166667))
    else:
        # sin CLEAR aun (offline/lobby): caer al lerp por frame como antes
        alpha = min(1.0, dt * 8.0)
    pos = snap["position"]
    target_x = _f(pos[0]) if isinstance(pos, (list, tuple)) and len(pos) > 0 and pos[0] is not None else 0.0
    target_z = (_f(pos[2]) if isinstance(pos, (list, tuple)) and len(pos) > 2 and pos[2] is not None
                else (_f(pos[1]) if isinstance(pos, (list, tuple)) and len(pos) > 1 and pos[1] is not None else 0.0))
    mw, mh = world_bounds(snap)
    # zoom fit-to-size REAL del binario
    masa_j = snap.get("mass", 0) or 50.0
    radio_j = math.floor(math.sqrt(masa_j) * 10.0 + 0.5) + 1 or 40.0
    cs = _cam_state
    # fit-to-size con la escala ACTUAL (sizePx = radio*zoom_actual), como el
    # binario; la escala objetivo se suaviza /10 por frame (lerp 0.10)
    zoom_target = _fit_zoom(radio_j, cs["zoom"])
    if cs["x"] is None:
        cs["x"], cs["z"], cs["zoom"] = target_x, target_z, zoom_target
    else:
        cam_jump = math.hypot(target_x - cs["x"], target_z - cs["z"])
        if cam_jump > 1500.0:
            # spawn/respawn o cambio de sala: snap, nunca arrastrar la camara
            # por miles de unidades (causa de la camara erratica).
            cs["x"], cs["z"] = target_x, target_z
        else:
            cs["x"] += (target_x - cs["x"]) * 0.125
            cs["z"] += (target_z - cs["z"]) * 0.125
        cs["zoom"] += (zoom_target - cs["zoom"]) * 0.10
    cam_x, cam_y, zoom = cs["x"], cs["z"], cs["zoom"]

    # LIMITES DEL MAPA: borde neón cyan
    mx0, my0 = world_to_screen(0, 0, cam_x, cam_y, zoom)
    mx1, my1 = world_to_screen(mw, mh, cam_x, cam_y, zoom)
    bx, by = min(mx0, mx1), min(my0, my1)
    bw2, bh2 = abs(mx1 - mx0), abs(my1 - my0)
    pygame.draw.rect(surf, (0, 120, 180, 60), (bx, by, bw2, bh2), 2)
    pygame.draw.rect(surf, ACCENT, (bx, by, bw2, bh2), 1)

    # Grid sutil
    step = 500
    if mw > 15000:
        step = 2000
    elif mw > 9000:
        step = 1000
    for gx in range(0, int(mw) + 1, step):
        sx, _ = world_to_screen(gx, 0, cam_x, cam_y, zoom)
        if 0 <= sx <= W:
            pygame.draw.line(surf, GRID_COLOR, (sx, 0), (sx, H), 1)
    for gy in range(0, int(mh) + 1, step):
        _, sy = world_to_screen(0, gy, cam_x, cam_y, zoom)
        if 0 <= sy <= H:
            pygame.draw.line(surf, GRID_COLOR, (0, sy), (W, sy), 1)

    # PARTICULAS del mapa (food): circulitos con la paleta de comida REAL.
    # SIN glow por particula: con miles de partículas visibles, un blit
    # SRCALPHA 12x12 por particula + circle era el lag principal a 60fps.
    for px_, py_ in snap.get("particles", {}).values():
        sx, sy = world_to_screen(px_, py_, cam_x, cam_y, zoom)
        if -10 <= sx <= W + 10 and -10 <= sy <= H + 10:
            fc = FOOD_PALETA[(int(px_ * 31 + py_) % len(FOOD_PALETA))]
            pygame.draw.circle(surf, fc, (sx, sy), 3)

    # ENTIDADES CLASIFICADAS (n_campos <= 1 = particula, >= 2 = celula)
    # Clasificacion VERIFICADA contra el binario (0 desyncs) -> NO tocar.
    for f, e in snap["entities"].items():
        if e.get("x") is None or e.get("y") is None:
            continue
        sx, sy = world_to_screen(e["x"], e["y"], cam_x, cam_y, zoom)
        if -30 <= sx <= W + 30 and -30 <= sy <= H + 30:
            n_c = e.get("n_campos", 1)
            if n_c <= 1:
                color = (80, 180, 220)
                pygame.draw.circle(surf, color, (sx, sy), 2)
            else:
                color = e["color"] or FOOD_COLOR
                pygame.draw.circle(surf, color, (sx, sy), 7)
                pygame.draw.circle(surf, CELL_BORDER, (sx, sy), 7, 1)

    # ENTIDADES REALES del parser (binario): z-order por masa, culling por
    # frustrum, glow/relleno CACHEADOS por (radio, color)
    fr_x0 = cam_x - (W / zoom) / 2.0 - 10
    fr_z0 = cam_y - (H / zoom) / 2.0 - 10
    fr_w = W / zoom + 20
    fr_h = H / zoom + 20
    ec_list = []
    player_cells = snap.get("player_cells") or set()
    lb_names16 = snap.get("leaderboard") or {}
    pinfo_map = snap.get("player_info") or {}
    me_ent = snap.get("player_ent_id")
    if me_ent is not None:
        player_cells = player_cells | {me_ent}
    for eid, ec in snap.get("entities_clear", {}).items():
        ex, ez = _lerp_pos(ec, alpha)
        if ex is None or ez is None:
            continue
        if eid in player_cells:
            continue  # las celulas del jugador se dibujan en la seccion JUGADOR
        if not (fr_x0 <= ex <= fr_x0 + fr_w and fr_z0 <= ez <= fr_z0 + fr_h):
            continue
        ec_list.append((ec.get("masa", 0.0), eid, ec, ex, ez))
    ec_list.sort(key=lambda t: t[0])
    for _, eid, ec, ex, ez in ec_list:
        sx, sy = world_to_screen(ex, ez, cam_x, cam_y, zoom)
        masa_e = ec.get("masa", 0.0)
        etype = ec.get("type") or 0
        if ec.get("radio"):
            r_w = ec["radio"]
        elif masa_e > 0:
            r_w = math.floor(math.sqrt(masa_e) * 10.0 + 0.5) + 1
        else:
            r_w = 2
        r_px = max(int(r_w * zoom), 2)
        if etype == 4:
            # VIRUS (entityType 4, fabrica FUN_14073b220): verde con pinchos,
            # como el juego real. Radio grande, masa ~100+.
            pygame.draw.circle(surf, (40, 180, 80), (sx, sy), max(r_px, 8))
            n_sp = 12
            for k in range(n_sp):
                a_ = k * (2 * math.pi / n_sp)
                x1 = sx + math.cos(a_) * r_px * 0.8
                y1 = sy + math.sin(a_) * r_px * 0.8
                x2 = sx + math.cos(a_) * (r_px + max(3, r_px // 4))
                y2 = sy + math.sin(a_) * (r_px + max(3, r_px // 4))
                pygame.draw.line(surf, (30, 140, 60), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(surf, (80, 220, 120), (sx, sy), max(r_px, 8), 2)
            continue
        if etype == 5:
            # MONEDA (entityType 5 = CoinEntity): dorada brillante
            pygame.draw.circle(surf, (255, 200, 40), (sx, sy), max(r_px, 5))
            pygame.draw.circle(surf, (255, 240, 160), (sx, sy), max(r_px, 5), 1)
            continue
        if masa_e <= 0:
            # comida: circulito con la paleta de comida REAL del binario
            # (colores brillantes: magenta, verde lima, naranja, cyan...) —
            # el gris azulado era invisible sobre el fondo oscuro.
            fc = FOOD_PALETA[(eid * 7 + 3) % len(FOOD_PALETA)]
            pygame.draw.circle(surf, fc, (sx, sy), 3)
        else:
            # celula: color REAL de la cuenta si llego por op 16 (player_info),
            # si no la paleta del binario por id.
            pinfo = pinfo_map.get(eid)
            if pinfo and pinfo.get("color"):
                color = pinfo["color"]
            else:
                color = paleta_color(eid)
            if r_px > 14:
                glow_r = r_px + 6
                key = (glow_r, color)
                glow_surf = _glow_cache.get(key)
                if glow_surf is None:
                    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (color[0], color[1], color[2], 35), (glow_r, glow_r), glow_r)
                    _glow_cache[key] = glow_surf
                surf.blit(glow_surf, (sx - glow_r, sy - glow_r))
            if r_px > 8:
                # relleno semitransparente (surface cacheada por (radio, color))
                key = (r_px, color)
                inner = _fill_cache.get(key)
                if inner is None:
                    inner = pygame.Surface((r_px * 2, r_px * 2), pygame.SRCALPHA)
                    pygame.draw.circle(inner, (color[0], color[1], color[2], 180), (r_px, r_px), r_px)
                    _fill_cache[key] = inner
                surf.blit(inner, (sx - r_px, sy - r_px))
            else:
                # celula pequena: circulo solido directo (sin surface)
                pygame.draw.circle(surf, color, (sx, sy), r_px)
            # borde luminoso
            border_c = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
            pygame.draw.circle(surf, border_c, (sx, sy), r_px, 1)
            # nombre: el NOMBRE REAL de la cuenta si llego por AMF3 op 16
            # (captura real: 'Pikachu18'), si no el id limpio. Con sombra.
            if r_px >= 10:
                nm = lb_names16.get(eid)
                label = nm if nm else str(eid)
                lbl = render_cached(font_small, label, True, TEXT)
                shd = render_cached(font_small, label, True, (0, 0, 0))
                surf.blit(shd, (sx - r_px + 1, sy - r_px - 11))
                surf.blit(lbl, (sx - r_px, sy - r_px - 12))

    # JUGADOR: dibuja TODAS las celulas del jugador (split: cada parte con su
    # posicion y radio REALES del parser, no la masa global del snapshot que
    # se queda desincronizada al dividirse).
    if isinstance(pos, (list, tuple)) or player_cells:
        pz = pos[2] if isinstance(pos, (list, tuple)) and len(pos) > 2 and pos[2] is not None else (pos[1] if isinstance(pos, (list, tuple)) and len(pos) > 1 and pos[1] is not None else 0)
        px, py = world_to_screen(pos[0] if isinstance(pos, (list, tuple)) and pos[0] is not None else 0, pz, cam_x, cam_y, zoom)
        # lista de celulas del jugador: (eid, entidad) reales si estan, si no
        # la posicion global (eid None). Los eids son ints (ClearEntity.id).
        my_cells = []
        for cid in sorted(player_cells):
            ce = snap.get("entities_clear", {}).get(cid)
            if ce is not None and ce.get("x") is not None and ce.get("z") is not None:
                my_cells.append((cid, ce))
        if not my_cells and isinstance(pos, (list, tuple)):
            # celula unica de respaldo: usa la masa SUAVIZADA del snapshot
            my_cells = [(None, {"x": pos[0], "z": pz,
                         "masa": snap.get("mass_display", snap.get("mass", 0)) or 50.0})]
        # la camara sigue a la celula principal (mayor masa)
        if my_cells:
            main_c = max(my_cells, key=lambda t: t[1].get("masa", 0))
            mx_, mz_ = _lerp_pos(main_c[1], alpha)
            if mx_ is not None and mz_ is not None:
                px, py = world_to_screen(mx_, mz_, cam_x, cam_y, zoom)
        # color REAL de cuenta (op 16 -> STATE.player_info[eid]['color'] 0xRRGGBB
        # ya convertido a tupla RGB) de la celula principal (mayor masa), igual
        # que el binario pinta la celula del jugador con su color de cuenta.
        # Fallback cyan (0,180,230) si el op 16 no llego aun.
        pcolor = (0, 180, 230)
        if my_cells:
            main_eid = main_c[0]
            if main_eid is not None:
                pinfo = pinfo_map.get(main_eid)
                if pinfo is None and isinstance(main_eid, int):
                    pinfo = pinfo_map.get(str(main_eid))
                if pinfo and pinfo.get("color"):
                    pcolor = pinfo["color"]
        for ci, (cid, c) in enumerate(my_cells):
            if (c is main_c if my_cells else True) and isinstance(pos, (list, tuple)):
                # la celula PRINCIPAL se dibuja en la posicion del snapshot
                # (STATE.position = prediccion local del mouse + correccion
                # suave del server lerp 0.25). Si se dibujara desde la entidad
                # CLEAR cruda, la celula se quedaria atras de la camara y no
                # responderia al mouse (el bug del usuario).
                cx_ = pos[0] if pos[0] is not None else 0.0
                cz_ = (pos[2] if len(pos) > 2 and pos[2] is not None
                       else (pos[1] if len(pos) > 1 and pos[1] is not None else 0.0))
            else:
                cx_, cz_ = _lerp_pos(c, alpha)
            if cx_ is None or cz_ is None:
                continue
            cx, cy = world_to_screen(cx_, cz_, cam_x, cam_y, zoom)
            masa_c = c.get("masa", 0) or 50.0
            # la celula PRINCIPAL (mayor masa) usa la masa SUAVIZADA del
            # snapshot (interpolacion del binario +0x158): su radio no salta
            # de tamano al comer/splittear. Las celdas del split conservan
            # su masa REAL del parser.
            if (c is main_c if my_cells else True):
                masa_c = snap.get("mass_display", masa_c) or masa_c
            r_c = math.floor(math.sqrt(masa_c) * 10.0 + 0.5) + 1
            # minimo 12px SOLO visual (radio del jugador en pantalla): NO
            # altera el zoom ni la proyeccion del resto de entidades
            r_px_c = max(int(r_c * zoom), 12)
            # glow grande del jugador (cacheado por radio, color REAL de cuenta)
            glow_r = r_px_c + 12
            key = (glow_r, pcolor)
            glow_surf = _glow_cache.get(key)
            if glow_surf is None:
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (pcolor[0], pcolor[1], pcolor[2], 30), (glow_r, glow_r), glow_r)
                _glow_cache[key] = glow_surf
            surf.blit(glow_surf, (cx - glow_r, cy - glow_r))
            # relleno semitransparente del color de cuenta (cacheado por radio)
            key = (r_px_c, pcolor)
            inner = _fill_cache.get(key)
            if inner is None:
                inner = pygame.Surface((r_px_c * 2, r_px_c * 2), pygame.SRCALPHA)
                pygame.draw.circle(inner, (pcolor[0], pcolor[1], pcolor[2], 190), (r_px_c, r_px_c), r_px_c)
                _fill_cache[key] = inner
            surf.blit(inner, (cx - r_px_c, cy - r_px_c))
            # borde blanco brillante (se mantiene: el binario usa blanco/negro
            # segun contraste; aqui siempre blanco)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r_px_c, 2)
            # nucleo blanco (se mantiene)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(3, r_px_c // 5))
            # linea de direccion solo en la celula principal
            if ci == 0 or c is main_c if my_cells else False:
                ang = math.radians(snap["fisica"].get("ang", 0))
                dx, dy = math.cos(ang) * (r_px_c + 14), math.sin(ang) * (r_px_c + 14)
                pygame.draw.line(surf, ACCENT2, (cx, cy), (cx + dx, cy + dy), 2)
            # etiqueta: solo en la celula principal (masa_c ya es mass_display
            # suavizada cuando existe)
            if (c is main_c if my_cells else True):
                lbl = render_cached(font_small, "YO - MASA: %d" % int(masa_c), True, TEXT)
                shd = render_cached(font_small, "YO - MASA: %d" % int(masa_c), True, (0, 0, 0))
                surf.blit(shd, (cx + r_px_c + 7, cy - r_px_c - 5))
                surf.blit(lbl, (cx + r_px_c + 6, cy - r_px_c - 6))
        if snap["target"]:
            tx, ty = world_to_screen(snap["target"][0], snap["target"][1], cam_x, cam_y, zoom)
            pygame.draw.circle(surf, ACCENT2, (tx, ty), 5, 2)


FOOD_COLOR = (80, 200, 255)  # partículas comida: cyan suave

# paleta REAL de células del binario (Ghidra 2026-08-14, .rdata 0x141d167c0,
# 8 colores u32 LE, copiada por FUN_1405928a0; seleccion _id % len).
# Fuente unica: re/mito_engine.py CELL_RGB (misma tabla).
_PALETA = CELL_RGB
# paleta de comida del binario (.rdata 0x141d16860, 7 colores, FUN_14066fa50).
# Fuente unica: re/mito_engine.py FOOD_RGB (misma tabla).
FOOD_PALETA = FOOD_RGB
_paleta_cache = {}
def paleta_color(eid):
    """Color estable por id de entidad (hash -> paleta)."""
    c = _paleta_cache.get(eid)
    if c is None:
        c = _PALETA[eid % len(_PALETA)]
        _paleta_cache[eid] = c
    return c


def _f(v, d=0.0):
    """Coercion numerica segura: frames corruptos del parser pueden traer
    strings (p.ej. posicion como '1234.5') que contaminan _cam_state y
    revientan la aritmetica del mouse (crash 'can only concatenate str').
    Nunca devuelve un string."""
    if v is None:
        return d
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _norm_pid(v):
    """Normaliza el player id: si viene una lista anidada (p.ej. [id, extra]),
    extrae el primer elemento numerico. Nunca devuelve una lista."""
    for _ in range(4):
        if isinstance(v, (list, tuple)):
            v = v[0] if v else 0
        else:
            break
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def draw_minimap(surf, snap):
    """Minimapa estilo neón: fondo oscuro, borde cyan, puntos luminosos."""
    # INTERPOLACION igual que draw_map (alpha = min(1.0, dt*8.0), timer propio):
    # los CLEAR llegan a rafagas y las posiciones crudas hacen temblar el
    # minimapa. Se interpola SOLO celulas (masa > 0) y el jugador; las
    # particulas/comida quedan crudas (son muchas y pequenas).
    global _mm_last_t
    now_t = time.time()
    dt = now_t - _mm_last_t if _mm_last_t else 0.0
    _mm_last_t = now_t
    alpha = min(1.0, dt * 8.0)
    mm_w, mm_h = 180, 180
    mm_x, mm_y = 12, 56
    mw, mh = world_bounds(snap)
    # fondo translúcido con borde cyan
    mm_s = pygame.Surface((mm_w + 8, mm_h + 8), pygame.SRCALPHA)
    mm_s.fill((10, 12, 18, 200))
    pygame.draw.rect(mm_s, (0, 200, 255, 80), mm_s.get_rect(), 1, border_radius=4)
    surf.blit(mm_s, (mm_x - 4, mm_y - 4))
    pygame.draw.rect(surf, (14, 18, 24), (mm_x, mm_y, mm_w, mm_h))
    pos = snap["position"]
    px = pos[0] if isinstance(pos, (list, tuple)) else 0
    pz = pos[2] if isinstance(pos, (list, tuple)) and len(pos) > 2 else (pos[1] if isinstance(pos, (list, tuple)) and len(pos) > 1 else 0)
    # particulas: puntos diminutos cyan (crudas, sin interpolacion)
    for pxx, pyy in snap.get("particles", {}).values():
        sx = mm_x + int(pxx / mw * mm_w)
        sy = mm_y + int(pyy / mh * mm_h)
        if mm_x <= sx <= mm_x + mm_w and mm_y <= sy <= mm_y + mm_h:
            pygame.draw.circle(surf, (60, 160, 200), (sx, sy), 1)
    # entidades REALES del parser: celulas = punto de 2px, comida = 1px.
    # Solo celulas (masa > 0) y el jugador se interpolan; comida cruda.
    me_ent = snap.get("player_ent_id")
    for eid, ec in snap.get("entities_clear", {}).items():
        if ec.get("masa", 0) > 0 or eid == me_ent:
            ex, ez = _lerp_pos(ec, alpha)
        else:
            ex, ez = ec.get("x"), ec.get("z")
        if ex is None or ez is None:
            continue
        sx = mm_x + int(ex / mw * mm_w)
        sy = mm_y + int(ez / mh * mm_h)
        if mm_x <= sx <= mm_x + mm_w and mm_y <= sy <= mm_y + mm_h:
            if ec.get("masa", 0) > 0:
                pygame.draw.circle(surf, ACCENT, (sx, sy), 2)
            else:
                pygame.draw.circle(surf, (60, 100, 120), (sx, sy), 1)
    # jugador: punto blanco con borde cyan. Interpola con x_prev/z_prev de su
    # entidad en entities_clear si existe; si no, posicion global cruda.
    if me_ent is not None:
        pec = snap.get("entities_clear", {}).get(me_ent)
        if pec is not None and pec.get("x") is not None:
            px, pz = _lerp_pos(pec, alpha)
    sx = mm_x + int(px / mw * mm_w)
    sy = mm_y + int(pz / mh * mm_h)
    if mm_x <= sx <= mm_x + mm_w and mm_y <= sy <= mm_y + mm_h:
        pygame.draw.circle(surf, (255, 255, 255), (sx, sy), 4)
        pygame.draw.circle(surf, ACCENT2, (sx, sy), 4, 1)


def draw_panel(surf, snap, font_small, font_tiny):
    """Panel LOG/CHAT estilo neón: fondo translúcido, bordes cyan."""
    panel_w = 300
    px = W - 330
    py = 264
    panel_h = (H - 60) - py
    panel_s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_s.fill((10, 12, 18, 180))
    pygame.draw.rect(panel_s, (0, 200, 255, 60), panel_s.get_rect(), 1, border_radius=6)
    surf.blit(panel_s, (px, py))

    title = render_cached(font_small, "LOG / CHAT", True, ACCENT)
    surf.blit(title, (px + 12, py + 8))
    y = py + 36
    for ts, msg in snap["log"][-16:]:
        t = render_cached(font_tiny, msg[:44], True, DIM)
        surf.blit(t, (px + 12, y))
        y += 16
    y += 6
    for sender, msg in snap["chat"][-6:]:
        t = render_cached(font_tiny, "%s: %s" % (sender, msg[:38]), True, ACCENT2)
        surf.blit(t, (px + 12, y))
        y += 15


def draw_lobby(surf, snap, room, font, font_small, font_tiny, muerto=False, pausa=False):
    """Lobby estilo neón moderno: fondo oscuro profundo, logo MITOSIS con glow,
    botones glassmorphism, partículas flotantes neón."""
    # fondo: gradiente oscuro profundo azulado
    for y in range(H):
        t = y / H
        r = int(8 + 6 * t)
        g = int(8 + 8 * t)
        b = int(14 + 8 * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (W, y))

    # partículas flotantes neón (cyan, magenta, amarillo)
    for _ in range(60):
        px = random.uniform(0, W)
        py = random.uniform(0, H)
        c = random.choice([(0, 200, 255), (255, 48, 113), (255, 215, 0), (124, 255, 104)])
        alpha = random.randint(15, 40)
        ps = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(ps, (c[0], c[1], c[2], alpha), (4, 4), 4)
        surf.blit(ps, (int(px), int(py)))
    # puntos pequeños estáticos
    for _ in range(40):
        px = random.randint(0, W)
        py = random.randint(0, H)
        c = random.choice([(0, 200, 255), (255, 48, 113)])
        pygame.draw.circle(surf, c, (px, py), 1)

    # barra superior translúcida
    bar_sup = pygame.Surface((W, 56), pygame.SRCALPHA)
    bar_sup.fill((10, 12, 18, 230))
    surf.blit(bar_sup, (0, 0))
    pygame.draw.line(surf, ACCENT, (0, 55), (W, 55), 1)

    # botones superiores (glassmorphism)
    top_btns = ["RANGOS", "LOGROS", "AMIGOS", "BATTLE PASS"]
    bx = W - 30
    for b in reversed(top_btns):
        lbl = render_cached(font_tiny, b, True, DIM)
        bw = lbl.get_width() + 16
        bx -= bw
        btn_s = pygame.Surface((bw - 8, 32), pygame.SRCALPHA)
        btn_s.fill((20, 24, 32, 180))
        pygame.draw.rect(btn_s, (0, 200, 255, 60), btn_s.get_rect(), 1, border_radius=6)
        surf.blit(btn_s, (bx, 12))
        surf.blit(lbl, (bx + 4, 20))
        bx -= 8

    # --- Logo MITOSIS con glow ---
    logo_text = "MITOSIS"
    logo = render_cached(font, logo_text, True, TEXT)
    lx = W // 2 - logo.get_width() // 2
    surf.blit(logo, (lx, 100))
    # O roja (célula mitosis)
    ox = lx + font.size("MIT")[0] + font.size("O")[0] // 2
    oy = 100 + font.size(logo_text)[1] // 2
    r = font.size("O")[1] // 2 - 2
    # glow exterior de la O
    glow_os = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
    pygame.draw.circle(glow_os, (255, 48, 113, 40), (r * 2, r * 2), r * 2)
    surf.blit(glow_os, (ox - r * 2, oy - r * 2))
    # rectangulo oscuro tapando la O original
    pygame.draw.rect(surf, (10, 12, 18), (ox - r - 1, oy - r - 1, r * 2 + 3, r * 2 + 3))
    # circulo rojo de la O
    pygame.draw.circle(surf, ACCENT3, (ox, oy), r)
    # punto blanco (nucleo)
    pygame.draw.circle(surf, (255, 255, 255), (ox, oy), max(2, r // 3))

    # --- Estado central ---
    if muerto:
        st = render_cached(font_small, "HAS MUERTO", True, ACCENT3)
        surf.blit(st, (W // 2 - st.get_width() // 2, 170))
    elif pausa:
        st = render_cached(font_small, "PAUSA - SESION VIVA, Enter para seguir", True, GOLD)
        surf.blit(st, (W // 2 - st.get_width() // 2, 170))
    else:
        st = render_cached(font_small, "MASA MAXIMA HISTORICA: %d" % int(snap.get("score", 0)), True, DIM)
        surf.blit(st, (W // 2 - st.get_width() // 2, 170))

    # ===== SELECTORES DEL LOBBY =====
    sel = snap.get("lobby_sel", {})
    sel_mode = sel.get("mode", 0)
    sel_room = sel.get("room", room)
    sel_server = sel.get("server", "europe")
    sel_edit = sel.get("edit", False)
    es_salas = (sel_mode == 0)

    # MODO: botones SALAS / CTF / FFA / HVZ
    mode_lbl = render_cached(font_tiny, "MODO", True, ACCENT)
    surf.blit(mode_lbl, (W // 2 - 260, 208))
    for i, (mname, mval) in enumerate(MODOS):
        active = (mval == sel_mode)
        bx = L_MODE_X0 + i * L_MODE_STEP
        if active:
            # botón activo: cyan neón
            btn_s = pygame.Surface((L_MODE_W, L_MODE_H), pygame.SRCALPHA)
            btn_s.fill((0, 200, 255, 200))
            pygame.draw.rect(btn_s, (0, 245, 255, 255), btn_s.get_rect(), 2, border_radius=8)
            surf.blit(btn_s, (bx, L_MODE_Y))
        else:
            btn_s = pygame.Surface((L_MODE_W, L_MODE_H), pygame.SRCALPHA)
            btn_s.fill((16, 20, 28, 200))
            pygame.draw.rect(btn_s, (40, 50, 60, 150), btn_s.get_rect(), 1, border_radius=8)
            surf.blit(btn_s, (bx, L_MODE_Y))
        col = TEXT if active else DIM
        tl = render_cached(font_small, mname, True, col)
        surf.blit(tl, (bx + L_MODE_W // 2 - tl.get_width() // 2, L_MODE_Y + 8))

    if es_salas:
        sala_lbl = render_cached(font_tiny, "SALA (escribe el nombre y Enter)", True, ACCENT)
        surf.blit(sala_lbl, (W // 2 - sala_lbl.get_width() // 2, 264))
        sbox = L_SALA
        if sel_edit:
            pygame.draw.rect(surf, (20, 30, 40), sbox, border_radius=8)
            pygame.draw.rect(surf, ACCENT2, sbox, 2, border_radius=8)
        else:
            pygame.draw.rect(surf, (16, 20, 28), sbox, border_radius=8)
            pygame.draw.rect(surf, (40, 50, 60), sbox, 1, border_radius=8)
        room_disp = sel_room if sel_room.strip() else "..."
        room_col = TEXT if sel_room.strip() else DIM
        stxt = render_cached(font_small, room_disp + ("|" if sel_edit else ""), True, room_col)
        surf.blit(stxt, (sbox[0] + 10, sbox[1] + 9))

    # SERVIDOR
    srv_lbl = render_cached(font_tiny, "SERVIDOR", True, ACCENT)
    surf.blit(srv_lbl, (W // 2 - 200, 320))
    sname = sel_server.replace("_", " ").upper()
    st2 = render_cached(font_small, sname, True, TEXT)
    surf.blit(st2, (W // 2 - st2.get_width() // 2, 318))
    ix0, iy0, iw, ih = L_SRV_IZQ
    pygame.draw.polygon(surf, ACCENT, [(ix0 + iw, iy0 + ih // 2), (ix0 + iw - 10, iy0), (ix0 + iw - 10, iy0 + ih)])
    ix0, iy0, iw, ih = L_SRV_DER
    pygame.draw.polygon(surf, ACCENT, [(ix0, iy0 + ih // 2), (ix0 + 10, iy0), (ix0 + 10, iy0 + ih)])

    # --- Botón JUGAR grande (glassmorphism neón) ---
    btn_txt = "Continuar  »" if pausa else ("Respawn  »" if muerto else "JUGAR  »")
    eb = render_cached(font, btn_txt, True, TEXT)
    jx, jy, jw, jh = L_JUGAR
    # glow del botón
    glow_btn = pygame.Surface((jw + 20, jh + 20), pygame.SRCALPHA)
    pygame.draw.rect(glow_btn, (0, 200, 255, 25), (10, 10, jw, jh), border_radius=12)
    surf.blit(glow_btn, (jx - 10, jy - 10))
    # botón principal
    btn_s = pygame.Surface((jw, jh), pygame.SRCALPHA)
    btn_s.fill((0, 150, 200, 180))
    pygame.draw.rect(btn_s, ACCENT2, btn_s.get_rect(), 2, border_radius=10)
    surf.blit(btn_s, (jx, jy))
    surf.blit(eb, (jx + jw // 2 - eb.get_width() // 2, jy + jh // 2 - eb.get_height() // 2))

    # 'Invita a un amigo' (debajo del toggle AUTORESPAWN, fuera de su area)
    inv = render_cached(font_small, "Invite a friend", True, DIM)
    surf.blit(inv, (W // 2 - inv.get_width() // 2, 506))

    # --- AUTORESPAWN toggle (glassmorphism) ---
    ar_on = sel.get("autorespawn", False)
    ax, ay, aw, ah = L_AUTORESP
    ar_s = pygame.Surface((aw, ah), pygame.SRCALPHA)
    if ar_on:
        ar_s.fill((0, 200, 255, 180))
        pygame.draw.rect(ar_s, ACCENT2, ar_s.get_rect(), 2, border_radius=8)
    else:
        ar_s.fill((20, 24, 32, 180))
        pygame.draw.rect(ar_s, (40, 50, 60), ar_s.get_rect(), 1, border_radius=8)
    surf.blit(ar_s, (ax, ay))
    ar_txt = render_cached(font_small, "AUTORESPAWN: %s" % ("ON" if ar_on else "OFF"), True, TEXT)
    surf.blit(ar_txt, (ax + aw // 2 - ar_txt.get_width() // 2, ay + 7))

    # --- Botones inferiores EVO/EQUIP/POW/GEM (glassmorphism) ---
    bottom_btns = ["EVO", "EQUIP", "POW", "GEM"]
    total_w = 0
    sizes = {}
    for b in bottom_btns:
        lbl = render_cached(font_tiny, b, True, DIM)
        sizes[b] = lbl
        total_w += lbl.get_width() + 24
    x0 = W // 2 - total_w // 2
    y0 = H - 70
    for b in bottom_btns:
        lbl = sizes[b]
        btn_s = pygame.Surface((lbl.get_width() + 24, 36), pygame.SRCALPHA)
        btn_s.fill((16, 20, 28, 180))
        pygame.draw.rect(btn_s, (40, 50, 60, 100), btn_s.get_rect(), 1, border_radius=8)
        surf.blit(btn_s, (x0, y0))
        surf.blit(lbl, (x0 + 12, y0 + 9))
        x0 += lbl.get_width() + 24 + 12

    # estado de conexion
    if snap["ready_for_spawn"]:
        st2 = render_cached(font_tiny, "EN SALA - pulsa ENTER para spawnear", True, GREEN)
    elif snap["connected"]:
        st2 = render_cached(font_tiny, "CONECTADO - handshake en curso...", True, GOLD)
    else:
        st2 = render_cached(font_tiny, "CONECTANDO...", True, GOLD)
    surf.blit(st2, (W // 2 - st2.get_width() // 2, H - 30))

    if pausa:
        hint_txt = "ENTER o clic para continuar    Q para salir"
    elif muerto:
        hint_txt = "ENTER o clic para respawnear    Q para salir"
    elif es_salas:
        hint_txt = "clic en modo/sala/servidor    ENTER para jugar    Q para salir"
    else:
        hint_txt = "clic en modo/servidor    ENTER para jugar    Q para salir"
    hint = render_cached(font_tiny, hint_txt, True, DIM)
    surf.blit(hint, (W // 2 - hint.get_width() // 2, H - 14))


def run_ui(device, pem, room):
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    mode_name = next((n for n, m in MODOS if m == STATE.lobby_mode), "SALAS")
    cap = "MitosisOG - %s" % (room if room.strip() else ("AUTO %s" % mode_name))
    pygame.display.set_caption(cap)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 24)
    font_tiny = pygame.font.Font(None, 18)

    stars = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.5, 1.5), random.randint(50, 150))
             for _ in range(80)]
    # Pre-render de las estrellas: se dibujan UNA vez al iniciar en una
    # Surface transparente y luego se blitea entera (1 blit por frame en
    # vez de 80 pygame.draw.circle).
    star_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for x, y, r, a in stars:
        pygame.draw.circle(star_layer, (a, a, a, 255), (int(x), int(y)), int(r))

    stop_event = threading.Event()
    bot = None
    bot_started = False

    def start_bot():
        nonlocal bot, bot_started
        if bot_started:
            return
        bot_started = True
        bot = threading.Thread(target=bot_session, args=(stop_event, device, pem, room), daemon=True)
        bot.start()

    # LOGIN + CONEXION AL INICIAR LA APP (no al unirse a la sala): el bot hace
    # login HTTP + joinroom + TCP + AUTH y queda "en sala" esperando el Enter
    # (READY diferido -> spawn manual). El lobby muestra el estado real.
    start_bot()

    def _reconnect_sesion():
        # Cerrar el socket actual: run_session retorna con EOF y bot_session
        # reintenta con la seleccion NUEVA del lobby (server/modo/sala).
        sock = _sock_holder.get("sock")
        if sock is not None:
            try:
                sock.close()
                STATE.log_msg("sesion reiniciada: aplicando seleccion nueva del lobby")
                print("[LOBBY] reconectando a la seleccion nueva...", flush=True)
            except Exception:
                pass

    def _aplicar_seleccion():
        # Si el usuario cambio servidor/modo/sala en el lobby, reiniciar la
        # sesion para que bot_session reconecte con la seleccion nueva.
        with STATE.lock:
            cur = (STATE.lobby_server, STATE.lobby_mode,
                   STATE.lobby_room.strip())  # vacio = AUTO (sala del modo)
            active = STATE.session_sel
        if active is not None and cur != active:
            _reconnect_sesion()

    running = True
    last_frame = time.time()
    in_lobby = True
    while running:
        now = time.time()
        dt = min(now - last_frame, 0.1)
        last_frame = now

        # ---- ENGINE del binario: tick de los sistemas (client/) ----
        STATE.stats.frame(dt)
        STATE.timer.tick(dt)
        STATE.defer.tick(dt)
        STATE.animator.tick(dt)
        STATE.chat_sys.visible = True
        for sl in list(STATE.score_labels):
            sl.tick(dt)
            if not sl.visible:
                STATE.score_labels.remove(sl)
        if STATE.phase == "game":
            STATE.player.mass = STATE.mass
            STATE.world.view = STATE

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if STATE.lobby_room_edit and in_lobby:
                    # escribir el nombre de la sala en el campo de texto
                    # (PRIMERO: la q debe ir al campo, no cerrar la app)
                    if ev.key == pygame.K_BACKSPACE:
                        with STATE.lock:
                            STATE.lobby_room = STATE.lobby_room[:-1]
                    elif ev.key == pygame.K_RETURN:
                        with STATE.lock:
                            STATE.lobby_room_edit = False
                        # Enter en el campo = jugar en esa sala
                        STATE.phase = "game"
                        STATE.dead_at = None
                        in_lobby = False
                        STATE.spawn_event.set()
                        _aplicar_seleccion()
                    elif ev.key == pygame.K_ESCAPE:
                        with STATE.lock:
                            STATE.lobby_room_edit = False
                    elif ev.unicode and ev.unicode.isprintable():
                        with STATE.lock:
                            if len(STATE.lobby_room) < 32:
                                STATE.lobby_room += ev.unicode
                elif ev.key == pygame.K_q:
                    running = False
                elif ev.key == pygame.K_RETURN and (in_lobby or STATE.phase == "dead"):
                    # lobby -> jugar: SOLO disparar el spawn (READY diferido).
                    # El login/joinroom/TCP ya se hicieron al iniciar la app.
                    with STATE.lock:
                        STATE.lobby_room_edit = False
                    STATE.phase = "game"
                    STATE.dead_at = None
                    in_lobby = False
                    STATE.spawn_event.set()
                    _aplicar_seleccion()
                elif ev.key == pygame.K_ESCAPE and not in_lobby:
                    # PAUSA: volver al lobby sin matar la sesion TCP
                    STATE.phase = "paused"
                    STATE.set_mouse(0.0, 0.0)
                    in_lobby = True
                    STATE.log_msg("pausa - volviste al lobby (Enter para seguir)")
                    print("[PAUSA] ESC -> lobby (sesion viva)", flush=True)
                elif ev.key == pygame.K_s:
                    STATE.command_queue.put("SPAWN")
                elif ev.key == pygame.K_SPACE:
                    STATE.command_queue.put("SPLIT")
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                x, y = ev.pos
                if in_lobby or STATE.phase == "dead":
                    # ---- botones del lobby: modo / sala / servidor / jugar ----
                    # (geometria = constantes L_* compartidas con draw_lobby)
                    clicked = False
                    # MODO: SALAS / CTF / FFA / HVZ
                    for i, (mname, mval) in enumerate(MODOS):
                        bx = L_MODE_X0 + i * L_MODE_STEP
                        if bx <= x <= bx + L_MODE_W and L_MODE_Y <= y <= L_MODE_Y + L_MODE_H:
                            with STATE.lock:
                                STATE.lobby_mode = mval
                            STATE.log_msg("modo seleccionado: %s (%d)" % (mname, mval))
                            print("[LOBBY] modo=%s (%d)" % (mname, mval), flush=True)
                            clicked = True
                            break
                    if not clicked:
                        # SALA: campo de texto (solo en modo SALAS, 0)
                        if STATE.lobby_mode == 0:
                            sx0, sy0, sw, sh = L_SALA
                            if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                                with STATE.lock:
                                    STATE.lobby_room_edit = True
                                clicked = True
                    if not clicked:
                        # SERVIDOR: flechas ‹ › (se aplica al presionar
                        # JUGAR junto con modo/sala, no al ciclar)
                        sx0, sy0, sw, sh = L_SRV_IZQ
                        if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                            with STATE.lock:
                                i = SERVER_LIST.index(STATE.lobby_server) if STATE.lobby_server in SERVER_LIST else 0
                                STATE.lobby_server = SERVER_LIST[(i - 1) % len(SERVER_LIST)]
                            STATE.log_msg("servidor: %s" % STATE.lobby_server)
                            print("[LOBBY] server=%s" % STATE.lobby_server, flush=True)
                            clicked = True
                        else:
                            sx0, sy0, sw, sh = L_SRV_DER
                            if sx0 <= x <= sx0 + sw and sy0 <= y <= sy0 + sh:
                                with STATE.lock:
                                    i = SERVER_LIST.index(STATE.lobby_server) if STATE.lobby_server in SERVER_LIST else 0
                                    STATE.lobby_server = SERVER_LIST[(i + 1) % len(SERVER_LIST)]
                                STATE.log_msg("servidor: %s" % STATE.lobby_server)
                                print("[LOBBY] server=%s" % STATE.lobby_server, flush=True)
                                clicked = True
                    if not clicked:
                        # AUTORESPAWN toggle (L_AUTORESP)
                        ax, ay, aw, ah = L_AUTORESP
                        if ax <= x <= ax + aw and ay <= y <= ay + ah:
                            with STATE.lock:
                                STATE.autorespawn = not STATE.autorespawn
                            STATE.log_msg("autorespawn: %s" % ("ON" if STATE.autorespawn else "OFF"))
                            print("[LOBBY] autorespawn=%s" % STATE.autorespawn, flush=True)
                            clicked = True
                    if not clicked:
                        # boton JUGAR » (L_JUGAR)
                        jx, jy, jw, jh = L_JUGAR
                        if jx <= x <= jx + jw and jy <= y <= jy + jh:
                            with STATE.lock:
                                STATE.lobby_room_edit = False
                            STATE.phase = "game"
                            STATE.dead_at = None
                            in_lobby = False
                            STATE.spawn_event.set()
                            _aplicar_seleccion()
                else:
                    # boton PAUSA abajo-izquierda (volver al lobby)
                    if 20 <= x <= 170 and H - 46 <= y <= H - 10:
                        STATE.phase = "paused"
                        STATE.set_mouse(0.0, 0.0)
                        in_lobby = True
                        STATE.log_msg("pausa - volviste al lobby (Enter para seguir)")
                        print("[PAUSA] boton -> lobby (sesion viva)", flush=True)
                    elif W - 130 <= x <= W - 20 and H - 46 <= y <= H - 10:
                        running = False

        snap = STATE.snapshot()

        # Diagnostico persistente de render/proyeccion, una muestra por
        # segundo. Registra coordenadas reales recibidas, rango, camara,
        # zoom, culling, op19 y UDP. Asi se puede determinar con datos si
        # el problema es eje, escala, camara o render.
        _diag_last = getattr(run_ui, "_diag_last", 0.0)
        if now - _diag_last >= 1.0:
            run_ui._diag_last = now
            try:
                ents_diag = snap.get("entities_clear", {})
                coords = []
                with_mass = []
                for did, de in ents_diag.items():
                    dx_ = de.get("x")
                    dz_ = de.get("z")
                    if dx_ is None or dz_ is None:
                        continue
                    pair = [did, round(dx_, 1), round(dz_, 1), round(de.get("masa", 0), 1)]
                    coords.append(pair)
                    if de.get("masa", 0) > 0:
                        with_mass.append(pair)
                pos_diag = snap.get("position")
                if isinstance(pos_diag, (list, tuple)):
                    pos_diag = list(pos_diag)
                else:
                    pos_diag = None
                own_status = {}
                for oid in sorted(snap.get("player_cells", [])):
                    oe = ents_diag.get(oid)
                    own_status[str(oid)] = None if oe is None else {
                        "x": oe.get("x"), "z": oe.get("z"),
                        "masa": oe.get("masa", 0),
                        "has_x_prev": oe.get("x_prev") is not None,
                        "has_z_prev": oe.get("z_prev") is not None,
                    }
                diag = {
                    "t": round(now, 3),
                    "phase": STATE.phase,
                    "position": pos_diag,
                    "own_status": own_status,
                    "camera": [round(_cam_state["x"], 2), round(_cam_state["z"], 2)] if _cam_state["x"] is not None else None,
                    "zoom": round(_cam_state["zoom"], 5) if _cam_state["zoom"] is not None else None,
                    "n_entities": len(ents_diag),
                    "n_coords": len(coords),
                    "n_mass": len(with_mass),
                    "coord_min": [round(min(x[1] for x in coords), 1), round(min(x[2] for x in coords), 1)] if coords else None,
                    "coord_max": [round(max(x[1] for x in coords), 1), round(max(x[2] for x in coords), 1)] if coords else None,
                    "sample_mass": sorted(with_mass, key=lambda x: -x[3])[:8],
                    "player_ent": snap.get("player_ent_id"),
                    "player_cells": sorted(snap.get("player_cells", [])),
                    "udp_sent": _udp_holder.get("sent", 0),
                    "udp_angle": round(_udp_holder.get("last_angle", 0.0), 4),
                    "udp_power": round(_udp_holder.get("last_power", 0.0), 4),
                }
                with open(os.path.join(ROOT, "_view_diag.log"), "a", encoding="utf-8") as df:
                    df.write(json.dumps(diag, separators=(",", ":")) + "\n")
            except Exception:
                pass

        # --- sesion muerta en partida: el socket se cerro (server corto o
        # reconexion en curso) -> volver al lobby para no dejar el mapa
        # congelado. bot_session reintenta solo en background.
        if STATE.phase == "game" and not STATE.connected and not STATE.spawned:
            STATE.phase = "paused"
            STATE.set_mouse(0.0, 0.0)
            STATE.dead_at = None
            in_lobby = True
            STATE.log_msg("sesion perdida - reconectando...")
            print("[SESION] socket cerrado -> lobby (reconectando)", flush=True)
            snap = STATE.snapshot()

        # --- deteccion de muerte: el jugador dejo de existir y no respawneo ---
        if STATE.phase == "game" and STATE.spawned and STATE._player_ent is not None:
            pe = STATE.entities_clear.get(STATE._player_ent)
            if pe is None or (pe.x is None and pe.z is None):
                # el jugador desaparecio del mundo -> muerto
                if STATE.dead_at is None:
                    STATE.dead_at = now
                elif now - STATE.dead_at > 8.0:
                    STATE.phase = "dead"
                    STATE.log_msg("jugador eliminado del mundo - lobby de muerte")
                    print("[MUERTE] jugador fuera del mundo -> lobby", flush=True)
            else:
                STATE.dead_at = None

        if in_lobby or STATE.phase == "dead":
            muerto = (STATE.phase == "dead")
            pausa = (STATE.phase == "paused")
            draw_lobby(screen, snap, room, font, font_small, font_tiny, muerto=muerto, pausa=pausa)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # --- fase de juego ---
        # LOG DE DIAGNOSTICO (analizable, JSON lines en _view_diag.log):
        # cada 1s registra camara, posicion, celulas del jugador, mouse y
        # entidades visibles — para diagnosticar el movimiento/camara sin
        # adivinar. Se cierra al salir.
        _diag_last = getattr(run_ui, "_diag_last", 0.0)
        if now - _diag_last >= 1.0:
            run_ui._diag_last = now
            try:
                with open(os.path.join(ROOT, "_view_diag.log"), "a", encoding="utf-8") as df:
                    mstate = STATE.mouse_snapshot()
                    pos2d_ = STATE.pos2d()
                    ent_vis = []
                    if pos2d_:
                        camx_ = _f(_cam_state["x"]) if _cam_state["x"] is not None else _f(pos2d_[0])
                        camz_ = _f(_cam_state["z"]) if _cam_state["z"] is not None else _f(pos2d_[1])
                        zz = _cam_state["zoom"] or 0.0
                        # entidades con masa visibles en el frustrum
                        fr_w = W / zz + 20 if zz > 0 else 0
                        for eid, ec in snap.get("entities_clear", {}).items():
                            ex, ez = ec.get("x"), ec.get("z")
                            if ex is None or ez is None:
                                continue
                            if abs(ex - camx_) <= fr_w / 2 and abs(ez - camz_) <= fr_w / 2:
                                ent_vis.append([eid, round(ec.get("masa", 0), 1)])
                        ent_vis.sort(key=lambda t: -t[1])
                        df.write(json.dumps({
                            "t": round(now, 3),
                            "phase": STATE.phase,
                            "pos": [round(pos2d_[0], 1), round(pos2d_[1], 1)],
                            "cam": [round(camx_, 1), round(camz_, 1)],
                            "zoom": round(zz, 4),
                            "player_ent": STATE.player_entity_id,
                            "player_cells": sorted(STATE.player_cells),
                            "mass": round(snap.get("mass", 0), 1),
                            "mass_display": snap.get("mass_display"),
                            "mouse": {"angle": round(mstate.get("angle", 0), 3),
                                      "power": round(mstate.get("power", 0), 3),
                                      "active": mstate.get("active")},
                            "ent_vis_top": ent_vis[:10],
                            "n_ent": len(snap.get("entities_clear", {})),
                        }) + "\n")
            except Exception:
                pass
        pos2d = STATE.pos2d()
        if pos2d:
            try:
                    # CONTROL POR MOUSE: replica EXACTA del binario (Ghidra,
                # re/protocolo_haxe_fisica_movimiento.md seccion 3.1):
                #   dir = normalize(mouse - centro)
                #   dist = |mouse - centro| en px;  maxSpeed ~400 (config +0x388)
                #   force = sqrt(clamp(dist/maxSpeed, 0, 1))  -> se envia en el MOVE
                #   velocidad LOCAL (prediccion del cliente, applyExtrapolation
                #   FUN_1414c7ec0): v = dir * clamp(dist, maxSpeed, 3*maxSpeed)
                #                    / (size * 2)  POR TICK 16.6ms (x60 = /s)
                #   el server corrige con los CLEAR (posicion real) — la
                #   prediccion local cubre los gaps y da control inmediato.
                # El angulo se calcula contra la CAMARA RENDERIZADA (_cam_state)
                # y no contra la posicion logica: si la camara va con lerp detras,
                # calcular contra pos2d hace que el cursor del mundo no coincida
                # con lo que se ve -> orbita (el bug de los circulos).
                mx, my = pygame.mouse.get_pos()
                cam_x = _f(_cam_state["x"]) if _cam_state["x"] is not None else _f(pos2d[0])
                cam_y = _f(_cam_state["z"]) if _cam_state["z"] is not None else _f(pos2d[1])
                mw, mh = world_bounds(snap)
                # mismo zoom que la camara dibujada (consistente con la pantalla);
                # fallback = formula fit-to-size del binario con el radio actual
                masa_m = snap.get("mass_display") or snap.get("mass", 0) or 50.0
                radio_m = math.floor(math.sqrt(masa_m) * 10.0 + 0.5) + 1 or 40.0
                zoom = _f(_cam_state["zoom"]) or _fit_zoom(radio_m, 1.0)
                # cursor -> coordenadas del mundo (contra la camara renderizada)
                wx = cam_x + (mx - W / 2) / zoom
                wy = cam_y + (my - H / 2) / zoom
                dx, dz = wx - pos2d[0], wy - pos2d[1]
                dist = math.hypot(dx, dz)
                cdist = math.hypot(mx - W / 2, my - H / 2)
                if cdist > 20:
                    angle = math.atan2(dz, dx)
                    # fuerza del MOVE (binario): sqrt(clamp(dist/maxSpeed, 0, 1))
                    power = math.sqrt(min(1.0, max(0.0, cdist / 400.0)))
                    STATE.set_mouse(angle, power)
                    # SIN prediccion local de posicion: integrate_dir mueve
                    # STATE.position y el CLEAR la corrige con la real -> la
                    # celula orbita (el bug de los circulos, confirmado 2x).
                    # Server-authoritative: el MOVE solo lleva angulo/potencia;
                    # la posicion llega por CLEAR y la interpola el fixed-
                    # timestep (draw_map, alpha = dt_desde_CLEAR / 16.66ms).
                else:
                    STATE.set_mouse(0.0, 0.0)

            except Exception:
                STATE.set_mouse(0.0, 0.0)

        draw_gradient(screen)
        screen.blit(star_layer, (0, 0))
        try:
            draw_map(screen, snap, font_small, font_tiny)
            draw_minimap(screen, snap)
            draw_panel(screen, snap, font_small, font_tiny)
            draw_hud(screen, snap, font, font_small)
        except Exception as e:
            # un frame corrupto (string en posicion/masa del parser) jamas
            # debe tumbar el visor: se salta el dibujo y se sigue.
            print("[RENDER] frame saltado: %r" % (e,), flush=True)
        pygame.display.flip()
        clock.tick(FPS)

    stop_event.set()
    pygame.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", default="", help="sala por nombre (modo SALAS); vacio = AUTO")
    ap.add_argument("--server", default="europe")
    ap.add_argument("--mode", type=int, default=0, help="0=SALAS 4=CTF 5=FFA 7=HVZ")
    ap.add_argument("--device", default=None)
    ap.add_argument("--pem", default=None)
    args = ap.parse_args()
    device = args.device or load_device_id()
    pem = args.pem or os.path.join(_PARENT, "embedded_rsa_private_14.pem")
    if not os.path.exists(pem):
        pem = os.path.join(_PARENT, "mito_client", "embedded_rsa_private_14.pem")
    with STATE.lock:
        STATE.lobby_server = args.server
        STATE.lobby_mode = args.mode
        STATE.lobby_room = args.room or ""
    run_ui(device, pem, args.room)
