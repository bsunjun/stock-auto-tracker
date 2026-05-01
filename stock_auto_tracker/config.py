from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from stock_auto_tracker.models import Holding


def load_watchlist(path: str | Path) -> list[Holding]:
    path = Path(path)
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("holdings", [])

    holdings: list[Holding] = []
    for item in items:
        holdings.append(
            Holding(
                symbol=str(item["symbol"]).strip(),
                name=str(item.get("name", "")).strip(),
                quantity=float(item.get("quantity", 0) or 0),
                avg_price=_optional_float(item.get("avg_price")),
                stop_price=_optional_float(item.get("stop_price")),
                target_price=_optional_float(item.get("target_price")),
                note=str(item.get("note", "")).strip(),
            )
        )
    return holdings


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
