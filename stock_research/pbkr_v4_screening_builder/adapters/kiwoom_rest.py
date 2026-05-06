"""Kiwoom REST API adapter.

Production: hits Kiwoom OpenAPI REST endpoints (with credentials kept
strictly in the local environment). For development and CI we accept
a pre-shaped JSON file with already-computed daily features.

The adapter also computes a few derived helpers when the upstream
input omits them: 20d/60d high, MA fallbacks. ATR / MAs are *not*
back-computed here — when missing they remain ``None`` and downstream
filters degrade gracefully.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..constants import SCHEMA_VERSION, SIGNAL_SAFETY_BLOCK


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None  # NaN guard


def _last(seq: Iterable[float] | None) -> float | None:
    if not seq:
        return None
    seq = list(seq)
    return _f(seq[-1]) if seq else None


def _max_window(closes: list[float] | None, window: int) -> float | None:
    if not closes:
        return None
    sl = closes[-window:] if len(closes) >= window else closes
    return max(sl) if sl else None


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    closes = raw.get("closes")
    if isinstance(closes, list):
        closes_f = [_f(x) for x in closes if _f(x) is not None]
    else:
        closes_f = []

    close = _f(raw.get("close")) or _last(closes_f)

    high_20d = _f(raw.get("high_20d")) or _max_window(closes_f, 20)
    high_60d = _f(raw.get("high_60d")) or _max_window(closes_f, 60)

    return {
        "ticker": str(raw["ticker"]).strip(),
        "close": close if close is not None else 0.0,
        "open":  _f(raw.get("open")),
        "high":  _f(raw.get("high")),
        "low":   _f(raw.get("low")),
        "volume": _f(raw.get("volume")),
        "trading_value": _f(raw.get("trading_value")) or 0.0,
        "volume_ratio": _f(raw.get("volume_ratio")),
        "investor_flow":              _f(raw.get("investor_flow")),
        "foreigner_flow":              _f(raw.get("foreigner_flow")),
        "institution_flow":            _f(raw.get("institution_flow")),
        "financial_investment_flow":   _f(raw.get("financial_investment_flow")),
        "ma9":   _f(raw.get("ma9")),
        "ma21":  _f(raw.get("ma21")),
        "ma50":  _f(raw.get("ma50")),
        "ma120": _f(raw.get("ma120")),
        "atr14": _f(raw.get("atr14")),
        "recent_low":    _f(raw.get("recent_low")),
        "stop_distance": _f(raw.get("stop_distance")),
        "high_20d": high_20d,
        "high_60d": high_60d,
    }


def load_kiwoom_features(path: str | Path, asof: str) -> dict[str, Any]:
    """Load Kiwoom daily features into the canonical kiwoom_feature_pack shape."""
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    raw_rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    rows = [_normalize_row(r) for r in raw_rows if isinstance(r, dict) and r.get("ticker")]

    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "rows": rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }


def load_kiwoom_universe(path: str | Path) -> dict[str, Any]:
    """Load the Kiwoom universe daily-close series used by the RS calculator.

    Expected shape::

        {
          "benchmark": { "ticker": "KOSPI", "closes": [..., float, ...] },
          "tickers": {
              "AAA.KS": { "closes": [...] },
              "BBB.KQ": { "closes": [...] },
              ...
          }
        }

    Raw real OHLCV must never be committed; this loader is meant to
    consume a file that lives outside the repo.
    """
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"kiwoom_universe payload must be an object: {path}")

    bench = payload.get("benchmark") or {}
    bench_closes = [_f(x) for x in bench.get("closes") or [] if _f(x) is not None]

    tickers = {}
    for tkr, body in (payload.get("tickers") or {}).items():
        closes = [_f(x) for x in (body or {}).get("closes") or [] if _f(x) is not None]
        if closes:
            tickers[str(tkr)] = closes

    return {
        "benchmark": {
            "ticker": str(bench.get("ticker") or "BENCHMARK"),
            "closes": bench_closes,
        },
        "tickers": tickers,
    }
