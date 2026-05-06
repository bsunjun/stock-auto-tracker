"""Seven-state classifier for the PBKR v4 screening engine.

State priority (top → bottom; first match wins):

    1. HARD_EXCLUDE
    2. NO_ENTRY_MARKET_STRUCTURE_ACTIVE
    3. EXTREME_RISK_FLAG_WATCH
    4. REGULAR_PB_EXCLUDE                (default for 투자주의/경고/단기과열)
    5. RISK_FLAG_PULLBACK_WATCH          (REGULAR_PB_EXCLUDE +
                                          rs_pass and trend_pass)
    6. WATCH_CANDIDATE                   (all filters pass, no risk flags)
    7. WATCH_ONLY                        (otherwise)

`RISK_FLAG_PULLBACK_WATCH` is **not** a `PB_TRIGGER`. It is a
high-risk *watch-only* label that promotes a name to elevated
attention without authorizing entry. The doctrine forbids regular
pullback entries on a `투자주의/경고/단기과열` designation, so the
default outcome remains `REGULAR_PB_EXCLUDE`.
"""
from __future__ import annotations

from typing import Any


def classify_state(
    risk_buckets: list[str],
    market_structure_active: bool,
    filters: dict[str, bool],
) -> str:
    if "HARD_EXCLUDE" in risk_buckets:
        return "HARD_EXCLUDE"
    if market_structure_active:
        return "NO_ENTRY_MARKET_STRUCTURE_ACTIVE"
    if "EXTREME_RISK_FLAG_WATCH" in risk_buckets:
        return "EXTREME_RISK_FLAG_WATCH"

    if "REGULAR_PB_EXCLUDE" in risk_buckets:
        # promote to RISK_FLAG_PULLBACK_WATCH only when the tape is
        # constructive enough to warrant elevated watch — still NOT
        # a PB_TRIGGER and NOT an entry.
        if filters.get("rs_pass") and filters.get("trend_pass") and filters.get("ema_pass"):
            return "RISK_FLAG_PULLBACK_WATCH"
        return "REGULAR_PB_EXCLUDE"

    all_pass = all(filters.get(k) for k in (
        "rs_pass", "trading_value_pass", "ema_pass", "trend_pass", "structure_pass",
    ))
    return "WATCH_CANDIDATE" if all_pass else "WATCH_ONLY"


def market_structure_blocks(market_structure: dict[str, Any]) -> bool:
    """Return True when market-structure conditions block new entry.

    Auction windows are *not* automatic blockers in the broader
    doctrine, but per the user's instruction the screening builder
    treats opening / closing auction windows as
    NO_ENTRY_MARKET_STRUCTURE_ACTIVE: the tape is unreliable and the
    state classifier short-circuits.
    """
    if market_structure.get("circuit_breaker_active"):
        return True
    if market_structure.get("sidecar_active"):
        return True
    if market_structure.get("auction_window") in ("opening", "closing"):
        return True
    return False
