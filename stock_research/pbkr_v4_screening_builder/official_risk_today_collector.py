"""KRX / KIND / DART official-risk collector.

Builds the ``official_risk_flags_latest.json`` input that the read-only
``live-screen`` runner consumes, plus an audit-only
``official_risk_collection_report_latest.json``.

Hard rules
----------
1. **Only KRX / KIND / DART are official.**  Telegram, news, blog,
   social-media or chat-room mentions of risk are *not* official and
   may not promote a row to a risk bucket.  The collector enforces this
   via an allow-list (``ALLOWED_OFFICIAL_SOURCES``) and a deny-list
   (``FORBIDDEN_NON_OFFICIAL_SOURCES``).
2. **No silent fallback.**  If the input bundle does not record which
   official sources were checked (``sources_checked``), the collector
   refuses to publish — it never invents an "all clean" pack.  An
   empty ``sources_checked`` is treated the same as missing.
3. **Audit status.**  When ``sources_checked`` is non-empty *and* no
   row carries a bucket, the pack is marked
   ``audit_status = "NO_OFFICIAL_RISK_FLAG_CONFIRMED"`` so downstream
   consumers can see that the absence of flags is a *checked* result,
   not an uninformed default.
4. **Market-structure summary.**  ``market_structure.market_structure_state``
   is derived from sidecar / circuit-breaker / auction-window booleans
   and surfaces as ``"NO_ENTRY_MARKET_STRUCTURE_ACTIVE"`` whenever any
   of those is active.  This is independent of per-row buckets.
5. **No execution.**  ``--no-execution`` is required at the CLI; the
   pack carries the canonical ``signal_safety`` block.
6. **Output is private.**  Output directory must live under
   ``$PBKR_PROCESSED_ROOT/live_screen_inputs`` (or an explicit
   ``--output-dir``) and **must** resolve outside the repository.
7. **Atomic publish.**  Both ``_latest.json`` files are written via
   the same two-phase ``<name>.tmp → rename`` sequence the Kiwoom
   collector uses.

Input bundle shape
------------------
The collector reads a JSON file whose shape mirrors the official-risk
fixture used by the screening builder, *plus* a required
``sources_checked`` array::

    {
      "sources_checked": ["KRX", "KIND", "DART"],
      "market_structure": {
        "circuit_breaker_active": false,
        "sidecar_active": false,
        "auction_window": "none"
      },
      "rows": [
        {"ticker": "AAA.KS", "raw_designations": []},
        {"ticker": "BBB.KQ", "raw_designations": ["투자주의"]}
      ]
    }
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.official_risk import (
    derive_audit_status,
    derive_market_structure_state,
    load_official_risk_flags,
)
from .constants import DAILY_PACKET_SIGNAL_SAFETY, SCHEMA_VERSION


DEFAULT_OUTPUT_BASE = (
    os.getenv("PBKR_PROCESSED_ROOT")
    or "/Users/bsunjun/trading/phase3/processed"
)

LIVE_SCREEN_INPUTS_SUBDIR = "live_screen_inputs"

OFFICIAL_RISK_FLAGS_FILENAME = "official_risk_flags_latest.json"
OFFICIAL_RISK_REPORT_FILENAME = "official_risk_collection_report_latest.json"

# The only sources that may promote a row to a risk bucket.
ALLOWED_OFFICIAL_SOURCES: tuple[str, ...] = ("KRX", "KIND", "DART")

# Non-official mention sources — explicitly listed for a clearer error
# message when an operator's bundle accidentally lists one.
FORBIDDEN_NON_OFFICIAL_SOURCES: tuple[str, ...] = (
    "telegram",
    "news",
    "blog",
    "twitter",
    "x",
    "youtube",
    "kakao",
    "discord",
    "reddit",
    "naver_cafe",
)

# Per-row source-claim fields.  When a row carries any of these and
# names a non-official channel, the bundle is rejected — even if the
# top-level ``sources_checked`` only lists KRX/KIND/DART.  This blocks
# bundles that claim to consult an official source but try to launder
# a Telegram / news / blog row through anyway.
ROW_SOURCE_FIELDS: tuple[str, ...] = (
    "source",
    "source_type",
    "source_name",
    "origin",
    "channel",
    "evidence_source",
)


class OfficialRiskCollectorError(Exception):
    """Base class for official-risk collector errors."""


class OfficialRiskBundlePathInRepoError(OfficialRiskCollectorError):
    """The --source-bundle path resolves inside the repository."""


class OfficialRiskOutputPathInRepoError(OfficialRiskCollectorError):
    """The requested output directory is inside the repository."""


class OfficialRiskBundleMissingError(OfficialRiskCollectorError):
    """The --source-bundle argument was not supplied or the file is missing/empty."""


class OfficialRiskBundleInvalidError(OfficialRiskCollectorError):
    """The bundle file is structurally invalid."""


class OfficialRiskNoSourceCheckedError(OfficialRiskCollectorError):
    """The bundle did not record any official source as checked."""


class OfficialRiskUnauthorizedSourceError(OfficialRiskCollectorError):
    """The bundle lists a source outside ALLOWED_OFFICIAL_SOURCES."""


class OfficialRiskCollectionFailed(OfficialRiskCollectorError):
    """The collector failed before any output was published."""


def _assert_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    raise OfficialRiskOutputPathInRepoError(
        f"refusing to write official-risk collector outputs inside the repository: {path}\n"
        f"set --output-dir (or $PBKR_PROCESSED_ROOT) to a local/private path "
        f"such as {DEFAULT_OUTPUT_BASE}/{LIVE_SCREEN_INPUTS_SUBDIR}"
    )


def _assert_bundle_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    raise OfficialRiskBundlePathInRepoError(
        f"refusing to read official-risk bundle from inside the repository: {path}\n"
        "place the bundle file under a private path."
    )


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    base = Path(DEFAULT_OUTPUT_BASE).expanduser()
    return (base / LIVE_SCREEN_INPUTS_SUBDIR).resolve()


def _publish_atomic(triples: list[tuple[Path, dict[str, Any]]]) -> None:
    """Two-phase atomic publish.  Mirrors the Kiwoom collector helper."""
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


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _asof_iso(date_str: str) -> str:
    return f"{date_str}T15:30:00+09:00"


def _validate_sources_checked(raw_payload: Any, source_path: Path) -> list[str]:
    """Validate ``sources_checked`` and return the canonical (uppercased) list.

    * Missing or empty → ``OfficialRiskNoSourceCheckedError``.  An
      "all clean" pack without a source claim is forbidden.
    * Any entry outside ``ALLOWED_OFFICIAL_SOURCES`` →
      ``OfficialRiskUnauthorizedSourceError``.  Telegram / news / blog
      / social-media mentions cannot promote a risk flag.
    """
    if not isinstance(raw_payload, dict):
        raise OfficialRiskBundleInvalidError(
            f"official-risk bundle {source_path} must be a JSON object."
        )
    raw = raw_payload.get("sources_checked")
    if raw is None:
        raise OfficialRiskNoSourceCheckedError(
            f"official-risk bundle {source_path} has no 'sources_checked' key.\n"
            f"the collector requires explicit acknowledgement of which official "
            f"sources were consulted (allowed: {list(ALLOWED_OFFICIAL_SOURCES)}).  "
            "an all-none output without a source claim is forbidden."
        )
    if not isinstance(raw, list) or not raw:
        raise OfficialRiskNoSourceCheckedError(
            f"official-risk bundle {source_path} 'sources_checked' must be a "
            f"non-empty array of {list(ALLOWED_OFFICIAL_SOURCES)}."
        )
    canonical: list[str] = []
    for entry in raw:
        if not isinstance(entry, str):
            raise OfficialRiskBundleInvalidError(
                f"official-risk bundle {source_path} 'sources_checked' must "
                f"contain strings only (got {type(entry).__name__})."
            )
        token = entry.strip()
        upper = token.upper()
        lower = token.lower()
        if lower in FORBIDDEN_NON_OFFICIAL_SOURCES:
            raise OfficialRiskUnauthorizedSourceError(
                f"official-risk bundle {source_path} lists non-official source "
                f"{token!r}.  Telegram / news / blog / social-media mentions are "
                f"NEVER promoted to an official risk flag.  Only "
                f"{list(ALLOWED_OFFICIAL_SOURCES)} are accepted."
            )
        if upper not in ALLOWED_OFFICIAL_SOURCES:
            raise OfficialRiskUnauthorizedSourceError(
                f"official-risk bundle {source_path} lists unauthorized source "
                f"{token!r}.  Allowed: {list(ALLOWED_OFFICIAL_SOURCES)}."
            )
        if upper not in canonical:
            canonical.append(upper)
    return canonical


def _validate_bundle_shape(raw_payload: Any, source_path: Path) -> None:
    if not isinstance(raw_payload, dict):
        raise OfficialRiskBundleInvalidError(
            f"official-risk bundle {source_path} must be a JSON object."
        )
    rows = raw_payload.get("rows")
    if rows is None:
        raise OfficialRiskBundleInvalidError(
            f"official-risk bundle {source_path} has no 'rows' key."
        )
    if not isinstance(rows, list):
        raise OfficialRiskBundleInvalidError(
            f"official-risk bundle {source_path} 'rows' must be a JSON array."
        )


def _validate_row_sources(raw_payload: dict[str, Any], source_path: Path) -> None:
    """Enforce per-row source claims, when present.

    Top-level ``sources_checked`` says *which* official feeds the
    operator consulted; per-row source fields claim *which* source
    surfaced the row.  A bundle with ``sources_checked = ["KRX"]`` but
    a row whose ``source_type = "telegram"`` is trying to launder a
    non-official mention through an official-looking pack — the
    collector refuses such a bundle.

    Recognised row-level fields (any of them is sufficient): see
    ``ROW_SOURCE_FIELDS``.  When *none* of these fields is set on a
    row, the row inherits the top-level ``sources_checked`` claim and
    no further check is required.
    """
    rows = raw_payload.get("rows") or []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        for field_name in ROW_SOURCE_FIELDS:
            value = row.get(field_name)
            if value is None:
                continue
            # Row source fields are expected to be string scalars.  A
            # list / dict shape is structurally invalid: we surface a
            # specific error rather than silently ignoring it.
            if not isinstance(value, str):
                raise OfficialRiskBundleInvalidError(
                    f"official-risk bundle {source_path} row[{idx}] field "
                    f"{field_name!r} must be a string, got {type(value).__name__}."
                )
            token = value.strip()
            if not token:
                continue
            ticker = str(row.get("ticker") or f"<row[{idx}]>")
            lowered = token.lower()
            uppered = token.upper()
            if lowered in FORBIDDEN_NON_OFFICIAL_SOURCES:
                raise OfficialRiskUnauthorizedSourceError(
                    f"official-risk bundle {source_path} row {ticker!r} field "
                    f"{field_name!r}={token!r} is a non-official source.  "
                    f"Telegram / news / blog / social-media mentions are NEVER "
                    f"promoted to an official risk flag.  Only "
                    f"{list(ALLOWED_OFFICIAL_SOURCES)} are accepted at the row level."
                )
            if uppered not in ALLOWED_OFFICIAL_SOURCES:
                raise OfficialRiskUnauthorizedSourceError(
                    f"official-risk bundle {source_path} row {ticker!r} field "
                    f"{field_name!r}={token!r} is not an allowed official source.  "
                    f"Allowed at the row level: {list(ALLOWED_OFFICIAL_SOURCES)}."
                )


@dataclass
class OfficialRiskCollectionResult:
    asof_date: str
    output_dir: Path
    flags_path: Path
    report_path: Path
    sources_checked: list[str]
    audit_status: str
    market_structure_state: str
    row_count: int
    flagged_row_count: int


def collect_today_official_risk(
    *,
    asof_date: str,
    bundle_path: str | Path,
    output_dir: Path,
    repo_root: Path,
) -> OfficialRiskCollectionResult:
    """Build ``official_risk_flags_latest.json`` from a KRX/KIND/DART bundle."""
    _assert_outside_repo(output_dir, repo_root)

    src = Path(bundle_path).expanduser()
    _assert_bundle_outside_repo(src, repo_root)
    if not src.exists():
        raise OfficialRiskBundleMissingError(
            f"official-risk bundle not found: {src}\n"
            "the collector refuses to substitute a synthetic / mock input on missing source."
        )
    if not src.is_file():
        raise OfficialRiskBundleMissingError(
            f"official-risk bundle is not a regular file: {src}"
        )
    if src.stat().st_size == 0:
        raise OfficialRiskBundleMissingError(
            f"official-risk bundle is empty: {src}\n"
            "the collector refuses to substitute a synthetic / mock input on empty source."
        )

    started_at = _utc_iso_now()

    try:
        raw_payload = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OfficialRiskBundleInvalidError(
            f"official-risk bundle {src} is not valid JSON: {exc}"
        ) from exc

    _validate_bundle_shape(raw_payload, src)
    sources_checked = _validate_sources_checked(raw_payload, src)
    _validate_row_sources(raw_payload, src)

    pack = load_official_risk_flags(src, asof=_asof_iso(asof_date))

    market_structure_state = derive_market_structure_state(pack["market_structure"])
    pack["market_structure"]["market_structure_state"] = market_structure_state
    pack["sources_checked"] = list(sources_checked)
    pack["audit_status"] = derive_audit_status(pack["rows"])

    flagged_row_count = sum(1 for r in pack["rows"] if r.get("buckets"))
    bucket_counts = {
        "HARD_EXCLUDE": 0,
        "REGULAR_PB_EXCLUDE": 0,
        "EXTREME_RISK_FLAG_WATCH": 0,
        "RISK_FLAG_PULLBACK_WATCH": 0,
    }
    for r in pack["rows"]:
        for b in r.get("buckets", []):
            if b in bucket_counts:
                bucket_counts[b] += 1

    flags_path = output_dir / OFFICIAL_RISK_FLAGS_FILENAME
    report_path = output_dir / OFFICIAL_RISK_REPORT_FILENAME
    finished_at = _utc_iso_now()

    report_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "collector": "official_risk_today_collector",
        "asof_date": asof_date,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "output_dir": str(output_dir),
        "flags_file": OFFICIAL_RISK_FLAGS_FILENAME,
        "source_bundle_path": str(src),
        "sources_checked": list(sources_checked),
        "allowed_official_sources": list(ALLOWED_OFFICIAL_SOURCES),
        "audit_status": pack["audit_status"],
        "market_structure_state": market_structure_state,
        "row_count": len(pack["rows"]),
        "flagged_row_count": int(flagged_row_count),
        "bucket_counts": bucket_counts,
        "no_execution": True,
        "broker_order_path_present": False,
        "auto_execution_allowed": False,
        "forbidden_artifact_emitted": False,
        "success": True,
        "failure_reason": None,
        "signal_safety": dict(DAILY_PACKET_SIGNAL_SAFETY),
    }

    _publish_atomic([
        (flags_path, pack),
        (report_path, report_payload),
    ])

    return OfficialRiskCollectionResult(
        asof_date=asof_date,
        output_dir=output_dir,
        flags_path=flags_path,
        report_path=report_path,
        sources_checked=list(sources_checked),
        audit_status=pack["audit_status"],
        market_structure_state=market_structure_state,
        row_count=len(pack["rows"]),
        flagged_row_count=int(flagged_row_count),
    )


def cli_main(args: Any, repo_root: Path) -> int:
    """argparse entry point shared by the top-level CLI."""
    if not getattr(args, "no_execution", False):
        print(
            "[official-risk-collect] --no-execution is required.\n"
            "this subcommand is read-only and never authorizes broker orders, "
            "automatic execution, or trade tickets.  re-invoke with --no-execution "
            "to acknowledge.",
            file=sys.stderr,
        )
        return 2

    output_dir = _resolve_output_dir(args.output_dir)
    try:
        _assert_outside_repo(output_dir, repo_root)
    except OfficialRiskOutputPathInRepoError as exc:
        print(f"[official-risk-collect] {exc}", file=sys.stderr)
        return 2

    bundle = getattr(args, "source_bundle", None)
    if not bundle:
        print(
            "[official-risk-collect] --source-bundle <path> is required.\n"
            "supply the KRX/KIND/DART bundle JSON.  the collector never falls back "
            "to a synthetic / mock fixture in production.",
            file=sys.stderr,
        )
        return 2

    try:
        result = collect_today_official_risk(
            asof_date=args.date,
            bundle_path=bundle,
            output_dir=output_dir,
            repo_root=repo_root,
        )
    except (
        OfficialRiskBundlePathInRepoError,
        OfficialRiskOutputPathInRepoError,
        OfficialRiskBundleMissingError,
        OfficialRiskBundleInvalidError,
        OfficialRiskNoSourceCheckedError,
        OfficialRiskUnauthorizedSourceError,
    ) as exc:
        print(f"[official-risk-collect] {exc}", file=sys.stderr)
        return 2
    except OfficialRiskCollectionFailed as exc:
        print(f"[official-risk-collect] {exc}", file=sys.stderr)
        return 1

    print(f"[official-risk-collect] wrote: {result.flags_path}")
    print(f"[official-risk-collect] wrote: {result.report_path}")
    print(
        f"[official-risk-collect] sources_checked={result.sources_checked} "
        f"audit_status={result.audit_status} "
        f"market_structure_state={result.market_structure_state} "
        f"rows={result.row_count} flagged={result.flagged_row_count}"
    )
    return 0
