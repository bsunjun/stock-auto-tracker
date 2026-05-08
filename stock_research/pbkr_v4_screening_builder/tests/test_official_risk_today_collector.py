"""Tests for the KRX/KIND/DART official-risk collector.

Covers the PR #68 acceptance criteria for the official-risk side:

* sources_checked missing/empty → fail (no synthetic all-none fallback)
* sources_checked = ["KRX"] + no flags → audit_status =
  NO_OFFICIAL_RISK_FLAG_CONFIRMED
* market-structure active → market_structure_state =
  NO_ENTRY_MARKET_STRUCTURE_ACTIVE
* telegram / news / blog source → rejected (non-official)
* repo-internal output / bundle path → fail
* outputs contain ZERO doctrinal trade-artifact tokens
* HARD_EXCLUDE designations carry the right bucket
* CLI parser exposes ``official-risk-collect`` with --no-execution gate
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from stock_research.pbkr_v4_screening_builder.cli import build_parser
from stock_research.pbkr_v4_screening_builder.official_risk_today_collector import (
    ALLOWED_OFFICIAL_SOURCES,
    OFFICIAL_RISK_FLAGS_FILENAME,
    OFFICIAL_RISK_REPORT_FILENAME,
    OfficialRiskBundleInvalidError,
    OfficialRiskBundleMissingError,
    OfficialRiskBundlePathInRepoError,
    OfficialRiskNoSourceCheckedError,
    OfficialRiskOutputPathInRepoError,
    OfficialRiskUnauthorizedSourceError,
    cli_main as official_risk_cli_main,
    collect_today_official_risk,
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
        source_bundle=None,
        output_dir=None,
        no_execution=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _write_bundle(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _clean_bundle(sources=("KRX", "KIND", "DART")) -> dict:
    return {
        "sources_checked": list(sources),
        "market_structure": {
            "circuit_breaker_active": False,
            "sidecar_active": False,
            "auction_window": "none",
        },
        "rows": [
            {"ticker": "AAA.KS", "raw_designations": []},
            {"ticker": "BBB.KQ", "raw_designations": []},
            {"ticker": "CCC.KS", "raw_designations": []},
        ],
    }


def _flagged_bundle() -> dict:
    return {
        "sources_checked": ["KRX", "KIND", "DART"],
        "market_structure": {
            "circuit_breaker_active": False,
            "sidecar_active": False,
            "auction_window": "none",
        },
        "rows": [
            {"ticker": "AAA.KS", "raw_designations": []},
            {"ticker": "BBB.KQ", "raw_designations": ["투자주의"]},
            {"ticker": "CCC.KS", "raw_designations": ["투자위험"]},
            {"ticker": "DDD.KQ", "raw_designations": ["관리종목", "거래정지"]},
            {"ticker": "EEE.KS", "raw_designations": ["불성실공시"]},
            {"ticker": "FFF.KQ", "raw_designations": ["감사의견 거절"]},
        ],
    }


# ---------------------------------------------------------------------
# 1. sources_checked missing / empty -> refuse.
# ---------------------------------------------------------------------


def test_missing_sources_checked_is_rejected(tmp_path):
    bad = _clean_bundle()
    del bad["sources_checked"]
    p = _write_bundle(tmp_path / "bundle.json", bad)
    with pytest.raises(OfficialRiskNoSourceCheckedError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_empty_sources_checked_is_rejected(tmp_path):
    bad = _clean_bundle()
    bad["sources_checked"] = []
    p = _write_bundle(tmp_path / "bundle.json", bad)
    with pytest.raises(OfficialRiskNoSourceCheckedError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


# ---------------------------------------------------------------------
# 2. checked + no flags -> NO_OFFICIAL_RISK_FLAG_CONFIRMED.
# ---------------------------------------------------------------------


def test_no_flags_with_sources_checked_emits_no_official_risk_flag_confirmed(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    out = tmp_path / "out"
    result = collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.audit_status == "NO_OFFICIAL_RISK_FLAG_CONFIRMED"
    assert result.flagged_row_count == 0
    pack = json.loads(result.flags_path.read_text(encoding="utf-8"))
    assert pack["audit_status"] == "NO_OFFICIAL_RISK_FLAG_CONFIRMED"
    assert pack["sources_checked"] == ["KRX", "KIND", "DART"]


def test_flagged_bundle_emits_official_risk_flags_present(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _flagged_bundle())
    out = tmp_path / "out"
    result = collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.audit_status == "OFFICIAL_RISK_FLAGS_PRESENT"
    pack = json.loads(result.flags_path.read_text(encoding="utf-8"))
    assert pack["audit_status"] == "OFFICIAL_RISK_FLAGS_PRESENT"
    by_ticker = {r["ticker"]: r for r in pack["rows"]}
    assert "REGULAR_PB_EXCLUDE" in by_ticker["BBB.KQ"]["buckets"]
    assert "EXTREME_RISK_FLAG_WATCH" in by_ticker["CCC.KS"]["buckets"]
    assert "HARD_EXCLUDE" in by_ticker["DDD.KQ"]["buckets"]
    assert "HARD_EXCLUDE" in by_ticker["EEE.KS"]["buckets"]
    assert "HARD_EXCLUDE" in by_ticker["FFF.KQ"]["buckets"]


# ---------------------------------------------------------------------
# 3. market_structure_state = NO_ENTRY_MARKET_STRUCTURE_ACTIVE.
# ---------------------------------------------------------------------


@pytest.mark.parametrize("market_structure_overrides", [
    {"circuit_breaker_active": True},
    {"sidecar_active": True},
    {"auction_window": "opening"},
    {"auction_window": "closing"},
])
def test_market_structure_active_state(tmp_path, market_structure_overrides):
    bundle = _clean_bundle()
    bundle["market_structure"].update(market_structure_overrides)
    p = _write_bundle(tmp_path / "bundle.json", bundle)
    out = tmp_path / "out"
    result = collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.market_structure_state == "NO_ENTRY_MARKET_STRUCTURE_ACTIVE"
    pack = json.loads(result.flags_path.read_text(encoding="utf-8"))
    assert pack["market_structure"]["market_structure_state"] == "NO_ENTRY_MARKET_STRUCTURE_ACTIVE"


def test_market_structure_open_state(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    out = tmp_path / "out"
    result = collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    assert result.market_structure_state == "OPEN"


# ---------------------------------------------------------------------
# 4. Non-official sources are rejected.
# ---------------------------------------------------------------------


@pytest.mark.parametrize("forbidden", [
    "telegram", "news", "blog", "twitter", "x",
    "youtube", "kakao", "discord", "reddit", "naver_cafe",
    "Telegram",  # case-insensitive
])
def test_non_official_source_in_sources_checked_is_rejected(tmp_path, forbidden):
    bundle = _clean_bundle()
    bundle["sources_checked"] = ["KRX", forbidden]
    p = _write_bundle(tmp_path / "bundle.json", bundle)
    with pytest.raises(OfficialRiskUnauthorizedSourceError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_unknown_source_is_rejected(tmp_path):
    bundle = _clean_bundle()
    bundle["sources_checked"] = ["KRX", "MADE_UP_SOURCE"]
    p = _write_bundle(tmp_path / "bundle.json", bundle)
    with pytest.raises(OfficialRiskUnauthorizedSourceError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_only_allowed_sources_pass(tmp_path):
    for source in ALLOWED_OFFICIAL_SOURCES:
        bundle = _clean_bundle()
        bundle["sources_checked"] = [source]
        p = _write_bundle(tmp_path / f"{source}.json", bundle)
        result = collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / f"out_{source}",
            repo_root=REPO_ROOT,
        )
        assert result.sources_checked == [source]


# ---------------------------------------------------------------------
# 5. Repo-internal output / bundle path are rejected.
# ---------------------------------------------------------------------


def test_collector_rejects_repo_internal_output_dir(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    with pytest.raises(OfficialRiskOutputPathInRepoError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=REPO_ROOT / "should_not_write_orisk",
            repo_root=REPO_ROOT,
        )
    assert not (REPO_ROOT / "should_not_write_orisk").exists()


def test_collector_rejects_bundle_inside_repo(tmp_path):
    in_repo = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "test_inrepo_orisk_bundle.json"
    in_repo.write_text(json.dumps(_clean_bundle()), encoding="utf-8")
    try:
        with pytest.raises(OfficialRiskBundlePathInRepoError):
            collect_today_official_risk(
                asof_date="2026-05-08",
                bundle_path=in_repo,
                output_dir=tmp_path / "out",
                repo_root=REPO_ROOT,
            )
    finally:
        in_repo.unlink(missing_ok=True)


# ---------------------------------------------------------------------
# 6. Missing / empty / invalid bundles are rejected (no synthetic fallback).
# ---------------------------------------------------------------------


def test_missing_bundle_raises(tmp_path):
    with pytest.raises(OfficialRiskBundleMissingError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=tmp_path / "nope.json",
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_empty_bundle_raises(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    with pytest.raises(OfficialRiskBundleMissingError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_invalid_json_bundle_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{oops", encoding="utf-8")
    with pytest.raises(OfficialRiskBundleInvalidError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


def test_bundle_without_rows_raises(tmp_path):
    bad = _clean_bundle()
    del bad["rows"]
    p = _write_bundle(tmp_path / "bundle.json", bad)
    with pytest.raises(OfficialRiskBundleInvalidError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=tmp_path / "out",
            repo_root=REPO_ROOT,
        )


# ---------------------------------------------------------------------
# 7. Schema compatibility: published pack validates against the
#    canonical official_risk_flags_pack schema.
# ---------------------------------------------------------------------


def test_published_pack_validates_against_schema(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    p = _write_bundle(tmp_path / "bundle.json", _flagged_bundle())
    out = tmp_path / "out"
    collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    pack = json.loads((out / OFFICIAL_RISK_FLAGS_FILENAME).read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS_DIR / "official_risk_flags_pack.schema.json").read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(pack))
    assert errors == [], [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in errors
    ]


# ---------------------------------------------------------------------
# 8. Doctrinal token grep on published outputs.
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


def test_outputs_contain_no_doctrinal_artifact_tokens(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _flagged_bundle())
    out = tmp_path / "out"
    collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    for name in (OFFICIAL_RISK_FLAGS_FILENAME, OFFICIAL_RISK_REPORT_FILENAME):
        payload = json.loads((out / name).read_text(encoding="utf-8"))
        counts = _count_forbidden(payload)
        for k, v in counts.items():
            assert v == 0, f"{name}: {k}={v}"


# ---------------------------------------------------------------------
# 9. Failed run leaves previous _latest files untouched.
# ---------------------------------------------------------------------


def test_failed_run_does_not_overwrite_previous_latest(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    prev_flags = out / OFFICIAL_RISK_FLAGS_FILENAME
    prev_report = out / OFFICIAL_RISK_REPORT_FILENAME
    prev_flags.write_text('{"sentinel": "do_not_overwrite_flags"}', encoding="utf-8")
    prev_report.write_text('{"sentinel": "do_not_overwrite_report"}', encoding="utf-8")

    bad = _clean_bundle()
    del bad["sources_checked"]
    p = _write_bundle(tmp_path / "bundle.json", bad)
    with pytest.raises(OfficialRiskNoSourceCheckedError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p,
            output_dir=out,
            repo_root=REPO_ROOT,
        )
    assert json.loads(prev_flags.read_text())["sentinel"] == "do_not_overwrite_flags"
    assert json.loads(prev_report.read_text())["sentinel"] == "do_not_overwrite_report"


# ---------------------------------------------------------------------
# 10. CLI parser + --no-execution gate.
# ---------------------------------------------------------------------


def test_cli_parser_exposes_official_risk_collect_with_safety_flags():
    parser = build_parser()
    ns = parser.parse_args([
        "official-risk-collect",
        "--date", "2026-05-08",
        "--source-bundle", "/private/path/orisk_bundle.json",
        "--output-dir", "/private/path/live_screen_inputs",
        "--no-execution",
    ])
    assert ns.command == "official-risk-collect"
    assert ns.source_bundle == "/private/path/orisk_bundle.json"
    assert ns.no_execution is True


def test_cli_parser_official_risk_default_no_execution_false():
    parser = build_parser()
    ns = parser.parse_args([
        "official-risk-collect",
        "--date", "2026-05-08",
    ])
    assert ns.no_execution is False
    assert ns.source_bundle is None


def test_cli_official_risk_collect_requires_no_execution_flag(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    args = _ns(
        source_bundle=str(p),
        output_dir=str(tmp_path / "out"),
        no_execution=False,
    )
    rc = official_risk_cli_main(args, REPO_ROOT)
    assert rc == 2
    assert not (tmp_path / "out").exists() or not list((tmp_path / "out").glob("*.json"))


def test_cli_official_risk_collect_requires_source_bundle(tmp_path):
    args = _ns(
        source_bundle=None,
        output_dir=str(tmp_path / "out"),
        no_execution=True,
    )
    rc = official_risk_cli_main(args, REPO_ROOT)
    assert rc == 2


def test_cli_official_risk_collect_succeeds_with_no_execution(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    out = tmp_path / "out"
    args = _ns(
        source_bundle=str(p),
        output_dir=str(out),
        no_execution=True,
    )
    rc = official_risk_cli_main(args, REPO_ROOT)
    assert rc == 0
    assert (out / OFFICIAL_RISK_FLAGS_FILENAME).exists()
    assert (out / OFFICIAL_RISK_REPORT_FILENAME).exists()
    pack = json.loads((out / OFFICIAL_RISK_FLAGS_FILENAME).read_text(encoding="utf-8"))
    assert pack["audit_status"] == "NO_OFFICIAL_RISK_FLAG_CONFIRMED"


def test_cli_official_risk_collect_refuses_repo_output(tmp_path):
    p = _write_bundle(tmp_path / "bundle.json", _clean_bundle())
    args = _ns(
        source_bundle=str(p),
        output_dir=str(REPO_ROOT / "should_not_write_orisk_cli"),
        no_execution=True,
    )
    rc = official_risk_cli_main(args, REPO_ROOT)
    assert rc == 2
    assert not (REPO_ROOT / "should_not_write_orisk_cli").exists()


# ---------------------------------------------------------------------
# 11. Bundle compatibility with the existing screening fixture shape.
# ---------------------------------------------------------------------


def test_collector_consumes_existing_synthetic_fixture_with_sources_added(tmp_path):
    """The PR #65 synthetic fixture is missing ``sources_checked`` by design.

    The collector must reject it as-is; once we add ``sources_checked``
    the same payload publishes successfully, demonstrating the new
    field is the only delta required.
    """
    src = FIXTURES_DIR / "official_risk_synthetic.json"
    raw = json.loads(src.read_text(encoding="utf-8"))

    # Without sources_checked: rejected.
    p_bare = _write_bundle(tmp_path / "bundle_bare.json", raw)
    with pytest.raises(OfficialRiskNoSourceCheckedError):
        collect_today_official_risk(
            asof_date="2026-05-08",
            bundle_path=p_bare,
            output_dir=tmp_path / "out_bare",
            repo_root=REPO_ROOT,
        )

    # With sources_checked: published.
    raw["sources_checked"] = ["KRX", "KIND", "DART"]
    p_ok = _write_bundle(tmp_path / "bundle_ok.json", raw)
    result = collect_today_official_risk(
        asof_date="2026-05-08",
        bundle_path=p_ok,
        output_dir=tmp_path / "out_ok",
        repo_root=REPO_ROOT,
    )
    assert result.audit_status == "OFFICIAL_RISK_FLAGS_PRESENT"
