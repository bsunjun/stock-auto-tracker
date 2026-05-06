"""Shared constants and the canonical signal-safety block."""
from __future__ import annotations

SCHEMA_VERSION = "v4.2"

# The relative-strength primary feature is computed locally from the
# Kiwoom daily-OHLCV universe. TradingView RS_SCORE / RS_PROXY is
# *never* used as a hard filter: it is auxiliary only, and is carried
# (when present) as a categorical label, not as a numeric gate.
PBKR_RS_RANK_SOURCE = "kiwoom_daily_universe"

# Signal-safety block embedded in every payload-bearing JSON. The
# screening builder is candidate generation only.
SIGNAL_SAFETY_BLOCK = {
    "screening_only": True,
    "candidate_generation_only": True,
    "direct_trade_signal": False,
    "trade_signal": False,
    "automatic_execution_allowed": False,
    "trade_ticket_generation_allowed": False,
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

# Forbidden artifact identifiers — the screening builder never emits
# any of these. The post-write verifier counts exact-match
# occurrences in JSON keys / values and asserts zero.
FORBIDDEN_ARTIFACT_TOKENS = (
    "PB_TRIGGER",
    "PB_READY",
    "PB_SCOUT",
    "trade_ticket",
    "order_intent",
    "order_preparation",
    "execution_artifact",
    "automatic_alert",
    "automatic_execution_hook",
)

# Allowed screening-layer states. The five-state contract.
ALLOWED_SCREENING_STATES = (
    "WATCH_CANDIDATE",
    "WATCH_ONLY",
    "RISK_FLAG_PULLBACK_WATCH",
    "REGULAR_PB_EXCLUDE",
    "SCREENING_EXCLUDE",
)
