from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.schemas import RatioRead
from app.services.ratio_fetcher import RatioFetchError, fetch_ratio
from app.worker import get_latest_quote

router = APIRouter(tags=["status"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ratio", response_model=RatioRead)
async def get_ratio() -> RatioRead:
    cached = get_latest_quote()
    if cached is not None:
        return RatioRead(
            ratio=cached.ratio,
            gold_price=cached.gold_price,
            silver_price=cached.silver_price,
            source=cached.source,
            fetched_at=cached.fetched_at,
            market_state=cached.market_state,
        )

    try:
        quote = await fetch_ratio()
    except RatioFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return RatioRead(
        ratio=quote.ratio,
        gold_price=quote.gold_price,
        silver_price=quote.silver_price,
        source=quote.source,
        fetched_at=quote.fetched_at,
        market_state=quote.market_state,
    )
