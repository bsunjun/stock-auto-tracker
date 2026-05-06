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
# call.  These are the **documented** read-only market-data TRs;
# nothing here touches accounts or orders.  The list is **hard-coded**
# at the module level — adding a TR id requires a code PR.  The
# operator's local config may *narrow* this set (subset-only), but it
# may **never** extend it.
#
# Documented TRs (per the official Kiwoom REST API docs):
#   ka10099 — 종목정보 리스트          (universe listing) → /api/dostk/stkinfo
#   ka10081 — 주식일봉차트조회요청     (daily OHLCV)      → /api/dostk/chart
#   ka10060 — 종목별투자자기관별차트요청 (supply / flows)  → /api/dostk/chart
DEFAULT_ALLOWED_TR_IDS: tuple[str, ...] = (
    "ka10099",
    "ka10081",
    "ka10060",
)

# Well-known account / order TR ids, listed explicitly so the error
# message is informative when an operator's config tries to include
# one.  The subset-of-DEFAULT enforcement plus the substring guard
# below already reject anything outside DEFAULT_ALLOWED_TR_IDS — this
# constant exists for documentation and clearer test failures.
#
#   ka00001 — 계좌번호조회           (account list)
#   kt10000 — 주식 매수주문
#   kt10001 — 주식 매도주문
#   kt10002 — 주식 정정주문
#   kt10003 — 주식 취소주문
#   kt00011 — 주문가능수량
WELL_KNOWN_FORBIDDEN_TR_IDS: tuple[str, ...] = (
    "ka00001",
    "kt10000",
    "kt10001",
    "kt10002",
    "kt10003",
    "kt00011",
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


class KiwoomConfigPathInRepoError(KiwoomCollectorError):
    """The Kiwoom REST config file is located inside the repository."""


class KiwoomOutputPathInRepoError(KiwoomCollectorError):
    """The requested output directory is inside the repository."""


class KiwoomForbiddenEndpointError(KiwoomCollectorError):
    """A TR id / endpoint that is not market-data-only was requested."""


class KiwoomCollectionFailed(KiwoomCollectorError):
    """The collector failed before all required outputs were produced."""


class KiwoomRestClient(Protocol):
    """Minimal market-data-only client surface.

    A real implementation wraps the Kiwoom OpenAPI REST endpoints
    (ka10099 / ka10081 / ka10060); the test suite passes
    ``MockKiwoomRestClient``.  Both implementations must:

      * never expose order / account TRs (kt10000-kt10003, ka00001,
        kt00011 …);
      * never echo the OAuth token (au10001 response) in a returned
        payload;
      * raise on transport / auth failure rather than returning empty.

    **Pagination contract.** The Kiwoom REST responses use the
    ``cont-yn`` and ``next-key`` response headers to signal that more
    rows are available.  The client wrapper is responsible for
    transparently following pagination: while the response header
    ``cont-yn == "Y"``, it must re-issue the same TR with the
    ``cont-yn: Y`` request header and the previous response's
    ``next-key`` set on the request, concatenating rows in the
    natural (chronological for chart TRs, listing-order for ka10099)
    order.  The collector consumes the **already aggregated** result
    and trusts the wrapper to have honoured pagination — there is
    no cont-yn affordance at this layer.

    The wrapper is also responsible for parsing the official response
    shapes; ``normalize_ka10081_response`` / ``normalize_ka10060_response``
    / ``normalize_ka10099_response`` are exposed in this module so
    the wrapper can stay thin.
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


def load_config(config_path: str | Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    """Read the local Kiwoom REST config file.

    The config is expected to live **outside** the repo (e.g. under
    the operator's home dir).  It carries the OAuth credentials and
    the REST endpoint base URL.  This loader **does not** validate
    the secret material — it only checks that the structurally
    required keys are present.

    When ``repo_root`` is supplied, the loader refuses to open a
    config that resolves *inside* the repo and raises
    ``KiwoomConfigPathInRepoError`` before any byte is read.
    """
    p = Path(config_path).expanduser()
    if repo_root is not None:
        _assert_config_outside_repo(p, repo_root)
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


def _resolve_allowed_tr_ids(config_allowlist: Iterable[str] | None) -> tuple[str, ...]:
    """Validate and return the effective TR allow-list.

    The base allow-list is hard-coded as ``DEFAULT_ALLOWED_TR_IDS``.
    The config may *narrow* this set (subset-only) but **never**
    extend it.  Any TR id outside ``DEFAULT_ALLOWED_TR_IDS`` raises
    ``KiwoomForbiddenEndpointError`` — and well-known account / order
    TR ids surface a more pointed error message.
    """
    if config_allowlist is None:
        return DEFAULT_ALLOWED_TR_IDS
    overrides = tuple(str(x).strip() for x in config_allowlist if str(x).strip())
    if not overrides:
        return DEFAULT_ALLOWED_TR_IDS

    extras = [t for t in overrides if t not in DEFAULT_ALLOWED_TR_IDS]
    if extras:
        well_known = [t for t in extras if t in WELL_KNOWN_FORBIDDEN_TR_IDS]
        if well_known:
            raise KiwoomForbiddenEndpointError(
                f"config allowed_tr_ids contains forbidden account / order TR ids: "
                f"{well_known}.  These endpoints are explicitly out of scope and "
                f"cannot be enabled via config."
            )
        raise KiwoomForbiddenEndpointError(
            f"config allowed_tr_ids tries to extend the hard-coded allow-list with "
            f"{extras!r}.  The collector pins DEFAULT_ALLOWED_TR_IDS = "
            f"{DEFAULT_ALLOWED_TR_IDS}; adding new TRs requires a code PR."
        )
    # belt-and-braces substring guard
    for tr_id in overrides:
        lowered = tr_id.lower()
        for tok in FORBIDDEN_TR_TOKENS:
            if tok in lowered:
                raise KiwoomForbiddenEndpointError(
                    f"refusing TR id {tr_id!r}: matches forbidden token {tok!r}."
                )
    return overrides


def _assert_config_outside_repo(path: Path, repo_root: Path) -> None:
    """Refuse to read a config file that lives inside the repository."""
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    raise KiwoomConfigPathInRepoError(
        f"refusing to read Kiwoom REST config from inside the repository: {path}\n"
        "place the config file under a private path (e.g. ~/.config/kiwoom_rest.json)."
    )


def _is_excluded_security(row: Mapping[str, Any], cfg: CollectorConfig) -> tuple[bool, str | None]:
    """Return ``(excluded, reason)`` for a normalized universe row.

    Reasons are coarse and conservative.  The detailed risk taxonomy
    is the responsibility of the official-risk pack — this filter
    only enforces the "보통주 중심 KOSPI/KOSDAQ" universe contract.
    """
    sec_type = str(row.get("sec_type") or "").lower()

    if not cfg.include_etf and sec_type == "etf":
        return True, "etf_excluded"
    if not cfg.include_etn and sec_type == "etn":
        return True, "etn_excluded"
    if not cfg.include_spac and sec_type == "spac":
        return True, "spac_excluded"
    if not cfg.include_preferred and sec_type == "preferred":
        return True, "preferred_excluded"
    if not cfg.include_admin_issue and bool(row.get("admin_issue")):
        return True, "admin_issue_excluded"
    if not cfg.include_trading_halt and bool(row.get("trading_halt")):
        return True, "trading_halt_excluded"
    market = str(row.get("market") or "").upper()
    if market not in {m.upper() for m in cfg.markets}:
        return True, f"market_not_in_scope:{market or 'UNKNOWN'}"
    return False, None


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


def _publish_atomic(triples: list[tuple[Path, dict[str, Any]]]) -> None:
    """Two-phase atomic publish for a run's _latest.json files.

    Phase 1: write each payload to ``<path>.tmp``.
    Phase 2: rename every ``.tmp`` onto its destination.

    If any Phase-1 write fails, every ``.tmp`` already created is
    unlinked and **no** destination is touched — the previous
    ``_latest.json`` files survive untouched.  Phase-2 renames are
    sequential; on most filesystems they are individually atomic, so
    a Phase-2 failure leaves at most a partial publish across the
    set, which the operator can detect by reading
    ``kiwoom_collection_report_latest.json`` (which is renamed last).
    """
    tmps: list[tuple[Path, Path]] = []
    try:
        for path, payload in triples:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmps.append((tmp, path))
    except Exception:
        for tmp, _ in tmps:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
        raise

    for tmp, path in tmps:
        os.replace(tmp, path)


# ---------------------------------------------------------------------
# Official Kiwoom REST response normalizers.
#
# These helpers convert raw JSON returned by the documented market-data
# TRs into the canonical row shapes the collector consumes.  They
# exist so the operator's local client wrapper can stay thin: it
# performs the HTTP call (with cont-yn / next-key pagination, see
# KiwoomRestClient docstring), forwards the JSON body to the
# corresponding ``normalize_*_response`` function, and returns the
# resulting list.
# ---------------------------------------------------------------------


def _abs_numeric(v: Any) -> float | None:
    """Parse a price field whose ``+/-`` prefix is a *direction* indicator.

    Kiwoom's daily-chart response uses ``cur_prc = "+65800"`` /
    ``"-65800"`` to signal up / down vs. the previous close — the
    actual price is always the absolute value of the digits.
    """
    if v is None:
        return None
    try:
        s = str(v).strip().replace(",", "")
    except Exception:
        return None
    if not s:
        return None
    try:
        return abs(float(s))
    except (TypeError, ValueError):
        return None


def _signed_numeric(v: Any) -> float | None:
    """Parse a numeric field whose sign is meaningful (volume, flows)."""
    if v is None:
        return None
    try:
        s = str(v).strip().replace(",", "")
    except Exception:
        return None
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def normalize_ka10081_response(payload: Any) -> list[dict[str, Any]]:
    """Normalize a ka10081 (주식일봉차트조회요청) response into OHLCV rows.

    Official response shape::

        {
          "stk_dt_pole_chart_qry": [
            {"dt": "20260506",
             "cur_prc":  "+65800",
             "open_pric": "65500",
             "high_pric": "+65900",
             "low_pric":  "-65300",
             "trde_qty":   "1234567",
             "trde_prica": "812345600000",
             ...},
            ...
          ]
        }

    Returned rows are sorted ascending by ``date`` so downstream
    moving-average / ATR helpers see chronological data.  Prices are
    abs-numeric (the +/- prefix is a direction indicator, not a sign
    on the price itself).
    """
    items = _extract_list(
        payload,
        keys=("stk_dt_pole_chart_qry", "output", "list"),
    )
    rows: list[dict[str, Any]] = []
    for r in items:
        if not isinstance(r, dict):
            continue
        rows.append({
            "date":           str(r.get("dt") or r.get("date") or "").strip(),
            "close":          _abs_numeric(r.get("cur_prc")  if "cur_prc"  in r else r.get("close")),
            "open":           _abs_numeric(r.get("open_pric") if "open_pric" in r else r.get("open")),
            "high":           _abs_numeric(r.get("high_pric") if "high_pric" in r else r.get("high")),
            "low":            _abs_numeric(r.get("low_pric")  if "low_pric"  in r else r.get("low")),
            "volume":         _signed_numeric(r.get("trde_qty")    if "trde_qty"    in r else r.get("volume")),
            "trading_value":  _signed_numeric(r.get("trde_prica") if "trde_prica" in r else r.get("trading_value")),
        })
    if rows and all(r.get("date") for r in rows):
        rows.sort(key=lambda r: r["date"])
    return rows


def normalize_ka10060_response(payload: Any) -> list[dict[str, Any]]:
    """Normalize a ka10060 (종목별투자자기관별차트요청) response into flow rows.

    Official response shape::

        {
          "stk_invsr_orgn_chart": [
            {"dt": "20260506",
             "ind_invsr":  "-1712493409",
             "frgnr_invsr": "+2923859607",
             "orgn":         "+389981923",
             "fnnc_invt":    "-883511469",
             ...},
            ...
          ]
        }

    Flow values keep their sign — a negative ``foreigner_flow`` is
    net selling.
    """
    items = _extract_list(
        payload,
        keys=("stk_invsr_orgn_chart", "output", "list"),
    )
    rows: list[dict[str, Any]] = []
    for r in items:
        if not isinstance(r, dict):
            continue
        rows.append({
            "date":                       str(r.get("dt") or r.get("date") or "").strip(),
            "investor_flow":              _signed_numeric(r.get("ind_invsr",   r.get("investor_flow"))),
            "foreigner_flow":             _signed_numeric(r.get("frgnr_invsr", r.get("foreigner_flow"))),
            "institution_flow":           _signed_numeric(r.get("orgn",        r.get("institution_flow"))),
            "financial_investment_flow":  _signed_numeric(r.get("fnnc_invt",   r.get("financial_investment_flow"))),
        })
    if rows and all(r.get("date") for r in rows):
        rows.sort(key=lambda r: r["date"])
    return rows


def normalize_ka10099_response(payload: Any) -> list[dict[str, Any]]:
    """Normalize a ka10099 (종목정보 리스트) response into universe rows.

    Per-row fields (per the official docs):
      * ``code``         → ``ticker``
      * ``name``         → ``name``
      * ``marketCode`` / ``marketName`` → ``market`` (KOSPI / KOSDAQ)
      * ``auditInfo``    — 감리 정보 (e.g. "정상", "투자주의환기")
      * ``state``        — 상태 (e.g. "관리종목", "거래정지")
      * ``orderWarning`` — 주문 경고 (e.g. "투자유의")

    The normalizer projects the raw row into the shape
    ``_is_excluded_security`` understands: ``ticker``, ``name``,
    ``market``, ``sec_type``, ``admin_issue``, ``trading_halt``, and
    keeps the raw audit / state / order-warning strings on the row so
    the report can record *why* a ticker was rejected.
    """
    items = _extract_list(
        payload,
        keys=("list", "stk_info_list", "output"),
    )
    rows: list[dict[str, Any]] = []
    for r in items:
        if not isinstance(r, dict):
            continue
        code = str(r.get("code") or r.get("stk_cd") or "").strip()
        if not code:
            continue
        market_code = str(r.get("marketCode") or r.get("mrkt_id") or "").strip()
        market_name = str(r.get("marketName") or r.get("mrkt_nm") or "").strip()
        market = (market_name or _market_from_code(market_code)).upper() or "UNKNOWN"

        state = str(r.get("state") or "").strip()
        audit_info = str(r.get("auditInfo") or "").strip()
        order_warning = str(r.get("orderWarning") or "").strip()
        name = str(r.get("name") or "").strip()
        sec_type = _detect_sec_type(name, r)

        admin_issue = ("관리종목" in state) or ("관리" in audit_info)
        trading_halt = ("거래정지" in state) or ("정지" in state)
        attention = ("투자주의" in audit_info) or ("투자주의" in order_warning) \
                    or ("환기" in audit_info)

        rows.append({
            "ticker": code,
            "name": name,
            "market": market,
            "sec_type": sec_type,
            "admin_issue": admin_issue,
            "trading_halt": trading_halt,
            "attention_issue": attention,
            "audit_info": audit_info or None,
            "order_warning": order_warning or None,
            "state_raw": state or None,
        })
    return rows


def _extract_list(payload: Any, *, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for k in keys:
        v = payload.get(k)
        if isinstance(v, list):
            return v
    return []


def _market_from_code(market_code: str) -> str:
    code = (market_code or "").strip()
    if code in {"0", "STK", "KOSPI", "kospi"}:
        return "KOSPI"
    if code in {"10", "KSQ", "KOSDAQ", "kosdaq"}:
        return "KOSDAQ"
    return ""


_PREFERRED_SUFFIXES = ("우", "우B", "1우", "2우B", "3우B")
_ETF_PREFIXES = ("KODEX", "TIGER", "ARIRANG", "HANARO", "ACE", "PLUS", "SOL", "KOSEF", "KBSTAR")


def _detect_sec_type(name: str, raw: Mapping[str, Any]) -> str:
    """Infer sec_type from raw ka10099 row fields when not explicit."""
    explicit = str(raw.get("sec_type") or raw.get("stk_cls") or "").strip().lower()
    if explicit:
        return explicit
    nm = (name or "").strip()
    upper = nm.upper()
    if any(upper.startswith(p) for p in _ETF_PREFIXES):
        return "etf"
    if "스팩" in nm or "SPAC" in upper:
        return "spac"
    if "ETN" in upper:
        return "etn"
    if any(nm.endswith(s) for s in _PREFERRED_SUFFIXES):
        return "preferred"
    return "common"


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

    allowed_tr_ids = _resolve_allowed_tr_ids(config.get("allowed_tr_ids"))
    # belt-and-braces: still run the substring guard on every entry.
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
        excluded, reason = _is_excluded_security(row, cfg)
        if excluded:
            rejected[str(row["ticker"])] = reason or "excluded"
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
            rejected[ticker] = f"insufficient_history:{len(closes)}"
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

    # Run-level atomic publish: write all three to <name>.tmp first;
    # only rename onto the _latest paths once every tmp write
    # succeeded.  A mid-run failure never replaces the previous
    # _latest files.
    _publish_atomic([
        (features_path, features_payload),
        (universe_path, universe_payload),
        (report_path,   report_payload),
    ])

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
        config = load_config(config_path, repo_root=repo_root)
    except (KiwoomConfigMissingError, KiwoomConfigPathInRepoError) as exc:
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
