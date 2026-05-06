# Screening Builder — output layout

> Outputs of this module **must not** be committed to the repository.

## 1. Default location

### 1.1 `screen` subcommand (offline / dev)

Writes to `${PBKR_SCREENING_OUT}/<YYYY-MM-DD>/`, falling back to
`/tmp/pbkr_v4_screening_out/<YYYY-MM-DD>/` when the env var is
unset. The CLI refuses any `--out-dir` under the repo root.

### 1.2 `live-screen` subcommand (real live inputs, read-only)

Writes to `${PBKR_LIVE_SCREENING_OUT_BASE}/<YYYYMMDD>/<YYYY-MM-DD>/`,
falling back to
`/Users/bsunjun/trading/phase3/output/pbkr_screening/<YYYYMMDD>/<YYYY-MM-DD>/`
when the env var is unset. The runner refuses any `--output-dir`
under the repo root and refuses to start without `--no-execution`.

## 2. Files per run

`screen`:

```
<OUT_DIR>/<YYYY-MM-DD>/
  tradingview_scan_pack.json
  kiwoom_feature_pack.json
  official_risk_flags_pack.json
  screening_candidates_pack.json
  daily_input_packet.json     # canonical for GPT Orchestrator
  daily_input_packet.md       # human-readable summary
```

`live-screen` writes the same six files plus an audit artifact:

```
<OUTPUT_DIR>/<YYYYMMDD>/<YYYY-MM-DD>/
  tradingview_scan_pack.json
  kiwoom_feature_pack.json
  official_risk_flags_pack.json
  screening_candidates_pack.json
  daily_input_packet.json
  daily_input_packet.md
  verification_report.json    # NEW: read-only proof artifact
```

`verification_report.json` records:

* the runner identifier (`live_screening_runner`),
* the as-of date,
* fingerprints of every input source (path, size, mtime,
  SHA-256 of first 1 MiB),
* the resolved output dir and the list of emitted files,
* every doctrinal counter (15 of them) — each constrained to
  `const: 0` by `schemas/verification_report.schema.json`,
* the screening counts and the PBKR_RS_RANK summary,
* the full signal-safety block plus
  `no_execution: true`, `broker_order_path_present: false`,
  `auto_execution_allowed: false`,
* a top-level `pass: true`.

The presence of this file with `pass: true` is the audit proof
that no execution path was taken during the run.

## 3. Forbidden content

The validator (`validator.py::sanitize_payload`) raises
`SafetyViolation` if any payload contains:

* `account_no`, `account_number`
* `order_no`, `order_id`
* `api_key`, `apikey`
* `token`, `access_token`, `refresh_token`
* `password`, `secret`
* `broker_response`

The post-write verifier (`validator.py::verify_run_directory`)
additionally counts and asserts zero for every forbidden artifact
token in JSON keys / values:

* `PB_TRIGGER`, `PB_READY`, `PB_SCOUT`
* `trade_ticket`, `order_intent`, `order_preparation`
* `execution_artifact`, `automatic_alert`, `automatic_execution_hook`

It also asserts:

* `direct_trade_signal_true_count == 0`
* `trade_signal_true_count == 0`
* `automatic_execution_allowed_true_count == 0`
* `trade_ticket_generation_allowed_true_count == 0`
* `operator_decision_execute_count == 0`

Real OHLCV, real KR designation rows, real broker responses, and
real ticker names belong outside the repo. The fixtures shipped in
`fixtures/` are synthetic by construction (anonymized tickers,
seeded RNG, hand-authored designation strings).

## 4. .gitignore backstop

`pbkr_v4_screening_out/` is added to the repository `.gitignore` to
catch the accidental case where someone runs the CLI with
`--out-dir` pointing inside the repo (the CLI also rejects this,
but defense-in-depth).
