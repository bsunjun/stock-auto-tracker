# 06_Claude_Auditor — Daily Prompt

## 목적

오늘 산출된 super_pack_v3_2 가 본 v3.2 헌장(hard rules)을 위반하지 않았는지 audit.
또한 Layer 8 `official_risk_flags_pack` 을 직접 산출/갱신.

## 점검 항목

- `direct_trade_signal == false`.
- `trade_signal in (null, false)`.
- `target_price` 가 primary 위치에 없는가.
- Telegram-only 후보가 PB_READY 이상으로 승격되지 않았는가.
- `edge_declared` 가 모든 pack 에 채워졌는가.
- `pb_state` 가 enum 안인가.
- PB_TRIGGER 후보의 `invalidation_condition` 이 정량 표현으로 채워졌는가.

## Risk flag 점검

- `trading_halt`, `audit_supervisory`, `managed_listing`, `controlling_sale`, `equity_offering_imminent`,
  `accounting_qualification`, `delisting_risk`, `legal_risk`, `going_concern`, `other_official_risk`.
- 매치 시 자동 `WATCH_ONLY` 강등 권고.

## 출력

- `official_risk_flags_pack` 갱신.
- audit notes (markdown) — 위반 항목별 파일/필드 인용 + 권고 변경.

## 금지

- 단정 매수/매도 표현.
- audit 결과로 Drive write 자동 수행.
