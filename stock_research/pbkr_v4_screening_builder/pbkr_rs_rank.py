"""PBKR_RS_RANK — locally computed 0-100 percentile rank.

Composite of 1M / 3M / 6M / 12M trailing returns, percentile-ranked
across the supplied universe and weighted (defaults: 0.20, 0.30, 0.30,
0.20). When a benchmark close series is supplied, returns are also
benchmark-relative; the two scores are averaged.

Edge cases:
  * If a ticker lacks enough history for a horizon, that horizon's
    weight is redistributed across the remaining horizons.
  * If a ticker has no usable horizon, its rank is ``None``.
  * Universe size of 1 produces a degenerate rank (always 50.0).
"""
from __future__ import annotations

from typing import Mapping

from .constants import DEFAULT_RS_WEIGHTS, PBKR_RS_RANK_SOURCE, RS_WINDOW_DAYS


def _trailing_return(closes: list[float], window: int) -> float | None:
    if len(closes) < window + 1:
        return None
    last, prior = closes[-1], closes[-1 - window]
    if prior <= 0:
        return None
    return (last / prior) - 1.0


def _percentile_rank(values: dict[str, float]) -> dict[str, float]:
    """Return per-ticker percentile rank in [0, 100].

    Ties resolved by the average of high and low ranks (so equal
    returns get equal percentile)."""
    if not values:
        return {}
    n = len(values)
    if n == 1:
        return {next(iter(values)): 50.0}

    ordered = sorted(values.items(), key=lambda kv: kv[1])
    out: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        # ranks i..j are tied; assign them the midpoint percentile
        avg_rank = (i + j) / 2
        pct = 100.0 * avg_rank / (n - 1)
        for k in range(i, j + 1):
            out[ordered[k][0]] = pct
        i = j + 1
    return out


def _compute_horizon_ranks(
    universe: Mapping[str, list[float]],
    window: int,
    benchmark: list[float] | None,
) -> dict[str, float]:
    raw_returns: dict[str, float] = {}
    for tkr, closes in universe.items():
        r = _trailing_return(closes, window)
        if r is None:
            continue
        raw_returns[tkr] = r

    pct = _percentile_rank(raw_returns)

    if benchmark and len(benchmark) >= window + 1:
        b_ret = _trailing_return(benchmark, window)
        if b_ret is not None:
            rel: dict[str, float] = {t: r - b_ret for t, r in raw_returns.items()}
            rel_pct = _percentile_rank(rel)
            for tkr in pct:
                if tkr in rel_pct:
                    pct[tkr] = (pct[tkr] + rel_pct[tkr]) / 2.0
    return pct


def compute_pbkr_rs_rank(
    universe: Mapping[str, list[float]],
    benchmark: list[float] | None = None,
    weights: Mapping[str, float] | None = None,
) -> dict[str, float | None]:
    """Compute PBKR_RS_RANK for every ticker in ``universe``.

    Returns a mapping ``{ticker: rank_or_None}``. Tickers in the
    universe but with no usable horizon get ``None``.
    """
    weights = dict(weights or DEFAULT_RS_WEIGHTS)
    horizons = list(RS_WINDOW_DAYS.keys())

    horizon_ranks: dict[str, dict[str, float]] = {}
    for h in horizons:
        horizon_ranks[h] = _compute_horizon_ranks(universe, RS_WINDOW_DAYS[h], benchmark)

    out: dict[str, float | None] = {}
    for tkr in universe:
        present = [h for h in horizons if tkr in horizon_ranks[h]]
        if not present:
            out[tkr] = None
            continue
        present_weight = sum(weights[h] for h in present)
        if present_weight <= 0:
            out[tkr] = None
            continue
        composite = sum(horizon_ranks[h][tkr] * (weights[h] / present_weight) for h in present)
        out[tkr] = round(max(0.0, min(100.0, composite)), 2)
    return out


def summarize_rs_rank(
    rs_ranks: Mapping[str, float | None],
    threshold: float,
    weights: Mapping[str, float] | None,
    benchmark_used: bool,
) -> dict[str, object]:
    weights = dict(weights or DEFAULT_RS_WEIGHTS)
    passed = sum(1 for v in rs_ranks.values() if v is not None and v >= threshold)
    return {
        "universe_size": len(rs_ranks),
        "threshold": threshold,
        "passed_threshold_count": passed,
        "benchmark_relative_used": bool(benchmark_used),
        "source": PBKR_RS_RANK_SOURCE,
        "weights": {k: float(weights[k]) for k in ("m1", "m3", "m6", "m12")},
    }
