from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    TickerTrendAlertCooldown,
    TickerTrendSnapshot,
    TrendSchedulerMeta,
)
from app.services.trend_service import EnrichedTrend
from app.services.types import AssetClass

SCHEDULER_META_ID = 1


async def insert_batch(
    session: AsyncSession,
    rows: list[EnrichedTrend],
    *,
    snapshot_time: datetime,
    asset_class: AssetClass = "stock",
) -> None:
    for row in rows:
        session.add(
            TickerTrendSnapshot(
                ticker=row.ticker,
                rank=row.rank,
                mentions=row.mentions,
                upvotes=row.upvotes,
                change_24h=row.change_24h,
                asset_class=asset_class,
                snapshot_time=snapshot_time,
            )
        )
    await session.commit()


async def purge_old(session: AsyncSession, *, cutoff: datetime) -> int:
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=UTC)
    result = await session.execute(
        delete(TickerTrendSnapshot).where(TickerTrendSnapshot.snapshot_time < cutoff)
    )
    await session.commit()
    return result.rowcount or 0


async def get_latest_batch(
    session: AsyncSession,
    asset_class: AssetClass = "stock",
) -> list[TickerTrendSnapshot] | None:
    latest_time = await session.scalar(
        select(func.max(TickerTrendSnapshot.snapshot_time)).where(
            TickerTrendSnapshot.asset_class == asset_class
        )
    )
    if latest_time is None:
        return None

    result = await session.scalars(
        select(TickerTrendSnapshot)
        .where(
            TickerTrendSnapshot.asset_class == asset_class,
            TickerTrendSnapshot.snapshot_time == latest_time,
        )
        .order_by(TickerTrendSnapshot.rank)
    )
    rows = result.all()
    return rows if rows else None


def snapshots_to_enriched(rows: list[TickerTrendSnapshot]) -> list[EnrichedTrend]:
    from app.services.trend_service import compute_trend_score

    return [
        EnrichedTrend(
            ticker=row.ticker,
            rank=row.rank,
            mentions=row.mentions,
            upvotes=row.upvotes,
            change_24h=row.change_24h,
            trend_score=compute_trend_score(row.mentions, row.change_24h),
            asset_class=row.asset_class,  # type: ignore[arg-type]
        )
        for row in rows
    ]


async def get_last_alert_at(
    session: AsyncSession,
    *,
    ticker: str,
    asset_class: AssetClass = "stock",
) -> datetime | None:
    result = await session.get(TickerTrendAlertCooldown, (asset_class, ticker))
    return result.last_alert_at if result else None


async def cooldown_elapsed(
    session: AsyncSession,
    *,
    ticker: str,
    asset_class: AssetClass,
    cooldown_hours: int,
    now: datetime | None = None,
) -> bool:
    last_alert_at = await get_last_alert_at(session, ticker=ticker, asset_class=asset_class)
    if last_alert_at is None:
        return True

    current = now or datetime.now(UTC)
    if last_alert_at.tzinfo is None:
        last_alert_at = last_alert_at.replace(tzinfo=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)

    return current - last_alert_at >= timedelta(hours=cooldown_hours)


async def set_last_alert_at(
    session: AsyncSession,
    *,
    ticker: str,
    asset_class: AssetClass,
    at: datetime,
) -> None:
    existing = await session.get(TickerTrendAlertCooldown, (asset_class, ticker))
    if existing:
        existing.last_alert_at = at
        session.add(existing)
    else:
        session.add(
            TickerTrendAlertCooldown(
                asset_class=asset_class,
                ticker=ticker,
                last_alert_at=at,
            )
        )
    await session.commit()


async def get_daily_summary_date(session: AsyncSession) -> date | None:
    meta = await session.get(TrendSchedulerMeta, SCHEDULER_META_ID)
    if meta is None:
        return None
    return meta.last_daily_summary_date


async def set_daily_summary_date(session: AsyncSession, summary_date: date) -> None:
    meta = await session.get(TrendSchedulerMeta, SCHEDULER_META_ID)
    if meta is None:
        session.add(
            TrendSchedulerMeta(id=SCHEDULER_META_ID, last_daily_summary_date=summary_date)
        )
    else:
        meta.last_daily_summary_date = summary_date
        session.add(meta)
    await session.commit()
