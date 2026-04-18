import datetime
import logging
from typing import List, Optional

import requests

from pytz import timezone
from constants import AL_LEAGUE_ID, AL_WEST_DIVISION_ID, MARINERS_ID
from mlb.mlb_dataclasses import Game

logger = logging.getLogger(__name__)


def get_mlb_url(team_id):
    today = datetime.datetime.now(timezone("America/Los_Angeles")).date()
    date_str = today.strftime("%Y-%m-%d")
    return f"https://statsapi.mlb.com/api/v1/schedule?teamId={team_id}&date={date_str}&sportId=1"


def get_schedule_url(team_id: int, start_date: str, end_date: str) -> str:
    return (
        f"https://statsapi.mlb.com/api/v1/schedule?teamId={team_id}"
        f"&startDate={start_date}&endDate={end_date}&sportId=1"
    )


def get_schedule_games(team_id: int, start_date: str, end_date: str) -> List[Game]:
    """All games for a team in an inclusive date range (YYYY-MM-DD)."""
    url = get_schedule_url(team_id, start_date, end_date)
    try:
        data = requests.get(url, timeout=20).json()
    except Exception as e:
        logger.error("Error fetching schedule %s–%s: %s", start_date, end_date, e)
        return []
    games: List[Game] = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            games.append(Game.from_schedule_game(g))
    return games


def get_al_west_standings_text(season: str) -> Optional[str]:
    """
    Multi-line AL West regular-season standings for the given year, or None if unavailable.
    """
    if not season:
        return None
    url = (
        "https://statsapi.mlb.com/api/v1/standings"
        f"?season={season}&leagueId={AL_LEAGUE_ID}&standingsTypes=regularSeason"
    )
    try:
        data = requests.get(url, timeout=20).json()
    except Exception as e:
        logger.error("Error fetching standings for season %s: %s", season, e)
        return None
    for record in data.get("records", []):
        div = record.get("division") or {}
        if div.get("id") != AL_WEST_DIVISION_ID:
            continue
        lines = ["AL West standings:"]
        teams = sorted(record.get("teamRecords", []), key=lambda tr: int(tr["divisionRank"]))
        for tr in teams:
            name = tr["team"]["name"]
            wins, losses = tr["wins"], tr["losses"]
            pct = tr.get("winningPercentage", "")
            dgb = tr.get("divisionGamesBack", "-")
            gb_suffix = ""
            if dgb not in (None, "", "-"):
                gb_suffix = f" ({dgb} GB)"
            lines.append(f"{tr['divisionRank']}. {name} {wins}-{losses} ({pct}){gb_suffix}")
        return "\n".join(lines)
    logger.warning("No AL West standings block in response for season %s", season)
    return None


def get_game():
    url = get_mlb_url(MARINERS_ID)
    try:
        response = requests.get(url, []).json()
        return Game.from_dict(response)
    except Exception as e:
        logger.error(f"Error checking game status: {e}")
        return None