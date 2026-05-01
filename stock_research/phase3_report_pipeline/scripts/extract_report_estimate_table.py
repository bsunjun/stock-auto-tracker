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
# --- PR #17: real-WiseReport revision-table layout parser ----------------
# These helpers are additive: parse_text_to_rows runs them AFTER the PR #12
# arrow-pair scanner, and only fills metrics the arrow scanner missed. This
# keeps the existing synthetic regression (PR #12 fixtures) byte-identical
# while extending coverage to '표3. 실적 전망' / '수정 후 / 수정 전 / 변동률'
# layouts that pdfplumber emits from real WiseReport company reports.

# Year tokens like 2025, 2026E, 2027F, 2028F, 2024A. Standalone match — used
# both to detect a horizon header line and to choose the preferred column.
# `A` (actual) added in PR #18 so headers like '2024A 2025A 2026E 2027F'
# (typical real-WiseReport forecast tables) are correctly recognized as
# year-pivot tables for gap_reason='ambiguous_year_pivot' classification.
_YEAR_HEADER_TOKEN_RE = re.compile(r"\b(20\d{2}[AEF]?)\b")

# Markers used inside the revision table.
_AFTER_LABELS = ("수정 후", "수정후")        # 'after' = new_target
_BEFORE_LABELS = ("수정 전", "수정전")        # 'before' = old_target
_PCT_LABELS = ("변동률", "변동 률", "변동율")


def select_horizon_from_header(header_line: str) -> tuple[str, int] | None:
    """Pick a horizon token + its 0-based column index from a header line.

    Preference, in order:
        1. first 'YYYYE' (estimate year)
        2. first 'YYYYF' (forecast year)
        3. first bare 'YYYY'
    Returns (horizon_token, column_index) or None when the line has no
    year-shaped tokens. Forward-year preference is intentional so the
    parser keeps choosing the most-recent E column as time rolls.
    """
    if not isinstance(header_line, str):
        return None
    tokens = _YEAR_HEADER_TOKEN_RE.findall(header_line)
    if not tokens:
        return None
    for i, t in enumerate(tokens):
        if t.endswith("E"):
            return t, i
    for i, t in enumerate(tokens):
        if t.endswith("F"):
            return t, i
    return tokens[0], 0


def find_estimate_revision_table_window(text: str) -> tuple[int, int] | None:
    """Locate the [start, end] line range of the revision table.

    Anchors:
      * a line containing '수정 후' (or '수정후') OR '수정 전' (or '수정전')
        (definitive marker for revision rows in this layout family);
      * a 'YYYYE'-bearing header line within ~15 lines above the anchor.
    If no after/before marker exists, return None — the new parser sees
    no revision table and stays out of the way.
    """
    if not isinstance(text, str):
        return None
    lines = text.splitlines()
    if not lines:
        return None
    anchor = None
    for i, line in enumerate(lines):
        if any(lab in line for lab in _AFTER_LABELS + _BEFORE_LABELS):
            anchor = i
            break
    if anchor is None:
        return None
    look_back = max(0, anchor - 15)
    header_idx = None
    for i in range(anchor, look_back - 1, -1):
        if select_horizon_from_header(lines[i]) is not None:
            header_idx = i
            break
    win_start = header_idx if header_idx is not None else max(0, anchor - 5)
    # End the window at the first non-table marker we recognize, or after
    # 40 lines (whichever is sooner). We look for known stop markers:
    #   - blank line followed by another blank
    #   - line starting with '목표주가' (target price block)
    win_end = min(len(lines) - 1, anchor + 40)
    return win_start, win_end


def parse_metric_revision_rows_from_window(
    text: str, *, start: int, end: int
) -> tuple[dict[str, dict], str]:
    """Walk the table window line by line; return (metrics, horizon_token).

    metrics: {<canonical-metric>: {old: <raw>, new: <raw>}}
    horizon_token: chosen header token; "" if none.

    Handles BOTH compact form (numbers on the same line as '수정 후/전') and
    split-line form (label and numbers on separate lines). 변동률 lines are
    informational and skipped.
    """
    if not isinstance(text, str):
        return {}, ""
    lines = text.splitlines()[start:end + 1]
    if not lines:
        return {}, ""

    horizon_token = ""
    horizon_col = None
    for line in lines:
        sel = select_horizon_from_header(line)
        if sel is not None:
            horizon_token, horizon_col = sel
            break
    if horizon_col is None:
        return {}, ""

    metrics: dict[str, dict] = {}
    current_metric: str | None = None
    pending_after: list[str] | None = None
    pending_before: list[str] | None = None

    def _commit():
        nonlocal pending_after, pending_before
        if (current_metric and current_metric not in metrics
                and pending_after is not None and pending_before is not None
                and len(pending_after) > horizon_col
                and len(pending_before) > horizon_col):
            metrics[current_metric] = {
                "old": pending_before[horizon_col],
                "new": pending_after[horizon_col],
            }
        # Reset pendings whether or not we committed; the next metric starts fresh.
        pending_after = None
        pending_before = None

    for raw_line in lines:
        s = raw_line.strip()
        if not s:
            continue

        # 1) Skip target-price line: never primary in PR #12/#17 contract.
        if "목표주가" in s:
            continue

        # 2) Metric label line. The longest match wins (e.g. '지배순이익' beats
        #    '순이익'). Only treat as a label if the line begins with the alias
        #    OR has the alias preceded by punctuation only.
        matched_label = None
        for label in _METRIC_LABEL_PREFIXES:
            if s.startswith(label):
                matched_label = label
                break
        if matched_label is not None:
            # Commit any pending data for the previous metric before switching.
            _commit()
            current_metric = METRIC_ALIASES[matched_label]
            # If the same line already carries 'old → new' (PR #12 arrow form),
            # let _try_extract_metric_line handle it via parse_text_to_rows;
            # the new layout parser's _commit fires only when 수정 후/전 are
            # populated, so a same-line arrow row does NOT incorrectly commit
            # here. Continue to the next line.
            continue

        # 3) 수정 후 / 수정 전 / 변동률 markers.
        if any(lab in s for lab in _AFTER_LABELS):
            nums = _NUMBER_TOKEN_RE.findall(s)
            # Strip prefix '- 수정 후' tokens; numbers come AFTER the marker.
            pending_after = nums  # may be [] if numbers wrap to next line
            # If we now have both sides, commit immediately.
            if pending_after and pending_before is not None and pending_before:
                _commit()
            continue
        if any(lab in s for lab in _BEFORE_LABELS):
            nums = _NUMBER_TOKEN_RE.findall(s)
            pending_before = nums
            if pending_after is not None and pending_after and pending_before:
                _commit()
            continue
        if any(lab in s for lab in _PCT_LABELS):
            # 변동률 line — informational only; never commit numbers from it.
            continue

        # 4) Numeric-only continuation line: fill the most-recently-opened
        #    pending bucket that is still empty. This handles the split-line
        #    form where '- 수정 후' is on one line and the numbers come on
        #    the next non-marker line.
        nums = _NUMBER_TOKEN_RE.findall(s)
        if not nums:
            continue
        if pending_after is not None and not pending_after:
            pending_after = nums
        elif pending_before is not None and not pending_before:
            pending_before = nums
        if pending_after and pending_before:
            _commit()

    # Commit any trailing pending metric at end of window.
    _commit()
    return metrics, horizon_token


def parse_revision_table_layout(text: str) -> tuple[dict[str, dict], str]:
    """Top-level entry: locate window + parse metrics. ({}, "") on miss."""
    win = find_estimate_revision_table_window(text)
    if win is None:
        return {}, ""
    return parse_metric_revision_rows_from_window(text, start=win[0], end=win[1])


# --- PR #18: additional broker-template variants --------------------------
# Three label conventions different brokers use for "old / new" columns,
# plus a side-anchor format observed in real WiseReport PDFs where the
# revision rows are folded next to body text by pdfplumber.
#
# Variant header pairs. Each entry is (old_labels, new_labels, kind).
# old_labels and new_labels are tuples of strings; the parser commits when
# it sees BOTH a column whose header contains an old_label and a column
# whose header contains a new_label.
_VARIANT_LABEL_PAIRS: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    # 기존 (existing) / 변경 (changed)
    (("기존",), ("변경",), "existing_changed"),
    # 변경 전 / 변경 후
    (("변경 전", "변경전"), ("변경 후", "변경후"), "change_before_after"),
    # 직전 / 현재 (real WiseReport convention; e.g. 대덕전자)
    (("직전",), ("현재",), "previous_current"),
)

# Side-anchor metric pattern: '<metric>(<year>[E|F]) <a> <b> ▲|▼|-'.
# The change indicator (▲/▼/-) is REQUIRED. Real WiseReport revision panels
# always include it; growth-rate / YoY tables do not. Requiring the
# indicator is the cleanest discriminator between revision rows and other
# tabular content that incidentally has the same `<metric>(<year>) <num> <num>`
# shape (e.g. consensus growth percentages).
_SIDE_ANCHOR_METRIC_RE = re.compile(
    r"(?P<metric>매출액|매출|영업이익|OP|순이익|지배순이익|NI|EPS)"
    r"\s*\(\s*(?P<horizon>\d{2,4}[EF]?)\s*\)\s+"
    r"(?P<a>[+-]?[\d,]+(?:\.\d+)?)\s+"
    r"(?P<b>[+-]?[\d,]+(?:\.\d+)?)"
    r"\s+(?P<dir>[▲▼\-—–])"
)

# Side-anchor target price pattern (audit-only; never primary). Indicator
# also required for symmetry with the metric pattern.
_SIDE_ANCHOR_TARGET_PRICE_RE = re.compile(
    r"목표주가\s+"
    r"(?P<a>[+-]?[\d,]+(?:\.\d+)?)\s+"
    r"(?P<b>[+-]?[\d,]+(?:\.\d+)?)"
    r"\s+(?P<dir>[▲▼\-—–])"
)


def _normalize_horizon(token: str) -> str:
    """Two-digit year tokens like '26E' → '2026E'; pass through 4-digit."""
    if not token:
        return token
    m = re.match(r"^(\d{2,4})([EF]?)$", token)
    if not m:
        return token
    yr, suffix = m.group(1), m.group(2)
    if len(yr) == 2:
        yr = "20" + yr
    return yr + suffix


def _resolve_old_new_with_indicator(a: str, b: str, indicator: str | None) -> tuple[str, str] | None:
    """Given a side-anchor row's two number tokens and an optional ▲/▼
    indicator, return (old, new). If the indicator contradicts the natural
    column order (e.g. ▲ but a < b), swap so old/new align with the
    indicator. Returns None when the indicator is ambiguous AND both
    numbers fail to parse to finite floats.
    """
    a_n = parse_numeric(a)
    b_n = parse_numeric(b)
    # Default convention: first=new, second=old.
    if a_n is None or b_n is None:
        return None
    if indicator in ("▲",):
        return (b, a) if a_n >= b_n else (a, b)  # ensure new > old
    if indicator in ("▼",):
        return (b, a) if a_n <= b_n else (a, b)  # ensure new < old
    # No indicator OR flat marker: trust column order (first=new, second=old).
    return (b, a)


def parse_side_anchor_revision_rows(text: str) -> tuple[dict[str, dict], str]:
    """Scan every line for the '<metric>(<year>) <a> <b> [▲|▼]' side-anchor
    pattern that real WiseReport PDFs use when pdfplumber folds the right-hand
    revision panel into body lines. Returns (metrics, horizon).

    First side-anchor occurrence per metric wins. The horizon returned is the
    earliest forward-year token attached to the highest-priority metric, after
    PRIMARY_METRIC_PRIORITY ordering.
    """
    if not isinstance(text, str):
        return {}, ""
    metrics: dict[str, dict] = {}
    metric_horizons: dict[str, str] = {}
    for line in text.splitlines():
        for m in _SIDE_ANCHOR_METRIC_RE.finditer(line):
            label = m.group("metric")
            metric_name = METRIC_ALIASES.get(label) or METRIC_ALIASES.get(label.lower())
            if metric_name is None or metric_name in metrics:
                continue
            old_new = _resolve_old_new_with_indicator(
                m.group("a"), m.group("b"), m.group("dir")
            )
            if old_new is None:
                continue
            old, new = old_new
            metrics[metric_name] = {"old": old, "new": new}
            metric_horizons[metric_name] = _normalize_horizon(m.group("horizon"))

    # Pick a representative horizon from the highest-priority metric.
    horizon = ""
    for m in PRIMARY_METRIC_PRIORITY:
        if m in metric_horizons:
            horizon = metric_horizons[m]
            break
    return metrics, horizon


def parse_target_price_side_anchor(text: str) -> dict | None:
    """Detect '목표주가 <a> <b> [▲|▼|-]' (no arrow) form and return
    {'old', 'new'} so the secondary-audit path picks it up. Returns None
    if not found or numbers don't parse."""
    if not isinstance(text, str):
        return None
    for line in text.splitlines():
        m = _SIDE_ANCHOR_TARGET_PRICE_RE.search(line)
        if not m:
            continue
        old_new = _resolve_old_new_with_indicator(m.group("a"), m.group("b"), m.group("dir"))
        if old_new is None:
            continue
        old, new = old_new
        return {"old": old, "new": new}
    return None


def find_variant_estimate_table_window(text: str) -> tuple[int, int, str] | None:
    """Locate a column-revision window that uses 기존/변경, 변경 전/후, or
    직전/현재 instead of PR #17's 수정 후/전. Returns (start, end, kind) or
    None. Used as a fallback to PR #17's locator on broker templates with
    different label conventions.
    """
    if not isinstance(text, str):
        return None
    lines = text.splitlines()
    if not lines:
        return None
    # Find a header line containing BOTH an old-label and a new-label.
    header_idx = None
    matched_kind = None
    for i, line in enumerate(lines):
        for old_labs, new_labs, kind in _VARIANT_LABEL_PAIRS:
            if any(o in line for o in old_labs) and any(n in line for n in new_labs):
                header_idx = i
                matched_kind = kind
                break
        if header_idx is not None:
            break
    if header_idx is None:
        return None
    win_end = min(len(lines) - 1, header_idx + 40)
    return header_idx, win_end, matched_kind


def parse_before_after_variant_rows(
    text: str, *, start: int, end: int, variant_kind: str
) -> tuple[dict[str, dict], str]:
    """Walk a variant column-window (e.g. 기존/변경) and parse metric rows.

    Strategy: for each row that begins with a known metric label, look for
    two numeric columns adjacent to the header columns. We use the SAME
    column-index strategy as PR #17 (select_horizon_from_header to pick a
    forward year) BUT the column-meaning depends on header order, which
    varies by variant.

    Conservative: when we cannot confidently identify which column is 'old'
    vs 'new' (e.g. column count mismatch), return ({}, '') so caller falls
    through to gap_reason logic.
    """
    if not isinstance(text, str):
        return {}, ""
    lines = text.splitlines()[start:end + 1]
    if not lines:
        return {}, ""

    # Determine which side of the header carries 'new' vs 'old' for this variant.
    # By design _VARIANT_LABEL_PAIRS lists (old_labels, new_labels), so we
    # compare positions of any old_label vs any new_label within the header.
    header = lines[0]
    old_labs, new_labs, _ = next(
        triple for triple in _VARIANT_LABEL_PAIRS if triple[2] == variant_kind
    )
    old_pos = min((header.find(lab) for lab in old_labs if lab in header), default=-1)
    new_pos = min((header.find(lab) for lab in new_labs if lab in header), default=-1)
    if old_pos < 0 or new_pos < 0:
        return {}, ""
    new_first = new_pos < old_pos  # if 'new' appears before 'old' in header

    # Horizon: prefer YYYYE in header line, else default to "" (caller will
    # try parse_horizon).
    sel = select_horizon_from_header(header)
    horizon = sel[0] if sel else ""

    metrics: dict[str, dict] = {}
    for line in lines[1:]:
        s = line.strip()
        if not s:
            continue
        matched_label = None
        for label in _METRIC_LABEL_PREFIXES:
            if s.startswith(label):
                matched_label = label
                break
        if matched_label is None:
            continue
        rest = s[len(matched_label):]
        rest = re.sub(r"^\s*\([^)]*\)", "", rest)
        nums = _NUMBER_TOKEN_RE.findall(rest)
        if len(nums) < 2:
            continue
        # Two-column variant rows: take the first two numbers.
        a, b = nums[0], nums[1]
        if new_first:
            new_val, old_val = a, b
        else:
            old_val, new_val = a, b
        # Validate finite numerics; skip otherwise.
        if parse_numeric(old_val) is None or parse_numeric(new_val) is None:
            continue
        metric_name = METRIC_ALIASES[matched_label]
        if metric_name not in metrics:
            metrics[metric_name] = {"old": old_val, "new": new_val}
    return metrics, horizon


def parse_year_pivot_revision_rows(text: str) -> bool:
    """Detect a year-pivot forecast table that lists multiple year columns
    (e.g. 2024A 2025A 2026E) for metric rows but DOES NOT supply paired
    before/after data. Returns True when such a table is detected.

    The caller treats True as 'ambiguous_year_pivot' for gap_reason; we do
    NOT emit metrics from this table because old/new is undeterminable.
    """
    if not isinstance(text, str):
        return False
    for line in text.splitlines():
        # A line containing 3+ year-shaped tokens (e.g. '2024A 2025A 2026E')
        # is the typical forecast-table header.
        toks = _YEAR_HEADER_TOKEN_RE.findall(line)
        if len(toks) >= 3:
            return True
    return False
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
    p.add_argument("--debug-text-out", default=None,
                   help="(PR #13) Optional path to write the raw extracted text "
                        "from --pdf for inspection. MUST live outside the repo "
                        "(refused with exit 2 otherwise). Default: not written.")
    p.add_argument("--pdf-engine", dest="pdf_engine", default="auto",
                   choices=("auto", "pdfplumber", "pypdf"),
                   help="(PR #16) Deterministic PDF text extraction engine. "
                        "'auto' (default) tries pdfplumber first then falls back "
                        "to pypdf. Both are local-only — no OCR/Vision/API. If "
                        "neither is installed the parser exits 2 with install "
                        "guidance.")

    p.add_argument("--no-ocr", dest="ocr", action="store_false", default=False,
                   help="(default) Disable any OCR fallback. PR #12/#13 are "
                        "deterministic-only.")
    p.add_argument("--ocr", dest="ocr", action="store_true",
                   help="Refused in PR #12/#13. Reserved for a future cost-gated PR.")

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
                       date: str, pdf_engine: str | None = None) -> dict:
    """Parse a single PDF's pre-extracted text into a structured record.

    Returned dict:
        source_pdf_sha256, filename, broker, ticker_hint, horizon,
        metrics: {<metric>: {old: <raw>, new: <raw>}, ...},
        target_price: {old, new} | None,
        date, extraction_method, pdf_engine

    `pdf_engine` (PR #16) is one of None / "pdfplumber" / "pypdf" and
    indicates which deterministic extractor produced the input text. None
    means the text came from --text or --inventory + --text-dir (no PDF
    bytes touched by the parser).
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

    # Metrics: scan every line; first occurrence per metric wins (PR #12
    # 'old → new' arrow-pair form).
    metrics: dict[str, dict] = {}
    for line in text.splitlines():
        result = _try_extract_metric_line(line)
        if result is None:
            continue
        metric_name, old, new = result
        if metric_name not in metrics:
            metrics[metric_name] = {"old": old, "new": new}

    # PR #17: real-WiseReport revision-table layout. Runs ONLY on metrics
    # the PR #12 arrow scanner missed — so synthetic regression fixtures
    # (which match arrow-pair) keep their identical metrics dict.
    layout_metrics, layout_horizon = parse_revision_table_layout(text)
    for m, vals in layout_metrics.items():
        if m not in metrics:
            metrics[m] = vals

    # PR #18: variant column-window labels (기존/변경, 변경 전/후, 직전/현재).
    # Additive — only fills missing metrics. Tracks whether any variant
    # window was found, for gap_reason classification.
    variant_kind_seen: str | None = None
    variant_window = find_variant_estimate_table_window(text)
    variant_horizon = ""
    if variant_window is not None:
        v_start, v_end, v_kind = variant_window
        variant_kind_seen = v_kind
        v_metrics, v_horizon = parse_before_after_variant_rows(
            text, start=v_start, end=v_end, variant_kind=v_kind
        )
        for m, vals in v_metrics.items():
            if m not in metrics:
                metrics[m] = vals
        variant_horizon = v_horizon

    # PR #18: side-anchor row form (e.g. real WiseReport: '영업이익(26E) 251 201 ▲').
    side_metrics, side_horizon = parse_side_anchor_revision_rows(text)
    for m, vals in side_metrics.items():
        if m not in metrics:
            metrics[m] = vals

    # PR #18: side-anchor target price (e.g. '목표주가 190,000 120,000 ▲'); only
    # fills target_price if the existing arrow-form scan didn't.
    if target_price is None:
        tp_side = parse_target_price_side_anchor(text)
        if tp_side is not None:
            target_price = tp_side

    # Horizon precedence:
    # 1. PR #17 column-window horizon
    # 2. PR #18 variant-window horizon
    # 3. PR #18 side-anchor horizon (most-priority metric)
    # 4. existing parse_horizon (first bare/E/F token in raw text)
    if layout_horizon:
        horizon = layout_horizon
    elif variant_horizon:
        horizon = variant_horizon
    elif side_horizon:
        horizon = side_horizon
    # else: keep parse_horizon-derived horizon

    # PR #18: gap_reason classification — additive audit field on breakdown.
    gap_reason: str
    if not text or not text.strip():
        gap_reason = "empty_text"
    elif metrics:
        gap_reason = "parsed_metric_pair"
    else:
        # No metrics. Decide why.
        if target_price is not None:
            # Target-price-only is a meaningful state (PR #12 contract).
            gap_reason = "target_price_only"
        elif (find_estimate_revision_table_window(text) is not None
              or variant_kind_seen is not None):
            # We saw a revision-shaped window but couldn't pair old/new.
            gap_reason = "no_metric_pair"
        elif parse_year_pivot_revision_rows(text):
            # Forecast-only table without paired before/after data.
            gap_reason = "ambiguous_year_pivot"
        else:
            gap_reason = "no_revision_anchor"

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
        "pdf_engine": pdf_engine,
        "gap_reason": gap_reason,
        "variant_kind": variant_kind_seen,  # one of None / 'existing_changed' / etc.
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

    pdf_engine = parsed.get("pdf_engine")
    em = EXTRACTION_METHOD if not pdf_engine else f"{EXTRACTION_METHOD}+{pdf_engine}"
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
        "extraction_method": em,
        "source_key": sk,
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _build_breakdown(parsed: dict) -> dict:
    """Produce an audit-only per-PDF breakdown record covering EVERY metric
    found (not just the primary). Goes to estimate_table_breakdown.json.

    PR #18 adds two additive audit fields:
      * gap_reason — one of {parsed_metric_pair, no_revision_anchor,
        no_metric_pair, ambiguous_year_pivot, target_price_only,
        empty_text}. Used for next-PR scoping; never consumed downstream.
      * variant_kind — which variant column-window matched (if any).
    """
    pdf_engine = parsed.get("pdf_engine")
    em = EXTRACTION_METHOD if not pdf_engine else f"{EXTRACTION_METHOD}+{pdf_engine}"
    return {
        "source_pdf_sha256": parsed.get("source_pdf_sha256", ""),
        "filename": parsed.get("filename", ""),
        "broker": parsed.get("broker", ""),
        "ticker_hint": parsed.get("ticker_hint", ""),
        "horizon": parsed.get("horizon", ""),
        "metrics": parsed.get("metrics") or {},
        "target_price": parsed.get("target_price"),
        "primary_metric": select_primary_metric(parsed.get("metrics") or {}),
        "extraction_method": em,
        "pdf_engine": pdf_engine,
        "gap_reason": parsed.get("gap_reason"),
        "variant_kind": parsed.get("variant_kind"),
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _build_target_price_secondary(parsed: dict) -> dict | None:
    """Produce a target-price audit record, or None if the PDF has no
    parseable 목표주가 numeric pair.

    Recorded for EVERY PDF whose target-price line yielded two finite
    numbers, regardless of whether a primary metric row was emitted.
    The role is always `secondary_reference`; this file is NEVER consumed
    by merge_meta / build_report_estimate / rolling_append.

    Returns None if:
      * `parsed["target_price"]` is missing, or
      * either `old` or `new` fails to parse as a finite number
        (defense-in-depth — the parser already filters non-numeric pairs
         at extraction time, but we re-check here so audit data is always
         numerically valid).
    """
    tp = parsed.get("target_price")
    if not tp:
        return None
    if parse_numeric(tp.get("old")) is None or parse_numeric(tp.get("new")) is None:
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
        "pdf_engine": parsed.get("pdf_engine"),
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
    }


def _read_text_for_input(args: argparse.Namespace, *, filename_hint: str = "",
                         text_path: Path | None = None) -> str:
    if text_path is not None and text_path.is_file():
        return text_path.read_text(encoding="utf-8", errors="replace")
    return ""


def _engines_to_try(requested: str) -> list[str]:
    """Return the ordered list of engines `_read_pdf_text` will attempt.

    'pdfplumber' / 'pypdf' → just that one engine.
    'auto' → ['pdfplumber', 'pypdf'] — pdfplumber preferred for table
    fidelity; pypdf used as a lighter fallback when pdfplumber is missing
    or its native dep stack is broken (e.g. cffi/cryptography panic on
    cloud sandboxes).
    """
    if requested == "auto":
        return ["pdfplumber", "pypdf"]
    if requested in ("pdfplumber", "pypdf"):
        return [requested]
    raise ValueError(f"unknown --pdf-engine value: {requested!r}")


def _extract_with_pdfplumber(path: Path) -> tuple[str, str | None]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return "", "pdfplumber not installed (`pip install pdfplumber`)"
    except Exception as exc:  # pyo3 panic, broken native deps, etc.
        return "", f"pdfplumber import failed: {exc!r}"
    try:
        parts: list[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts), None
    except Exception as exc:
        return "", f"pdfplumber failed to read {path}: {exc!r}"


def _extract_with_pypdf(path: Path) -> tuple[str, str | None]:
    try:
        import pypdf  # type: ignore
    except ImportError:
        return "", "pypdf not installed (`pip install pypdf`)"
    except Exception as exc:  # cryptography native panic, etc.
        return "", f"pypdf import failed: {exc!r}"
    try:
        parts: list[str] = []
        reader = pypdf.PdfReader(str(path))
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts), None
    except Exception as exc:
        return "", f"pypdf failed to read {path}: {exc!r}"


def _read_pdf_text(path: Path, engines: list[str]) -> tuple[str, str | None, list[str]]:
    """Extract text using the first engine in `engines` that succeeds.

    Returns (text, used_engine_or_None, attempt_log). Each engine is tried
    in order; if it fails (import error or parse error), the next is tried.
    `attempt_log` is a list of strings like 'pdfplumber: <reason>' for
    every engine attempted; useful for stderr diagnostics in the iterator.

    NEVER calls OCR / Vision / network. Both pdfplumber and pypdf are
    local-only deterministic libraries. Empty extract_text() output is
    preserved verbatim — downstream parse_text_to_rows treats it as
    no-metric and the row is correctly audited as primary=None.
    """
    log: list[str] = []
    for eng in engines:
        if eng == "pdfplumber":
            text, err = _extract_with_pdfplumber(path)
        elif eng == "pypdf":
            text, err = _extract_with_pypdf(path)
        else:
            log.append(f"{eng}: unknown engine")
            continue
        if err is None:
            return text, eng, log
        log.append(f"{eng}: {err}")
    return "", None, log


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
        # PR #13/#16: deterministic-first, no-cost --pdf path via pdfplumber
        # and/or pypdf. No OCR / Vision / API. main()'s pre-flight has
        # confirmed at least one engine in --pdf-engine's request list is
        # importable; here we run them in order and fall through on failure.
        if count >= args.max_pdfs:
            return
        pp = Path(args.pdf).expanduser().resolve()
        if not pp.is_file():
            print(f"error: --pdf not found: {pp}", file=sys.stderr)
            return
        engines = _engines_to_try(args.pdf_engine)
        text, used, log = _read_pdf_text(pp, engines)
        for line in log:
            # Surface every engine attempt so operators can see why a
            # primary engine failed and the fallback ran. These lines
            # never include PDF body content.
            print(f"[pdf engine] {line}", file=sys.stderr)
        if used is None:
            print(
                f"error: --pdf engines exhausted ({', '.join(engines)}); "
                f"install at least one (`pip install pdfplumber` preferred, "
                f"`pip install pypdf` lighter). PR #16 does not call "
                f"OCR/Vision/API.",
                file=sys.stderr,
            )
            return
        if used != engines[0]:
            print(f"[pdf engine] fell back to {used} after primary failed",
                  file=sys.stderr)
        if args.debug_text_out:
            dbg = Path(args.debug_text_out).expanduser().resolve()
            if _is_inside_repo(dbg):
                print(f"error: --debug-text-out must live outside the repo "
                      f"(got {dbg})", file=sys.stderr)
                return
            dbg.parent.mkdir(parents=True, exist_ok=True)
            dbg.write_text(text, encoding="utf-8")
            print(f"[pdf] wrote extracted text to {dbg}", file=sys.stderr)
        # source_pdf_sha256 is the sha256 of the actual PDF bytes (not the
        # extracted text), so it joins with merge_meta keys cleanly.
        sha = hashlib.sha256(pp.read_bytes()).hexdigest()
        # Stash the engine on a per-call attribute so the main consumer
        # can thread it into parse_text_to_rows.
        args._chosen_engine = used
        yield text, sha, pp.name
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

    # PR #13 pre-flight for --debug-text-out (most specific check first so the
    # operator gets the clearest error if they accidentally aim it at the repo).
    if args.debug_text_out and not args.pdf:
        print("error: --debug-text-out is only meaningful with --pdf.",
              file=sys.stderr)
        return 2
    if args.debug_text_out:
        dbg = Path(args.debug_text_out).expanduser().resolve()
        if _is_inside_repo(dbg):
            print(f"error: --debug-text-out must live outside the repo "
                  f"(got {dbg})", file=sys.stderr)
            return 2

    # PR #13/#16 pre-flight for the --pdf path: hard-fail (exit 2) on missing
    # file, unknown engine choice, or no usable engine on the system.
    if args.pdf:
        pp = Path(args.pdf).expanduser().resolve()
        if not pp.is_file():
            print(f"error: --pdf not found: {pp}", file=sys.stderr)
            return 2
        try:
            engines = _engines_to_try(args.pdf_engine)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        # Probe each requested engine for importability. A pyo3/cffi panic
        # during import (cloud sandbox class of failures) is treated the
        # same as ImportError — the engine is unavailable for this run.
        usable: list[str] = []
        attempt_log: list[str] = []
        for eng in engines:
            try:
                __import__(eng)
                usable.append(eng)
            except ImportError as exc:
                attempt_log.append(f"{eng}: not installed ({exc})")
            except Exception as exc:
                attempt_log.append(f"{eng}: import failed ({type(exc).__name__})")
        if not usable:
            for line in attempt_log:
                print(f"[pdf engine] {line}", file=sys.stderr)
            print(
                "error: --pdf requires at least one of: "
                f"{', '.join(engines)}. Install via `pip install pdfplumber` "
                "(preferred) or `pip install pypdf` (lighter, PR #16 fallback). "
                "PR #16 does not call OCR/Vision/API; --text and --inventory "
                "paths remain available without any PDF library.",
                file=sys.stderr,
            )
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
        # When --pdf was used, _iter_inputs stashed the chosen engine on
        # args._chosen_engine; for --text and --inventory paths it stays
        # unset and pdf_engine remains None.
        engine = getattr(args, "_chosen_engine", None) if args.pdf else None
        parsed = parse_text_to_rows(text, source_pdf_sha256=sha,
                                    filename=fn, date=args.date,
                                    pdf_engine=engine)
        breakdown.append(_build_breakdown(parsed))

        row = project_structured_row(parsed, date=args.date)
        if row is not None:
            # Hard invariant: never emit direct_trade_signal=True.
            if row.get("direct_trade_signal") is not False:
                print(f"error: invariant violated — direct_trade_signal != False "
                      f"on emitted row for {fn}", file=sys.stderr)
                return 3
            structured.append(row)

        # Target-price audit is INDEPENDENT of primary emission. Every PDF
        # with a parseable 목표주가 numeric pair is recorded; PDFs whose
        # target-price line is absent or malformed are not. The primary
        # contract is unaffected — target price never becomes a primary
        # estimate row.
        tp = _build_target_price_secondary(parsed)
        if tp is not None:
            # Defensive: secondary records must also carry direct_trade_signal=False.
            if tp.get("direct_trade_signal") is not False:
                print(f"error: invariant violated — direct_trade_signal != False "
                      f"on secondary record for {fn}", file=sys.stderr)
                return 3
            secondary.append(tp)
            if row is None:
                target_price_only_count += 1
        elif row is None:
            # No primary AND no parseable target price → fully malformed input.
            malformed_count += 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] inputs parsed                  = {parsed_count} (cap {args.max_pdfs})")
    print(f"[{mode}] structured (primary emitted)   = {len(structured)}")
    print(f"[{mode}] breakdown (audit, all metrics) = {len(breakdown)}")
    print(f"[{mode}] target_price_secondary (audit) = {len(secondary)}  "
          f"(every PDF with parseable 목표주가 pair, primary or not)")
    print(f"[{mode}] target-price-only count        = {target_price_only_count}  "
          f"(no primary, secondary present)")
    print(f"[{mode}] no-metric / malformed count    = {malformed_count}  "
          f"(no primary AND no parseable target price)")
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
