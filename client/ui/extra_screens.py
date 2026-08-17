"""
Pantallas adicionales — réplica literal (fkengine.gui.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    FindGuild / GuildRow     — busqueda de gremios
    ExperienceBar            — barra de experiencia
    TeamMap / ITeamMapEntity — mapa del equipo
    BoardViewItem            — item de vista de tablero
"""


class GuildRow:
    """fkengine.gui.findguild.GuildRow — fila de gremio."""

    def __init__(self, name="", members=0, level=0):
        self.name = name
        self.members = members
        self.level = level


class FindGuild:
    """fkengine.gui.findguild.FindGuild — busqueda de gremios."""

    def __init__(self):
        self.rows = []
        self.query = ""

    def search(self, query):
        self.query = query
        return [r for r in self.rows if query.lower() in r.name.lower()]


class ExperienceBar:
    """fkengine.gui.experiencebar.ExperienceBar — barra de experiencia."""

    def __init__(self, level=0, xp=0, xp_next=100):
        self.level = level
        self.xp = xp
        self.xp_next = xp_next

    def add_xp(self, xp):
        self.xp += xp
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = int(self.xp_next * 1.5)

    @property
    def progress(self):
        return min(1.0, self.xp / self.xp_next) if self.xp_next > 0 else 1.0


class ITeamMapEntity:
    """fkengine.gui.teammap.ITeamMapEntity — entidad del mapa de equipo."""

    def __init__(self):
        self.x = 0.0
        self.z = 0.0


class TeamMap:
    """fkengine.gui.teammap.TeamMap — mapa del equipo."""

    def __init__(self):
        self.entities = []

    def add(self, entity):
        self.entities.append(entity)


class BoardViewItem:
    """fkengine.gui.components.boardview.BoardViewItem — item de tablero."""

    def __init__(self, label="", value=0):
        self.label = label
        self.value = value
