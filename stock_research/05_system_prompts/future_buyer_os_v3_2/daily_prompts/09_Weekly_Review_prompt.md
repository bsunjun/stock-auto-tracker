# 09_Weekly_Review — Prompt

## 목적

주 1회(주말 권장) 운영 가설/구조의 적합성을 회고합니다.

## 입력

- 1주일치 `super_pack_v3_2`.
- 1주일치 `pb_state_decision_pack` 변화 이력.
- 매주의 layer 별 산출 pack.

## 점검 항목

- 어떤 buyer_type 가설이 가장 자주 invalid 되었는가.
- 어떤 layer 가 PB_SCOUT/PB_TRIGGER 승격에 가장 결정적이었는가.
- Telegram 단서가 PB_READY 이상 승격에 영향을 미치려 한 시도(hard rule 위반 시도)가 있었는가.
- risk flag 매치로 인한 강등 빈도와 사유.
- `target_price` 가 primary 위치에 사용되려 한 시도가 있었는가.

## 산출

- `weekly_review_notes` (markdown).
- 운영 prompts 의 미세 조정 권고 (실제 수정은 별도 PR).

## 금지

- 회고를 매매 정당화로 사용.
- 다음 주 단정 매수/매도 표현.
- Drive write 자동 수행.
