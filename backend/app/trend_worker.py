import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import engine
from app.schemas import TickerTrendRead
from app.services import apewisdom_client, notifier, trend_repository, trend_service
from app.services.apewisdom_client import ApeWisdomClientError

logger = logging.getLogger(__name__)

_latest_trends: list[TickerTrendRead] | None = None
_backoff_seconds = 0
ASSET_CLASS = "stock"


def get_latest_trends() -> list[TickerTrendRead] | None:
    return _latest_trends


async def _send_alerts(session: AsyncSession, enriched: list[trend_service.EnrichedTrend]) -> None:
    if not settings.discord_webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not configured; skipping trend alerts")
        return

    candidates = trend_service.evaluate_alerts(enriched, settings)
    now = datetime.now(UTC)

    ready: list[trend_service.AlertCandidate] = []
    for candidate in candidates:
        elapsed = await trend_repository.cooldown_elapsed(
            session,
            ticker=candidate.ticker,
            asset_class=candidate.asset_class,
            cooldown_hours=settings.apewisdom_alert_cooldown_hours,
            now=now,
        )
        if elapsed:
            ready.append(candidate)

    to_send = trend_service.select_top_alert_candidates(
        ready,
        max_count=settings.apewisdom_alert_max_per_cycle,
    )
    if not to_send:
        return

    try:
        await notifier.send_discord_content(
            trend_service.build_batch_alert_message(to_send, polled_at=now)
        )
    except notifier.NotifierError:
        logger.exception("Failed to send trend alerts")
        return

    for candidate in to_send:
        await trend_repository.set_last_alert_at(
            session,
            ticker=candidate.ticker,
            asset_class=candidate.asset_class,
            at=now,
        )
        logger.info(
            "Trend alert sent: %s (reason=%s, score=%.1f)",
            candidate.ticker,
            candidate.reason,
            candidate.trend_score,
        )


async def _maybe_send_daily_summary(
    session: AsyncSession,
    enriched: list[trend_service.EnrichedTrend],
) -> None:
    now = datetime.now(UTC)
    last_date = await trend_repository.get_daily_summary_date(session)

    if not trend_service.should_send_daily_summary(
        now=now,
        last_summary_date=last_date,
        summary_hour_utc=settings.apewisdom_daily_summary_hour_utc,
    ):
        return

    if not settings.discord_webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not configured; skipping daily trend summary")
        return

    content = trend_service.build_daily_summary(enriched, summary_date=now.date())
    try:
        await notifier.send_discord_content(content)
    except notifier.NotifierError:
        logger.exception("Failed to send daily trend summary")
        return

    await trend_repository.set_daily_summary_date(session, now.date())
    logger.info("Daily trend summary sent for %s", now.date().isoformat())


async def trend_once() -> None:
    global _latest_trends, _backoff_seconds

    try:
        raw = await apewisdom_client.fetch_stocks(top_n=settings.apewisdom_top_n)
    except ApeWisdomClientError:
        logger.exception("Failed to fetch ApeWisdom stock trends")
        _backoff_seconds = min(
            max(_backoff_seconds * 2, settings.apewisdom_fetch_interval_seconds),
            300,
        )
        return

    _backoff_seconds = 0
    enriched = trend_service.enrich_snapshots(raw)
    snapshot_time = datetime.now(UTC)
    cutoff = snapshot_time - timedelta(days=settings.apewisdom_history_days)

    try:
        async with AsyncSession(engine) as session:
            await trend_repository.insert_batch(
                session,
                enriched,
                snapshot_time=snapshot_time,
                asset_class=ASSET_CLASS,
            )
            deleted = await trend_repository.purge_old(session, cutoff=cutoff)
            if deleted:
                logger.info("Purged %s old trend snapshot rows", deleted)

            await _send_alerts(session, enriched)
            await _maybe_send_daily_summary(session, enriched)
    except Exception:
        logger.exception("Failed to persist or process trend snapshots")
        return

    _latest_trends = trend_service.to_api_response(
        enriched,
        min_mentions=settings.apewisdom_min_mentions,
    )
    logger.info("Trend snapshot stored: %s symbols at %s", len(enriched), snapshot_time.isoformat())


async def trend_loop() -> None:
    logger.info(
        "Trend loop started (interval=%sm, discord=%s)",
        settings.apewisdom_fetch_interval_minutes,
        "configured" if settings.discord_webhook_url else "missing",
    )

    while True:
        await trend_once()
        sleep_for = _backoff_seconds or settings.apewisdom_fetch_interval_seconds
        await asyncio.sleep(sleep_for)
