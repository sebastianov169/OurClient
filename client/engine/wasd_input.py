"""
Input por teclado del binario — réplica literal
(fkengine.game.input.WASDKeyView / WASDView / SingleJoystickInputManager).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    WASDKeyView  — vista de teclas WASD
    WASDView     — vista WASD (movimiento con teclado)
    SingleJoystickInputManager — joystick unico (movil)
"""


class WASDKeyView:
    """fkengine.game.input.WASDKeyView — vista de teclas WASD."""

    def __init__(self):
        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.visible = False

    def key_down(self, key):
        k = key.lower()
        if k in self.keys:
            self.keys[k] = True

    def key_up(self, key):
        k = key.lower()
        if k in self.keys:
            self.keys[k] = False

    @property
    def direction(self):
        """Direccion normalizada del WASD (x, z)."""
        x = (1.0 if self.keys["d"] else 0.0) - (1.0 if self.keys["a"] else 0.0)
        z = (1.0 if self.keys["s"] else 0.0) - (1.0 if self.keys["w"] else 0.0)
        if x == 0.0 and z == 0.0:
            return (0.0, 0.0)
        import math
        d = math.hypot(x, z)
        return (x / d, z / d)


class WASDView:
    """fkengine.game.input.WASDView — vista WASD."""

    def __init__(self):
        self.key_view = WASDKeyView()
        self.active = False


class SingleJoystickInputManager:
    """fkengine.game.input.SingleJoystickInputManager — joystick unico."""

    def __init__(self):
        self.x = 0.0
        self.z = 0.0
        self.active = False

    def update(self, x, z):
        self.x, self.z = x, z
        self.active = True

    def clear(self):
        self.x, self.z = 0.0, 0.0
        self.active = False
