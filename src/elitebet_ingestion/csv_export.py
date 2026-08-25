"""Export normalized match JSON into a flat CSV of odds rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def export_odds_csv(input_path: Path, output_path: Path) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of normalized match objects")

    fieldnames = [
        "match_id",
        "home_team",
        "away_team",
        "start_time",
        "sport",
        "league",
        "odd_id",
        "market",
        "bet_name",
        "american_odds",
    ]
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for match in payload:
            if not isinstance(match, dict):
                continue
            odds = match.get("odds", [])
            if not isinstance(odds, list):
                continue
            for odd in odds:
                if not isinstance(odd, dict):
                    continue
                writer.writerow(
                    {
                        "match_id": str(match.get("id", "")),
                        "home_team": str(match.get("home_team", "")),
                        "away_team": str(match.get("away_team", "")),
                        "start_time": str(match.get("start_time", "")),
                        "sport": str(match.get("sport", "")),
                        "league": str(match.get("league", "")),
                        "odd_id": str(odd.get("id", "")),
                        "market": str(odd.get("market", "")),
                        "bet_name": str(odd.get("bet_name", "")),
                        "american_odds": str(odd.get("american_odds", "")),
                    }
                )
                row_count += 1
    return row_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert normalized Elitebet JSON into a flat Odds CSV."
    )
    parser.add_argument("input", type=Path, help="Normalized JSON file")
    parser.add_argument("-o", "--output", type=Path, default=Path("odds.normalized.csv"))
    args = parser.parse_args()

    rows = export_odds_csv(args.input, args.output)
    print(f"Wrote {rows} odds rows to {args.output}")


if __name__ == "__main__":
    main()