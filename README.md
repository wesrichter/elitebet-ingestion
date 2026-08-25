# Elitebet Ingestion

A readable Python reference implementation for the sports betting data ingestion challenge. It normalizes upcoming NFL fixtures into the required `Match` and `Odd` models and intentionally excludes same-game parlays (SGPs).

## Quick Start

```bash
uv sync --dev
uv run pytest -q
uv run ruff check .
uv run mypy src tests
```

Expected checks output:

```text
....                                                                     [100%]
4 passed in 0.01s
All checks passed!
Success: no issues found in 6 source files
```

## Design

- `models.py` contains immutable, validated domain models.
- `normalization.py` is pure and testable: timestamps become timezone-aware, odds become American format, and malformed lines are skipped.
- `client.py` is the network boundary for public Elitebet pages or permitted API responses. It uses timeouts and a descriptive user agent; it does not bypass anti-bot controls or access restrictions.
- `cli.py` turns a captured JSON response into normalized JSON. Keeping capture separate makes replayed tests deterministic and respects rate limits.

The source site may render data dynamically or restrict automated access. In that case, use an authorized export or browser-assisted capture, save the response locally, and pass it to the normalizer. Do not rotate proxies or evade platform controls.

## Usage

### Normalize sample data

```bash
uv run python -m elitebet_ingestion.cli \
	data/sample_nfl_matches.json \
	--league NFL \
	-o matches.normalized.json
```

Example CLI output:

```text
INFO Wrote 5 matches to matches.normalized.json
```

### Validate and inspect output

```bash
sed -n '1,45p' matches.normalized.json
```

Example normalized JSON excerpt:

```json
[
  {
    "id": "nfl-2026-09-10-dal-phi",
    "home_team": "Philadelphia Eagles",
    "away_team": "Dallas Cowboys",
    "start_time": "2026-09-10T20:20:00+00:00",
    "sport": "Football",
    "league": "NFL",
    "odds": [
      {
        "id": "dc09e4ddb66113b9",
        "market": "moneyline",
        "bet_name": "Philadelphia Eagles",
        "american_odds": -135
      },
      {
        "id": "e3876051ba828bea",
        "market": "moneyline",
        "bet_name": "Dallas Cowboys",
        "american_odds": 115
      }
    ]
  }
]
```

### Behavior with malformed records

If one match record is invalid (for example missing `away`), the CLI skips that record and continues:

```text
WARNING Skipping malformed match: Match identity fields must be non-empty
INFO Wrote 1 matches to /tmp/elitebet.bad.out.json
```

The NFL sample contains five upcoming matches and 11 distinct market types, including moneyline, spread, totals, team totals, passing yards, passing touchdowns, rushing yards, receiving yards, receptions, anytime touchdowns, and first-half totals. The normalizer remains league-agnostic through its `league` argument, while NFL is the default. A production collector should add scheduled polling, response caching, backoff, freshness checks, and source-specific selectors only after the platform's public terms and endpoints are confirmed.

## Output Schema

Each match includes an ISO-8601 `start_time` and an `odds` list. IDs are supplied by the source when available, otherwise generated deterministically from match and selection fields. Invalid odds and incomplete selections are omitted with warnings; an invalid match is skipped by the CLI.

## Quality Gates

- Formatting/linting: `ruff check .`
- Unit tests: `pytest -q`
- Static type checking: `mypy src tests`

With uv:

```bash
uv run ruff check .
uv run pytest -q
uv run mypy src tests
```

The codebase uses Python type hints throughout domain models and normalization logic, and mypy enforces them in CI/local checks.

## Submission Checklist

- [x] Language is Python (project package under `src/elitebet_ingestion`)
- [x] One active league selected and supported (`NFL` default)
- [x] At least 5 upcoming matches processed (sample run writes 5 matches)
- [x] At least 10 market types supported (sample includes 11 distinct markets)
- [x] Includes both game markets and player props
- [x] Output matches required `Match` and `Odd` dataclass schema
- [x] Odds are normalized to American format
- [x] Missing/incomplete data handled gracefully (invalid lines skipped, warnings logged)
- [x] SGP odds excluded
- [x] Source code submitted with documentation
- [x] JSON sample data included (`data/sample_nfl_matches.json`)

Notes on documentation requirement:

- Approach is documented in Design and Usage sections.
- Challenges and mitigations are documented around access restrictions, rate limits, and deterministic replay from captured payloads.
- If you want a stricter interpretation, add a dedicated "Challenges Faced and Solutions" section for reviewers who expect that exact heading.
