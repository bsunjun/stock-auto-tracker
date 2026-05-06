"""Output emitter for the four packs and the DAILY_INPUT_PACKET.

Outputs land **outside** the repo by default. Callers must pass
``out_dir`` explicitly; the CLI defaults to ``$PBKR_SCREENING_OUT``
or ``/tmp/pbkr_v4_screening_out``.

The Markdown rendering of DAILY_INPUT_PACKET is a human-readable
summary; the JSON is canonical for the orchestrator.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validator import sanitize_payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    sanitize_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_daily_input_packet_md(packet: dict[str, Any]) -> str:
    summary = packet["screening_candidates_pack_summary"]
    rs = packet["pbkr_rs_rank_summary"]
    risk_summary = packet["official_risk_flags_pack_summary"]

    lines: list[str] = []
    lines.append("# DAILY_INPUT_PACKET (PBKR v4)")
    lines.append("")
    lines.append("> Educational. **Not advice. Not a trade signal.**")
    lines.append("> `screening_only = true`. `candidate_generation_only = true`.")
    lines.append("> `direct_trade_signal = false`. `automatic_execution_allowed = false`.")
    lines.append("> `trade_ticket_generation_allowed = false`. `human_gate_required = true`.")
    lines.append("> `operator_decision != execute`.")
    lines.append("")
    lines.append(f"- **as-of:** {packet['asof']}")
    lines.append(f"- **schema_version:** {packet['schema_version']}")
    lines.append(f"- **pbkr_rs_rank_source:** `{packet['pbkr_rs_rank_source']}` (primary)")
    lines.append(f"- **tradingview_role:** `{packet['tradingview_role']}` (auxiliary; never a hard filter)")
    lines.append("")
    lines.append("## Market regime placeholder")
    lines.append(f"- regime: `{packet['market_regime_placeholder']['regime']}`")
    lines.append(f"- note: {packet['market_regime_placeholder']['note']}")
    lines.append("")
    lines.append("## TradingView scan pack (auxiliary)")
    lines.append(f"- row_count: {packet['tradingview_scan_pack_summary']['row_count']}")
    dist = packet['tradingview_scan_pack_summary']['rs_proxy_label_distribution']
    lines.append(
        "- tv_rs_proxy_label distribution: "
        f"high={dist.get('high', 0)}, mid={dist.get('mid', 0)}, "
        f"low={dist.get('low', 0)}, absent={dist.get('absent', 0)}"
    )
    lines.append("")
    lines.append("## Kiwoom feature pack (primary)")
    lines.append(f"- row_count: {packet['kiwoom_feature_pack_summary']['row_count']}")
    lines.append(f"- median_trading_value: {packet['kiwoom_feature_pack_summary']['median_trading_value']:,.0f} KRW")
    lines.append("")
    lines.append("## Official risk flags pack")
    lines.append(f"- row_count: {risk_summary['row_count']}")
    lines.append(f"- market_structure_active: {risk_summary['market_structure_active']}")
    if risk_summary["by_bucket"]:
        lines.append("- by_bucket:")
        for k, v in sorted(risk_summary["by_bucket"].items()):
            lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("## PBKR_RS_RANK summary")
    lines.append(f"- source: `{rs['source']}` (primary relative-strength feature)")
    lines.append(f"- universe_size: {rs['universe_size']}")
    lines.append(f"- threshold: {rs['threshold']}")
    lines.append(f"- passed_threshold_count: {rs['passed_threshold_count']}")
    lines.append(f"- benchmark_relative_used: {rs['benchmark_relative_used']}")
    w = rs["weights"]
    lines.append(f"- weights: 1M={w['m1']}, 3M={w['m3']}, 6M={w['m6']}, 12M={w['m12']}")
    lines.append("")
    lines.append("## Screening candidates pack")
    lines.append(f"- total: {summary['total']}")
    if summary["by_state"]:
        lines.append("- by_state:")
        for k in (
            "WATCH_CANDIDATE",
            "WATCH_ONLY",
            "RISK_FLAG_PULLBACK_WATCH",
            "REGULAR_PB_EXCLUDE",
            "SCREENING_EXCLUDE",
        ):
            if k in summary["by_state"]:
                lines.append(f"  - {k}: {summary['by_state'][k]}")
    if summary["watch_candidate_top"]:
        lines.append("- watch_candidate_top:")
        for c in summary["watch_candidate_top"]:
            rs_v = c["pbkr_rs_rank"]
            rs_s = f"{rs_v:.1f}" if isinstance(rs_v, (int, float)) else "n/a"
            lines.append(f"  - `{c['ticker']}` ({c['name']}) — pbkr_rs_rank={rs_s}, state={c['state']}")
    lines.append("")
    lines.append("## Hard rules re-stated (educational)")
    lines.append("- This packet does **not** authorize an entry.")
    lines.append("- The screening builder never emits `PB_TRIGGER`, `PB_READY`, `PB_SCOUT`,")
    lines.append("  `trade_ticket`, `order_intent`, `order_preparation`, `execution_artifact`,")
    lines.append("  `automatic_alert`, or `automatic_execution_hook`.")
    lines.append("- `RISK_FLAG_PULLBACK_WATCH` is a watch-only label and **never** promotes to `PB_TRIGGER`.")
    lines.append("- TradingView is **auxiliary**: `tv_rs_proxy_label` is informational, never a hard filter.")
    lines.append("- Operator decision must be `review` or `defer`. `execute` is forbidden at this stage.")
    return "\n".join(lines) + "\n"


def write_outputs(
    out_dir: str | Path,
    asof_date: str,
    tv_pack: dict[str, Any],
    kw_pack: dict[str, Any],
    risk_pack: dict[str, Any],
    candidates_pack: dict[str, Any],
    daily_packet: dict[str, Any],
) -> dict[str, Any]:
    base = Path(out_dir).expanduser() / asof_date
    base.mkdir(parents=True, exist_ok=True)

    paths = {
        "tradingview_scan_pack":      base / "tradingview_scan_pack.json",
        "kiwoom_feature_pack":        base / "kiwoom_feature_pack.json",
        "official_risk_flags_pack":   base / "official_risk_flags_pack.json",
        "screening_candidates_pack":  base / "screening_candidates_pack.json",
        "daily_input_packet_json":    base / "daily_input_packet.json",
        "daily_input_packet_md":      base / "daily_input_packet.md",
    }

    _write_json(paths["tradingview_scan_pack"], tv_pack)
    _write_json(paths["kiwoom_feature_pack"], kw_pack)
    _write_json(paths["official_risk_flags_pack"], risk_pack)
    _write_json(paths["screening_candidates_pack"], candidates_pack)
    _write_json(paths["daily_input_packet_json"], daily_packet)

    md_text = _render_daily_input_packet_md(daily_packet)
    paths["daily_input_packet_md"].write_text(md_text, encoding="utf-8")

    return {"out_dir": str(base), "files": {k: str(v) for k, v in paths.items()}}
