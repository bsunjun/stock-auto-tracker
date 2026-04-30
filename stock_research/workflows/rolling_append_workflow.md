# Rolling Append Workflow

`stock_research/templates/*.csv` 의 history 파일에 신규 행을 안전하게 누적하는 절차. 모든 append는 `scripts/rolling_append.py`를 통해 수행하고, 기본 동작은 dry-run이다.

## Principles
1. **append-only** — 이미 쌓인 행은 수정/삭제하지 않는다. 정정이 필요하면 별도 `correction_*` 파일로 기록.
2. **idempotent** — 같은 (`date`, dedupe key, `source_key`) 조합은 반복 실행해도 한 번만 들어간다.
3. **schema-aligned** — 입력 행의 컬럼 집합이 CSV 헤더와 정확히 일치해야 한다.
4. **safe-by-default** — `--apply`를 명시하지 않으면 항상 dry-run.

## Dedupe Keys

| 파일 | dedupe key |
| --- | --- |
| `candidate_history.csv` | `date, ticker, source_key` |
| `sector_history.csv` | `date, sector, source_key` |
| `estimate_revision_history.csv` | `date, ticker, broker, source_key` |
| `pb_state_history.csv` | `date, ticker, source_key` |
| `audit_history.csv` | `date, ticker, source_key` |
| `portfolio_risk_history.csv` | `date, source_key` |

`source_key` 는 `phase3:report_estimate:v1.3.2+<sha256[:12]>` 형태로 source PDF 의 sha256 prefix 를 포함하므로 사실상 `source_pdf_sha256` 동등성을 함께 보장한다. 별도로 `source_pdf_sha256` 을 dedupe key 에 추가할 필요는 없다.

## Standard Invocation

```
# 1) Dry-run (default)
python stock_research/scripts/rolling_append.py \
  --csv stock_research/templates/candidate_history.csv \
  --rows /path/outside/repo/candidate_rows.json \
  --dedupe-keys date,ticker,source_key

# 2) Apply after review
python stock_research/scripts/rolling_append.py \
  --csv stock_research/templates/candidate_history.csv \
  --rows /path/outside/repo/candidate_rows.json \
  --dedupe-keys date,ticker,source_key \
  --apply
```

## Strict Estimate Mode (PR #8)

`build_report_estimate_v132.py --strict` 가 만든 `estimate_revision_rows.json`
을 받을 때는 `--strict-estimate` 를 함께 켠다. 이 모드는 다음을 강제한다:

- `direct_trade_signal == false` 인 row 만 통과 — Phase3 산출물은 매매 신호가 아니다.
- `ticker` 가 `KRX:` 형식
- `direction ∈ {up, down, flat}` (불확정 `unknown` 은 차단)
- `old_target` / `new_target` / `source_key` 비어있지 않음
- `reject_reasons` / `missing_fields` 같은 reject 마커가 들어있는 row 는
  무조건 거부 — `estimate_revision_rejected_rows.json` 형태가 잘못 흘러들어도
  rolling history 에는 절대 들어가지 않는다.
- audit 전용 컬럼 (`source_pdf_sha256`, `direct_trade_signal`) 은 검증에만 쓰이고
  CSV 에는 기록되지 않는다 (헤더는 기존과 동일).

dry-run 에서는 validated / rejected 카운트와 `reject_reason_counts` 가 출력되며,
파일 쓰기는 일어나지 않는다.

```
# 1) Dry-run with strict-estimate
python stock_research/scripts/rolling_append.py \
  --csv stock_research/templates/estimate_revision_history.csv \
  --rows /path/outside/repo/estimate_revision_rows.json \
  --dedupe-keys date,ticker,broker,source_key \
  --strict-estimate

# 2) Apply after review
python stock_research/scripts/rolling_append.py \
  --csv stock_research/templates/estimate_revision_history.csv \
  --rows /path/outside/repo/estimate_revision_rows.json \
  --dedupe-keys date,ticker,broker,source_key \
  --strict-estimate \
  --apply
```

> ⚠️ `estimate_revision_rejected_rows.json` 은 절대 `--rows` 로 넘기지 말 것.
> 마지막 보안망으로 `--strict-estimate` 가 거부하긴 하지만, 입력 자체가 잘못된 신호다.

## Output Log
스크립트는 다음을 stdout에 기록한다:
- 입력 행 수
- (--strict-estimate) validated / rejected 카운트와 reject_reason_counts
- 중복으로 스킵한 행 수
- 추가될/추가된 행 수
- 변경 전/후 파일 라인 수

## Where History Lives
- repo: 헤더만 있는 템플릿 (이 디렉토리)
- Drive: 실제 누적 데이터. repo의 템플릿 파일에는 데이터를 직접 커밋하지 않는다.
- 실험적 append 결과를 repo에 푸시하지 말 것 — `git status`에 `stock_research/templates/*.csv`가 잡히면 반드시 검토 후 되돌릴 것.
