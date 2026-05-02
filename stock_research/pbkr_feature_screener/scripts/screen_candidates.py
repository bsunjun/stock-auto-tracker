"""
screen_candidates.py — PBKR Quant Feature Screener v1

Apply hard excludes and soft filters from feature_screen_v1.yaml to a
feature table and emit a screened_candidate_pack_v1.

This module is the single enforcement point for the OS v3.2
candidate-compression layer:

  * It NEVER emits direct_trade_signal=true.
  * It NEVER emits a truthy trade_signal.
  * It NEVER labels a row as "BUY" / "SELL" / "강력매수".
  * It NEVER promotes outputs to latest / SuperPack / rolling --apply.
  * PB_READY / PB_TRIGGER (if present in upstream features) are passed
    through as audit metadata only — never as a trade instruction.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "screened_candidate_pack_v1"

DEFAULT_PASSING_THRESHOLD = 3

# Filters expressed in plain Python so this module has zero external
# deps. Each entry: (id, predicate, weight, human-readable expr).
DEFAULT_FILTERS: List[Tuple[str, Any, float, str]] = [
    (
        "ibdrs_approx_top",
        lambda r: _gte(r.get("ibdrs_approx"), 80),
        1.0,
        "ibdrs_approx >= 80",
    ),
    (
        "rs_60d_top",
        lambda r: _gte(r.get("rs_60d_percentile"), 80),
        1.0,
        "rs_60d_percentile >= 80",
    ),
    (
        "estimate_revision_or_surprise",
        lambda r: _gt(r.get("op_revision_pct"), 0)
        or _gte(r.get("latest_op_surprise_pct"), 15),
        1.0,
        "op_revision_pct > 0 OR latest_op_surprise_pct >= 15",
    ),
    (
        "institution_flow_or_consecutive",
        lambda r: _gte(r.get("institution_flow_score"), 70)
        or _gte(r.get("financial_investment_consecutive_days"), 3),
        1.0,
        "institution_flow_score >= 70 OR financial_investment_consecutive_days >= 3",
    ),
    (
        "stop_distance_tight",
        lambda r: _lte(r.get("stop_distance_pct"), 5),
        1.0,
        "stop_distance_pct <= 5",
    ),
]


# Forbidden patterns the emitted pack must not contain.
FORBIDDEN_KEY_PATTERNS = [
    re.compile(r"^api[_-]?key$", re.IGNORECASE),
    re.compile(r"^token$", re.IGNORECASE),
    re.compile(r"^password$", re.IGNORECASE),
    re.compile(r"^secret$", re.IGNORECASE),
]
FORBIDDEN_DIRECTIVE_PHRASES = (
    "지금 매수",
    "사라",
    "팔라",
    "강력매수",
    "BUY NOW",
    "STRONG BUY",
)


def _gte(v: Optional[float], thr: float) -> bool:
    return v is not None and v >= thr


def _gt(v: Optional[float], thr: float) -> bool:
    return v is not None and v > thr


def _lte(v: Optional[float], thr: float) -> bool:
    return v is not None and v <= thr


def _audit_no_forbidden(obj: Any) -> List[str]:
    issues: List[str] = []

    def walk(x: Any, path: str = "$") -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "direct_trade_signal" and v is True:
                    issues.append(f"{path}.{k}=true")
                if k == "trade_signal" and bool(v):
                    issues.append(f"{path}.{k} truthy")
                for pat in FORBIDDEN_KEY_PATTERNS:
                    if pat.match(str(k)):
                        issues.append(f"{path}.{k} matches forbidden key pattern")
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, str):
            for phrase in FORBIDDEN_DIRECTIVE_PHRASES:
                if phrase in x:
                    issues.append(f"{path}: directive phrase {phrase!r}")
        return None

    walk(obj)
    return issues


def screen(
    feature_rows: List[Dict[str, Any]],
    asof_date: str,
    filters: Optional[List[Tuple[str, Any, float, str]]] = None,
    passing_threshold: int = DEFAULT_PASSING_THRESHOLD,
) -> Dict[str, Any]:
    flt = filters or DEFAULT_FILTERS
    universe_size = len(feature_rows)

    survivors: List[Dict[str, Any]] = []
    hard_exclude_count = 0
    for row in feature_rows:
        if bool(row.get("official_risk_hard_exclude")):
            hard_exclude_count += 1
            continue
        survivors.append(row)

    candidates: List[Dict[str, Any]] = []
    for row in survivors:
        passed_ids: List[str] = []
        failed_ids: List[str] = []
        score = 0.0
        for fid, pred, weight, _expr in flt:
            try:
                ok = bool(pred(row))
            except Exception:
                ok = False
            if ok:
                passed_ids.append(fid)
                score += float(weight)
            else:
                failed_ids.append(fid)

        if len(passed_ids) < passing_threshold:
            continue

        reasons = [
            f"passed:{fid}" for fid in passed_ids
        ] + [
            f"failed:{fid}" for fid in failed_ids
        ]
        feature_snapshot = {k: row.get(k) for k in row.keys()}
        feature_snapshot.pop("trade_signal", None)
        feature_snapshot["direct_trade_signal"] = False

        candidates.append(
            {
                "ticker": row.get("ticker"),
                "sector": row.get("sector"),
                "pass_count": len(passed_ids),
                "screen_score": score,
                "passed_filters": passed_ids,
                "failed_filters": failed_ids,
                "reasons": reasons,
                "features": feature_snapshot,
                "human_review_required": True,
            }
        )

    candidates.sort(
        key=lambda c: (
            -c["pass_count"],
            -c["screen_score"],
            -(c["features"].get("ibdrs_approx") or 0.0),
        )
    )

    pack = {
        "schema_version": SCHEMA_VERSION,
        "asof_date": asof_date,
        "universe_size": universe_size,
        "hard_exclude_count": hard_exclude_count,
        "passing_threshold": passing_threshold,
        "direct_trade_signal": False,
        "trade_signal": None,
        "filter_ids": [fid for fid, _, _, _ in flt],
        "candidates": candidates,
        "notes": [
            "Research artifact — NOT a trade signal.",
            "PB_READY / PB_TRIGGER are audit metadata, not orders.",
        ],
    }

    issues = _audit_no_forbidden(pack)
    if issues:
        raise RuntimeError(
            "Refusing to emit screened_candidate_pack: forbidden content detected: "
            + "; ".join(issues)
        )
    return pack


def to_json(pack: Dict[str, Any]) -> str:
    return json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(
        "screen_candidates is a library; run examples/run_feature_screener_fixture.py instead."
    )
