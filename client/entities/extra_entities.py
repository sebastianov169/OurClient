"""
Entidades adicionales — réplica literal (fkengine.game.entities.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    FlagCarrierEntity      (FUN_1414c2010) — portador de bandera (CTF)
    VariousImage           (FUN_1414bd010) — imagen variada (skins)
    ParticleGroupContainer (clase vecina)  — contenedor de grupos de particulas
"""

from client.engine.game_entity import GameEntity


class FlagCarrierEntity(GameEntity):
    """fkengine.game.entities.FlagCarrierEntity — portador de la bandera CTF."""

    def __init__(self, eid=0):
        super().__init__(eid, entityType=6)
        self.team = 0
        self.carrier = None  # entidad que lleva la bandera


class VariousImage(GameEntity):
    """fkengine.game.entities.VariousImage — imagen variada (skins/items)."""

    def __init__(self, eid=0):
        super().__init__(eid, entityType=8)
        self.texture = None


class ParticleGroupContainer(GameEntity):
    """fkengine.game.entities.ParticleGroupContainer — grupo de particulas
    (attachParticleGroup slot del dispatcher GameEntity)."""

    def __init__(self, eid=0):
        super().__init__(eid, entityType=3)
        self.particles = []
