"""
Leaderboards del binario — réplica literal (fkengine.game.leaderboards.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados del rango 0x1414).

    Leaderboard / LeaderboardBase — base
    LeaderboardStrike / LeaderboardStrikeView / LeaderboardStrikeViewItem
    LeaderboardConquest / LeaderboardConquestRow
    LeaderboardCTF / LeaderboardCTFCarrier / LeaderboardCTFScoreboard
    LeaderboardGuilds
    LeaderboardSlot
    LeaderboardTeam / TeamView / TeamObject / TeamObjectGuild / TeamViewGuild
"""


class LeaderboardSlot:
    """fkengine.game.leaderboards.LeaderboardSlot — slot del leaderboard."""

    def __init__(self, rank=0, name="", score=0.0, entity_id=None):
        self.rank = rank
        self.name = name
        self.score = score
        self.entity_id = entity_id  # el > del visor compara contra esto


class LeaderboardBase:
    """Base de leaderboard."""

    NAME = "base"

    def __init__(self):
        self.slots = []
        self.visible = False

    def update(self, slots):
        self.slots = slots
        self.visible = bool(slots)

    def top(self, n=10):
        return self.slots[:n]


class Leaderboard(LeaderboardBase):
    """fkengine.game.leaderboards.Leaderboard — el leaderboard normal
    (masa; el visor lo muestra con nombres reales del op16)."""

    NAME = "normal"

    def __init__(self):
        super().__init__()


class LeaderboardStrike(LeaderboardBase):
    """leaderboardstrike.LeaderboardStrike — modo strike."""

    NAME = "strike"


class LeaderboardStrikeView(LeaderboardBase):
    """Vista del strike."""

    NAME = "strike_view"


class LeaderboardStrikeViewItem(LeaderboardSlot):
    """Item de la vista del strike."""

    def __init__(self, rank=0, name="", score=0.0):
        super().__init__(rank, name, score)


class LeaderboardConquest(LeaderboardBase):
    """Modo conquista."""

    NAME = "conquest"


class LeaderboardConquestRow(LeaderboardSlot):
    """Fila de conquista."""


class LeaderboardCTF(LeaderboardBase):
    """fkengine.game.leaderboards.LeaderboardCTF — leaderboard CTF
    (el visor NO lo muestra en CTF: el usuario confirmo que el binario
    no lo hace)."""

    NAME = "ctf"


class LeaderboardCTFCarrier(LeaderboardSlot):
    """Portador de la bandera en CTF."""


class LeaderboardCTFScoreboard(LeaderboardBase):
    """Scoreboard CTF."""

    NAME = "ctf_score"


class LeaderboardGuilds(LeaderboardBase):
    """Leaderboard de gremios."""

    NAME = "guilds"


class LeaderboardTeam(LeaderboardBase):
    """Leaderboard por equipos."""

    NAME = "team"


class TeamObject:
    """fkengine.game.leaderboards.TeamObject — objeto de equipo."""

    def __init__(self, team_id=0, name="", score=0.0):
        self.team_id = team_id
        self.name = name
        self.score = score


class TeamObjectGuild(TeamObject):
    """Equipo de gremio."""

    def __init__(self, guild_id=0, name="", score=0.0):
        super().__init__(guild_id, name, score)
        self.guild_id = guild_id


class TeamView(LeaderboardBase):
    """Vista de equipo."""

    NAME = "team_view"


class TeamViewGuild(TeamView):
    """Vista de equipo de gremio."""

    NAME = "team_view_guild"
