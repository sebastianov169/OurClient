"""
OurClient/view.py — el VIEW del binario (FUN_140795df0) en Python.

Procesa: input del mouse (updateMouse_core FUN_1414a8d20), camara
(lerp + fit-to-size), interpolacion de posiciones (fixed-timestep
16.66ms), y el render del mundo con las paletas reales del binario.

Independiente del visor: solo usa client/ + OurClient/world.
"""
import math
import time

import pygame

from client.entities import CELL_RGB, FOOD_RGB, TEAM_RGB, radio_from_masa
from client.engine.update_mouse import updateMouse_core

MUNDO_W = 16384.0
MUNDO_H = 16384.0


def _f(v, d=0.0):
    try:
        if v is None:
            return d
        return float(v)
    except (TypeError, ValueError):
        return d


class View:
    """El View del binario: camara + input + render del mundo."""

    def __init__(self, world, w=1280, h=720):
        self.world = world
        self.w, self.h = w, h
        self.cam_x = None          # posicion logica de la camara (mundo)
        self.cam_z = None
        self.zoom = 0.05
        self._zoom_smooth = None   # zoom suavizado (anti-oscilacion)
        self._cam_sx = 0.0         # suavizada (lerp 0.125 del binario)
        self._cam_sz = 0.0
        self.mouse_world = (0.0, 0.0)
        self.last_move = {"angle": 0.0, "power": 0.5, "t": 0.0}
        self._cache = {}

    # ---- input: updateMouse_core (FUN_1414a8d20) ----
    def update_mouse(self, mx, my, send_move=None):
        """Mouse de pantalla -> direccion/fuerza del binario.

        El angulo se calcula contra la POSICION LOGICA del jugador
        (w.own_x/own_z — la real del server, actualizada por el 0x00 de la
        propia), NO contra la camara suavizada ni la celula virtual del
        spawn: la camara va desfasada por el lerp y el spawn queda FIJO en
        la esquina (0,1,10239) — calcular contra el spawn hacia que la
        celula no respondiera al mouse (se tepeaba entre la virtual y la
        real). Este es el fix SYNC_DIRECTO del visor (client/main.py
        _sync_player L605).
        """
        w = self.world
        px, pz = w.own_x, w.own_z
        if px is None or pz is None:
            # sin posicion real aun: spawn_pos del [20] (posicion REAL del
            # spawn, nunca None en partida) — SIEMPRE mandar el MOVE: sin
            # MOVEs el server no correlaciona y nunca manda el 0x1c
            # (identificacion) -> circulo vicioso: sin identificacion el
            # update_mouse hacia return y el MOVE no salia (own=None
            # permanente + "no puedo moverme")
            sp = w.spawn_pos
            if sp is not None:
                px, pz = _f(sp[0]), _f(sp[1])
            else:
                return
        px, pz = _f(px), _f(pz)
        # mouse en coordenadas de MUNDO: relativo a la celula del jugador,
        # NO a la camara (el mouse del centro = celula en el centro = 0 fuerza)
        wx = (mx - self.w / 2) / self.zoom + px
        wz = (my - self.h / 2) / self.zoom + pz
        self.mouse_world = (wx, wz)
        dist = math.hypot(wx - px, wz - pz)
        angle = math.atan2(wz - pz, wx - px)
        # velocidad/fuerza REAL del binario (updateMouse_core FUN_1414a8d20):
        # fuerza = sqrt(clamp(dist / maxSpeed)); maxSpeed del objeto.
        # El binario NUNCA manda power < 0.59 (capturas: power 0.59-1.0):
        # la celula SIEMPRE avanza hacia el angulo — con power 0.1 el
        # control se siente muerto (el usuario: "no puedo moverlo"). Con
        # maxSpeed 200 la curva de poder satura antes: el mouse a 100px
        # del centro ya da power ~0.7.
        # maxSpeed DINAMICO segun la masa: el binario lo reduce a medida
        # que creces (celulas grandes son mas lentas). Masa 50 -> 200,
        # masa 1000 -> 100, masa 5000 -> 50 (aprox, escala 1/sqrt(masa/50)).
        own_m = self.world.own_mass if self.world.own_mass > 1.0 else 50.0
        max_speed = max(50.0, 200.0 / max(1.0, (own_m / 50.0) ** 0.5))
        power = math.sqrt(max(0.0, min(1.0, dist / max_speed)))
        if power < 0.59:
            power = 0.59
        self.last_move = {"angle": angle, "power": power, "t": time.time()}
        if send_move:
            send_move(angle, power)

    def send_split(self, send=None):
        """splitButton del binario (SPACE): opcode del split."""
        if send:
            send("split")

    def send_eject(self, send=None):
        """ejectButton del binario (W): opcode del eject."""
        if send:
            send("eject")

    # ---- camara (STUCK a la celula real, del binario) ----
    def update_camera(self, dt):
        # camara STUCK a la celula del jugador. la prioridad es:
        #   1. own_x/own_z (cache REAL, actualizada por 0x00 de la propia,
        #      por el op20, y por la integracion local del MOVE): la camara
        #      sigue al jugador donde ESTA realmente, sin saltos.
        #   2. la entidad de own_id_real si existe.
        #   3. fallback: spawn_pos del [20] (nunca None en partida).
        # ANTES la camara saltaba al spawn cuando player_entity_id se
        # invalidaba (id sin entidad). Ahora SIEMPRE usa own_x/own_z
        # (la integracion local mantiene este valor actualizado en tiempo
        # real hacia donde apunta el mouse).
        w = self.world
        tx, tz = None, None
        if w.own_x is not None and w.own_z is not None:
            tx, tz = _f(w.own_x), _f(w.own_z)
        elif w.own_id_real is not None and w.own_id_real in w.entities:
            e = w.entities[w.own_id_real]
            if e.grid_x is not None and e.grid_y is not None and (e.masa or 0) > 1.0:
                tx, tz = _f(e.grid_x), _f(e.grid_y)
        if tx is None:
            if self.cam_x is not None:
                return
            if w.spawn_pos is not None:
                tx, tz = _f(w.spawn_pos[0]), _f(w.spawn_pos[1])
            else:
                return
        if self.cam_x is None:
            self.cam_x, self.cam_z = tx, tz
            self._cam_sx, self._cam_sz = tx, tz
        cam_jump = math.hypot(tx - self.cam_x, tz - self.cam_z)
        if cam_jump > 1500.0:
            # spawn/respawn o cambio de sala: SNAP (nunca arrastrar)
            self.cam_x, self.cam_z = tx, tz
            self._cam_sx, self._cam_sz = tx, tz
        else:
            # STUCK DURO a la posicion REAL del server
            self.cam_x, self.cam_z = tx, tz
            self._cam_sx, self._cam_sz = tx, tz
        # zoom fit-to-size con la masa SUAVIZADA del jugador
        masa_j = max(1.0, w.own_mass if w.own_mass > 1.0 else 50.0)
        radio_j = math.floor(math.sqrt(masa_j) * 10.0 + 0.5) + 1
        import client.main as _C
        zoom = _C._fit_zoom(radio_j, self.zoom)
        if self._zoom_smooth is None:
            self._zoom_smooth = zoom
        # lerp 0.10 del binario
        self._zoom_smooth += (zoom - self._zoom_smooth) * 0.10
        self.zoom = max(0.02, min(1.5, self._zoom_smooth))

    # ---- interpolacion (fixed-timestep 16.66ms del binario) ----
    def interp_alpha(self):
        """alpha = dt_desde_ultimo_CLEAR / 16.66ms, clamp [0,1)
        (FUN_140795df0 L553: FUN_1407959e0(param_1, dVar23 / 16.6667))."""
        t = self.world._t_last_clear
        if not t:
            return 1.0
        return max(0.0, min(1.0, (time.time() - t) / 0.0166667))

    def lerp_pos(self, eid, e):
        """Posicion interpolada: prev + (cur - prev) * alpha.

        El CLEAR resetea el acumulador (_t_last_clear): justo despues de un
        CLEAR alpha~0 -> se dibuja la posicion ANTERIOR; entre CLEARs alpha
        sube a 1 -> posicion actual. Eso es exactamente applyPosition-
        Interpolated del binario (FUN_1406790f0: x += (target-x)*alpha)."""
        w = self.world
        with w.lock:
            prev = w._ent_prev.get(eid)
            cx, cy = e.grid_x, e.grid_y
        alpha = self.interp_alpha()
        if prev and alpha < 1.0:
            return (prev[0] + (cx - prev[0]) * alpha,
                    prev[1] + (cy - prev[1]) * alpha)
        return (cx, cy)

    # ---- proyeccion ----
    def world_to_screen(self, wx, wz):
        if self.cam_x is None:
            return (-100000, -100000)
        return ((wx - self.cam_x) * self.zoom + self.w / 2,
                (wz - self.cam_z) * self.zoom + self.h / 2)

    # ---- render ----
    def draw(self, surf, font_small, font_tiny, mouse=None):
        self._draw_bg(surf)
        self._draw_world(surf, font_small, font_tiny)
        # crosshair + flecha de direccion sobre la celula (feedback del
        # control: el jugador ve DONDE apunta el mouse y CON QUE fuerza)
        if mouse is not None:
            self._draw_cursor_feedback(surf, mouse)

    def _draw_bg(self, surf):
        surf.fill((14, 16, 22))
        # grid del mundo
        if self.cam_x is not None:
            step = 1024
            for g in range(0, int(MUNDO_W) + 1, step):
                p1 = self.world_to_screen(g, 0)
                p2 = self.world_to_screen(g, MUNDO_H)
                pygame.draw.line(surf, (30, 34, 44), p1, p2, 1)
                p1 = self.world_to_screen(0, g)
                p2 = self.world_to_screen(MUNDO_W, g)
                pygame.draw.line(surf, (30, 34, 44), p1, p2, 1)
            # borde del mundo (GameBorders)
            corners = [(0, 0), (MUNDO_W, 0), (MUNDO_W, MUNDO_H), (0, MUNDO_H), (0, 0)]
            pts = [self.world_to_screen(x, z) for x, z in corners]
            pygame.draw.lines(surf, (180, 60, 60), False, pts, 3)

    def _draw_cursor_feedback(self, surf, mouse):
        """Flecha indicadora del angulo + barra de power: el usuario ve
        hacia donde va a ir la celula y con que fuerza."""
        mx, my = mouse
        own_x = self.world.own_x
        own_z = self.world.own_z
        if own_x is None:
            return
        sx, sy = self.world_to_screen(own_x, own_z)
        if not (-50 <= sx <= self.w + 50 and -50 <= sy <= self.h + 50):
            return
        dx, dy = mx - sx, my - sy
        d = math.hypot(dx, dy)
        if d < 1:
            return
        # linea desde la celula hasta el mouse
        nx, ny = dx / d, dy / d
        # la longitud visual de la flecha escala con el power (~max 100px)
        arrow_len = min(120, 24 + int(96 * self.last_move.get("power", 0.5)))
        ax = sx + nx * arrow_len
        ay = sy + ny * arrow_len
        color = (255, 230, 80) if self.last_move.get("power", 0.5) > 0.85 else (80, 195, 255)
        pygame.draw.line(surf, color, (int(sx), int(sy)), (int(ax), int(ay)), 3)
        # punta de flecha
        left_x = ax - nx * 12 + (-ny) * 6
        left_y = ay - ny * 12 + nx * 6
        right_x = ax - nx * 12 - (-ny) * 6
        right_y = ay - ny * 12 - nx * 6
        pygame.draw.polygon(surf, color, [
            (int(ax), int(ay)), (int(left_x), int(left_y)), (int(right_x), int(right_y))])
        # barra de power: arco pequeño debajo del cursor (saturación)
        bar_w = 50
        bx = int(mx - bar_w / 2)
        by = int(my + 22)
        pygame.draw.rect(surf, (24, 28, 36), (bx, by, bar_w, 5), border_radius=2)
        pw = self.last_move.get("power", 0.5)
        pygame.draw.rect(surf, color, (bx, by, int(bar_w * pw), 5), border_radius=2)

    def _draw_world(self, surf, font_small, font_tiny):
        w = self.world
        alpha = self.interp_alpha()
        # copia bajo lock: el hilo de red muta w.entities (RuntimeError si
        # se itera el dict vivo)
        with w.lock:
            items = list(w.entities.items())
            my_cells = set(w.player_cells)
            my_id = w.player_entity_id
        # zOrder: pequenos detras, grandes delante (sortByZOrder)
        items.sort(key=lambda t: _f(t[1].masa, 0))
        own_drawn = None  # (sx, sy, r_px, color, name) -> dibujado al FINAL
        # identificacion de la propia: SOLO el id REAL (owner==account_id)
        # o el player_entity_id (marca 0x19/0x1a del CLEAR). NO usar
        # player_cells suelto: el 0x1c que llega en frames esporadicos
        # mete cualquier id que el server marco ese frame (incluyendo
        # momentos donde adopta una ajena cercana al spawn como propia).
        # Antes el bucle pintaba ESA ajena como "is_own" (color de equipo)
        # y al siguiente frame la verdadera -> el usuario veia la celula
        # cambiar de color/tamaño/posicion (el bug que reporto).
        own_real_id = w.own_id_real if w.own_id_real is not None else my_id
        for eid, e in items:
            if eid == "__virtual__":
                # la virtual SOLO es el fallback de posicion/masa cuando la
                # identificacion fluctua; la celula REAL del jugador se
                # dibuja al final con own_x/own_z/own_mass — dibujar la
                # virtual como entidad ajena duplicaba el circulo
                continue
            px, pz = self.lerp_pos(eid, e)
            sx, sy = self.world_to_screen(px, pz)
            if sx < -200 or sx > self.w + 200 or sy < -200 or sy > self.h + 200:
                continue
            masa = _f(e.masa, 0)
            r_w = _f(e.radius, 0) or radio_from_masa(masa)
            r_px = max(4.0, r_w * self.zoom)  # minimo 4px (antes 1.5 -> invisibles)
            # SOLO es "propia" si coincide con el id REAL (own_id_real /
            # player_entity_id). player_cells sigue incluyendo ids que el
            # 0x1c marco transitoriamente — pintar esas como propias hacia
            # que la celula cambiara de color y de tamaño entre frames
            # (reporte: "se agranda, se achiquita y cambia de color").
            is_own = (own_real_id is not None and eid == own_real_id)
            # la celula del jugador SIEMPRE visible: tamaño minimo en pantalla
            # (recien spawneada tiene masa 1.0 como la comida -> indistinguible;
            # el binario la pinta azul team + nombre + minimo ~28px)
            if is_own and r_px < 32:
                r_px = 32.0
            # color: paleta del binario (la celula propia usa el color REAL
            # del jugador del op16 player_info si llego; si no, team azul)
            if is_own:
                own_info = w.player_info.get(eid, {})
                c = own_info.get("color")
                if isinstance(c, (int, float)) and not isinstance(c, bool):
                    color = ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)
                else:
                    color = TEAM_RGB[1] if len(TEAM_RGB) > 1 else (80, 160, 255)
            elif masa <= 1.0:
                color = FOOD_RGB[eid % len(FOOD_RGB)] if FOOD_RGB else (200, 200, 200)
            else:
                # eid puede ser "__virtual__" (string) — indice numerico seguro
                try:
                    _idx = eid % len(CELL_RGB)
                except TypeError:
                    _idx = abs(hash(eid)) % len(CELL_RGB) if CELL_RGB else 0
                color = CELL_RGB[_idx] if CELL_RGB else (100, 100, 200)
            if is_own:
                # la celula propia se dibuja AL FINAL (encima de la comida
                # que la tapaba: con masa 1.0 quedaba enterrada en el grupo
                # de miles de pepitas del zOrder por masa)
                name = w.names.get(eid) or w.player_info.get(eid, {}).get("name")
                own_drawn = (sx, sy, r_px, color, name)
                continue
            if r_px > 6:
                pygame.draw.circle(surf, color, (int(sx), int(sy)), int(r_px))
                pygame.draw.circle(surf, (min(255, color[0] + 60),
                                          min(255, color[1] + 60),
                                          min(255, color[2] + 60)),
                                   (int(sx), int(sy)), int(r_px), max(1, int(r_px * 0.08)))
            else:
                pygame.draw.circle(surf, color, (int(sx), int(sy)), int(r_px))
            # nombre: solo para celulas con jugador (masa > 10 y zoom decente)
            # para que se vean los nombres reales en partida
            if masa > 10 and r_px >= 6:
                name = w.names.get(eid) or w.player_info.get(eid, {}).get("name")
                if name:
                    lbl = font_tiny.render(name, True, (255, 255, 255))
                    shadow = font_tiny.render(name, True, (0, 0, 0))
                    nx = int(sx - lbl.get_width() / 2)
                    ny = int(sy - r_px - 12)
                    surf.blit(shadow, (nx + 1, ny + 1))
                    surf.blit(lbl, (nx, ny))
        # --- celula del jugador: encima de TODO, con borde y nombre ---
        # SIEMPRE se dibuja (con la posicion/masa REALES own_x/own_z/
        # own_mass): aunque player_entity_id fluctue (el 0x1c es esporadico
        # en FFA), el jugador NUNCA pierde su celula de vista
        if own_drawn is None and w.own_x is not None and w.own_z is not None:
            sx, sy = self.world_to_screen(w.own_x, w.own_z)
            if -200 <= sx <= self.w + 200 and -200 <= sy <= self.h + 200:
                m_real = w.own_mass if w.own_mass and w.own_mass > 1.0 else 10.0
                r_w = radio_from_masa(m_real)
                r_px = max(28.0, r_w * self.zoom)
                color = (80, 195, 255)
                nid = w.own_id_real
                name = None
                if nid is not None:
                    name = (w.names.get(nid)
                            or w.player_info.get(nid, {}).get("name")
                            or w.leaderboard.get(nid, {}).get("name"))
                own_drawn = (sx, sy, r_px, color, name)
        if own_drawn is not None:
            sx, sy, r_px, color, name = own_drawn
            pygame.draw.circle(surf, color, (int(sx), int(sy)), int(r_px))
            # borde brillante + halo (como el binario)
            pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), int(r_px), 2)
            pygame.draw.circle(surf, (min(255, color[0] + 80), min(255, color[1] + 80),
                                      min(255, color[2] + 80)),
                               (int(sx), int(sy)), int(r_px + 3), 1)
            if name:
                lbl = font_small.render(name, True, (255, 255, 255))
                # nombre con sombra (legible sobre cualquier fondo)
                shadow = font_small.render(name, True, (0, 0, 0))
                nx = int(sx - lbl.get_width() / 2)
                ny = int(sy - r_px - 16)
                surf.blit(shadow, (nx + 1, ny + 1))
                surf.blit(lbl, (nx, ny))
