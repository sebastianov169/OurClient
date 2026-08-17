"""
MoveableEntity — réplica literal del binario (fkengine.game.entities.MoveableEntity).

Fuente: Ghidra MCP, re/decomp_mov/MoveableEntity_init.c (FUN_1414c50d0).
Clase intermedia entre GameEntity y PlayerEntity (herencia Haxe).

init: nombre "MoveableEntity", tamano 0xe.
"""

from client.engine.game_entity import GameEntity


class MoveableEntity(GameEntity):
    def __init__(self, eid=0, entityType=1):
        super().__init__(eid, entity_type)
        # campos de MoveableEntity (dispatcher FUN_1414c8820/B):
        self._shape = None     # case 5: param_1[0x23] "_shape"
        self._shape2 = None    # case 6: param_1[0x1f] "_shape2"
        self._asset = None     # case 6: param_1[0x24] "_asset"
