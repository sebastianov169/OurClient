"""
OurClient/hud.py — la GUI del binario.

  - Lobby: fkengine.gui.game.Game (playButton, gameModeLabel, coinsButton,
    equipmentBar, experienceBar+currentLevel, botones superiores)
  - HUD en juego: fkengine.gui.game.CurrentPlayingView (leaderboard lateral
    con LeaderboardSlot, score arriba, XP bar, SPLIT/EJECT del
    MouseInputManager: splitButton/ejectButton)
"""
import pygame

W, H = 1280, 720

# tema del binario (MetalWorksMobileTheme)
BG = (18, 20, 28)
PANEL = (16, 18, 26)
ACCENT = (0, 200, 255)
TEXT = (230, 235, 245)
DIM = (140, 150, 165)
GOLD = (255, 200, 60)
GREEN = (90, 220, 120)
DANGER = (255, 70, 70)

_cache = {}


def rc(font, text, aa, color):
    key = (id(font), text, aa, color)
    if key not in _cache:
        _cache[key] = font.render(text, aa, color)
    return _cache[key]


def draw_btn(surf, x, y, w, h, label, font, accent=None, hot=False):
    accent = accent or ACCENT
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    bg = (40, 48, 60, 240) if hot else (30, 36, 46, 230)
    bd = accent + (160,) if hot else accent + (80,)
    pygame.draw.rect(s, bg, s.get_rect(), border_radius=8)
    pygame.draw.rect(s, bd, s.get_rect(), 2 if hot else 1, border_radius=8)
    surf.blit(s, (x, y))
    lbl = rc(font, label, True, TEXT)
    surf.blit(lbl, (x + (w - lbl.get_width()) // 2, y + (h - lbl.get_height()) // 2))


def draw_input(surf, x, y, w, h, text, caret, active, font, placeholder=""):
    """Input box del binario: border azul si activo, caret parpadea."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    bg = (28, 32, 44, 240) if active else (22, 26, 36, 220)
    bd = ACCENT + (220,) if active else DIM + (160,)
    pygame.draw.rect(s, bg, s.get_rect(), border_radius=6)
    pygame.draw.rect(s, bd, s.get_rect(), 2 if active else 1, border_radius=6)
    surf.blit(s, (x, y))
    if not text and placeholder:
        lbl = rc(font, placeholder, True, DIM)
        surf.blit(lbl, (x + 10, y + (h - lbl.get_height()) // 2))
    else:
        lbl = rc(font, text, True, TEXT)
        surf.blit(lbl, (x + 10, y + (h - lbl.get_height()) // 2))
        if active:
            # caret: solo cuando el tiempo es "on" (~30 blinks/s)
            import time as _t
            if int(_t.time() * 2) % 2 == 0:
                cx = x + 10 + lbl.get_width() + 2
                pygame.draw.line(surf, ACCENT, (cx, y + 6), (cx, y + h - 6), 2)


def draw_xp_bar(surf, x, y, w, h, level, xp, xp_next, font):
    pygame.draw.rect(surf, (24, 28, 36), (x, y, w, h), border_radius=4)
    prog = min(1.0, xp / xp_next) if xp_next > 0 else 1.0
    if prog > 0:
        pygame.draw.rect(surf, (0, 170, 220), (x, y, int(w * prog), h), border_radius=4)
    pygame.draw.rect(surf, (60, 70, 90), (x, y, w, h), 1, border_radius=4)
    lbl = rc(font, "NIVEL %d" % level, True, TEXT)
    surf.blit(lbl, (x + 6, y + (h - lbl.get_height()) // 2))


def draw_minimap(surf, view, x, y, size):
    """Mini-mapa del binario: el mundo 16384u -> size px. La propia =
    circulo blanco, los gigantes del mundo = puntos."""
    w = view.world
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((10, 12, 18, 220))
    pygame.draw.rect(s, (40, 46, 60), s.get_rect(), 1, border_radius=3)
    sx, sz = w.own_x, w.own_z
    if sx is None:
        sx, sz = (w.spawn_pos or (8192, 8192))
    cx = float(_safe(sx, 8192.0))
    cz = float(_safe(sz, 8192.0))
    scale = size / 16384.0
    # los gigantes del mundo (>500 de masa): puntos grandes y brillantes
    with w.lock:
        items = list(w.entities.items())
    for eid, e in items:
        if eid == "__virtual__":
            continue
        m = float(getattr(e, "masa", 0) or 0)
        if m < 500.0:
            continue
        ex = float(getattr(e, "grid_x", 0) or 0)
        ez = float(getattr(e, "grid_y", 0) or 0)
        px = int(ex * scale)
        py = int(ez * scale)
        if 0 <= px < size and 0 <= py < size:
            r = max(1, int(min(4, m / 2000.0)))
            color = (255, 200, 60)  # gigante = dorado
            pygame.draw.circle(s, color, (px, py), r)
    # la propia SIEMPRE visible: blanco brillante
    px = int(cx * scale)
    py = int(cz * scale)
    if 0 <= px < size and 0 <= py < size:
        pygame.draw.circle(s, (255, 255, 255), (px, py), 4)
        pygame.draw.circle(s, (0, 200, 255), (px, py), 6, 1)
    surf.blit(s, (x, y))
    lbl = rc(_get_font_tiny(), "MAPA", True, DIM)
    surf.blit(lbl, (x + 6, y + 4))


def _safe(v, d):
    try:
        return float(v) if v is not None else d
    except Exception:
        return d


def _get_font_tiny():
    # cache el font a 18 una vez (lo pasa el caller como font_tiny pero esta
    # funcion puede ser llamada desde draw_minimap sin contexto — la
    # alternativa seria inyectar el font, mejor: import pygame y singleton)
    import pygame as _pg
    global _TINY_FONT
    try:
        return _TINY_FONT
    except NameError:
        _TINY_FONT = _pg.font.Font(None, 16)
        return _TINY_FONT


def draw_stats_bar(surf, x, y, w, h, font_tiny, fps, ping_ms, server, pings):
    """Barra de estado superior derecha: FPS, PING ms, servidor, pings."""
    items = [
        ("FPS", "%d" % int(fps), TEXT if fps >= 55 else (GOLD if fps >= 30 else DANGER)),
        ("PING", "%dms" % int(ping_ms), TEXT if ping_ms <= 80 else (GOLD if ping_ms <= 200 else DANGER)),
        ("SRV", server.upper(), DIM),
        ("PINGS", "%d" % pings, DIM),
    ]
    s_ = pygame.Surface((w, h), pygame.SRCALPHA)
    s_.fill((10, 12, 18, 200))
    pygame.draw.rect(s_, (40, 46, 60), s_.get_rect(), 1, border_radius=4)
    surf.blit(s_, (x, y))
    cx = x + 8
    for label, val, col in items:
        lbl_l = rc(font_tiny, label + ":", True, DIM)
        lbl_v = rc(font_tiny, val, True, col)
        surf.blit(lbl_l, (cx, y + (h - lbl_l.get_height()) // 2))
        cx += lbl_l.get_width() + 3
        surf.blit(lbl_v, (cx, y + (h - lbl_v.get_height()) // 2))
        cx += lbl_v.get_width() + 12


def draw_equipment_bar(surf, x, y, slots, font):
    """EquipmentBar del binario: 4 slots."""
    sw, sh, gap = 40, 40, 6
    for i in range(len(slots)):
        sx = x + i * (sw + gap)
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(s, (24, 28, 38, 220), s.get_rect(), border_radius=6)
        pygame.draw.rect(s, (60, 70, 90, 160), s.get_rect(), 1, border_radius=6)
        surf.blit(s, (sx, y))
        item = slots[i]
        if item:
            lbl = rc(font, str(item), True, GOLD)
            surf.blit(lbl, (sx + (sw - lbl.get_width()) // 2, y + 10))


def draw_lobby(surf, font, font_small, font_tiny, state, room, muerto=False, pausa=False,
                sala_edit_state=None, fps=60, ping_ms=0, server="europe", pings=0):
    """fkengine.gui.game.Game — el lobby del binario.

    Geometria compartida con el click handling (constantes L_* del visor):
    MODO (SALAS/CTF/FFA/HVZ), sala, servidor ‹ ›, JUGAR, AUTORESPAWN.
    """
    global MODOS, L_MODE_X0, L_MODE_STEP, L_MODE_Y, L_MODE_W, L_MODE_H
    from client.main import (MODOS, L_MODE_X0, L_MODE_Y, L_MODE_W, L_MODE_H,
                             L_MODE_STEP, L_SALA, L_SRV_IZQ, L_SRV_DER,
                             L_JUGAR, L_AUTORESP)
    from client.main import STATE as _ST
    surf.fill(BG)
    # barra superior: coins + perfil + opciones
    bar = pygame.Surface((W, 52), pygame.SRCALPHA)
    bar.fill((12, 14, 20, 235))
    surf.blit(bar, (0, 0))
    pygame.draw.line(surf, (40, 46, 60), (0, 51), (W, 51), 1)
    draw_btn(surf, 14, 9, 140, 34, "GEMAS: 0", font_small)
    draw_btn(surf, 166, 9, 90, 34, "PERFIL", font_small, accent=DIM)
    draw_btn(surf, W - 250, 9, 100, 34, "OPCIONES", font_small, accent=DIM)
    draw_btn(surf, W - 140, 9, 60, 34, "SONIDO", font_small, accent=DIM)
    draw_btn(surf, W - 70, 9, 56, 34, "?x", font_small, accent=DIM)
    # centro: logo
    logo = rc(font, "MITOSIS", True, TEXT)
    surf.blit(logo, ((W - logo.get_width()) // 2, 120))
    sub = rc(font_small, "OurClient — replica del binario", True, DIM)
    surf.blit(sub, ((W - sub.get_width()) // 2, 175))

    # --- MODO: SALAS / CTF / FFA / HVZ (botones reales del lobby) ---
    modo_act = _ST.lobby_mode
    for i, (mname, mval) in enumerate(MODOS):
        bx = L_MODE_X0 + i * L_MODE_STEP
        act = (mval == modo_act)
        draw_btn(surf, bx, L_MODE_Y, L_MODE_W, L_MODE_H, mname, font_small,
                 accent=ACCENT if act else DIM)
    # --- SALA (solo en modo SALAS) — input box REAL ---
    if modo_act == 0:
        sx0, sy0, sw, sh = L_SALA
        # sala_edit_state viene del main; si no, fallback a la string room
        if sala_edit_state is None:
            sala_state = {"active": False, "text": room, "caret": 0}
        else:
            sala_state = sala_edit_state
        ph = "(sala automatica)" if not sala_state["text"] else ""
        draw_input(surf, sx0, sy0, sw, sh, sala_state["text"], sala_state["caret"],
                   sala_state["active"], font_small, ph)
    # --- SERVIDOR: flechas ‹ › + nombre ---
    srv = _ST.lobby_server
    sx0, sy0, sw, sh = L_SRV_IZQ
    pygame.draw.polygon(surf, DIM, [(sx0 + 4, sy0 + sh // 2), (sx0 + sw - 4, sy0 + 4),
                                    (sx0 + sw - 4, sy0 + sh - 4)])
    sx0, sy0, sw, sh = L_SRV_DER
    pygame.draw.polygon(surf, DIM, [(sx0 + sw - 4, sy0 + sh // 2), (sx0 + 4, sy0 + 4),
                                    (sx0 + 4, sy0 + sh - 4)])
    sl = rc(font_small, "SERVIDOR: " + srv.upper(), True, ACCENT)
    surf.blit(sl, (W // 2 - sl.get_width() // 2, 344))
    # --- AUTORESPAWN toggle ---
    ax, ay, aw, ah = L_AUTORESP
    st = "AUTORESPAWN: " + ("ON" if _ST.autorespawn else "OFF")
    draw_btn(surf, ax, ay, aw, ah, st, font_small,
             accent=GREEN if _ST.autorespawn else DIM)

    # --- JUGAR / REAPARECER / CONTINUAR ---
    jx, jy, jw, jh = L_JUGAR
    if muerto:
        draw_btn(surf, jx, jy, jw, jh, "REAPARECER", font, accent=GREEN)
    elif pausa:
        draw_btn(surf, jx, jy, jw, jh, "CONTINUAR", font)
    else:
        draw_btn(surf, jx, jy, jw, jh, "JUGAR", font)
    if room:
        rl = rc(font_small, "SALA: " + room, True, DIM)
        surf.blit(rl, ((W - rl.get_width()) // 2, 460))
    # estado de conexion
    st = rc(font_tiny, state.upper(), True, DIM)
    surf.blit(st, (14, H - 30))
    # stats bar siempre visible tambien en el lobby (FPS/server/pings)
    draw_stats_bar(surf, W - 290, H - 32, 220, 22, font_tiny, fps, ping_ms, server, pings)


def draw_hud(surf, font, font_small, snap, view, font_tiny=None,
             fps=60, ping_ms=0, server="europe", pings=0):
    """fkengine.gui.game.CurrentPlayingView — el HUD en juego."""
    if font_tiny is None:
        font_tiny = font_small  # fallback si el caller no lo pasa
    w = view.world
    # --- stats bar (FPS/PING/SRV/PINGS) esquina superior derecha ---
    # la stats bar termina en X = (W - 290) + 220 = W - 70; el leaderboard
    # empieza en W - 230 (= 160px del borde derecho). NO se solapan.
    draw_stats_bar(surf, W - 290, 8, 220, 22, font_tiny, fps, ping_ms, server, pings)
    # --- minimapa esquina superior izquierda ---
    draw_minimap(surf, view, 14, 38, 110)
    # --- leaderboard lateral (Leaderboard + LeaderboardSlot) ---
    lb = w.leaderboard
    # masa real por entidad
    rows = []
    for eid, info in lb.items():
        e = w.entities.get(eid)
        rows.append((eid, info.get("name") or "", e.masa if e else 0))
    rows.sort(key=lambda r: -r[2])
    # el leaderboard empieza mas abajo para no chocar con la stats bar
    px = W - 230
    LB_TOP = 44  # debajo de la stats bar (8+26+10)
    ph = min(400, 34 + len(rows) * 22)
    panel = pygame.Surface((220, ph), pygame.SRCALPHA)
    panel.fill((10, 12, 18, 200))
    surf.blit(panel, (px, LB_TOP))
    pygame.draw.rect(surf, (40, 46, 60), (px, LB_TOP, 220, ph), 1)
    ttl = rc(font_small, "CLASIFICACION", True, ACCENT)
    surf.blit(ttl, (px + 10, LB_TOP + 6))
    my_id = w.player_entity_id
    for i, (eid, name, masa) in enumerate(rows[:14]):
        col = GOLD if eid == my_id else TEXT
        row = rc(font_small, "%2d  %s" % (i + 1, (name or "jugador %d" % eid)), True, col)
        surf.blit(row, (px + 10, LB_TOP + 30 + i * 22))
        mv = rc(font_small, "%d" % int(masa), True, DIM)
        surf.blit(mv, (px + 200 - mv.get_width(), LB_TOP + 30 + i * 22))
    # --- score arriba (bestScore) ---
    score = int(w.score)
    sc = rc(font, "%d" % score, True, TEXT)
    surf.blit(sc, ((W - sc.get_width()) // 2, 12))
    # --- masa ---
    # la masa REAL de la propia (ultima conocida): cuando la identificacion
    # fluctua, main_cell cae a la celula virtual (masa 10.0 = imposible en
    # el juego real) o None (0) — mostrar la virtual confunde al usuario.
    # own_mass se actualiza con el CLEAR/owner==account_id de la propia.
    main = w.main_cell
    m_raw = (main.masa if main and main.masa
             and main.masa > 1.0
             else (w.own_mass if w.own_mass > 1.0 else 0))
    masa = int(m_raw)
    ml = rc(font_small, "MASA: %d" % masa, True, TEXT)
    surf.blit(ml, (14, 12))
    # --- XP bar abajo ---
    draw_xp_bar(surf, W // 2 - 220, H - 44, 440, 22, 1, 0, 100, font_small)
    # --- SPLIT / EJECT (splitButton/ejectButton del MouseInputManager) ---
    draw_btn(surf, W - 235, H - 90, 105, 44, "SPLIT [SPACE]", font_small)
    draw_btn(surf, W - 122, H - 90, 100, 44, "EJECT [W]", font_small, accent=GREEN)
