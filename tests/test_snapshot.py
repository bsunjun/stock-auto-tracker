from stock_auto_tracker.analyzer import build_snapshot
from stock_auto_tracker.config import load_watchlist
from stock_auto_tracker.provider import CsvPriceProvider


def test_build_snapshot_from_fixture():
    holdings = load_watchlist("config/watchlist.example.yaml")
    provider = CsvPriceProvider("tests/fixtures/prices_sample.csv")
    quotes = provider.fetch([holding.symbol for holding in holdings])

    rows = build_snapshot(holdings, quotes)

    assert len(rows) == 2
    assert rows[0].symbol == "005930.KS"
    assert rows[0].last_price == 73500
    assert rows[0].market_value == 735000
    assert round(rows[0].pnl_pct, 2) == 2.08
