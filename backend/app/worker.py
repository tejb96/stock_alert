import asyncio
import logging

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import engine
from app.models import Alert, RatioSnapshot
from app.services import alert_engine, notifier
from app.services.ratio_fetcher import RatioFetchError, RatioQuote, fetch_ratio

logger = logging.getLogger(__name__)

_latest_quote: RatioQuote | None = None
_backoff_seconds = 0


def get_latest_quote() -> RatioQuote | None:
    return _latest_quote


async def _save_snapshot(session: AsyncSession, quote: RatioQuote) -> None:
    session.add(
        RatioSnapshot(
            gold_price=quote.gold_price,
            silver_price=quote.silver_price,
            ratio=quote.ratio,
            source=quote.source,
            fetched_at=quote.fetched_at,
        )
    )
    await session.commit()


async def _process_alerts(session: AsyncSession, quote: RatioQuote) -> None:
    result = await session.exec(select(Alert).where(Alert.enabled == True))  # noqa: E712
    alerts = result.all()

    for alert in alerts:
        alert_engine.rearm_if_cleared(alert, quote.ratio)

        if not alert_engine.should_fire(alert, quote.ratio):
            continue

        try:
            await notifier.send_discord_alert(
                quote=quote,
                threshold=alert.threshold,
                operator=alert.operator.value,
                alert_name=alert.name,
            )
        except notifier.NotifierError:
            logger.exception("Failed to send Discord alert for alert id=%s", alert.id)
            continue

        alert_engine.mark_fired(alert, quote)
        logger.info("Alert fired: %s", alert_engine.format_alert_summary(alert, quote))

    await session.commit()


async def poll_once() -> None:
    global _latest_quote, _backoff_seconds

    try:
        quote = await fetch_ratio()
    except (RatioFetchError, Exception):
        logger.exception("Failed to fetch gold/silver ratio")
        _backoff_seconds = min(max(_backoff_seconds * 2, settings.poll_interval_seconds), 300)
        return

    _backoff_seconds = 0
    _latest_quote = quote

    async with AsyncSession(engine) as session:
        await _save_snapshot(session, quote)
        await _process_alerts(session, quote)


async def poll_loop() -> None:
    logger.info(
        "Poll loop started (interval=%ss, discord=%s)",
        settings.poll_interval_seconds,
        "configured" if settings.discord_webhook_url else "missing",
    )

    while True:
        await poll_once()
        sleep_for = _backoff_seconds or settings.poll_interval_seconds
        await asyncio.sleep(sleep_for)
