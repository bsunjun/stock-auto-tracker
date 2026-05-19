"""DART fundamentals adapter for Deepvue-style Korean-market screens.

The production collector should keep DART credentials and raw filings outside
this repository.  This adapter intentionally accepts only a local, pre-shaped
JSON export and normalizes the fields required by the preset screen filters.

Supported row aliases are deliberately broad because DART extractors may name
quarterly / annual fields differently.  Unknown or unavailable values remain
``None`` so the corresponding screen predicate fails closed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..constants import SCHEMA_VERSION, SIGNAL_SAFETY_BLOCK


def _f(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, str):
        v = v.replace(",", "").replace("%", "").strip()
        if not v:
            return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def _first_float(raw: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in raw:
            value = _f(raw.get(key))
            if value is not None:
                return value
    return None


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    ticker = str(raw.get("ticker") or raw.get("code") or raw.get("stock_code") or "").strip()
    if not ticker:
        raise ValueError("DART fundamentals row is missing ticker/code/stock_code")
    return {
        "ticker": ticker,
        "eps_growth_latest_qtr_pct": _first_float(
            raw,
            "eps_growth_latest_qtr_pct",
            "eps_growth_latest_reported_qtr_pct",
            "latest_qtr_eps_growth_pct",
            "eps_yoy_q_pct",
        ),
        "avg_eps_growth_last_3yrs_pct": _first_float(
            raw,
            "avg_eps_growth_last_3yrs_pct",
            "avg_eps_growth_last_3_years_pct",
            "eps_cagr_3y_pct",
        ),
        "eps_growth_next_qtr_pct": _first_float(
            raw,
            "eps_growth_next_qtr_pct",
            "consensus_eps_growth_next_qtr_pct",
            "next_qtr_eps_growth_pct",
        ),
        "eps_surprise_latest_qtr_pct": _first_float(
            raw,
            "eps_surprise_latest_qtr_pct",
            "latest_qtr_eps_surprise_pct",
            "earnings_surprise_latest_qtr_pct",
        ),
        "sales_growth_latest_qtr_pct": _first_float(
            raw,
            "sales_growth_latest_qtr_pct",
            "sales_growth_latest_reported_qtr_pct",
            "latest_qtr_sales_growth_pct",
            "revenue_yoy_q_pct",
        ),
        "sales_growth_next_qtr_pct": _first_float(
            raw,
            "sales_growth_next_qtr_pct",
            "consensus_sales_growth_next_qtr_pct",
            "next_qtr_sales_growth_pct",
        ),
        # KRW amounts.  Exporters may provide won or million-won values.
        "sales_latest_rptd_year_krw": _first_float(
            raw,
            "sales_latest_rptd_year_krw",
            "revenue_latest_year_krw",
            "annual_sales_krw",
        ),
        "sales_latest_rptd_qtr_krw": _first_float(
            raw,
            "sales_latest_rptd_qtr_krw",
            "revenue_latest_qtr_krw",
            "quarterly_sales_krw",
        ),
        "ipo_date": raw.get("ipo_date") or raw.get("listing_date"),
    }


def load_dart_fundamentals(path: str | Path, asof: str) -> dict[str, Any]:
    """Load a private DART-derived fundamentals JSON export.

    Accepted shapes are either ``[{...}]`` or ``{"rows": [{...}]}``.
    The returned pack contains no credentials or raw filing payloads.
    """
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    raw_rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    rows = [_normalize_row(r) for r in raw_rows if isinstance(r, dict)]
    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "rows": rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
