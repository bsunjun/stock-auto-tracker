# PBKR v4 — Screening and Watchlist System

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Purpose

The screening and watchlist system feeds eligible candidates to the
daily process (`SNIPE_DAILY_PROCESS.md`). It does not produce
positions; it produces *candidates that may, on a given session,
satisfy `ENTRY_TACTICS_SPEC.md`*.

Screening and watchlist are intentionally separated:

- **Screening** is a wide, mostly automated reduction of the
  universe to a manageable candidate pool.
- **Watchlist** is a narrow, manually curated set with a written
  thesis per name.

Names move from screen to watchlist only after human review.

---

## 2. The Funnel

```
Universe (KR-listed equities)
    -> Eligibility filter (growth gate + KR adaptations)
        -> Liquidity filter
            -> Structural filter (tape state)
                -> Screen output (ranked list)
                    -> Manual review
                        -> Watchlist (with thesis)
                            -> Daily snipe queue
```

Each layer is *additive*: a name reaches the next layer only after
clearing the prior. The layers are intentionally ordered so that the
most expensive checks run on the smallest set.

---

## 3. Eligibility Filter

Defined in `PBKR_V4_GROWTH_POLICY.md` and
`PBKR_V4_KOREAN_MARKET_ADAPTATION.md`. Names failing here are
removed for the quarter (growth gate) or for the duration of the
disqualifying condition (KR-specific designations).

---

## 4. Liquidity Filter

- Trailing 20-session median traded value above tier threshold.
- Touch spread below tier threshold (sampled outside auction
  windows).
- Free-float adequate relative to candidate position size.

Failing names are removed and re-evaluated only on a quarterly
liquidity recheck.

---

## 5. Structural Filter

Names are tagged with their current tape state:

- **Stage 1 / 2 / 3 / 4 at the name level.** The same four-stage
  taxonomy as MCS-KR, applied per name.
- **Pattern proximity.** Whether the name is currently within a
  defined proximity of a doctrinal pattern pivot
  (`ENTRY_TACTICS_SPEC.md` §2).
- **Group context.** Tag of the issuer's industry group and the
  current group state.

Only Stage 1 and Stage 2 names with a constructive pattern proximity
advance to the screen output by default. Stage 3 names are admitted
only with an explicit RT note. Stage 4 names are excluded.

---

## 6. Ranking the Screen Output

Screen output is ranked by a doctrinal score that is **never**
exposed as an order signal. Inputs include:

- Pattern quality (clarity of base, tightness of consolidation,
  cleanness of pivot).
- Volume profile during the constructive structure.
- Group strength.
- Growth-floor margin (how comfortably the name cleared the gate).
- Liquidity headroom relative to default position size.

The score is a *prioritization aid for human review*. It does not
size, it does not time, and it does not authorize.

---

## 7. From Screen to Watchlist

A name promotes from the screen to the watchlist only when an
operator writes:

1. A one-paragraph thesis in plain language.
2. The doctrinal pattern label being watched.
3. The provisional pivot, stop, and resulting initial size at
   current equity.
4. The disqualifiers checked.
5. The next quarterly report date.

Without all five, a name remains on the screen and does not enter
the watchlist.

---

## 8. Watchlist Hygiene

- A maximum count cap on the active watchlist (calibrated in the
  operating notebook). Beyond the cap, lower-ranked names are
  pruned.
- Weekly re-scoring across the entire watchlist; names whose
  thesis has materially weakened are demoted to a *cold* sub-list
  with a re-promotion trigger noted.
- Quarterly purge: every name re-evaluated against the eligibility
  filter on the publication of new financials.

---

## 9. Watchlist States

| State | Meaning | Daily handling |
|---|---|---|
| Active | Thesis intact, pivot/stop current | Included in snipe queue |
| Pending | Thesis intact but pivot too far | Monitored, not in snipe queue |
| Cold | Thesis weakened, awaiting re-trigger | Out of queue; re-promotion criteria logged |
| Retired | Thesis invalidated | Removed; lessons logged |

State transitions are explicit operator decisions, logged in the
journal.

---

## 10. What This Document Is Not

- Not a list of names; this is a process specification.
- Not a screen ruleset that emits orders.
- Not a recommendation regarding any specific security.
- Not a signal source. No score, ranking, or watchlist state should
  set any external `trade_signal` field truthy.
