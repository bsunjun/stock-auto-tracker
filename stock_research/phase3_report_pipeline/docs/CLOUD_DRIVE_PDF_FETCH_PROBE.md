# Cloud-Drive PDF Fetch Probe (PR #15)

**This is a CAPABILITY PROBE runbook, not a parser PR.** The goal is to
discover — without violating the existing forbidden-action discipline —
whether a Claude Code cloud session can:

1. enumerate Google Drive files on the user's stock-research tree;
2. read file metadata (sha256 / size / mtime / name);
3. fetch a single raw PDF body to a workdir under `/tmp` for downstream
   parsing.

If raw fetch is **not** available the probe ends at the discovery step
and that finding is itself the deliverable. If raw fetch IS available,
the probe is allowed to download exactly **one** PDF, run
`extract_report_estimate_table.py --pdf` against it, and report
schema-aligned counters back. No PDF body, no extracted text, no
output JSON ever lands in the repo.

The companion paste-back schema lives in
[`CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md).

---

## Hard caps (PR #15 contract)

| Constraint | How it is enforced |
|---|---|
| `pdf_count == 1` (probe is single-PDF only) | Operator self-cap; the probe runbook stops after one PDF. The PR #11 selector's `--max 1` would make this mechanical if Drive is locally mounted. |
| Drive originals must NOT be modified, moved, or renamed | Probe uses **read-only** API surfaces only (search / metadata / download). No write/move/rename API calls are documented or executed. |
| OCR / Vision / API calls | `extract_report_estimate_table.py --ocr` is refused with exit 2 (PR #12/#13). Probe does NOT call any LLM or Vision API on the PDF body. |
| `latest` / promote / Super Pack | Out of scope; not invoked by anything PR #15 documents. |
| `rolling_append.py --apply` | Not invoked. The existing `--strict-estimate --dry-run` path inside `run_estimate_revision_dryrun.py` is the only rolling step considered. |
| `direct_trade_signal=true` rows | Phase3 invariant. PR #7 / #9 / #12 already refuse to write or proceed if violated. |
| Real-data commits to repo | `.gitignore` from PR #11 + operator self-check. PDF bytes / extracted text / output JSON / sha (full) NEVER paste-back; only counters. |

> PR #14 (operator-host smoke) and PR #15 (cloud-drive probe) are
> independent. Use whichever environment actually has Drive reachable.
> Where both are available, prefer PR #14 (Mac with mounted Drive)
> for routine work and reserve PR #15 for capability checks of the
> cloud session itself.

---

## Phase 0 — Capability discovery (NO PDF fetched yet)

Before downloading anything, enumerate what the running Claude Code
cloud session can actually do. Capture the answers in the
`drive_search_available` / `drive_metadata_available` /
`drive_raw_fetch_available` fields of the result template.

### 0.1 Identify the cloud_environment

Record the runtime label so future runs are comparable:

- model name + version (`Sonnet 4.6`, `Opus 4.7`, etc.)
- harness (`Claude Code cloud`, `Claude Desktop MCP`, ...)
- session id (last 8 chars only, e.g. `…abcd1234`)

### 0.2 Tool surface enumeration

Document, **without invoking**, which of the following are visible:

| Capability | Typical surface | What to record |
|---|---|---|
| Drive search | MCP server like `gdrive`, custom `search_files` tool, or no surface at all | tool name + true/false |
| File metadata | `get_file_metadata`, `list_recent_files` | tool name + true/false |
| Raw fetch | `download_file_content`, `read_file_content`, `mcp__gdrive__fetch` | tool name + true/false |
| Local mount | `/mnt/...` `gdrive` fuse, `$GOOGLE_DRIVE_ROOT` resolves | true/false |

An honest "no surface visible" outcome is the correct answer if that's
the truth — that is itself the probe's finding for this session.

### 0.3 Stop conditions

Stop the probe at Phase 0 (and only paste back the discovery fields)
if any of the following hold:

- No Drive search surface AND no metadata surface AND no raw fetch
  surface AND no local mount.
- Drive surface exists but the session lacks user-scoped credentials
  for the stock-research tree (don't try to broaden the scope —
  that's outside PR #15).
- Any tool would require running an operation other than read /
  metadata / download. (e.g., write, rename, move, share-permission
  change — all forbidden.)

---

## Phase 1 — Single-PDF metadata pull (read-only)

Only proceed when Phase 0 reported `drive_search_available=true` AND
`drive_metadata_available=true`. Use the available surface to:

1. Search the configured `<root>/<date>/기업/` location for `.pdf`
   filenames that match the WiseReport pattern
   (`YYYYMMDD_[종목명] 제목.pdf` from PR #11).
2. Pick **exactly one** file. The selection rule is the same as the
   selector script's: prefer a complete `[종목명]` block; if multiple
   match, pick the smallest-sha-prefix lexicographic order so the
   choice is deterministic across runs.
3. Record:
   - `pdf_filename_basename_only` — basename, never the full Drive
     path.
   - `pdf_sha256_prefix` — first 12 hex chars of the file sha256, if
     the metadata surface exposes it; otherwise leave `""` and set a
     note in `next_action`.

No fetch yet. If Phase 1 already exposes broker/ticker via filename,
PR #15 still does not parse it — that is Phase 2's job, gated on
`drive_raw_fetch_available=true`.

---

## Phase 2 — Single PDF raw fetch (only if Phase 0 cleared it)

Conditional on `drive_raw_fetch_available=true` AND Phase 1 produced
exactly one file. Steps:

```
mkdir -p /tmp/pr15_probe                      # workdir OUTSIDE the repo
# Use the cloud session's Drive download surface to write bytes to
# /tmp/pr15_probe/<basename>.pdf — never inside the repo.
# Compute a local sha256 of the downloaded bytes and confirm the
# prefix matches Phase 1 (a separate sanity check, not a security
# claim).
sha256sum /tmp/pr15_probe/<basename>.pdf | cut -c1-12
```

If the Drive surface refuses to download (access denied / quota /
unsupported MIME / etc.), Phase 2 stops here and the result template's
`next_action` records the obstacle. Do NOT widen the scope, retry with
elevated permissions, or fall back to OCR/Vision.

---

## Phase 3 — Run the deterministic parser (still cloud-side, no API)

Only when Phase 2 produced a local PDF. Try installing **either**
pdfplumber **or** pypdf (deterministic-only, no API cost). Both are
acceptable — PR #16 added pypdf as a lighter fallback for cloud
sandboxes where pdfplumber's native dep stack is broken (cffi /
cryptography panics under pyo3).

```
# Option A — preferred: pdfplumber (better table fidelity)
python3 -m pip install --user pdfplumber 2>&1 | tail -1
python3 -c "import pdfplumber; print(pdfplumber.__version__)"

# Option B — fallback: pypdf (lighter; PR #16). Use this if Option A
# crashes on import.
python3 -m pip install --user pypdf 2>&1 | tail -1
python3 -c "import pypdf; print(pypdf.__version__)"

# Run the parser with --pdf-engine auto (PR #16). It tries pdfplumber
# first then falls back to pypdf; either is fine. NO OCR / Vision / API.
python3 stock_research/phase3_report_pipeline/scripts/extract_report_estimate_table.py \
  --pdf /tmp/pr15_probe/<basename>.pdf \
  --pdf-engine auto \
  --date <YYYY-MM-DD> \
  --workdir /tmp/pr15_probe/_extract \
  --apply
```

Capture from the parser stdout / from
`/tmp/pr15_probe/_extract/structured_extraction.json` etc.:

- `pdfplumber_available` — true/false (record version too)
- `pypdf_available` — true/false (PR #16 fallback)
- `parser_exit_code`
- `structured_rows`, `breakdown_rows`, `target_price_secondary_rows`
- `direct_trade_signal_true_count` — **MUST be 0**; otherwise STOP and
  escalate

If parser_exit_code is 2 because BOTH pdfplumber AND pypdf are unavailable
in the cloud session and `pip install` cannot succeed there, that is a
valid Phase 3 outcome — record it and stop.

---

## Phase 4 — Optional chain via `run_estimate_revision_dryrun.py`

Only when Phase 3 produced a non-empty `structured_extraction.json`.
Feed it through the existing PR #9/#10 runner with a synthetic
1-record bridge_meta (same shape as
`examples/estimate_table_fixtures/bridge_meta.synthetic.json`) and
capture from `pipeline_summary.json`:

- `build_rows_accepted`
- `build_rows_rejected`
- `reject_reason_counts`
- `rolling validated/rejected/dup/to_add` (informational only — record
  whichever is most useful for the next-action narrative)
- `forbidden_actions_confirmed` — every entry MUST be 0

If the runner refuses (e.g., the cloud session can't produce a
synthetic bridge_meta because PR #15 explicitly avoids inventing
ticker codes for real names), Phase 4 may be skipped without it
counting as a probe failure. Record the reason in `next_action`.

---

## Phase 5 — Fill the result template, paste back, cleanup

1. Open
   [`CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md),
   fill the YAML block from each phase's outputs.
2. **Paste the filled YAML into a PR comment or chat — never into a
   tracked file.** Sha **prefixes only** (12 chars), no full sha, no
   Drive path, no PDF body, no broker/target verbatim.
3. Cleanup:
   ```
   rm -rf /tmp/pr15_probe
   git status   # MUST be clean before claiming the probe is done
   ```
4. The repo's `.gitignore` (PR #11) already blocks `_realdata/` /
   `tmp_workdir/` / `pr11_realdata/` / `_pipeline_workdir/`; do not add
   `pr15_probe/` to staging by accident. Defense-in-depth applies but
   the primary discipline is operator self-check.

---

## Compatibility with PR #17 + PR #18 + PR #19 + PR #20 + PR #26 + PR #27 + PR #28 layout parsers

PR #17 added a "표3. 실적 전망 / 수정 후 / 수정 전 / 변동률" layout reader.
**PR #18 extends this with additional broker-template variants**:
`기존 / 변경`, `변경 전 / 변경 후`, `직전 / 현재` column headers, plus a
`<metric>(<year>) <new> <old> ▲|▼|-` side-anchor scanner. The indicator
(▲/▼/-) is REQUIRED for the side-anchor pattern so growth-rate / YoY rows
without indicators don't produce false positives.

**PR #19 tightens the side-anchor scanner further** — matches are now
restricted to lines within ~15 of a recognized revision header (the same
header pairs PR #18 already detects, plus hint phrases like `추정치 변경`).
Off-header side-anchor matches are rejected with
`gap_reason='side_anchor_no_near_header'`. Target-price side-anchor remains
unrestricted (audit-only; it never feeds a primary row).

**PR #20 applies the same precision tightening to the variant column-window
scanner.** The 직전/현재 (and 기존/변경, 변경 전/후) column-window now caps
at 15 lines past its header (down from 40), terminates early when a
`목표주가` line is encountered inside the window, and drops candidate rows
whose `old`/`new` both have `abs<100` for `sales/operating_profit/net_income`
(EPS exempt — 원 단위 EPS can legitimately be small). Rejected rows surface
as `gap_reason='variant_rejected_growth_rate'`. This eliminates the cloud-
smoke false positive observed on the 대덕전자 PDF (op `1.9 → -6.2`); the
parser now correctly returns op `201 → 251` from the actual revision panel
or `0 structured rows` for short comments without one.

**PR #26 adds three conservative gap-handling helpers** triggered by the
post-PR-#22 5-PDF cloud smoke:
1. **Natural-language revision regex** — `<metric> X에서 Y로 상향/하향`
   form. Direction word is REQUIRED (60-char tail window) and MUST match
   numeric direction; ambiguity rejects → `gap_reason='natural_language_revision_ambiguous'`.
2. **Inline KV side-anchor** — `<metric>(year): 기존 X / 변경 Y` form.
   Both labels REQUIRED inline so PR #18 table-layout (header-row labels)
   does not double-fire.
3. **Flat duplicate-column audit** — when the variant column-window
   scanner reads two byte-identical numeric tokens on a single metric row,
   the breakdown's metric entry carries `audit_flags=['flat_possible_duplicate_column']`.
   The structured row is still emitted (`direction='flat'`,
   `direct_trade_signal=false`); operator decides whether it's intentional
   flat or a column-duplication read.

PR #26 also adds `gap_reason='year_pivot_no_revision_pair'` for the strict
forecast-only year-pivot case (no `목표주가/가이던스/추정치 변경/변동률/
revision` keywords). The legacy PR #18 `ambiguous_year_pivot` path remains
for texts that DO have those keywords, preserving fixture byte-identity.

**PR #27 promotes the PR #26 `flat_possible_duplicate_column` audit flag
into a hard rejection.** The variant column-window scanner now refuses to
commit any row whose `old`/`new` raw tokens are byte-identical strings,
UNLESS the same line carries an explicit flat-context marker
(`유지 / 동일 / 변동 없음 / unchanged / flat / no change`). Rejected rows
never enter the breakdown's `metrics` dict, and when no metric survives
the variant scan, `gap_reason='duplicate_column_flat_rejected'` fires.
The PR #26 audit flag is removed. PR #12 arrow-pair flat (`<metric> X →
X`) is unaffected — arrow-pair scanner is a separate code path. On the
post-PR-#22 5-PDF cloud smoke this drops LG전자 from the structured rows
(its `change_before_after` window had `매출액 23,733 23,733` and
`영업이익 1,673.6 1,673.6` rows that the parser previously emitted as
flat); structured_rows_total goes from 2 to 1, no false positives.

**PR #28 adds three side-anchor template guards** triggered by the
post-PR-#27 5-PDF cloud smoke residuals (삼성물산 / 두산퓨얼셀):
1. **Multi-line KV form** — picks up
   `<metric>\n2026E 기존 X 변경 Y` and
   `<metric>(26E)\n기존 X\n변경 Y`. The metric-anchor line MUST be
   metric-only (no numbers, no extra text) so a normal data row can
   never trigger this entry point.
2. **Reversed-inline KV** — `<metric>(year): 변경 Y / 기존 X` (new-
   label first). Fall-through: the existing PR #26 forward-order regex
   runs first; reversed runs second; first match wins.
3. **Row-level margin / yoy / (%) reject** — any inline KV match whose
   row line carries one of `영업이익률 / 이익률 / 변동률 / 성장률 /
   yoy / qoq / margin / growth / yield / (%)` is silently rejected.
   The multi-line helper applies the same reject across its window.

The 5-PDF cohort is unchanged from PR #27 — the residual gaps on
삼성물산 (`side_anchor_header_found_no_metric_pair`) and 두산퓨얼셀
(`ambiguous_year_pivot`) are NOT addressable by these helpers because
their PDFs use SK증권's multi-column-positional template (3+ header
lines above the data row) and a narrative-only revision style
respectively. Both are deferred to operator-host parsing or a future
template-aware extraction pass. PR #28 conservatively does NOT fire on
either.

The probe runbook is unchanged — `--pdf-engine auto` (PR #16) still selects
the extraction engine, and all layout parsers are wholly internal. PR #18
also adds an audit-only `gap_reason` field on each breakdown record so the
operator can read why a particular PDF didn't yield a structured row;
PR #19 added two more values to that vocabulary
(`side_anchor_no_near_header` / `side_anchor_header_found_no_metric_pair`)
and PR #20 added one more (`variant_rejected_growth_rate`). No OCR / Vision
/ API fallback added.

## What this PR does NOT do

- **Does not execute** any Drive search, metadata read, or PDF
  download in the sandbox running this PR. Phase 0–5 are documented
  for a future cloud session to follow on the operator's behalf.
- **Does not** implement any new Drive-fetch tooling. Whatever the
  cloud session has at runtime is what the probe uses.
- **Does not** add OCR / Vision / API fallback. PR #15 is purely
  capability-discovery + a 1-PDF deterministic smoke that reuses
  PR #13's `--pdf` path.
- **Does not** modify any existing parser, runner, selector, or
  fixture. Pure docs.
- **Does not** lift the `--max 3` cap from PR #14 — PR #15 is
  *tighter* (`pdf_count == 1`) because its purpose is capability
  discovery, not coverage.

---

## See also

- [`REALDATA_SAMPLE_RUN.md`](REALDATA_SAMPLE_RUN.md) — operator-host
  procedures (PR #11 sample, PR #14 1–3 PDF smoke).
- [`REAL_PDF_SMOKE_RESULT_TEMPLATE.md`](REAL_PDF_SMOKE_RESULT_TEMPLATE.md)
  — operator-host paste-back schema (PR #14, sibling of PR #15's
  result template).
- [`CLAUDE_CODE_RUNBOOK.md`](CLAUDE_CODE_RUNBOOK.md) — Phase3
  pipeline runbook (general).
