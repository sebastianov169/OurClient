"""
Pantallas GUI del binario — réplica literal (fkengine.gui.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    Achievements       — logros
    ActiveStatus       — estado activo (vida, buffs)
    BattlePass         — pase de batalla
    BattleTag          — etiqueta de batalla
    ChangeLanguage     — cambio de idioma
    ChangeResolution   — cambio de resolucion
    ChangeFramerate    — cambio de fps
    AttachFacebook     — vincular Facebook
"""


class Achievements:
    """fkengine.gui.achievements.Achievements — logros."""

    def __init__(self):
        self.items = []
        self.unlocked = set()

    def add(self, item):
        self.items.append(item)

    def unlock(self, achievement_id):
        self.unlocked.add(achievement_id)


class AchievementsItem:
    """Item de logro."""

    def __init__(self, aid="", name="", progress=0.0):
        self.id = aid
        self.name = name
        self.progress = progress


class ActiveStatusBase:
    """fkengine.gui.activestatus.ActiveStatusBase — base."""

    def __init__(self):
        self.visible = False


class ActiveStatus(ActiveStatusBase):
    """fkengine.gui.activestatus.ActiveStatus — estado activo."""

    def __init__(self):
        super().__init__()
        self.status = 0
        self.duration = 0.0


class LifeIndicatorBlock:
    """Bloque del indicador de vida."""

    def __init__(self, filled=True):
        self.filled = filled


class BattlePass:
    """fkengine.gui.battlepass.BattlePass — pase de batalla."""

    def __init__(self):
        self.level = 0
        self.xp = 0
        self.items = []

    def add_xp(self, xp):
        self.xp += xp


class BattlePassItem:
    """Item del pase."""

    def __init__(self, level=0, reward=None):
        self.level = level
        self.reward = reward


class BattleTag:
    """fkengine.gui.battletag.BattleTag — etiqueta de batalla."""

    def __init__(self, tag=""):
        self.tag = tag


class ChangeLanguage:
    """Cambio de idioma."""

    def __init__(self, current="es"):
        self.current = current
        self.languages = ["es", "en", "pt", "de", "fr"]


class ChangeResolution:
    """Cambio de resolucion."""

    RESOLUTIONS = [(1280, 720), (1600, 900), (1920, 1080)]

    def __init__(self, current=0):
        self.current = current

    def apply(self, index):
        self.current = index % len(self.RESOLUTIONS)
        return self.RESOLUTIONS[self.current]


class ChangeFramerate:
    """Cambio de fps."""

    def __init__(self, fps=60):
        self.fps = fps


class AttachFacebook:
    """Vincular Facebook."""

    def __init__(self):
        self.attached = False
