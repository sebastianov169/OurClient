"""
Entidades del binario MitosisOG.exe — portadas a client/entities/.

Fábrica FUN_14073b220: entityType (ent+0x28) -> clase.
Paletas reales .rdata: CELL_COLORS 0x141d167c0 (8), TEAM_COLORS 0x141d16830
(4), FOOD_COLORS 0x141d16860 (7). entityColor = paleta[id % len].
"""

from client.engine.game_entity import GameEntity, radio_from_masa

# Paletas REALES del binario (.rdata, read_memory Ghidra)
CELL_COLORS = (0x66CCFF, 0xFF66FF, 0x6666FF, 0x66CCFF,
               0x66FF99, 0xFFFF66, 0xFFCC66, 0xFF6666)   # 0x141d167c0 (8)
TEAM_COLORS = (0xFF6666, 0x66CCFF, 0xFFCC66, 0x66FF99)    # 0x141d16830 (4)
FOOD_COLORS = (0xFF07CA, 0xFF071D, 0x1DFF3F, 0xFF8807,
               0x5A07FF, 0x07F9FF, 0xBFFF07)              # 0x141d16860 (7)


def _hex_to_rgb(c):
    return ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)


CELL_RGB = [_hex_to_rgb(c) for c in CELL_COLORS]
TEAM_RGB = [_hex_to_rgb(c) for c in TEAM_COLORS]
FOOD_RGB = [_hex_to_rgb(c) for c in FOOD_COLORS]

# entityType (fabrica FUN_14073b220, ent+0x28)
ET_FOOD = 1
ET_PLAYER = 2
ET_FLOATING = 3
ET_VIRUS = 4
ET_COIN = 5
ET_FLAG_BASE = 6
ET_CHEST = 7
ET_CUSTOM = 8
ET_IMAGE = 9
ET_DIAMOND = 11
ET_CONQUERABLE = 12
ET_SNAKES_PLAYER = 13
ET_SKINNED_PLAYER = 14
ET_SPRITE = 15


def entity_color(entity_id, palette):
    """entityColor = _randomColors[_id % len] (GameEntity.as L650-652)."""
    return palette[entity_id % len(palette)]


class FoodEntity(GameEntity):
    """FoodEntity: _size = 1 fijo (FUN_14066e490: *(ent+0x12) = 1)."""

    def __init__(self, eid):
        super().__init__(eid, ET_FOOD)
        self.size = 1
        self.color = entity_color(eid, FOOD_RGB)


class VirusEntity(GameEntity):
    """VirusEntity (entityType 4): verde con pinchos en el render."""

    def __init__(self, eid):
        super().__init__(eid, ET_VIRUS)
        self.color = entity_color(eid, CELL_RGB)


class CoinEntity(GameEntity):
    """CoinEntity (entityType 5): dorada en el render."""

    def __init__(self, eid):
        super().__init__(eid, ET_COIN)
        self.color = entity_color(eid, CELL_RGB)


class FlagBaseEntity(GameEntity):
    """FlagBaseEntity (entityType 6): bases CTF con color de equipo."""

    def __init__(self, eid):
        super().__init__(eid, ET_FLAG_BASE)
        self.team = 0
        self.color = entity_color(eid, TEAM_RGB)


ENTITY_FACTORY = {
    ET_FOOD: FoodEntity,
    ET_PLAYER: None,  # PlayerEntity en client/entities/player_entity.py
    ET_VIRUS: VirusEntity,
    ET_COIN: CoinEntity,
    ET_FLAG_BASE: FlagBaseEntity,
}


def build_entity(eid, entity_type):
    """Fabrica FUN_14073b220: crea la clase segun entityType (ent+0x28)."""
    from client.entities.player_entity import PlayerEntity
    cls = ENTITY_FACTORY.get(entity_type)
    if cls is None:
        cls = PlayerEntity if entity_type == ET_PLAYER else GameEntity
    if cls in (GameEntity,):
        return cls(eid, entityType=entity_type)
    return cls(eid)
