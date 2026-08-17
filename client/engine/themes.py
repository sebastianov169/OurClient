"""
Temas del binario — réplica literal (fkengine.themes.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    BaseMetalWorksMobileTheme — tema base (metal works, movil)
    MetalWorksMobileTheme      — tema metal works
    BattlesTheme               — tema de batallas
    ThemeManager               — gestor de temas
    SoundManager               — gestor de sonido
"""


class Theme:
    """Tema base."""

    NAME = "base"
    COLORS = {}

    def __init__(self):
        self.palette = dict(self.COLORS)

    def color(self, key, default=(255, 255, 255)):
        return self.palette.get(key, default)


class MetalWorksMobileTheme(Theme):
    """fkengine.themes.MetalWorksMobileTheme — tema metal works (movil)."""

    NAME = "metalworks"
    COLORS = {
        "bg": (18, 20, 28),
        "accent": (0, 200, 255),
        "text": (230, 235, 245),
    }


class BaseMetalWorksMobileTheme(Theme):
    """Base del tema metal works."""

    NAME = "metalworks_base"
    COLORS = {
        "bg": (10, 12, 18),
        "panel": (16, 18, 26),
        "accent": (0, 190, 250),
    }


class BattlesTheme(Theme):
    """fkengine.themes.BattlesTheme — tema de batallas."""

    NAME = "battles"
    COLORS = {
        "bg": (24, 10, 16),
        "accent": (255, 48, 113),
        "text": (245, 230, 235),
    }


class ThemeManager:
    """fkengine.sound.theme.ThemeManager — gestor de temas."""

    def __init__(self):
        self.themes = {}
        self.current = None

    def register(self, theme):
        self.themes[theme.NAME] = theme

    def set(self, name):
        self.current = self.themes.get(name)

    def get(self, name=None):
        if name:
            return self.themes.get(name)
        return self.current


class SoundManager:
    """fkengine.sound.SoundManager — gestor de sonido."""

    def __init__(self):
        self.volume_master = 1.0
        self.volume_music = 1.0
        self.volume_sfx = 1.0

    def set_master(self, v):
        self.volume_master = max(0.0, min(1.0, v))

    def set_music(self, v):
        self.volume_music = max(0.0, min(1.0, v))

    def set_sfx(self, v):
        self.volume_sfx = max(0.0, min(1.0, v))
