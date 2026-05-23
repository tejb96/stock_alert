from app.models import Alert, AlertOperator
from app.services.ratio_fetcher import RatioQuote


def condition_met(alert: Alert, ratio: float) -> bool:
    if alert.operator == AlertOperator.gte:
        return ratio >= alert.threshold
    return ratio <= alert.threshold


def should_fire(alert: Alert, ratio: float) -> bool:
    if not alert.enabled:
        return False
    return alert.armed and condition_met(alert, ratio)


def mark_fired(alert: Alert, quote: RatioQuote) -> None:
    alert.armed = False
    alert.last_fired_at = quote.fetched_at


def rearm_if_cleared(alert: Alert, ratio: float) -> None:
    if not condition_met(alert, ratio):
        alert.armed = True


def disarm_if_already_met(alert: Alert, ratio: float) -> None:
    """Skip the first notification when the ratio is already past the threshold."""
    if condition_met(alert, ratio):
        alert.armed = False


def format_alert_summary(alert: Alert, quote: RatioQuote) -> str:
    op = ">=" if alert.operator == AlertOperator.gte else "<="
    name = alert.name or f"Alert #{alert.id}"
    return f"{name}: ratio {quote.ratio:.2f} {op} {alert.threshold:.2f}"
