#!/usr/bin/env python3
"""
Phase 3 — Ticker resolver (PR #21).

Loads the authoritative `resources/ticker_map.csv` (or any CSV in either the
rich PR #21 schema or the legacy PR #4 schema) and resolves Korean company
names from broker-report PDFs into KRX:NNNNNN tickers.

Pure data + lookup. NO OCR, NO Vision, NO network call. The resolver is
deterministic and offline; it only consumes a CSV and a text fragment.

Schema (rich, PR #21 — the new authoritative format):
    company_name_kr,ticker,aliases,market,notes

Schema (legacy, PR #4 — still accepted for backward compatibility):
    name_kr,ticker

Lookup contract:
    `resolve(value, *, filename=None, ticker_map=...)` returns
    "KRX:NNNNNN" on hit OR None on miss. Inputs that already start with
    "KRX:" are returned as-is. Lookup order:
        1. exact value in ticker_map (which already includes aliases)
        2. normalize(value) in ticker_map (strips ㈜ / 주식회사 / spaces /
           trailing parens-with-digits)
        3. extract `[<korean name>]` from `filename`, then re-try (1)+(2)
    `filename` is optional; when omitted only steps 1+2 run.

Validation contract (`validate_ticker_map(rows)`):
    Surfaces fatal data errors as a list of strings. Empty list = OK.
    Errors covered:
      * ticker is not 'KRX:[0-9]{6}'
      * duplicate company_name_kr
      * duplicate ticker
      * alias collides with another canonical company_name_kr
      * alias collides with another row's alias
      * market not in {KOSPI, KOSDAQ, KONEX} (rich schema only)

This module is invoked directly via `--verify` for CI-style data checks
and is also imported by `bridge_scan_to_parsed_meta.py`.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable, List

KRX_TICKER_RE = re.compile(r"^KRX:[0-9]{6}$")
ALLOWED_MARKETS: frozenset[str] = frozenset({"KOSPI", "KOSDAQ", "KONEX"})

# Korean entity-form prefixes/suffixes that should not affect lookup.
# Stripped during normalization (longest forms first).
_ENTITY_PREFIXES: tuple[str, ...] = ("주식회사 ", "주식회사", "(주)", "㈜")
_ENTITY_SUFFIXES: tuple[str, ...] = ("주식회사", "(주)", "㈜")

# Trailing parens-with-digits / KRX code embedded in the company token, e.g.
#   '대덕전자(353200)' / '삼성전자(KRX:005930)' → drop the parenthesized tail.
_TRAILING_PAREN_DIGIT_RE = re.compile(r"\s*\([^)]*\d[^)]*\)\s*$")

# Matches the '[<name>]' bracket block typical of WiseReport filenames:
#   '20260430_[대덕전자] 클 대.pdf' → '대덕전자'
_BRACKET_NAME_RE = re.compile(r"\[([^\]]+)\]")


def normalize_kr_company(name: str) -> str:
    """Strip 주식회사 / ㈜ / (주) / surrounding whitespace / trailing
    parens-with-digits. Returns '' if the result is empty or `name` isn't
    a string. Idempotent — running it twice yields the same result.
    """
    if not isinstance(name, str):
        return ""
    s = name.strip()
    if not s:
        return ""
    # Drop a trailing parenthesized fragment that contains digits (e.g. '(353200)').
    s = _TRAILING_PAREN_DIGIT_RE.sub("", s).strip()
    # Strip entity-form prefixes (longest first to avoid '(주' being eaten by '(주)').
    for pref in _ENTITY_PREFIXES:
        if s.startswith(pref):
            s = s[len(pref):].lstrip()
            break
    # Strip entity-form suffixes.
    for suf in _ENTITY_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)].rstrip()
            break
    # Collapse internal whitespace runs to a single space.
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_bracketed_name(filename: str) -> str:
    """Return the FIRST '[...]' fragment in `filename`, normalized. Returns
    '' if `filename` isn't a string or has no bracket block.
    """
    if not isinstance(filename, str):
        return ""
    m = _BRACKET_NAME_RE.search(filename)
    if not m:
        return ""
    return normalize_kr_company(m.group(1))


def is_krx(t: object) -> bool:
    """True iff `t` is a string of the form 'KRX:NNNNNN'."""
    return isinstance(t, str) and bool(KRX_TICKER_RE.match(t))


def _split_aliases(raw: str) -> list[str]:
    """Semicolon-split + trim. Empty / whitespace-only entries are dropped."""
    if not raw:
        return []
    return [a.strip() for a in raw.split(";") if a and a.strip()]


def load_ticker_map_rows(path: Path) -> list[dict]:
    """Read the CSV file and return a list of row dicts. Comment lines
    starting with '#' are skipped (so the data file can carry a header
    block). The CSV is auto-detected as either:
        rich:    company_name_kr,ticker,aliases,market,notes
        legacy:  name_kr,ticker
    Each row is normalized to the rich shape (missing fields default to '').
    """
    text = path.read_text(encoding="utf-8")
    # Strip lines that are entirely a CSV comment (start with '#'). DictReader
    # cannot do this natively — but a leading '#' is unambiguous in our schema
    # because no real Korean company name starts with '#'.
    cleaned = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    reader = csv.DictReader(cleaned.splitlines())
    if not reader.fieldnames:
        raise ValueError(f"ticker_map has no header row: {path}")
    fields = set(reader.fieldnames)
    rows: list[dict] = []
    if "company_name_kr" in fields and "ticker" in fields:
        for r in reader:
            rows.append({
                "company_name_kr": (r.get("company_name_kr") or "").strip(),
                "ticker": (r.get("ticker") or "").strip(),
                "aliases": (r.get("aliases") or "").strip(),
                "market": (r.get("market") or "").strip(),
                "notes": (r.get("notes") or "").strip(),
            })
        return rows
    if "name_kr" in fields and "ticker" in fields:
        for r in reader:
            rows.append({
                "company_name_kr": (r.get("name_kr") or "").strip(),
                "ticker": (r.get("ticker") or "").strip(),
                "aliases": "",
                "market": "",
                "notes": "(legacy schema)",
            })
        return rows
    raise ValueError(
        f"ticker_map columns must be either "
        f"(company_name_kr,ticker,aliases,market,notes) or (name_kr,ticker); "
        f"got {sorted(fields)}"
    )


def validate_ticker_map(rows: list[dict], *, strict_market: bool = True) -> list[str]:
    """Return a list of human-readable validation errors. Empty list = OK.

    `strict_market` requires market ∈ {KOSPI,KOSDAQ,KONEX} when the
    market column is non-empty (legacy rows have it blank and are exempt).
    """
    errors: list[str] = []
    seen_companies: dict[str, int] = {}
    seen_tickers: dict[str, int] = {}
    seen_aliases: dict[str, int] = {}
    canonical_set: set[str] = {r["company_name_kr"] for r in rows if r["company_name_kr"]}

    for i, r in enumerate(rows, start=1):
        cn = r["company_name_kr"]
        tk = r["ticker"]
        if not cn:
            errors.append(f"row {i}: empty company_name_kr")
        if not tk:
            errors.append(f"row {i}: empty ticker for {cn!r}")
        elif not KRX_TICKER_RE.match(tk):
            errors.append(f"row {i}: ticker {tk!r} for {cn!r} is not 'KRX:NNNNNN'")
        if cn:
            if cn in seen_companies:
                errors.append(
                    f"row {i}: duplicate company_name_kr {cn!r} "
                    f"(also at row {seen_companies[cn]})"
                )
            else:
                seen_companies[cn] = i
        if tk:
            if tk in seen_tickers:
                errors.append(
                    f"row {i}: duplicate ticker {tk!r} for {cn!r} "
                    f"(also at row {seen_tickers[tk]})"
                )
            else:
                seen_tickers[tk] = i
        # Market gate (rich schema only — legacy rows have market='').
        if strict_market and r["market"] and r["market"] not in ALLOWED_MARKETS:
            errors.append(
                f"row {i}: market {r['market']!r} for {cn!r} not in "
                f"{sorted(ALLOWED_MARKETS)}"
            )
        for alias in _split_aliases(r["aliases"]):
            if alias == cn:
                # An alias identical to its own canonical name is harmless;
                # silently ignore so authors don't have to dedupe by hand.
                continue
            if alias in canonical_set and alias != cn:
                errors.append(
                    f"row {i}: alias {alias!r} on {cn!r} collides with another "
                    f"row's canonical company_name_kr"
                )
            if alias in seen_aliases:
                errors.append(
                    f"row {i}: alias {alias!r} on {cn!r} also defined at "
                    f"row {seen_aliases[alias]}"
                )
            else:
                seen_aliases[alias] = i
    return errors


def build_lookup(rows: list[dict]) -> dict[str, str]:
    """Flatten rows into {<name-or-alias>: 'KRX:NNNNNN'}. Each canonical name
    AND each alias becomes a key. Order: canonical takes precedence (so an
    alias collision on top of a canonical doesn't override). Whitespace is
    preserved as-given so a lookup can hit before normalization.
    """
    out: dict[str, str] = {}
    # Canonical first.
    for r in rows:
        cn = r["company_name_kr"]
        tk = r["ticker"]
        if cn and tk:
            out.setdefault(cn, tk)
    # Aliases second — only fill if not already taken by a canonical name.
    for r in rows:
        tk = r["ticker"]
        if not tk:
            continue
        for alias in _split_aliases(r["aliases"]):
            out.setdefault(alias, tk)
    return out


def load_ticker_map(path: Path, *, strict_market: bool = True) -> dict[str, str]:
    """Convenience wrapper: read + validate + flatten. Raises ValueError on
    any validation error — callers that need partial recovery should use
    `load_ticker_map_rows` + `validate_ticker_map` directly.
    """
    rows = load_ticker_map_rows(path)
    errors = validate_ticker_map(rows, strict_market=strict_market)
    if errors:
        raise ValueError(
            "ticker_map validation failed:\n  " + "\n  ".join(errors)
        )
    return build_lookup(rows)


def resolve(
    value: str | None,
    *,
    filename: str | None = None,
    ticker_map: dict[str, str],
) -> str | None:
    """Return 'KRX:NNNNNN' on hit, None on miss.

    Lookup order:
      1. value already in KRX:NNNNNN form → returned as-is.
      2. exact value in ticker_map.
      3. normalized value in ticker_map.
      4. if `filename` is given: extract the first '[...]' bracket name,
         normalize it, and re-try ticker_map.
    """
    if value and is_krx(value):
        return value
    if isinstance(value, str) and value:
        if value in ticker_map:
            return ticker_map[value]
        norm = normalize_kr_company(value)
        if norm and norm in ticker_map:
            return ticker_map[norm]
    if filename:
        bn = extract_bracketed_name(filename)
        if bn:
            if bn in ticker_map:
                return ticker_map[bn]
            norm = normalize_kr_company(bn)
            if norm and norm in ticker_map:
                return ticker_map[norm]
    return None


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.ticker_map).expanduser().resolve()
    if not path.is_file():
        print(f"error: --ticker-map not found: {path}", file=sys.stderr)
        return 2
    try:
        rows = load_ticker_map_rows(path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_ticker_map(rows, strict_market=not args.no_strict_market)
    flat = build_lookup(rows)
    n_aliases = sum(len(_split_aliases(r["aliases"])) for r in rows)
    print(f"[ticker_map] file              = {path}")
    print(f"[ticker_map] rows              = {len(rows)}")
    print(f"[ticker_map] aliases (total)   = {n_aliases}")
    print(f"[ticker_map] lookup keys total = {len(flat)}  (canonical + aliases)")
    if rows:
        markets: dict[str, int] = {}
        for r in rows:
            markets[r["market"] or "(blank)"] = markets.get(r["market"] or "(blank)", 0) + 1
        for m in sorted(markets):
            print(f"[ticker_map] market {m:8s} = {markets[m]}")
    if errors:
        print(f"[ticker_map] VALIDATION ERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 3
    print("[ticker_map] validation: PASS")
    return 0


def _cmd_resolve(args: argparse.Namespace) -> int:
    path = Path(args.ticker_map).expanduser().resolve()
    if not path.is_file():
        print(f"error: --ticker-map not found: {path}", file=sys.stderr)
        return 2
    try:
        tmap = load_ticker_map(path, strict_market=not args.no_strict_market)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    hit = resolve(args.value or "", filename=args.filename, ticker_map=tmap)
    if hit is None:
        print(f"unresolved: value={args.value!r} filename={args.filename!r}")
        return 1
    print(hit)
    return 0


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--ticker-map", required=True,
                   help="Path to ticker_map CSV (rich or legacy schema).")
    p.add_argument("--verify", action="store_true",
                   help="Validate the ticker_map (format / dupes / collisions). "
                        "Exits 0 on PASS, 3 on validation error, 2 on I/O error.")
    p.add_argument("--resolve", dest="resolve_mode", action="store_true",
                   help="Resolve a single value via the loaded map. Use --value "
                        "and/or --filename.")
    p.add_argument("--value", default=None,
                   help="Korean company name or KRX:NNNNNN to resolve.")
    p.add_argument("--filename", default=None,
                   help="Optional filename hint (e.g. '20260430_[대덕전자] 보고서.pdf').")
    p.add_argument("--no-strict-market", action="store_true",
                   help="Disable the KOSPI/KOSDAQ/KONEX market gate (use only for "
                        "legacy two-column maps that have no market field).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv if argv is not None else sys.argv[1:])
    if args.resolve_mode:
        return _cmd_resolve(args)
    if args.verify:
        return _cmd_verify(args)
    print("error: pass --verify or --resolve", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
