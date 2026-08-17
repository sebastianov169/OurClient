"""
Timing del binario — réplica literal (fkengine.game.data.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    Timer    — timer del juego (cooldowns, efectos, animaciones)
    Tickable — objetos que reciben tick del game loop (60 fps)
    Defer    — ejecucion diferida
"""


class Tickable:
    """fkengine.game.data.Tickable — recibe tick del game loop."""

    def __init__(self):
        self.enabled = True

    def tick(self, dt):
        """llamado cada frame del game loop (60fps)."""
        pass


class Timer(Tickable):
    """fkengine.game.data.Timer — timer del binario."""

    def __init__(self, duration=0.0, repeat=False):
        super().__init__()
        self.duration = duration
        self.repeat = repeat
        self.elapsed = 0.0
        self.finished = False
        self.on_complete = None

    def start(self, duration=None):
        if duration is not None:
            self.duration = duration
        self.elapsed = 0.0
        self.finished = False

    def tick(self, dt):
        if self.finished or not self.enabled:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            if self.repeat:
                self.elapsed = 0.0
            else:
                self.finished = True
            if self.on_complete:
                self.on_complete()

    @property
    def progress(self):
        return min(1.0, self.elapsed / self.duration) if self.duration > 0 else 1.0


class Defer:
    """fkengine.game.data.Defer — ejecucion diferida (cola por frames)."""

    def __init__(self):
        self.queue = []

    def defer(self, fn, delay_frames=1):
        self.queue.append([fn, delay_frames])

    def tick(self, dt):
        remaining = []
        for item in self.queue:
            item[1] -= 1
            if item[1] <= 0:
                item[0]()
            else:
                remaining.append(item)
        self.queue = remaining
