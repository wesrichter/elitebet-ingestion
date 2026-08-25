"""HTTP client boundary for Elitebet pages."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


class ElitebetClient:
    """Small, polite client. It does not attempt to bypass access controls."""

    def __init__(
        self, base_url: str = "https://www.elitebet.com.au", *, timeout: float = 20.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch(self, path: str) -> str:
        """Fetch a public page and surface useful errors to the caller."""
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        headers = {"User-Agent": "elitebet-ingestion/0.1 (educational assessment)"}
        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Elitebet request failed for {url}: {exc}") from exc
        return response.text

    @staticmethod
    def records_from_json(payload: Any) -> list[Mapping[str, Any]]:
        """Accept common API envelope shapes without assuming a private endpoint."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, Mapping):
            for key in ("matches", "events", "fixtures", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, Mapping)]
        return []
