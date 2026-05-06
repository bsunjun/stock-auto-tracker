"""Output sanitization tests."""
from __future__ import annotations

import pytest

from stock_research.pbkr_v4_screening_builder.validator import (
    SafetyViolation,
    sanitize_payload,
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
