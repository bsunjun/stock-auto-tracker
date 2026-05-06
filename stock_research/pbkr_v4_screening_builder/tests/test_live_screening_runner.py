"""Read-only live screening runner tests.

The runner targets real inputs in production. The tests use the
synthetic fixtures shipped in ``fixtures/`` (anonymized AAA..KKK
tickers, seeded RNG) and a ``tmp_path`` output directory, exercising
the doctrinal preconditions:

  * --no-execution is required;
  * output dir must live outside the repository;
  * each input source must be an existing, non-empty file (no
    silent synthetic fallback on missing source);
  * the verification_report.json is emitted with every counter at 0
    and ``pass: true``;
  * the verification_report payload validates against its schema.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from stock_research.pbkr_v4_screening_builder.constants import (
    DEFAULT_MIN_TRADING_VALUE,
    DEFAULT_RS_THRESHOLD,
    DEFAULT_RS_WEIGHTS,
)
from stock_research.pbkr_v4_screening_builder.live_screening_runner import (
    LiveInputError,
    NoExecutionFlagRequiredError,
    OutputPathInRepoError,
    cli_main,
    run_live_screen,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "fixtures"


def _live_kwargs(tmp_path: Path, **overrides) -> dict:
    base = {
        "date": "2026-05-06",
        "tradingview":     str(FIXTURES / "tradingview_scan_synthetic.json"),
        "kiwoom_features": str(FIXTURES / "kiwoom_features_synthetic.json"),
        "kiwoom_universe": str(FIXTURES / "kiwoom_universe_synthetic.json"),
        "official_risk":   str(FIXTURES / "official_risk_synthetic.json"),
        "output_dir":      str(tmp_path),
        "no_execution":    True,
        "repo_root":       REPO_ROOT,
        "rs_threshold":    DEFAULT_RS_THRESHOLD,
        "min_trading_value": DEFAULT_MIN_TRADING_VALUE,
        "rs_weights":      dict(DEFAULT_RS_WEIGHTS),
    }
    base.update(overrides)
    return base


def test_run_writes_four_outputs_plus_verification_report(tmp_path):
    manifest = run_live_screen(**_live_kwargs(tmp_path))
    run_dir = Path(manifest["out_dir"])
    expected = {
        "tradingview_scan_pack.json",
        "kiwoom_feature_pack.json",
        "official_risk_flags_pack.json",
        "screening_candidates_pack.json",
        "daily_input_packet.json",
        "daily_input_packet.md",
        "verification_report.json",
    }
    actually_written = {p.name for p in run_dir.iterdir() if p.is_file()}
    assert expected.issubset(actually_written)


def test_run_emits_verification_report_with_zero_counters(tmp_path):
    manifest = run_live_screen(**_live_kwargs(tmp_path))
    report_path = Path(manifest["verification_report"])
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["runner"] == "live_screening_runner"
    assert payload["no_execution"] is True
    assert payload["broker_order_path_present"] is False
    assert payload["auto_execution_allowed"] is False
    assert payload["pass"] is True

    counters = payload["doctrinal_counters"]
    for k, v in counters.items():
        assert v == 0, f"{k} must be zero, got {v}"

    safety = payload["signal_safety"]
    assert safety["screening_only"] is True
    assert safety["candidate_generation_only"] is True
    assert safety["direct_trade_signal"] is False
    assert safety["automatic_execution_allowed"] is False
    assert safety["trade_ticket_generation_allowed"] is False
    assert safety["human_gate_required"] is True


def test_run_refuses_repo_internal_output_dir(tmp_path):
    kwargs = _live_kwargs(tmp_path, output_dir=str(REPO_ROOT / "should_not_write"))
    with pytest.raises(OutputPathInRepoError):
        run_live_screen(**kwargs)
    assert not (REPO_ROOT / "should_not_write").exists(), \
        "runner must reject the path before any directory is created"


def test_run_refuses_when_no_execution_flag_is_false(tmp_path):
    kwargs = _live_kwargs(tmp_path, no_execution=False)
    with pytest.raises(NoExecutionFlagRequiredError):
        run_live_screen(**kwargs)


def test_run_refuses_missing_tradingview_input(tmp_path):
    kwargs = _live_kwargs(
        tmp_path,
        tradingview=str(tmp_path / "does_not_exist.json"),
    )
    with pytest.raises(LiveInputError):
        run_live_screen(**kwargs)


def test_run_refuses_empty_input_file(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    kwargs = _live_kwargs(tmp_path / "out", tradingview=str(empty))
    with pytest.raises(LiveInputError):
        run_live_screen(**kwargs)


def test_input_source_fingerprints_recorded(tmp_path):
    manifest = run_live_screen(**_live_kwargs(tmp_path))
    payload = json.loads(Path(manifest["verification_report"]).read_text(encoding="utf-8"))
    sources = payload["input_sources"]
    assert set(sources.keys()) == {"tradingview", "kiwoom_features", "kiwoom_universe", "official_risk"}
    for s in sources.values():
        assert s["exists"] is True
        assert s["size_bytes"] > 0
        assert len(s["sha256_first_mib"]) == 64


def test_verification_report_validates_against_schema(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    manifest = run_live_screen(**_live_kwargs(tmp_path))
    payload = json.loads(Path(manifest["verification_report"]).read_text(encoding="utf-8"))

    schema_path = (
        REPO_ROOT
        / "stock_research"
        / "pbkr_v4_screening_builder"
        / "schemas"
        / "verification_report.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(payload))
    assert errors == [], [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors
    ]


def test_cli_main_returns_2_when_no_execution_flag_missing(tmp_path):
    args = argparse.Namespace(**{
        **_live_kwargs(tmp_path, no_execution=False),
        "rs_weight_m1":  DEFAULT_RS_WEIGHTS["m1"],
        "rs_weight_m3":  DEFAULT_RS_WEIGHTS["m3"],
        "rs_weight_m6":  DEFAULT_RS_WEIGHTS["m6"],
        "rs_weight_m12": DEFAULT_RS_WEIGHTS["m12"],
    })
    # cli_main expects the rs_weights as separate args, plus --output-dir
    # already named correctly. Build the namespace manually:
    args = argparse.Namespace(
        date="2026-05-06",
        tradingview=str(FIXTURES / "tradingview_scan_synthetic.json"),
        kiwoom_features=str(FIXTURES / "kiwoom_features_synthetic.json"),
        kiwoom_universe=str(FIXTURES / "kiwoom_universe_synthetic.json"),
        official_risk=str(FIXTURES / "official_risk_synthetic.json"),
        output_dir=str(tmp_path),
        no_execution=False,
        rs_threshold=DEFAULT_RS_THRESHOLD,
        min_trading_value=DEFAULT_MIN_TRADING_VALUE,
        rs_weight_m1=DEFAULT_RS_WEIGHTS["m1"],
        rs_weight_m3=DEFAULT_RS_WEIGHTS["m3"],
        rs_weight_m6=DEFAULT_RS_WEIGHTS["m6"],
        rs_weight_m12=DEFAULT_RS_WEIGHTS["m12"],
    )
    rc = cli_main(args, REPO_ROOT)
    assert rc == 2


def test_cli_main_succeeds_with_no_execution(tmp_path):
    args = argparse.Namespace(
        date="2026-05-06",
        tradingview=str(FIXTURES / "tradingview_scan_synthetic.json"),
        kiwoom_features=str(FIXTURES / "kiwoom_features_synthetic.json"),
        kiwoom_universe=str(FIXTURES / "kiwoom_universe_synthetic.json"),
        official_risk=str(FIXTURES / "official_risk_synthetic.json"),
        output_dir=str(tmp_path),
        no_execution=True,
        rs_threshold=DEFAULT_RS_THRESHOLD,
        min_trading_value=DEFAULT_MIN_TRADING_VALUE,
        rs_weight_m1=DEFAULT_RS_WEIGHTS["m1"],
        rs_weight_m3=DEFAULT_RS_WEIGHTS["m3"],
        rs_weight_m6=DEFAULT_RS_WEIGHTS["m6"],
        rs_weight_m12=DEFAULT_RS_WEIGHTS["m12"],
    )
    rc = cli_main(args, REPO_ROOT)
    assert rc == 0
