"""Five-state classifier for the PBKR v4 screening engine.

The screening *layer* exposes only five states:

    WATCH_CANDIDATE
    WATCH_ONLY
    RISK_FLAG_PULLBACK_WATCH
    REGULAR_PB_EXCLUDE
    SCREENING_EXCLUDE

The *risk-flag bucket* taxonomy at the input layer
(``HARD_EXCLUDE``, ``EXTREME_RISK_FLAG_WATCH``,
``REGULAR_PB_EXCLUDE``, ``RISK_FLAG_PULLBACK_WATCH``) is preserved on
the official-risk pack and on each candidate's ``risk.buckets``
field; what the classifier collapses is the *state*.

Priority (top → bottom; first match wins):

    1. SCREENING_EXCLUDE          — risk bucket HARD_EXCLUDE,
                                    market structure active, or
                                    risk bucket EXTREME_RISK_FLAG_WATCH.
    2. RISK_FLAG_PULLBACK_WATCH   — risk bucket REGULAR_PB_EXCLUDE +
                                    constructive tape (rs_pass and
                                    trend_pass and ema_pass).
    3. REGULAR_PB_EXCLUDE         — risk bucket REGULAR_PB_EXCLUDE
                                    without constructive tape.
    4. WATCH_CANDIDATE            — clean + all five filters pass.
    5. WATCH_ONLY                 — otherwise.

`RISK_FLAG_PULLBACK_WATCH` is **not** a `PB_TRIGGER`. It is a
high-risk *watch-only* label that elevates attention without
authorizing entry. Doctrine forbids regular pullback entries on a
`투자주의 / 경고 / 단기과열` designation; the default outcome remains
`REGULAR_PB_EXCLUDE`.

The classifier additionally returns a ``state_reason`` enum so the
operator can see *why* a row was excluded without having to peer at
the risk buckets.
"""
from __future__ import annotations

from typing import Any


def classify_state(
    risk_buckets: list[str],
    market_structure_active: bool,
    filters: dict[str, bool],
) -> tuple[str, str]:
    """Return ``(state, state_reason)``.

    ``state`` is one of the five allowed screening-layer values.
    ``state_reason`` is a free-form, low-cardinality enum useful for
    auditing.
    """
    if "HARD_EXCLUDE" in risk_buckets:
        return "SCREENING_EXCLUDE", "hard_designation"
    if market_structure_active:
        return "SCREENING_EXCLUDE", "market_structure"
    if "EXTREME_RISK_FLAG_WATCH" in risk_buckets:
        return "SCREENING_EXCLUDE", "extreme_risk_flag"

    if "REGULAR_PB_EXCLUDE" in risk_buckets:
        if filters.get("rs_pass") and filters.get("trend_pass") and filters.get("ema_pass"):
            return "RISK_FLAG_PULLBACK_WATCH", "regular_pb_designation_watch"
        return "REGULAR_PB_EXCLUDE", "regular_pb_designation"

    all_pass = all(filters.get(k) for k in (
        "rs_pass", "trading_value_pass", "ema_pass", "trend_pass", "structure_pass",
    ))
    if all_pass:
        return "WATCH_CANDIDATE", "all_filters_pass"
    return "WATCH_ONLY", "partial_filters"


def market_structure_blocks(market_structure: dict[str, Any]) -> bool:
    """Return True when market-structure conditions block new entry.

    Per the current screening contract, opening / closing auction
    windows count as market-structure blockers: the tape is unreliable
    in those windows and the state classifier should short-circuit.
    """
    if market_structure.get("circuit_breaker_active"):
        return True
    if market_structure.get("sidecar_active"):
        return True
    if market_structure.get("auction_window") in ("opening", "closing"):
        return True
    return False
