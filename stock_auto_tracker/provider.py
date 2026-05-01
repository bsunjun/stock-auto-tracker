from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from stock_auto_tracker.models import PriceQuote


class PriceProvider:
    def fetch(self, symbols: list[str]) -> dict[str, PriceQuote]:
        raise NotImplementedError


class YFinancePriceProvider(PriceProvider):
    def fetch(self, symbols: list[str]) -> dict[str, PriceQuote]:
        quotes: dict[str, PriceQuote] = {}

        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.get("last_price") or info.get("lastPrice")

            if price is None:
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise RuntimeError(f"No price data returned for {symbol}")
                price = float(hist["Close"].iloc[-1])

            quotes[symbol] = PriceQuote(
                symbol=symbol,
                last_price=float(price),
                currency=str(info.get("currency", "")),
                provider="yfinance",
            )

        return quotes


class CsvPriceProvider(PriceProvider):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, symbols: list[str]) -> dict[str, PriceQuote]:
        df = pd.read_csv(self.path)
        required = {"symbol", "last_price"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in offline price file: {sorted(missing)}")

        quotes: dict[str, PriceQuote] = {}
        for _, row in df.iterrows():
            symbol = str(row["symbol"]).strip()
            if symbol in symbols:
                quotes[symbol] = PriceQuote(
                    symbol=symbol,
                    last_price=float(row["last_price"]),
                    currency=str(row.get("currency", "")),
                    provider="csv",
                )

        missing_symbols = set(symbols) - set(quotes)
        if missing_symbols:
            raise RuntimeError(f"Missing offline prices for: {sorted(missing_symbols)}")

        return quotes
