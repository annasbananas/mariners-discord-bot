from datetime import datetime
import logging
import json
import requests


from constants import (
    BOOMS_GIF,
    GOMS_GIF,
    MARINERS_ID,
    S3_BUCKET_NAME,
    S3_OBJECT_KEY,
    LIVE_STATUSES,
    FINAL_STATUSES,
    WEBHOOK_URL,
)
from internal_status import InternalStatus
from logging_config import configure_logging
from mlb.api import get_game
from mlb.mlb_dataclasses import Game
from s3 import get_s3_object, put_s3_object
from webhooks import send_webhook

configure_logging()
logger = logging.getLogger(__name__)


def send_gif_via_webhook(gif_url: str):
    payload = {"embeds": [{"image": {"url": gif_url}}]}
    return requests.post(WEBHOOK_URL, json=payload, timeout=10)


def get_current_status():
    logger.info("Looking for object: bucket=%s, key=%s", S3_BUCKET_NAME, S3_OBJECT_KEY)
    s3_object = get_s3_object(S3_BUCKET_NAME, S3_OBJECT_KEY)
    if not s3_object or "Body" not in s3_object:
        logger.info("Couldn't find S3 object")
        return InternalStatus({}, "")

    status = s3_object["Body"].read().decode("utf-8")
    if status:
        logger.info("Found previous status; status=%s", status)
        internal_status = InternalStatus.from_dict(json.loads(status))
        return internal_status
    else:
        return InternalStatus({}, "")


def check_scoring_changes(previous_game: Game, current_game: Game):
    # Return: (home score, away score)
    previous_score = (previous_game.teams.home.score, previous_game.teams.away.score)
    current_score = (current_game.teams.home.score, current_game.teams.away.score)

    logger.info(
        "Scoring update: previous_score=%s, current_score=%s",
        previous_score,
        current_score,
    )
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
    logger.info("Checking statuses; status=%s, last_status=%s", status, last_status)
    message = ""
    if game.teams.home.team.id == MARINERS_ID:
        mariners = game.teams.home
        opponent = game.teams.away
        logger.info("Mariners are home; %s are away", opponent.team.name)
    else:
        mariners = game.teams.away
        opponent = game.teams.home
        logger.info("Mariners are away; %s are home", opponent.team.name)

    if last_status is not None and status == last_status:
        updated_score = check_scoring_changes(last_update.game, game)
        if updated_score:
            home_score, away_score = updated_score
            message = f"Scoring update:\n{game.teams.home.team.name} - {home_score}\n{game.teams.away.team.name} - {away_score}"
            send_webhook(message)
    else:
        if status in LIVE_STATUSES:
            message = f"🚨 The game is about to start! {mariners.team.name} vs. {opponent.team.name} 🚨"
            send_webhook(message)
        elif status in FINAL_STATUSES:
            if mariners.score > opponent.score:
                message = f"🎉 GOMS! Final score\n{mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}.\nThe Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
                send_webhook(message)
                send_gif_via_webhook(gif_url=GOMS_GIF)
            else:
                message = f"😞 BOOMS! Final score - {mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}. The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
                send_webhook(message)
                send_gif_via_webhook(gif_url=BOOMS_GIF)
    logger.info(message)
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
