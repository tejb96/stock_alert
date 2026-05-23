from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.config import settings

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
GOLD_SYMBOL = "GC=F"
SILVER_SYMBOL = "SI=F"


@dataclass(frozen=True)
class RatioQuote:
    gold_price: float
    silver_price: float
    ratio: float
    source: str
    fetched_at: datetime
    market_state: str


class RatioFetchError(Exception):
    pass


def _extract_price(payload: dict) -> tuple[float, str]:
    result = payload.get("chart", {}).get("result")
    if not result:
        raise RatioFetchError("Yahoo chart response missing result")

    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    if price is None:
        price = meta.get("previousClose")
    if price is None:
        raise RatioFetchError("Yahoo chart response missing price")

    market_state = meta.get("marketState", "unknown")
    return float(price), str(market_state)


async def fetch_ratio() -> RatioQuote:
    headers = {"User-Agent": settings.yahoo_user_agent}
    params = {"interval": "1m", "range": "1d"}

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        gold_resp, silver_resp = await client.get(
            YAHOO_CHART_URL.format(symbol=GOLD_SYMBOL),
            params=params,
        ), await client.get(
            YAHOO_CHART_URL.format(symbol=SILVER_SYMBOL),
            params=params,
        )

    gold_resp.raise_for_status()
    silver_resp.raise_for_status()

    gold_price, gold_market = _extract_price(gold_resp.json())
    silver_price, silver_market = _extract_price(silver_resp.json())

    if silver_price <= 0:
        raise RatioFetchError("Invalid silver price")

    market_state = gold_market if gold_market == silver_market else f"{gold_market}/{silver_market}"

    return RatioQuote(
        gold_price=gold_price,
        silver_price=silver_price,
        ratio=gold_price / silver_price,
        source="yahoo_finance",
        fetched_at=datetime.now(UTC),
        market_state=market_state,
    )
