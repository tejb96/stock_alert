import asyncio
import logging
from typing import Any

import httpx

from app.services.types import TickerSnapshot

logger = logging.getLogger(__name__)

APEWISDOM_STOCKS_URL = "https://apewisdom.io/api/v1.0/filter/all-stocks"
MAX_RETRIES = 3
RETRY_DELAYS = (1.0, 2.0, 4.0)


class ApeWisdomClientError(Exception):
    pass


def _coerce_int(value: Any, field: str, ticker: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid %s for ticker %s: %r", field, ticker, value)
        return None


def _parse_row(raw: dict[str, Any]) -> TickerSnapshot | None:
    ticker_raw = raw.get("ticker")
    if not ticker_raw or not isinstance(ticker_raw, str):
        logger.warning("Skipping row with missing ticker: %r", raw)
        return None

    ticker = ticker_raw.strip().upper()
    rank = _coerce_int(raw.get("rank"), "rank", ticker)
    mentions = _coerce_int(raw.get("mentions"), "mentions", ticker)
    upvotes = _coerce_int(raw.get("upvotes"), "upvotes", ticker)
    if rank is None or mentions is None or upvotes is None:
        return None

    mentions_24h_ago = _coerce_int(raw.get("mentions_24h_ago"), "mentions_24h_ago", ticker)

    return TickerSnapshot(
        ticker=ticker,
        rank=rank,
        mentions=mentions,
        upvotes=upvotes,
        mentions_24h_ago=mentions_24h_ago,
        asset_class="stock",
    )


def _parse_payload(payload: dict[str, Any], *, top_n: int) -> list[TickerSnapshot]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise ApeWisdomClientError("ApeWisdom response missing results list")

    snapshots: list[TickerSnapshot] = []
    for raw in results[:top_n]:
        if not isinstance(raw, dict):
            logger.warning("Skipping non-object result row: %r", raw)
            continue
        row = _parse_row(raw)
        if row is not None:
            snapshots.append(row)

    if not snapshots:
        raise ApeWisdomClientError("No valid ticker rows in ApeWisdom response")

    return snapshots


async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    response = await client.get(url)
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                await asyncio.sleep(float(retry_after))
            except ValueError:
                pass
        raise ApeWisdomClientError(f"ApeWisdom rate limited: {response.status_code}")
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ApeWisdomClientError("ApeWisdom response is not a JSON object")
    return data


async def fetch_stocks(*, top_n: int) -> list[TickerSnapshot]:
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=20.0) as client:
        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                payload = await _fetch_json(client, APEWISDOM_STOCKS_URL)
                return _parse_payload(payload, top_n=top_n)
            except ApeWisdomClientError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "ApeWisdom fetch attempt %s failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt < len(RETRY_DELAYS) - 1:
                    await asyncio.sleep(delay)

    raise ApeWisdomClientError(f"ApeWisdom fetch failed after retries: {last_error}") from last_error
