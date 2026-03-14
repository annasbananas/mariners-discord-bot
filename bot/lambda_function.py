from mlb_api import *
from s3 import *
from constants import *
from webhooks import *
import logging

logger = logging.getLogger(__name__)

def get_current_status():
    status = get_s3_object(S3_BUCKET_NAME, S3_OBJECT_KEY, "status.json")
    return InternalStatus.from_dict(json.loads(status))

def check_statuses(game):
    gamePk = game.gamePk
    status = game.status.detailedState

    if game.teams.home.teamInfo.id == MARINERS_ID:
        mariners = game.teams.home
        opponent = game.teams.away
    else:
        mariners = game.teams.away
        opponent = game.teams.home

    if status in LIVE_STATUSES:
        message = f"🚨 The game is about to start! {mariners.teamInfo.name} vs. {opponent.teamInfo.name} 🚨"
    elif status in FINAL_STATUSES:
        if mariners.score > opponent.score:
            message = f"🎉 GOMS! Final score - {mariners.teamInfo.name}: {mariners.score} - {opponent.teamInfo.name}: {opponent.score}. The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
        else:
            message = f"😞 BOOMS! Final score - {mariners.teamInfo.name}: {mariners.score} - {opponent.teamInfo.name}: {opponent.score}. The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
    else:
        logger.info(f"Game status {status} is not supported.")

    send_webhook(message)
    update_status(game, datetime.now())

def update_status(game, last_update):
    internal_status = InternalStatus(game, last_update)
    save_s3_object(S3_BUCKET_NAME, S3_OBJECT_KEY, "status.json", json.dumps(internal_status.to_dict()))

def main():
    current_status = get_current_status()
    game = get_game()
    if game:
        check_statuses(game)


def lambda_handler(event, context):    
    result = main()