from dataclasses import dataclass
from typing import Literal

AssetClass = Literal["stock", "crypto"]


@dataclass(frozen=True)
class TickerSnapshot:
    ticker: str
    rank: int
    mentions: int
    upvotes: int
    mentions_24h_ago: int | None
    asset_class: AssetClass = "stock"
