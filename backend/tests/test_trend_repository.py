from datetime import UTC, datetime, timedelta

import pytest

from app.services import trend_repository, trend_service
from app.services.types import TickerSnapshot


@pytest.mark.asyncio
async def test_insert_batch_and_latest(session):
    raw = [TickerSnapshot("AAA", 1, 50, 10, 40)]
    enriched = trend_service.enrich_snapshots(raw)
    snapshot_time = datetime(2026, 5, 25, 12, 0, tzinfo=UTC)

    await trend_repository.insert_batch(
        session, enriched, snapshot_time=snapshot_time, asset_class="stock"
    )

    latest = await trend_repository.get_latest_batch(session, asset_class="stock")
    assert latest is not None
    assert len(latest) == 1
    assert latest[0].ticker == "AAA"
    assert latest[0].change_24h == 25.0


@pytest.mark.asyncio
async def test_purge_old(session):
    old_time = datetime(2026, 1, 1, tzinfo=UTC)
    new_time = datetime(2026, 5, 25, tzinfo=UTC)
    row = trend_service.enrich_snapshots([TickerSnapshot("OLD", 1, 30, 1, 20)])[0]

    await trend_repository.insert_batch(session, [row], snapshot_time=old_time)
    await trend_repository.insert_batch(
        session,
        [trend_service.enrich_snapshots([TickerSnapshot("NEW", 2, 40, 1, 30)])[0]],
        snapshot_time=new_time,
    )

    deleted = await trend_repository.purge_old(
        session, cutoff=new_time - timedelta(days=30)
    )
    assert deleted == 1

    latest = await trend_repository.get_latest_batch(session)
    assert latest is not None
    assert len(latest) == 1
    assert latest[0].ticker == "NEW"


@pytest.mark.asyncio
async def test_cooldown(session):
    now = datetime(2026, 5, 25, 12, 0, tzinfo=UTC)
    assert await trend_repository.cooldown_elapsed(
        session, ticker="AAA", asset_class="stock", cooldown_hours=6, now=now
    )

    await trend_repository.set_last_alert_at(
        session, ticker="AAA", asset_class="stock", at=now
    )
    assert not await trend_repository.cooldown_elapsed(
        session, ticker="AAA", asset_class="stock", cooldown_hours=6, now=now
    )


@pytest.mark.asyncio
async def test_daily_summary_meta(session):
    assert await trend_repository.get_daily_summary_date(session) is None
    await trend_repository.set_daily_summary_date(session, datetime(2026, 5, 25, tzinfo=UTC).date())
    assert await trend_repository.get_daily_summary_date(session) == datetime(
        2026, 5, 25, tzinfo=UTC
    ).date()
