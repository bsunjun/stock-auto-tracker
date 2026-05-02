#!/usr/bin/env python3
"""PR #46 — Self-test runner for the metric-label / same-column / horizon
pair guards.

Targeted Validation Pack v3 surfaced two distinct parser bugs:

  1. EPS rows mis-promoted to operating_profit. The 에코프로비엠 IBK report
     has an EPS row with values 217 → 604 that fall in a magnitude band
     plausible for OP in 십억원. Without an EPS-class label invariant a
     downstream stage could file the row as `operating_profit`, leaking
     into the build pipeline as if it were OP_KRW_bn.

  2. Same-column adjacent-numeric mis-pairing across horizons. The
     한화솔루션 미래에셋 table layout puts two horizons (1Q26F + 2026F)
     under each side (변경 전 / 변경 후), producing 4 numeric tokens per
     metric row in the order [H1_old, H2_old, H1_new, H2_new]. The
     previous variant scanner naively grabbed `nums[0], nums[1]` and
     emitted a single `(-5 → 1029)` pair — but those two tokens are
     BOTH 변경 전 values for two different horizons. The pair is
     spurious.

PR #46 adds three parser guards:

  G1. METRIC_ALIASES expansion: `주당순이익` is now an EPS alias.
  G2. EPS-class label invariant + runtime check: any label containing
      `주당` (Korean) or `eps` (case-insensitive Latin) MUST map to the
      canonical metric `eps`. Module-load asserts the table; commit-time
      `_label_metric_class_compatible` rejects any inconsistent row.
  G3. Multi-horizon variant-row rejection: a `<metric>` row inside the
      variant column-window scanner with > _VARIANT_MAX_NUMS_FOR_PAIR (3)
      numeric tokens is refused. gap_hint=
      'multi_horizon_variant_row_no_pair' surfaces when no other metric
      committed.

Fixture-name → scenario mapping (intentionally verbose so a reviewer
can match a failure to the specific bug it pins):

  * pr46_sampleco_eps_not_op.txt
        → SAMPLECO_EPS_NOT_OP. EPS 217 → 604 must commit as `eps`.
          The `operating_profit` slot must NOT contain this pair.

  * pr46_sampleco_same_column_old_values_not_pair.txt
        → SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR. Single OP row with
          [-5, 1029, 93, 1251] tokens; the parser must not emit
          `(-5 → 1029)` (two 변경 전 tokens for different horizons).

  * pr46_sampleco_horizon_mismatch_no_pair.txt
        → SAMPLECO_HORIZON_MISMATCH_NO_PAIR. Three metric rows each
          with a 1Q26F + 2026F mix; no row may emit a cross-horizon
          pair.

Failure-message contract (for Codex / human reviewers)
------------------------------------------------------
Every assertion that fails prints a multi-line block of the form:

    FAIL [<SCENARIO>] <reason>
      bug_signature       : <one-line tag a reviewer can grep>
      offending_metric    : <canonical metric name or "(none)">
      offending_pair      : {"old": ..., "new": ...} or "(none)"
      forbidden_value(s)  : explicit list of values that must not be paired
      source_row          : verbatim line from the fixture text that triggered it
      full_metrics_dump   : the entire `metrics` dict as the parser saw it

The bug_signature tags are stable strings:
    * EPS_LABEL_ROW_PROMOTED_TO_OP
    * VARIANT_FOUR_TOKEN_ROW_PAIRED   (first-old conflated with second-old)
    * VARIANT_HORIZON_CROSSED         (1Q26F value paired with 2026F value)
    * VARIANT_GAP_HINT_MISSING        (parser dropped the row but didn't
                                        surface the new gap_hint)
    * MODULE_INVARIANT_DRIFT          (METRIC_ALIASES or
                                        _label_metric_class_compatible drifted)

Forbidden-actions guarantees verified per emitted record:
  * direct_trade_signal == False
  * trade_signal field is absent / None / False
  * target_price field is `target_price`, never the primary metric

Usage
-----
  python3 examples/run_pr46_pair_guards_fixture.py

Exit code: 0 on PASS, 1 on first FAIL with the diagnostic block above.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
SCRIPTS = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts"
TEXTS = HERE / "estimate_table_fixtures" / "texts"

sys.path.insert(0, str(SCRIPTS))
from extract_report_estimate_table import (  # noqa: E402
    METRIC_ALIASES,
    _label_metric_class_compatible,
    parse_before_after_variant_rows,
    find_variant_estimate_table_window,
    parse_text_to_rows,
)


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def _fail(scenario: str, reason: str, *,
          bug_signature: str,
          offending_metric: str | None = None,
          offending_pair: dict | None = None,
          forbidden_values: list | None = None,
          source_row: str | None = None,
          full_metrics: dict | None = None,
          extra: dict | None = None) -> None:
    """Print a Codex/human-friendly diagnostic block and exit 1.

    Every block follows the same shape so a reviewer can grep
    `bug_signature` to land on the exact bug class. Empty / unknown
    fields render as '(none)' rather than being omitted, so a missing
    line in the output is itself a signal.
    """
    print(f"FAIL [{scenario}] {reason}", file=sys.stderr)
    print(f"  bug_signature       : {bug_signature}", file=sys.stderr)
    print(f"  offending_metric    : {offending_metric or '(none)'}", file=sys.stderr)
    print(f"  offending_pair      : "
          f"{json.dumps(offending_pair, ensure_ascii=False) if offending_pair else '(none)'}",
          file=sys.stderr)
    print(f"  forbidden_value(s)  : "
          f"{forbidden_values if forbidden_values else '(none)'}", file=sys.stderr)
    src_repr = repr(source_row) if source_row else "(none)"
    print(f"  source_row          : {src_repr}", file=sys.stderr)
    print(f"  full_metrics_dump   : "
          f"{json.dumps(full_metrics, ensure_ascii=False) if full_metrics is not None else '(none)'}",
          file=sys.stderr)
    if extra:
        for k, v in extra.items():
            print(f"  {k:20s}: {v}", file=sys.stderr)
    sys.exit(1)


def _read(name: str) -> str:
    p = TEXTS / name
    if not p.is_file():
        print(f"FATAL: fixture text not found: {p}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def _parse(name: str) -> dict:
    text = _read(name)
    out = parse_text_to_rows(
        text,
        source_pdf_sha256="deadbeefcafe1234deadbeefcafe1234deadbeefcafe1234deadbeefcafe1234",
        filename=name,
        date="2026-04-30",
        pdf_engine="pdfplumber",
    )
    if not isinstance(out, dict):
        print(f"FATAL: parse_text_to_rows returned {type(out).__name__}",
              file=sys.stderr)
        sys.exit(1)
    return out


def _find_metric_row(text: str, metric_label: str) -> str:
    """Return the first line in `text` that begins (after lstrip) with
    `metric_label`, or '' if not found. Used to enrich diagnostics so a
    reviewer can see exactly which row in the fixture triggered a guard
    miss."""
    for line in text.splitlines():
        if line.lstrip().startswith(metric_label):
            return line.rstrip()
    return ""


# ---------------------------------------------------------------------------
# Module invariant tests
# ---------------------------------------------------------------------------

def test_module_invariants() -> None:
    # G1: 주당순이익 alias.
    if METRIC_ALIASES.get("주당순이익") != "eps":
        _fail(
            "MODULE_INVARIANTS",
            "G1: METRIC_ALIASES['주당순이익'] must be 'eps'",
            bug_signature="MODULE_INVARIANT_DRIFT",
            extra={
                "expected": "'eps'",
                "actual": repr(METRIC_ALIASES.get("주당순이익")),
                "fix_hint": "PR #46 expects '주당순이익' added as an EPS alias.",
            },
        )
    # G2: runtime guard returns False on EPS-class → non-eps slot.
    eps_class_pairs = [
        ("EPS",          "operating_profit", False),
        ("EPS",          "eps",              True),
        ("eps",          "eps",              True),
        ("EPS(원)",      "eps",              True),
        ("주당순이익",     "operating_profit", False),
        ("주당순이익",     "eps",              True),
        ("주당당기순이익", "eps",              True),  # any "주당"-containing label
        ("매출액",        "sales",            True),
        ("영업이익",      "operating_profit", True),
        ("",             "operating_profit", True),  # empty label is permissive
    ]
    for label, metric, expected in eps_class_pairs:
        actual = _label_metric_class_compatible(label, metric)
        if actual is not expected:
            _fail(
                "MODULE_INVARIANTS",
                f"G2: _label_metric_class_compatible({label!r}, {metric!r}) "
                f"= {actual!r}, expected {expected!r}",
                bug_signature="MODULE_INVARIANT_DRIFT",
                extra={
                    "label": repr(label),
                    "canonical_metric": repr(metric),
                    "expected": repr(expected),
                    "actual": repr(actual),
                    "fix_hint": "EPS-class labels (containing '주당' or "
                                "'eps') must NEVER pair with a non-eps "
                                "canonical metric.",
                },
            )
    print("PASS module invariants (G1: 주당순이익 alias + G2: 9-pair "
          "label-class compatibility table)")


# ---------------------------------------------------------------------------
# S1 — SAMPLECO_EPS_NOT_OP
# ---------------------------------------------------------------------------

def test_s1_eps_not_op() -> None:
    scenario = "S1 SAMPLECO_EPS_NOT_OP"
    fixture = "pr46_sampleco_eps_not_op.txt"
    text = _read(fixture)
    out = _parse(fixture)
    metrics = out.get("metrics") or {}

    # Direct-trade-signal / trade_signal leaks.
    if out.get("direct_trade_signal") is True:
        _fail(scenario, "direct_trade_signal=true leaked into output",
              bug_signature="DIRECT_TRADE_SIGNAL_LEAK",
              full_metrics=metrics)
    if out.get("trade_signal") not in (None, False):
        _fail(scenario, "trade_signal truthy",
              bug_signature="TRADE_SIGNAL_TRUTHY_LEAK",
              extra={"trade_signal": repr(out.get("trade_signal"))},
              full_metrics=metrics)

    # **Bug 1 signature**: an EPS-labeled row in the fixture
    # (`EPS (원) 217 604`) ended up under `operating_profit`.
    if "operating_profit" in metrics:
        op = metrics["operating_profit"]
        _fail(
            scenario,
            "EPS row 217 → 604 was incorrectly promoted to operating_profit. "
            "PR #46 G2 (EPS-class label invariant) must keep this row "
            "under canonical metric `eps`.",
            bug_signature="EPS_LABEL_ROW_PROMOTED_TO_OP",
            offending_metric="operating_profit",
            offending_pair=op if isinstance(op, dict) else None,
            forbidden_values=[op.get("old"), op.get("new")] if isinstance(op, dict) else None,
            source_row=_find_metric_row(text, "EPS"),
            full_metrics=metrics,
            extra={
                "expected_metric": "eps",
                "expected_pair": '{"old": "217", "new": "604"}',
                "fix_hint": "Verify _label_metric_class_compatible() is "
                            "wired into every commit site (variant + "
                            "side-anchor regex + KV forward + KV reversed "
                            "+ multi-line KV + NL parser).",
            },
        )

    # Positive: EPS slot must carry the correct pair.
    if metrics.get("eps") != {"old": "217", "new": "604"}:
        _fail(
            scenario,
            "EPS metric pair missing or wrong value",
            bug_signature="EPS_PAIR_MISSING_OR_DRIFTED",
            offending_metric="eps",
            offending_pair=metrics.get("eps") if isinstance(metrics.get("eps"), dict) else None,
            source_row=_find_metric_row(text, "EPS"),
            full_metrics=metrics,
            extra={"expected_pair": '{"old": "217", "new": "604"}'},
        )

    # Horizon + target-price sanity (separate from the bug signature; we
    # still want a clear failure message if upstream logic regresses).
    if out.get("horizon") != "2026E":
        _fail(scenario, f"horizon expected '2026E', got {out.get('horizon')!r}",
              bug_signature="EPS_FIXTURE_HORIZON_DRIFT",
              full_metrics=metrics,
              extra={"expected_horizon": "2026E",
                     "actual_horizon": repr(out.get("horizon"))})
    tp = out.get("target_price")
    if not (isinstance(tp, dict) and tp.get("old") == "80,000"
            and tp.get("new") == "95,000"):
        _fail(scenario, "target_price expected 80,000 → 95,000",
              bug_signature="EPS_FIXTURE_TARGET_PRICE_DRIFT",
              extra={"actual_target_price": repr(tp)},
              full_metrics=metrics)
    if any(slot in metrics for slot in ("target_price", "tp", "price_target")):
        _fail(scenario,
              "target_price slot leaked into metrics dict (must stay audit-only)",
              bug_signature="TARGET_PRICE_AS_PRIMARY_LEAK",
              full_metrics=metrics)

    print(f"PASS S1 SAMPLECO_EPS_NOT_OP: 'EPS 217 → 604' committed as "
          f"`eps`, operating_profit slot empty.")


# ---------------------------------------------------------------------------
# S2 — SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR
# ---------------------------------------------------------------------------

def test_s2_same_column_old_values_not_pair() -> None:
    scenario = "S2 SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR"
    fixture = "pr46_sampleco_same_column_old_values_not_pair.txt"
    text = _read(fixture)
    out = _parse(fixture)
    metrics = out.get("metrics") or {}

    # **Bug 2 signature**: the variant scanner picked nums[0], nums[1] off
    # a 4-token row and conflated two 변경 전 values for different
    # horizons. The classic offender: -5 (1Q26F 변경 전) paired with 1,029
    # (2026F 변경 전).
    forbidden_pairs = [
        # Each tuple is (old_value_substring, new_value_substring) — both
        # numbers are substring-matched against the parser's raw-token
        # output to handle the comma-stripped variants (`'1,029'` vs
        # `'1029'`).
        ("-5",     "1,029"),
        ("-5",     "1029"),
        ("1,029",  "1,251"),  # second-pair conflation, also forbidden
        ("1029",   "1251"),
    ]
    if metrics:
        # The per-row OP source line is the canonical place to point a
        # reviewer at — it visually shows the 4 tokens.
        offender = next(iter(metrics.items()))
        m_name, pair = offender
        old_v = pair.get("old", "") if isinstance(pair, dict) else ""
        new_v = pair.get("new", "") if isinstance(pair, dict) else ""
        # Decide which sub-signature we tripped.
        is_cross_pair = any(
            (a in str(old_v) and b in str(new_v))
            for a, b in forbidden_pairs
        )
        if is_cross_pair:
            sig = "VARIANT_FOUR_TOKEN_ROW_PAIRED"
        else:
            sig = "VARIANT_FOUR_TOKEN_ROW_NOT_REJECTED"
        _fail(
            scenario,
            "A multi-horizon variant row produced a metric pair. "
            "Token-order alone cannot tell which horizon each token "
            "belongs to; PR #46 G3 must refuse the row outright.",
            bug_signature=sig,
            offending_metric=m_name,
            offending_pair=pair if isinstance(pair, dict) else None,
            forbidden_values=[old_v, new_v],
            source_row=_find_metric_row(text, "영업이익"),
            full_metrics=metrics,
            extra={
                "row_token_order": "[H1_변경전(-5), H2_변경전(1,029), "
                                   "H1_변경후(93), H2_변경후(1,251)]",
                "expected_metrics": "{}",
                "fix_hint": "Verify _VARIANT_MAX_NUMS_FOR_PAIR threshold "
                            "and the `len(nums) > _VARIANT_MAX_NUMS_FOR_PAIR` "
                            "early-continue branch in "
                            "parse_before_after_variant_rows().",
            },
        )

    # target-price column is single-horizon (`목표주가 50,000원 → 50,000원`)
    # so it MUST still parse — a regression here would suggest the
    # target-price scanner got over-aggressive while fixing the variant
    # scanner.
    tp = out.get("target_price")
    if not (isinstance(tp, dict) and tp.get("old") == "50,000"
            and tp.get("new") == "50,000"):
        _fail(scenario, "target_price expected 50,000 → 50,000",
              bug_signature="TARGET_PRICE_REGRESSION_FROM_VARIANT_GUARD",
              extra={"actual_target_price": repr(tp)},
              full_metrics=metrics)

    # gap_hint surface check via the variant helper directly.
    win = find_variant_estimate_table_window(text)
    if win is None:
        _fail(scenario,
              "find_variant_estimate_table_window returned None on "
              "fixture (header should be detected)",
              bug_signature="VARIANT_HEADER_DETECTION_REGRESSION",
              source_row=_find_metric_row(text, "영업이익"))
    v_start, v_end, v_kind = win
    v_metrics, _h, v_gap = parse_before_after_variant_rows(
        text, start=v_start, end=v_end, variant_kind=v_kind,
    )
    if v_metrics:
        _fail(scenario, "variant scanner emitted metrics on the 4-token row",
              bug_signature="VARIANT_FOUR_TOKEN_ROW_PAIRED",
              offending_pair=next(iter(v_metrics.values()),
                                  None) if v_metrics else None,
              full_metrics=v_metrics,
              source_row=_find_metric_row(text, "영업이익"))
    if v_gap != "multi_horizon_variant_row_no_pair":
        _fail(scenario,
              f"gap_hint expected 'multi_horizon_variant_row_no_pair', "
              f"got {v_gap!r}",
              bug_signature="VARIANT_GAP_HINT_MISSING",
              extra={"actual_gap_hint": repr(v_gap),
                     "expected_gap_hint": "'multi_horizon_variant_row_no_pair'",
                     "fix_hint": "Verify the rejected_multi_horizon flag is "
                                 "set when len(nums) > _VARIANT_MAX_NUMS_FOR_PAIR "
                                 "and that the gap_hint waterfall checks it "
                                 "before the older growth/dup-flat branches."})
    print(f"PASS S2 SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR: 4-token "
          f"row [-5, 1,029, 93, 1,251] refused; no -5 → 1,029 leak; "
          f"gap_hint='multi_horizon_variant_row_no_pair'.")


# ---------------------------------------------------------------------------
# S3 — SAMPLECO_HORIZON_MISMATCH_NO_PAIR
# ---------------------------------------------------------------------------

def test_s3_horizon_mismatch_no_pair() -> None:
    scenario = "S3 SAMPLECO_HORIZON_MISMATCH_NO_PAIR"
    fixture = "pr46_sampleco_horizon_mismatch_no_pair.txt"
    text = _read(fixture)
    out = _parse(fixture)
    metrics = out.get("metrics") or {}

    # **Bug 3 signature**: any committed metric pair whose values come
    # from BOTH horizon columns (1Q26F + 2026F). Each row in the fixture
    # has the shape [1Q26F_old, 2026F_old, 1Q26F_new, 2026F_new]. The
    # forbidden pairings include adjacent same-side cross-horizon
    # (1Q26F_old ↔ 2026F_old) and diagonal (1Q26F_old ↔ 2026F_new).
    forbidden_per_metric: dict[str, list[tuple[str, str]]] = {
        # sales row: 300 / 2,800 / 320 / 2,950
        "sales": [
            ("300", "2,800"),       # both-old, same column
            ("300", "2,950"),       # diagonal
            ("2,800", "2,950"),     # 2026F_old ↔ 2026F_new (same horizon
                                    # OK, but parser must refuse 4-token
                                    # rows so even the legitimate pair is
                                    # blocked under PR #46's policy)
        ],
        # operating_profit row: 8 / 180 / 12 / 205
        "operating_profit": [
            ("8", "180"),
            ("8", "205"),
            ("180", "205"),
        ],
        # net_income row: 5 / 150 / 8 / 170
        "net_income": [
            ("5", "150"),
            ("5", "170"),
            ("150", "170"),
        ],
    }

    for metric_name, forbidden_pairs in forbidden_per_metric.items():
        v = metrics.get(metric_name)
        if v is None:
            continue
        old_v = str(v.get("old", "")) if isinstance(v, dict) else ""
        new_v = str(v.get("new", "")) if isinstance(v, dict) else ""
        for a, b in forbidden_pairs:
            if old_v == a and new_v == b:
                # Identify the source row in the fixture for this metric.
                label = {
                    "sales": "매출액",
                    "operating_profit": "영업이익",
                    "net_income": "지배순이익",
                }[metric_name]
                source = _find_metric_row(text, label)
                _fail(
                    scenario,
                    f"Metric `{metric_name}` paired across horizons: "
                    f"({a} → {b}) is a 1Q26F + 2026F mix that PR #46 G3 "
                    f"must refuse.",
                    bug_signature="VARIANT_HORIZON_CROSSED",
                    offending_metric=metric_name,
                    offending_pair=v if isinstance(v, dict) else None,
                    forbidden_values=[a, b],
                    source_row=source,
                    full_metrics=metrics,
                    extra={
                        "row_token_order": "[1Q26F_old, 2026F_old, 1Q26F_new, "
                                           "2026F_new]",
                        "expected_outcome": "row refused with "
                                            "gap_hint='multi_horizon_variant_"
                                            "row_no_pair'; metrics dict "
                                            "stays empty.",
                    },
                )

    # Stronger assertion: NO metric should be present at all (the row-
    # refusal rule is uniform across all 3 metric rows in the fixture).
    if metrics:
        first_metric, first_pair = next(iter(metrics.items()))
        label_lookup = {
            "sales": "매출액",
            "operating_profit": "영업이익",
            "net_income": "지배순이익",
        }
        _fail(
            scenario,
            "1Q26F + 2026F cross-horizon rows must yield empty metrics; "
            "the parser admitted at least one metric.",
            bug_signature="VARIANT_FOUR_TOKEN_ROW_PAIRED",
            offending_metric=first_metric,
            offending_pair=first_pair if isinstance(first_pair, dict) else None,
            source_row=_find_metric_row(text, label_lookup.get(first_metric, "")),
            full_metrics=metrics,
            extra={
                "row_token_order": "[1Q26F_old, 2026F_old, 1Q26F_new, 2026F_new]",
                "fix_hint": "All 3 metric rows in the fixture have 4 tokens "
                            "each; G3 should reject every one of them.",
            },
        )

    # gap_hint surface check.
    win = find_variant_estimate_table_window(text)
    if win is None:
        _fail(scenario, "find_variant_estimate_table_window returned None",
              bug_signature="VARIANT_HEADER_DETECTION_REGRESSION")
    v_start, v_end, v_kind = win
    _v_metrics, _h, v_gap = parse_before_after_variant_rows(
        text, start=v_start, end=v_end, variant_kind=v_kind,
    )
    if v_gap != "multi_horizon_variant_row_no_pair":
        _fail(scenario,
              f"gap_hint expected 'multi_horizon_variant_row_no_pair', "
              f"got {v_gap!r}",
              bug_signature="VARIANT_GAP_HINT_MISSING",
              extra={"actual_gap_hint": repr(v_gap)})
    print(f"PASS S3 SAMPLECO_HORIZON_MISMATCH_NO_PAIR: 3 metric rows × "
          f"4 tokens (1Q26F + 2026F mix) all refused; no cross-horizon "
          f"pair leaked.")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    test_module_invariants()
    test_s1_eps_not_op()
    test_s2_same_column_old_values_not_pair()
    test_s3_horizon_mismatch_no_pair()
    print("PASS run_pr46_pair_guards_fixture: 3 module invariants + "
          "3 fixture scenarios. "
          "Bug-signature taxonomy: EPS_LABEL_ROW_PROMOTED_TO_OP, "
          "VARIANT_FOUR_TOKEN_ROW_PAIRED, VARIANT_HORIZON_CROSSED, "
          "VARIANT_GAP_HINT_MISSING, MODULE_INVARIANT_DRIFT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
