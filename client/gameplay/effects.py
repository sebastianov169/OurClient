import math
"""
Efectos del juego — réplica literal (fkengine.game.effects.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    EntityEffect  (FUN_1414d3080)  — efecto base de entidad
    Displacement  (FUN_1414d1010)  — desplazamiento
    Dislocation   (FUN_1414d21e0)  — dislocacion
    FluidBorder   (FUN_1414cfc60)  — borde fluido (de la celula)
    Tremolio      (FUN_1414cd560)  — temblor (get_tremolio slot 0x1d8)
"""


class EntityEffect:
    """fkengine.game.effects.EntityEffect — efecto base de entidad."""

    def __init__(self, entity=None):
        self.entity = entity
        self.active = False
        self.duration = 0.0
        self.elapsed = 0.0

    def apply(self, entity):
        self.entity = entity
        self.active = True
        self.elapsed = 0.0

    def tick(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.duration > 0 and self.elapsed >= self.duration:
            self.active = False


class Displacement(EntityEffect):
    """Desplazamiento de la entidad."""

    def __init__(self, entity=None, dx=0.0, dz=0.0):
        super().__init__(entity)
        self.dx, self.dz = dx, dz

    def tick(self, dt):
        if self.active and self.entity is not None:
            self.entity.grid_x += self.dx * dt
            self.entity.grid_y += self.dz * dt
        super().tick(dt)


class Dislocation(EntityEffect):
    """Dislocacion (posicion visual distinta de la real)."""

    def __init__(self, entity=None, offset_x=0.0, offset_z=0.0):
        super().__init__(entity)
        self.offset_x, self.offset_z = offset_x, offset_z


class FluidBorder(EntityEffect):
    """Borde fluido de la celula (slot 0x1d8 get_tremolio / fluid)."""

    def __init__(self, entity=None, fluid=0.0):
        super().__init__(entity)
        self.fluid = fluid


class Tremolio(EntityEffect):
    """Temblor de la entidad (get_tremolio del dispatcher GameEntity)."""

    def __init__(self, entity=None, amplitude=0.0):
        super().__init__(entity)
        self.amplitude = amplitude
        self.phase = 0.0

    def tick(self, dt):
        if self.active and self.entity is not None:
            self.phase += dt * 10.0
            self.entity.grid_x += math.sin(self.phase) * self.amplitude * 0.01
            self.entity.grid_y += math.cos(self.phase) * self.amplitude * 0.01
        super().tick(dt)
