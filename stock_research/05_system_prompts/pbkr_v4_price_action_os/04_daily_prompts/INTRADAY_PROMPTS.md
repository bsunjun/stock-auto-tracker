# Intraday Prompts (KST 09:00–15:30)

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null`.
> `human_gate_required = true`.

---

## 0. Purpose

The intraday block executes the snipe queue produced by
`MORNING_PROMPTS.md` against the live tape, while monitoring open
positions for trim, structural-exit, and risk-stop conditions.

---

## 1. Window Map

| Window | KST | Doctrinal posture |
|---|---|---|
| Opening auction | 09:00–09:15 | **Observe; do not transact.** |
| Primary | 09:15–11:30 | Confirmation reads on snipe queue; existing-position checks |
| Mid-day | 11:30–13:30 | Re-evaluate queue; only "near-yes from morning" entries permitted |
| Afternoon | 13:30–15:10 | Continued reads; structural exits priority |
| Closing window | 15:10–15:30 | **No new entries.** Structural / risk-stop only |

Times are doctrinal defaults (`SNIPE_DAILY_PROCESS.md` §2).

---

## 2. Primary-Window Per-Name Checklist (09:15–11:30)

For each name in the snipe queue, the operator answers four questions
in order:

1. **Pivot proximity:** is the entry tactic's `trigger_level` being
   approached or tested today?
2. **Confirmation:** are the four confirmation requirements
   (`ENTRY_TACTICS_SPEC.md` §7) — range expansion, volume confirmation,
   closing strength (or sustained intraday hold), no contradicting
   macro print — met simultaneously?
3. **Group/sector context:** does the issuer's group still support the
   entry?
4. **TOR headroom:** is `TOR_pct + R_new_pct ≤ K * TOR_ceiling_pct`
   still satisfied?

If all four are **yes**, a doctrinal entry is constructed (single
tranche, pre-defined stop). If any is **no**, the name remains on
watch. The operator records the per-question answer in the ticket
(`Daily_Focus_Ticket_Template.md`).

---

## 3. Existing-Position Per-Name Checklist (Continuous)

Run continuously through the primary, mid-day, and afternoon windows:

1. **Risk stop:** is the pre-defined stop level breached on a closing
   basis (or hard intraday margin)?
2. **Structural exit triggers** (`SELL_RULES_POSITION_MANAGEMENT.md`
   §4):
   - Failed higher-low?
   - Distribution print?
   - Two closes below the trade-class MA reference (21EMA for swing,
     50SMA / 10주선 for position)?
   - Entry-tactic `failure_level` breached?
   - Sector / group breakdown?
   - Key reversal bar?
3. **Trim into strength** (`SELL_RULES_POSITION_MANAGEMENT.md` §5.1):
   - +5% partial in Stage 1 / Stage 2?
   - R-multiple partial (1R / 2R / 3R)?
   - Base extension 20–25% partial?
   - Climax-style session?
4. **Trim into weakness** (`SELL_RULES_POSITION_MANAGEMENT.md` §5.2):
   - First close below MA reference (pre-empt second close)?
   - Failed higher-low test without clean reclaim?
5. **Time-stop window**: has the position failed to make a higher
   high or higher low above the entry trigger within the
   stage-dependent window?

Each affirmative answer triggers the corresponding action per
`SELL_RULES_POSITION_MANAGEMENT.md`. Each action is logged.

---

## 4. Mid-Day Window (11:30–13:30) — Restricted

- Re-evaluate snipe queue; demote names whose intraday structure has
  decayed.
- Permit a new entry **only** for names that were a *near-yes* in the
  primary window and whose mid-day print resolves the missing
  confirmation cleanly.
- No re-entry attempts on names that triggered a stop earlier in the
  session.

---

## 5. Closing Window (15:10–15:30) — No New Entries

- No new entries.
- Risk-stop and structural-exit actions still permitted, evaluated on
  the closing print.
- The closing-auction (`15:20–15:30`) print is observed for distribution
  vs. accumulation evidence; no transactions inside the auction unless
  rebalancing a position whose stop was breached on the close.

---

## 6. Hard Constraints (Apply Always)

- No transaction during a circuit-breaker or sidecar condition
  (`PBKR_V4_KOREAN_MARKET_ADAPTATION.md` §3).
- No transaction inside the opening auction
  (`09:00`–`09:15`).
- No transaction inside the closing auction
  (`15:20`–`15:30`) unless rebalancing for a stop breach.
- No add-on entry on a position whose stop has not migrated to at
  least breakeven (`SELL_RULES_POSITION_MANAGEMENT.md` §6).
- No relaxation of `trigger_level` / `failure_level` because the
  setup "looks good."

---

## 7. Live-Agent Use During the Day — Restrained

Live AI prompts during the trading day are minimized and bounded:

- **Auditor (Claude):** invoked only if a focus name is being
  considered for an *unanticipated* deviation from its ticket — for
  example, a setup transformation. The Auditor returns `pass` /
  `block` / `revise_required`. No transaction on `revise_required`.
- **NewsGrounder (Gemini):** invoked only if a material news print
  emerges intraday and a focus name's thesis depends on it.
- **Orchestrator (GPT):** **not invoked intraday**, except to
  re-validate the ticket against
  `PBKR_V4_ticket_schema.json` if the ticket is being modified.
- **Repo Automation (Claude Code):** invoked only for ticket
  validation; never to transact.

The intraday rule is: when in doubt, look at the tape, not at the
chat window.

---

## 8. Hard Vetoes (Refuse Always)

- "Just enter; we'll log it later." Refuse.
- "Skip the Auditor; the morning audit covered it." Refuse if the
  setup has materially changed.
- "Override the stop." Refuse.
- "Set the `direct_trade_signal` flag truthy and let it go." Refuse.

---

## 9. Failure Mode Recovery

- Stop-out on a name: log the exit, do not re-enter on the same
  pivot, write a 1-line lesson to the modelbook.
- Multiple consecutive stop-outs: tighten `K` per the drawdown
  governor (`POSITION_SIZING_TOTAL_OPEN_RISK.md` §12).
- Tape evidence contradicts a focus thesis: structural exit takes
  priority over the original ticket.
