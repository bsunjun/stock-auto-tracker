"""Tests for the TradingView auxiliary scan collector.

Covers the PR #68 acceptance criteria for the TradingView side:

* synthetic fixture → tradingview_scan_latest.json PASS
* RS_SCORE absent → still PASS (auxiliary only)
* RS_SCORE hard gate → count 0 in report; bundle that asserts a
  hard gate is rejected
* repo-internal output / export path → fail
* outputs contain ZERO doctrinal trade-artifact tokens
* CLI parser exposes ``tradingview-collect`` with --no-execution gate
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from stock_research.pbkr_v4_screening_builder.cli import build_parser
from stock_research.pbkr_v4_screening_builder.tradingview_today_scan_collector import (
    TRADINGVIEW_REPORT_FILENAME,
    TRADINGVIEW_SCAN_FILENAME,
    TradingViewExportInvalidError,
    TradingViewExportMissingError,
    TradingViewExportPathInRepoError,
    TradingViewOutputPathInRepoError,
    TradingViewRSScoreHardGateError,
    cli_main as tradingview_cli_main,
    collect_today_tradingview_scan,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "schemas"
FIXTURES_DIR = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "fixtures"


# ---------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------


def _ns(**overrides):
    base = dict(
        date="2026-05-08",
        source_export=None,
        source_label=None,
        output_dir=None,
        no_execution=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _write_export(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _minimal_export() -> dict:
    return {
        "source": "synthetic_tv_export",
        "rows": [
            {
                "ticker": "AAA.KS",
                "name": "Synthetic Alpha",
                "tv_ema_state": "above_21ema",
                "tv_price_action_label": "post_breakout_continuation",
                "tv_pullback_state": "shallow",
                "tv_rs_proxy_label": "high",
                "tv_source_timestamp": "2026-05-08T15:30:00+09:00",
            },
            {
                "ticker": "BBB.KQ",
                "name": "Synthetic Bravo",
                "tv_ema_state": "mixed",
                "tv_price_action_label": "consolidation",
                "tv_pullback_state": "none",
                # NOTE: no tv_rs_proxy_label / rs_score → must still pass
            },
        ],
    }


# ---------------------------------------------------------------------
# 1. Synthetic export -> tradingview_scan_latest.json + report.
# ---------------------------------------------------------------------


def test_synthetic_export_writes_scan_and_report(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    out = tmp_path / "live_screen_inputs"
    result = collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=export,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.scan_path == out / TRADINGVIEW_SCAN_FILENAME
    assert result.report_path == out / TRADINGVIEW_REPORT_FILENAME
    assert result.scan_path.exists()
    assert result.report_path.exists()
    pack = json.loads(result.scan_path.read_text(encoding="utf-8"))
    assert pack["auxiliary_only"] is True
    assert pack["screening_input_only"] is True
    assert len(pack["rows"]) == 2
    # The second row (no rs_proxy) is bucketed to "absent" — but PASSes.
    by_ticker = {r["ticker"]: r for r in pack["rows"]}
    assert by_ticker["BBB.KQ"]["tv_rs_proxy_label"] == "absent"


# ---------------------------------------------------------------------
# 2. RS_SCORE absent -> still PASS.
# ---------------------------------------------------------------------


def test_rs_score_absent_still_passes(tmp_path):
    payload = {
        "source": "no_rs_export",
        "rows": [
            {
                "ticker": "CCC.KS",
                "name": "Synthetic Charlie",
                "tv_ema_state": "above_21ema",
                # No rs_score / tv_rs_proxy_label / rs_proxy at all.
            },
        ],
    }
    export = _write_export(tmp_path / "tv_export.json", payload)
    out = tmp_path / "out"
    result = collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=export,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.row_count == 1
    assert result.rs_score_hard_gate_count == 0
    pack = json.loads(result.scan_path.read_text(encoding="utf-8"))
    assert pack["rows"][0]["tv_rs_proxy_label"] == "absent"


# ---------------------------------------------------------------------
# 3. RS_SCORE hard gate is rejected; report records count 0 on success.
# ---------------------------------------------------------------------


def test_rs_score_hard_gate_in_export_is_rejected(tmp_path):
    payload = _minimal_export()
    payload["rows"][0]["rs_score_hard_gate"] = True
    export = _write_export(tmp_path / "tv_export.json", payload)
    with pytest.raises(TradingViewRSScoreHardGateError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=export,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_pack_level_rs_score_required_flag_is_rejected(tmp_path):
    payload = _minimal_export()
    payload["rs_score_required"] = True
    export = _write_export(tmp_path / "tv_export.json", payload)
    with pytest.raises(TradingViewRSScoreHardGateError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=export,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_report_records_rs_score_hard_gate_count_zero(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    out = tmp_path / "out"
    collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=export,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    report = json.loads((out / TRADINGVIEW_REPORT_FILENAME).read_text(encoding="utf-8"))
    assert report["rs_score_hard_gate_count"] == 0
    assert report["auxiliary_only"] is True
    assert report["screening_input_only"] is True
    assert report["primary_rs_source"] == "kiwoom_daily_universe"
    assert report["no_execution"] is True
    assert report["broker_order_path_present"] is False
    assert report["auto_execution_allowed"] is False


# ---------------------------------------------------------------------
# 4. Repo-internal output dir / export path are rejected.
# ---------------------------------------------------------------------


def test_collector_rejects_repo_internal_output_dir(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    with pytest.raises(TradingViewOutputPathInRepoError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=export,
            output_dir=REPO_ROOT / "should_not_write_tv",
            repo_root=REPO_ROOT,
        )
    assert not (REPO_ROOT / "should_not_write_tv").exists()


def test_collector_rejects_export_path_inside_repo(tmp_path):
    in_repo = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "test_inrepo_tv_export.json"
    in_repo.write_text(json.dumps(_minimal_export()), encoding="utf-8")
    try:
        with pytest.raises(TradingViewExportPathInRepoError):
            collect_today_tradingview_scan(
                asof_date="2026-05-08",
                export_path=in_repo,
                output_dir=tmp_path / "out",
                repo_root=REPO_ROOT,
            )
    finally:
        in_repo.unlink(missing_ok=True)


# ---------------------------------------------------------------------
# 5. Missing / empty export is rejected (no synthetic fallback).
# ---------------------------------------------------------------------


def test_missing_export_raises(tmp_path):
    with pytest.raises(TradingViewExportMissingError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=tmp_path / "nope.json",
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_empty_export_raises(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    with pytest.raises(TradingViewExportMissingError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(TradingViewExportInvalidError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_export_with_no_usable_rows_raises(tmp_path):
    p = _write_export(tmp_path / "no_rows.json", {"rows": [{"name": "no ticker"}]})
    with pytest.raises(TradingViewExportInvalidError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


# ---------------------------------------------------------------------
# 6. Schema compatibility: published pack validates against the
#    canonical tradingview_scan_pack schema.
# ---------------------------------------------------------------------


def test_published_scan_validates_against_schema(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    out = tmp_path / "out"
    collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=export,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    pack = json.loads((out / TRADINGVIEW_SCAN_FILENAME).read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS_DIR / "tradingview_scan_pack.schema.json").read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(pack))
    assert errors == [], [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in errors
    ]


# ---------------------------------------------------------------------
# 7. Doctrinal token grep on published outputs.
# ---------------------------------------------------------------------


_FORBIDDEN_TOKENS = (
    "PB_READY", "PB_SCOUT", "PB_TRIGGER",
    "trade_ticket", "order_intent", "order_preparation",
    "execution_artifact", "automatic_alert", "automatic_execution_hook",
)


def _walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, path + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + (f"[{i}]",))
    else:
        yield path, node


def _count_forbidden(payload: dict) -> dict[str, int]:
    counts = {tok: 0 for tok in _FORBIDDEN_TOKENS}
    flag_truthy = {
        "automatic_execution_allowed_true_count": 0,
        "trade_ticket_generation_allowed_true_count": 0,
        "direct_trade_signal_true_count": 0,
        "trade_signal_true_count": 0,
    }
    allowlist_keys = {"trade_ticket_generation_allowed"}
    for path, value in _walk(payload):
        for seg in path:
            base = seg.lstrip("[").rstrip("]")
            if base in allowlist_keys:
                continue
            for tok in _FORBIDDEN_TOKENS:
                if base == tok:
                    counts[tok] += 1
        if isinstance(value, str):
            for tok in _FORBIDDEN_TOKENS:
                if value == tok:
                    counts[tok] += 1
        if path:
            leaf = path[-1]
            if leaf == "automatic_execution_allowed" and value is True:
                flag_truthy["automatic_execution_allowed_true_count"] += 1
            elif leaf == "trade_ticket_generation_allowed" and value is True:
                flag_truthy["trade_ticket_generation_allowed_true_count"] += 1
            elif leaf == "direct_trade_signal" and value is True:
                flag_truthy["direct_trade_signal_true_count"] += 1
            elif leaf == "trade_signal" and value is True:
                flag_truthy["trade_signal_true_count"] += 1
    return {**counts, **flag_truthy}


def test_outputs_contain_no_doctrinal_artifact_tokens_or_truthy_flags(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    out = tmp_path / "out"
    collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=export,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    for name in (TRADINGVIEW_SCAN_FILENAME, TRADINGVIEW_REPORT_FILENAME):
        payload = json.loads((out / name).read_text(encoding="utf-8"))
        counts = _count_forbidden(payload)
        for k, v in counts.items():
            assert v == 0, f"{name}: {k}={v}"


# ---------------------------------------------------------------------
# 8. Failed run leaves previous _latest files untouched.
# ---------------------------------------------------------------------


def test_failed_run_does_not_overwrite_previous_latest(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    prev_scan = out / TRADINGVIEW_SCAN_FILENAME
    prev_report = out / TRADINGVIEW_REPORT_FILENAME
    prev_scan.write_text('{"sentinel": "do_not_overwrite_scan"}', encoding="utf-8")
    prev_report.write_text('{"sentinel": "do_not_overwrite_report"}', encoding="utf-8")

    payload = _minimal_export()
    payload["rows"][0]["rs_score_hard_gate"] = True
    export = _write_export(tmp_path / "tv_export.json", payload)
    with pytest.raises(TradingViewRSScoreHardGateError):
        collect_today_tradingview_scan(
            asof_date="2026-05-08",
            export_path=export,
            output_dir=out,
            repo_root=REPO_ROOT,
        )
    assert json.loads(prev_scan.read_text())["sentinel"] == "do_not_overwrite_scan"
    assert json.loads(prev_report.read_text())["sentinel"] == "do_not_overwrite_report"


# ---------------------------------------------------------------------
# 9. CLI parser + --no-execution gate.
# ---------------------------------------------------------------------


def test_cli_parser_exposes_tradingview_collect_with_safety_flags():
    parser = build_parser()
    ns = parser.parse_args([
        "tradingview-collect",
        "--date", "2026-05-08",
        "--source-export", "/private/path/tv_export.json",
        "--source-label", "tradingview_mcp_2026-05-08",
        "--output-dir", "/private/path/live_screen_inputs",
        "--no-execution",
    ])
    assert ns.command == "tradingview-collect"
    assert ns.source_export == "/private/path/tv_export.json"
    assert ns.source_label == "tradingview_mcp_2026-05-08"
    assert ns.no_execution is True


def test_cli_parser_tradingview_collect_default_no_execution_false():
    parser = build_parser()
    ns = parser.parse_args([
        "tradingview-collect",
        "--date", "2026-05-08",
    ])
    assert ns.no_execution is False
    assert ns.source_export is None


def test_cli_tradingview_collect_requires_no_execution_flag(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    args = _ns(
        source_export=str(export),
        output_dir=str(tmp_path / "out"),
        no_execution=False,
    )
    rc = tradingview_cli_main(args, REPO_ROOT)
    assert rc == 2
    assert not (tmp_path / "out").exists() or not list((tmp_path / "out").glob("*.json"))


def test_cli_tradingview_collect_requires_source_export(tmp_path, monkeypatch):
    args = _ns(
        source_export=None,
        output_dir=str(tmp_path / "out"),
        no_execution=True,
    )
    rc = tradingview_cli_main(args, REPO_ROOT)
    assert rc == 2


def test_cli_tradingview_collect_succeeds_with_no_execution(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    out = tmp_path / "out"
    args = _ns(
        source_export=str(export),
        output_dir=str(out),
        no_execution=True,
    )
    rc = tradingview_cli_main(args, REPO_ROOT)
    assert rc == 0
    assert (out / TRADINGVIEW_SCAN_FILENAME).exists()
    assert (out / TRADINGVIEW_REPORT_FILENAME).exists()


def test_cli_tradingview_collect_refuses_repo_output(tmp_path):
    export = _write_export(tmp_path / "tv_export.json", _minimal_export())
    args = _ns(
        source_export=str(export),
        output_dir=str(REPO_ROOT / "should_not_write_tv_cli"),
        no_execution=True,
    )
    rc = tradingview_cli_main(args, REPO_ROOT)
    assert rc == 2
    assert not (REPO_ROOT / "should_not_write_tv_cli").exists()


# ---------------------------------------------------------------------
# 10. Existing project fixture validates end-to-end.
# ---------------------------------------------------------------------


def test_collector_consumes_existing_synthetic_fixture(tmp_path):
    """The PR #65 synthetic fixture is a valid input shape for the collector.

    This locks in compatibility: the screening-builder fixture and the
    PR #68 collector both consume the same export shape.  We deliberately
    copy the fixture into tmp_path because the collector refuses to read
    a path inside the repo.
    """
    src = FIXTURES_DIR / "tradingview_scan_synthetic.json"
    target = tmp_path / "tv_export.json"
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    out = tmp_path / "out"
    result = collect_today_tradingview_scan(
        asof_date="2026-05-08",
        export_path=target,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.row_count == 11  # number of rows in the fixture
    assert result.rs_score_hard_gate_count == 0
