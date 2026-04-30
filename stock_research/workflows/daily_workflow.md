# PBKR Daily Workflow

매 거래일 1회(09:00 KST 이후) 실행하는 표준 사이클. 산출물은 Google Drive `stock_research/` 측 `daily/<YYYY-MM-DD>/` 폴더에 저장하고, 본 repo에는 코드/스키마만 둔다.

## Sequence

1. **가격 스냅샷 수집**
   - 트리거: `.github/workflows/serp_run.yml` (자동) 또는 수동
   - 산출: repo 루트 `current_prices.json` / `current_prices.csv`
   - 품질 게이트: 모든 종목에 `price` 또는 `error`가 채워져야 함

2. **Orchestrator 1차 실행**
   - 입력: `current_prices.json`, Drive `rolling_memory.json`
   - 출력: `candidate_score_pack.json`
   - 검증: `python stock_research/scripts/validate_pbkr_outputs.py --pack <path> --schema stock_research/schemas/candidate_score_pack.schema.json`

3. **Auditor 실행 (병렬 가능)**
   - 입력: `candidate_score_pack.json`, `rolling_memory.json`
   - 출력: `audit_pack.json`
   - 검증: `audit_pack.schema.json`

4. **NewsGrounder 실행 (병렬 가능)**
   - 입력: `candidate_score_pack.json`의 ticker 목록, SerpApi `google_news`
   - 출력: `news_pack.json`
   - 검증: `news_pack.schema.json`

5. **Orchestrator 2차 통합**
   - 입력: `candidate_score_pack` + `audit_pack` + `news_pack`
   - 출력: `trade_ticket.json` (`input_pack_ids`에 위 3개 pack_id 기록)
   - 검증: `trade_ticket.schema.json`

6. **History append** (rolling)
   - `python stock_research/scripts/rolling_append.py --csv stock_research/templates/candidate_history.csv --rows <projected_rows.json>`
   - 기본 dry-run. 검토 후 `--apply`로 실행.
   - 동일 (date, ticker, source_key) 중복은 자동 차단.

7. **Memory append**
   - Orchestrator가 별도로 발행한 `rolling_memory.append.json`을 Drive 측 `rolling_memory.json`에 병합
   - 병합 도구는 향후 `scripts/`에 추가 예정 (현재는 수동)

## Gates / Refusal
- 단계 2~5 중 어느 산출물이라도 스키마 검증 실패 → 사이클 중단, `daily/<date>/INCOMPLETE` 마커 생성.
- `news_pack`에 `severity: critical` 항목이 있는 종목은 Orchestrator 2차에서 자동 `hold`로 강등.

## What this repo does NOT do
- 실제 주문 실행, 브로커 API 호출 — 없음.
- 계좌 잔고/평단 입력 — 없음. 정책(목표 비중)은 사용자 측에서 주입.
