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

## Output Log
스크립트는 다음을 stdout에 기록한다:
- 입력 행 수
- 중복으로 스킵한 행 수
- 추가될/추가된 행 수
- 변경 전/후 파일 라인 수

## Where History Lives
- repo: 헤더만 있는 템플릿 (이 디렉토리)
- Drive: 실제 누적 데이터. repo의 템플릿 파일에는 데이터를 직접 커밋하지 않는다.
- 실험적 append 결과를 repo에 푸시하지 말 것 — `git status`에 `stock_research/templates/*.csv`가 잡히면 반드시 검토 후 되돌릴 것.
