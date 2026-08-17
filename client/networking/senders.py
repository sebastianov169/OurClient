"""
Senders del protocolo — réplica literal del binario (send_wrapper1-17).

Fuente: Ghidra MCP, re/decomp_mov/send_wrapper*.c.

El View del binario envía por FUN_14096e330 (m2xcTcp, +0x340) con opcodes:
    0x2726 (10022) = MOVE (ángulo + fuerza)
    0x2727 (10023) = ? (rotación en milirradianes, floor(v*1000))
    0x2729 (10025) = ? (con/sin flag, +0x310 estado de conexión)
    0x272a (10026) = ? (con/sin flag)
    0x272b (10027) = toggle (param_2 ^ 1) — pausa/autorespawn?
    0x272c (10028) = ? (inverso de 0x272b)

Condición de envío: *(*(param_1+0x310)+0x10) != 0 y *(lVar1+0x10) != 0
(sesión de juego activa). El flag +0x330 de la entidad controla si la
fuerza viaja (0 = sí).

El MOVE (send_wrapper9, FUN_140780510) construye un array de 3 floats:
    [0] = atan2(dir.z, dir.x)  (FUN_141c05178 = atan2, ángulo en rad)
    [1] = fuerza (param_1+0x298, del updateMouse core) si +0x330==0 si no 0
    [2] = dir normalizada? (0x11 = tamaño del array de 17 floats?)
"""

import math


class Sender:
    """Replica los send_wrapper del binario (protocolo m2xcTcp).

    conn: objeto con send(opcode, payload) — el socket m2xcTcp real.
    """

    def __init__(self, conn):
        self.conn = conn
        self.session_active = False   # *(*(+0x310)+0x10) != 0
        self.flag_330 = False         # +0x330 de la entidad

    def _can_send(self):
        return self.session_active

    # ---- FUN_140780120: send_wrapper1 (0x272b + (param_2 ^ 1)) ----
    def toggle(self, param):
        if self._can_send():
            self.conn.send(0x272b + (param ^ 1), [])

    # ---- FUN_140780170: send_wrapper2 (0x272b si param else 0x272c) ----
    def send_272b_or_272c(self, param):
        op = 0x272b if param else 0x272c
        if self._can_send():
            self.conn.send(op, [])

    # ---- FUN_1407801f0 / FUN_140780240: send_wrapper3/4 (0x2729) ----
    def send_2729(self, with_flag=False):
        if self._can_send():
            self.conn.send(0x2729, [])

    # ---- FUN_1407802a0 / FUN_1407802f0: send_wrapper5/6 (0x272a) ----
    def send_272a(self, with_flag=False):
        if self._can_send():
            self.conn.send(0x272a, [])

    # ---- FUN_140780350: send_wrapper7 (0x2727, rot en mrad) ----
    def send_rotation(self, rot):
        # marca +0x628 = 1 y envía floor(rot*1000+0.5)
        self.flag_330 = True
        if self._can_send():
            self.conn.send(0x2727, [int(math.floor(rot * 1000.0 + 0.5))])

    # ---- FUN_1407814a0 / FUN_1407814f0: send_wrapper10/11 (0x271c) ----
    def send_271c(self, with_flag=False):
        # marca +0x628 = 0 (detener el envio de MOVE?)
        self.flag_330 = False
        if self._can_send():
            self.conn.send(0x271c, [])

    # ---- FUN_1407815b0: send_wrapper12 (0x271a) ----
    def send_271a(self, with_flag=False):
        if self._can_send():
            self.conn.send(0x271a, [])

    # ---- FUN_140781600: send_wrapper13 (0x271a sin flag) ----
    def send_271a_simple(self):
        if self._can_send():
            self.conn.send(0x271a, [])

    # ---- FUN_140789420 / FUN_140789450: send_wrapper14/15 (0x2727) ----
    def send_2727(self, with_flag=False):
        if self._can_send():
            self.conn.send(0x2727, [])

    # ---- FUN_140789490 / FUN_1407894c0: send_wrapper16/17 (0x2720) ----
    def send_2720(self, with_flag=False):
        if self._can_send():
            self.conn.send(0x2720, [])

    # ---- FUN_140780510: send_wrapper9 = MOVE (0x2726) ----
    def send_move(self, angle, fuerza, dir_x=None, dir_z=None):
        """MOVE real: [atan2(dir.z,dir.x), fuerza, dir...]."""
        if not self._can_send():
            return
        a = math.atan2(dir_z, dir_x) if dir_x is not None and dir_z is not None else angle
        f = fuerza if not self.flag_330 else 0.0
        self.conn.send(0x2726, [a, f])
