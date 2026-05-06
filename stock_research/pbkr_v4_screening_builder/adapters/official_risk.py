"""KRX / KIND / DART official risk-flag taxonomy mapper.

Maps Korean designation strings to the four risk buckets used by the
state classifier:

    HARD_EXCLUDE              — administrative / delisting / halt /
                                non-standard audit / unfaithful
                                disclosure / capital impairment.
    EXTREME_RISK_FLAG_WATCH   — 투자위험 / 투자위험 지정예고.
    REGULAR_PB_EXCLUDE        — 투자주의 / 투자경고 / 단기과열 /
                                매매거래정지 예고 (cooling-off).
    RISK_FLAG_PULLBACK_WATCH  — same designations as REGULAR_PB_EXCLUDE
                                but the tape is constructive enough to
                                *watch only*. The actual decision to
                                emit this label happens later in the
                                state classifier; this mapper only
                                produces REGULAR_PB_EXCLUDE for the
                                designation-derived bucket.

Market-structure events (sidecar / circuit breaker / opening or
closing auction window) feed the
``NO_ENTRY_MARKET_STRUCTURE_ACTIVE`` state and live on the pack's
``market_structure`` field, not on per-row buckets.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..constants import SCHEMA_VERSION, SIGNAL_SAFETY_BLOCK


HARD_EXCLUDE_KEYS = (
    "관리종목",
    "상장폐지",
    "상폐",
    "거래정지",
    "trading_halt",
    "delisting",
    "감사의견 비적정",
    "감사의견 거절",
    "감사의견 한정",
    "non_standard_audit",
    "qualified_audit",
    "감사의견 부적정",
    "adverse_audit",
    "불성실공시",
    "unfaithful_disclosure",
    "자본잠식",
    "capital_impairment",
    "상장적격성 실질심사",
    "listing_review",
)

EXTREME_RISK_KEYS = (
    "투자위험종목",
    "투자위험",
    "투자위험 지정예고",
    "investment_risk",
    "investment_risk_notice",
)

REGULAR_PB_KEYS = (
    "투자주의",
    "investment_attention",
    "투자경고",
    "investment_warning",
    "단기과열",
    "short_term_overheating",
)


def _classify_designation(raw: str) -> set[str]:
    """Return all buckets that match the given designation string."""
    s = (raw or "").strip().lower()
    if not s:
        return set()
    buckets: set[str] = set()
    if any(k.lower() in s or s in k.lower() for k in HARD_EXCLUDE_KEYS):
        buckets.add("HARD_EXCLUDE")
    if any(k.lower() in s or s in k.lower() for k in EXTREME_RISK_KEYS):
        buckets.add("EXTREME_RISK_FLAG_WATCH")
    if any(k.lower() in s or s in k.lower() for k in REGULAR_PB_KEYS):
        buckets.add("REGULAR_PB_EXCLUDE")
    return buckets


def _row_buckets(designations: list[str]) -> list[str]:
    out: set[str] = set()
    for d in designations:
        out |= _classify_designation(d)
    if "HARD_EXCLUDE" in out:
        # HARD_EXCLUDE absorbs the rest at output time, but we keep
        # the per-row reasoning honest by leaving all matched buckets.
        return sorted(out)
    return sorted(out)


def load_official_risk_flags(path: str | Path, asof: str) -> dict[str, Any]:
    """Load and normalize a KRX / KIND / DART risk-flags JSON file."""
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"official_risk payload must be an object: {path}")

    market_structure = payload.get("market_structure") or {}
    market_structure = {
        "circuit_breaker_active": bool(market_structure.get("circuit_breaker_active", False)),
        "sidecar_active": bool(market_structure.get("sidecar_active", False)),
        "auction_window": str(market_structure.get("auction_window") or "none"),
    }
    if market_structure["auction_window"] not in ("none", "opening", "closing"):
        market_structure["auction_window"] = "none"

    rows: list[dict[str, Any]] = []
    for r in payload.get("rows", []):
        if not isinstance(r, dict) or not r.get("ticker"):
            continue
        designations = [str(d).strip() for d in (r.get("raw_designations") or []) if str(d).strip()]
        rows.append({
            "ticker": str(r["ticker"]).strip(),
            "raw_designations": designations,
            "buckets": _row_buckets(designations),
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "market_structure": market_structure,
        "rows": rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
