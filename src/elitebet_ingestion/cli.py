"""Command-line entry point."""

import argparse
import json
import logging
from pathlib import Path

from .normalization import normalize_match


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Elitebet match records into JSON.")
    parser.add_argument("input", type=Path, help="JSON file containing a list or matches envelope")
    parser.add_argument("-o", "--output", type=Path, default=Path("matches.normalized.json"))
    parser.add_argument("--league", default="NFL")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    records = (
        payload
        if isinstance(payload, list)
        else payload.get("matches", payload.get("data", []))
    )
    matches = []
    for record in records:
        try:
            matches.append(normalize_match(record, league=args.league).to_dict())
        except (TypeError, ValueError) as exc:
            logging.warning("Skipping malformed match: %s", exc)
    args.output.write_text(json.dumps(matches, indent=2), encoding="utf-8")
    logging.info("Wrote %d matches to %s", len(matches), args.output)


if __name__ == "__main__":
    main()
