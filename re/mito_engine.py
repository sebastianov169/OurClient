#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mito_engine.py - Replica del ENGINE de MitosisOG.exe en Python.

Copia literal de las clases y funciones del binario (Ghidra, base 0x140000000),
fuente: re/pc_analysis/hallazgos_entidades_paleta_leaderboard.md,
re/protocolo_haxe_fisica_movimiento.md y decompilados re/_decomp_*.txt.

CLASES DEL BINARIO (fabrica FUN_14073b220, entityType en ent+0x28):
  1=FoodEntity 2=PlayerEntity 3=FloatingEntity 4=VirusEntity 5=CoinEntity
  6=FlagBaseEntity 7=ChestEntity 8=CustomEntity 9=ImageEntity
  11=DiamondEntity 12=ConquerableEntity 13=SnakesPlayerEntity
  14=SkinnedPlayerEntity 15=SpriteEntity

FUNCIONES COPIA:
  - setMassAndRadius = FUN_140677760: radio = floor(sqrt(masa)*10+0.5)+1
    (el +1 lo aplica setRadius, slot vtable 0x1c8)
  - get_speed = FUN_140677ff0: constante 0.2 (0x3fc999999999999a)
  - applyForce (PlayerEntity slot +0x1a8) = FUN_1414c7e40: dir en +0x100,
    force en +0x108
  - applyExtrapolation (slot +0x1b0) = FUN_1414c7ec0: pos += delta
  - updateMouse core = FUN_1414a8d20: dir normalizada, force =
    sqrt(clamp(dist/maxSpeed,0,1)), velocidad dir*clamp(dist,maxSpeed,
    3*maxSpeed)/(size*2), suavizado pos += (target-pos)*0.25
  - applyPositionInterpolated = FUN_1406790f0:
    x = x_actual + (x_target - x_actual)*alpha; rot wrap 2*pi
  - entityColor = _randomColors[_id % len(_randomColors)] (GameEntity.as L650)
  - interpolacion de masa (frame 60fps): masa += (target-masa)/3.0 (FUN_140795df0)
"""
import math

# ============================================================
# PALETAS REALES del binario (.rdata, verificadas con read_memory)
# ============================================================
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

# entityType del binario (fabrica FUN_14073b220)
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


def radio_from_masa(masa):
    """setMassAndRadius = FUN_140677760 (re/_d_140677760.txt L17-25).

    dVar2 = floor(sqrt(masa)*10 + 0.5); setRadius(dVar2 + 1)
    -> radio final = floor(sqrt(m)*10 + 0.5) + 1
    """
    if masa <= 0:
        return 0.0
    return math.floor(math.sqrt(masa) * 10.0 + 0.5) + 1


def wrap_2pi(a):
    """wrap de angulo a [0, 2*pi) (FUN_1406790f0 usa ±6.283185307179586)."""
    TWO_PI = 6.283185307179586
    while a < 0.0:
        a += TWO_PI
    while a >= TWO_PI:
        a -= TWO_PI
    return a


class GameEntity(object):
    """GameEntity del binario (GameEntity.as; campos ent+0x28/0x90/0xc0).

    - entityType en +0x28 (int, de la fabrica FUN_14073b220)
    - _size en +0x90 (comida=1 fijo)
    - masa (double) en +0xc0
    - radio via setRadius (slot vtable 0x1c8)
    - color via slot vtable 0x188
    - get_speed = FUN_140677ff0 -> 0.2 constante
    - entityColor = _randomColors[_id % len] (GameEntity.as L650-652)
    """
    def __init__(self, eid, entity_type=ET_FOOD):
        self.id = eid
        self.entityType = entity_type      # ent+0x28
        self.size = 1 if entity_type == ET_FOOD else 0   # ent+0x90
        self.masa = 0.0                    # ent+0xc0 (double)
        self.radio = 0.0                   # via setRadius
        self.x = None                     # posicion real mundo
        self.z = None
        self.rot = 0.0                     # rotacion (miliradianes en el binario)
        self.color = None                  # slot vtable 0x188
        self._last_real_x = None           # _lastRealPositionX/Z (interp)
        self._last_real_z = None
        self.eventos = 0

    # --- setMassAndRadius = FUN_140677760 ---
    def setMassAndRadius(self, masa):
        self.masa = float(masa)
        self.size = int(masa)              # ent+0x90 int
        self.setRadius(radio_from_masa(masa))

    # --- setRadius (slot vtable 0x1c8) ---
    def setRadius(self, r):
        self.radio = float(r)

    # --- get_speed = FUN_140677ff0 -> 0.2 constante ---
    def get_speed(self):
        return 0.2

    # --- color: entityColor = _randomColors[_id % len] (GameEntity.as L650) ---
    def set_entity_color(self, palette):
        self.color = palette[self.id % len(palette)]

    # --- applyPositionInterpolated = FUN_1406790f0 ---
    def applyPositionInterpolated(self, x0, z0, x1, z1, rot_target, alpha):
        """x/z = lerp(actual, target, alpha); rot con wrap 2*pi."""
        if self.x is None:
            self.x, self.z = x1, z1
        else:
            self.x = self.x + (x1 - self.x) * alpha
            self.z = self.z + (z1 - self.z) * alpha
        self.rot = wrap_2pi(self.rot + (wrap_2pi(rot_target) - self.rot) * alpha)

    def __repr__(self):
        return ("GameEntity(id=%d, type=%d, masa=%.1f, radio=%.1f, x=%s, z=%s)" % (
            self.id, self.entityType, self.masa, self.radio,
            None if self.x is None else round(self.x, 1),
            None if self.z is None else round(self.z, 1)))


class FoodEntity(GameEntity):
    """FoodEntity: _size = 1 fijo (FUN_14066e490: *(ent+0x12) = 1)."""
    def __init__(self, eid):
        super(FoodEntity, self).__init__(eid, ET_FOOD)
        self.size = 1
        self.set_entity_color(FOOD_RGB)


class PlayerEntity(GameEntity):
    """PlayerEntity: cells, applyForce/applyExtrapolation/updateMouse."""
    def __init__(self, eid):
        super(PlayerEntity, self).__init__(eid, ET_PLAYER)
        self.dir_x = 0.0        # +0x100 (floats +0xc/+0x14)
        self.dir_z = 0.0
        self.force = 0.0        # +0x108
        self.set_entity_color(CELL_RGB)

    # --- applyForce (slot vtable +0x1a8) = FUN_1414c7e40 ---
    def applyForce(self, dir_x, dir_z, force):
        self.dir_x = float(dir_x)
        self.dir_z = float(dir_z)
        self.force = float(force)

    # --- applyExtrapolation (slot +0x1b0) = FUN_1414c7ec0: pos += delta ---
    def applyExtrapolation(self, dx, dz):
        if self.x is not None and self.z is not None:
            self.x += dx
            self.z += dz

    # --- updateMouse core = FUN_1414a8d20 (mates de la celula) ---
    def updateMouse(self, mouse_x, mouse_y, center_x, center_y, max_speed=400.0):
        """updateMouse core REAL (FUN_1414a8d20, lineas 128-144):
        1. dir = normalize(mousePos - centerPos)  (sqrt FUN_141bf6990)
        2. force = sqrt(clamp(dist/maxSpeed, 0, 1))  -> se guarda en jugador+0x298
           y es el 'force' que el frame processor envia en el MOVE 10022
        3. si dist > maxSpeed: v = clamp(dist, maxSpeed, 3*maxSpeed)/(size*2),
           vX = dirX_norm*v, vZ = dirZ_norm*v  (velocidad visual del cliente)
        4. suavizado exponencial: pos += (target - pos)*0.25
        Devuelve (vx, vz, force): el visor envia force en el MOVE y usa vx/vz
        para la prediccion local entre updates del server."""
        dx = mouse_x - center_x
        dy = mouse_y - center_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist <= 0.0001:
            return 0.0, 0.0, 0.0
        dir_x = dx / dist
        dir_z = dy / dist
        force = math.sqrt(max(0.0, min(1.0, dist / max_speed)))
        if self.size > 0:
            v = max(max_speed, min(dist, max_speed * 3.0)) / (self.size * 2)
        else:
            v = 0.0
        vx = dir_x * v
        vz = dir_z * v
        # suavizado exponencial x0.25 hacia el target (prediccion local)
        if self.x is not None and self.z is not None:
            self.x += (self.x + dir_x * max_speed * 0.01 - self.x) * 0.25
            self.z += (self.z + dir_z * max_speed * 0.01 - self.z) * 0.25
        return vx, vz, force


class VirusEntity(GameEntity):
    """VirusEntity (entityType 4)."""
    def __init__(self, eid):
        super(VirusEntity, self).__init__(eid, ET_VIRUS)
        self.set_entity_color(CELL_RGB)


class CoinEntity(GameEntity):
    """CoinEntity (entityType 5)."""
    def __init__(self, eid):
        super(CoinEntity, self).__init__(eid, ET_COIN)
        self.set_entity_color(CELL_RGB)


class FlagBaseEntity(GameEntity):
    """FlagBaseEntity (entityType 6, bases CTF)."""
    def __init__(self, eid):
        super(FlagBaseEntity, self).__init__(eid, ET_FLAG_BASE)
        self.team = 0
        self.set_entity_color(TEAM_RGB)


ENTITY_FACTORY = {
    ET_FOOD: FoodEntity,
    ET_PLAYER: PlayerEntity,
    ET_VIRUS: VirusEntity,
    ET_COIN: CoinEntity,
    ET_FLAG_BASE: FlagBaseEntity,
}


def build_entity(eid, entity_type):
    """Fabrica FUN_14073b220: crea la clase segun entityType (ent+0x28)."""
    cls = ENTITY_FACTORY.get(entity_type, GameEntity)
    return cls(eid)
