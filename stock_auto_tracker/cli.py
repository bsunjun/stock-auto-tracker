from __future__ import annotations

import argparse

import pandas as pd

from stock_auto_tracker.analyzer import build_snapshot
from stock_auto_tracker.config import load_watchlist
from stock_auto_tracker.provider import CsvPriceProvider, YFinancePriceProvider
from stock_auto_tracker.storage import save_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(prog="stock-tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Create portfolio snapshot")
    snap.add_argument("--config", default="config/watchlist.yaml")
    snap.add_argument("--offline-prices", default=None)
    snap.add_argument("--output-dir", default="output/snapshots")

    args = parser.parse_args()

    if args.command == "snapshot":
        holdings = load_watchlist(args.config)
        symbols = [h.symbol for h in holdings]

        provider = CsvPriceProvider(args.offline_prices) if args.offline_prices else YFinancePriceProvider()
        quotes = provider.fetch(symbols)

        rows = build_snapshot(holdings, quotes)
        csv_path, json_path = save_snapshot(rows, args.output_dir)

        df = pd.DataFrame([row.__dict__ for row in rows])
        print(df.to_string(index=False))
        print(f"\nSaved: {csv_path}")
        print(f"Saved: {json_path}")


if __name__ == "__main__":
    main()
