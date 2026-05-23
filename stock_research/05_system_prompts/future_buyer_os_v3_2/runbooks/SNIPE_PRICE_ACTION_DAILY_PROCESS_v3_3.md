# S.N.I.P.E. Daily Process — Price-Action First v3.3

**Doctrine:** `rulebook/TRADER_HANDBOOK_PRICE_ACTION_DOCTRINE_v3_3.md`
**Patch:** `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md`

> `direct_trade_signal = false` · `trade_signal = null` ·
> `human_gate_required = true`
>
> This runbook governs *review*. It does not authorize execution.
> Order entry is human and out-of-band.

---

## 0. Mandate

Each session, walk every candidate through the S.N.I.P.E. discipline
in order. Reject anything that fails an upstream letter; never let a
later letter *promote* a candidate past a failed earlier letter.

Order is **load-bearing**: S → N → I → P → E. Estimates / news /
Telegram (the **N** letter) are *secondary* and cannot rescue a
failure at **S** or **I**.

## 1. The five letters

### S — **Setup** (price action)

Identify which of the six structural setups the chart is showing:

| code | look for |
|---|---|
| HVE | initiating-thrust volume off a base or pivot |
| HV1 | day-1 highest-volume thrust in the prior N sessions |
| HVIPO | recent IPO carving its first base on rising volume |
| Gapper | constructive gap that holds with structure intact |
| Launch Pad | tight, low-vol consolidation pressed under resistance |
| Base Breakout | cup / handle / flat-base / VCP-style break of pivot |

**No setup → name does not enter the funnel.** A name without a
declared pivot is research, not a setup.

### N — **Narrative** (secondary; never primary)

Catalog any secondary edge:

- estimate revisions (`op_revision_pct`, `eps_revision_pct`)
- earnings surprise (`latest_op_surprise_pct`)
- WiseReport / broker coverage
- news-grounder output
- Telegram corroboration

Rules:

- **N may confirm S; N may not replace S.**
- A *positive N* without *valid S* is **not** a setup.
- A *negative N* with *valid S and I* downgrades sizing but does not
  veto on its own. Vetoes come from price action and from official
  risk flags.

### I — **Indicator** (price/volume/RS confirmation)

For the chosen S, verify:

- **Volume**: confirming on the breakout / gap / HV day; contracting
  on pullbacks; expanding on resumption.
- **Relative Strength**: `rs_60d` percentile in the leadership zone,
  or sector-relative RS leading the index.
- **Trend / MAs**: structure relative to EMA20 / EMA50 / EMA150
  consistent with the chosen setup (e.g., EMA50 holding for a
  late-stage pullback; EMA20 reclaim for a tight launch pad).
- **Pivot integrity**: the declared pivot has not been violated on
  closing basis.
- **Institutional character**: no distribution candles into resistance,
  consolidations on lower volume, advances on higher volume.

If I fails, the candidate cannot move past `PB_SCOUT` regardless of
N.

### P — **Plan** (entry / stop / invalidation / review milestones)

Declare, in writing, before any human-gate completion:

- entry tactic — exactly one of:
  - Key Support Reclaim
  - Consolidation Pivot Breakout
  - Key Moving Average Pullback
  - High Volume Close Pivot
  - Intraday Base Entry
- `stop_price` — the absolute level that invalidates the setup.
- `stop_distance_pct` — `(close − stop_price) / close × 100`.
- `invalidation_condition` — one-sentence structural description
  (e.g., "close below pivot on volume").
- review milestones — the structural points at which the plan will be
  re-examined (e.g., "first 3-day tight after entry", "test of EMA20").

Without all of the above, the candidate **cannot** reach `PB_TRIGGER`.

### E — **Execution** (human gate; out-of-band)

This OS does **not** execute. The E letter is the *human gate*:

- Confirm S, N (annotated), I, and P are documented.
- Confirm `official_risk_hard_exclude == false`.
- Confirm `stop_distance_pct` is within doctrine bounds (default
  `≤ 5%`; otherwise reduced sizing or reject).
- Confirm portfolio-level `total_portfolio_risk` budget would not be
  breached if the plan is filled.

If all confirmations pass, the candidate is marked `PB_TRIGGER`. The
operator then decides — **manually, out-of-band** — whether to enter.
The pack continues to assert `direct_trade_signal=false`,
`trade_signal=null`, `human_gate_required=true`.

## 2. Daily process (operator script)

1. **Cycle read** — note current market-cycle phase. Tighten gates if
   in correction.
2. **Universe pull** — start from the candidate-compression layer
   (PBKR Quant Feature Screener v1) survivor list.
3. **For each survivor, run S → N → I → P → E.** Stop at the first
   failure.
4. **State assignment** — at most one per ticker per session:
   - `PRE_BREAKOUT_WATCH` if S is forming but no entry pattern; **not
     a buy**
   - `PB_SCOUT` if S valid + I forming + risk gates pending
   - `PB_READY` if S valid + I confirmed + valid breakout/gapper/HV
     edge + constructive pullback in progress + risk gates declared
   - `PB_TRIGGER` if entry tactic confirmed + human gate completed
5. **Audit** — at end of session, run the audit checks of
   `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md §7`. Every
   value must remain at zero.
6. **Close-out** — write the day's review notes. Do not commit any
   real-data outputs to the repository.

## 3. State transitions (allowed only)

```
nothing
   │ S forming, no entry
   ▼
PRE_BREAKOUT_WATCH   — NOT a buy
   │ S valid + I forming
   ▼
PB_SCOUT             — reconnaissance only
   │ valid breakout/gapper/HV edge + constructive pullback + risk gates declared
   ▼
PB_READY             — review-ready, NOT an order
   │ entry tactic confirmed + human gate completed
   ▼
PB_TRIGGER           — review-completed, NOT an order
```

A candidate may **skip** levels downward (e.g., `PB_TRIGGER → PB_SCOUT`
on a structure failure) but may not **skip** upward without re-running
the full S → N → I → P → E sequence.

## 4. What this runbook never authorizes

- ✗ auto-execution
- ✗ `direct_trade_signal=true` in any artifact
- ✗ truthy `trade_signal` in any artifact
- ✗ "지금 매수", "사라", "팔라", "강력매수" or any directive trade
  language outside of explicit prohibition documentation
- ✗ promoting outputs to `latest`, `SuperPack`, or `rolling --apply`
- ✗ committing real PDFs, output JSON/CSV, parquet, or xlsx
- ✗ Drive write / rename / delete
- ✗ storing API keys / tokens / passwords / secrets
- ✗ modifying parser / bridge / merge / build / emit / ticker_map
  engines

## 5. Sanity invariants (per session)

```yaml
session_invariants:
  doctrine_version: "v3.3"
  direct_trade_signal: false
  trade_signal: null
  human_gate_required: true
  per_candidate_required:
    PB_READY:
      - stop_distance_pct
      - stop_price
      - invalidation_condition
    PB_TRIGGER:
      - stop_distance_pct
      - stop_price
      - invalidation_condition
      - entry_tactic in {KSR, CPB, KMA, HVCP, IBE}
      - human_gate_completed: true
  hard_veto:
    - official_risk_hard_exclude == true
```
