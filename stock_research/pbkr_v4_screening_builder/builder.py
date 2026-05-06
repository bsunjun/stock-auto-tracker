"""End-to-end screening builder.

Loads adapter inputs, computes PBKR_RS_RANK, applies filters,
classifies each row, and emits the four input packs plus a
DAILY_INPUT_PACKET.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .adapters.kiwoom_rest import load_kiwoom_features, load_kiwoom_universe
from .adapters.official_risk import load_official_risk_flags
from .adapters.tradingview_mcp import load_tradingview_scan
from .constants import (
    DAILY_PACKET_SIGNAL_SAFETY,
    DEFAULT_MIN_TRADING_VALUE,
    DEFAULT_RS_THRESHOLD,
    DEFAULT_RS_WEIGHTS,
    PBKR_RS_RANK_SOURCE,
    SCHEMA_VERSION,
    SIGNAL_SAFETY_BLOCK,
)
from .packet_emitter import write_outputs
from .pbkr_rs_rank import compute_pbkr_rs_rank, summarize_rs_rank
from .screening_filters import (
    evaluate_filters,
    label_pullback,
    label_stop_distance,
    label_volume,
)
from .state_classifier import classify_state, market_structure_blocks


KST = timezone(timedelta(hours=9))


def _asof_iso(date_str: str) -> str:
    """Convert ``YYYY-MM-DD`` to a KST 15:30:00 ISO timestamp.

    15:30 is the close of the regular continuous session and is the
    canonical asof for daily artifacts.
    """
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, 15, 30, 0, tzinfo=KST).isoformat()


def _build_screening_candidates(
    tv_pack: dict[str, Any],
    kw_pack: dict[str, Any],
    risk_pack: dict[str, Any],
    rs_ranks: dict[str, float | None],
    rs_threshold: float,
    min_trading_value: float,
    asof: str,
) -> dict[str, Any]:
    tv_by_ticker = {r["ticker"]: r for r in tv_pack["rows"]}
    risk_by_ticker = {r["ticker"]: r for r in risk_pack["rows"]}
    market_structure = risk_pack.get("market_structure", {})
    market_active = market_structure_blocks(market_structure)

    candidates: list[dict[str, Any]] = []
    for feat in kw_pack["rows"]:
        tkr = feat["ticker"]
        tv_row = tv_by_ticker.get(tkr)
        risk_row = risk_by_ticker.get(tkr) or {"buckets": [], "raw_designations": []}

        rs_rank = rs_ranks.get(tkr)

        filters = evaluate_filters(
            feat,
            pbkr_rs_rank=rs_rank,
            rs_threshold=rs_threshold,
            min_trading_value=min_trading_value,
            tv_row=tv_row,
        )

        state, state_reason = classify_state(
            risk_buckets=list(risk_row.get("buckets") or []),
            market_structure_active=market_active,
            filters=filters,
        )

        labels = {
            "volume_state_label": label_volume(feat),
            "pullback_state_label": label_pullback(feat, tv_row),
            "stop_distance_label": label_stop_distance(feat),
        }

        candidates.append({
            "ticker": tkr,
            "name": (tv_row or {}).get("name") or tkr,
            "state": state,
            "state_reason": state_reason,
            "pbkr_rs_rank": rs_rank,
            "tv_rs_proxy_label": (tv_row or {}).get("tv_rs_proxy_label", "absent"),
            "filters": filters,
            "labels": labels,
            "risk": {
                "buckets": list(risk_row.get("buckets") or []),
                "raw_designations": list(risk_row.get("raw_designations") or []),
            },
            "notes": "",
        })

    by_state: dict[str, int] = {}
    for c in candidates:
        by_state[c["state"]] = by_state.get(c["state"], 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "pbkr_rs_rank_source": PBKR_RS_RANK_SOURCE,
        "summary": {
            "total": len(candidates),
            "by_state": by_state,
        },
        "candidates": candidates,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }


def _build_daily_input_packet(
    asof: str,
    tv_pack: dict[str, Any],
    kw_pack: dict[str, Any],
    risk_pack: dict[str, Any],
    candidates_pack: dict[str, Any],
    rs_summary: dict[str, Any],
) -> dict[str, Any]:
    rs_label_dist: dict[str, int] = {"high": 0, "mid": 0, "low": 0, "absent": 0}
    for r in tv_pack["rows"]:
        lbl = r.get("tv_rs_proxy_label") or "absent"
        rs_label_dist[lbl] = rs_label_dist.get(lbl, 0) + 1

    trading_values = [r["trading_value"] for r in kw_pack["rows"] if r.get("trading_value")]
    median_tv = statistics.median(trading_values) if trading_values else 0.0

    by_bucket: dict[str, int] = {}
    for r in risk_pack["rows"]:
        for b in r["buckets"]:
            by_bucket[b] = by_bucket.get(b, 0) + 1

    market_structure_active = market_structure_blocks(risk_pack.get("market_structure", {}))

    watch = sorted(
        (c for c in candidates_pack["candidates"] if c["state"] == "WATCH_CANDIDATE"),
        key=lambda c: (c.get("pbkr_rs_rank") or 0.0),
        reverse=True,
    )[:20]
    watch_top = [{
        "ticker": c["ticker"],
        "name": c["name"],
        "pbkr_rs_rank": c.get("pbkr_rs_rank"),
        "state": c["state"],
    } for c in watch]

    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "pbkr_rs_rank_source": PBKR_RS_RANK_SOURCE,
        "tradingview_role": "auxiliary",
        "market_regime_placeholder": {
            "regime": "unknown",
            "note": "MARKET_CYCLE_SYSTEM_KR posture not yet wired in. Operator must assess MCS-KR before promoting to weekly universe.",
        },
        "tradingview_scan_pack_summary": {
            "row_count": len(tv_pack["rows"]),
            "rs_proxy_label_distribution": rs_label_dist,
        },
        "kiwoom_feature_pack_summary": {
            "row_count": len(kw_pack["rows"]),
            "median_trading_value": float(median_tv),
        },
        "official_risk_flags_pack_summary": {
            "row_count": len(risk_pack["rows"]),
            "by_bucket": by_bucket,
            "market_structure_active": market_structure_active,
        },
        "screening_candidates_pack_summary": {
            "total": candidates_pack["summary"]["total"],
            "by_state": candidates_pack["summary"]["by_state"],
            "watch_candidate_top": watch_top,
        },
        "pbkr_rs_rank_summary": rs_summary,
        "signal_safety": dict(DAILY_PACKET_SIGNAL_SAFETY),
    }


def build_screening_run(
    tradingview_path: str | Path,
    kiwoom_features_path: str | Path,
    kiwoom_universe_path: str | Path,
    official_risk_path: str | Path,
    asof_date: str,
    out_dir: str | Path,
    rs_threshold: float = DEFAULT_RS_THRESHOLD,
    min_trading_value: float = DEFAULT_MIN_TRADING_VALUE,
    rs_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run the full screening pipeline. Returns a manifest of writes."""
    asof = _asof_iso(asof_date)

    tv_pack = load_tradingview_scan(tradingview_path, asof)
    kw_pack = load_kiwoom_features(kiwoom_features_path, asof)
    risk_pack = load_official_risk_flags(official_risk_path, asof)
    universe = load_kiwoom_universe(kiwoom_universe_path)

    rs_ranks = compute_pbkr_rs_rank(
        universe["tickers"],
        benchmark=universe["benchmark"]["closes"] or None,
        weights=rs_weights or DEFAULT_RS_WEIGHTS,
    )
    rs_summary = summarize_rs_rank(
        rs_ranks=rs_ranks,
        threshold=rs_threshold,
        weights=rs_weights or DEFAULT_RS_WEIGHTS,
        benchmark_used=bool(universe["benchmark"]["closes"]),
    )

    candidates_pack = _build_screening_candidates(
        tv_pack=tv_pack,
        kw_pack=kw_pack,
        risk_pack=risk_pack,
        rs_ranks=rs_ranks,
        rs_threshold=rs_threshold,
        min_trading_value=min_trading_value,
        asof=asof,
    )

    daily_packet = _build_daily_input_packet(
        asof=asof,
        tv_pack=tv_pack,
        kw_pack=kw_pack,
        risk_pack=risk_pack,
        candidates_pack=candidates_pack,
        rs_summary=rs_summary,
    )

    manifest = write_outputs(
        out_dir=out_dir,
        asof_date=asof_date,
        tv_pack=tv_pack,
        kw_pack=kw_pack,
        risk_pack=risk_pack,
        candidates_pack=candidates_pack,
        daily_packet=daily_packet,
    )
    manifest["rs_summary"] = rs_summary
    manifest["counts"] = {
        "tradingview_rows": len(tv_pack["rows"]),
        "kiwoom_rows": len(kw_pack["rows"]),
        "risk_rows": len(risk_pack["rows"]),
        "candidates": candidates_pack["summary"]["total"],
        "by_state": candidates_pack["summary"]["by_state"],
    }
    return manifest
