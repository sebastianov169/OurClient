"""
Utils del binario — réplica literal (fkengine.utils.*).

Fuente: Ghidra MCP (classregs decompilados).

    MersenneTwister (FUN_141314560, vtable DAT_1421ba890, ctor FUN_141314720)
        — el RNG del cliente (seed del server para desturple/encoding).
    QuickArray      (FUN_14130d970)
    NumberUtil, ArrayUtil, FloatExtender, StringExtender, Percent
"""


class MersenneTwister:
    """fkengine.utils.MersenneTwister — MT19937 del binario.

    ctor: FUN_141314720 (hash 0x6e141979), alloc 0x28 (624 u32 + idx).
    El server manda la seed (greeting suffix) y el cliente genera las
    seeds de encoding desturple con este generador.
    """

    N = 624
    M = 397
    MATRIX_A = 0x9908B0DF
    UPPER_MASK = 0x80000000
    LOWER_MASK = 0x7FFFFFFF

    def __init__(self, seed=5489):
        self.mt = [0] * self.N
        self.mti = self.N + 1
        self.seed(seed)

    def seed(self, s):
        self.mt[0] = s & 0xFFFFFFFF
        for i in range(1, self.N):
            self.mt[i] = (1812433253 * (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) + i) & 0xFFFFFFFF
        self.mti = self.N

    def next_u32(self):
        if self.mti >= self.N:
            self._twist()
        y = self.mt[self.mti]
        self.mti += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        return y & 0xFFFFFFFF

    def _twist(self):
        for i in range(self.N):
            y = (self.mt[i] & self.UPPER_MASK) | (self.mt[(i + 1) % self.N] & self.LOWER_MASK)
            self.mt[i] = self.mt[(i + self.M) % self.N] ^ (y >> 1)
            if y & 1:
                self.mt[i] ^= self.MATRIX_A
        self.mti = 0

    def next_float(self):
        """float en [0,1) — como lo usa el binario para random()."""
        return self.next_u32() / 4294967296.0


class QuickArray:
    """fkengine.utils.QuickArray — array rapido del binario."""

    def __init__(self):
        self._data = []

    def push(self, v):
        self._data.append(v)

    def pop(self):
        return self._data.pop() if self._data else None

    def get(self, i):
        return self._data[i] if 0 <= i < len(self._data) else None

    def __len__(self):
        return len(self._data)
