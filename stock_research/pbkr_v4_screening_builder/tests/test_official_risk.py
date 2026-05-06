"""KR designation taxonomy mapper tests."""
from __future__ import annotations

from stock_research.pbkr_v4_screening_builder.adapters.official_risk import (
    _classify_designation,
)


def test_administrative_issue_is_hard_exclude():
    assert "HARD_EXCLUDE" in _classify_designation("관리종목")


def test_trading_halt_is_hard_exclude():
    assert "HARD_EXCLUDE" in _classify_designation("거래정지")


def test_unfaithful_disclosure_is_hard_exclude():
    assert "HARD_EXCLUDE" in _classify_designation("불성실공시법인")


def test_non_standard_audit_is_hard_exclude():
    assert "HARD_EXCLUDE" in _classify_designation("감사의견 거절")


def test_investment_risk_is_extreme():
    assert "EXTREME_RISK_FLAG_WATCH" in _classify_designation("투자위험종목")


def test_investment_warning_is_regular_pb_exclude():
    assert "REGULAR_PB_EXCLUDE" in _classify_designation("투자경고")


def test_investment_attention_is_regular_pb_exclude():
    assert "REGULAR_PB_EXCLUDE" in _classify_designation("투자주의")


def test_short_term_overheating_is_regular_pb_exclude():
    assert "REGULAR_PB_EXCLUDE" in _classify_designation("단기과열")


def test_clean_string_yields_no_buckets():
    assert _classify_designation("") == set()
    assert _classify_designation("ordinary_news") == set()
