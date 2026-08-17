"""
ScoreLabel y extras — réplica literal (fkengine.game.ScoreLabel, VectorInt).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).
"""


class ScoreLabel:
    """fkengine.game.ScoreLabel — etiqueta de puntuacion flotante
    (el "+N" que sale al comer)."""

    def __init__(self, value=0, x=0.0, z=0.0):
        self.value = value
        self.x, self.z = x, z
        self.lifetime = 1.5
        self.elapsed = 0.0
        self.visible = True

    def tick(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.lifetime:
            self.visible = False

    @property
    def alpha(self):
        return max(0.0, 1.0 - self.elapsed / self.lifetime)


class VectorInt:
    """fkengine.game.VectorInt — vector de enteros (util del juego)."""

    def __init__(self, x=0, y=0):
        self.x, self.y = x, y

    def __repr__(self):
        return "VectorInt(%d, %d)" % (self.x, self.y)
