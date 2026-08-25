"""Domain models and serialization helpers for normalized betting data."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Odd:
    """One selectable betting line in American odds format."""

    id: str
    market: str
    bet_name: str
    american_odds: int

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.market.strip() or not self.bet_name.strip():
            raise ValueError("Odd id, market, and bet_name must be non-empty")
        if self.american_odds == 0:
            raise ValueError("American odds cannot be zero")


@dataclass(frozen=True, slots=True)
class Match:
    """A scheduled sporting event and its available betting lines."""

    id: str
    home_team: str
    away_team: str
    start_time: datetime
    sport: str
    league: str
    odds: list[Odd]

    def __post_init__(self) -> None:
        identity = (self.id, self.home_team, self.away_team, self.sport, self.league)
        if not all(value.strip() for value in identity):
            raise ValueError("Match identity fields must be non-empty")
        if self.home_team.casefold() == self.away_team.casefold():
            raise ValueError("Home and away teams must be different")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-ready data using ISO-8601 timestamps."""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        return data
