"""
UI del binario — réplica literal (fkengine.gui.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados 2026-08-14).

Clases identificadas por classreg:
    Button          (FUN_14061a8f0, vtable DAT_1421b8d40, ctor FUN_14061aca0)
    Popup           (FUN_140605800, vtable DAT_1421b8cd0, ctor FUN_140605b20)
    ModalPopup      (clase vecina)
    Alert           (fkengine.gui.components.alert.Alert)
    NavigationController (FUN_140629e90, ctor FUN_14062a110)
    NavigationManager
    ArrangeableContainer
    LifeIndicator   (fkengine.gui.activestatus.LifeIndicator)
    Measures        (fkengine.gui.Measures)
"""


class Button:
    """fkengine.gui.components.button.Button (FUN_14061aca0)."""

    def __init__(self, label="", x=0, y=0, w=0, h=0):
        self.label = label
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.visible = True
        self.enabled = True
        self.on_click = None

    def hit_test(self, mx, my):
        return self.visible and (self.x <= mx <= self.x + self.w and
                                 self.y <= my <= self.y + self.h)

    def click(self):
        if self.enabled and self.on_click:
            self.on_click()


class Popup:
    """fkengine.gui.components.popup.Popup (FUN_140605b20)."""

    def __init__(self, title=""):
        self.title = title
        self.visible = False
        self.buttons = []
        self.on_close = None

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False
        if self.on_close:
            self.on_close()


class ModalPopup(Popup):
    """fkengine.gui.components.popup.ModalPopup — bloquea la UI de detras."""

    def __init__(self, title=""):
        super().__init__(title)
        self.modal = True


class Alert(Popup):
    """fkengine.gui.components.alert.Alert — mensaje con boton OK."""

    def __init__(self, message=""):
        super().__init__("Alert")
        self.message = message


class NavigationController:
    """fkengine.gui.NavigationController (FUN_14062a110) — controla vistas."""

    def __init__(self):
        self.stack = []
        self.current = None

    def push(self, view):
        self.stack.append(view)
        self.current = view

    def pop(self):
        if self.stack:
            self.stack.pop()
            self.current = self.stack[-1] if self.stack else None
        return self.current


class NavigationManager:
    """fkengine.gui.NavigationManager — gestiona los controllers."""

    def __init__(self):
        self.controllers = {}

    def register(self, name, controller):
        self.controllers[name] = controller

    def get(self, name):
        return self.controllers.get(name)


class ArrangeableContainer:
    """fkengine.gui.ArrangeableContainer — contenedor con layout."""

    def __init__(self):
        self.children = []
        self.layout = "vertical"

    def add(self, child):
        self.children.append(child)

    def arrange(self):
        y = 0
        for c in self.children:
            c.y = y
            y += c.h


class LifeIndicator:
    """fkengine.gui.activestatus.LifeIndicator — indicador de vida."""

    def __init__(self):
        self.value = 1.0
        self.max = 1.0

    def set(self, v):
        self.value = max(0.0, min(self.max, v))


class Measures:
    """fkengine.gui.Measures — constantes de medida de la UI."""

    SCREEN_W = 1280
    SCREEN_H = 720
