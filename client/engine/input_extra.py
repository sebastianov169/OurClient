"""
Gremios y entrada — réplica literal (fkengine.game.gw.*, input restante).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    GuildWarManager         — guerra de gremios
    JoystickInputManager    — input por joystick (updateJoystickPosition)
    AccelerometerInputManager — input por acelerometro (movil)
    IInputReceiver          — interfaz de input
"""


class GuildWarManager:
    """fkengine.game.gw.GuildWarManager — guerra de gremios."""

    def __init__(self):
        self.war_active = False
        self.guilds = {}

    def set_war(self, active):
        self.war_active = active


class IInputReceiver:
    """fkengine.game.input.IInputReceiver — interfaz de input."""

    def on_touch(self, x, y):
        pass

    def on_key(self, key, pressed):
        pass


class JoystickInputManager(IInputReceiver):
    """fkengine.game.input.JoystickInputManager — joystick
    (updateJoystickPosition_impl FUN_1414a9510 -> FUN_1414a94a0)."""

    def __init__(self):
        self.x = 0.0
        self.z = 0.0
        self.active = False

    def update(self, x, z):
        self.x, self.z = x, z
        self.active = True


class AccelerometerInputManager(IInputReceiver):
    """fkengine.game.input.AccelerometerInputManager — acelerometro (movil)."""

    def __init__(self):
        self.ax = 0.0
        self.az = 0.0

    def update(self, ax, az):
        self.ax, self.az = ax, az
