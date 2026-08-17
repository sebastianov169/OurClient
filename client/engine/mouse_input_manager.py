"""
MouseInputManager — réplica literal del binario
(fkengine.game.MouseInputManager, FUN_1414a1890).

Fuente: Ghidra MCP, re/decomp_mov/MouseInputManager_*.c + MIM_*.c.

Estados del speedup (MIM_startSpeedup FUN_140646040 / endSpeedup
FUN_1406460d0): flag +0x2ad (speedup activo), condición +0x308 (habilitado),
objeto +0x2b0 (BonusSpeed). El speedup llama slot 0x70 del objeto (busca
por hash 0x5f5c03c1 = "startSpeedup"/"endSpeedup"?) y luego slot 0x28/0x30.
speedupCheck (FUN_140646910) lee "skipout" de +0x300 (config).
keyPressed (FUN_1406464b0) -> slot 0x348 del receptor (procesar tecla).
touchReceived (FUN_1406494f0) -> slot 0x390 (touch -> posicion).
secondaryTouch (FUN_140649430) -> slot 0x388.
messageReceived (FUN_140a25600) -> slot 0x2b8.
"""


class MouseInputManager:
    """Gestor de input del mouse del binario."""

    # slots del receptor (el View): 0x100=process, 0x348=keyPressed,
    # 0x388=secondaryTouch, 0x390=touchReceived, 0x2b8=messageReceived

    def __init__(self):
        # +0x2ad: speedup activo (flag)
        self.speedup_active = False
        # +0x308: speedup habilitado
        self.speedup_enabled = True
        # +0x2b0: objeto BonusSpeed
        self.bonus_speed = None
        # +0x300: config (dict con "skipout")
        self.config = {"skipout": 0}

    # ---- FUN_140646040: startSpeedup ----
    def startSpeedup(self):
        """Si habilitado (+0x308) y no activo (+0x2ad): marca activo y
        llama al BonusSpeed (slot 0x70 -> hash 0x5f5c03c1, slot 0x28)."""
        if self.speedup_enabled and not self.speedup_active:
            self.speedup_active = True
            if self.bonus_speed is not None:
                self.bonus_speed.start()

    # ---- FUN_1406460d0: endSpeedup ----
    def endSpeedup(self):
        """Si habilitado y activo: desmarca y llama slot 0x30 del BonusSpeed."""
        if self.speedup_enabled and self.speedup_active:
            self.speedup_active = False
            if self.bonus_speed is not None:
                self.bonus_speed.end()

    # ---- FUN_140646910: speedupCheck ----
    def speedupCheck(self, param):
        """Lee 'skipout' de la config (+0x300); si no es 0, el speedup
        sigue activo (skipout)."""
        skipout = self.config.get("skipout", 0)
        return skipout != 0

    # ---- FUN_1406464b0: keyPressed (slot 0x348) ----
    def keyPressed(self, key_code, pressed):
        # en el binario: (**(code **)(*param_2 + 0x348))(param_2, pressed, key)
        return key_code, pressed

    # ---- FUN_140a25600: messageReceived (slot 0x2b8) ----
    def messageReceived(self, msg):
        return msg
