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

Three fixture scenarios drive the assertions below:

  S1. SAMPLECO_EPS_NOT_OP                           — EPS 217 → 604 must
                                                       commit as `eps`.
                                                       Operating-profit
                                                       slot must NOT
                                                       contain this pair.
  S2. SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR      — single OP row with
                                                       4 tokens; metrics
                                                       must be empty;
                                                       no `(-5 → 1029)`
                                                       leak.
  S3. SAMPLECO_HORIZON_MISMATCH_NO_PAIR             — sales / OP / NI
                                                       rows each with 4
                                                       tokens; metrics
                                                       must be empty.

Plus three module-level invariant smokes:
  * METRIC_ALIASES['주당순이익'] == 'eps'
  * _label_metric_class_compatible('EPS', 'operating_profit') is False
  * _label_metric_class_compatible('주당순이익', 'eps') is True

Forbidden-actions guarantees verified per emitted record:
  * direct_trade_signal == False
  * trade_signal field is absent / None / False
  * target_price field is `target_price`, never the primary metric

Usage
-----
  python3 examples/run_pr46_pair_guards_fixture.py

Exit code: 0 on PASS, 1 on first FAIL with descriptive stderr message.
"""
from __future__ import annotations

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


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _read(name: str) -> str:
    p = TEXTS / name
    if not p.is_file():
        _fail(f"fixture text not found: {p}")
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
        _fail(f"[{name}] parse_text_to_rows returned non-dict: {type(out).__name__}")
    return out


def _assert_no_trade_signal_leak(out: dict, scenario: str) -> None:
    if out.get("direct_trade_signal") is True:
        _fail(f"[{scenario}] direct_trade_signal=true leaked into output")
    ts = out.get("trade_signal")
    if ts not in (None, False):
        _fail(f"[{scenario}] trade_signal truthy: {ts!r}")


def _assert_target_price_not_promoted(out: dict, scenario: str) -> None:
    """target_price is audit-only and must NEVER show up as a primary
    metric. The parser already keeps it in a separate top-level field;
    we re-verify here as defense-in-depth."""
    metrics = out.get("metrics") or {}
    for slot in ("target_price", "tp", "price_target"):
        if slot in metrics:
            _fail(f"[{scenario}] target-price slot leaked into metrics dict: {slot}")


def test_module_invariants() -> None:
    # G1: 주당순이익 alias.
    if METRIC_ALIASES.get("주당순이익") != "eps":
        _fail(f"G1: METRIC_ALIASES['주당순이익'] expected 'eps', got "
              f"{METRIC_ALIASES.get('주당순이익')!r}")
    # G2: runtime guard.
    if _label_metric_class_compatible("EPS", "operating_profit") is not False:
        _fail("G2: _label_metric_class_compatible('EPS', 'operating_profit') "
              "must be False")
    if _label_metric_class_compatible("주당순이익", "operating_profit") is not False:
        _fail("G2: _label_metric_class_compatible('주당순이익', "
              "'operating_profit') must be False")
    if _label_metric_class_compatible("eps", "eps") is not True:
        _fail("G2: _label_metric_class_compatible('eps', 'eps') must be True")
    if _label_metric_class_compatible("주당순이익", "eps") is not True:
        _fail("G2: _label_metric_class_compatible('주당순이익', 'eps') must "
              "be True")
    if _label_metric_class_compatible("매출액", "sales") is not True:
        _fail("G2: _label_metric_class_compatible('매출액', 'sales') must "
              "be True")
    # Permissive on missing labels.
    if _label_metric_class_compatible("", "operating_profit") is not True:
        _fail("G2: empty label must permit any metric (column-window "
              "scanner has no per-row label)")
    print("PASS module invariants (G1 + G2)")


def test_s1_eps_not_op() -> None:
    out = _parse("pr46_sampleco_eps_not_op.txt")
    _assert_no_trade_signal_leak(out, "S1")
    _assert_target_price_not_promoted(out, "S1")
    metrics = out.get("metrics") or {}

    if "operating_profit" in metrics:
        _fail(f"S1: EPS row leaked into operating_profit slot: "
              f"{metrics['operating_profit']!r}")
    if metrics.get("eps") != {"old": "217", "new": "604"}:
        _fail(f"S1: EPS metric must be {{'old':'217','new':'604'}}, got "
              f"{metrics.get('eps')!r}")
    if out.get("horizon") != "2026E":
        _fail(f"S1: horizon expected '2026E', got {out.get('horizon')!r}")
    tp = out.get("target_price")
    if not (isinstance(tp, dict) and tp.get("old") == "80,000"
            and tp.get("new") == "95,000"):
        _fail(f"S1: target_price expected 80,000 → 95,000, got {tp!r}")
    print("PASS S1 SAMPLECO_EPS_NOT_OP")


def test_s2_same_column_old_values_not_pair() -> None:
    out = _parse("pr46_sampleco_same_column_old_values_not_pair.txt")
    _assert_no_trade_signal_leak(out, "S2")
    _assert_target_price_not_promoted(out, "S2")
    metrics = out.get("metrics") or {}

    # The bug case would have produced metrics['operating_profit'] =
    # {'old':'-5','new':'1,029'} — a (-5 → 1029) pair from same-column
    # 변경 전 tokens spanning two horizons.
    if metrics:
        _fail(f"S2: multi-horizon variant row must yield empty metrics; "
              f"got {metrics!r}")
    op = metrics.get("operating_profit")
    if op is not None:
        _fail(f"S2: operating_profit must be absent, got {op!r}")
    # The target-price section is single-horizon and unaffected.
    tp = out.get("target_price")
    if not (isinstance(tp, dict) and tp.get("old") == "50,000"
            and tp.get("new") == "50,000"):
        _fail(f"S2: target_price expected 50,000 → 50,000, got {tp!r}")

    # gap_hint surface check via the variant helper directly. We re-run
    # the variant scanner on the fixture text and assert it returned the
    # PR #46 hint when no metric committed.
    text = _read("pr46_sampleco_same_column_old_values_not_pair.txt")
    win = find_variant_estimate_table_window(text)
    if win is None:
        _fail("S2: find_variant_estimate_table_window returned None on "
              "fixture (header should be detected)")
    v_start, v_end, v_kind = win
    v_metrics, _h, v_gap = parse_before_after_variant_rows(
        text, start=v_start, end=v_end, variant_kind=v_kind,
    )
    if v_metrics:
        _fail(f"S2: variant scanner emitted metrics; got {v_metrics!r}")
    if v_gap != "multi_horizon_variant_row_no_pair":
        _fail(f"S2: gap_hint expected 'multi_horizon_variant_row_no_pair', "
              f"got {v_gap!r}")
    print("PASS S2 SAMPLECO_SAME_COLUMN_OLD_VALUES_NOT_PAIR")


def test_s3_horizon_mismatch_no_pair() -> None:
    out = _parse("pr46_sampleco_horizon_mismatch_no_pair.txt")
    _assert_no_trade_signal_leak(out, "S3")
    _assert_target_price_not_promoted(out, "S3")
    metrics = out.get("metrics") or {}

    if metrics:
        _fail(f"S3: 1Q26F + 2026F cross-horizon rows must yield empty "
              f"metrics; got {metrics!r}")
    for forbidden_value in ("300", "2,800", "8", "180", "5", "150"):
        # If the parser accidentally paired these, they would show up in
        # `old`/`new` slots. None of them should appear anywhere in a
        # metric pair.
        for v in metrics.values():
            if isinstance(v, dict):
                if v.get("old") == forbidden_value or v.get("new") == forbidden_value:
                    _fail(f"S3: forbidden cross-horizon value "
                          f"{forbidden_value!r} leaked into metrics: {v!r}")

    # gap_hint surface check.
    text = _read("pr46_sampleco_horizon_mismatch_no_pair.txt")
    win = find_variant_estimate_table_window(text)
    if win is None:
        _fail("S3: find_variant_estimate_table_window returned None")
    v_start, v_end, v_kind = win
    _v_metrics, _h, v_gap = parse_before_after_variant_rows(
        text, start=v_start, end=v_end, variant_kind=v_kind,
    )
    if v_gap != "multi_horizon_variant_row_no_pair":
        _fail(f"S3: gap_hint expected 'multi_horizon_variant_row_no_pair', "
              f"got {v_gap!r}")
    print("PASS S3 SAMPLECO_HORIZON_MISMATCH_NO_PAIR")


def main() -> int:
    test_module_invariants()
    test_s1_eps_not_op()
    test_s2_same_column_old_values_not_pair()
    test_s3_horizon_mismatch_no_pair()
    print("PASS run_pr46_pair_guards_fixture: 3 module invariants + "
          "3 fixture scenarios (G1 + G2 + G3 verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
