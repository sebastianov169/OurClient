"""
Componentes GUI del binario — réplica literal (fkengine.gui.components.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    Checkbox           (FUN_14141e490)
    LoaderBar          (FUN_1414330f0)
    Prompt             (FUN_1414305d0)
    SimpleDataTable    (FUN_141429f20)
    EquipmentBar       (FUN_14141a0a0)
    MultipleSelector   (FUN_141432400)
    QUniversalTextInput (FUN_14142dd30)
    QList              (FUN_1414608d0)
"""

from client.ui import Button


class Checkbox(Button):
    """fkengine.gui.components.checkbox.Checkbox (FUN_14141e490)."""

    def __init__(self, label="", checked=False):
        super().__init__(label)
        self.checked = checked

    def click(self):
        self.checked = not self.checked
        if self.on_click:
            self.on_click(self.checked)


class LoaderBar:
    """fkengine.gui.components.loaderbar.LoaderBar (FUN_1414330f0) —
    barra de carga (assets)."""

    def __init__(self):
        self.progress = 0.0
        self.visible = False

    def set_progress(self, p):
        self.progress = max(0.0, min(1.0, p))
        self.visible = True


class Prompt:
    """fkengine.gui.components.prompt.Prompt (FUN_1414305d0) — prompt de texto."""

    def __init__(self, title="", placeholder=""):
        self.title = title
        self.placeholder = placeholder
        self.value = ""
        self.on_submit = None

    def submit(self):
        if self.on_submit:
            self.on_submit(self.value)


class SimpleDataTable:
    """fkengine.gui.components.simpledatatable.SimpleDataTable
    (FUN_141429f20) — tabla simple (leaderboard por filas)."""

    def __init__(self, columns=()):
        self.columns = list(columns)
        self.rows = []

    def add_row(self, row):
        self.rows.append(list(row))


class SimpleDataTableRow:
    """Fila de la tabla."""

    def __init__(self, cells=()):
        self.cells = list(cells)


class MultipleSelector:
    """fkengine.gui.components.multipleselector.MultipleSelector
    (FUN_141432400) — selector multiple."""

    def __init__(self, options=()):
        self.options = list(options)
        self.selected = []

    def toggle(self, option):
        if option in self.selected:
            self.selected.remove(option)
        else:
            self.selected.append(option)


class QUniversalTextInput:
    """fkengine.gui.components.quniversaltextinput.QUniversalTextInput
    (FUN_14142dd30) — campo de texto."""

    def __init__(self, text=""):
        self.text = text
        self.focused = False


class QList:
    """fkengine.gui.QList (FUN_1414608d0) — lista (amigos, items)."""

    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)
