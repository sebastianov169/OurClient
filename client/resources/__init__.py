"""
Recursos del binario — réplica literal (fkengine.loaders / file / db / dm).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    LoadingEvents       (FUN_1414ee180, vtable DAT_1421cc488, ctor FUN_1414ee2d0)
    DownloaderAsset     (FUN_1406804e0, vtable DAT_1421b8f70)
    ImageLoader, LoadingBase (fkengine.loaders.*)
    NativeFileManager   (fkengine.file.native.NativeFileManager)
    DatabaseManager     (fkengine.db.DatabaseManager)
    URLStreamTagged     (fkengine.dm.URLStreamTagged)
"""


class LoadingEvents:
    """fkengine.loaders.LoadingEvents (FUN_1414ee2d0) — eventos de carga."""

    START = "start"
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"

    def __init__(self):
        self.listeners = []

    def on(self, event, cb):
        self.listeners.append((event, cb))

    def emit(self, event, *args):
        for ev, cb in self.listeners:
            if ev == event:
                cb(*args)


class DownloaderAsset:
    """fkengine.game.downloader.DownloaderAsset (FUN_1406804e0) — asset
    descargado (los recursos del juego bajan por HTTP)."""

    def __init__(self, url=""):
        self.url = url
        self.data = None
        self.loaded = False


class ImageLoader:
    """fkengine.loaders.ImageLoader — carga imagenes (atlas/fnt)."""

    def __init__(self):
        self.cache = {}

    def load(self, path):
        if path not in self.cache:
            self.cache[path] = None  # pendiente: decodificar el formato real
        return self.cache[path]
