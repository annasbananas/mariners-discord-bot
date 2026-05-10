from datetime import datetime, timedelta
from typing import Literal, Optional

from constants import FINAL_STATUSES
from mlb.api import get_schedule_games
from mlb.mlb_dataclasses import Game

SweepKind = Literal["mariners_sweep", "opponent_sweep"]


def _mariners_won_game(game: Game, mariners_id: int) -> Optional[bool]:
    """True/False if decided from MLB fields or score; None if unclear."""
    if game.teams.home.team.id == mariners_id:
        side, other = game.teams.home, game.teams.away
    elif game.teams.away.team.id == mariners_id:
        side, other = game.teams.away, game.teams.home
    else:
        return None
    if side.isWinner is True:
        return True
    if side.isWinner is False:
        return False
    if other.isWinner is True:
        return False
    if other.isWinner is False:
        return True
    if side.score == other.score:
        return None
    return side.score > other.score


def series_sweep_outcome(game: Game, mariners_id: int) -> Optional[SweepKind]:
    """
    After a series finale, return whether the Mariners swept or were swept.
    Uses schedule games sharing seriesNumber and opponent; None if not a sweep or uncertain.
    """
    if game.gamesInSeries < 2 or game.seriesGameNumber != game.gamesInSeries:
        return None
    if not game.seriesNumber:
        return None
    opponent_id = (
        game.teams.away.team.id
        if game.teams.home.team.id == mariners_id
        else game.teams.home.team.id
    )
    try:
        end = datetime.strptime(game.officialDate, "%Y-%m-%d").date()
    except ValueError:
        return None
    start = end - timedelta(days=7)
    start_s, end_s = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    candidates = [
        g
        for g in get_schedule_games(mariners_id, start_s, end_s)
        if g.season == game.season
        and g.seriesNumber == game.seriesNumber
        and mariners_id in (g.teams.home.team.id, g.teams.away.team.id)
        and opponent_id in (g.teams.home.team.id, g.teams.away.team.id)
    ]
    finals = [g for g in candidates if g.status.detailedState in FINAL_STATUSES]
    if len(finals) != game.gamesInSeries:
        return None
    outcomes = [_mariners_won_game(g, mariners_id) for g in finals]
    if any(o is None for o in outcomes):
        return None
    if all(outcomes):
        return "mariners_sweep"
    if not any(outcomes):
        return "opponent_sweep"
    return None
