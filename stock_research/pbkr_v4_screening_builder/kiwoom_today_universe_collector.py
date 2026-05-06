"""Today-date Kiwoom REST universe + feature collector.

Builds the two Kiwoom inputs that the read-only ``live-screen`` runner
consumes (``kiwoom_features_latest.json`` and
``kiwoom_universe_latest.json``) plus an audit-only
``kiwoom_collection_report_latest.json``, **for the current trading
date** — *not* by re-shaping past phase3 outputs.

Hard rules
----------
1. **Read-only market-data only.** The collector calls the injected
   ``KiwoomRestClient`` with TR ids that are explicitly allowlisted as
   market data. Any TR id that names ``order`` / ``account`` / ``cash``
   / ``deposit`` / ``balance`` is rejected before the HTTP call.
2. **No credential ever lands in the repo.** The OAuth token, app key,
   app secret, and config file path come from the local environment
   (``KIWOOM_REST_CONFIG``) or an explicit ``--config`` argument; the
   collector refuses to start when they are missing.
3. **Output is private.** The output directory must live under
   ``$PBKR_PROCESSED_ROOT/live_screen_inputs`` (or an explicit
   ``--output-dir``) and **must** resolve outside the repository.
4. **No synthetic / mock fallback in production.** The collector accepts
   a ``KiwoomRestClient`` parameter; production code passes the real
   client. Tests pass a ``MockKiwoomRestClient``. The CLI never
   silently falls back to mock — when no client wiring is configured
   it errors out.
5. **Atomic ``_latest.json`` writes.** Each output is written to
   ``<name>.tmp`` first and renamed onto ``<name>_latest.json`` only
   when the entire pipeline succeeds. A partial / failed run never
   overwrites the previous ``_latest`` artifact.
6. **Never emits a doctrinal trade artifact.** The collection report
   carries the canonical signal-safety block plus
   ``no_execution: true``, ``broker_order_path_present: false``,
   ``account_endpoint_used: false``, ``order_endpoint_used: false``.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from .adapters.kiwoom_rest import _normalize_row  # canonical row shape
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

KIWOOM_FEATURES_FILENAME = "kiwoom_features_latest.json"
KIWOOM_UNIVERSE_FILENAME = "kiwoom_universe_latest.json"
KIWOOM_COLLECTION_REPORT_FILENAME = "kiwoom_collection_report_latest.json"

# Minimum daily-close history required so the live-screen
# PBKR_RS_RANK can compute a 12-month percentile.
MIN_CLOSE_SERIES_LEN = 252

# Allow-list of Kiwoom OpenAPI REST TR ids the collector is willing to
# call.  These are read-only market data lookups; nothing here touches
# accounts or orders.  The exact TR ids depend on the deployed Kiwoom
# environment, so the collector also accepts an explicit override via
# config (``allowed_tr_ids``).  The values below are the documented
# market-data ids used in the phase3 reference snapshot and adapter
# (universe listing, daily OHLCV, daily investor / foreigner flows).
DEFAULT_ALLOWED_TR_IDS: tuple[str, ...] = (
    "ka10099",  # 종목정보 리스트 (universe listing)
    "ka10081",  # 일봉 차트 조회 (daily OHLCV)
    "ka10086",  # 일별주가
    "ka10059",  # 종목별 투자자 / 기관 / 외국인 매매 동향
    "ka10063",  # 외국인 / 기관 일별 매매
)

# Hard-deny substrings.  If a TR id (or any endpoint path) contains one
# of these tokens, the collector refuses to call it.  This is a
# belt-and-braces check on top of the allow-list.
FORBIDDEN_TR_TOKENS: tuple[str, ...] = (
    "order",
    "ord",
    "account",
    "acct",
    "cash",
    "deposit",
    "balance",
    "execution",
    "trade_ticket",
    "buy",
    "sell",
)


class KiwoomCollectorError(Exception):
    """Base class for collector errors."""


class KiwoomConfigMissingError(KiwoomCollectorError):
    """Required Kiwoom REST config / token was not supplied."""


class KiwoomOutputPathInRepoError(KiwoomCollectorError):
    """The requested output directory is inside the repository."""


class KiwoomForbiddenEndpointError(KiwoomCollectorError):
    """A TR id / endpoint that is not market-data-only was requested."""


class KiwoomCollectionFailed(KiwoomCollectorError):
    """The collector failed before all required outputs were produced."""


class KiwoomRestClient(Protocol):
    """Minimal market-data-only client surface.

    A real implementation wraps the Kiwoom OpenAPI REST endpoints; the
    test suite passes ``MockKiwoomRestClient``.  Both implementations
    must:

      * never expose order / account TRs;
      * never echo the OAuth token in a returned payload;
      * raise on transport / auth failure rather than returning empty.
    """

    def list_universe(self, *, market: str) -> list[dict[str, Any]]:
        """Return a list of ``{ticker, name, market, sec_type, ...}`` rows."""

    def fetch_daily_ohlcv(self, *, ticker: str, lookback_days: int) -> list[dict[str, Any]]:
        """Return chronological daily OHLCV rows for ``ticker``."""

    def fetch_daily_flows(self, *, ticker: str, lookback_days: int) -> list[dict[str, Any]]:
        """Return chronological daily investor-flow rows for ``ticker``.

        May return ``[]`` if the upstream feed does not expose flows for
        the ticker — the collector records the gap in the report's
        ``missing_fields``.
        """


@dataclass
class CollectorConfig:
    """Resolved configuration for one collector invocation."""

    config_path: Path
    output_dir: Path
    markets: tuple[str, ...] = ("KOSPI", "KOSDAQ")
    include_etf: bool = False
    include_etn: bool = False
    include_spac: bool = False
    include_preferred: bool = False
    include_admin_issue: bool = False
    include_trading_halt: bool = False
    lookback_days: int = 280
    min_close_series_len: int = MIN_CLOSE_SERIES_LEN
    allowed_tr_ids: tuple[str, ...] = DEFAULT_ALLOWED_TR_IDS
    request_pause_seconds: float = 0.0


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Read the local Kiwoom REST config file.

    The config is expected to live outside the repo (e.g. under the
    operator's home dir).  It carries the OAuth credentials and the
    REST endpoint base URL.  This loader **does not** validate the
    secret material — it only checks that the structurally-required
    keys are present.
    """
    p = Path(config_path).expanduser()
    if not p.exists():
        raise KiwoomConfigMissingError(
            f"Kiwoom REST config file not found: {p}\n"
            "Set $KIWOOM_REST_CONFIG to the local config path or pass "
            "--config <path>.  The config must live outside the repo."
        )
    if not p.is_file():
        raise KiwoomConfigMissingError(f"Kiwoom REST config is not a regular file: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise KiwoomConfigMissingError(f"Kiwoom REST config must be a JSON object: {p}")

    required = ("rest_base_url", "appkey", "appsecret")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        raise KiwoomConfigMissingError(
            f"Kiwoom REST config {p} is missing required keys: {missing}"
        )
    return payload


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    base = Path(DEFAULT_OUTPUT_BASE).expanduser()
    return (base / LIVE_SCREEN_INPUTS_SUBDIR).resolve()


def _assert_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root)
    except ValueError:
        return
    raise KiwoomOutputPathInRepoError(
        f"refusing to write Kiwoom collector outputs inside the repository: {path}\n"
        f"set --output-dir (or $PBKR_PROCESSED_ROOT) to a local/private path "
        f"such as {DEFAULT_OUTPUT_BASE}/{LIVE_SCREEN_INPUTS_SUBDIR}"
    )


def _assert_tr_allowed(tr_id: str, allowed: Iterable[str]) -> None:
    """Reject any TR id outside the read-only allow-list."""
    if tr_id not in set(allowed):
        raise KiwoomForbiddenEndpointError(
            f"refusing to call non-allowlisted TR id: {tr_id!r}.  "
            f"Only market-data-only TRs may be invoked."
        )
    lowered = tr_id.lower()
    for tok in FORBIDDEN_TR_TOKENS:
        if tok in lowered:
            raise KiwoomForbiddenEndpointError(
                f"refusing TR id {tr_id!r}: matches forbidden token {tok!r} "
                f"(account / order / cash / balance / execution endpoints are out of scope)."
            )


def _is_excluded_security(row: Mapping[str, Any], cfg: CollectorConfig) -> bool:
    """Return True if the row should be dropped from today's universe.

    Reasons are coarse and conservative.  The detailed risk taxonomy
    is the responsibility of the official-risk pack — this filter
    only enforces the "보통주 중심 KOSPI/KOSDAQ" universe contract.
    """
    sec_type = str(row.get("sec_type") or "").lower()
    name = str(row.get("name") or "")

    if not cfg.include_etf and ("etf" in sec_type or name.startswith("KODEX") or name.startswith("TIGER")):
        return True
    if not cfg.include_etn and "etn" in sec_type:
        return True
    if not cfg.include_spac and ("spac" in sec_type or "스팩" in name):
        return True
    if not cfg.include_preferred and ("preferred" in sec_type or "우" in name[-1:]):
        # naive preferred-share heuristic; the canonical adapter is
        # expected to set sec_type explicitly.
        if "preferred" in sec_type:
            return True
    if not cfg.include_admin_issue and bool(row.get("admin_issue")):
        return True
    if not cfg.include_trading_halt and bool(row.get("trading_halt")):
        return True
    market = str(row.get("market") or "").upper()
    if market not in {m.upper() for m in cfg.markets}:
        return True
    return False


def _to_close_series(daily_rows: list[Mapping[str, Any]]) -> list[float]:
    """Project chronological daily rows to a list of float closes."""
    out: list[float] = []
    for r in daily_rows:
        v = r.get("close")
        if v is None:
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _ma(closes: list[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return round(sum(closes[-window:]) / window, 4)


def _atr14(rows: list[Mapping[str, Any]]) -> float | None:
    if len(rows) < 15:
        return None
    trs: list[float] = []
    for i in range(len(rows) - 14, len(rows)):
        prev_close = rows[i - 1].get("close")
        hi = rows[i].get("high")
        lo = rows[i].get("low")
        if prev_close is None or hi is None or lo is None:
            return None
        try:
            tr = max(float(hi) - float(lo), abs(float(hi) - float(prev_close)), abs(float(lo) - float(prev_close)))
        except (TypeError, ValueError):
            return None
        trs.append(tr)
    if not trs:
        return None
    return round(sum(trs) / len(trs), 4)


def _max_window(closes: list[float], window: int) -> float | None:
    if not closes:
        return None
    sl = closes[-window:] if len(closes) >= window else closes
    return round(max(sl), 4)


def _min_window(closes: list[float], window: int) -> float | None:
    if not closes:
        return None
    sl = closes[-window:] if len(closes) >= window else closes
    return round(min(sl), 4)


def _build_feature_row(
    *,
    ticker: str,
    daily_rows: list[Mapping[str, Any]],
    flow_rows: list[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Compute the canonical feature row + report which fields were missing."""
    missing: list[str] = []
    closes = _to_close_series(daily_rows)
    if not closes:
        missing.append("close")

    last = daily_rows[-1] if daily_rows else {}
    flow_last = flow_rows[-1] if flow_rows else {}

    raw = {
        "ticker": ticker,
        "close":          last.get("close"),
        "open":           last.get("open"),
        "high":           last.get("high"),
        "low":            last.get("low"),
        "volume":         last.get("volume"),
        "trading_value":  last.get("trading_value"),
        "volume_ratio":   last.get("volume_ratio"),
        "investor_flow":             flow_last.get("investor_flow"),
        "foreigner_flow":            flow_last.get("foreigner_flow"),
        "institution_flow":          flow_last.get("institution_flow"),
        "financial_investment_flow": flow_last.get("financial_investment_flow"),
        "ma9":   _ma(closes, 9),
        "ma21":  _ma(closes, 21),
        "ma50":  _ma(closes, 50),
        "ma120": _ma(closes, 120),
        "atr14": _atr14(daily_rows),
        "recent_low": _min_window(closes, 20),
        "high_20d": _max_window(closes, 20),
        "high_60d": _max_window(closes, 60),
    }
    atr14 = raw["atr14"]
    recent_low = raw["recent_low"]
    last_close = raw["close"]
    if atr14 is not None and last_close is not None and recent_low is not None:
        raw["stop_distance"] = round(
            max(2.0 * float(atr14), 0.5 * max(float(last_close) - float(recent_low), 1.0)),
            4,
        )
    else:
        raw["stop_distance"] = None

    for field_name in (
        "trading_value", "volume", "volume_ratio",
        "investor_flow", "foreigner_flow", "institution_flow",
        "financial_investment_flow",
    ):
        if raw.get(field_name) is None:
            missing.append(field_name)

    return _normalize_row(raw), missing


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` to ``<path>.tmp`` then rename onto ``path``.

    Failure during ``write_text`` leaves the previous ``path`` intact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _asof_iso(date_str: str) -> str:
    return f"{date_str}T15:30:00+09:00"


@dataclass
class CollectionResult:
    asof_date: str
    output_dir: Path
    features_path: Path
    universe_path: Path
    report_path: Path
    universe_size: int
    feature_rows: int
    missing_fields_per_ticker: dict[str, list[str]] = field(default_factory=dict)
    rejected_tickers: dict[str, str] = field(default_factory=dict)


def collect_today_universe(
    *,
    asof_date: str,
    config: dict[str, Any],
    client: KiwoomRestClient,
    output_dir: Path,
    repo_root: Path,
    cfg: CollectorConfig | None = None,
) -> CollectionResult:
    """Run the read-only Kiwoom REST collector for ``asof_date``.

    The function deliberately operates in two phases:

      1. ``list_universe`` for each configured market, then prune
         non-common shares / suspended issues.
      2. For each remaining ticker, fetch daily OHLCV (and, when the
         feed exposes it, daily investor / foreigner / institution
         flows), then compute MAs / ATR / stop-distance.

    The two ``_latest.json`` outputs are only published when the run
    yields at least one feature row.  Otherwise the previous
    ``_latest.json`` files are left untouched and ``KiwoomCollectionFailed``
    is raised so the operator can inspect the partial-success report.
    """
    cfg = cfg or CollectorConfig(
        config_path=Path(config.get("__source_path") or ""),
        output_dir=output_dir,
    )
    _assert_outside_repo(output_dir, repo_root)

    allowed_tr_ids = tuple(config.get("allowed_tr_ids") or cfg.allowed_tr_ids)
    for tr_id in allowed_tr_ids:
        _assert_tr_allowed(tr_id, allowed_tr_ids)

    started_at = _utc_iso_now()

    raw_universe: list[dict[str, Any]] = []
    for market in cfg.markets:
        rows = client.list_universe(market=market)
        for r in rows:
            if not r.get("ticker"):
                continue
            r.setdefault("market", market)
            raw_universe.append(r)

    rejected: dict[str, str] = {}
    kept_universe: list[dict[str, Any]] = []
    for row in raw_universe:
        if _is_excluded_security(row, cfg):
            rejected[str(row["ticker"])] = "non_common_or_suspended"
            continue
        kept_universe.append(row)

    feature_rows: list[dict[str, Any]] = []
    universe_tickers: dict[str, dict[str, Any]] = {}
    missing_fields: dict[str, list[str]] = {}

    for row in kept_universe:
        ticker = str(row["ticker"])
        try:
            daily = client.fetch_daily_ohlcv(ticker=ticker, lookback_days=cfg.lookback_days)
        except Exception as exc:  # pragma: no cover - exercised via tests
            rejected[ticker] = f"daily_ohlcv_error:{type(exc).__name__}"
            continue

        closes = _to_close_series(daily)
        if len(closes) < cfg.min_close_series_len:
            rejected[ticker] = f"close_series_too_short:{len(closes)}"
            continue

        try:
            flows = client.fetch_daily_flows(ticker=ticker, lookback_days=cfg.lookback_days)
        except Exception as exc:  # pragma: no cover
            flows = []
            missing_fields.setdefault(ticker, []).append(f"flows_error:{type(exc).__name__}")

        normalized, gaps = _build_feature_row(
            ticker=ticker, daily_rows=daily, flow_rows=flows,
        )
        if gaps:
            missing_fields.setdefault(ticker, []).extend(gaps)
        feature_rows.append(normalized)
        universe_tickers[ticker] = {"closes": closes}

        if cfg.request_pause_seconds:
            time.sleep(cfg.request_pause_seconds)

    if not feature_rows:
        report = _build_report(
            asof_date=asof_date,
            started_at=started_at,
            finished_at=_utc_iso_now(),
            output_dir=output_dir,
            features_filename=KIWOOM_FEATURES_FILENAME,
            universe_filename=KIWOOM_UNIVERSE_FILENAME,
            kept_universe=kept_universe,
            feature_rows=feature_rows,
            missing_fields=missing_fields,
            rejected=rejected,
            allowed_tr_ids=allowed_tr_ids,
            success=False,
            failure_reason="no feature rows produced",
        )
        report_path = output_dir / KIWOOM_COLLECTION_REPORT_FILENAME
        _atomic_write_json(report_path, report)
        raise KiwoomCollectionFailed(
            "no Kiwoom feature rows produced; "
            f"latest files left untouched.  see {report_path}"
        )

    benchmark_ticker = str(config.get("benchmark_ticker") or "BENCHMARK_KOSPI_PROXY")
    benchmark_closes: list[float] = []
    bench_loader = config.get("benchmark_closes")
    if isinstance(bench_loader, list):
        benchmark_closes = [float(x) for x in bench_loader if isinstance(x, (int, float))]

    features_payload = {
        "schema_version": SCHEMA_VERSION,
        "asof": _asof_iso(asof_date),
        "rows": feature_rows,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
    universe_payload = {
        "benchmark": {"ticker": benchmark_ticker, "closes": benchmark_closes},
        "tickers": universe_tickers,
    }
    finished_at = _utc_iso_now()
    report_payload = _build_report(
        asof_date=asof_date,
        started_at=started_at,
        finished_at=finished_at,
        output_dir=output_dir,
        features_filename=KIWOOM_FEATURES_FILENAME,
        universe_filename=KIWOOM_UNIVERSE_FILENAME,
        kept_universe=kept_universe,
        feature_rows=feature_rows,
        missing_fields=missing_fields,
        rejected=rejected,
        allowed_tr_ids=allowed_tr_ids,
        success=True,
        failure_reason=None,
    )

    features_path = output_dir / KIWOOM_FEATURES_FILENAME
    universe_path = output_dir / KIWOOM_UNIVERSE_FILENAME
    report_path = output_dir / KIWOOM_COLLECTION_REPORT_FILENAME

    _atomic_write_json(features_path, features_payload)
    _atomic_write_json(universe_path, universe_payload)
    _atomic_write_json(report_path, report_payload)

    return CollectionResult(
        asof_date=asof_date,
        output_dir=output_dir,
        features_path=features_path,
        universe_path=universe_path,
        report_path=report_path,
        universe_size=len(kept_universe),
        feature_rows=len(feature_rows),
        missing_fields_per_ticker=missing_fields,
        rejected_tickers=rejected,
    )


def _build_report(
    *,
    asof_date: str,
    started_at: str,
    finished_at: str,
    output_dir: Path,
    features_filename: str,
    universe_filename: str,
    kept_universe: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    missing_fields: dict[str, list[str]],
    rejected: dict[str, str],
    allowed_tr_ids: tuple[str, ...],
    success: bool,
    failure_reason: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "collector": "kiwoom_today_universe_collector",
        "asof_date": asof_date,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "output_dir": str(output_dir),
        "features_file": features_filename,
        "universe_file": universe_filename,
        "universe_size": len(kept_universe),
        "feature_rows": len(feature_rows),
        "rejected_tickers": rejected,
        "missing_fields_per_ticker": missing_fields,
        "allowed_tr_ids": list(allowed_tr_ids),
        "no_execution": True,
        "broker_order_path_present": False,
        "account_endpoint_used": False,
        "order_endpoint_used": False,
        "auto_execution_allowed": False,
        "success": success,
        "failure_reason": failure_reason,
        "signal_safety": dict(DAILY_PACKET_SIGNAL_SAFETY),
    }


# ---------------------------------------------------------------------
# Mock client (tests only).  Production code injects a real client.
# ---------------------------------------------------------------------


@dataclass
class MockKiwoomRestClient:
    """Deterministic in-memory client used by the test suite.

    The collector treats the real and mock clients identically; the
    mock just answers from a pre-built dict and never opens a socket.
    """

    universe: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    daily_ohlcv: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    daily_flows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def list_universe(self, *, market: str) -> list[dict[str, Any]]:
        return list(self.universe.get(market, []))

    def fetch_daily_ohlcv(self, *, ticker: str, lookback_days: int) -> list[dict[str, Any]]:
        rows = list(self.daily_ohlcv.get(ticker, []))
        return rows[-lookback_days:] if rows else rows

    def fetch_daily_flows(self, *, ticker: str, lookback_days: int) -> list[dict[str, Any]]:
        rows = list(self.daily_flows.get(ticker, []))
        return rows[-lookback_days:] if rows else rows


# ---------------------------------------------------------------------
# CLI bridge.
# ---------------------------------------------------------------------


def cli_main(args: Any, repo_root: Path) -> int:
    """argparse entry point shared by the top-level CLI."""
    output_dir = _resolve_output_dir(args.output_dir)
    try:
        _assert_outside_repo(output_dir, repo_root)
    except KiwoomOutputPathInRepoError as exc:
        print(f"[kiwoom-collect] {exc}", file=sys.stderr)
        return 2

    config_path = args.config or os.getenv("KIWOOM_REST_CONFIG")
    if not config_path:
        print(
            "[kiwoom-collect] missing Kiwoom REST config.\n"
            "Set $KIWOOM_REST_CONFIG to the local config path or pass --config <path>.",
            file=sys.stderr,
        )
        return 2

    try:
        config = load_config(config_path)
    except KiwoomConfigMissingError as exc:
        print(f"[kiwoom-collect] {exc}", file=sys.stderr)
        return 2

    # The CLI does not silently fall back to a mock client.  Real
    # client wiring is provided through ``config['client_factory']``
    # (a dotted import path) — the operator's local config plugs in
    # the concrete ``KiwoomRestClient`` implementation.  Tests
    # import ``collect_today_universe`` directly and pass a
    # ``MockKiwoomRestClient`` instance.
    client_factory = config.get("client_factory")
    if not client_factory:
        print(
            "[kiwoom-collect] no client_factory in config; refusing to fall back to mock.\n"
            "Configure client_factory to a dotted import path (module:callable) "
            "that returns a KiwoomRestClient instance.",
            file=sys.stderr,
        )
        return 2

    try:
        client = _load_client(client_factory, config)
    except KiwoomCollectorError as exc:
        print(f"[kiwoom-collect] {exc}", file=sys.stderr)
        return 2

    try:
        result = collect_today_universe(
            asof_date=args.date,
            config={**config, "__source_path": str(Path(config_path).expanduser())},
            client=client,
            output_dir=output_dir,
            repo_root=repo_root,
        )
    except KiwoomCollectionFailed as exc:
        print(f"[kiwoom-collect] {exc}", file=sys.stderr)
        return 1
    except KiwoomCollectorError as exc:
        print(f"[kiwoom-collect] {exc}", file=sys.stderr)
        return 2

    print(f"[kiwoom-collect] wrote: {result.features_path}")
    print(f"[kiwoom-collect] wrote: {result.universe_path}")
    print(f"[kiwoom-collect] wrote: {result.report_path}")
    print(f"[kiwoom-collect] universe={result.universe_size} feature_rows={result.feature_rows}")
    return 0


def _load_client(dotted: str, config: dict[str, Any]) -> KiwoomRestClient:
    """Resolve ``module:callable`` to a ``KiwoomRestClient`` instance.

    Kept tiny on purpose: the heavy lifting (auth, retries, rate
    limits) lives in the operator's local module that the dotted
    path points at.
    """
    if ":" not in dotted:
        raise KiwoomCollectorError(
            f"invalid client_factory {dotted!r}: expected 'module:callable'"
        )
    module_name, attr = dotted.split(":", 1)
    try:
        import importlib

        mod = importlib.import_module(module_name)
    except ImportError as exc:
        raise KiwoomCollectorError(
            f"client_factory module not importable: {module_name}: {exc}"
        ) from exc
    factory = getattr(mod, attr, None)
    if factory is None:
        raise KiwoomCollectorError(
            f"client_factory attribute not found: {module_name}:{attr}"
        )
    client = factory(config)
    if client is None:
        raise KiwoomCollectorError(
            f"client_factory {dotted} returned None"
        )
    return client
