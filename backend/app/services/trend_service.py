from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.config import Settings
from app.schemas import TickerTrendRead
from app.services.types import AssetClass, TickerSnapshot


@dataclass(frozen=True)
class EnrichedTrend:
    ticker: str
    rank: int
    mentions: int
    upvotes: int
    change_24h: float | None
    trend_score: float
    asset_class: AssetClass = "stock"


@dataclass(frozen=True)
class AlertCandidate:
    ticker: str
    rank: int
    mentions: int
    upvotes: int
    change_24h: float | None
    trend_score: float
    reason: str
    asset_class: AssetClass = "stock"


def compute_change_24h(mentions: int, mentions_24h_ago: int | None) -> float | None:
    if mentions_24h_ago is None or mentions_24h_ago <= 0:
        return None
    return ((mentions - mentions_24h_ago) / mentions_24h_ago) * 100


def compute_trend_score(mentions: int, change_24h: float | None) -> float:
    growth = max(change_24h or 0.0, 0.0)
    return mentions * (1 + growth / 100)


def enrich_snapshots(raw: list[TickerSnapshot]) -> list[EnrichedTrend]:
    enriched: list[EnrichedTrend] = []
    for row in raw:
        change_24h = compute_change_24h(row.mentions, row.mentions_24h_ago)
        enriched.append(
            EnrichedTrend(
                ticker=row.ticker,
                rank=row.rank,
                mentions=row.mentions,
                upvotes=row.upvotes,
                change_24h=change_24h,
                trend_score=compute_trend_score(row.mentions, change_24h),
                asset_class=row.asset_class,
            )
        )
    return enriched


def apply_min_mentions(rows: list[EnrichedTrend], min_mentions: int) -> list[EnrichedTrend]:
    return [row for row in rows if row.mentions >= min_mentions]


def _meets_mentions_change_threshold(row: EnrichedTrend, settings: Settings) -> bool:
    if row.change_24h is None:
        return False
    return (
        row.mentions >= settings.apewisdom_alert_mentions
        and row.change_24h >= settings.apewisdom_alert_change_24h
    )


def evaluate_alerts(rows: list[EnrichedTrend], settings: Settings) -> list[AlertCandidate]:
    eligible = apply_min_mentions(rows, settings.apewisdom_min_mentions)
    candidates: list[AlertCandidate] = []

    for row in eligible:
        reasons: list[str] = []
        if _meets_mentions_change_threshold(row, settings):
            reasons.append("mentions_change")
        if row.trend_score >= settings.apewisdom_alert_score_threshold:
            reasons.append("trend_score")
        if not reasons:
            continue

        candidates.append(
            AlertCandidate(
                ticker=row.ticker,
                rank=row.rank,
                mentions=row.mentions,
                upvotes=row.upvotes,
                change_24h=row.change_24h,
                trend_score=row.trend_score,
                reason="+".join(reasons),
                asset_class=row.asset_class,
            )
        )

    return candidates


def _format_change(change_24h: float | None) -> str:
    if change_24h is None:
        return "n/a"
    sign = "+" if change_24h >= 0 else ""
    return f"{sign}{change_24h:.1f}%"


def _format_alert_block(index: int, candidate: AlertCandidate) -> str:
    return (
        f"**{index}. {candidate.ticker}** · Rank #{candidate.rank}\n"
        f"Mentions: **{candidate.mentions}** · 24h change: **{_format_change(candidate.change_24h)}**\n"
        f"Upvotes: **{candidate.upvotes}** · Trend score: **{candidate.trend_score:.1f}**\n"
        f"Trigger: {candidate.reason}"
    )


def select_top_alert_candidates(
    candidates: list[AlertCandidate],
    *,
    max_count: int,
) -> list[AlertCandidate]:
    if max_count <= 0:
        return []
    ranked = sorted(candidates, key=lambda c: c.trend_score, reverse=True)
    return ranked[:max_count]


def build_batch_alert_message(
    candidates: list[AlertCandidate],
    *,
    polled_at: datetime | None = None,
) -> str:
    when = polled_at or datetime.now(UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    else:
        when = when.astimezone(UTC)

    count = len(candidates)
    header = f"**Trend alerts** (top {count} · apewisdom)\n{when.strftime('%Y-%m-%d %H:%M')} UTC"
    blocks = [_format_alert_block(i, c) for i, c in enumerate(candidates, start=1)]
    return header + "\n\n" + "\n\n".join(blocks)


def _top_by(rows: list[EnrichedTrend], key: str, n: int = 5) -> list[EnrichedTrend]:
    if key == "mentions":
        return sorted(rows, key=lambda r: r.mentions, reverse=True)[:n]
    if key == "change_24h":
        return sorted(
            rows,
            key=lambda r: r.change_24h if r.change_24h is not None else float("-inf"),
            reverse=True,
        )[:n]
    if key == "trend_score":
        return sorted(rows, key=lambda r: r.trend_score, reverse=True)[:n]
    raise ValueError(f"Unknown sort key: {key}")


def _format_summary_line(row: EnrichedTrend) -> str:
    return (
        f"{row.ticker} (#{row.rank}, {row.mentions} mentions, "
        f"{_format_change(row.change_24h)}, score {row.trend_score:.1f})"
    )


def build_daily_summary(rows: list[EnrichedTrend], *, summary_date: date | None = None) -> str:
    eligible = apply_min_mentions(rows, 1)
    day = summary_date or datetime.now(UTC).date()
    top_mentions = _top_by(eligible, "mentions")
    top_change = _top_by(eligible, "change_24h")
    top_score = _top_by(eligible, "trend_score")

    lines = [
        f"**Daily trend summary** ({day.isoformat()} UTC)",
        "**Top mentions:** " + ", ".join(_format_summary_line(r) for r in top_mentions),
        "**Top 24h change:** " + ", ".join(_format_summary_line(r) for r in top_change),
        "**Top trend score:** " + ", ".join(_format_summary_line(r) for r in top_score),
    ]
    return "\n".join(lines)


def to_api_response(rows: list[EnrichedTrend], *, min_mentions: int) -> list[TickerTrendRead]:
    filtered = apply_min_mentions(rows, min_mentions)
    return [
        TickerTrendRead(
            ticker=row.ticker,
            rank=row.rank,
            mentions=row.mentions,
            change_24h=row.change_24h,
            upvotes=row.upvotes,
            trend_score=row.trend_score,
        )
        for row in sorted(filtered, key=lambda r: r.rank)
    ]


def should_send_daily_summary(
    *,
    now: datetime,
    last_summary_date: date | None,
    summary_hour_utc: int,
) -> bool:
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    else:
        now = now.astimezone(UTC)

    if now.hour != summary_hour_utc:
        return False

    today = now.date()
    return last_summary_date != today
