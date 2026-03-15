from dataclasses import dataclass
from mlb.mlb_dataclasses import Game

@dataclass
class InternalStatus:
    game: Game
    last_update: str

    @classmethod
    def from_dict(cls, d: dict[str]) -> "InternalStatus":
        game_dict = d["game"] if "game" in d else d
        game = Game.from_dict(game_dict)
        last_update = d["last_update"] if "last_update" in d else d
        return cls(game, last_update)
    
    def to_dict(self) -> dict:
        return {
            "game": self.game.to_dict(),
            "last_updated": self.last_update.isoformat()
        }