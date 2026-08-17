"""
Sonido del binario — réplica literal (fkengine.game.sounds.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    SpatialSoundsManager          — gestiona sonidos espaciales
    SpatialSoundPlayer            — reproductor espacial (posicion en el mundo)
    SpatialSoundPlayerShared      — compartido
    SpatialSoundPlayerSound       — un sonido

Los assets de audio estan embebidos en el exe; la capa de sonido del visor
(pygame.mixer) se conecta aqui cuando los assets se extraigan.
"""


class SpatialSoundPlayerSound:
    """fkengine.game.sounds.SpatialSoundPlayerSound — un sonido."""

    def __init__(self, asset_id="", volume=1.0):
        self.asset_id = asset_id
        self.volume = volume
        self.playing = False


class SpatialSoundPlayer:
    """fkengine.game.sounds.SpatialSoundPlayer — sonido en una posicion."""

    def __init__(self, x=0.0, z=0.0):
        self.x, self.z = x, z
        self.sounds = []

    def play(self, asset_id, volume=1.0):
        self.sounds.append(SpatialSoundPlayerSound(asset_id, volume))

    def set_position(self, x, z):
        self.x, self.z = x, z


class SpatialSoundPlayerShared(SpatialSoundPlayer):
    """Compartido entre reproductores."""

    def __init__(self):
        super().__init__()


class SpatialSoundsManager:
    """fkengine.game.sounds.SpatialSoundsManager — gestiona todos."""

    def __init__(self):
        self.players = []
        self.listener_x = 0.0
        self.listener_z = 0.0

    def add(self, player):
        self.players.append(player)

    def set_listener(self, x, z):
        self.listener_x, self.listener_z = x, z
