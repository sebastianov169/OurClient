"""
SteeringBehaviour — réplica literal del binario
(fkengine.game.behaviours.SteeringBehaviour).

Fuente: Ghidra MCP, re/decomp_mov/SteeringBehaviour_*.c.
init (FUN_1414e57b0): nombre "SteeringBehaviour", tamano 0x11.
full_init (FUN_1414e9100): clase registrada con vtable.

Comportamiento de direccion (steering) de las entidades moviles.
"""


class SteeringBehaviour:
    def __init__(self):
        self.target = None
        self.enabled = True

    def steer(self, entity):
        """Comportamiento base: sin direccion propia (las subclases
        sobreescriben). En el binario el steering se registra por nombre
        en la vtable (FUN_1414e5be0/FUN_1414e5cd0 = metodos)."""
        return None
