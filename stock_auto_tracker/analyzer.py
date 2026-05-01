from __future__ import annotations

from stock_auto_tracker.models import Holding, PriceQuote, SnapshotRow


def build_snapshot(
    holdings: list[Holding],
    quotes: dict[str, PriceQuote],
) -> list[SnapshotRow]:
    rows: list[SnapshotRow] = []

    for holding in holdings:
        quote = quotes[holding.symbol]
        last = quote.last_price
        qty = holding.quantity
        market_value = qty * last

        pnl = None
        pnl_pct = None
        if holding.avg_price and qty:
            cost = holding.avg_price * qty
            pnl = market_value - cost
            pnl_pct = (last / holding.avg_price - 1.0) * 100

        stop_distance_pct = None
        if holding.stop_price:
            stop_distance_pct = (last / holding.stop_price - 1.0) * 100

        target_distance_pct = None
        if holding.target_price:
            target_distance_pct = (holding.target_price / last - 1.0) * 100

        rows.append(
            SnapshotRow(
                symbol=holding.symbol,
                name=holding.name,
                quantity=qty,
                avg_price=holding.avg_price,
                last_price=last,
                market_value=market_value,
                pnl=pnl,
                pnl_pct=pnl_pct,
                stop_price=holding.stop_price,
                stop_distance_pct=stop_distance_pct,
                target_price=holding.target_price,
                target_distance_pct=target_distance_pct,
                note=holding.note,
            )
        )

    return rows
