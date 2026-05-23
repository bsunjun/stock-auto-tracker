# Price-Action-First Project Prompts Patch v3.3

**Type:** patch instructions for v3.2 project-level prompts under
`stock_research/05_system_prompts/future_buyer_os_v3_2/project_prompts/`.
**Status:** ADDITIVE. **No v3.2 prompt is deleted by this patch.**
This document tells operators *how to read* v3.2 prompts under v3.3
doctrine; it does not modify them in place.

> `direct_trade_signal = false` · `trade_signal = null` ·
> `human_gate_required = true`

---

## 1. Reading order at runtime

When any v3.2 project prompt is invoked, operators (human or model)
must apply the v3.3 doctrine *as a higher-priority lens* over the
v3.2 text:

1. Load the v3.2 project prompt as written.
2. Apply this v3.3 patch on top.
3. If a clause in the v3.2 prompt conflicts with §3 of this patch,
   the v3.3 clause **wins**.
4. If a clause is *additional* (i.e., not contradicted), keep it.

This is a *prompt-time* override, not a file rewrite.

## 2. Mapping table — v3.2 prompt phrasing → v3.3 reading

| if v3.2 prompt says... | v3.3 reading is... |
|---|---|
| "promote on positive estimate revision" | promote only if **price-action gate** passes; estimate revision is secondary confirmation |
| "primary signal: estimates / catalysts" | **primary signal**: price action / volume / RS / setup |
| "PB_READY requires positive op_revision_pct" | **rescinded** — PB_READY requires valid breakout/gapper/HV edge + constructive pullback |
| "watchlist = PRE_BREAKOUT_WATCH" | unchanged; **explicitly NOT a buy** |
| "use Telegram channel as a confirmation" | only as a *secondary* edge booster; never primary |
| "WiseReport summary required" | not required for PB_READY; useful as N (Narrative) under S.N.I.P.E. |

## 3. Clauses that **win** over any v3.2 text

The following clauses are binding regardless of v3.2 prompt wording:

1. The chart leads. Estimates / news / Telegram are secondary.
2. PB_READY requires a valid breakout / gapper / HV edge **plus** a
   constructive pullback. Estimate revision is not required.
3. PB_SCOUT means *price-action reconnaissance* — key support reclaim,
   key MA pullback, or pivot reclaim — under acceptable market and
   institutional character. Flow-only or news-only states are
   `PRE_BREAKOUT_WATCH`, not `PB_SCOUT`.
4. PB_TRIGGER requires confirmation of one of the five entry tactics
   (KSR, CPB, KMA, HVCP, IBE) **plus** human-gate completion.
5. PRE_BREAKOUT_WATCH is **not** a buy.
6. `official_risk_hard_exclude == true` is a **hard veto**.
7. Every candidate at `PB_READY` or above must declare
   `stop_distance_pct`, `stop_price`, `invalidation_condition`.
8. Position sizing is bounded at the portfolio level by
   `total_portfolio_risk`. Per-position sizing math is research scope
   for a follow-up; the bound is binding now.
9. No artifact may set `direct_trade_signal=true`.
10. No artifact may emit a truthy `trade_signal`.
11. No artifact may emit "지금 매수", "사라", "팔라", "강력매수", or
    any directive trade language outside of explicit prohibition
    documentation.

## 4. Pack-output contract (any prompt-emitted pack)

Any pack emitted under this patch must satisfy:

```yaml
schema_or_pack_envelope:
  doctrine_version: "v3.3"
  direct_trade_signal: false
  trade_signal: null
  human_gate_required: true

each_candidate_at_PB_READY_or_above:
  required:
    - stop_distance_pct
    - stop_price
    - invalidation_condition
    - setup.code in {HVE, HV1, HVIPO, GAPPER, LAUNCH_PAD, BASE_BREAKOUT}
    - plan.entry_tactic in {KSR, CPB, KMA, HVCP, IBE}
  forbidden:
    - direct_trade_signal: true
    - "trade_signal: BUY|SELL|STRONG_BUY"
    - "buy/sell/지금 매수/사라/팔라/강력매수 directive language"
  hard_veto:
    - official_risk_hard_exclude == true
```

## 5. Operational guardrails

This patch **must not**:

- modify parser / bridge / merge / build / emit / ticker_map engines;
- commit real market data, real PDFs, output JSON/CSV, parquet, or
  xlsx files;
- store API keys, tokens, passwords, or secrets;
- perform any Drive write / rename / delete;
- promote any output to `latest`, `SuperPack`, or `rolling --apply`
  paths;
- author any v3.2 prompt rewrites that would mark a candidate as a
  buy/sell directive.

## 6. Author checklist (when writing a v3.3-aware prompt)

Before merging any prompt that depends on this patch:

- [ ] doctrine_version field declared as `"v3.3"`
- [ ] `direct_trade_signal=false` asserted in every emitted pack
- [ ] `trade_signal` set to `null` in every emitted pack
- [ ] `human_gate_required=true` asserted in every emitted pack
- [ ] PB_READY definition cites breakout/gapper/HV edge + pullback,
      not estimates
- [ ] PB_SCOUT definition cites KSR / KMA / pivot-reclaim
      reconnaissance, not flow-only or news-only
- [ ] PB_TRIGGER definition cites one of the five entry tactics +
      human gate
- [ ] PRE_BREAKOUT_WATCH explicitly stated as **not** a buy
- [ ] official-risk hard veto preserved
- [ ] every PB_READY/PB_TRIGGER candidate carries
      `stop_distance_pct` / `stop_price` / `invalidation_condition`
- [ ] no real-data artifacts committed alongside
- [ ] no parser/bridge/merge/build/emit/ticker_map engine edits
- [ ] no Drive call introduced
- [ ] no `latest` / `SuperPack` / `rolling --apply` promotion
- [ ] forbidden-audit invariants from
      `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md §7`
      remain at zero

## 7. Cross-references

- Doctrine: `rulebook/TRADER_HANDBOOK_PRICE_ACTION_DOCTRINE_v3_3.md`
- Master patch: `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md`
- Daily process: `runbooks/SNIPE_PRICE_ACTION_DAILY_PROCESS_v3_3.md`
- Core playbook: `runbooks/BREAKOUT_FIRST_PULLBACK_PLAYBOOK_v3_3.md`

> Reading guidance: in any conflict between these documents and a
> v3.2 file, the v3.3 documents win. None of the v3.2 files are
> deleted. v3.3 is overlaid, not substituted by deletion.
