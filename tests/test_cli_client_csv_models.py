from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from elitebet_ingestion import cli
from elitebet_ingestion.client import ElitebetClient
from elitebet_ingestion.csv_export import export_odds_csv
from elitebet_ingestion.models import Match, Odd


def test_cli_skips_invalid_match_and_writes_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    input_payload = [
        {
            "id": "m1",
            "home": "Philadelphia Eagles",
            "away": "Dallas Cowboys",
            "start": "2026-09-10T20:20:00Z",
            "odds": [{"market": "Moneyline", "selection": "Philadelphia Eagles", "odds": "1.50"}],
        },
        {
            "id": "bad",
            "home": "OnlyOneTeam",
            "start": "2026-09-10T20:20:00Z",
            "odds": [],
        },
    ]
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "elitebet-ingest",
            str(input_path),
            "--league",
            "NFL",
            "-o",
            str(output_path),
        ],
    )

    cli.main()

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(written) == 1
    assert written[0]["league"] == "NFL"


def test_client_records_from_json_envelopes() -> None:
    items = [{"id": "a"}, {"id": "b"}]
    assert len(ElitebetClient.records_from_json(items)) == 2
    assert len(ElitebetClient.records_from_json({"matches": items})) == 2
    assert len(ElitebetClient.records_from_json({"events": items})) == 2
    assert len(ElitebetClient.records_from_json({"fixtures": items})) == 2
    assert len(ElitebetClient.records_from_json({"data": items})) == 2
    assert ElitebetClient.records_from_json({"unknown": []}) == []


def test_client_fetch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        text = "ok"

        def raise_for_status(self) -> None:
            return None

    def _fake_get(*args: object, **kwargs: object) -> _Response:
        return _Response()

    monkeypatch.setattr(httpx, "get", _fake_get)
    client = ElitebetClient(base_url="https://example.com", timeout=5.0)
    assert client.fetch("/foo") == "ok"


def test_client_fetch_wraps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get(*args: object, **kwargs: object) -> str:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", _fake_get)
    client = ElitebetClient(base_url="https://example.com")
    with pytest.raises(RuntimeError, match="Elitebet request failed"):
        client.fetch("/foo")


def test_export_odds_csv_writes_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "matches.normalized.json"
    output_path = tmp_path / "odds.csv"
    payload = [
        {
            "id": "m1",
            "home_team": "A",
            "away_team": "B",
            "start_time": "2026-09-10T20:20:00+00:00",
            "sport": "Football",
            "league": "NFL",
            "odds": [
                {
                    "id": "o1",
                    "market": "moneyline",
                    "bet_name": "A",
                    "american_odds": -110,
                }
            ],
        }
    ]
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    rows = export_odds_csv(input_path, output_path)

    assert rows == 1
    csv_text = output_path.read_text(encoding="utf-8")
    assert "match_id,home_team,away_team" in csv_text
    assert "m1,A,B" in csv_text


def test_export_odds_csv_rejects_non_list_payload(tmp_path: Path) -> None:
    input_path = tmp_path / "not_list.json"
    input_path.write_text(json.dumps({"matches": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Input JSON must be a list"):
        export_odds_csv(input_path, tmp_path / "out.csv")


def test_models_validation_and_serialization() -> None:
    odd = Odd("o1", "moneyline", "Eagles", -120)
    match = Match(
        "m1",
        "Eagles",
        "Cowboys",
        datetime(2026, 9, 10, 20, 20, tzinfo=UTC),
        "Football",
        "NFL",
        [odd],
    )
    serialized = match.to_dict()
    assert serialized["start_time"] == "2026-09-10T20:20:00+00:00"


def test_models_reject_invalid_fields() -> None:
    with pytest.raises(ValueError):
        Odd("", "moneyline", "Eagles", -120)
    with pytest.raises(ValueError):
        Odd("o1", "moneyline", "Eagles", 0)
    with pytest.raises(ValueError):
        Match(
            "m1",
            "Eagles",
            "eagles",
            datetime(2026, 9, 10, 20, 20, tzinfo=UTC),
            "Football",
            "NFL",
            [],
        )