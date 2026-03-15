from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TeamInfo:
    id: int
    name: str
    link: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TeamInfo":
        team = d["team"] if "team" in d else d
        return cls(id=team["id"], name=team["name"], link=team["link"])

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "link": self.link}


@dataclass
class LeagueRecord:
    wins: int
    losses: int
    pct: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LeagueRecord":
        rec = d["leagueRecord"] if "leagueRecord" in d else d
        return cls(wins=rec["wins"], losses=rec["losses"], pct=str(rec["pct"]))

    def to_dict(self) -> dict[str, Any]:
        return {"wins": self.wins, "losses": self.losses, "pct": self.pct}


@dataclass
class Status:
    abstractGameState: str
    codedGameState: str
    detailedState: str
    statusCode: str
    startTimeTBD: bool
    abstractGameCode: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Status":
        s = d["status"] if "status" in d else d
        return cls(
            abstractGameState=s["abstractGameState"],
            codedGameState=s["codedGameState"],
            detailedState=s["detailedState"],
            statusCode=s["statusCode"],
            startTimeTBD=s.get("startTimeTBD", False),
            abstractGameCode=s["abstractGameCode"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "abstractGameState": self.abstractGameState,
            "codedGameState": self.codedGameState,
            "detailedState": self.detailedState,
            "statusCode": self.statusCode,
            "startTimeTBD": self.startTimeTBD,
            "abstractGameCode": self.abstractGameCode,
        }


@dataclass
class Team:
    team: TeamInfo
    leagueRecord: LeagueRecord
    score: int
    splitSquad: bool
    seriesNumber: int

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Team":
        return cls(
            team=TeamInfo.from_dict(d),
            leagueRecord=LeagueRecord.from_dict(d),
            score=d.get("score", 0),
            splitSquad=d.get("splitSquad", False),
            seriesNumber=d.get("seriesNumber", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "team": self.team.to_dict(),
            "leagueRecord": self.leagueRecord.to_dict(),
            "score": self.score,
            "splitSquad": self.splitSquad,
            "seriesNumber": self.seriesNumber,
        }


@dataclass
class Teams:
    home: Team
    away: Team

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Teams":
        return cls(home=Team.from_dict(d["home"]), away=Team.from_dict(d["away"]))

    def to_dict(self) -> dict[str, Any]:
        return {"home": self.home.to_dict(), "away": self.away.to_dict()}


@dataclass
class Game:
    gamePk: int
    gameGuid: str
    link: str
    gameType: str
    season: str
    gameDate: str
    officialDate: str
    status: Status
    teams: Teams
    seriesDescription: str

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> Optional["Game"]:
        """Convert MLB API response to Game. Accepts full schedule or single game dict."""
        if not d:
            return None
        game_raw = d
        if "dates" in d:
            dates = d.get("dates", [])
            if not dates or not dates[0].get("games"):
                return None
            game_raw = dates[0]["games"][0]
        return cls(
            gamePk=game_raw["gamePk"],
            gameGuid=game_raw.get("gameGuid", ""),
            link=game_raw.get("link", ""),
            gameType=game_raw.get("gameType", ""),
            season=game_raw.get("season", ""),
            gameDate=game_raw.get("gameDate", ""),
            officialDate=game_raw.get("officialDate", ""),
            status=Status.from_dict(game_raw),
            teams=Teams.from_dict(game_raw["teams"]),
            seriesDescription=game_raw.get("seriesDescription", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gamePk": self.gamePk,
            "gameGuid": self.gameGuid,
            "link": self.link,
            "gameType": self.gameType,
            "season": self.season,
            "gameDate": self.gameDate,
            "officialDate": self.officialDate,
            "status": self.status.to_dict(),
            "teams": self.teams.to_dict(),
            "seriesDescription": self.seriesDescription,
        }
        




