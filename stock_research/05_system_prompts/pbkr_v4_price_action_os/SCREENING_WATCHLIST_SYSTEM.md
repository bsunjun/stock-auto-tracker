# PBKR v4 — Screening and Watchlist System

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Purpose

The screening and watchlist system feeds eligible candidates to the
daily process (`SNIPE_DAILY_PROCESS.md`). It does not produce
positions; it produces *candidates that may, on a given session,
satisfy `ENTRY_TACTICS_SPEC.md`*.

v4 enforces three concentric layers of attention, each more
selective and each requiring more documentation than the last.

---

## 2. The Three-Layer Structure

```
Broad Universe (KR-listed equities)
    -> Weekly Universe (re-scored every weekend)
        -> Daily Focus List (1–3 ideal, max 5)
            -> Daily Snipe Queue (pivot proximity within session)
```

| Layer | Cadence | Cap | Required artifacts |
|---|---|---|---|
| Broad universe | Continuous | None | Eligibility filter applied automatically |
| Weekly universe | Weekly review | Soft cap, calibrated | Setup label + edge cited |
| Daily focus list | Daily, at pre-open | **Max 5; ideally 1–3** | Setup + entry tactic + stop + size plan |
| Daily snipe queue | Within-session | TOR-headroom-derived | Pivot-proximity flag + tactic readiness |

Names move from broad to weekly to daily by **explicit operator
promotion**, never by automatic ranking alone.

---

## 3. Eligibility Filter (Broad → Broad-Eligible)

Defined in `PBKR_V4_GROWTH_POLICY.md` (trade-class taxonomy and
disqualifications) and `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`
(designations, liquidity, capital events).

Names failing here are removed for the relevant period: a quarter
for trade-class disqualification, the duration of the condition for
KR-specific designations.

---

## 4. The Screen Set — Multiple Views

v4 runs multiple screens against the eligible universe; each screen
is a *radar*, not a transaction signal. Outputs feed the weekly
universe candidate pool.

### 4.1 Korean Deepvue-Style Screen

A composite screen emphasizing relative-strength rank, base-and-pivot
proximity, group strength, and liquidity tier. The Korean adaptation
substitutes the equivalent KR sector taxonomy and uses KOSPI/KOSDAQ
relative-strength references.

### 4.2 Gap on Volume Screen

Identifies sessions of material gap-up on volume materially above
trailing reference. **This is a future-setup radar, not an entry
signal.** A name surfaced by this screen becomes a candidate for a
later setup (e.g., the post-gap consolidation that may host an
entry tactic).

### 4.3 Stage 2 Leaders Screen

Filters for names whose tape state at the name level is Stage 2 with
a constructive structural posture, group leadership, and persistent
relative strength. This screen prioritizes the *position-trade* and
*leader* trade classes.

### 4.4 CANSLIM-Style Growth Screen — Treated as Leader-Quality
Screen

A growth-oriented screen emphasizing earnings acceleration, sales
acceleration, and operating-margin expansion. **In v4 this is a
leader-quality screen, not an entry trigger.** Surfacing on this
screen contributes to *trade class* and *conviction*, never to
timing.

---

## 5. Liquidity Filter

- Trailing 20-session median traded value above tier threshold.
- Touch spread below tier threshold (sampled outside auction
  windows).
- Free-float adequate relative to candidate position size.

Failing names are removed and re-evaluated only on a quarterly
liquidity recheck.

---

## 6. Structural Filter

Names are tagged with their current tape state:

- **Stage 1 / 2 / 3 / 4 at the name level.** The same four-stage
  taxonomy as MCS-KR, applied per name.
- **Setup proximity.** Whether the name is currently presenting a
  recognized setup (`ENTRY_TACTICS_SPEC.md` §4) and how close the
  setup is to producing a tactic-level trigger.
- **Group context.** Tag of the issuer's industry group and the
  current group state.

Only Stage 1 and Stage 2 names with a constructive setup advance to
the weekly universe by default. Stage 3 names are admitted only with
an explicit Reversal-of-Trend note. Stage 4 names are excluded.

---

## 7. Weekly Universe — Promotion Requirements

A name promotes from broad-eligible to the weekly universe only
when an operator writes:

1. The cited edge(s) (`ENTRY_TACTICS_SPEC.md` §3).
2. The setup currently presenting (`ENTRY_TACTICS_SPEC.md` §4).
3. A one-paragraph thesis.
4. The trade-class assignment (`PBKR_V4_GROWTH_POLICY.md` §4) and
   the growth evidence cited.
5. The next quarterly report date.

Without all five, a name remains on the screens and does not enter
the weekly universe.

---

## 8. Daily Focus List — Promotion Requirements

The daily focus list is the operator's prepared, attention-prioritized
short list for the upcoming session. **Capped at 5 names; ideally
1–3.**

A name on the daily focus list must additionally have:

1. A specific entry tactic chosen from `ENTRY_TACTICS_SPEC.md` §5.
2. Defined `trigger_level` and `failure_level` for the tactic.
3. Defined `stop_logic` and the resulting protective stop.
4. A computed initial `position_size` plan at current equity, with
   all caps applied (see `POSITION_SIZING_TOTAL_OPEN_RISK.md`).
5. A KR-market caveat note for the chosen tactic.

A name without all five is a *weekly-universe* name, not a daily
focus name. The cap is a forcing function: only the highest-quality
candidates with executable plans make the daily list.

---

## 9. Daily Snipe Queue

The snipe queue (built at pre-open) is the subset of the daily focus
list whose tactic is within a defined proximity of producing a
trigger today. It is governed entirely by `SNIPE_DAILY_PROCESS.md`
§3.

The snipe queue is bounded by Total Open Risk headroom, not by the
daily focus list cap; on days of saturated TOR the snipe queue may
be shorter than the focus list.

---

## 10. Watchlist Hygiene

- **Weekly review** rescores the weekly universe and demotes names
  whose thesis has materially weakened to a *cold* sub-list with a
  re-promotion trigger noted.
- **Modelbook**: every closed trade contributes a modelbook entry
  with chart, edge, setup, tactic, exit category, and one-line
  lesson. The modelbook is the operator's pattern memory and is
  reviewed during the weekly review.
- **Quarterly purge**: every name re-evaluated against the
  eligibility filter on the publication of new financials.

---

## 11. Watchlist States

| State | Meaning | Daily handling |
|---|---|---|
| Active | Thesis intact, daily focus list candidate | May enter snipe queue |
| Pending | Thesis intact but tactic not yet ready | Monitored, not in snipe queue |
| Cold | Thesis weakened, awaiting re-trigger | Out of queue; re-promotion criteria logged |
| Retired | Thesis invalidated | Removed; modelbook entry written |

State transitions are explicit operator decisions, logged in the
journal.

---

## 12. What This Document Is Not

- Not a list of names; this is a process specification.
- Not a screen ruleset that emits orders.
- Not a recommendation regarding any specific security.
- Not a signal source. No score, ranking, or watchlist state should
  set any external `trade_signal` field truthy.
