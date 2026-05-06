"""Output sanitization + verification tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stock_research.pbkr_v4_screening_builder.validator import (
    SafetyViolation,
    sanitize_payload,
    verify_run_directory,
)


def test_sanitize_rejects_account_no():
    with pytest.raises(SafetyViolation):
        sanitize_payload({"account_no": "1234"})


def test_sanitize_rejects_token_nested():
    with pytest.raises(SafetyViolation):
        sanitize_payload({"meta": {"auth": {"token": "secret"}}})


def test_sanitize_rejects_broker_response_in_list():
    with pytest.raises(SafetyViolation):
        sanitize_payload({"items": [{"broker_response": {"ok": True}}]})


def test_sanitize_passes_clean_payload():
    sanitize_payload({"asof": "x", "candidates": [{"ticker": "AAA.KS"}]})


def test_verify_detects_pb_trigger_value(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"state": "PB_TRIGGER"}), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["pb_trigger_count"] == 1
    assert report["pass"] is False


def test_verify_detects_trade_ticket_key(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"trade_ticket": {"id": "x"}}), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["trade_ticket_count"] == 1
    assert report["pass"] is False


def test_verify_detects_order_intent_key(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"order_intent": {"side": "buy"}}), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["order_intent_count"] == 1
    assert report["pass"] is False


def test_verify_detects_automatic_alert_value(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"action": "automatic_alert"}), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["automatic_alert_count"] == 1
    assert report["pass"] is False


def test_verify_detects_trade_ticket_filename(tmp_path: Path):
    bad = tmp_path / "trade_ticket_x.json"
    bad.write_text(json.dumps({"ticker": "AAA.KS"}), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["trade_ticket_file_count"] >= 1
    assert report["pass"] is False


def test_verify_detects_truthy_signal_flags(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({
        "signal_safety": {
            "direct_trade_signal": True,
            "trade_signal": True,
            "automatic_execution_allowed": True,
            "trade_ticket_generation_allowed": True,
        }
    }), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    assert report["direct_trade_signal_true_count"] == 1
    assert report["trade_signal_true_count"] == 1
    assert report["automatic_execution_allowed_true_count"] == 1
    assert report["trade_ticket_generation_allowed_true_count"] == 1
    assert report["pass"] is False


def test_verify_allows_denial_field_name(tmp_path: Path):
    """`trade_ticket_generation_allowed: false` is the *denial*, not an emission."""
    good = tmp_path / "good.json"
    good.write_text(json.dumps({
        "signal_safety": {"trade_ticket_generation_allowed": False}
    }), encoding="utf-8")
    report = verify_run_directory(tmp_path)
    # The substring matches but the allowlist tolerates this exact key.
    assert report["trade_ticket_count"] == 0
    assert report["trade_ticket_generation_allowed_true_count"] == 0
