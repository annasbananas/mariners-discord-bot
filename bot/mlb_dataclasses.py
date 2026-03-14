from dataclasses import dataclass

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

@dataclass
class Teams:
    home: TeamScore
    away: TeamScore

@dataclass
class Team:
    team: TeamInfo
    leagueRecord: LeagueRecord
    score: int
    splitSquad: bool
    seriesNumber: int

@dataclass
class TeamInfo:
    id: int
    name: str
    link: str

@dataclass
class LeagueRecord:
    wins: int
    losses: int
    pct: string

@dataclass
class Status:
    abstractGameState: str
    codedGameState: str
    detailedState: str
    statusCode: str
    startTimeTBD: bool
    abstractGameCode: str