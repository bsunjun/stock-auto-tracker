# Weekly Review Workflow

매주 1회(주 후반, 보통 금요일 마감 후) 누적 history와 메모리를 점검하여 다음 주 사이클의 가설/한도를 갱신한다.

## Inputs
- 이번 주 5영업일치 `candidate_history.csv`, `audit_history.csv`, `pb_state_history.csv`, `portfolio_risk_history.csv` 누적 (Drive 측)
- 이번 주 발행된 `trade_ticket.*.json` 일체
- 직전 주 `weekly_review.md`

## Output
- `weekly_review.md` — Drive `stock_research/weekly/<YYYY-Www>/` 하위에 저장
- (선택) `rolling_memory.append.json` — 신규 가설/리스크/감사 finding을 메모리에 추가

## Review Sections
1. **점수→결정 적합도** — `candidate_history`의 상위 conviction 종목이 실제 `trade_ticket`에 반영되었는가
2. **Audit 시그널 누적** — 같은 종목에 `warn` 또는 `reject`가 반복되는지
3. **PB 상태 변화** — `pb_state_history`의 z-score 분포 이동
4. **포트폴리오 리스크** — `portfolio_risk_history`의 vol_30d, concentration_top3 추이
5. **News-grounded 카탈리스트 실현률** — 지난 주 `news_pack`의 catalyst 중 실현/미실현 분류
6. **다음 주 한도 조정** — 정책 한도 재조정 제안 (실행은 사용자 승인 후)

## Procedure
1. `validate_pbkr_outputs.py`로 이번 주 모든 pack의 스키마 통과 여부 일괄 점검.
2. CSV history는 read-only로 다룸. 정정 사항은 `corrections/` 별도 파일로 기록.
3. 회고 결과를 `rolling_memory.append.json`으로 만들고 `rolling_append` 패턴으로 메모리에 병합 (현재 수동, 추후 자동화 예정).

## Refusal
- 5영업일 중 INCOMPLETE 마커가 2일 이상이면 회고를 부분 수행하고, 누락된 일자는 `gaps` 섹션에 명시.
- 데이터 누락을 임의로 추정/보간하지 않는다.
