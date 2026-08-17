"""
Vistas GUI del binario — réplica literal (fkengine.gui.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    CreatePrivateRoom  (FUN_141424f10) — creacion de sala privada
    Disconnected       (FUN_14141ad30) — pantalla de desconexion
    Conversation       (FUN_14140a820) — conversacion (amigos/mensajero)
    FriendListItem     (FUN_141404ef0) — item de lista de amigos
    EquipmentBar       (FUN_14141a0a0) — barra de equipamiento
    NavigationView     (clase vecina)
"""


class CreatePrivateRoom:
    """fkengine.gui.createprivateroom.CreatePrivateRoom (FUN_141424f10) —
    la pantalla de crear sala privada (joinroom del visor)."""

    def __init__(self):
        self.room_name = ""
        self.mode = 0
        self.password = ""
        self.on_create = None

    def create(self):
        if self.on_create:
            self.on_create(self.room_name, self.mode, self.password)


class Disconnected:
    """fkengine.gui.disconnected.Disconnected (FUN_14141ad30) —
    pantalla de desconexion (el visor la emula con el lobby de muerte)."""

    def __init__(self):
        self.visible = False
        self.reason = ""
        self.on_reconnect = None

    def show(self, reason=""):
        self.reason = reason
        self.visible = True

    def reconnect(self):
        self.visible = False
        if self.on_reconnect:
            self.on_reconnect()


class Conversation:
    """fkengine.gui.friends.Conversation (FUN_14140a820) — conversacion."""

    def __init__(self, peer=""):
        self.peer = peer
        self.messages = []
        self.unread = 0

    def add_message(self, sender, text):
        self.messages.append((sender, text))
        if sender != self.peer:
            self.unread += 1


class FriendListItem:
    """fkengine.gui.friends.FriendListItem (FUN_141404ef0)."""

    def __init__(self, name="", online=False):
        self.name = name
        self.online = online


class EquipmentBar:
    """fkengine.gui.equipment.EquipmentBar (FUN_14141a0a0) — barra de
    equipamiento (items/gemas del jugador)."""

    def __init__(self, slots=4):
        self.slots = [None] * slots

    def equip(self, index, item):
        if 0 <= index < len(self.slots):
            self.slots[index] = item

    def get(self, index):
        return self.slots[index] if 0 <= index < len(self.slots) else None


class EquipmentBarSlot:
    """Slot de la barra."""

    def __init__(self):
        self.item = None
        self.durability = 0
