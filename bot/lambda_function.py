from dataclasses import dataclass
from datetime import datetime
import logging
import json
import requests
from typing import Callable, Literal


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
from mlb.api import get_al_west_standings_text, get_game
from mlb.mlb_dataclasses import Game, Team
from mlb.series import series_sweep_outcome
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


def _send_standings_if_any(season: str) -> None:
    block = get_al_west_standings_text(season)
    if block:
        send_webhook(block)


def _post_final_sequence(score_line: str, gif_url: str, season: str) -> None:
    send_webhook(score_line)
    send_gif_via_webhook(gif_url=gif_url)
    _send_standings_if_any(season)


@dataclass(frozen=True)
class GameNotifyContext:
    """Snapshot of current game + Mariners/opponent sides for notification handlers."""

    game: Game
    last_game: Game | None
    mariners: Team
    opponent: Team

    @property
    def status(self) -> str:
        return self.game.status.detailedState

    @property
    def last_status(self) -> str | None:
        if self.last_game is None or getattr(self.last_game, "status", None) is None:
            return None
        return self.last_game.status.detailedState


def _notify_context(game: Game, last_update: InternalStatus) -> GameNotifyContext:
    last_game = last_update.game if last_update and getattr(last_update, "game", None) else None
    if game.teams.home.team.id == MARINERS_ID:
        mariners, opponent = game.teams.home, game.teams.away
        logger.info("Mariners are home; %s are away", opponent.team.name)
    else:
        mariners, opponent = game.teams.away, game.teams.home
        logger.info("Mariners are away; %s are home", opponent.team.name)
    return GameNotifyContext(game=game, last_game=last_game, mariners=mariners, opponent=opponent)


def _notify_scoring_if_changed(ctx: GameNotifyContext) -> str:
    """While detailedState is unchanged, post score changes only."""
    updated_score = check_scoring_changes(ctx.last_game, ctx.game)
    if not updated_score:
        return ""
    home_score, away_score = updated_score
    inning = ctx.game.linescore_position_label()
    header = (
        f"Scoring update ({inning}):\n"
        if inning
        else "Scoring update:\n"
    )
    message = (
        f"{header}{ctx.game.teams.home.team.name} - {home_score}\n"
        f"{ctx.game.teams.away.team.name} - {away_score}"
    )
    send_webhook(message)
    return message


FinalOutcome = Literal[
    "mariners_win_regular",
    "mariners_win_sweep",
    "mariners_loss_regular",
    "mariners_loss_sweep",
    "tie",
]


@dataclass(frozen=True)
class FinalAnnouncement:
    score_line: str
    gif_url: str


def _classify_final_outcome(ctx: GameNotifyContext) -> FinalOutcome:
    sweep = series_sweep_outcome(ctx.game, MARINERS_ID)
    m_score, o_score = ctx.mariners.score, ctx.opponent.score
    if m_score > o_score:
        return "mariners_win_sweep" if sweep == "mariners_sweep" else "mariners_win_regular"
    if m_score < o_score:
        return "mariners_loss_sweep" if sweep == "opponent_sweep" else "mariners_loss_regular"
    return "tie"


def _final_announcement_for_outcome(ctx: GameNotifyContext, outcome: FinalOutcome) -> FinalAnnouncement:
    mar, opp = ctx.mariners, ctx.opponent
    if outcome == "mariners_win_sweep":
        return FinalAnnouncement(
            score_line=(
                f"🧹 GOMS! The Mariners swept the {opp.team.name}! "
                f"Final: {mar.team.name} {mar.score}, {opp.team.name} {opp.score}."
            ),
            gif_url=GOMS_SWEEP_GIF,
        )
    if outcome == "mariners_win_regular":
        return FinalAnnouncement(
            score_line=(
                f"🎉 GOMS! Final — {mar.team.name}: {mar.score} - "
                f"{opp.team.name}: {opp.score}"
            ),
            gif_url=GOMS_GIF,
        )
    if outcome == "mariners_loss_sweep":
        return FinalAnnouncement(
            score_line=(
                f"🧹 BOOMS! The {opp.team.name} swept the Mariners. "
                f"Final: {mar.team.name} {mar.score}, {opp.team.name} {opp.score}."
            ),
            gif_url=BOOMS_SWEEP_GIF,
        )
    if outcome == "mariners_loss_regular":
        return FinalAnnouncement(
            score_line=(
                f"😞 BOOMS! Final — {mar.team.name}: {mar.score} - "
                f"{opp.team.name}: {opp.score}"
            ),
            gif_url=BOOMS_GIF,
        )
    return FinalAnnouncement(
        score_line=(
            f"⚾ Final tie — {mar.team.name}: {mar.score} - {opp.team.name}: {opp.score}"
        ),
        gif_url=GOMS_GIF,
    )


def _handle_game_start_notification(ctx: GameNotifyContext) -> str | None:
    if not _should_announce_game_start(ctx.last_game, ctx.game):
        return None
    message = (
        f"🚨 The game is about to start! {ctx.mariners.team.name} vs. "
        f"{ctx.opponent.team.name} 🚨"
    )
    send_webhook(message)
    return message


def _handle_final_notification(ctx: GameNotifyContext) -> str | None:
    if ctx.status not in FINAL_STATUSES:
        return None
    if _is_final_state(ctx.last_status):
        logger.info(
            "Skipping duplicate final message; last_status=%s, status=%s",
            ctx.last_status,
            ctx.status,
        )
        return ""
    outcome = _classify_final_outcome(ctx)
    announcement = _final_announcement_for_outcome(ctx, outcome)
    _post_final_sequence(announcement.score_line, announcement.gif_url, ctx.game.season)
    return announcement.score_line


_STATUS_TRANSITION_HANDLERS: tuple[
    Callable[[GameNotifyContext], str | None],
    ...,
] = (
    _handle_game_start_notification,
    _handle_final_notification,
)


def _notify_on_status_transition(ctx: GameNotifyContext) -> str:
    for handler in _STATUS_TRANSITION_HANDLERS:
        result = handler(ctx)
        if result is not None:
            return result
    return ""


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
    ctx = _notify_context(game, last_update)
    logger.info("Checking statuses; status=%s, last_status=%s", ctx.status, ctx.last_status)

    if ctx.last_status is not None and ctx.status == ctx.last_status:
        message = _notify_scoring_if_changed(ctx)
    else:
        message = _notify_on_status_transition(ctx)

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
