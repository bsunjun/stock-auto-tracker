"""
backtest_filter_ic.py — PBKR Quant Feature Screener v1

Forward-IC and hit-rate diagnostics for each soft filter.

Inputs:
  * feature panel: List[ {ticker, asof_date, <feature columns>} ]
  * forward returns: dict[(ticker, asof_date)] -> {"fwd_5d": x, "fwd_20d": y, ...}

Outputs: filter_performance_pack_v1 dict.

Diagnostic-only. NEVER emits trade signals.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "filter_performance_pack_v1"


def _spearman_ic(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None

    def rank(seq: List[float]) -> List[float]:
        order = sorted(range(len(seq)), key=lambda i: seq[i])
        ranks = [0.0] * len(seq)
        i = 0
        while i < len(seq):
            j = i
            while j + 1 < len(seq) and seq[order[j + 1]] == seq[order[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    n = len(rx)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((v - mx) ** 2 for v in rx))
    dy = math.sqrt(sum((v - my) ** 2 for v in ry))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def evaluate_filter(
    rows: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool],
    fwd_returns: Dict[Tuple[str, str], Dict[str, float]],
    horizons_days: Iterable[int],
) -> Dict[str, Any]:
    flags: List[float] = []
    fwd_by_h: Dict[int, List[float]] = {h: [] for h in horizons_days}
    for r in rows:
        key = (r.get("ticker"), r.get("asof_date"))
        if key not in fwd_returns:
            continue
        try:
            ok = bool(predicate(r))
        except Exception:
            ok = False
        flags.append(1.0 if ok else 0.0)
        for h in fwd_by_h:
            v = fwd_returns[key].get(f"fwd_{h}d")
            fwd_by_h[h].append(float(v) if v is not None else float("nan"))

    ic: Dict[str, Optional[float]] = {}
    for h, ys in fwd_by_h.items():
        clean_x: List[float] = []
        clean_y: List[float] = []
        for xv, yv in zip(flags, ys):
            if math.isnan(yv):
                continue
            clean_x.append(xv)
            clean_y.append(yv)
        ic[f"ic_{h}d"] = _spearman_ic(clean_x, clean_y)
    return {"n_obs": len(flags), "ic": ic}


def hit_rate_pos_fwd(
    rows: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool],
    fwd_returns: Dict[Tuple[str, str], Dict[str, float]],
    horizon_days: int,
) -> Optional[float]:
    keep: List[float] = []
    for r in rows:
        key = (r.get("ticker"), r.get("asof_date"))
        if key not in fwd_returns:
            continue
        try:
            ok = bool(predicate(r))
        except Exception:
            ok = False
        if not ok:
            continue
        v = fwd_returns[key].get(f"fwd_{horizon_days}d")
        if v is None:
            continue
        keep.append(float(v))
    if not keep:
        return None
    return sum(1.0 for v in keep if v > 0) / len(keep)


def build_pack(
    asof_date: str,
    feature_rows: List[Dict[str, Any]],
    filters: List[Tuple[str, Callable[[Dict[str, Any]], bool], float, str]],
    fwd_returns: Dict[Tuple[str, str], Dict[str, float]],
    horizons_days: Iterable[int] = (5, 20, 60),
    hit_rate_horizon_days: int = 20,
    min_obs_per_filter: int = 30,
) -> Dict[str, Any]:
    out_filters: List[Dict[str, Any]] = []
    for fid, pred, _w, expr in filters:
        ev = evaluate_filter(feature_rows, pred, fwd_returns, horizons_days)
        notes: List[str] = []
        if ev["n_obs"] < min_obs_per_filter:
            notes.append(
                f"low_n_obs (<{min_obs_per_filter}); IC unreliable for diagnostic use only"
            )
        out_filters.append(
            {
                "filter_id": fid,
                "expr": expr,
                "n_obs": ev["n_obs"],
                "ic": ev["ic"],
                "hit_rate_pos_fwd": hit_rate_pos_fwd(
                    feature_rows, pred, fwd_returns, hit_rate_horizon_days
                ),
                "notes": notes,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "asof_date": asof_date,
        "horizons_days": list(horizons_days),
        "hit_rate_horizon_days": hit_rate_horizon_days,
        "direct_trade_signal": False,
        "trade_signal": None,
        "filters": out_filters,
    }


if __name__ == "__main__":
    raise SystemExit(
        "backtest_filter_ic is a library; run examples/run_feature_screener_fixture.py instead."
    )
