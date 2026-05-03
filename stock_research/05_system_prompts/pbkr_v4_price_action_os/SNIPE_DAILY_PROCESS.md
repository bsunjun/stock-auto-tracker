# PBKR v4 — Snipe Daily Process

> Educational doctrine. Not advice. Not a signal source. Describes a
> human operating routine. Nothing in this document is intended to
> drive automated execution or to set any external system field truthy.

---

## 1. Purpose

The daily process — the "snipe" — is the execution surface of v4.
Every prior document defines *what* may be done; the snipe defines
*when* and *in what order* it is done during a session.

The process is deliberately rote. Discretion is reserved for the
small number of decision points; everything else is checklist.

---

## 2. Day Structure

| Block | Window (KST) | Purpose |
|---|---|---|
| Pre-open prep | 08:00 – 08:50 | Stage read, watchlist refresh, queue build |
| Opening discovery | 09:00 – 09:15 | Observe; do not transact (auction unsettled) |
| Primary window | 09:15 – 11:30 | Confirmation reads on snipe queue |
| Mid-day | 11:30 – 13:30 | Re-evaluate queue; light activity |
| Afternoon | 13:30 – 15:10 | Continued reads; structural exits if triggered |
| Closing window | 15:10 – 15:30 | No new entries; review end-of-day prints |
| Post-close | 15:30 – 17:00 | Journal, watchlist update, next-day prep |

Times are doctrinal defaults; operator may compress or expand by
explicit journal note, never by improvisation.

---

## 3. Pre-Open Prep (08:00 – 08:50)

Checklist:

1. Read overnight global tape and FX moves. Note material gaps in
   ADRs of large KOSPI constituents.
2. Read MCS-KR stage. If a transition is plausible today, mark the
   inputs to watch.
3. Refresh the watchlist:
   - Recompute provisional pivots for any names whose tape moved
     materially overnight in offshore proxies.
   - Demote any name whose thesis was invalidated by a fresh
     disclosure.
4. Build the **snipe queue**: the subset of the active watchlist
   whose pattern is within a defined proximity of its pivot today.
5. Compute current TOR and headroom. Cap the snipe queue at the
   number of new positions that headroom can support given default
   sizes.

The session does not begin without these five items completed and
logged.

---

## 4. Opening Discovery (09:00 – 09:15)

- No new entries. The opening cross often distorts pivots and
  spreads.
- Note any snipe-queue names that print materially through their
  pivot at the open. These are *demoted* for the session, not
  chased; the entry condition has degraded.
- Note any names that gap and then immediately reverse on heavy
  volume; these are tape evidence inputs for the structural read.

---

## 5. Primary Window (09:15 – 11:30)

For each snipe-queue name, evaluate:

1. Is the pivot being approached or tested?
2. Are the four confirmation requirements
   (`ENTRY_TACTICS_SPEC.md` §7) met simultaneously?
3. Does the group context still support the entry?
4. Does TOR still have headroom for the resulting size?

If all four are yes, a doctrinal entry is constructed (single
tranche, pre-defined stop). If any is no, the name remains on
watch.

Existing positions are simultaneously monitored:

- Risk-stop checks (intraday hard, EOD soft).
- Trim-condition checks against extension references.
- Time-stop window checks.

---

## 6. Mid-Day (11:30 – 13:30)

A common false-signal window. Doctrinal posture:

- Re-evaluate the snipe queue; demote names whose intraday
  structure has decayed.
- Permit entries only on names whose primary-window read was
  already a *near-yes* and whose mid-day print resolves it cleanly.
- No re-entry attempts on names that triggered a stop earlier in
  the session.

---

## 7. Afternoon (13:30 – 15:10)

- Continue snipe-queue reads.
- Structural exit triggers take priority over new-entry decisions.
- Pre-close in last 30 minutes: only structural and risk-stop
  actions; no fresh discretionary entries.

---

## 8. Closing Window (15:10 – 15:30)

- No new entries.
- Observe the closing-auction print for evidence of distribution
  vs. accumulation, but do not transact during the auction unless
  rebalancing a position whose stop was breached on the close.

---

## 9. Post-Close (15:30 – 17:00)

The journaling block. Mandatory entries:

1. End-of-session TOR, K, and per-stage allocation.
2. Each new position: entry pattern, pivot, stop, size, R, thesis.
3. Each exit: category, trigger evidence, residual stop, P&L,
   one-line lesson.
4. Each watchlist state transition with rationale.
5. Adherence note: where today deviated from the process, with the
   reason.

A session is not complete until the journal is written.

---

## 10. Weekly and Monthly Cadence

- **Weekly:** rescore the watchlist; review process-adherence notes;
  recompute correlation factors used by the sizing throttle.
- **Monthly:** recalibrate the operating-notebook thresholds (growth
  floors, liquidity tiers, K defaults) only if the prior month
  produced sufficient evidence of regime change. Calibration drift
  without evidence is non-doctrinal.
- **Quarterly:** full eligibility re-evaluation on publication of
  new financials.

---

## 11. Hard Constraints on the Snipe

- The snipe never transacts during circuit-breaker or sidecar
  conditions.
- The snipe never adds to a position whose risk stop has not
  migrated to at least cost.
- The snipe never relaxes a precondition because "the setup looks
  too good to miss."
- The snipe never produces an automated order. Every transaction
  is initiated by a human after a checklist pass.

---

## 12. What This Document Is Not

- Not a trade-of-the-day publication.
- Not a recommendation regarding any specific security.
- Not a system that emits `trade_signal` of any kind. The snipe is
  a human operating routine; nothing in it should set an external
  `direct_trade_signal` or equivalent flag truthy. Engine code is
  out of scope for v4 doctrine.
