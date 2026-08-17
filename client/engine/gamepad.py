"""
Gamepad nativo — réplica literal (fkengine.gamepad.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    GamepadButtons       — botones del gamepad (en gameplay/input_chat.py)
    INativeGamepad       — gamepad nativo
    INativeGamepadReceiver — receptor de eventos del gamepad
"""


class INativeGamepad:
    """fkengine.gamepad.INativeGamepad — gamepad nativo."""

    def __init__(self):
        self.connected = False
        self.axes = [0.0, 0.0]

    def update(self, dt):
        pass


class INativeGamepadReceiver:
    """fkengine.gamepad.INativeGamepadReceiver — receptor."""

    def on_button(self, button, pressed):
        pass

    def on_axis(self, axis, value):
        pass
