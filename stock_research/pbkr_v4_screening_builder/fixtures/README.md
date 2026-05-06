# Synthetic fixtures — PBKR v4 Screening Builder

These files are **synthetic**. Every ticker is anonymized
(`AAA.KS`, `BBB.KQ`, …) and every numeric series is hand-authored
to exercise specific code paths in the screening engine. They
contain **no real OHLCV, no real designation row, no real broker
response, and no API credentials**.

The doctrine forbids committing real data to the repo. These
fixtures exist only so that the screening builder can be exercised
end-to-end in CI and during development without needing a live
TradingView MCP server, a Kiwoom REST connection, or a KIND/DART
feed.

When you wire real adapters in, point the CLI at your local /
private path — never check the resulting JSON files into git.
