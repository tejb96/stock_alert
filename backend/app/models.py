from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class AlertOperator(str, Enum):
    gte = "gte"
    lte = "lte"


class Alert(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    threshold: float
    operator: AlertOperator = AlertOperator.gte
    enabled: bool = True
    # True = waiting for a cross into the satisfied zone; False = already in zone (no repeat alerts)
    armed: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_fired_at: datetime | None = None


class RatioSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    gold_price: float
    silver_price: float
    ratio: float
    source: str = "yahoo_finance"
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TickerTrendSnapshot(SQLModel, table=True):
    __table_args__ = (
        Index("ix_tickertrend_ticker_snapshot_time", "ticker", "snapshot_time"),
        Index("ix_tickertrend_snapshot_time", "snapshot_time"),
        Index("ix_tickertrend_asset_class_snapshot_time", "asset_class", "snapshot_time"),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    rank: int
    mentions: int
    upvotes: int
    change_24h: float | None = None
    asset_class: str = Field(default="stock", index=True)
    snapshot_time: datetime = Field(index=True)


class TickerTrendAlertCooldown(SQLModel, table=True):
    asset_class: str = Field(primary_key=True)
    ticker: str = Field(primary_key=True)
    last_alert_at: datetime


class TrendSchedulerMeta(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    last_daily_summary_date: date | None = None
