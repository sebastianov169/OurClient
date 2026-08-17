"""
Extrapolation — réplica literal del binario (fkengine.game.Extrapolation).

Fuente: Ghidra MCP, re/decomp_mov/Extrapolation_*.c.
init (FUN_1414ecdb0): nombre "Extrapolation", tamano 0xd.
full_init (FUN_1414ed600): clase registrada con vtable + campos por nombre
(DAT_1420f66c0).

Es el objeto de VELOCIDAD que PlayerEntity usa en +0x58: el array +0x10
tiene vx en +0xc y vz en +0x14 (ver PE_applyExtrapolation_REAL).
"""


class Extrapolation:
    def __init__(self):
        # +0x10: array de floats (vx en +0xc, vz en +0x14)
        self.array = [0.0, 0.0, 0.0]
        self.vx = 0.0   # espejo de array[0xc/4] = array[3]
        self.vz = 0.0   # espejo de array[0x14/4] = array[5]

    def get_vx(self):
        return self.array[3]

    def get_vz(self):
        return self.array[5]

    def set_velocity(self, vx, vz):
        self.array[3] = vx
        self.array[5] = vz
        self.vx = vx
        self.vz = vz
