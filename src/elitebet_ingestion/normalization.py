"""Pure normalization functions kept independent from network and HTML concerns."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .models import Match, Odd

_SGP_RE = re.compile(r"\b(?:same\s+game\s+parlay|sgp|multi[-\s]?bet)\b", re.IGNORECASE)


def american_odds(value: Any) -> int:
    """Convert common decimal/fractional/American representations to American odds."""
    if isinstance(value, bool):
        raise ValueError("boolean is not an odds value")
    text = str(value).strip().replace("−", "-")
    if not text:
        raise ValueError("empty odds value")
    if "/" in text:
        numerator, denominator = (float(part) for part in text.split("/", 1))
        decimal = 1 + numerator / denominator
    else:
        number = float(text.replace("+", ""))
        decimal = number if 1 < number < 100 else None
        if decimal is None:
            result = int(number)
            if result == 0:
                raise ValueError("American odds cannot be zero")
            return result
    if decimal <= 1:
        raise ValueError("decimal odds must be greater than 1")
    return round((decimal - 1) * 100) if decimal >= 2 else round(-100 / (decimal - 1))


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return digest


def normalize_match(raw: Mapping[str, Any], *, league: str = "NFL") -> Match:
    """Normalize one source record; raises ValueError for incomplete match data."""
    home = str(raw.get("home_team") or raw.get("home") or "").strip()
    away = str(raw.get("away_team") or raw.get("away") or "").strip()
    match_id = str(raw.get("id") or _stable_id(home, away, str(raw.get("start_time", ""))))
    start_value = raw.get("start_time") or raw.get("start")
    if isinstance(start_value, datetime):
        start_time = start_value
    else:
        start_time = datetime.fromisoformat(str(start_value).replace("Z", "+00:00"))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)

    odds: list[Odd] = []
    for index, item in enumerate(raw.get("odds", [])):
        if not isinstance(item, Mapping):
            continue
        fields = " ".join(
            str(item.get(key, "")) for key in ("market", "bet_name", "selection", "name")
        )
        if _SGP_RE.search(fields):
            continue
        market = str(item.get("market") or "unknown").strip().lower().replace(" ", "_")
        bet_name = str(
            item.get("bet_name") or item.get("selection") or item.get("name") or ""
        ).strip()
        if not bet_name:
            continue
        try:
            price = american_odds(item.get("american_odds", item.get("odds")))
        except (TypeError, ValueError):
            continue
        odd_id = str(item.get("id") or _stable_id(match_id, market, bet_name, str(index)))
        odds.append(Odd(odd_id, market, bet_name, price))

    return Match(
        match_id, home, away, start_time, str(raw.get("sport") or "Football"), league, odds
    )
