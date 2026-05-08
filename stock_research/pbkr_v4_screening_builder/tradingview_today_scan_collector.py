"""TradingView auxiliary scan collector.

Builds the ``tradingview_scan_latest.json`` input that the read-only
``live-screen`` runner consumes, plus an audit-only
``tradingview_collection_report_latest.json``.

**Auxiliary input only.**  TradingView is *never* the relative-strength
primary source.  The PBKR v4 screening builder computes
``PBKR_RS_RANK`` locally from the Kiwoom daily-OHLCV universe (see
``constants.PBKR_RS_RANK_SOURCE``).  TradingView contributes four
categorical labels per row — ``tv_ema_state``, ``tv_price_action_label``,
``tv_pullback_state``, ``tv_rs_proxy_label`` — plus an optional
``tv_source_timestamp``.  ``tv_rs_proxy_label`` is **never** used as a
hard filter; a missing or absent label is acceptable and a row with
``tv_rs_proxy_label == "absent"`` still passes the screening builder.

Hard rules
----------
1. **No execution.**  ``--no-execution`` is required at the CLI; the
   pack carries the canonical ``signal_safety`` block,
   ``auxiliary_only: true`` and ``screening_input_only: true``.
2. **Output is private.**  The output directory must live under
   ``$PBKR_PROCESSED_ROOT/live_screen_inputs`` (or an explicit
   ``--output-dir``) and **must** resolve outside the repository.
3. **No silent fallback.**  When ``--source-export`` is missing, the
   CLI exits 2 instead of substituting a synthetic / mock fixture.
   Tests pass an explicit fixture path and exercise the same code
   path.
4. **No RS_SCORE hard gate.**  The collector counts how many rows
   carry an ``rs_score`` / ``rs_score_hard_gate`` field on the raw
   input and asserts ``rs_score_hard_gate_count == 0`` in the
   collection report.  Numeric RS_SCORE values *are* allowed in the
   raw export (they get bucketed into ``high`` / ``mid`` / ``low``)
   but no field on the normalized output ever names ``rs_score``.
5. **Atomic publish.**  Both ``_latest.json`` files are written via
   the same two-phase ``<name>.tmp → rename`` sequence the Kiwoom
   collector uses; a partial / failed run never overwrites the
   previous artifacts.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.tradingview_mcp import VALID_RS_PROXY_LABELS, load_tradingview_scan
from .constants import (
    DAILY_PACKET_SIGNAL_SAFETY,
    SCHEMA_VERSION,
    SIGNAL_SAFETY_BLOCK,
)


DEFAULT_OUTPUT_BASE = (
    os.getenv("PBKR_PROCESSED_ROOT")
    or "/Users/bsunjun/trading/phase3/processed"
)

LIVE_SCREEN_INPUTS_SUBDIR = "live_screen_inputs"

TRADINGVIEW_SCAN_FILENAME = "tradingview_scan_latest.json"
TRADINGVIEW_REPORT_FILENAME = "tradingview_collection_report_latest.json"

# Raw-input field names that would imply a hard RS_SCORE gate.  These
# never appear on the normalized pack — the collector counts them on
# the raw input and asserts the count is zero in the audit report.
RS_SCORE_HARD_GATE_FIELDS: tuple[str, ...] = (
    "rs_score_hard_gate",
    "rs_required",
    "require_rs_score",
)


class TradingViewCollectorError(Exception):
    """Base class for TradingView collector errors."""


class TradingViewExportPathInRepoError(TradingViewCollectorError):
    """The --source-export path resolves inside the repository."""


class TradingViewOutputPathInRepoError(TradingViewCollectorError):
    """The requested output directory is inside the repository."""


class TradingViewExportMissingError(TradingViewCollectorError):
    """The --source-export argument was not supplied or the file is missing/empty."""


class TradingViewExportInvalidError(TradingViewCollectorError):
    """The TradingView export file is structurally invalid."""


class TradingViewRSScoreHardGateError(TradingViewCollectorError):
    """The export tries to assert a TradingView RS_SCORE hard gate."""


class TradingViewCollectionFailed(TradingViewCollectorError):
    """The collector failed before any output was published."""


def _assert_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    raise TradingViewOutputPathInRepoError(
        f"refusing to write TradingView collector outputs inside the repository: {path}\n"
        f"set --output-dir (or $PBKR_PROCESSED_ROOT) to a local/private path "
        f"such as {DEFAULT_OUTPUT_BASE}/{LIVE_SCREEN_INPUTS_SUBDIR}"
    )


def _assert_export_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    raise TradingViewExportPathInRepoError(
        f"refusing to read TradingView export from inside the repository: {path}\n"
        "place the export file under a private path."
    )


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    base = Path(DEFAULT_OUTPUT_BASE).expanduser()
    return (base / LIVE_SCREEN_INPUTS_SUBDIR).resolve()


def _publish_atomic(triples: list[tuple[Path, dict[str, Any]]]) -> None:
    """Two-phase atomic publish for the run's _latest.json files.

    Mirrors ``kiwoom_today_universe_collector._publish_atomic``.
    """
    tmps: list[tuple[Path, Path]] = []
    try:
        for path, payload in triples:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmps.append((tmp, path))
    except Exception:
        for tmp, _ in tmps:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
        raise

    for tmp, path in tmps:
        os.replace(tmp, path)


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _asof_iso(date_str: str) -> str:
    return f"{date_str}T15:30:00+09:00"


def _count_rs_score_hard_gates(raw_payload: Any) -> int:
    """Return the number of rows asserting an RS_SCORE hard gate.

    The collector ALWAYS reports zero — if any row sets one of
    ``RS_SCORE_HARD_GATE_FIELDS`` to a truthy value, this function
    surfaces the count and the caller raises.
    """
    rows: list[Any] = []
    if isinstance(raw_payload, dict):
        rows = raw_payload.get("rows") or []
    elif isinstance(raw_payload, list):
        rows = raw_payload
    count = 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        for f in RS_SCORE_HARD_GATE_FIELDS:
            if r.get(f):
                count += 1
                break
    # The pack-level ``rs_score_required: true`` flag would also imply a
    # hard gate.  Count it once if present.
    if isinstance(raw_payload, dict) and raw_payload.get("rs_score_required"):
        count += 1
    return count


def _validate_export_shape(raw_payload: Any, source_path: Path) -> list[dict[str, Any]]:
    """Reject obviously malformed exports.

    Accepted shapes:
      * ``{"rows": [...]}``
      * ``[...]``  (a bare list of row dicts)

    Each row must be a dict with a non-empty ``ticker``.
    """
    if isinstance(raw_payload, dict):
        rows = raw_payload.get("rows")
        if rows is None:
            raise TradingViewExportInvalidError(
                f"TradingView export {source_path} has no 'rows' key."
            )
    elif isinstance(raw_payload, list):
        rows = raw_payload
    else:
        raise TradingViewExportInvalidError(
            f"TradingView export {source_path} must be a JSON object or array."
        )
    if not isinstance(rows, list):
        raise TradingViewExportInvalidError(
            f"TradingView export {source_path} 'rows' must be a JSON array."
        )
    cleaned: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if not r.get("ticker"):
            continue
        cleaned.append(r)
    if not cleaned:
        raise TradingViewExportInvalidError(
            f"TradingView export {source_path} contains zero usable rows."
        )
    return cleaned


@dataclass
class TradingViewCollectionResult:
    asof_date: str
    output_dir: Path
    scan_path: Path
    report_path: Path
    row_count: int
    rs_score_hard_gate_count: int
    source_label: str


def collect_today_tradingview_scan(
    *,
    asof_date: str,
    export_path: str | Path,
    output_dir: Path,
    repo_root: Path,
    source_label: str | None = None,
) -> TradingViewCollectionResult:
    """Build ``tradingview_scan_latest.json`` from a TradingView export.

    The export is a JSON file produced by the operator's TradingView
    desktop / MCP workflow.  The collector never opens a network socket;
    its only job is to normalize the export into the v4 pack shape and
    publish it atomically.
    """
    _assert_outside_repo(output_dir, repo_root)

    src = Path(export_path).expanduser()
    _assert_export_outside_repo(src, repo_root)
    if not src.exists():
        raise TradingViewExportMissingError(
            f"TradingView export not found: {src}\n"
            "the collector refuses to substitute a synthetic / mock input on missing source."
        )
    if not src.is_file():
        raise TradingViewExportMissingError(
            f"TradingView export is not a regular file: {src}"
        )
    if src.stat().st_size == 0:
        raise TradingViewExportMissingError(
            f"TradingView export is empty: {src}\n"
            "the collector refuses to substitute a synthetic / mock input on empty source."
        )

    started_at = _utc_iso_now()

    try:
        raw_payload = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TradingViewExportInvalidError(
            f"TradingView export {src} is not valid JSON: {exc}"
        ) from exc

    cleaned_rows = _validate_export_shape(raw_payload, src)

    rs_score_hard_gate_count = _count_rs_score_hard_gates(raw_payload)
    if rs_score_hard_gate_count > 0:
        raise TradingViewRSScoreHardGateError(
            f"TradingView export {src} asserts an RS_SCORE hard gate "
            f"({rs_score_hard_gate_count} row(s) / pack-level flags).  "
            "TradingView RS_SCORE is auxiliary only and may never be a hard gate."
        )

    pack = load_tradingview_scan(src, asof=_asof_iso(asof_date))
    if source_label:
        pack["source"] = str(source_label)[:120]

    pack_path = output_dir / TRADINGVIEW_SCAN_FILENAME
    report_path = output_dir / TRADINGVIEW_REPORT_FILENAME
    finished_at = _utc_iso_now()

    proxy_label_counts = {label: 0 for label in VALID_RS_PROXY_LABELS}
    for row in pack["rows"]:
        proxy_label_counts[row.get("tv_rs_proxy_label", "absent")] += 1

    report_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "collector": "tradingview_today_scan_collector",
        "asof_date": asof_date,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "output_dir": str(output_dir),
        "scan_file": TRADINGVIEW_SCAN_FILENAME,
        "source_export_path": str(src),
        "source_label": pack["source"],
        "raw_row_count": len(cleaned_rows),
        "normalized_row_count": len(pack["rows"]),
        "rs_score_hard_gate_count": int(rs_score_hard_gate_count),
        "rs_proxy_label_counts": proxy_label_counts,
        "auxiliary_only": True,
        "screening_input_only": True,
        "primary_rs_source": "kiwoom_daily_universe",
        "no_execution": True,
        "broker_order_path_present": False,
        "auto_execution_allowed": False,
        "forbidden_artifact_emitted": False,
        "success": True,
        "failure_reason": None,
        "signal_safety": dict(DAILY_PACKET_SIGNAL_SAFETY),
    }

    _publish_atomic([
        (pack_path, pack),
        (report_path, report_payload),
    ])

    return TradingViewCollectionResult(
        asof_date=asof_date,
        output_dir=output_dir,
        scan_path=pack_path,
        report_path=report_path,
        row_count=len(pack["rows"]),
        rs_score_hard_gate_count=int(rs_score_hard_gate_count),
        source_label=pack["source"],
    )


def cli_main(args: Any, repo_root: Path) -> int:
    """argparse entry point shared by the top-level CLI."""
    if not getattr(args, "no_execution", False):
        print(
            "[tradingview-collect] --no-execution is required.\n"
            "this subcommand is read-only and never authorizes broker orders, "
            "automatic execution, or trade tickets.  re-invoke with --no-execution "
            "to acknowledge.",
            file=sys.stderr,
        )
        return 2

    output_dir = _resolve_output_dir(args.output_dir)
    try:
        _assert_outside_repo(output_dir, repo_root)
    except TradingViewOutputPathInRepoError as exc:
        print(f"[tradingview-collect] {exc}", file=sys.stderr)
        return 2

    source_export = getattr(args, "source_export", None)
    if not source_export:
        print(
            "[tradingview-collect] --source-export <path> is required.\n"
            "supply the TradingView desktop / MCP export JSON.  the collector "
            "never falls back to a synthetic / mock fixture in production.",
            file=sys.stderr,
        )
        return 2

    try:
        result = collect_today_tradingview_scan(
            asof_date=args.date,
            export_path=source_export,
            output_dir=output_dir,
            repo_root=repo_root,
            source_label=getattr(args, "source_label", None),
        )
    except (
        TradingViewExportPathInRepoError,
        TradingViewOutputPathInRepoError,
        TradingViewExportMissingError,
        TradingViewExportInvalidError,
        TradingViewRSScoreHardGateError,
    ) as exc:
        print(f"[tradingview-collect] {exc}", file=sys.stderr)
        return 2
    except TradingViewCollectionFailed as exc:
        print(f"[tradingview-collect] {exc}", file=sys.stderr)
        return 1

    print(f"[tradingview-collect] wrote: {result.scan_path}")
    print(f"[tradingview-collect] wrote: {result.report_path}")
    print(
        f"[tradingview-collect] rows={result.row_count} "
        f"rs_score_hard_gate_count={result.rs_score_hard_gate_count} "
        f"source={result.source_label}"
    )
    print(
        "[tradingview-collect] auxiliary_only=true; PBKR_RS_RANK is computed "
        "from the Kiwoom daily-OHLCV universe (kiwoom_universe_latest.json)."
    )
    return 0
