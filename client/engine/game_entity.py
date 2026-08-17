"""
GameEntity — réplica literal del binario MitosisOG.exe (clase Haxe GameEntity).

Fuente: Ghidra MCP. Decompilados en re/decomp_mov/GameEntity_*.c y
FUN_14067a160 (dispatcher de campos, case 0-0x1c).

Estructura (offsets en longlong* = x8 bytes, del dispatcher FUN_14067a160):
    +0x28 entityType        (case 0xe: get_entityType -> FUN_1400f1b80)
    +0x2c id                (case 2: "id" -> *(param_1 + 0x2c))
    +0x34 particle_count?   (case 9: "_particle_count" -> *(param_1 + 0x34))
    +0x48 size              (case 5: "size" -> param_1[5]; FoodEntity._size=1)
    +0x58 particle_duration (case 0x12: "_particle_duration" -> param_1[7])
    +0x60 entity_state?     (case 10: "entityType" -> param_1[6])
    +0x68 points?           (case 10: "_particle_scale" -> param_1[8])
    +0x70 points            (case 9: "_points" -> param_1[9])
    +0x78 circle_radius     (case 7: "_circle_radius" -> param_1[10])
    +0x80 object            (case 6: "object" -> param_1[0xb])
    +0x88 object2           (case 7: "object2" -> param_1[0xc])
    +0x90 MASA/size         (case 4: "size" -> param_1[0x12]; setSize FUN_140677930
                             escribe +0x90; setMassAndRadiusInterpolado lee/escribe)
    +0xa0 radius            (case 6: "radius" -> param_1[0x11]; setRadius slot 0x1c8)
    +0xa1 alive?            (case 0xd: "_addToLayer" byte -> param_1 + 0xa1)
    +0xa8 meshContainer     (case 0xe: "_meshContainer" -> param_1[0xe])
    +0xb0 mesh?             (case 0xf: "_mesh...2" -> param_1[0xf])
    +0xb8 flags?            (case 0xd: "set_alive" / "get_alive" -> param_1[0x14])
    +0xc0 x (lastRealX)     (case 0x12: "_lastRealPositionX" -> param_1[0x15])
    +0xc8 z (lastRealZ)     (case 0x12: "_lastRealPositionZ" -> param_1[0x16])
    +0xd0 rotation          (case 0x11: "_rotation..." -> param_1[0x17])
    +0xd8 realSize?         (case 0xd: "_lastSize..." -> param_1[0x18])
    +0xe0 positionX         (case 5: "gridX" -> *(param_1 + 0xdc))
    +0xe8 positionY?        (case 5: "gridY" -> param_1[0x1c])
    +0xf0 status            (case 0xc: "activeStatus" -> param_1[0x1d])
    +0xf8 wasInFrustrum     (case 0xe: "_wasInFrustrum" -> param_1[0x1e])
    +0x100 directionNorm?   (case 0x14: "_directionNormalized" -> param_1[0x1b])
    +0x110 level            (case 9: "_level" -> param_1[0x13])
    +0x118 exp              (case 7: "_exp" -> param_1[0x19])
    +0x120 owner            (case 9: "_owner" -> param_1[0x1a] / case 5 param_1[5])

Slots de vtable referenciados por el dispatcher y los wrappers:
    0x108 get_registerAnimator?  0x110 hasSecondaryObject
    0x118 entityState?           0x128 gameRotation
    0x130 rotation?              0x140 updateMesh (setSize llama 0x140)
    0x158 entityType?            0x160 level
    0x168 updatePosition         0x178 estado 0/1 (setActiveStatus?)
    0x180 setRotation            0x188 setColor
    0x198 entityColor            0x1a8 applyForce
    0x1b0 applyExtrapolation     0x1b8 setRotation (interp)
    0x1c0 update                 0x1c8 setRadius
    0x1d0 scaleFactor?           0x1d8 tremolio?
    0x1e0 fluid?                 0x1f8 points
    0x210 direction              0x218 destroy
    0x220 containerLayer
"""

import math

# Constante del binario: get_speed devuelve 0.2 (FUN_140677ff0,
# 0x3fc999999999999a = double 0.2)
SPEED_BASE = 0.2


class GameEntity:
    """GameEntity del binario. Los campos usan los offsets reales (x8).

    En Python los atributos son nombres, pero cada uno documenta su offset
    para trazabilidad byte a byte con Ghidra.
    """

    __slots__ = (
        "entityType", "eid", "particle_count", "size", "particle_duration",
        "entity_state", "particle_scale", "points", "circle_radius",
        "object", "object2", "masa", "radius", "alive", "mesh_container",
        "mesh2", "flags", "last_real_x", "last_real_z", "rotation",
        "real_size", "grid_x", "grid_y", "status", "was_in_frustrum",
        "direction_normalized", "level", "exp", "owner", "x_prev", "z_prev",
    )

    def __init__(self, eid=0, entityType=1):
        self.entityType = entityType      # +0x28 (fabrica FUN_14073b220)
        self.eid = eid                      # +0x2c
        self.particle_count = 0             # +0x34
        self.size = 1                       # +0x48 (FoodEntity._size=1)
        self.particle_duration = 0          # +0x58
        self.entity_state = 0               # +0x60
        self.particle_scale = 0             # +0x68
        self.points = 0                     # +0x70
        self.circle_radius = 0              # +0x78
        self.object = None                  # +0x80
        self.object2 = None                 # +0x88
        self.masa = 0.0                     # +0x90 (campo size/masa real)
        self.radius = 0.0                   # +0xa0 (setRadius slot 0x1c8)
        self.alive = True                   # +0xa1
        self.mesh_container = None          # +0xa8
        self.mesh2 = None                   # +0xb0
        self.flags = 0                      # +0xb8
        self.last_real_x = 0.0              # +0xc0 (_lastRealPositionX)
        self.last_real_z = 0.0              # +0xc8 (_lastRealPositionZ)
        self.rotation = 0.0                 # +0xd0 (mrad)
        self.real_size = 0.0                # +0xd8
        self.grid_x = 0.0                   # +0xe0
        self.grid_y = 0.0                   # +0xe8
        self.status = 0                     # +0xf0 (activeStatus)
        self.was_in_frustrum = False        # +0xf8
        self.direction_normalized = False   # +0x100
        self.level = 0                      # +0x110
        self.exp = 0                        # +0x118
        self.owner = None                   # +0x120
        self.x_prev = 0.0                   # historial (InterpolationHistory)
        self.z_prev = 0.0

    # ---- FUN_140677ff0: get_speed (devuelve 0.2) ----
    def get_speed(self):
        return SPEED_BASE

    # ---- FUN_140677760: setMassAndRadius ----
    # (decomp re/_d_140677760.txt; slot 0x1c8 setRadius con
    #  radio = floor(sqrt(masa)*10+0.5)+1)
    def setMassAndRadius(self, masa):
        self.masa = float(masa)
        self.radius = radio_from_masa(self.masa)

    # ---- FUN_140677930: setSize (escribe +0x90, updateMesh 0x140) ----
    def setSize(self, size):
        self.masa = float(size)
        self.updateMesh()

    # ---- FUN_1406784b0: updatePosition (slot 0x168) ----
    def updatePosition(self):
        # en el binario: slot 0x168 (posicion real del server -> mesh)
        self.last_real_x = self.grid_x
        self.last_real_z = self.grid_y

    # ---- FUN_140679550: update (slot 0x1c0) ----
    def update(self):
        # en el binario: slot 0x1c0 (update del mesh/estado)
        pass

    # ---- FUN_140678f90: applyForce (wrapper slot 0x1a8) ----
    def applyForce(self, f1, f2, f3):
        # en el binario: (**(code **)(*param_2 + 0x1a8))(param_2, f1, f2, f3)
        self.applyForce_impl(f1, f2, f3)

    def applyForce_impl(self, f1, f2, f3):
        raise NotImplementedError("PlayerEntity sobreescribe (PE_applyForce_REAL)")

    # ---- FUN_140679060: applyExtrapolation (wrapper slot 0x1b0) ----
    def applyExtrapolation(self, e1, e2):
        self.applyExtrapolation_impl(e1, e2)

    def applyExtrapolation_impl(self, e1, e2):
        raise NotImplementedError("PlayerEntity sobreescribe (PE_applyExtrapolation_REAL)")

    # ---- FUN_140679290: applyPositionInterpolated (wrapper FUN_1406790f0) ----
    def applyPositionInterpolated(self, x_new, z_new, rot_new, alpha):
        """x = x_prev + (x_new - x_prev) * alpha; rot con wrap 2π.

        FUN_1406790f0 decompilada: dVar1=z_prev, dVar2=x_prev,
        dVar3=wrap(rot_prev/1000), dVar4=wrap(rot_new/1000),
        dVar5 = dVar4-dVar3 con wrap ±π; setRotation((dVar3+(dVar4-dVar3)
        *alpha)*1000); setPosition((1-a)*x_prev + a*x_new, ...)."""
        # rotacion en miliradianes con wrap
        r3 = (self.rotation / 1000.0) % (2 * math.pi)
        r4 = (rot_new / 1000.0) % (2 * math.pi)
        d5 = r4 - r3
        if d5 < -math.pi:
            r4 += 2 * math.pi
        if d5 > math.pi:
            r4 -= 2 * math.pi
        rot_interp = (r3 + (r4 - r3) * alpha) * 1000.0
        self.setRotation(rot_interp)
        self.setPosition((1.0 - alpha) * self.x_prev + alpha * x_new,
                         (1.0 - alpha) * self.z_prev + alpha * z_new)

    # ---- FUN_1406776e0: setMassAndRadiusInterpolated (wrapper FUN_1406775f0) ----
    def setMassAndRadiusInterpolated(self, masa_nueva, alpha):
        """masa_interp = (1-a)*masa_prev + a*nueva; si cambia el entero,
        aplica int(masa) y radio = floor(sqrt(m)*10+0.5)+1 (slot 0x1c8) + 0x140.

        FUN_1406775f0 decompilada: dVar2 = (1-param_3)*param_1[0x18] + param_2
        *param_3; si iVar1 (int) != param_1[0x12]: escribe int(param_2) en
        +0x90, radio = floor(sqrt(m)*10+0.5), setRadius(radio+1), slot 0x140."""
        masa_interp = (1.0 - alpha) * self.real_size + alpha * masa_nueva
        if int(masa_interp) != int(self.masa):
            self.masa = float(int(masa_nueva))
            radio = math.floor(math.sqrt(self.masa) * 10.0 + 0.5)
            self.setRadius(radio + 1)
            self.updateMesh()

    # ---- slots basicos ----
    def setRadius(self, r):
        self.radius = float(r)

    def setRotation(self, rot):
        self.rotation = rot

    def setPosition(self, x, z):
        self.grid_x = x
        self.grid_y = z

    def setColor(self, color):
        self.object2 = color  # slot 0x188: el color viaja por CLEAR 0x20

    def destroy(self):
        self.alive = False

    def updateMesh(self):
        pass  # slot 0x140: en el binario actualiza el mesh del renderer


# ---- FUN_140677760 (radio_from_masa): floor(sqrt(m)*10+0.5)+1 ----
def radio_from_masa(masa):
    m = float(masa)
    if m <= 0:
        return 0.0
    return math.floor(math.sqrt(m) * 10.0 + 0.5) + 1
