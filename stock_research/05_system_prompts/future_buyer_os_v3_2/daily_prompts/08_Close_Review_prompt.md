# 08_Close_Review — Prompt

## 목적

장 마감(15:30 KST) 후 오늘의 super_pack_v3_2 운영 결과를 회고합니다.
회고는 **운영 가설의 적합성** 을 점검하는 단계이며, 매매 결정 정당화가 아닙니다.

## 입력

- 오늘의 `super_pack_v3_2`.
- 오늘의 `pb_state_decision_pack` 변화 이력 (07_Intraday 갱신 포함).
- 오늘 종가/거래량/매수주체 마감 데이터 (스냅샷, raw 거래데이터 커밋 금지).

## 점검 항목

- thesis 별 `invalidation_condition` 충족 여부.
- 강등/승격 결정의 근거 사후 점검.
- PB_SCOUT/PB_TRIGGER 후보의 실제 buyer 군집 매수 여부 (단순 확인, 매매 결정 아님).

## 산출

- `close_review_notes` (markdown) — 후보별 1줄 회고 + 다음날 관찰 포인트.
- 필요 시 `pb_state_decision_pack` 갱신.

## 금지

- 사후 매매 정당화 표현.
- "내일 사라/팔라" 단정 표현.
- Drive write 자동 수행.
