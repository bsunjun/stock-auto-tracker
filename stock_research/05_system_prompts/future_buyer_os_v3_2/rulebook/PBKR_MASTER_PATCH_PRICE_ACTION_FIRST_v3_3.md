# PBKR Master Patch — Price-Action-First v3.3

**Type:** SUPERSEDE / PATCH document. Additive only.
**Supersedes:** the implicit estimates-first ordering in
`MASTER_TRADING_PRINCIPLES` (concept-level). No file is deleted.
**Authority:** binds the
**PBKR Future Buyer Momentum OS v3.2** prompts, runbooks, and review
states from v3.3 onward.

> `direct_trade_signal = false`
> `trade_signal = null`
> `human_gate_required = true`

---

## 1. What this patch changes (delta)

| topic | v3.2 (implicit) | v3.3 (this patch) |
|---|---|---|
| Primary signal | estimates / report momentum + price action | **price action** + volume + RS + setup |
| Estimates / WiseReport / news / Telegram | candidate-driving | **secondary edge booster only** |
| `op_revision_pct > 0` | implicitly mandatory for PB\_READY | **NOT required** |
| Core entry | undefined / various | **breakout → first low-risk pullback** |
| `PB_SCOUT` | flow/footprint observation | **price-action reconnaissance**: key support reclaim, key MA pullback, pivot reclaim |
| `PB_READY` | requires positive estimates / catalysts | requires **valid breakout/gapper/HV edge + constructive pullback** |
| `PB_TRIGGER` | catalyst-based promotion | **entry-tactic confirmation** (one of five) + risk gate + human gate |
| `PRE_BREAKOUT_WATCH` | watchlist | **watchlist; explicitly NOT a buy** |
| Official risk flags | strong filter | **hard veto** |
| Position sizing | implicit | research scope; principles fixed: `stop_distance_pct` + `total_portfolio_risk` constraint |

## 2. Binding rules

1. **Price-action gate first.** Before estimates, news, Telegram, or
   broker reports are consulted, the price-action gate must pass:
   constructive structure, supportive volume, supportive RS,
   acceptable market cycle, acceptable institutional character.
2. **Secondary inputs cannot upgrade a name above `PB_SCOUT`.** They
   confirm; they do not initiate.
3. **A clean chart with no estimate revision is acceptable** for
   `PB_READY` so long as a valid breakout / gapper / HV edge has
   occurred and the pullback is constructive.
4. **A bullish estimate revision into a broken chart is rejected.**
   The chart wins.
5. **Every candidate at `PB_READY` or `PB_TRIGGER` must declare**
   `stop_distance_pct`, `stop_price`, and `invalidation_condition`.
6. **`official_risk_hard_exclude == true` is a hard veto.** No override.
7. **Auto-execution is forbidden.** Every `PB_TRIGGER` is a *review-
   completed* state, never an order.

## 3. Pack-level invariants

Every pack emitted by any prompt or schema influenced by this patch
must satisfy:

```yaml
direct_trade_signal: false
trade_signal: null
human_gate_required: true
doctrine_version: "v3.3"
required_per_candidate:
  - stop_distance_pct
  - stop_price
  - invalidation_condition
forbidden_per_candidate:
  - direct_trade_signal_true
  - trade_signal_truthy
  - "buy/sell directive language"
hard_veto:
  - official_risk_hard_exclude == true
```

## 4. Compatibility

- **No engine code is modified.** Parser, bridge, merge, build, emit,
  and ticker_map are untouched by this patch.
- **No real data is committed.** No PDFs, parquet, xlsx, output
  JSON/CSV.
- **No Drive call.** No write / rename / delete from this layer.
- **No promotion.** No latest / SuperPack / rolling --apply.
- **No secrets.** No API keys, tokens, passwords stored.

## 5. Conflict resolution with v3.2

Where any v3.2 prompt instructs an estimates-first ordering, the
following resolution rule applies at runtime:

> If a v3.2 prompt would elevate a name to `PB_READY` *because of*
> estimates/news/Telegram in the absence of a valid breakout/gapper/HV
> edge, the v3.3 doctrine **demotes** that name to `PB_SCOUT` until
> the price-action gate passes.

Authors of v3.2 prompts may choose to backport this resolution rule
inline. They are **not required** to delete or rewrite v3.2 prompts.

## 6. Documents bound by this patch

- `rulebook/TRADER_HANDBOOK_PRICE_ACTION_DOCTRINE_v3_3.md` — the
  doctrine text.
- `runbooks/SNIPE_PRICE_ACTION_DAILY_PROCESS_v3_3.md` — daily process.
- `runbooks/BREAKOUT_FIRST_PULLBACK_PLAYBOOK_v3_3.md` — core trade
  playbook.
- `project_prompts_patch/PRICE_ACTION_FIRST_PROJECT_PATCH_v3_3.md` —
  project-level prompt patch.

## 7. Audit hooks

The following statements must be **true** for any review surface
(human-facing message, generated pack, runbook output) bound by this
patch:

- `direct_trade_signal=true` count == 0
- truthy `trade_signal` count == 0
- buy/sell directive count (outside of explicit prohibition lists) == 0
- `PRE_BREAKOUT_WATCH treated as buy` count == 0
- `official_risk_hard_exclude=true` candidate emitted at `PB_READY`
  or above count == 0
- candidate without `stop_distance_pct` count at `PB_READY` or
  above == 0
