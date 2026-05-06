"""TradingView MCP / Screener scan adapter.

The real production adapter calls a TradingView MCP server. For
development and CI we accept a pre-shaped JSON file that mirrors the
MCP server's response shape. RS_PROXY (i.e. TradingView RS_SCORE) is
*optional* — TradingView's free Screener does not always expose it,
and the screening engine never assumes it.
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


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    ema_state = str(raw.get("ema_state") or "mixed").strip()
    if ema_state not in VALID_EMA_STATES:
        ema_state = "mixed"

    rs_proxy = raw.get("rs_proxy")
    if rs_proxy is not None:
        try:
            rs_proxy = max(0.0, min(100.0, float(rs_proxy)))
        except (TypeError, ValueError):
            rs_proxy = None

    target_ema = raw.get("target_ema")
    if target_ema is not None:
        try:
            target_ema = int(target_ema)
        except (TypeError, ValueError):
            target_ema = None

    return {
        "ticker": str(raw["ticker"]).strip(),
        "name": str(raw.get("name") or raw["ticker"]).strip(),
        "target_ema": target_ema,
        "ema_state": ema_state,
        "price_action_label": str(raw.get("price_action_label", "")).strip()[:64],
        "pullback_label": str(raw.get("pullback_label", "")).strip()[:64],
        "rs_proxy": rs_proxy,
    }


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
        "rows": rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
