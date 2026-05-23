from datetime import UTC, datetime
from enum import Enum

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
