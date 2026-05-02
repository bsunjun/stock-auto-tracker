"""
build_flow_features.py — PBKR Quant Feature Screener v1

Investor-flow features: institutional accumulation, financial-investment
streaks, private-fund flow strength.

Research-only; does NOT emit trade signals.
"""

from __future__ import annotations

from typing import List, Optional, Sequence


DOMAIN = "flow"


def institution_flow_score(net_buy_series: Sequence[float]) -> Optional[float]:
    """Map a recent series of net-buy values to a 0..100 score by
    normalizing the sum vs. its absolute extremes. Pure utility — no
    trade signal."""
    if not net_buy_series:
        return None
    s = sum(net_buy_series)
    denom = sum(abs(v) for v in net_buy_series)
    if denom == 0:
        return 50.0
    raw = s / denom
    return max(0.0, min(100.0, (raw + 1.0) * 50.0))


def consecutive_positive_days(net_buy_series: Sequence[float]) -> int:
    n = 0
    for v in reversed(net_buy_series):
        if v > 0:
            n += 1
        else:
            break
    return n


def private_fund_flow_strength(
    private_fund_net: Sequence[float],
    market_net: Sequence[float],
) -> Optional[float]:
    if not private_fund_net or not market_net:
        return None
    pf = sum(private_fund_net)
    mk = sum(abs(x) for x in market_net)
    if mk == 0:
        return None
    return pf / mk


def build_flow_row(
    ticker: str,
    asof_date: str,
    institution_net: Sequence[float],
    financial_investment_net: Sequence[float],
    private_fund_net: Sequence[float],
    market_net: Sequence[float],
) -> dict:
    return {
        "ticker": ticker,
        "asof_date": asof_date,
        "institution_flow_score": institution_flow_score(institution_net),
        "financial_investment_consecutive_days": consecutive_positive_days(
            financial_investment_net
        ),
        "private_fund_flow_strength": private_fund_flow_strength(
            private_fund_net, market_net
        ),
    }


def build_flow_features(rows: List[dict]) -> List[dict]:
    return [dict(r) for r in rows]


if __name__ == "__main__":
    raise SystemExit(
        "build_flow_features is a library; run examples/run_feature_screener_fixture.py instead."
    )
