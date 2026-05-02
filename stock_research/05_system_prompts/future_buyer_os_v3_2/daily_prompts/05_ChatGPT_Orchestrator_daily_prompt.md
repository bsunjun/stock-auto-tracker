# 05_ChatGPT_Orchestrator — Daily Prompt

## 목적

오늘 기준 1~8 레이어 pack 을 통합해 **Layer 9 future_buyer_thesis_pack** 과
**Layer 10 pb_state_decision_pack** 을 산출하고, 마지막에 **super_pack_v3_2** 로 묶습니다.

## 입력

- `macro_politics_technology_flow` (L1)
- `attention_flow_pack` (L2)
- `theme_radar_pack` (L3)
- `institutional_justification_pack` (L4)
- `us_korea_readthrough_pack` (L4 보조)
- `official_evidence_pack` (L5)
- `actual_buyer_confirmation_pack` (L6)
- `chart_timing_pack` (L7)
- `official_risk_flags_pack` (L8)

## 산출

- `future_buyer_thesis_pack` (L9)
- `pb_state_decision_pack` (L10)
- `super_pack_v3_2`

## 승격 규칙 (요약)

- `WATCH_ONLY` — 단일 레이어 / Telegram-only.
- `THEME_DISCOVERY` — 테마 단위 단서.
- `PB_READY` — L4+L5+L1or2 일치. 매수 신호 아님.
- `PB_SCOUT` — `PB_READY` + L6 + L7. 정찰. human gate 필수.
- `PB_TRIGGER` — `PB_SCOUT` + L9 thesis 명확 + `invalidation_condition` 정량.

## 강등 규칙

- L8 risk flag 매치 → 자동 `WATCH_ONLY`.
- Telegram-only 만 단서 → 자동 `WATCH_ONLY`.
- `target_price` 가 primary 로 사용되려 하면 reject.

## 표현 가이드

- thesis 본문에 단정 명령형 금지.
- `why_they_buy`, `when_they_buy`, `invalidation_condition` 모두 채울 것. 비면 thesis 무효.
- `edge_declared` 필수.
