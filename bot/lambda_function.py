from datetime import datetime, timedelta
import logging
import json
import requests
from typing import Literal, Optional


from constants import (
    BOOMS_GIF,
    GOMS_GIF,
    MARINERS_ID,
    S3_BUCKET_NAME,
    S3_OBJECT_KEY,
    FINAL_STATUSES,
    WEBHOOK_URL,
    GOMS_SWEEP_GIF,
    BOOMS_SWEEP_GIF,
)
from internal_status import InternalStatus
from logging_config import configure_logging
from mlb.api import get_al_west_standings_text, get_game, get_schedule_games
from mlb.mlb_dataclasses import Game
from s3 import get_s3_object, put_s3_object
from webhooks import send_webhook

configure_logging()
logger = logging.getLogger(__name__)


def _is_final_state(detailed_state):
    """True if MLB detailedState is a game-ended status."""
    return detailed_state is not None and detailed_state in FINAL_STATUSES


def _abstract_game_state(game: Game | None):
    """MLB abstractGameState: Preview | Live | Final. None if game/status missing."""
    if game is None or not isinstance(game, Game):
        return None
    return getattr(game.status, "abstractGameState", None)


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


def _should_announce_game_start(last_game: Game | None, current_game: Game) -> bool:
    """
    Fire only on Preview -> Live, not when detailedState flips during a live game
    (e.g. In Progress <-> Delayed) while abstractGameState stays Live.
    """
    if current_game.status.abstractGameState != "Live":
        return False
    last_abs = _abstract_game_state(last_game)
    return last_abs != "Live"


def send_gif_via_webhook(gif_url: str):
    payload = {"embeds": [{"image": {"url": gif_url}}]}
    return requests.post(WEBHOOK_URL, json=payload, timeout=10)


def _final_message_with_standings(body: str, season: str) -> str:
    block = get_al_west_standings_text(season)
    if block:
        return f"{body}\n\n{block}"
    return body


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
    last_game = last_update.game if last_update and getattr(last_update, "game", None) else None
    last_status = last_game.status.detailedState if last_game and getattr(last_game, "status", None) else None
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
        if _should_announce_game_start(last_game, game):
            message = f"🚨 The game is about to start! {mariners.team.name} vs. {opponent.team.name} 🚨"
            send_webhook(message)
        elif status in FINAL_STATUSES:
            # MLB often moves between final-ish strings (e.g. Game Over -> Final).
            # Only announce once per game end, not on every relabel.
            if _is_final_state(last_status):
                logger.info(
                    "Skipping duplicate final message; last_status=%s, status=%s",
                    last_status,
                    status,
                )
            elif mariners.score > opponent.score:
                sweep = series_sweep_outcome(game, MARINERS_ID)
                if sweep == "mariners_sweep":
                    message = (
                        f"🧹 GOMS! The Mariners swept the {opponent.team.name}!\n"
                        f"Final: {mariners.team.name} {mariners.score}, {opponent.team.name} {opponent.score}.\n"
                        f"The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
                    )
                    send_gif_via_webhook(gif_url=GOMS_SWEEP_GIF)
                else:
                    message = f"🎉 GOMS! Final score\n{mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}.\nThe Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
                send_webhook(message)
                send_gif_via_webhook(gif_url=GOMS_GIF)
                send_webhook(_final_message_with_standings(message, game.season))

            else:
                sweep = series_sweep_outcome(game, MARINERS_ID)
                if sweep == "opponent_sweep":
                    message = (
                        f"🧹 BOOMS! The {opponent.team.name} swept the Mariners.\n"
                        f"Final: {mariners.team.name} {mariners.score}, {opponent.team.name} {opponent.score}.\n"
                        f"The Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
                    )
                    send_gif_via_webhook(gif_url=BOOMS_SWEEP_GIF)
                else:
                    message = f"😞 BOOMS! Final score\n{mariners.team.name}: {mariners.score} - {opponent.team.name}: {opponent.score}. \nThe Mariners are now {mariners.leagueRecord.wins}-{mariners.leagueRecord.losses} ({mariners.leagueRecord.pct})"
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
