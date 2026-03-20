from datetime import datetime
import logging
import json

from constants import (
    MARINERS_ID,
    S3_BUCKET_NAME,
    S3_OBJECT_KEY,
    LIVE_STATUSES,
    FINAL_STATUSES,
)
from internal_status import InternalStatus
from mlb.api import get_game
from mlb.mlb_dataclasses import Game
from s3 import get_s3_object, put_s3_object
from webhooks import send_webhook

logger = logging.getLogger(__name__)


def get_current_status():
    s3_object = get_s3_object(S3_BUCKET_NAME, S3_OBJECT_KEY)
    if not s3_object or "Body" not in s3_object:
        logger.info("Couldn't find S3 object")
        return InternalStatus({}, "")

    status = s3_object["Body"].read().decode("utf-8")
    if status:
        logger.info("Found previous status")
        return InternalStatus.from_dict(json.loads(status))
    else:
        return InternalStatus({}, "")


def check_scoring_changes(previous_game: Game, current_game: Game):
    # Return: (home score, away score)
    previous_score = (previous_game.teams.home.score, previous_game.teams.away.score)
    current_score = (current_game.teams.home.score, current_game.teams.away.score)
    if previous_score != current_score:
        return current_score
    else:
        return False

def check_statuses(game: Game, last_update: InternalStatus):
    status = game.status.detailedState
    last_status = (
        last_update.game.status.detailedState
        if last_update and getattr(last_update, "game", None)
        else None
    )
    
    message = ""
    if game.teams.home.team.id == MARINERS_ID:
        mariners = game.teams.home
        opponent = game.teams.away
    else:
        mariners = game.teams.away
        opponent = game.teams.home
    
    if last_status is not None and status == last_status:
        updated_score = check_scoring_changes(last_update.game, game)
        if updated_score:
            home_score, away_score = updated_score
            message = f"Scoring update: {game.teams.home}-{home_score}, {game.teams.away}-{away_score}"
    else:
        if status in LIVE_STATUSES:
            message = f"🚨 The game is about to start! {mariners.team.name} vs. {opponent.team.name} 🚨"
        elif status in FINAL_STATUSES:
            if mariners.score > opponent.score:
                message = f"🎉 GOMS! Final score - {mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}. The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
            else:
                message = f"😞 BOOMS! Final score - {mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}. The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"

    if message:
        send_webhook(message)
    update_status(game, datetime.now())


def update_status(game, last_update):
    internal_status = InternalStatus(game=game, last_update=last_update)
    put_s3_object(
        S3_BUCKET_NAME,
        S3_OBJECT_KEY,
        json.dumps(internal_status.to_dict()),
    )


def main():
    last_update = get_current_status()
    game = get_game()
    if game:
        check_statuses(game, last_update)


def lambda_handler(event, context):
    main()


if __name__ == "__main__":
    main()
