from dataclasses import dataclass
from mlb_dataclasses import Game

@dataclass
class InternalStatus:
    game: Game
    last_update: str
