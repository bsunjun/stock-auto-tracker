"""Full-system pack writer.

Writes the six packs of the PBKR Full System v1 funnel:

  - market_breadth_pack.json
  - kr_leader_universe_pack.json
  - sector_leadership_pack.json
  - theme_leadership_pack.json
  - evidence_overlay_pack.json
  - pbkr_full_daily_input_packet.json
  - pbkr_full_daily_input_packet.md   (human-readable summary)

Outputs are written **outside** the repository tree. Callers must
pass ``out_dir`` explicitly; the local phase3 driver defaults to
``$PBKR_PROCESSED_ROOT`` or ``$PBKR_OUTPUT_ROOT``. A
``SafetyViolation`` is raised if ``out_dir`` resolves inside the repo.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .full_system_validator import (
    DAILY_PACKET_SIGNAL_SAFETY,
    SIGNAL_SAFETY_BLOCK,
    assert_out_dir_outside_repo,
    assert_signal_safety,
    sanitize_payload,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    sanitize_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_full_daily_input_packet_md(packet: dict[str, Any]) -> str:
    mb = packet["market_breadth_summary"]
    leaders = packet["kr_leader_universe_summary"]
    sector = packet["sector_leadership_summary"]
    theme = packet["theme_leadership_summary"]
    spec = packet["specialist_screen_summary"]
    ev = packet["evidence_overlay_summary"]

    lines: list[str] = []
    lines.append("# PBKR Full DAILY_INPUT_PACKET (v1)")
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
    lines.append(
        f"- **tradingview_role:** `{packet['tradingview_role']}` (auxiliary; never a hard filter)"
    )
    lines.append("")

    lines.append("## 1. Market breadth / regime")
    lines.append(f"- regime: `{mb['regime']}`")
    lines.append(f"- pct_above_ma200: {mb['pct_above_ma200']}")
    lines.append(f"- advance_decline_ratio: {mb['advance_decline_ratio']}")
    lines.append("")

    lines.append("## 2. KR leader universe")
    lines.append(f"- universe_size: {leaders['universe_size']}")
    lines.append(f"- leader_count: {leaders['leader_count']}")
    lines.append(f"- rs_threshold: {leaders['rs_threshold']}")
    lines.append("")

    lines.append("## 3. Sector / theme leadership")
    lines.append(f"- sector_count: {sector['sector_count']}")
    lines.append(f"- leading_sector_count: {sector['leading_count']}")
    lines.append(f"- theme_count: {theme['theme_count']}")
    lines.append(f"- leading_theme_count: {theme['leading_count']}")
    lines.append("")

    lines.append("## 4. Specialist screens")
    lines.append(f"- total: {spec['total']}")
    lines.append("- by_screen:")
    for k in ("first_pullback", "pre_breakout_watch", "hve_gap_watch"):
        lines.append(f"  - {k}: {spec['by_screen'].get(k, 0)}")
    if spec.get("watch_candidate_top"):
        lines.append("- watch_candidate_top:")
        for c in spec["watch_candidate_top"]:
            rs_v = c.get("pbkr_rs_rank")
            rs_s = f"{rs_v:.1f}" if isinstance(rs_v, (int, float)) else "n/a"
            lines.append(
                f"  - `{c['ticker']}` ({c['name']}) — pbkr_rs_rank={rs_s}, "
                f"state={c['state']}, screen={c['screen']}"
            )
    lines.append("")

    lines.append("## 5. Evidence overlay")
    lines.append(f"- telegram_row_count: {ev['telegram_row_count']}")
    lines.append(f"- report_row_count: {ev['report_row_count']}")
    lines.append(f"- news_row_count: {ev['news_row_count']}")
    lines.append(f"- official_risk_row_count: {ev['official_risk_row_count']}")
    if ev.get("official_risk_by_bucket"):
        lines.append("- official_risk_by_bucket:")
        for k, v in sorted(ev["official_risk_by_bucket"].items()):
            lines.append(f"  - {k}: {v}")
    lines.append("")

    lines.append("## Hard rules re-stated (educational)")
    lines.append("- This packet does **not** authorize an entry.")
    lines.append("- The full-system layer never emits PB_TRIGGER, PB_READY, PB_SCOUT,")
    lines.append("  trade_ticket, order_intent, order_preparation, execution_artifact,")
    lines.append("  automatic_alert, or automatic_execution_hook.")
    lines.append("- TradingView is auxiliary. Telegram, ReportReader, Gemini news, and")
    lines.append("  official-risk evidence are auxiliary overlays — never hard filters.")
    lines.append("- Operator decision must be `review` or `defer`. `execute` is forbidden.")
    return "\n".join(lines) + "\n"


def write_full_system_outputs(
    out_dir: str | Path,
    asof_date: str,
    market_breadth_pack: dict[str, Any],
    kr_leader_universe_pack: dict[str, Any],
    sector_leadership_pack: dict[str, Any],
    theme_leadership_pack: dict[str, Any],
    evidence_overlay_pack: dict[str, Any],
    full_daily_input_packet: dict[str, Any],
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write the full-system packs to ``out_dir/<asof_date>/``.

    Parameters
    ----------
    out_dir
        Output base directory. Must resolve **outside** the repo.
    asof_date
        Date subdirectory (e.g. ``2026-05-09``).
    repo_root
        Optional repo root used by the out-of-repo guard. If supplied,
        ``out_dir`` will be checked against it via
        ``assert_out_dir_outside_repo``.
    """
    if repo_root is not None:
        assert_out_dir_outside_repo(out_dir, repo_root)

    for pack in (
        market_breadth_pack,
        kr_leader_universe_pack,
        sector_leadership_pack,
        theme_leadership_pack,
        evidence_overlay_pack,
    ):
        assert_signal_safety(pack, with_operator_decision=False)
    assert_signal_safety(full_daily_input_packet, with_operator_decision=True)

    base = Path(out_dir).expanduser() / asof_date
    base.mkdir(parents=True, exist_ok=True)

    paths = {
        "market_breadth_pack":           base / "market_breadth_pack.json",
        "kr_leader_universe_pack":       base / "kr_leader_universe_pack.json",
        "sector_leadership_pack":        base / "sector_leadership_pack.json",
        "theme_leadership_pack":         base / "theme_leadership_pack.json",
        "evidence_overlay_pack":         base / "evidence_overlay_pack.json",
        "pbkr_full_daily_input_packet":  base / "pbkr_full_daily_input_packet.json",
        "pbkr_full_daily_input_packet_md": base / "pbkr_full_daily_input_packet.md",
    }

    _write_json(paths["market_breadth_pack"], market_breadth_pack)
    _write_json(paths["kr_leader_universe_pack"], kr_leader_universe_pack)
    _write_json(paths["sector_leadership_pack"], sector_leadership_pack)
    _write_json(paths["theme_leadership_pack"], theme_leadership_pack)
    _write_json(paths["evidence_overlay_pack"], evidence_overlay_pack)
    _write_json(paths["pbkr_full_daily_input_packet"], full_daily_input_packet)

    md_text = _render_full_daily_input_packet_md(full_daily_input_packet)
    paths["pbkr_full_daily_input_packet_md"].write_text(md_text, encoding="utf-8")

    return {"out_dir": str(base), "files": {k: str(v) for k, v in paths.items()}}


def make_signal_safety_block() -> dict[str, Any]:
    """Return a fresh signal_safety dict for component packs."""
    return dict(SIGNAL_SAFETY_BLOCK)


def make_daily_packet_signal_safety_block(
    operator_decision: str | None = None,
) -> dict[str, Any]:
    """Return a fresh signal_safety dict for the full daily packet.

    ``operator_decision`` must be ``None``, ``"review"``, or ``"defer"``.
    """
    if operator_decision not in (None, "review", "defer"):
        raise ValueError(
            f"operator_decision must be null|review|defer; got {operator_decision!r}"
        )
    block = dict(DAILY_PACKET_SIGNAL_SAFETY)
    block["operator_decision"] = operator_decision
    return block
