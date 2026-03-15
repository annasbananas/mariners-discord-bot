import datetime
import logging
import requests

from pytz import timezone
from constants import MARINERS_ID
from mlb.mlb_dataclasses import Game

logger = logging.getLogger(__name__)

def get_mlb_url(team_id):
    today = datetime.datetime.now(timezone("America/Los_Angeles")).date()
    date_str = today.strftime("%Y-%m-%d")
    return f"https://statsapi.mlb.com/api/v1/schedule?teamId={team_id}&date={date_str}&sportId=1"

def get_game():
    url = get_mlb_url(MARINERS_ID)
    try:
        response = requests.get(url, []).json()
        return Game.from_dict(response)
    except Exception as e:
        logger.error(f"Error checking game status: {e}")
        return None