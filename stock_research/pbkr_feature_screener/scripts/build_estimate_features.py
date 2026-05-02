"""
build_estimate_features.py — PBKR Quant Feature Screener v1

Estimate-domain features (sales / OP / EPS, revisions, surprise, guidance).
Research-only; does NOT emit trade signals.
"""

from __future__ import annotations

from typing import List, Optional


DOMAIN = "estimate"


def revision_pct(latest: Optional[float], prior: Optional[float]) -> Optional[float]:
    if latest is None or prior is None or prior == 0:
        return None
    return (latest / prior - 1.0) * 100.0


def surprise_pct(actual: Optional[float], consensus: Optional[float]) -> Optional[float]:
    if actual is None or consensus is None or consensus == 0:
        return None
    return (actual / consensus - 1.0) * 100.0


def guidance_delta(
    new_guidance: Optional[float], prev_guidance: Optional[float]
) -> Optional[float]:
    if new_guidance is None or prev_guidance is None:
        return None
    return new_guidance - prev_guidance


def build_estimate_row(
    ticker: str,
    asof_date: str,
    latest_sales: Optional[float],
    latest_op: Optional[float],
    latest_eps: Optional[float],
    op_consensus_now: Optional[float] = None,
    op_consensus_prior: Optional[float] = None,
    eps_consensus_now: Optional[float] = None,
    eps_consensus_prior: Optional[float] = None,
    op_actual: Optional[float] = None,
    sales_guidance_now: Optional[float] = None,
    sales_guidance_prior: Optional[float] = None,
    op_guidance_now: Optional[float] = None,
    op_guidance_prior: Optional[float] = None,
) -> dict:
    return {
        "ticker": ticker,
        "asof_date": asof_date,
        "latest_sales": latest_sales,
        "latest_op": latest_op,
        "latest_eps": latest_eps,
        "op_revision_pct": revision_pct(op_consensus_now, op_consensus_prior),
        "eps_revision_pct": revision_pct(eps_consensus_now, eps_consensus_prior),
        "latest_op_surprise_pct": surprise_pct(op_actual, op_consensus_now),
        "sales_guidance_delta": guidance_delta(sales_guidance_now, sales_guidance_prior),
        "op_guidance_delta": guidance_delta(op_guidance_now, op_guidance_prior),
    }


def build_estimate_features(rows: List[dict]) -> List[dict]:
    return [dict(r) for r in rows]


if __name__ == "__main__":
    raise SystemExit(
        "build_estimate_features is a library; run examples/run_feature_screener_fixture.py instead."
    )
