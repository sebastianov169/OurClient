"""
Geometria del binario — réplica literal (fkengine.geometries.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados 2026-08-14).

    PointSet              (FUN_140639e30, vtable DAT_1421b8dc8, ctor FUN_14063a110)
    CircleGraphics        (FUN_140642050, vtable DAT_1421b8dd0, ctor FUN_140642700)
    BatchedCircleGraphicsList (FUN_141467c10, vtable DAT_1421bab88, ctor FUN_141467dd0)
    BatchedCircleGraphics (FUN_14146b2e0, vtable DAT_1421bab90, ctor FUN_14146b540)
"""


class PointSet:
    """fkengine.geometries.PointSet (FUN_14063a110) — conjunto de puntos."""

    def __init__(self):
        self.points = []  # [(x, y, z), ...]

    def add(self, x, y, z=0.0):
        self.points.append((x, y, z))

    def clear(self):
        self.points = []

    def __len__(self):
        return len(self.points)


class CircleGraphics:
    """fkengine.geometries.CircleGraphics (FUN_140642700) — circulo renderizable.

    Es la primitiva con la que el binario dibuja las celulas (radio, color,
    posicion). El visor pygame la emula con pygame.draw.circle."""

    def __init__(self, x=0.0, y=0.0, radius=1.0, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.visible = True
        self.z = 0.0  # zOrder = size/masa (sortByZOrder FUN_140a24c70)

    def set_position(self, x, y):
        self.x, self.y = x, y

    def set_radius(self, r):
        self.radius = r

    def set_color(self, c):
        self.color = c


class BatchedCircleGraphics:
    """fkengine.geometries.BatchedCircleGraphics (FUN_14146b540) — circulo
    en el batch de render (mismo formato que CircleGraphics pero agrupado)."""

    def __init__(self):
        self.circles = []

    def add(self, circle):
        self.circles.append(circle)

    def clear(self):
        self.circles = []


class BatchedCircleGraphicsList:
    """fkengine.geometries.BatchedCircleGraphicsList (FUN_141467dd0) — lista
    de batches (los del mundo + los del jugador + la comida...)."""

    def __init__(self):
        self.batches = []

    def add_batch(self, batch):
        self.batches.append(batch)

    def clear(self):
        self.batches = []
