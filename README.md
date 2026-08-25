# Elitebet Ingestion

A readable Python reference implementation for the sports betting data ingestion challenge. It normalizes upcoming NFL fixtures into the required `Match` and `Odd` models and intentionally excludes same-game parlays (SGPs).

## Design

- `models.py` contains immutable, validated domain models.
- `normalization.py` is pure and testable: timestamps become timezone-aware, odds become American format, and malformed lines are skipped.
- `client.py` is the network boundary for public Elitebet pages or permitted API responses. It uses timeouts and a descriptive user agent; it does not bypass anti-bot controls or access restrictions.
- `cli.py` turns a captured JSON response into normalized JSON. Keeping capture separate makes replayed tests deterministic and respects rate limits.

The source site may render data dynamically or restrict automated access. In that case, use an authorized export or browser-assisted capture, save the response locally, and pass it to the normalizer. Do not rotate proxies or evade platform controls.

## Run

```bash
python -m pip install -e '.[dev]'
pytest
python -m elitebet_ingestion.cli data/sample_nfl_matches.json --league NFL -o matches.normalized.json
ruff check .
```

The NFL sample contains five upcoming matches and 11 distinct market types, including moneyline, spread, totals, team totals, passing yards, passing touchdowns, rushing yards, receiving yards, receptions, anytime touchdowns, and first-half totals. The normalizer remains league-agnostic through its `league` argument, while NFL is the default. A production collector should add scheduled polling, response caching, backoff, freshness checks, and source-specific selectors only after the platform's public terms and endpoints are confirmed.

## Output

Each match includes an ISO-8601 `start_time` and an `odds` list. IDs are supplied by the source when available, otherwise generated deterministically from match and selection fields. Invalid odds and incomplete selections are omitted with warnings; an invalid match is skipped by the CLI.
