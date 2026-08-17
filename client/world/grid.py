"""
Grid — réplica literal del binario (fkengine.game.Grid).

Fuente: Ghidra MCP, FUN_1406f6e30 (classreg, decomp en re/_decomp_1406f6e30.txt).

El Grid es el MUNDO: crea el View (fkengine.gui.View, FUN_140a225a0) y un
Player por slot (param_1+0x67, FUN_140683830 con "fkengine.game.Player").
Usa DAT_1421b9328 (vtable) y FUN_140924140 (GRID_SIZE, decompilada antes).

Metodos (llamados por slot 0x68 del objeto):
    FUN_1406f9c70, FUN_1406fa5a0, FUN_1406faed0, FUN_1406fb800,
    FUN_1406fc130, FUN_1406fca60, FUN_1406fd3c0, FUN_1406fdcf0,
    FUN_1406fe650, FUN_1406fef80, FUN_1406ff8e0
"""

from client.engine.game_entity import GameEntity  # noqa: F401 (herencia del mundo)


class Grid:
    """El mundo del juego (Grid)."""

    # tamanos reales (FUN_140924140 lee GRID_SIZE de la config del server)
    WIDTH = 16384.0
    HEIGHT = 16384.0

    def __init__(self):
        # param_1 + 0x60: id de la sala
        self.room_id = 0
        # param_1 + 0x67: slots de jugadores (uno por slot)
        self.player_slots = []
        # param_1 + 0x6a/0x6b: contenedores de jugadores
        self.players_by_id = {}
        # el View (fkengine.gui.View) que renderiza el mundo
        self.view = None
        # param_1 + 0x651: flag (modo?)
        self.flag_651 = 0

    def add_player_slot(self, player):
        """Crea un Player por slot (FUN_140683830 + FUN_140685870)."""
        self.player_slots.append(player)
        self.players_by_id[player.pid] = player

    def in_bounds(self, x, z):
        """Clamp a boundaries (el binario clamp a [0, GRID_SIZE+8-1])."""
        return 0 <= x < self.WIDTH and 0 <= z < self.HEIGHT
