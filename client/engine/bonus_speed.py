"""
BonusSpeed / MaxSpeed — réplica literal del binario.

Fuente: Ghidra MCP, re/decomp_mov/BonusSpeed_*.c, MaxSpeed_*.c.
"""


class BonusSpeed:
    """Objeto de bonus de velocidad (+0x2b0 del MouseInputManager).

    start = slot 0x28, end = slot 0x30 (MIM_startSpeedup/endSpeedup).
    Campos del dispatcher (FUN_141422710): _name en +0xd8, _altar en +0x160.
    """

    def __init__(self):
        self.active = False
        self.multiplier = 1.0
        self.name = None       # +0xd8 (_name)
        self.altar = None      # +0x160 (_altar)

    def start(self):
        self.active = True

    def end(self):
        self.active = False


class MaxSpeed:
    """MaxSpeed del binario (config +0x388 del View, ~400)."""

    def __init__(self, value=400.0):
        self.value = value

    def get(self):
        return self.value
