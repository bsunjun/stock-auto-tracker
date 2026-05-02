# Industry Report Handoff Prompts

These prompts hand the PR #41 industry-summary stub pack
(`phase3:industry_summary_pack_stub:v1`, see
`INDUSTRY_REPORT_LLM_SUMMARY_TEMPLATE.md`) off to three different
LLM agents in three different roles. **None** of the prompts permit
a buy / sell / target-price / position-size suggestion. **None** of
them are wired into the PR #29 chain runner / PR #38 emit step /
`rolling_append.py`. They are review-time tools only.

The stub generator (PR #41) does NOT call any of these LLMs. The
operator copies the stub markdown into a chat session, runs the
prompt, and reviews the returned JSON manually before any downstream
use. There is no automated chain that could silently produce a trade
signal from these prompts.

---

## 1. Gemini — Drive 산업 리포트 목록화 / 중복 제거 / 우선순위 선정

**Inputs**: a Drive folder URL of a `<root>/<YYYY-MM-DD>/산업/` directory
(or the listing JSON if Gemini does not have Drive access).
**Output**: a triaged list — duplicates collapsed, priority ordering
proposed.

```
You are reviewing a Google Drive folder containing Korean broker
INDUSTRY (산업) research PDFs for date YYYY-MM-DD. Your task is
strictly metadata triage.

Hard rules:
1. Do NOT open the PDF body. Use only filename, file size, and
   created/modified timestamps.
2. Do NOT produce any buy / sell / target-price / position-size
   suggestion. Do NOT suggest any individual ticker as a trade
   candidate.
3. Do NOT modify, rename, move, copy, or delete any Drive file.
4. Treat all output as review-only — it will be hand-checked before
   any downstream use.

Tasks:
A. List every PDF in the folder (filename only).
B. Collapse duplicates — group reports that share the same `[sector]`
   bracket AND the same `title` (case-insensitive, whitespace-collapsed).
   For each group, return ONE representative filename and the count.
C. Propose a priority ordering using these signals:
   - sector frequency (sectors with multiple reports today are
     probably "in motion" — rank higher)
   - filename keywords suggesting concrete data (`Weekly`, `Preview`,
     `Review`, `1Q`, `2Q`, `점검`, `동향`) — rank higher
   - filename keywords suggesting opinion-only (`전망`, `예상`,
     `시나리오`) — rank lower
D. For each priority entry, return:
   - filename
   - sector_hint (the `[bracket]` text)
   - 1-line rationale (why this rank)
   - reading_difficulty: low | medium | high
     (use file size as a proxy: <500KB = low, 500KB–1.5MB = medium, >1.5MB = high)

Output format: a single JSON array, one object per priority entry.
Schema: { filename, sector_hint, priority_rank, rationale, reading_difficulty }.
No prose outside the JSON.
```

---

## 2. Claude — PDF 본문 정밀 독해 후 template 채우기

**Inputs**: one stub record from `industry_summary_pack_stub.json` plus
the corresponding PDF (uploaded as an attachment).
**Output**: the same stub with all 11 analytic fields filled, status
flipped to `llm_summary_filled`, `missing_verification` empty.

```
You are filling a structured stub for a single Korean broker INDUSTRY
(산업) research PDF. The stub schema is
`phase3:industry_summary_pack_stub:v1`. Read it once at:
docs/INDUSTRY_REPORT_LLM_SUMMARY_TEMPLATE.md

Hard rules (any violation → return the stub UNMODIFIED with
`status: pending_llm_summary` and add an entry to
`missing_verification`):
1. `direct_trade_signal` MUST stay `false`. `trade_signal` MUST stay
   `null`. Do NOT add any field carrying a buy/sell/target-price/
   position-size value.
2. Do NOT modify the pre-filled metadata fields (`report_date`,
   `sector`, `report_title`, `source_file_basename`,
   `sha256_prefix_12`).
3. Do NOT include the report's text verbatim. Quote at most a short
   phrase (≤ 10 Korean characters) for attribution.
4. `beneficiary_candidates` MUST contain bare company names ONLY —
   no tickers, no directional verbs, no price targets, no `Top Pick`
   / `Bottom Pick` / `매수 추천` / `매도 권고`.
5. `risk_flags` MUST come directly from risks the report itself
   raises. Do NOT invent risks.
6. `earnings_revision_link_possible == true` ONLY if the report
   explicitly forecasts EPS / OP / sales revisions for ≥ 1 named
   company. Mention names in `beneficiary_candidates`.
7. `source_confidence` is YOUR confidence in YOUR extraction
   (NOT the report's stated confidence). Use 0.0–1.0; round to 2 dp.

Task:
- Read the attached PDF in full.
- Fill EVERY analytic field listed in
  INDUSTRY_REPORT_LLM_SUMMARY_TEMPLATE.md.
- Set `missing_verification` to the list of fields you could NOT
  populate. If empty, also set `status: llm_summary_filled`.
- Return the COMPLETE updated stub as a single JSON object. No prose
  outside the JSON.

If you cannot honor any of the hard rules, return the original stub
unchanged AND set `missing_verification` to the full list of analytic
field names. Explain WHY in `core_thesis` as a single short sentence.
```

---

## 3. ChatGPT — 산업 요약팩을 주도 업종 판단 입력으로만 사용

**Inputs**: the full `industry_summary_pack_stub.json` (with multiple
filled stubs from step 2).
**Output**: a sector-rotation context note — NOT trade-signal-adjacent.

```
You are reviewing a CONSOLIDATED industry-summary pack
(`phase3:industry_summary_pack_stub:v1`, multiple stubs). Your task
is sector-rotation CONTEXT, not portfolio construction.

Hard rules:
1. You MUST NOT emit any buy / sell / overweight / underweight /
   target-price / position-size / `top pick` / `bottom pick`
   suggestion for ANY individual company or sector.
2. Treat `beneficiary_candidates` as topology hints only, not as
   trade candidates. Do NOT echo them into a recommendation list.
3. Treat `risk_flags` as observed risks, not as short-sale hints.
4. The output is reviewed by a human before any downstream use.
   It is NOT consumed by any automated trading or rolling-append
   pipeline.

Task:
- Aggregate by `sector`. For each sector with ≥ 1 stub, summarize:
  * dominant_thesis: 1-line plain-language summary of the consensus
    (or "혼재" if the stubs disagree).
  * shared_demand_signal: 1-line — common demand observation across
    stubs in the same sector. Empty string if disjoint.
  * shared_risk_flag: 1-line — most-cited risk across stubs.
  * earnings_revision_link_possible_count: integer count of stubs
    in this sector with the field `true`.
  * sector_signal_density: integer = number of stubs in this sector.
- Then return a top-level array of sectors sorted by
  `sector_signal_density` descending, ties broken alphabetically.

Output format: single JSON array. No prose outside the JSON.
Schema per sector:
  { sector, dominant_thesis, shared_demand_signal, shared_risk_flag,
    earnings_revision_link_possible_count, sector_signal_density }.
```

---

## Acceptance test before any downstream use

For every returned stub or aggregated note, the operator must verify:

1. `direct_trade_signal == false` AND `trade_signal == null` on every
   stub (`grep '"direct_trade_signal":\s*true' /tmp/.../*.json` returns
   nothing).
2. No buy/sell verb appears in any field (`grep -E
   '매수|매도|비중확대|비중축소|Top Pick|Bottom Pick|target.?price|cut.?loss|take.?profit'`
   returns nothing).
3. `missing_verification` is well-formed; if `status ==
   llm_summary_filled`, the list is empty.
4. The pre-filled metadata fields are byte-identical to the original
   stub.

If any check fails, **the stub is rejected and discarded**. There is
no fallback path that promotes a malformed stub.
