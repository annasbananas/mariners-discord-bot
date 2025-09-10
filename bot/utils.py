import datetime
import logging
from pytz import timezone
from constants import *
import requests

logger = logging.getLogger(__name__)

def get_mlb_url():
    today = datetime.datetime.now(timezone("America/Los_Angeles")).date()
    date_str = today.strftime("%Y-%m-%d")
    return f"https://statsapi.mlb.com/api/v1/schedule?teamId={MARINERS_ID}&date={date_str}&sportId=1"

def get_mlb_schedule_for_mariners():
    url = get_mlb_url()
    try:
        response = requests.get(url, []).json()
        return parse_mlb_schedule_payload(response)
    except Exception as e:
        print("Error checking game status:", e)

def parse_mlb_schedule_payload(response):
    games = response.get("dates", [])
    if games:
        game = games[0]["games"][0]
        logger.info(f"Today's game: {game}")
        mariners_team = game["teams"]["home"] if game["teams"]["home"]["team"]["id"] == MARINERS_ID else game["teams"]["away"]
        opponent_team = game["teams"]["away"] if mariners_team == game["teams"]["home"] else game["teams"]["home"]
        return game, mariners_team, opponent_team
    else:
        logger.info("No games today :'(")
        return {}, {}, {}