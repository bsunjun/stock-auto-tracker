#!/usr/bin/env python3
"""
Phase 3 — Deterministic PDF estimate table extractor (PR #12 — skeleton).

Reads a WiseReport company-report PDF (or a pre-extracted text file, or an
inventory of either) and emits, per source PDF, at most ONE primary-metric
row to a structured_extraction.json that merge_meta.py can consume.

Design (frozen for PR #12):
  * deterministic-first. No OCR, no Vision, no network call.
  * primary metric priority:
        operating_profit > net_income > sales > eps
    Exactly one primary row per source_pdf_sha256 is emitted to
    structured_extraction.json (matching merge_meta's 1-row-per-sha
    contract).
  * full per-metric breakdown is written to a workdir-only audit file
    (estimate_table_breakdown.json), not consumed by merge_meta.
  * target-price-only reports are NOT emitted to structured_extraction.json
    (they would otherwise become primary-accepted under build --strict).
    They go to a workdir-only audit file (target_price_secondary.json).
  * direct_trade_signal is always False on every emitted row. PR #12 is
    not a trade-signal generator.
  * --apply refuses any --out / --workdir inside the repo.
  * --no-ocr is the default and the only supported mode in PR #12;
    Vision/OCR fallback is documented as a future option, not implemented.

This file is the SKELETON committed by PR #12A. The actual parsing logic
(text → metric rows; metric → primary selection; target-price detection)
lives in TODO functions and is filled in by subsequent commits.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

# Phase3 invariant. Every emitted row carries this verbatim.
DIRECT_TRADE_SIGNAL = False

# Primary metric selection (highest priority first).
PRIMARY_METRIC_PRIORITY: tuple[str, ...] = (
    "operating_profit",
    "net_income",
    "sales",
    "eps",
)

HARD_MAX_PDFS = 10
SOURCE_KEY_BASE = "phase3:pdf_estimate_table:v1"
DATE_FMT_HELP = "YYYY-MM-DD"


# --- Helpers (PR #12B) ----------------------------------------------------
# Pure functions, no I/O. Each is independently testable via the smoke
# checks committed alongside this change.

# Korean / English aliases for the four primary metrics. Keys are matched
# AFTER stripping any parenthesized suffix like "(원)" / "(억원)" / "(YoY)".
METRIC_ALIASES: dict[str, str] = {
    # sales
    "매출액": "sales",
    "매출": "sales",
    "Sales": "sales",
    "sales": "sales",
    # operating profit
    "영업이익": "operating_profit",
    "OP": "operating_profit",
    "op": "operating_profit",
    # net income
    "순이익": "net_income",
    "지배순이익": "net_income",
    "NI": "net_income",
    "ni": "net_income",
    # eps
    "EPS": "eps",
    "eps": "eps",
}

# Sentinels treated as "no value" by parse_numeric. Lowercased before lookup.
_SENTINELS_NULL: frozenset[str] = frozenset({
    "", "-", "—", "–", "n/a", "na", "null", "none",
})

# Horizon tokens: 2026E, 2027E, FY26, FY2026, 1Q26, 2Q26, 1Q2026, ...
_HORIZON_RE = re.compile(
    r"\b("
    r"\d{4}E"           # 2026E
    r"|FY\d{2,4}"       # FY26 / FY2026
    r"|\dQ\d{2,4}"      # 1Q26 / 2Q26 / 1Q2026
    r")\b"
)


def classify_metric_label(label: str) -> str | None:
    """Return canonical metric name (sales / operating_profit / net_income /
    eps), or None if `label` isn't one of the recognized aliases.

    Tolerates parenthesized suffixes like "EPS(원)" or "매출액(억원, YoY)".
    """
    if not isinstance(label, str):
        return None
    # Drop ALL parenthesized fragments, then trim.
    s = re.sub(r"\([^)]*\)", "", label).strip()
    if not s:
        return None
    if s in METRIC_ALIASES:
        return METRIC_ALIASES[s]
    if s.lower() in METRIC_ALIASES:
        return METRIC_ALIASES[s.lower()]
    return None


def parse_horizon(text: str) -> str:
    """Extract the first horizon token in `text` (e.g. '2026E', 'FY26',
    '1Q26'). Returns '' if no token is found."""
    if not isinstance(text, str):
        return ""
    m = _HORIZON_RE.search(text)
    return m.group(1) if m else ""


def parse_numeric(s: object) -> float | None:
    """Parse a Korean-or-English numeric string into a finite float, or None.

    Accepts:
      * int / float (NaN / +inf / -inf rejected)
      * '1,234' / '1,000,000'
      * '1,000 억원' / '1,000 십억원' / '1,000 백만원' / '1,200원'
      * 'KRW 1,234' (prefix unit)
    Rejects:
      * None, bool, non-string non-numeric
      * '', '-', 'N/A', 'null' (any case) → None
      * 'NaN', 'inf', '-inf' (string or float) → None
      * any other unparseable string → None
    """
    if s is None or isinstance(s, bool):
        return None
    if isinstance(s, (int, float)):
        v = float(s)
        return v if math.isfinite(v) else None
    if not isinstance(s, str):
        return None
    t = s.strip()
    if not t or t.lower() in _SENTINELS_NULL:
        return None
    # Strip a leading currency token, e.g. 'KRW 1,234'.
    for prefix in ("KRW", "krw"):
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
            break
    # Strip a trailing Korean unit. Order matters: longest first so '십억원'
    # is matched before '억원' / '원'.
    for unit in ("십억원", "백만원", "천원", "억원", "원"):
        if t.endswith(unit):
            t = t[:-len(unit)].strip()
            break
    t = t.replace(",", "")
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def derive_direction(old: object, new: object) -> str:
    """Compare two numeric-like values; return 'up' / 'down' / 'flat' /
    'unknown'. Both sides must parse via parse_numeric for a finite verdict;
    otherwise the result is 'unknown' (matches build_report_estimate)."""
    o = parse_numeric(old)
    n = parse_numeric(new)
    if o is None or n is None:
        return "unknown"
    if n > o:
        return "up"
    if n < o:
        return "down"
    return "flat"


def select_primary_metric(metrics: dict) -> str | None:
    """Return the highest-priority metric present in `metrics`, per
    PRIMARY_METRIC_PRIORITY.

    `metrics` is keyed by canonical metric name; the value is expected to
    be a dict containing both 'old' and 'new' (raw forms). target_price
    is intentionally NOT a candidate — even if it is present in the dict
    (e.g., from a defensive caller), it is ignored. Returns None if no
    eligible candidate is present.
    """
    if not isinstance(metrics, dict):
        return None
    for m in PRIMARY_METRIC_PRIORITY:
        v = metrics.get(m)
        if isinstance(v, dict) and "old" in v and "new" in v:
            return m
    return None


# Longest first so '매출액' beats '매출', '지배순이익' beats '순이익'.
_METRIC_LABEL_PREFIXES: tuple[str, ...] = tuple(
    sorted(METRIC_ALIASES.keys(), key=len, reverse=True)
)

_ARROW_RE = re.compile(r"→|->")
_NUMBER_TOKEN_RE = re.compile(r"[+-]?[\d,]+(?:\.\d+)?")
_BROKER_SUFFIXES: tuple[str, ...] = ("증권", "금융투자", "자산운용")


def _extract_old_new_pair(line: str) -> tuple[str | None, str | None]:
    """Find an 'old → new' (or 'old -> new') numeric pair in a single line.

    Returns the raw token strings (still attached to any inline units);
    the caller passes each through parse_numeric to get a finite float.
    """
    if not isinstance(line, str):
        return None, None
    parts = _ARROW_RE.split(line, maxsplit=1)
    if len(parts) != 2:
        return None, None
    left, right = parts
    left_nums = _NUMBER_TOKEN_RE.findall(left)
    right_nums = _NUMBER_TOKEN_RE.findall(right)
    if not left_nums or not right_nums:
        return None, None
    return left_nums[-1], right_nums[0]


def _try_extract_metric_line(line: str) -> tuple[str, str, str] | None:
    """If `line` looks like a metric estimate change row of the form
    '<label>(...)?  <old> → <new>', return (canonical_metric, old_str,
    new_str). Else None.

    Recognized labels are anchored at the start of the line (after
    whitespace); the longest matching alias wins.
    """
    if not isinstance(line, str):
        return None
    s = line.lstrip()
    if not s:
        return None
    for label in _METRIC_LABEL_PREFIXES:
        if s.startswith(label):
            rest = s[len(label):]
            # Strip an immediately-following parenthesized clarifier like
            # 'EPS(원)' → ' ...'.
            rest = re.sub(r"^\s*\([^)]*\)", "", rest)
            old, new = _extract_old_new_pair(rest)
            if old is None or new is None:
                return None
            return METRIC_ALIASES[label], old, new
    return None
# --- end helpers ----------------------------------------------------------


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = p.add_argument_group("input (one of)")
    src.add_argument("--pdf", default=None,
                     help="Path to a single PDF (requires pdfplumber if used).")
    src.add_argument("--text", default=None,
                     help="Path to a pre-extracted text file (no PDF parsing needed).")
    src.add_argument("--inventory", default=None,
                     help="Path to a sample_inventory.json (PR #11 shape). "
                          "Each selected[] entry is processed; per-PDF text "
                          "is looked up under --text-dir by filename stem.")
    src.add_argument("--text-dir", default=None,
                     help="Directory holding <stem>.txt files when using --inventory.")

    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help=f"Target date {DATE_FMT_HELP} (default: today)")
    p.add_argument("--out", default=None,
                   help="Output structured_extraction.json path (must live "
                        "outside the repo). Defaults to <workdir>/structured_extraction.json.")
    p.add_argument("--workdir", default="/tmp/phase3_pr12",
                   help="Workdir for audit artifacts (estimate_table_breakdown.json, "
                        "target_price_secondary.json). Must be outside the repo.")
    p.add_argument("--max-pdfs", dest="max_pdfs", type=int, default=HARD_MAX_PDFS,
                   help=f"Hard cap on inputs (clamped to {HARD_MAX_PDFS}).")

    p.add_argument("--no-ocr", dest="ocr", action="store_false", default=False,
                   help="(default) Disable any OCR fallback. PR #12 is "
                        "deterministic-only.")
    p.add_argument("--ocr", dest="ocr", action="store_true",
                   help="Refused in PR #12. Reserved for a future cost-gated PR.")

    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Parse and report; do not write outputs.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize structured_extraction.json + audit files. "
                        "Refused if --out or --workdir is inside the repo.")
    return p.parse_args(argv)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


EXTRACTION_METHOD = "deterministic_pdf_table_v1"


def parse_text_to_rows(text: str, *, source_pdf_sha256: str, filename: str,
                       date: str) -> dict:
    """Parse a single PDF's pre-extracted text into a structured record.

    Returned dict:
        source_pdf_sha256, filename, broker, ticker_hint, horizon,
        metrics: {<metric>: {old: <raw>, new: <raw>}, ...},
        target_price: {old, new} | None,
        date, extraction_method
    """
    if not isinstance(text, str):
        text = ""

    # Broker: first non-empty line ending with a recognized suffix.
    broker = ""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(s.endswith(suf) for suf in _BROKER_SUFFIXES):
            broker = s
            break

    # Ticker hint: from filename's first '[...]' block if present.
    ticker_hint = ""
    fm = re.search(r"\[([^\]]+)\]", filename or "")
    if fm:
        ticker_hint = fm.group(1).strip()

    # Horizon: first horizon-like token anywhere in the text.
    horizon = parse_horizon(text)

    # Target price: a line containing '목표주가' with a numeric pair.
    target_price = None
    for line in text.splitlines():
        if "목표주가" not in line:
            continue
        old, new = _extract_old_new_pair(line)
        if old is not None and new is not None:
            target_price = {"old": old, "new": new}
            break

    # Metrics: scan every line; first occurrence per metric wins.
    metrics: dict[str, dict] = {}
    for line in text.splitlines():
        result = _try_extract_metric_line(line)
        if result is None:
            continue
        metric_name, old, new = result
        if metric_name not in metrics:
            metrics[metric_name] = {"old": old, "new": new}

    return {
        "source_pdf_sha256": source_pdf_sha256,
        "filename": filename,
        "broker": broker,
        "ticker_hint": ticker_hint,
        "horizon": horizon,
        "metrics": metrics,
        "target_price": target_price,
        "date": date,
        "extraction_method": EXTRACTION_METHOD,
    }


def project_structured_row(parsed: dict, *, date: str) -> dict | None:
    """Project a parsed record into a single merge_meta-compatible row.

    Returns None when no primary metric is selectable (target-price-only,
    empty, or all metric numbers malformed). The returned row always has
    direct_trade_signal=False.
    """
    metrics = parsed.get("metrics") or {}
    primary = select_primary_metric(metrics)
    if primary is None:
        return None

    metric_data = metrics[primary]
    old_raw = metric_data.get("old")
    new_raw = metric_data.get("new")
    if parse_numeric(old_raw) is None or parse_numeric(new_raw) is None:
        return None

    sha = parsed.get("source_pdf_sha256") or ""
    sha_short = sha[:12]
    sk = SOURCE_KEY_BASE + (f"+{sha_short}" if sha_short else "")
    direction = derive_direction(old_raw, new_raw)

    ticker = parsed.get("ticker_hint", "") or ""
    broker = parsed.get("broker", "") or ""
    horizon = parsed.get("horizon", "") or ""

    missing: list[str] = []
    if not ticker:
        missing.append("ticker")
    if not broker:
        missing.append("broker")
    if not date:
        missing.append("report_date")
    if not horizon:
        missing.append("horizon")
    complete = (not missing) and direction in {"up", "down", "flat"}

    return {
        "source_pdf_sha256": sha,
        "filename": parsed.get("filename", ""),
        "ticker": ticker,
        "broker": broker,
        "report_date": date,
        "horizon": horizon,
        "metric": primary,
        "old_target": old_raw,
        "new_target": new_raw,
        "direction": direction,
        "complete": complete,
        "missing_fields": missing,
        "extraction_method": EXTRACTION_METHOD,
        "source_key": sk,
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _build_breakdown(parsed: dict) -> dict:
    """Produce an audit-only per-PDF breakdown record covering EVERY metric
    found (not just the primary). Goes to estimate_table_breakdown.json."""
    return {
        "source_pdf_sha256": parsed.get("source_pdf_sha256", ""),
        "filename": parsed.get("filename", ""),
        "broker": parsed.get("broker", ""),
        "ticker_hint": parsed.get("ticker_hint", ""),
        "horizon": parsed.get("horizon", ""),
        "metrics": parsed.get("metrics") or {},
        "target_price": parsed.get("target_price"),
        "primary_metric": select_primary_metric(parsed.get("metrics") or {}),
        "extraction_method": EXTRACTION_METHOD,
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _build_target_price_secondary(parsed: dict) -> dict | None:
    """Produce a target-price-only audit record, or None if no target-price
    information is present. This file is NEVER consumed by merge_meta.
    """
    tp = parsed.get("target_price")
    if not tp:
        return None
    return {
        "source_pdf_sha256": parsed.get("source_pdf_sha256", ""),
        "filename": parsed.get("filename", ""),
        "broker": parsed.get("broker", ""),
        "ticker_hint": parsed.get("ticker_hint", ""),
        "target_price_old": tp.get("old"),
        "target_price_new": tp.get("new"),
        "target_price_role": "secondary_reference",
        "primary_metric_present": select_primary_metric(parsed.get("metrics") or {}) is not None,
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _read_text_for_input(args: argparse.Namespace, *, filename_hint: str = "",
                         text_path: Path | None = None) -> str:
    if text_path is not None and text_path.is_file():
        return text_path.read_text(encoding="utf-8", errors="replace")
    return ""


def _iter_inputs(args: argparse.Namespace):
    """Yield (text, source_pdf_sha256, filename) tuples from the chosen
    input mode. Honors --max-pdfs."""
    import hashlib
    import json as _json

    count = 0
    if args.inventory:
        inv_path = Path(args.inventory).expanduser().resolve()
        if not inv_path.is_file():
            print(f"error: --inventory not found: {inv_path}", file=sys.stderr)
            return
        try:
            inv = _json.loads(inv_path.read_text(encoding="utf-8"))
        except _json.JSONDecodeError as exc:
            print(f"error: --inventory not valid JSON: {exc}", file=sys.stderr)
            return
        selected = inv.get("selected") if isinstance(inv, dict) else None
        if not isinstance(selected, list):
            print("error: inventory has no `selected[]` list", file=sys.stderr)
            return
        text_dir = Path(args.text_dir).expanduser().resolve() if args.text_dir else None
        for entry in selected:
            if count >= args.max_pdfs:
                break
            sha = entry.get("source_pdf_sha256", "")
            fn = entry.get("filename", "")
            text = ""
            if text_dir:
                # try <stem>.txt
                stem = Path(fn).stem
                tp = text_dir / f"{stem}.txt"
                if tp.is_file():
                    text = tp.read_text(encoding="utf-8", errors="replace")
            yield text, sha, fn
            count += 1
        return

    if args.text:
        if count >= args.max_pdfs:
            return
        tp = Path(args.text).expanduser().resolve()
        if not tp.is_file():
            print(f"error: --text not found: {tp}", file=sys.stderr)
            return
        text = tp.read_text(encoding="utf-8", errors="replace")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        fn = tp.name
        yield text, sha, fn
        return

    if args.pdf:
        # PR #12 deliberately defers PDF body parsing through pdfplumber to a
        # later commit. For PR #12C the supported input modes are --text and
        # --inventory; --pdf raises a clear error.
        print("error: --pdf is not yet wired up. Use --text or --inventory "
              "with pre-extracted text. (pdfplumber path will land in a "
              "later commit on this branch.)", file=sys.stderr)
        return


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    # Skeleton-level guards that ARE active in PR #12A.
    if args.ocr:
        print("error: --ocr is refused in PR #12 (deterministic-only). "
              "OCR/Vision fallback is reserved for a future cost-gated PR.",
              file=sys.stderr)
        return 2

    if args.max_pdfs > HARD_MAX_PDFS:
        print(f"error: --max-pdfs {args.max_pdfs} exceeds the hard cap "
              f"({HARD_MAX_PDFS}); refusing.", file=sys.stderr)
        return 2
    if args.max_pdfs < 1:
        print("error: --max-pdfs must be >= 1", file=sys.stderr)
        return 2

    workdir = Path(args.workdir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out \
        else (workdir / "structured_extraction.json")

    if not args.dry_run:
        if _is_inside_repo(workdir):
            print(f"error: --workdir must live outside the repo (got {workdir})",
                  file=sys.stderr)
            return 2
        if _is_inside_repo(out_path):
            print(f"error: --out must live outside the repo (got {out_path})",
                  file=sys.stderr)
            return 2

    inputs_provided = sum(bool(x) for x in (args.pdf, args.text, args.inventory))
    if inputs_provided == 0:
        print("error: provide one of --pdf / --text / --inventory.", file=sys.stderr)
        return 2

    import json as _json
    structured: list[dict] = []
    breakdown: list[dict] = []
    secondary: list[dict] = []
    parsed_count = 0
    target_price_only_count = 0
    malformed_count = 0

    for text, sha, fn in _iter_inputs(args):
        parsed_count += 1
        parsed = parse_text_to_rows(text, source_pdf_sha256=sha,
                                    filename=fn, date=args.date)
        breakdown.append(_build_breakdown(parsed))
        row = project_structured_row(parsed, date=args.date)
        if row is not None:
            # Hard invariant: never emit direct_trade_signal=True.
            if row.get("direct_trade_signal") is not False:
                print(f"error: invariant violated — direct_trade_signal != False "
                      f"on emitted row for {fn}", file=sys.stderr)
                return 3
            structured.append(row)
        else:
            tp = _build_target_price_secondary(parsed)
            if tp is not None:
                secondary.append(tp)
                target_price_only_count += 1
            else:
                malformed_count += 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] inputs parsed                  = {parsed_count} (cap {args.max_pdfs})")
    print(f"[{mode}] structured (primary emitted)   = {len(structured)}")
    print(f"[{mode}] breakdown (audit, all metrics) = {len(breakdown)}")
    print(f"[{mode}] target_price_secondary (audit) = {len(secondary)}")
    print(f"[{mode}] target-price-only count        = {target_price_only_count}")
    print(f"[{mode}] no-metric / malformed count    = {malformed_count}")
    print(f"[{mode}] direct_trade_signal=true count = "
          f"{sum(1 for r in structured if r.get('direct_trade_signal') is not False)}")
    if structured:
        sample = structured[0]
        print(f"[{mode}] sample primary row             = "
              f"ticker={sample.get('ticker')!r} broker={sample.get('broker')!r} "
              f"metric={sample.get('metric')!r} {sample.get('old_target')!r}"
              f"→{sample.get('new_target')!r} ({sample.get('direction')!r})")

    if args.dry_run:
        print("[DRY-RUN] no files written. Re-run with --apply to materialize.")
        return 0

    workdir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_json.dumps(structured, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[APPLY] wrote {out_path}")
    bd_path = workdir / "estimate_table_breakdown.json"
    bd_path.write_text(_json.dumps(breakdown, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"[APPLY] wrote {bd_path}")
    sec_path = workdir / "target_price_secondary.json"
    sec_path.write_text(_json.dumps(secondary, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[APPLY] wrote {sec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
