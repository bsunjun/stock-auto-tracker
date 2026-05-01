# Cloud-Drive PDF Fetch Probe — Result Template (PR #15)

Use this template **after** running the PR #15 probe procedure
(see [`CLOUD_DRIVE_PDF_FETCH_PROBE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE.md))
in a Claude Code cloud session. Fill the YAML block, paste it into a
**PR comment or chat — NEVER into a tracked file**, then delete the
local copy.

This is the cloud-session sibling of PR #14's
[`REAL_PDF_SMOKE_RESULT_TEMPLATE.md`](REAL_PDF_SMOKE_RESULT_TEMPLATE.md).
Where PR #14 reflects an operator-Mac smoke (1–3 PDFs), PR #15
reflects a cloud-session capability probe (≤ 1 PDF).

---

## Hard rules (operator confirms before paste)

- [ ] `pdf_count == 0` (Phase 0/1 stop) **or** `pdf_count == 1`
      (Phase 2+). Anything else is a probe-scope violation.
- [ ] No PDF bytes / extracted text / structured_extraction.json /
      pipeline_summary.json contents are pasted verbatim — only
      counts, sha **prefixes** (12 chars), and aggregate reject
      reasons.
- [ ] `direct_trade_signal_true_count == 0`.
- [ ] `forbidden_actions_confirmed.*` are all 0.
- [ ] `git status` is clean and `/tmp/pr15_probe` is removed before
      paste-back.

---

## Template (fill, paste, then DELETE the local file)

```yaml
# === Phase 0: cloud session identification + Drive surface ===
cloud_environment:                 ""              # e.g. "Claude Code cloud / Sonnet 4.6"
session_id_suffix:                 ""              # last 8 chars of the session id

drive_search_available:            null            # true | false
drive_search_tool_name:            ""              # e.g. "mcp__gdrive__search_files" or ""
drive_metadata_available:          null            # true | false
drive_metadata_tool_name:          ""              # e.g. "mcp__gdrive__get_file_metadata" or ""
drive_raw_fetch_available:         null            # true | false
drive_raw_fetch_tool_name:         ""              # e.g. "mcp__gdrive__download_file_content" or ""
drive_local_mount_available:       null            # true | false  (e.g. /mnt/gdrive resolves)

# === Phase 1: single-PDF metadata pull (skip if Phase 0 stop) ===
pdf_count:                         0               # 0 (Phase 0/1 stop) or 1 (Phase 2+)
pdf_filename_basename_only:        ""              # basename only, no full Drive path
pdf_sha256_prefix:                 ""              # first 12 hex chars only; never full sha

# === Phase 2: raw fetch (skip if Phase 1 stop) ===
pdf_local_workdir_path:            ""              # e.g. "/tmp/pr15_probe/<basename>.pdf" — never inside the repo
local_sha256_prefix_matches:       null            # true | false  (Phase 2 sanity check vs. Phase 1)

# === Phase 3: deterministic parser (skip if Phase 2 stop) ===
pdfplumber_available:              null            # true | false
pdfplumber_version:                ""              # e.g. "0.11.0" or ""
pypdf_available:                   null            # true | false  (PR #16 fallback)
pypdf_version:                     ""              # e.g. "5.0.0" or ""
pdf_engine_used:                   ""              # "pdfplumber" | "pypdf" | ""  (which engine actually ran)
parser_exit_code:                  null            # 0 expected; 2 if pdfplumber missing or guard fired
structured_rows:                   0
breakdown_rows:                    0
target_price_secondary_rows:       0
direct_trade_signal_true_count:    0               # MUST be 0; otherwise STOP and escalate

# === Phase 4: chain (optional; skip if Phase 3 stop or skipped) ===
build_rows_accepted:               0
build_rows_rejected:               0
reject_reason_counts:                              # estimate_revision_summary.json[reject_reason_counts]
  complete_not_true: 0
  missing_fields_nonempty: 0
  direction_unknown: 0
  old_target_invalid: 0
  new_target_invalid: 0
  ticker_not_krx: 0
  broker_empty: 0
  date_empty: 0
  horizon_empty: 0
rolling_validated:                 0
rolling_rejected:                  0
rolling_dup:                       0
rolling_to_add:                    0

# === All-runs invariants (every key MUST be 0) ===
forbidden_actions_confirmed:
  ocr_or_vision_or_api_calls:      0
  drive_writes:                    0
  drive_renames:                   0
  drive_moves:                     0
  drive_deletes:                   0
  pdfs_committed_to_repo:          0
  extracted_text_committed:        0
  output_json_committed:           0
  templates_csv_writes:            0
  latest_updates:                  0
  promote_runs:                    0
  super_pack_rebuilds:             0
  rolling_apply_runs:              0
  pdfs_processed_above_cap:        0               # cap is 1 in PR #15

# === Concise narrative — aggregates only ===
next_action: |
  # One short paragraph. What the cloud session can / cannot do for
  # Phase3, and the single concrete next step. Examples:
  #   - "Drive surface absent in this cloud session; defer to PR #14
  #      operator host for now."
  #   - "Drive metadata + raw fetch both available; pdfplumber import
  #      succeeded; one PDF parsed cleanly with primary_metric_present
  #      = true. Open PR #16 to wire inventory-driven batch over the
  #      same surface."
  #   - "Drive metadata available but raw fetch refused (permission).
  #      Open issue to scope what permission is needed; do not retry."
```

---

## Field reference

| Field | Source | Allowed values |
|---|---|---|
| `cloud_environment` | runtime label | short string |
| `session_id_suffix` | session id | last 8 chars only |
| `drive_search_available` / `_metadata_available` / `_raw_fetch_available` | tool surface enumeration | `true` / `false` |
| `drive_search_tool_name` / `_metadata_tool_name` / `_raw_fetch_tool_name` | the actual tool name visible to the session | string or `""` |
| `drive_local_mount_available` | filesystem inspection | `true` / `false` |
| `pdf_count` | operator | **0 or 1** (anything else is a violation) |
| `pdf_filename_basename_only` | filename only | string |
| `pdf_sha256_prefix` | first 12 hex chars | string |
| `pdf_local_workdir_path` | `/tmp/pr15_probe/<basename>.pdf` | path **outside** the repo |
| `local_sha256_prefix_matches` | local sha256 of downloaded bytes vs. Phase 1 prefix | `true` / `false` |
| `pdfplumber_available` / `_version` | `python3 -c "import pdfplumber; ..."` | bool / string |
| `pypdf_available` / `_version` | `python3 -c "import pypdf; ..."` (PR #16 fallback) | bool / string |
| `pdf_engine_used` | parser's `[pdf engine]` log line / row's `extraction_method` suffix | `"pdfplumber"`, `"pypdf"`, or `""` |
| `parser_exit_code` | `extract_report_estimate_table.py --pdf` | int (0 = ok) |
| `structured_rows` / `breakdown_rows` / `target_price_secondary_rows` | parser output | int |
| `direct_trade_signal_true_count` | sum across all output files | **MUST be 0** |
| `build_rows_accepted` / `_rejected` | `pipeline_summary.json` | int |
| `reject_reason_counts` | `estimate_revision_summary.json` | dict |
| `rolling_validated` / `rolling_rejected` / `rolling_dup` / `rolling_to_add` | `pipeline_summary.json` | int |
| `forbidden_actions_confirmed` | self-attest + selector / runner outputs | every key MUST be 0 |
| `next_action` | operator | short paragraph; no PDF body excerpts |

---

## What NOT to paste

- ❌ Full sha256 (always 12-char prefix only)
- ❌ Full Drive path (basename only)
- ❌ Verbatim broker / target / metric text from the PDF body
- ❌ The downloaded PDF, the extracted text, or any output JSON
  contents pasted as-is (those carry too much detail; the
  schema-aligned counters above are the deliverable)
- ❌ More than one PDF (PR #15 cap is 1)
- ❌ Tool name strings that include user-specific identifiers
  (project ids, OAuth tokens, file ids that are not safe to share)

---

## Post-paste cleanup

```
rm -rf /tmp/pr15_probe
git status                                # must be clean
```

If `git status` is not clean, **STOP** and reconcile before
claiming the probe is done — the most likely cause is a real-data
file accidentally staged from outside the documented `/tmp/...`
workdir.
