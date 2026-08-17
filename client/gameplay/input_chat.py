"""
Input y chat del binario — réplica literal (fkengine.game.input / gamepad /
chat / leaderboards).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados 2026-08-14).

    GenericInputManager   (FUN_14064e7d0, vtable DAT_1421c16a8,
                           ctor FUN_14064ec50, metodos FUN_140644e40/4f00)
    GamepadButtons        (FUN_140642810, vtable DAT_1421c1660,
                           ctor FUN_140642a70, metodos FUN_140642760)
    Errors                (FUN_140680ed0, fkengine.game.data.Errors)
    InGameChatBalloon     (FUN_140683570, vtable DAT_1421b9118)
    LeaderboardStrikeViewItem (FUN_1406443b0)
    DownloaderAsset       (FUN_1406804e0, vtable DAT_1421b8f70)
"""


class GenericInputManager:
    """fkengine.game.input.GenericInputManager (FUN_14064ec50)."""

    def __init__(self):
        self.visible = True
        self.enabled = True
        self._touch = None
        self._keyboard = None

    def process(self):
        """slot 0x100: procesa el input del frame."""
        pass

    def touchReceived(self, x, y):
        self._touch = (x, y)

    def keyPressed(self, key, pressed):
        if self._keyboard:
            self._keyboard(key, pressed)


class GamepadButtons:
    """fkengine.gamepad.GamepadButtons (FUN_140642a70) — botones del gamepad."""

    # botones (como el binario: mapeo por nombre en el dispatcher)
    A = 1
    B = 2
    X = 4
    Y = 8
    LB = 0x10
    RB = 0x20

    def __init__(self):
        self.state = 0

    def press(self, button):
        self.state |= button

    def release(self, button):
        self.state &= ~button

    def is_down(self, button):
        return bool(self.state & button)


class Errors:
    """fkengine.game.data.Errors — errores del juego."""

    NONE = 0
    NOT_CONNECTED = 1
    TIMEOUT = 2
    SERVER_CLOSED = 3


class InGameChatBalloon:
    """fkengine.game.chat.InGameChatBalloon (FUN_140683570) — globo de chat."""

    def __init__(self, sender="", message=""):
        self.sender = sender
        self.message = message
        self.visible = False
        self.lifetime = 0.0

    def show(self, sender, message, lifetime=5.0):
        self.sender = sender
        self.message = message
        self.lifetime = lifetime
        self.visible = True

    def update(self, dt):
        if self.visible:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.visible = False


class LeaderboardStrikeViewItem:
    """fkengine.game.leaderboards.leaderboardstrike.LeaderboardStrikeViewItem
    (FUN_1406443b0) — item del leaderboard."""

    def __init__(self, rank=0, name="", score=0.0):
        self.rank = rank
        self.name = name
        self.score = score
