from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import TickerTrendRead
from app import trend_worker


def test_ticker_trends_disabled(monkeypatch):
    monkeypatch.setattr(settings, "apewisdom_enabled", False)
    client = TestClient(app)
    response = client.get("/ticker-trends")
    assert response.status_code == 200
    assert response.json() == []


def test_ticker_trends_from_cache(monkeypatch):
    monkeypatch.setattr(settings, "apewisdom_enabled", True)
    trend_worker._latest_trends = [
        TickerTrendRead(
            ticker="NVDA",
            rank=1,
            mentions=100,
            change_24h=50.0,
            upvotes=200,
            trend_score=150.0,
        )
    ]
    client = TestClient(app)
    response = client.get("/ticker-trends")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "NVDA"
    trend_worker._latest_trends = None
