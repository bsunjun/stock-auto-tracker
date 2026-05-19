from __future__ import annotations

from stock_research.pbkr_v4_screening_builder.adapters.dart_fundamentals import load_dart_fundamentals
from stock_research.pbkr_v4_screening_builder.deepvue_presets import evaluate_deepvue_presets


def _trend(start: float, step: float, n: int = 340) -> list[float]:
    return [start + i * step for i in range(n)]


def test_deepvue_presets_marks_full_leader() -> None:
    aaa_closes = _trend(10, 1.0)
    universe = {
        "AAA": aaa_closes,
        "BBB": _trend(10, 0.4),
        "CCC": _trend(10, 0.2),
        "DDD": _trend(10, 0.1),
    }
    row = {
        "ticker": "AAA",
        "name": "Synthetic Leader",
        "close": aaa_closes[-1],
        "closes": aaa_closes,
        "volumes": [200_000] * len(aaa_closes),
        "highs": [c * 1.02 for c in aaa_closes],
        "lows": [c * 0.98 for c in aaa_closes],
        "high_52w": aaa_closes[-1] * 1.01,
        "low_52w": aaa_closes[0],
        "ma50": 340,
        "ma150": 320,
        "ma200": 300,
        "ma120": 330,
        "ma30w": 310,
        "ma40w": 290,
        "avg_trading_value_20d": 30_000_001,
        "avg_volume_50d": 200_000,
        "adr_pct_10d": 3.0,
        "adr_pct_1d": 2.0,
        "weinstein_stage": "2A",
        "security_type": "common_stock",
        "ipo_date": "2024-01-02",
    }
    fundamentals = [{
        "ticker": "AAA",
        "eps_growth_latest_qtr_pct": 30,
        "avg_eps_growth_last_3yrs_pct": 30,
        "eps_growth_next_qtr_pct": 25,
        "eps_surprise_latest_qtr_pct": 45,
        "sales_growth_latest_qtr_pct": 30,
        "sales_growth_next_qtr_pct": 25,
        "sales_latest_rptd_year_krw": 200_000_001,
        "sales_latest_rptd_qtr_krw": 30_000_001,
    }]

    pack = evaluate_deepvue_presets(
        kiwoom_rows=[row],
        dart_rows=fundamentals,
        universe=universe,
        ticker_to_industry={"AAA": "semi", "BBB": "auto", "CCC": "bio", "DDD": "bank"},
        usd_krw=1.0,
    )

    result = pack["results"][0]
    assert set(result["passed_presets"]) == {
        "stage_analysis_leaders",
        "canslim_growth",
        "minervini_trend_template",
        "deepvue_leaders",
    }
    assert pack["summary"]["deepvue_leaders"] == 1
    assert result["preset_results"]["stage_analysis_leaders"]["predicates"]["weinstein_stage_2_or_2a"] is True


def test_dart_adapter_accepts_common_aliases(tmp_path) -> None:
    path = tmp_path / "dart.json"
    path.write_text(
        """
        {"rows": [{
          "stock_code": "005930",
          "eps_yoy_q_pct": "31.5%",
          "eps_cagr_3y_pct": "28",
          "revenue_yoy_q_pct": "26",
          "annual_sales_krw": "200000000000"
        }]}
        """,
        encoding="utf-8",
    )
    pack = load_dart_fundamentals(path, "2026-05-11T15:30:00+09:00")
    row = pack["rows"][0]
    assert row["ticker"] == "005930"
    assert row["eps_growth_latest_qtr_pct"] == 31.5
    assert row["avg_eps_growth_last_3yrs_pct"] == 28.0
    assert row["sales_growth_latest_qtr_pct"] == 26.0
    assert row["sales_latest_rptd_year_krw"] == 200_000_000_000.0


def test_union_universe_includes_any_preset_pass_with_tags() -> None:
    universe = {
        "AAA": _trend(10, 1.0),
        "BBB": _trend(10, 0.2),
        "CCC": _trend(10, 0.1),
    }
    canslim_only = {
        "ticker": "AAA",
        "name": "CANSLIM Only",
        "close": universe["AAA"][-1],
        "closes": universe["AAA"],
        "volumes": [200_000] * len(universe["AAA"]),
        "high_52w": universe["AAA"][-1] * 1.01,
        "low_52w": universe["AAA"][0],
        "ma50": 80,
        "ma150": 90,
        "ma200": 100,
        "security_type": "common_stock",
    }
    no_pass = {
        "ticker": "BBB",
        "name": "No Pass",
        "close": universe["BBB"][-1],
        "closes": universe["BBB"],
        "volumes": [10_000] * len(universe["BBB"]),
        "high_52w": universe["BBB"][-1] * 2,
        "low_52w": universe["BBB"][0],
        "security_type": "common_stock",
    }
    fundamentals = [{
        "ticker": "AAA",
        "eps_growth_latest_qtr_pct": 30,
        "avg_eps_growth_last_3yrs_pct": 30,
        "sales_growth_latest_qtr_pct": 30,
    }]

    pack = evaluate_deepvue_presets(
        kiwoom_rows=[canslim_only, no_pass],
        dart_rows=fundamentals,
        universe=universe,
        usd_krw=1.0,
    )

    assert pack["summary"]["union_universe"] == 1
    assert [row["ticker"] for row in pack["universe"]] == ["AAA"]
    assert pack["universe"][0]["filter_tags"] == ["preset:canslim_growth"]
    assert "canslim_growth:eps_growth_latest_qtr_gt_25pct" in pack["universe"][0]["passed_predicate_tags"]
    by_ticker = {row["ticker"]: row for row in pack["results"]}
    assert by_ticker["AAA"]["in_union_universe"] is True
    assert by_ticker["BBB"]["in_union_universe"] is False
