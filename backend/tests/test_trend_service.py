from datetime import UTC, datetime

from app.config import Settings
from app.services import trend_service
from app.services.types import TickerSnapshot


def test_compute_change_24h_positive():
    assert trend_service.compute_change_24h(150, 100) == 50.0


def test_compute_change_24h_zero_baseline():
    assert trend_service.compute_change_24h(100, 0) is None
    assert trend_service.compute_change_24h(100, None) is None


def test_compute_trend_score_examples():
    assert trend_service.compute_trend_score(100, 50.0) == 150.0
    assert trend_service.compute_trend_score(50, 200.0) == 150.0
    assert trend_service.compute_trend_score(100, None) == 100.0
    assert trend_service.compute_trend_score(100, -10.0) == 100.0


def test_apply_min_mentions():
    rows = trend_service.enrich_snapshots(
        [
            TickerSnapshot("AAA", 1, 25, 10, 20),
            TickerSnapshot("BBB", 2, 5, 10, 4),
        ]
    )
    filtered = trend_service.apply_min_mentions(rows, 20)
    assert [r.ticker for r in filtered] == ["AAA"]


def test_evaluate_alerts_mentions_change():
    settings = Settings(
        apewisdom_min_mentions=20,
        apewisdom_alert_mentions=50,
        apewisdom_alert_change_24h=100,
        apewisdom_alert_score_threshold=999,
    )
    rows = trend_service.enrich_snapshots(
        [TickerSnapshot("HOT", 1, 60, 100, 20)]
    )
    candidates = trend_service.evaluate_alerts(rows, settings)
    assert len(candidates) == 1
    assert candidates[0].ticker == "HOT"
    assert "mentions_change" in candidates[0].reason


def test_evaluate_alerts_trend_score():
    settings = Settings(
        apewisdom_min_mentions=20,
        apewisdom_alert_mentions=999,
        apewisdom_alert_change_24h=999,
        apewisdom_alert_score_threshold=150,
    )
    rows = trend_service.enrich_snapshots(
        [TickerSnapshot("HOT", 1, 100, 10, 50)]
    )
    candidates = trend_service.evaluate_alerts(rows, settings)
    assert len(candidates) == 1
    assert "trend_score" in candidates[0].reason


def test_select_top_alert_candidates_by_trend_score():
    low = trend_service.AlertCandidate(
        ticker="LOW",
        rank=10,
        mentions=50,
        upvotes=10,
        change_24h=100.0,
        trend_score=150.0,
        reason="trend_score",
    )
    high = trend_service.AlertCandidate(
        ticker="HIGH",
        rank=1,
        mentions=200,
        upvotes=100,
        change_24h=200.0,
        trend_score=600.0,
        reason="trend_score",
    )
    selected = trend_service.select_top_alert_candidates([low, high], max_count=1)
    assert [c.ticker for c in selected] == ["HIGH"]


def test_build_batch_alert_message():
    polled_at = datetime(2026, 5, 26, 11, 40, tzinfo=UTC)
    candidate = trend_service.AlertCandidate(
        ticker="SPY",
        rank=2,
        mentions=337,
        upvotes=7637,
        change_24h=227.2,
        trend_score=1102.6,
        reason="mentions_change+trend_score",
    )
    message = trend_service.build_batch_alert_message([candidate], polled_at=polled_at)
    assert "**Trend alerts** (top 1 · apewisdom)" in message
    assert "2026-05-26 11:40 UTC" in message
    assert "**1. SPY** · Rank #2" in message
    assert "Trigger: mentions_change+trend_score" in message


def test_should_send_daily_summary():
    now = datetime(2026, 5, 25, 21, 30, tzinfo=UTC)
    assert trend_service.should_send_daily_summary(
        now=now,
        last_summary_date=None,
        summary_hour_utc=21,
    )
    assert not trend_service.should_send_daily_summary(
        now=now,
        last_summary_date=now.date(),
        summary_hour_utc=21,
    )
    assert not trend_service.should_send_daily_summary(
        now=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
        last_summary_date=None,
        summary_hour_utc=21,
    )
