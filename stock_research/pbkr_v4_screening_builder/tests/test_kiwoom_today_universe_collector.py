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
    DEFAULT_ALLOWED_TR_IDS,
    KIWOOM_COLLECTION_REPORT_FILENAME,
    KIWOOM_FEATURES_FILENAME,
    KIWOOM_UNIVERSE_FILENAME,
    WELL_KNOWN_FORBIDDEN_TR_IDS,
    CollectorConfig,
    KiwoomCollectionFailed,
    KiwoomConfigMissingError,
    KiwoomConfigPathInRepoError,
    KiwoomForbiddenEndpointError,
    KiwoomOutputPathInRepoError,
    MIN_CLOSE_SERIES_LEN,
    MockKiwoomRestClient,
    _assert_tr_allowed,
    _resolve_allowed_tr_ids,
    cli_main as collector_cli_main,
    collect_today_universe,
    load_config,
    normalize_ka10060_response,
    normalize_ka10081_response,
    normalize_ka10099_response,
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


def test_collector_module_does_not_invoke_account_or_order_endpoints():
    """grep guard: no order / account endpoint URL or response key is invoked.

    The module deliberately *names* the well-known forbidden TR ids
    inside ``WELL_KNOWN_FORBIDDEN_TR_IDS`` and the ``KiwoomRestClient``
    Protocol docstring so the operator gets a pointed error message
    when their config accidentally lists one — this is the same
    denial-reference pattern the canonical ``validator.py`` uses for
    ``trade_ticket_generation_allowed``.  Behavioural rejection of
    those TR ids is asserted by the
    ``test_resolve_allowed_tr_ids_rejects_*`` tests below.

    This test only catches the *invocation* signatures: account /
    order endpoint URLs, account/cash response field names — strings
    a real client wrapper would have to hit to authorize an order.
    """
    from stock_research.pbkr_v4_screening_builder import (
        kiwoom_today_universe_collector as mod,
    )

    src = Path(mod.__file__).read_text(encoding="utf-8")
    needle = (
        "/oapi/order",
        "/uapi/domestic-stock/v1/trading",
        "/api/dostk/ord",
        "/api/dostk/acnt",
        "account_no",
        "account_number",
        "cash_balance_inquiry",
        "ord_qty",
        "ord_dvsn",
    )
    for s in needle:
        assert s not in src, (
            f"collector references an account / order invocation token: {s!r}"
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


# ---------------------------------------------------------------------
# 10. Default TR allow-list matches the official market-data-only set.
# ---------------------------------------------------------------------


def test_default_allowed_tr_ids_matches_official_market_data_set():
    assert DEFAULT_ALLOWED_TR_IDS == ("ka10099", "ka10081", "ka10060")


# ---------------------------------------------------------------------
# 11. config["allowed_tr_ids"] enforcement: subset-only.
# ---------------------------------------------------------------------


def test_resolve_allowed_tr_ids_default_when_unset():
    assert _resolve_allowed_tr_ids(None) == DEFAULT_ALLOWED_TR_IDS


def test_resolve_allowed_tr_ids_subset_is_accepted():
    assert _resolve_allowed_tr_ids(["ka10099"]) == ("ka10099",)
    assert _resolve_allowed_tr_ids(("ka10099", "ka10081")) == ("ka10099", "ka10081")


def test_resolve_allowed_tr_ids_rejects_account_tr():
    with pytest.raises(KiwoomForbiddenEndpointError):
        _resolve_allowed_tr_ids(["ka00001"])  # 계좌번호조회


@pytest.mark.parametrize("forbidden_tr", ["kt10000", "kt10001", "kt10002", "kt10003", "kt00011"])
def test_resolve_allowed_tr_ids_rejects_order_tr(forbidden_tr):
    with pytest.raises(KiwoomForbiddenEndpointError):
        _resolve_allowed_tr_ids([forbidden_tr])


def test_resolve_allowed_tr_ids_rejects_extension_outside_default():
    # ka10086 was an *earlier draft* allow-list entry; it is NOT in
    # the current DEFAULT, so config cannot reintroduce it.
    with pytest.raises(KiwoomForbiddenEndpointError):
        _resolve_allowed_tr_ids(["ka10099", "ka10086"])


def test_every_well_known_forbidden_tr_id_is_rejected():
    """Behavioural assertion: each well-known forbidden TR id raises."""
    for tr in WELL_KNOWN_FORBIDDEN_TR_IDS:
        with pytest.raises(KiwoomForbiddenEndpointError):
            _resolve_allowed_tr_ids([tr])


# ---------------------------------------------------------------------
# 12. Config-path-inside-repo rejection.
# ---------------------------------------------------------------------


def test_load_config_rejects_path_inside_repo():
    in_repo = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "test_inrepo_kiwoom.json"
    in_repo.write_text(json.dumps({
        "rest_base_url": "https://example.invalid",
        "appkey":        "TEST_APPKEY_NOT_REAL",
        "appsecret":     "TEST_APPSECRET_NOT_REAL",
    }), encoding="utf-8")
    try:
        with pytest.raises(KiwoomConfigPathInRepoError):
            load_config(in_repo, repo_root=REPO_ROOT)
    finally:
        in_repo.unlink(missing_ok=True)


def test_cli_kiwoom_collect_refuses_config_inside_repo(tmp_path, monkeypatch):
    in_repo = REPO_ROOT / "stock_research" / "pbkr_v4_screening_builder" / "test_inrepo_kiwoom.json"
    in_repo.write_text(json.dumps({
        "rest_base_url": "https://example.invalid",
        "appkey":        "TEST_APPKEY_NOT_REAL",
        "appsecret":     "TEST_APPSECRET_NOT_REAL",
    }), encoding="utf-8")
    monkeypatch.setenv("KIWOOM_REST_CONFIG", str(in_repo))
    try:
        args = argparse.Namespace(
            date="2026-05-06", config=None, output_dir=str(tmp_path),
        )
        rc = collector_cli_main(args, REPO_ROOT)
        assert rc == 2
    finally:
        in_repo.unlink(missing_ok=True)


# ---------------------------------------------------------------------
# 13. Official-shape response normalization.
# ---------------------------------------------------------------------


def test_normalize_ka10081_response_official_shape():
    raw = {
        "stk_dt_pole_chart_qry": [
            # Reverse-chrono in the wire response — normalizer must sort ascending.
            {"dt": "20260506", "cur_prc": "+65800", "open_pric": "65500",
             "high_pric": "+65900", "low_pric": "-65300",
             "trde_qty": "1234567", "trde_prica": "812345600000"},
            {"dt": "20260505", "cur_prc": "-65500", "open_pric": "65800",
             "high_pric": "65900", "low_pric": "65200",
             "trde_qty": "987654", "trde_prica": "647100000000"},
        ]
    }
    rows = normalize_ka10081_response(raw)
    assert len(rows) == 2
    # ascending by date
    assert rows[0]["date"] == "20260505"
    assert rows[1]["date"] == "20260506"
    # +/- prefix is direction, not sign — close is abs-numeric
    assert rows[0]["close"] == 65500.0
    assert rows[1]["close"] == 65800.0
    assert rows[1]["high"] == 65900.0  # "+65900" -> 65900
    assert rows[1]["low"]  == 65300.0  # "-65300" -> 65300
    assert rows[1]["volume"] == 1234567.0
    assert rows[1]["trading_value"] == 812345600000.0


def test_normalize_ka10081_response_handles_thousand_separators_and_empty():
    rows = normalize_ka10081_response({
        "stk_dt_pole_chart_qry": [
            {"dt": "20260506", "cur_prc": "1,234.5", "open_pric": "",
             "high_pric": None, "low_pric": "+1234.5",
             "trde_qty": "10,000", "trde_prica": "12,345,000"},
        ]
    })
    assert rows[0]["close"] == 1234.5
    assert rows[0]["open"] is None
    assert rows[0]["high"] is None
    assert rows[0]["low"] == 1234.5
    assert rows[0]["volume"] == 10000.0
    assert rows[0]["trading_value"] == 12345000.0


def test_normalize_ka10060_response_official_shape():
    raw = {
        "stk_invsr_orgn_chart": [
            {"dt": "20260506",
             "ind_invsr":   "-1712493409",
             "frgnr_invsr": "+2923859607",
             "orgn":        "+389981923",
             "fnnc_invt":   "-883511469"},
            {"dt": "20260505",
             "ind_invsr":   "295759856",
             "frgnr_invsr": "683446959",
             "orgn":        "-1667392329",
             "fnnc_invt":   "-647197118"},
        ]
    }
    rows = normalize_ka10060_response(raw)
    assert [r["date"] for r in rows] == ["20260505", "20260506"]
    # Flow signs are preserved (net buy/sell).
    assert rows[1]["investor_flow"]              == -1712493409.0
    assert rows[1]["foreigner_flow"]             ==  2923859607.0
    assert rows[1]["institution_flow"]           ==   389981923.0
    assert rows[1]["financial_investment_flow"]  ==  -883511469.0


def test_normalize_ka10099_response_official_shape():
    raw = {
        "list": [
            {"code": "005930", "name": "삼성전자", "marketCode": "0",
             "marketName": "KOSPI", "auditInfo": "정상",
             "state": "정상", "orderWarning": "정상"},
            # Admin issue — must surface admin_issue=True
            {"code": "111111", "name": "관리주식 Synthetic", "marketCode": "10",
             "marketName": "KOSDAQ", "auditInfo": "관리종목",
             "state": "관리종목", "orderWarning": "투자유의"},
            # Trading halt
            {"code": "222222", "name": "정지주식 Synthetic", "marketCode": "0",
             "marketName": "KOSPI", "auditInfo": "정상",
             "state": "거래정지", "orderWarning": ""},
            # ETF — sec_type=etf via name prefix
            {"code": "333333", "name": "KODEX Synthetic", "marketCode": "0",
             "marketName": "KOSPI", "auditInfo": "정상",
             "state": "정상", "orderWarning": ""},
            # Preferred — sec_type=preferred via name suffix
            {"code": "444444", "name": "Synthetic우", "marketCode": "0",
             "marketName": "KOSPI", "auditInfo": "정상",
             "state": "정상", "orderWarning": ""},
            # Investment-attention raised
            {"code": "555555", "name": "Synthetic Bravo", "marketCode": "10",
             "marketName": "KOSDAQ", "auditInfo": "투자주의환기",
             "state": "정상", "orderWarning": "투자주의"},
        ]
    }
    rows = normalize_ka10099_response(raw)
    by_code = {r["ticker"]: r for r in rows}

    assert by_code["005930"]["sec_type"] == "common"
    assert by_code["005930"]["market"] == "KOSPI"
    assert by_code["005930"]["admin_issue"] is False
    assert by_code["005930"]["trading_halt"] is False

    assert by_code["111111"]["admin_issue"] is True
    assert by_code["111111"]["market"] == "KOSDAQ"

    assert by_code["222222"]["trading_halt"] is True

    assert by_code["333333"]["sec_type"] == "etf"
    assert by_code["444444"]["sec_type"] == "preferred"

    assert by_code["555555"]["attention_issue"] is True


# ---------------------------------------------------------------------
# 14. Insufficient close-history is reported as 'insufficient_history'.
# ---------------------------------------------------------------------


def test_collector_marks_short_history_as_insufficient_history(tmp_path):
    universe, ohlcv, flows = _build_synthetic_universe()
    # Truncate one ticker to <252 closes — still a real ticker, just
    # short history.
    ohlcv["BBB.KQ"] = ohlcv["BBB.KQ"][:100]
    flows["BBB.KQ"] = flows["BBB.KQ"][:100]
    client = _mock_client_for(universe, ohlcv, flows)

    out = tmp_path / "out"
    result = collect_today_universe(
        asof_date="2026-05-06",
        config=_config_dict(tmp_path / "kiwoom_config.json"),
        client=client,
        output_dir=out,
        repo_root=REPO_ROOT,
    )
    # BBB.KQ should be in rejected with the insufficient_history reason.
    assert "BBB.KQ" in result.rejected_tickers
    assert result.rejected_tickers["BBB.KQ"].startswith("insufficient_history:")
    # Other 4 common-share tickers still produce feature rows.
    assert result.feature_rows == 4


# ---------------------------------------------------------------------
# 15. Run-level atomic publish: a failure mid-publish leaves previous
#     _latest files untouched.
# ---------------------------------------------------------------------


def test_run_level_atomic_publish_keeps_previous_latest_on_tmp_failure(
    tmp_path, monkeypatch,
):
    out = tmp_path / "out"
    out.mkdir(parents=True)
    prev_features = out / KIWOOM_FEATURES_FILENAME
    prev_universe = out / KIWOOM_UNIVERSE_FILENAME
    prev_report   = out / KIWOOM_COLLECTION_REPORT_FILENAME
    prev_features.write_text('{"sentinel": "prev_features"}', encoding="utf-8")
    prev_universe.write_text('{"sentinel": "prev_universe"}', encoding="utf-8")
    prev_report.write_text('{"sentinel": "prev_report"}',   encoding="utf-8")

    universe, ohlcv, flows = _build_synthetic_universe()
    client = _mock_client_for(universe, ohlcv, flows)

    # Make the SECOND tmp write (the universe payload) fail.  Phase 1
    # of the atomic publish must clean up the first tmp and leave the
    # previous _latest files untouched.
    real_write_text = Path.write_text
    fail_after = {"count": 0}

    def flaky(self, data, *args, **kwargs):
        fail_after["count"] += 1
        if KIWOOM_UNIVERSE_FILENAME in self.name:
            raise OSError("simulated tmp write failure")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.write_text", flaky)

    with pytest.raises(OSError):
        collect_today_universe(
            asof_date="2026-05-06",
            config=_config_dict(tmp_path / "kiwoom_config.json"),
            client=client,
            output_dir=out,
            repo_root=REPO_ROOT,
        )

    # Previous _latest files survive untouched.
    assert json.loads(prev_features.read_text())["sentinel"] == "prev_features"
    assert json.loads(prev_universe.read_text())["sentinel"] == "prev_universe"
    assert json.loads(prev_report.read_text())["sentinel"]   == "prev_report"
    # No leftover .tmp files in the directory.
    leftover = [p.name for p in out.iterdir() if p.name.endswith(".tmp")]
    assert leftover == [], f"unexpected leftover tmp files: {leftover}"
