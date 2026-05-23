from datetime import datetime

from pydantic import BaseModel, Field

from app.models import AlertOperator


class AlertCreate(BaseModel):
    threshold: float = Field(gt=0)
    operator: AlertOperator = AlertOperator.gte
    name: str | None = None
    enabled: bool = True


class AlertUpdate(BaseModel):
    threshold: float | None = Field(default=None, gt=0)
    operator: AlertOperator | None = None
    name: str | None = None
    enabled: bool | None = None


class AlertRead(BaseModel):
    id: int
    name: str | None
    threshold: float
    operator: AlertOperator
    enabled: bool
    armed: bool
    created_at: datetime
    last_fired_at: datetime | None

    model_config = {"from_attributes": True}


class RatioRead(BaseModel):
    ratio: float
    gold_price: float
    silver_price: float
    source: str
    fetched_at: datetime
    market_state: str
