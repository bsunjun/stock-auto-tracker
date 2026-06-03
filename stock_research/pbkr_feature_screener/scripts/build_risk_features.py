"""
build_risk_features.py — PBKR Quant Feature Screener v1

Hard risk classification: KRX 관리종목 / 거래정지 / 감사의견 거절 /
상장폐지 후보. A row classified as hard-exclude is removed from the
candidate universe regardless of any other score.

Research-only; does NOT emit trade signals.
"""

from __future__ import annotations

from typing import List, Optional


DOMAIN = "risk"


HARD_EXCLUDE_TAGS = frozenset(
    [
        "managed_stock",
        "trading_halt",
        "audit_opinion_disclaimer",
        "audit_opinion_adverse",
        "delisting_candidate",
    ]
)


def is_official_risk_hard_exclude(tags: Optional[List[str]]) -> bool:
    if not tags:
        return False
    return any(t in HARD_EXCLUDE_TAGS for t in tags)


def build_risk_row(
    ticker: str,
    asof_date: str,
    official_tags: Optional[List[str]],
) -> dict:
    return {
        "ticker": ticker,
        "asof_date": asof_date,
        "official_risk_hard_exclude": is_official_risk_hard_exclude(official_tags),
    }


def build_risk_features(rows: List[dict]) -> List[dict]:
    return [dict(r) for r in rows]


if __name__ == "__main__":
    raise SystemExit(
        "build_risk_features is a library; run examples/run_feature_screener_fixture.py instead."
    )
