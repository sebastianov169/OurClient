"""
Inventario y skins — réplica literal (fkengine.gui.inventory / skins / skinpaint).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    InventoryCache         — cache del inventario
    SkinView               — vista de skins
    SkinPainterPaper       — papel de pintado de skin
    SkinPainterPaperEvent  — evento de pintado
"""


class InventoryCache:
    """fkengine.gui.inventory.InventoryCache — cache del inventario
    (items del jugador: gemas, potions, skins)."""

    def __init__(self):
        self.items = {}
        self.gems = 0

    def add(self, item_id, count=1):
        self.items[item_id] = self.items.get(item_id, 0) + count

    def remove(self, item_id, count=1):
        if item_id in self.items:
            self.items[item_id] -= count
            if self.items[item_id] <= 0:
                del self.items[item_id]

    def has(self, item_id, count=1):
        return self.items.get(item_id, 0) >= count


class SkinView:
    """fkengine.gui.skins.SkinView — vista de skins."""

    def __init__(self):
        self.skins = []
        self.selected = None

    def select(self, skin_id):
        self.selected = skin_id


class SkinPainterPaper:
    """fkengine.gui.skinpaint.SkinPainterPaper — pintado de skin."""

    def __init__(self, size=64):
        self.size = size
        self.pixels = {}

    def paint(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.pixels[(x, y)] = color

    def clear(self):
        self.pixels = {}


class SkinPainterPaperEvent:
    """Evento de pintado."""

    def __init__(self, x=0, y=0, color=None):
        self.x, self.y = x, y
        self.color = color
