# PBKR v4 — Korean Market Adaptation

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Why a Korean Adaptation

The Korean equity market (KOSPI, KOSDAQ, KONEX) has structural features
that distort tactics designed for US markets. v4 explicitly adapts to
those features rather than importing US-market defaults wholesale.

The adaptations below describe **rules of engagement**, not orders.

---

## 2. Session Structure

Korean cash sessions include a regular continuous session and pre/post
single-price call auctions. Doctrinal implications:

- Opening auction (`09:00` cross) often re-prices overnight news in a
  single print. Treat the first 10–15 minutes of the continuous session
  as a *price-discovery window*, not a confirmation window.
- Closing auction (`15:20–15:30`) drives index-tracking flow. Late-day
  structural interpretations should down-weight the last 10 minutes.
- Lunch break is no longer in effect, but volume sag in the early
  afternoon is a real seasonality and should not be misread as a
  structural signal.

---

## 3. Daily Limits and Sidecars

Korean cash equities have a daily price limit of ±30% relative to the
prior close. Implications:

- Limit-up and limit-down prints compress information; structural
  patterns observed near the limits are unreliable until the next
  session re-opens with full two-sided liquidity.
- Sidecar and circuit-breaker triggers temporarily halt or constrain
  derivatives and program trading. Tape readings during these windows
  are degraded and should be treated as *non-evidence*.

---

## 4. Designations to Treat as Disqualifying

Names carrying any of the following exchange designations are
**ineligible** under the growth gate (see `PBKR_V4_GROWTH_POLICY.md`),
regardless of price action:

- Administrative issue (관리종목).
- Investment-attention / investment-warning / investment-risk
  (투자주의 / 투자경고 / 투자위험).
- Trading-halt pending disclosure clarification.
- Listing-eligibility-review status.

Reinstatement requires the formal removal of the designation, not the
passage of time.

---

## 5. Liquidity Floor

Doctrine sets a liquidity floor expressed in two simultaneous tests:

1. 20-session median traded value above a market-cap-tiered threshold.
2. Bid-ask spread at the touch, sampled outside the first/last 15
   minutes, below a tier-specific basis-point threshold.

Specific thresholds are calibrated in the operating notebook, not
hard-coded here, to keep this doctrine stable across regimes.

Names that fail liquidity are ineligible irrespective of growth or
tape quality. Slippage is a portfolio-level enemy, not a per-trade
nuisance.

---

## 6. Tax, Settlement, and Short-Sale Rules

- Cash equity settlement is T+2. Day-trip mechanics interact with this;
  doctrinal exits assume T+2 mechanics, not US-style T+1.
- Short-sale eligibility on Korean equities is restricted and varies
  over time. Doctrine treats short-sale tactics as **out of scope** for
  v4. v4 is a long-only operating doctrine.
- Securities transaction tax and any applicable financial investment
  income tax are treated as fixed friction in cost-of-trade
  estimates.

---

## 7. Disclosure Cadence

Korean issuers cluster mandatory disclosures around quarter-ends and
the AGM season (typically March). Doctrinal implications:

- Pre-disclosure windows (the trading days immediately before a known
  filing) are *event-risk windows*; new entries during these windows
  require an explicit event-risk note in the trade journal.
- AGM-season concentration of disclosures means watchlist re-scoring
  cadence should increase during March/April and August/November.

---

## 8. ETF and Index Mechanics

- KOSPI 200 / KOSDAQ 150 rebalances drive mechanical flows. These
  flows are tape *noise* relative to fundamental structure and should
  be discounted in pattern interpretation.
- Single-stock futures and ETF arbitrage can produce intraday divergences
  between cash and synthetic prices; cash tape remains the reference.

---

## 9. FX and Foreign-Investor Flow

- KRW/USD moves materially shift foreign-investor net flow, which in
  turn skews KOSPI large-cap tape. Doctrinal regime classification
  (see `MARKET_CYCLE_SYSTEM_KR.md`) incorporates a foreign-flow proxy.
- Foreign holdings ratio is tracked at the name level for liquidity-tier
  context; it is not a sizing input.

---

## 10. What This Document Does Not Do

- It does not provide live tickers, live designations, or live
  thresholds.
- It does not constitute a recommendation regarding any Korean issuer.
- It does not authorize any automated execution path.
