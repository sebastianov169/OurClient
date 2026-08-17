"""
Navegacion GUI — réplica literal (fkengine.gui.Navigation*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    NavigationContainer    — contenedor de navegacion
    NavigationView         — vista navegable
    INavigationControllerEvents — eventos de navegacion
"""


class NavigationContainer:
    """fkengine.gui.NavigationContainer — contenedor."""

    def __init__(self):
        self.views = []
        self.current_index = 0

    def add_view(self, view):
        self.views.append(view)

    def show(self, index):
        if 0 <= index < len(self.views):
            self.current_index = index
            for i, v in enumerate(self.views):
                v.visible = (i == index)

    @property
    def current(self):
        if self.views:
            return self.views[self.current_index]
        return None


class NavigationView:
    """fkengine.gui.NavigationView — vista navegable."""

    def __init__(self, name=""):
        self.name = name
        self.visible = False
        self.on_show = None
        self.on_hide = None

    def show(self):
        self.visible = True
        if self.on_show:
            self.on_show()

    def hide(self):
        self.visible = False
        if self.on_hide:
            self.on_hide()


class INavigationControllerEvents:
    """Eventos del controlador de navegacion."""

    def on_view_changed(self, view):
        pass
