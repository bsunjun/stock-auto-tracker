# 01_Telegram_ThemeRadar — Daily Prompt

## 목적

오늘 시각 기준 Telegram / 유료 채널의 **테마 확산 속도** 를 측정합니다.
산출은 `theme_radar_pack` 한 개입니다.

## 입력

- `00_INBOX_MOBILE/` 의 `tg_*` / `paid_*` 캡처 요약 (raw 메시지 본문은 복제 금지).
- 직전 영업일의 `theme_radar_pack` (있다면).

## 산출 필드 (요약)

- `as_of_kst` — 산출 시각.
- `themes[]`:
  - `theme_id`, `theme_label`
  - `channel_sync_count` — 같은 시간대에 등장한 채널 수.
  - `velocity_score` — 단위시간당 메시지 변화율 (정량 또는 0~3 정성).
  - `paid_only` — 유료 채널에만 등장하면 true.
  - `pb_state_recommendation` — `WATCH_ONLY` 또는 `THEME_DISCOVERY` 만 허용.
  - `edge_declared` — 한 줄.

## Hard rules

- Telegram-only 단서로 PB_READY 이상 권장 금지.
- `direct_trade_signal=false`, `trade_signal in (null, false)`.
- 메시지 raw 텍스트 복제 금지.
- 채널 운영자 개인 식별정보 출력 금지.

## 표현 가이드

- "지금 X 매수 권고" 같은 단정 표현 금지.
- 추천은 `pb_state_recommendation` 필드의 enum 값으로만 표현.
