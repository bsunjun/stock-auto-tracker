# PBKR v4 — Supreme Doctrine

> **Status:** Doctrinal reference. Educational and research-oriented framework.
> Nothing in this document constitutes investment advice or an actionable order.
> No content here is intended to be machine-consumed as an executable signal.

---

## 0. Purpose

PBKR v4 supersedes PBKR v3. Where v3 anchored decisions on **forward earnings
estimates** ("estimate-first"), v4 inverts the hierarchy and anchors decisions
on **observed price/volume behavior** ("price-action-first"). Growth in v4 is
neither a thesis-substitute nor a mere bonus point: growth is the
**structural edge** that classifies the *kind* of trade a name can become
(short-term, swing, position, leader) and shapes its conviction and size
ceiling, but it never starts a trade and never overrides tape evidence (see
`PBKR_V4_GROWTH_POLICY.md`).

This document defines the operating doctrine. Companion documents elaborate
each pillar.

---

## 1. The Three Inversions vs. v3

| Dimension | v3 (deprecated) | v4 (this doctrine) |
|---|---|---|
| Primary anchor | Estimate revisions and forward EPS | Price/volume structure on the tape |
| Role of growth | The thesis and the trigger | A structural edge: classifies trade type and shapes conviction / size ceiling |
| Role of risk | An afterthought sized to conviction | The first-class constraint sized before any thesis |

v4 is **price-action-first**, **growth-aware**, and **risk-first**. Anything
that contradicts these three principles is non-doctrinal.

---

## 2. The Five Pillars

1. **Tape Primacy.** The tape is the ground truth. Estimates, narratives, and
   models are interpretations of the tape; when they disagree with the tape,
   the tape wins until proven otherwise by subsequent tape.
2. **Growth as Structural Edge.** Growth is not an entry trigger and does
   not override tape, but it determines leader quality, conviction,
   holding-period bias, and size ceiling via `conviction_cap` and
   `setup_quality_cap`. Names without growth evidence may still be
   short-term trades; they cannot be classified as full-size leaders or
   position-trade leaders.
3. **Risk-First Sizing.** Position size is derived from a per-position risk
   budget and a portfolio-level Total Open Risk ceiling, not from conviction.
4. **Stage Awareness.** All tactics are conditional on the market cycle stage
   (see `MARKET_CYCLE_SYSTEM_KR.md`). The same setup means different things in
   different stages.
5. **Process Over Prediction.** Daily/weekly process is the unit of work.
   Outcomes are evaluated against process adherence, not against P&L alone.

---

## 3. Hierarchy of Evidence

When signals conflict, resolve top-down:

1. Index/regime stage (MCS-KR)
2. Group/sector behavior
3. Name-level price/volume structure
4. Liquidity profile
5. Trade-class assignment (growth-derived; see `PBKR_V4_GROWTH_POLICY.md` §4)
6. Narrative/catalyst
7. Estimate trajectory

Lower-tier evidence cannot override higher-tier evidence. v3 effectively
allowed (7) to override (3); v4 forbids this.

---

## 4. What v4 Removes from v3

- Estimate-revision-as-trigger.
- Conviction-weighted sizing.
- Narrative-led entries unsupported by tape.
- "Average down on quality" as a default reflex.
- Implicit pyramiding without a structural higher low.

## 5. What v4 Preserves from v3

- The discipline of written theses.
- The post-mortem cadence.
- The watchlist hygiene practices.
- The separation of research notes from execution notes.

---

## 6. Document Map

| Domain | Reference |
|---|---|
| Growth as structural edge / trade class | `PBKR_V4_GROWTH_POLICY.md` |
| Korean-market specifics | `PBKR_V4_KOREAN_MARKET_ADAPTATION.md` |
| Entry construction | `ENTRY_TACTICS_SPEC.md` |
| Exit and position management | `SELL_RULES_POSITION_MANAGEMENT.md` |
| Sizing and Total Open Risk | `POSITION_SIZING_TOTAL_OPEN_RISK.md` |
| Market cycle framework | `MARKET_CYCLE_SYSTEM_KR.md` |
| Screening and watchlist | `SCREENING_WATCHLIST_SYSTEM.md` |
| Daily process | `SNIPE_DAILY_PROCESS.md` |

---

## 7. Non-Goals and Disclaimers

- This doctrine does not produce automated orders.
- This doctrine does not emit `direct_trade_signal` or any equivalent
  machine-actionable flag. All references to entries and exits are
  educational descriptions of human decision rules.
- Backtests and historical references in companion documents are
  illustrative, not prescriptive.
- Nothing here should be interpreted as a recommendation regarding any
  specific security.

---

## 8. Versioning

- v4.0 — initial doctrine, supersedes v3.
- Future revisions require an explicit changelog entry and a rationale
  citing tape evidence, not opinion.
