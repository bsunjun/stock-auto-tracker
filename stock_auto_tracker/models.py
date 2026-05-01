from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Holding:
    symbol: str
    name: str = ""
    quantity: float = 0.0
    avg_price: Optional[float] = None
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    note: str = ""


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    last_price: float
    currency: str = ""
    provider: str = ""


@dataclass(frozen=True)
class SnapshotRow:
    symbol: str
    name: str
    quantity: float
    avg_price: Optional[float]
    last_price: float
    market_value: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    stop_price: Optional[float]
    stop_distance_pct: Optional[float]
    target_price: Optional[float]
    target_distance_pct: Optional[float]
    note: str
