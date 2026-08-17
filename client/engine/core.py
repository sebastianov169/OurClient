"""
Core del binario — réplica literal (fkengine.core.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    Engine   — el motor (main loop, layers)
    Layer2D  — capa 2D (contenedores de render)
    Stats    — estadisticas (fps)
"""


class Layer2D:
    """fkengine.core.Layer2D — capa de render 2D."""

    def __init__(self, name=""):
        self.name = name
        self.children = []
        self.visible = True
        self.x = 0.0
        self.y = 0.0

    def add(self, child):
        self.children.append(child)

    def remove(self, child):
        if child in self.children:
            self.children.remove(child)

    def clear(self):
        self.children = []


class Engine:
    """fkengine.core.Engine — el motor (main loop del binario).

    El game loop real es FUN_140795df0 (View.update) — ver analysis/. El
    Engine agrupa las capas y el loop de render."""

    def __init__(self):
        self.layers = {}
        self.running = False
        self.fps = 60.0
        self.frame = 0

    def add_layer(self, name, layer):
        self.layers[name] = layer

    def get_layer(self, name):
        return self.layers.get(name)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def tick(self, dt):
        self.frame += 1
        for layer in self.layers.values():
            if layer.visible:
                for child in layer.children:
                    if hasattr(child, "tick"):
                        child.tick(dt)


class Stats:
    """fkengine.core.Stats — estadisticas (fps, memoria)."""

    def __init__(self):
        self.fps = 0.0
        self.frame_count = 0
        self.dt_sum = 0.0

    def frame(self, dt):
        self.frame_count += 1
        self.dt_sum += dt
        if self.dt_sum >= 1.0:
            self.fps = self.frame_count / self.dt_sum
            self.frame_count = 0
            self.dt_sum = 0.0


class Stats_Item:
    """Item de Stats."""

    def __init__(self, key="", value=0.0):
        self.key = key
        self.value = value
