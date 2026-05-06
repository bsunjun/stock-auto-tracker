"""Tests for the read-only Kiwoom REST today-universe collector.

These tests exercise the doctrinal preconditions the collector has to
honour (read-only TR allow-list, repo-internal output rejection,
missing config rejection, atomic _latest writes that don't overwrite
on failure, schema compatibility with the live-screen runner) using
``MockKiwoomRestClient`` and a ``tmp_path`` output directory.

They also assert that the on-disk artifacts contain **zero**
doctrinal trade-artifact tokens (PB_READY / PB_SCOUT / PB_TRIGGER /
trade_ticket / order_intent / order_preparation / execution_artifact /
automatic_alert / automatic_execution_hook) and that no value sets
``automatic_execution_allowed`` (or its siblings) to ``true``.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import pytest

from stock_research.pbkr_v4_screening_builder.cli import build_parser
from stock_research.pbkr_v4_screening_builder.kiwoom_today_universe_collector import (
    KIWOOM_COLLECTION_REPORT_FILENAME,
    KIWOOM_FEATURES_FILENAME,
    KIWOOM_UNIVERSE_FILENAME,
    CollectorConfig,
    KiwoomCollectionFailed,
    KiwoomConfigMissingError,
    KiwoomForbiddenEndpointError,
    KiwoomOutputPathInRepoError,
    MIN_CLOSE_SERIES_LEN,
    MockKiwoomRestClient,
    _assert_tr_allowed,
    cli_main as collector_cli_main,
    collect_today_universe,
    load_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "schemas"


# ---------------------------------------------------------------------
# Helpers / fixtures.
# ---------------------------------------------------------------------


def _build_synthetic_universe(seed: int = 20260506) -> tuple[
    dict[str, list[dict]], dict[str, list[dict]], dict[str, list[dict]]
]:
    """Return (universe_by_market, daily_ohlcv_by_ticker, daily_flows_by_ticker).

    ~270 sessions of close history per ticker so the 252-day RS gate
    is satisfied without padding.  All identifiers are anonymized
    (``AAA.KS``, ``BBB.KQ``, …) and the RNG is seeded so the test
    is deterministic.
    """
    rng = random.Random(seed)
    profiles = [
        ("AAA.KS", "Synthetic Alpha",   "KOSPI",  "common", 25_000.0),
        ("BBB.KQ", "Synthetic Bravo",   "KOSDAQ", "common", 12_000.0),
        ("CCC.KS", "Synthetic Charlie", "KOSPI",  "common", 18_000.0),
        ("DDD.KQ", "Synthetic Delta",   "KOSDAQ", "common", 22_000.0),
        ("EEE.KS", "Synthetic Echo",    "KOSPI",  "common", 30_000.0),
    ]
    extras = [
        # ETF — must be excluded by default.
        ("ZZZ.KS", "KODEX Synthetic",   "KOSPI", "etf",  10_000.0, {}),
        # Trading halt — must be excluded.
        ("YYY.KQ", "Synthetic Yankee",  "KOSDAQ", "common", 5_000.0, {"trading_halt": True}),
    ]
    universe: dict[str, list[dict]] = {"KOSPI": [], "KOSDAQ": []}
    ohlcv: dict[str, list[dict]] = {}
    flows: dict[str, list[dict]] = {}

    n = 270  # > MIN_CLOSE_SERIES_LEN

    for tkr, name, market, sec_type, base in profiles:
        universe[market].append({
            "ticker": tkr, "name": name, "market": market, "sec_type": sec_type,
        })
        rows = []
        prev = base
        for _ in range(n):
            ret = rng.normalvariate(0.0008, 0.012)
            close = max(prev * math.exp(ret), 1.0)
            high  = close * (1.0 + abs(rng.normalvariate(0.0, 0.005)))
            low   = close * (1.0 - abs(rng.normalvariate(0.0, 0.005)))
            open_ = (high + low) / 2.0
            volume = rng.uniform(50_000, 600_000)
            rows.append({
                "open": round(open_, 2),
                "high": round(high, 2),
                "low":  round(low, 2),
                "close": round(close, 2),
                "volume": int(volume),
                "trading_value": round(close * volume, 0),
                "volume_ratio": round(rng.uniform(0.6, 2.5), 2),
            })
            prev = close
        ohlcv[tkr] = rows
        flows[tkr] = [
            {
                "investor_flow":             round(rng.uniform(-3.0e9, 3.0e9), 0),
                "foreigner_flow":            round(rng.uniform(-2.0e9, 4.0e9), 0),
                "institution_flow":          round(rng.uniform(-2.0e9, 2.0e9), 0),
                "financial_investment_flow": round(rng.uniform(-1.0e9, 1.5e9), 0),
            }
            for _ in range(n)
        ]

    for tkr, name, market, sec_type, base, extras_kw in extras:
        row = {"ticker": tkr, "name": name, "market": market, "sec_type": sec_type}
        row.update(extras_kw)
        universe[market].append(row)
        # Even if these were not pruned, still ship a series to prove
        # the upstream filter — not the close-length gate — drops them.
        rows = [{
            "open": base, "high": base, "low": base, "close": base,
            "volume": 1_000, "trading_value": base * 1_000, "volume_ratio": 1.0,
        }] * n
        ohlcv[tkr] = rows
        flows[tkr] = []
    return universe, ohlcv, flows


def _mock_client_for(universe, ohlcv, flows) -> MockKiwoomRestClient:
    return MockKiwoomRestClient(
        universe=universe, daily_ohlcv=ohlcv, daily_flows=flows,
    )


def _config_dict(path: Path) -> dict:
    return {
        "rest_base_url": "https://example.invalid/kiwoom",
        "appkey":        "TEST_APPKEY_NOT_REAL",
        "appsecret":     "TEST_APPSECRET_NOT_REAL",
        "benchmark_ticker": "BENCHMARK_KOSPI_PROXY",
        "benchmark_closes": [2700.0 + i * 0.5 for i in range(280)],
        "__source_path": str(path),
    }


# ---------------------------------------------------------------------
# 1. Repo-internal output path is rejected.
# ---------------------------------------------------------------------


def test_collector_rejects_repo_internal_output_dir(tmp_path):
    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)
    with pytest.raises(KiwoomOutputPathInRepoError):
        collect_today_universe(
            asof_date="2026-05-06",
            config=_config_dict(tmp_path / "kiwoom_config.json"),
            client=client,
            output_dir=REPO_ROOT / "should_not_write",
            repo_root=REPO_ROOT,
        )
    assert not (REPO_ROOT / "should_not_write").exists()


# ---------------------------------------------------------------------
# 2. Missing config / token causes explicit failure.
# ---------------------------------------------------------------------


def test_load_config_missing_file(tmp_path):
    with pytest.raises(KiwoomConfigMissingError):
        load_config(tmp_path / "does_not_exist.json")


def test_load_config_missing_required_keys(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"rest_base_url": "https://x"}), encoding="utf-8")
    with pytest.raises(KiwoomConfigMissingError):
        load_config(bad)


def test_cli_kiwoom_collect_requires_config(tmp_path, monkeypatch):
    monkeypatch.delenv("KIWOOM_REST_CONFIG", raising=False)
    args = argparse.Namespace(
        date="2026-05-06", config=None, output_dir=str(tmp_path),
    )
    rc = collector_cli_main(args, REPO_ROOT)
    assert rc == 2


def test_cli_kiwoom_collect_refuses_repo_output(tmp_path, monkeypatch):
    cfg_path = tmp_path / "kiwoom_config.json"
    cfg_path.write_text(json.dumps({
        "rest_base_url": "https://example.invalid",
        "appkey":        "TEST_APPKEY_NOT_REAL",
        "appsecret":     "TEST_APPSECRET_NOT_REAL",
    }), encoding="utf-8")
    monkeypatch.setenv("KIWOOM_REST_CONFIG", str(cfg_path))
    args = argparse.Namespace(
        date="2026-05-06", config=None,
        output_dir=str(REPO_ROOT / "should_not_write_either"),
    )
    rc = collector_cli_main(args, REPO_ROOT)
    assert rc == 2
    assert not (REPO_ROOT / "should_not_write_either").exists()


# ---------------------------------------------------------------------
# 3. No order / account endpoint code path exists.
# ---------------------------------------------------------------------


def test_assert_tr_allowed_rejects_unknown_id():
    with pytest.raises(KiwoomForbiddenEndpointError):
        _assert_tr_allowed("ka10001_order_request", allowed=("ka10099", "ka10081"))


def test_assert_tr_allowed_rejects_account_token_even_in_allowed_list():
    # Even if an operator mis-configured allowlist with an account TR,
    # the substring guard still rejects it.
    with pytest.raises(KiwoomForbiddenEndpointError):
        _assert_tr_allowed(
            "ka_account_balance",
            allowed=("ka_account_balance", "ka10081"),
        )


def test_collector_module_does_not_reference_account_or_order_endpoints():
    """grep guard: no order / account TR token literally appears."""
    from stock_research.pbkr_v4_screening_builder import (
        kiwoom_today_universe_collector as mod,
    )

    src = Path(mod.__file__).read_text(encoding="utf-8")
    needle = (
        "kt10000",  # 매수주문
        "kt10001",  # 매도주문
        "/oapi/order",
        "/uapi/domestic-stock/v1/trading",
        "account_no",
        "account_number",
        "cash_balance_inquiry",
    )
    for s in needle:
        assert s not in src, (
            f"collector accidentally references a forbidden endpoint token: {s!r}"
        )


# ---------------------------------------------------------------------
# 4. Synthetic mock client produces a complete pair of latest files.
# ---------------------------------------------------------------------


def test_synthetic_collect_writes_three_outputs(tmp_path):
    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)
    out = tmp_path / "live_screen_inputs"

    result = collect_today_universe(
        asof_date="2026-05-06",
        config=_config_dict(tmp_path / "kiwoom_config.json"),
        client=client,
        output_dir=out,
        repo_root=REPO_ROOT,
    )

    assert result.features_path.name == KIWOOM_FEATURES_FILENAME
    assert result.universe_path.name == KIWOOM_UNIVERSE_FILENAME
    assert result.report_path.name == KIWOOM_COLLECTION_REPORT_FILENAME
    assert result.feature_rows == 5  # the 5 common-share profiles
    assert "ZZZ.KS" in result.rejected_tickers  # ETF
    assert "YYY.KQ" in result.rejected_tickers  # halted


# ---------------------------------------------------------------------
# 5. kiwoom_universe_latest.json is schema-compatible with the runner's
# expectations (>= MIN_CLOSE_SERIES_LEN closes per ticker, plus the
# benchmark close series).
# ---------------------------------------------------------------------


def test_synthetic_universe_close_series_meets_rs_window(tmp_path):
    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)
    out = tmp_path / "out"
    collect_today_universe(
        asof_date="2026-05-06",
        config=_config_dict(tmp_path / "kiwoom_config.json"),
        client=client,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    payload = json.loads((out / KIWOOM_UNIVERSE_FILENAME).read_text(encoding="utf-8"))
    assert "benchmark" in payload and "tickers" in payload
    assert payload["benchmark"]["ticker"] == "BENCHMARK_KOSPI_PROXY"
    assert len(payload["benchmark"]["closes"]) >= MIN_CLOSE_SERIES_LEN
    assert payload["tickers"], "universe must contain at least one ticker"
    for tkr, body in payload["tickers"].items():
        assert len(body["closes"]) >= MIN_CLOSE_SERIES_LEN, (
            f"{tkr}: only {len(body['closes'])} closes — below {MIN_CLOSE_SERIES_LEN}"
        )


# ---------------------------------------------------------------------
# 6. kiwoom_features_latest.json validates against the canonical
#    kiwoom_feature_pack schema.
# ---------------------------------------------------------------------


def test_features_latest_validates_against_kiwoom_feature_pack_schema(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)
    out = tmp_path / "out"
    collect_today_universe(
        asof_date="2026-05-06",
        config=_config_dict(tmp_path / "kiwoom_config.json"),
        client=client,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    payload = json.loads((out / KIWOOM_FEATURES_FILENAME).read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS_DIR / "kiwoom_feature_pack.schema.json").read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(payload))
    assert errors == [], [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in errors
    ]


# ---------------------------------------------------------------------
# 7. Failure mode: when the collector cannot produce any feature rows
#    it must NOT overwrite the previous _latest files.
# ---------------------------------------------------------------------


def test_failed_run_does_not_overwrite_previous_latest(tmp_path):
    out = tmp_path / "out"
    out.mkdir(parents=True)
    prev_features = out / KIWOOM_FEATURES_FILENAME
    prev_universe = out / KIWOOM_UNIVERSE_FILENAME
    prev_features.write_text('{"sentinel": "do_not_overwrite_features"}', encoding="utf-8")
    prev_universe.write_text('{"sentinel": "do_not_overwrite_universe"}', encoding="utf-8")

    # Empty universe -> no feature rows -> KiwoomCollectionFailed.
    client = MockKiwoomRestClient(universe={"KOSPI": [], "KOSDAQ": []})
    with pytest.raises(KiwoomCollectionFailed):
        collect_today_universe(
            asof_date="2026-05-06",
            config=_config_dict(tmp_path / "kiwoom_config.json"),
            client=client,
            output_dir=out,
            repo_root=REPO_ROOT,
        )
    assert prev_features.read_text(encoding="utf-8") == '{"sentinel": "do_not_overwrite_features"}'
    assert prev_universe.read_text(encoding="utf-8") == '{"sentinel": "do_not_overwrite_universe"}'

    # Report DID get written (the report exists to explain the failure).
    report_path = out / KIWOOM_COLLECTION_REPORT_FILENAME
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["success"] is False
    assert report["failure_reason"]


# ---------------------------------------------------------------------
# 8. Output payloads contain ZERO doctrinal trade-artifact tokens.
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


def test_outputs_contain_no_doctrinal_artifact_tokens_or_truthy_execution_flags(tmp_path):
    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)
    out = tmp_path / "out"
    collect_today_universe(
        asof_date="2026-05-06",
        config=_config_dict(tmp_path / "kiwoom_config.json"),
        client=client,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    for name in (KIWOOM_FEATURES_FILENAME, KIWOOM_UNIVERSE_FILENAME, KIWOOM_COLLECTION_REPORT_FILENAME):
        payload = json.loads((out / name).read_text(encoding="utf-8"))
        counts = _count_forbidden(payload)
        for k, v in counts.items():
            assert v == 0, f"{name}: {k}={v}"


# ---------------------------------------------------------------------
# 9. The CLI parser exposes ``kiwoom-collect`` and respects --output-dir.
# ---------------------------------------------------------------------


def test_cli_parser_lists_kiwoom_collect_subcommand():
    parser = build_parser()
    ns = parser.parse_args([
        "kiwoom-collect",
        "--date", "2026-05-06",
        "--config", "/private/path/kiwoom_config.json",
        "--output-dir", "/private/path/live_screen_inputs",
    ])
    assert ns.command == "kiwoom-collect"
    assert ns.date == "2026-05-06"
    assert ns.config == "/private/path/kiwoom_config.json"
    assert ns.output_dir == "/private/path/live_screen_inputs"
