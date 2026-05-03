# PBKR v4 — Growth Policy

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Role of Growth in v4 — A Refined Statement

Growth in v4 is **not** a thesis-substitute, **not** an entry trigger, and
**not** a tape-override. But growth is not a mere bonus point either.

Growth is a **structural edge** that determines, for a name that has already
qualified on tape and risk grounds:

- **Leader quality** — whether the name is treated as a market leader or
  merely as a tradable mover.
- **Conviction** — how much weight the operator places on a constructive
  setup against ambiguous tape.
- **Holding period** — whether the position is managed as a swing, a
  position trade, or a leader-grade position trade.
- **Size cap** — the maximum tolerable position weight, via
  `conviction_cap` and `setup_quality_cap` (see
  `POSITION_SIZING_TOTAL_OPEN_RISK.md`).

In short: **growth does not start a trade, and growth does not size a trade
directly, but growth shapes the kind of trade a name can become.**

---

## 2. Three Operating Principles

1. **Growth is not an entry trigger.** No operator may enter a position
   because growth has accelerated; an entry tactic with a defined
   `trigger_level` and `failure_level` is required.
2. **Growth does not override tape or price action.** A growth-qualifying
   name with broken tape structure is not eligible. The tape ranks above
   the income statement (see `PBKR_V4_SUPREME_DOCTRINE.md` §3).
3. **Growth determines the *class* of trade, not the *event* of trade.**
   Without growth, a name can still be a short-term trade. Without growth,
   a name **cannot** be classified as a *full-size leader* or
   *position-trade leader*.

---

## 3. Growth Evidence — What Counts

The following are the recognized forms of growth evidence. Any single item
contributes; the combination is what classifies the name.

| Category | Examples |
|---|---|
| Income statement | Sales growth, EPS growth, operating profit growth, margin expansion |
| Operational momentum | Turnaround from prior contraction, ASP rise, shipment growth, capacity utilization rising |
| Forward visibility | Backlog / order growth, pipeline disclosures |
| Sell-side / consensus dynamics | Consensus upward revision, estimate-revision breadth improving |
| Disclosure events | Report cluster (multiple constructive disclosures in a short window), DART surprise |

Forecast-only categories (consensus / revisions) are accepted as **growth
evidence** but never as the sole basis for the leader-quality
classification (see §5).

---

## 4. Trade Class Taxonomy

Each candidate, once tape and risk preconditions hold, is classified as
one of the following:

| Class | Growth requirement | Default holding bias | Size posture |
|---|---|---|---|
| Short-term trade | None required | Days to a few weeks | Reduced `conviction_cap` |
| Swing trade | Some growth evidence (§3) | A few weeks | Standard `conviction_cap` |
| Position trade | Multi-category growth, multi-quarter | Multi-month | Full `conviction_cap` |
| Leader-grade position trade | Position-trade growth + leadership context (group/industry leadership, RS rank, durability) | Multi-month, allow trends to extend | Maximum `conviction_cap` and `setup_quality_cap` |

Names lacking growth evidence may still be traded as **short-term trades**.
They cannot be promoted to swing, position, or leader classes until growth
evidence emerges.

---

## 5. How Growth Influences Sizing — Indirectly

Growth never directly computes shares. It influences sizing via two
caps used by the sizing pipeline (see
`POSITION_SIZING_TOTAL_OPEN_RISK.md`):

- `conviction_cap` — modulated by growth strength and trade class.
- `setup_quality_cap` — modulated by setup cleanliness *and* the growth
  context that supports the setup's persistence.

The final position size remains the minimum of the risk-budget shares,
notional cap, liquidity cap, sector cap, conviction cap, and setup-quality
cap. Growth enters only through the latter two.

This preserves the v4 invariant: **stop sets the position size; growth
sets the position's ceiling and class.**

---

## 6. Anti-Goodhart Provisions

- One-off gains, asset disposals, and reversal of provisions are stripped
  before growth evidence is evaluated.
- A single blowout quarter is growth *evidence* but not, by itself,
  sufficient to classify a name as a leader-grade position trade.
- Aggressive accounting flags (receivables growing materially faster than
  revenue, inventory build outpacing COGS, capitalized R&D ratio rising)
  demote a name's leader-quality classification even if the headline
  growth qualifies.

---

## 7. Disqualifications (Independent of Growth)

A name is ineligible regardless of growth if any of the following holds:

- Going-concern qualification or modified audit opinion.
- Outstanding restatement or material accounting investigation.
- Liquidity below the floor defined in
  `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`.
- Designated as administrative-issue or investment-attention by the
  exchange (see Korean-market doc).
- Pending capital event (rights offering, large CB issuance) within a
  short window before/after the candidate entry, where dilution risk
  is non-trivial.

---

## 8. Re-Classification Cadence

- Trade-class classification is re-evaluated on each new quarterly
  publication.
- A class downgrade (leader → position → swing → short-term) takes effect
  immediately upon evidence loss.
- A class upgrade (short-term → swing → position → leader) requires the
  publication of new financials confirming the upgraded growth profile;
  tape strength alone does not trigger an upgrade.

---

## 9. Documentation Requirement

For each candidate, the watchlist record must contain:

1. Trade class assignment with the growth evidence cited (§3 categories).
2. The disqualification checks performed and their result.
3. Any soft-input notes (group leadership, RS context) that influenced
   the leader-quality decision.
4. The next quarterly report date, after which classification is
   re-evaluated.

Class assignments without this record are non-doctrinal.
