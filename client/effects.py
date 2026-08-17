"""
Efectos del binario — réplica literal (fkengine.effects.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    ParticleManager  (FUN_140a2e170, vtable DAT_1421c3c40, ctor FUN_140a2e540)
    BaseGeometry     (FUN_140a300b0, vtable DAT_1421b93c0)
"""


class Particle:
    """Particula individual (la comida del mundo usa applyParticle)."""

    def __init__(self, x=0.0, z=0.0, radius=1.0, color=(255, 255, 255)):
        self.x = x
        self.z = z
        self.radius = radius
        self.color = color
        self.alive = True


class ParticleManager:
    """fkengine.effects.particles.ParticleManager (FUN_140a2e540) — gestiona
    las particulas (comida, efectos). El binario usa applyParticle
    (FUN_140678b80) para crearlas y removeParticle (FUN_140678580)."""

    def __init__(self):
        self.particles = {}

    def applyParticle(self, eid, x, z, radius=1.0, color=(255, 255, 255)):
        """applyParticle del binario: crea/actualiza la particula eid."""
        self.particles[eid] = Particle(x, z, radius, color)

    def removeParticle(self, eid):
        self.particles.pop(eid, None)

    def clear(self):
        self.particles = {}


class BaseGeometry:
    """fkengine.effects.base.BaseGeometry — geometria base de los efectos."""

    def __init__(self):
        self.vertices = []
        self.visible = True
