from fastapi import APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import engine
from app.schemas import TickerTrendRead
from app.services import trend_repository, trend_service
from app.trend_worker import get_latest_trends

router = APIRouter(tags=["trends"])


@router.get("/ticker-trends", response_model=list[TickerTrendRead])
async def list_ticker_trends() -> list[TickerTrendRead]:
    if not settings.apewisdom_enabled:
        return []

    cached = get_latest_trends()
    if cached is not None:
        return cached

    async with AsyncSession(engine) as session:
        rows = await trend_repository.get_latest_batch(session, asset_class="stock")
        if rows is None:
            return []
        enriched = trend_repository.snapshots_to_enriched(rows)
        return trend_service.to_api_response(
            enriched,
            min_mentions=settings.apewisdom_min_mentions,
        )
