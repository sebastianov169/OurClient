"""
OurClient/world.py — el MUNDO del binario: Grid + entidades + player.

Replica fkengine.game.Grid (FUN_1406f6e30): el Grid crea el View y los
Players por slot. Las entidades se crean con la fabrica FUN_14073b220
(client.entities.build_entity) y se actualizan con los frames CLEAR.
Independiente del visor.
"""
import threading

from client.entities import build_entity
from client.world.grid import Grid as _Grid
from client.world.player import Player as _Player

# Limites del mundo (constante del binario: el mapa mide 16384x16384u)
MUNDO_W = 16384.0
MUNDO_H = 16384.0


class World(_Grid):
    """El Grid del binario: contenedor del mundo + entidades vivas."""

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.entities = {}          # eid -> GameEntity (via build_entity)
        self.player_entity_id = None  # marca 0x19/0x1a
        self.player_cells = set()     # ids de tus celulas (op19)
        self.names = {}               # eid -> nombre (op16)
        self.player_info = {}         # eid -> {color, team, lvl} (op16)
        self.leaderboard = {}         # eid -> {name, masa}
        self.spawn_pos = None
        self.account_id = None        # op4: id de la CUENTA (no entidad)
        self._op19_seen = False
        self.mass = 0.0
        self.score = 0.0
        self.spawned = False
        self.connected = False
        # ULTIMA posicion REAL conocida de la propia (se actualiza en el
        # feed cuando el id coincide). El angulo del mouse y el MOVE usan
        # ESTA posicion, NO la la celula virtual del spawn: el spawn queda
        # FIJO (p.ej. (0,1,10239) = esquina) y para calcular el angulo
        # contra el spawn hacia que la celula "no respondiera al mouse"
        # (se tepeaba entre la virtual y la real).
        self.own_x = None
        self.own_z = None
        # ULTIMA masa REAL de la propia (se actualiza con el CLEAR de la
        # propia / owner==account_id). El HUD y el zoom la usan SIEMPRE:
        # cuando la identificacion fluctua, main_cell cae a la celula
        # virtual con masa 10.0 (imposible en el juego real) -> el usuario
        # ve "MASA 10" y el zoom explota (radio 33 -> todo diminuto).
        self.own_mass = 0.0
        # SUAVIZADO de la masa: la masa del CLEAR del server fluctua con el
        # culling (a veces llega un valor bajo, luego alto, luego bajo). El
        # usuario decia "la masa cambia de la nada". Aqui guardamos un EMA
        # que se actualiza SOLO cuando el delta es razonable (no >2x en un
        # frame, no <0.5x en un frame que indicaria muerte/culling).
        self._mass_smooth = 0.0
        # ULTIMO id REAL de la propia (owner==account_id del CLEAR): la
        # vista lo usa para el NOMBRE/borde aunque player_entity_id fluctue
        self.own_id_real = None
        self._ent_prev = {}           # interpolacion
        self._t_last_clear = 0.0
        # INTEGRACION LOCAL del MOVE del jugador: aunque el server no
        # correlacione (cuenta fria) y no mande updates de la propia, el
        # cliente integra el MOVE localmente para que la camara y la celula
        # visible se muevan hacia donde apunta el mouse (como en el binario
        # real cuando esta cargando el mundo). Se actualiza desde main.py
        # con integrate_move(dx, dz) cada vez que sale un MOVE UDP.
        # Velocidad base (unidades/segundo): el binario escala por power.
        self._local_vel = 320.0
        # timestamp del ultimo CLEAR con player_entity_id (para detectar
        # respawns silenciosos)
        self._t_last_own_seen = 0.0

    # ---- entidades ----
    def upsert(self, eid, entity_type=None):
        """Crea la entidad si no existe.

        NO toma el lock (el caller _feed ya lo tiene — threading.Lock no es
        reentrante; tomarlo aqui causaba deadlock). NO recrea por cambio de
        entityType: el flag del parser CLEAR alterna entre 1 (dump comida),
        0x14/0x15 (célula con masa, = 20/21 decimal, fuera de la fabrica) y
        los flags reales (2/4/5/6...). Recrear perdia masa/posicion en cada
        frame alterno (bug de las celulas fantasma)."""
        e = self.entities.get(eid)
        if e is None:
            # tipo real de la fabrica si es valido (1-15); si no, generico
            from client.entities import ENTITY_FACTORY
            t = entity_type if entity_type in ENTITY_FACTORY else 0
            e = build_entity(eid, t)
            self.entities[eid] = e
        return e

    def remove(self, eid):
        with self.lock:
            self.entities.pop(eid, None)
            self._ent_prev.pop(eid, None)
            # NO descartar player_entity_id de player_cells: en FFA el 0x07
            # dead de la propia llega por culling/recreacion del server SIN
            # muerte real (la entidad se re-manda con el mismo id al frame
            # siguiente y el 0x1c la re-marca). Descartarla aqui cortaba la
            # identificacion en vivo (own=3707 masa=35 -> own=None sin
            # [MUERTE]). La muerte REAL se detecta por el [25] (spawned
            # False -> lobby) y el id reciclado por masa <= 1.0 en _feed.
            if eid != self.player_entity_id:
                self.player_cells.discard(eid)

    def clear(self):
        with self.lock:
            self.entities.clear()
            self._ent_prev.clear()
            self.player_cells.clear()

    # ---- entidad local del jugador (cuando el server no correlaciona) ----
    def set_own_pos(self, x, z, source="unknown"):
        """Setea la posicion REAL del jugador con trazabilidad.

        source indica de dónde el se obtuvo:
          - 'spawn': op20 (SPAWNED [20])
          - 'feed': CLEAR/0x04 con eid == player_entity_id o owner == account_id
          - 'op20': op0x2e (POSICION del jugador, escala u16/4)
          - 'local_move': integracion local del MOVE
          - 'p0': pos inicial (None)
        Solo actualiza si los valores son validos.
        """
        try:
            nx, nz = float(x), float(z)
        except (TypeError, ValueError):
            return
        if not (0 <= nx <= MUNDO_W and 0 <= nz <= MUNDO_H):
            # snap al borde si se sale (no teletransportar al spawn)
            nx = max(0.0, min(MUNDO_W, nx))
            nz = max(0.0, min(MUNDO_H, nz))
        self.own_x, self.own_z = nx, nz
        self._t_last_own_seen = time.time()

    def update_own_mass(self, masa):
        """Actualiza own_mass con SUAVIZADO. La masa del CLEAR del server
        fluctua con culling: a veces llega 80, luego 50, luego 100. El
        usuario se quejaba de "masa cambia de la nada". Aqui solo
        aceptamos cambios RAZONABLES (delta < 30% entre samples) y
        aplicamos un EMA con peso mayor para valores mas recientes.
        """
        if masa is None or masa <= 0:
            return
        m_cur = self.own_mass
        if m_cur <= 1.0:
            # sin valor previo: aceptar el primero
            self.own_mass = masa
            self._mass_smooth = masa
            return
        # ratio de cambio
        ratio = masa / m_cur if m_cur > 0 else 1.0
        # cambios >2x o <0.5x en un frame: probablemente culling/respawn,
        # no aplicar suavizado (aceptar directo). Esto evita que la masa
        # quede "anclada" a un valor viejo si llega un burst.
        if ratio > 2.0 or ratio < 0.5:
            self.own_mass = masa
            self._mass_smooth = masa
            return
        # cambio razonable: EMA con peso 0.7 al nuevo (suaviza culling)
        self._mass_smooth = 0.7 * masa + 0.3 * self._mass_smooth
        self.own_mass = self._mass_smooth

    def integrate_move(self, dt, angle, power):
        """Integra el MOVE localmente para que la camara y la celula
        visible se muevan hacia donde apunta el mouse, aunque el server
        no envie updates de la propia (cuenta fria).

        El visor hace esto mismo (client/main.py integrate_move), pero con
        un control: step = min(vel*dt, dist) para no salirse del mapa.
        Aqui se aplica el mismo control y ademas se clampea el resultado
        a los limites del mundo.

        Si llega CLEAR/owner con una posicion distinta, el feed sobreescribe.

        VELOCIDAD escalada por la masa del jugador: el binario reduce
        maxSpeed a medida que creces (celulas grandes son mas lentas).
        Velocidad base = 320u/s a masa 50; cae a ~100u/s a masa 5000.
        """
        import math as _m
        if self.own_x is None or self.own_z is None:
            return
        # escala: 320 / sqrt(masa/50). masa 50 -> 320, 200 -> 113, 1000 -> 51
        m_eff = max(1.0, self.own_mass if self.own_mass > 1.0 else 50.0)
        v_base = 320.0 / max(1.0, (m_eff / 50.0) ** 0.5)
        v = v_base * max(0.59, min(1.0, power))
        dx = _m.cos(angle) * v * dt
        dz = _m.sin(angle) * v * dt
        # aplicar con clip al mundo
        nx = self.own_x + dx
        nz = self.own_z + dz
        if nx < 0:
            nx = 0
        elif nx > MUNDO_W:
            nx = MUNDO_W
        if nz < 0:
            nz = 0
        elif nz > MUNDO_H:
            nz = MUNDO_H
        self.own_x, self.own_z = nx, nz

    # ---- estado del jugador ----
    @property
    def main_cell(self):
        """La celula principal: player_entity_id (marca 0x19/0x1a o best_own
        del op19). Si no existe como entidad, caer a la de MAS masa de
        player_cells (como feed_clear_entities del visor).

        FALLO FINAL (FFA, verificado en vivo diag10-16): el server NO manda
        la celula propia como entidad (dump=0, sin marca 0x19, sin flag=6,
        sin op19 valido — el op19 es leaderboard). La UNICA fuente de la
        posicion del jugador es el [20] SPAWNED (llega con posicion distinta
        en cada respawn: diag12/16). Sin esto la GUI no tiene nada que
        dibujar -> celula virtual en spawn_pos para que camara/MOVE/representacion
        funcionen; el [20] nuevo la actualiza (movimiento visible)."""
        if self.player_entity_id is not None:
            e = self.entities.get(self.player_entity_id)
            if e is not None and e.grid_x is not None:
                return e
            # id puesto pero la entidad NO existe (muerte/culling temporal):
            # NO devolver la virtual — la camara se queda donde esta y el
            # MOVE no sale desde el spawn fijo (own=2307 masa=10.0: la
            # celula "se tepeaba" entre el spawn y la real). Esperar a que
            # la entidad real aparezca o a la re-identificacion.
            return None
        if self.player_cells:
            # SOLO celulas REALES (masa > 1.0): los ids reciclados a comida
            # (masa 1.0) quedan en player_cells pero NO son la propia —
            # adoptarlos hacía que la celula se teletransportara/desapareciera
            # (own=1485 masa=1.0 en vivo).
            valid = [self.entities[eid] for eid in self.player_cells
                     if eid in self.entities
                     and self.entities[eid].grid_x is not None
                     and (self.entities[eid].masa or 0) > 1.0]
            if valid:
                return max(valid, key=lambda e: e.masa)
        # celula virtual: posicion del [20] (la real del jugador en FFA)
        # con la ULTIMA masa REAL conocida (nunca 10.0: es imposible en el
        # juego real y confunde al usuario + revienta el zoom)
        if self.spawn_pos is not None:
            v = self.entities.get("__virtual__")
            if v is None:
                from client.entities import build_entity
                v = build_entity("__virtual__", 2)
                self.entities["__virtual__"] = v
            v.grid_x, v.grid_y = self.spawn_pos
            v.masa = self.own_mass if self.own_mass > 1.0 else (
                self.mass if self.mass > 0 else 10.0)
            v.radio = 10.0
            return v
        return None

    def snapshot(self):
        """Estado plano para el HUD (sin lock — se llama desde el render)."""
        main = self.main_cell
        return {
            "entities": self.entities,
            "names": self.names,
            "player_info": self.player_info,
            "leaderboard": self.leaderboard,
            "player_ent_id": self.player_entity_id,
            "player_cells": sorted(self.player_cells),
            "spawn_pos": self.spawn_pos,
            "mass": main.masa if main and main.masa and main.masa > 1.0
            else (self.own_mass if self.own_mass > 1.0 else self.mass),
            "score": self.score,
            "spawned": self.spawned,
            "connected": self.connected,
        }
