"""
Descarga e invitaciones — réplica literal (fkengine.game.downloader.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    Downloader        — descarga de assets del juego (por HTTP)
    DownloaderAsset   — asset descargado (en resources/__init__.py)
    IDownloadReceiver — interfaz receptor
    GameInviteReceiver — receptor de invitaciones a salas
"""


class IDownloadReceiver:
    """fkengine.game.downloader.IDownloadReceiver — interfaz."""

    def on_download_progress(self, url, loaded, total):
        pass

    def on_download_complete(self, url, data):
        pass

    def on_download_error(self, url, error):
        pass


class Downloader:
    """fkengine.game.downloader.Downloader — descarga de assets."""

    def __init__(self):
        self.receivers = []
        self.cache = {}

    def register(self, receiver):
        self.receivers.append(receiver)

    def get(self, url):
        return self.cache.get(url)


class GameInviteReceiver:
    """fkengine.game.GameInviteReceiver — invitaciones a salas
    (el visor las recibe: [invite: s18394.mitos.is:443|token])."""

    def __init__(self):
        self.on_invite = None

    def receive(self, server, token):
        if self.on_invite:
            self.on_invite(server, token)
