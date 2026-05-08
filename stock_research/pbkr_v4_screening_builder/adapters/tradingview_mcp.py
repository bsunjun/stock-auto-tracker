"""TradingView MCP / Screener scan adapter.

The real production adapter calls a TradingView MCP server. For
development and CI we accept a pre-shaped JSON file that mirrors the
MCP server's response shape.

**Auxiliary only.** TradingView MCP is *not* the relative-strength
source. It supplies four auxiliary fields:

    tv_ema_state            — categorical EMA posture
    tv_price_action_label   — short price-action label
    tv_pullback_state       — pullback posture label
    tv_rs_proxy_label       — categorical RS proxy (high/mid/low/absent)

`tv_rs_proxy_label` is **never** used as a hard filter. The
screening builder treats RS_SCORE as optional and never required —
the primary relative-strength feature is `pbkr_rs_rank`, computed
locally from the Kiwoom daily-OHLCV universe (see
``constants.PBKR_RS_RANK_SOURCE``).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..constants import SCHEMA_VERSION, SIGNAL_SAFETY_BLOCK


VALID_EMA_STATES = {
    "above_21ema",
    "at_21ema",
    "below_21ema",
    "alignment_up",
    "alignment_down",
    "mixed",
}

VALID_RS_PROXY_LABELS = {"high", "mid", "low", "absent"}


def _bucket_rs_proxy(value: Any) -> str:
    """Map an optional RS_SCORE/RS_PROXY input to a categorical label.

    Inputs accepted:
      * a string already in {"high", "mid", "low", "absent"}
      * a number (TradingView's 0..100 RS_SCORE), bucketed into
        ``high`` (>=80), ``mid`` (>=50), ``low`` (<50)
      * ``None`` / missing / invalid → ``"absent"``

    The returned label is informational only; the screening filters
    do *not* gate on it.
    """
    if value is None:
        return "absent"
    if isinstance(value, str):
        v = value.strip().lower()
        return v if v in VALID_RS_PROXY_LABELS else "absent"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "absent"
    if n != n:  # NaN
        return "absent"
    if n >= 80:
        return "high"
    if n >= 50:
        return "mid"
    return "low"


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    # accept both the new tv_* names and the legacy unprefixed names
    ema_raw = raw.get("tv_ema_state") or raw.get("ema_state") or "mixed"
    tv_ema_state = str(ema_raw).strip()
    if tv_ema_state not in VALID_EMA_STATES:
        tv_ema_state = "mixed"

    tv_price_action_label = str(
        raw.get("tv_price_action_label") or raw.get("price_action_label") or ""
    ).strip()[:64]
    tv_pullback_state = str(
        raw.get("tv_pullback_state") or raw.get("pullback_label") or ""
    ).strip()[:64]
    tv_rs_proxy_label = _bucket_rs_proxy(
        raw.get("tv_rs_proxy_label", raw.get("rs_proxy"))
    )

    target_ema = raw.get("target_ema")
    if target_ema is not None:
        try:
            target_ema = int(target_ema)
        except (TypeError, ValueError):
            target_ema = None

    out: dict[str, Any] = {
        "ticker": str(raw["ticker"]).strip(),
        "name": str(raw.get("name") or raw["ticker"]).strip(),
        "target_ema": target_ema,
        "tv_ema_state": tv_ema_state,
        "tv_price_action_label": tv_price_action_label,
        "tv_pullback_state": tv_pullback_state,
        "tv_rs_proxy_label": tv_rs_proxy_label,
    }
    ts = raw.get("tv_source_timestamp")
    if ts is not None:
        ts_str = str(ts).strip()[:40]
        if ts_str:
            out["tv_source_timestamp"] = ts_str
    return out


def load_tradingview_scan(path: str | Path, asof: str) -> dict[str, Any]:
    """Load a TradingView MCP scan fixture and produce a normalized pack."""
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    raw_rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    rows = [_normalize_row(r) for r in raw_rows if isinstance(r, dict) and r.get("ticker")]

    return {
        "schema_version": SCHEMA_VERSION,
        "asof": asof,
        "source": str(payload.get("source", "tradingview_mcp_scan") if isinstance(payload, dict) else "tradingview_mcp_scan"),
        "auxiliary_only": True,  # TradingView is never the RS primary source
        "screening_input_only": True,  # row labels are evidence, never trade signals
        "rows": rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
