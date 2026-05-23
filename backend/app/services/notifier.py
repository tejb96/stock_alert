import httpx

from app.config import settings
from app.services.ratio_fetcher import RatioQuote


class NotifierError(Exception):
    pass


async def send_discord_alert(
    *,
    quote: RatioQuote,
    threshold: float,
    operator: str,
    alert_name: str | None,
) -> None:
    if not settings.discord_webhook_url:
        raise NotifierError("DISCORD_WEBHOOK_URL is not configured")

    op_label = ">=" if operator == "gte" else "<="
    title = alert_name or f"Ratio {op_label} {threshold:.2f}"
    content = (
        f"**{title}**\n"
        f"Gold/Silver ratio **{quote.ratio:.2f}** ({op_label} **{threshold:.2f}**)\n"
        f"Gold ${quote.gold_price:,.2f}/oz · Silver ${quote.silver_price:,.2f}/oz\n"
        f"Source: {quote.source} · Market: {quote.market_state}"
    )

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            settings.discord_webhook_url,
            json={"content": content},
        )

    if response.status_code >= 400:
        raise NotifierError(f"Discord webhook failed: {response.status_code} {response.text}")


async def send_discord_test() -> None:
    if not settings.discord_webhook_url:
        raise NotifierError("DISCORD_WEBHOOK_URL is not configured")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            settings.discord_webhook_url,
            json={"content": "stock_alert test — Discord webhook is working."},
        )

    if response.status_code >= 400:
        raise NotifierError(f"Discord webhook failed: {response.status_code} {response.text}")
