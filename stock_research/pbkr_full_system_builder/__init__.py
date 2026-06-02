"""PBKR Full System v1 — funnel packet contract.

Educational doctrine support tooling. Not a trade signal.
``screening_only=true``. ``candidate_generation_only=true``.
``direct_trade_signal=false``. ``automatic_execution_allowed=false``.
``trade_ticket_generation_allowed=false``. ``human_gate_required=true``.

This module wraps the existing PBKR v4 single-screen builder into the
full handbook funnel:

  1. Market Breadth / Regime
  2. KR Leader Universe
  3. Sector / Theme Leadership
  4. Specialist Screens
       - First Pullback
       - Pre-Breakout Watch
       - HVE / Gap Watch
  5. Evidence Overlay
       - Telegram ThemeRadar
       - ReportReader
       - Gemini NewsGrounder
       - Official Risk
  6. DAILY_INPUT_PACKET aggregator

The full-system layer **never** emits ``PB_TRIGGER``, ``PB_READY``,
``PB_SCOUT``, ``trade_ticket``, ``order_intent``,
``order_preparation``, ``execution_artifact``, ``automatic_alert``,
or ``automatic_execution_hook``. The post-write verifier counts
each token and asserts zero.
"""

__version__ = "v1.0"
