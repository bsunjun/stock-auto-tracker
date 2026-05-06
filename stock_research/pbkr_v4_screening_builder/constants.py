"""Shared constants and the canonical signal-safety block."""
from __future__ import annotations

SCHEMA_VERSION = "v4.1"

SIGNAL_SAFETY_BLOCK = {
    "screening_only": True,
    "direct_trade_signal": False,
    "trade_signal": False,
    "automatic_execution_allowed": False,
    "human_gate_required": True,
}

DAILY_PACKET_SIGNAL_SAFETY = {
    **SIGNAL_SAFETY_BLOCK,
    "operator_decision": None,
}

# Default screening parameters.
DEFAULT_RS_THRESHOLD = 80.0
DEFAULT_MIN_TRADING_VALUE = 5_000_000_000.0  # 50 억 KRW
DEFAULT_RS_WEIGHTS = {"m1": 0.20, "m3": 0.30, "m6": 0.30, "m12": 0.20}

# Approximate trading-day windows for return horizons.
RS_WINDOW_DAYS = {"m1": 21, "m3": 63, "m6": 126, "m12": 252}

# Forbidden keys — never persist these in any output.
FORBIDDEN_KEYS = {
    "account_no",
    "account_number",
    "order_no",
    "order_id",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "broker_response",
}
