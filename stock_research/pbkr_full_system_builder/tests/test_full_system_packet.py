"""End-to-end synthetic tests for the PBKR Full System v1 funnel.

The tests load every synthetic fixture, validate each against its
schema, write the entire output set to a tmp directory, and then run
the doctrinal verifier — asserting every forbidden-token counter is 0
and signal-safety invariants hold.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stock_research.pbkr_full_system_builder.full_system_packet_emitter import (
    make_daily_packet_signal_safety_block,
    make_signal_safety_block,
    write_full_system_outputs,
)
from stock_research.pbkr_full_system_builder.full_system_validator import (
    FORBIDDEN_ARTIFACT_TOKENS,
    SCHEMA_FILES,
    SafetyViolation,
    assert_out_dir_outside_repo,
    assert_signal_safety,
    load_schema,
    sanitize_payload,
    validate_with_schema,
    verify_run_directory,
)


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / f"{name}_synthetic.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def packs() -> dict:
    return {
        "market_breadth_pack": _load_fixture("market_breadth_pack"),
        "kr_leader_universe_pack": _load_fixture("kr_leader_universe_pack"),
        "sector_leadership_pack": _load_fixture("sector_leadership_pack"),
        "theme_leadership_pack": _load_fixture("theme_leadership_pack"),
        "evidence_overlay_pack": _load_fixture("evidence_overlay_pack"),
        "pbkr_full_daily_input_packet": _load_fixture("pbkr_full_daily_input_packet"),
    }


def test_schema_files_exist():
    schema_dir = Path(__file__).resolve().parent.parent / "schemas"
    for name, fname in SCHEMA_FILES.items():
        assert (schema_dir / fname).exists(), f"missing schema for {name}"


def test_synthetic_fixtures_validate_against_schemas(packs):
    for name, payload in packs.items():
        schema = load_schema(name)
        validate_with_schema(payload, schema)


def test_signal_safety_blocks(packs):
    for name in (
        "market_breadth_pack",
        "kr_leader_universe_pack",
        "sector_leadership_pack",
        "theme_leadership_pack",
        "evidence_overlay_pack",
    ):
        assert_signal_safety(packs[name], with_operator_decision=False)
    assert_signal_safety(
        packs["pbkr_full_daily_input_packet"], with_operator_decision=True
    )


def test_safety_block_factories():
    block = make_signal_safety_block()
    assert block["screening_only"] is True
    assert block["direct_trade_signal"] is False
    assert "operator_decision" not in block

    daily_review = make_daily_packet_signal_safety_block("review")
    assert daily_review["operator_decision"] == "review"
    daily_defer = make_daily_packet_signal_safety_block("defer")
    assert daily_defer["operator_decision"] == "defer"
    daily_none = make_daily_packet_signal_safety_block(None)
    assert daily_none["operator_decision"] is None

    with pytest.raises(ValueError):
        make_daily_packet_signal_safety_block("execute")


def test_sanitize_payload_rejects_forbidden_keys():
    sanitize_payload({"a": 1})
    with pytest.raises(SafetyViolation):
        sanitize_payload({"account_no": "1234"})
    with pytest.raises(SafetyViolation):
        sanitize_payload({"nested": {"api_key": "abc"}})
    with pytest.raises(SafetyViolation):
        sanitize_payload({"list": [{"order_no": "X"}]})


def test_assert_signal_safety_rejects_violations():
    with pytest.raises(SafetyViolation):
        assert_signal_safety({})
    bad = {
        "signal_safety": {
            "screening_only": True,
            "candidate_generation_only": True,
            "direct_trade_signal": True,
            "trade_signal": False,
            "automatic_execution_allowed": False,
            "trade_ticket_generation_allowed": False,
            "human_gate_required": True,
        }
    }
    with pytest.raises(SafetyViolation):
        assert_signal_safety(bad)
    bad2 = {
        "signal_safety": {
            **bad["signal_safety"],
            "direct_trade_signal": False,
            "automatic_execution_allowed": True,
        }
    }
    with pytest.raises(SafetyViolation):
        assert_signal_safety(bad2)


def test_assert_signal_safety_rejects_execute_operator_decision():
    bad = {
        "signal_safety": {
            "screening_only": True,
            "candidate_generation_only": True,
            "direct_trade_signal": False,
            "trade_signal": False,
            "automatic_execution_allowed": False,
            "trade_ticket_generation_allowed": False,
            "human_gate_required": True,
            "operator_decision": "execute",
        }
    }
    with pytest.raises(SafetyViolation):
        assert_signal_safety(bad, with_operator_decision=True)


def test_write_outputs_refuses_inside_repo(packs, tmp_path):
    inside_repo = REPO_ROOT / "tmp_should_be_rejected"
    with pytest.raises(SafetyViolation):
        write_full_system_outputs(
            inside_repo,
            "2026-05-08",
            packs["market_breadth_pack"],
            packs["kr_leader_universe_pack"],
            packs["sector_leadership_pack"],
            packs["theme_leadership_pack"],
            packs["evidence_overlay_pack"],
            packs["pbkr_full_daily_input_packet"],
            repo_root=REPO_ROOT,
        )


def test_write_outputs_and_verify(packs, tmp_path):
    out = write_full_system_outputs(
        tmp_path,
        "2026-05-08",
        packs["market_breadth_pack"],
        packs["kr_leader_universe_pack"],
        packs["sector_leadership_pack"],
        packs["theme_leadership_pack"],
        packs["evidence_overlay_pack"],
        packs["pbkr_full_daily_input_packet"],
        repo_root=REPO_ROOT,
    )
    run_dir = Path(out["out_dir"])
    assert run_dir.exists()
    expected = {
        "market_breadth_pack.json",
        "kr_leader_universe_pack.json",
        "sector_leadership_pack.json",
        "theme_leadership_pack.json",
        "evidence_overlay_pack.json",
        "pbkr_full_daily_input_packet.json",
        "pbkr_full_daily_input_packet.md",
    }
    assert expected.issubset({p.name for p in run_dir.iterdir()})

    report = verify_run_directory(run_dir)
    assert report["pass"] is True, report
    for key in (
        "direct_trade_signal_true_count",
        "trade_signal_true_count",
        "automatic_execution_allowed_true_count",
        "trade_ticket_generation_allowed_true_count",
        "operator_decision_execute_count",
        "pb_trigger_count",
        "pb_ready_count",
        "pb_scout_count",
        "trade_ticket_count",
        "order_intent_count",
        "order_preparation_count",
        "execution_artifact_count",
        "automatic_alert_count",
        "automatic_execution_hook_count",
        "trade_ticket_file_count",
    ):
        assert report[key] == 0, f"{key}={report[key]} expected 0 — {report}"
    assert not report["errors"]


def test_verify_detects_forbidden_artifact_tokens(packs, tmp_path):
    poisoned_packet = json.loads(
        json.dumps(packs["pbkr_full_daily_input_packet"])
    )
    poisoned_packet["specialist_screen_summary"]["watch_candidate_top"][0][
        "state"
    ] = "PB_TRIGGER"

    write_full_system_outputs(
        tmp_path,
        "2026-05-08",
        packs["market_breadth_pack"],
        packs["kr_leader_universe_pack"],
        packs["sector_leadership_pack"],
        packs["theme_leadership_pack"],
        packs["evidence_overlay_pack"],
        poisoned_packet,
        repo_root=REPO_ROOT,
    )
    run_dir = tmp_path / "2026-05-08"
    report = verify_run_directory(run_dir)
    assert report["pass"] is False
    assert report["pb_trigger_count"] >= 1


def test_verify_detects_execute_operator_decision(packs, tmp_path):
    poisoned_packet = json.loads(
        json.dumps(packs["pbkr_full_daily_input_packet"])
    )
    base = tmp_path / "2026-05-08"
    base.mkdir(parents=True)
    poisoned_packet["signal_safety"]["operator_decision"] = "execute"
    (base / "pbkr_full_daily_input_packet.json").write_text(
        json.dumps(poisoned_packet, indent=2), encoding="utf-8"
    )
    report = verify_run_directory(base)
    assert report["pass"] is False
    assert report["operator_decision_execute_count"] >= 1


def test_no_forbidden_tokens_in_synthetic_fixtures():
    for fname in FIXTURES_DIR.glob("*_synthetic.json"):
        text = fname.read_text(encoding="utf-8")
        for tok in FORBIDDEN_ARTIFACT_TOKENS:
            if tok == "trade_ticket":
                assert "\"trade_ticket\"" not in text and "\"trade_ticket\":" not in text
            else:
                assert tok not in text, f"forbidden token {tok!r} found in {fname.name}"


def test_assert_out_dir_outside_repo(tmp_path):
    assert_out_dir_outside_repo(tmp_path, REPO_ROOT)
    with pytest.raises(SafetyViolation):
        assert_out_dir_outside_repo(REPO_ROOT / "x", REPO_ROOT)
