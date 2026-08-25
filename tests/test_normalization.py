from datetime import UTC, datetime

import pytest

from elitebet_ingestion.normalization import american_odds, normalize_match


def test_converts_decimal_and_fractional_odds() -> None:
    assert american_odds("2.50") == 150
    assert american_odds("1.50") == -200
    assert american_odds("3/2") == 150
    assert american_odds("-110") == -110


def test_normalizes_match_and_excludes_sgp() -> None:
    match = normalize_match(
        {
            "home": "Philadelphia Eagles",
            "away": "Dallas Cowboys",
            "start": "2026-08-25T19:30:00Z",
            "odds": [
                {"market": "Moneyline", "selection": "Philadelphia Eagles", "odds": "1.50"},
                {
                    "market": "Player Passing Yards",
                    "selection": "Dak Prescott Over 265.5",
                    "odds": "+105",
                },
                {"market": "SGP", "selection": "Eagles + player passing yards", "odds": "+300"},
            ],
        }
    )
    assert match.league == "NFL"
    assert match.start_time == datetime(2026, 8, 25, 19, 30, tzinfo=UTC)
    assert [odd.american_odds for odd in match.odds] == [-200, 105]


def test_rejects_zero_odds() -> None:
    with pytest.raises(ValueError):
        american_odds("0")


def test_normalizes_nfl_player_props() -> None:
    match = normalize_match(
        {
            "home_team": "Philadelphia Eagles",
            "away_team": "Dallas Cowboys",
            "start_time": "2026-09-10T20:20:00Z",
            "sport": "Football",
            "odds": [
                {
                    "market": "player_passing_yards",
                    "bet_name": "Dak Prescott Over 265.5",
                    "american_odds": -110,
                },
                {
                    "market": "player_anytime_td",
                    "bet_name": "Saquon Barkley Anytime Touchdown",
                    "american_odds": -125,
                },
            ],
        },
        league="NFL",
    )
    assert match.league == "NFL"
    assert match.sport == "Football"
    assert {odd.market for odd in match.odds} == {
        "player_passing_yards",
        "player_anytime_td",
    }
