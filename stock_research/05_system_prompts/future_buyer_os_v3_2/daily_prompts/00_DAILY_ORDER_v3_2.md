# 00_DAILY_ORDER_v3_2 — Daily Sequence

이 문서는 **하루 운영의 실행 순서** 와 각 단계에서 사용할 daily prompt 의 매핑입니다.
모든 단계는 산출물의 디폴트 `direct_trade_signal=false` 를 유지합니다.

## 실행 순서 (KST)

| 시각 | 단계 | Daily prompt | 담당 |
|---|---|---|---|
| 07:30 | 거시/뉴스 grounding | `02_Gemini_Macro_NewsGrounder_daily_prompt.md` | Gemini |
| 08:00 | Telegram 테마 레이더 | `01_Telegram_ThemeRadar_daily_prompt.md` | Colab/Telegram_ThemeRadar |
| 08:30 | 보고서/공시 grounding | `03_ReportReader_daily_prompt.md` | Claude_ReportReader |
| 09:30 | 차트/매수주체 grounding | `04_ChartSupplyReader_daily_prompt.md` | ChartSupplyReader |
| 11:00 | thesis 통합 + PB state | `05_ChatGPT_Orchestrator_daily_prompt.md` | ChatGPT_Orchestrator |
| 11:30 | audit | `06_Claude_Auditor_daily_prompt.md` | Claude_Auditor |
| 13:30 | intraday update | `07_Intraday_PB_Update_prompt.md` | ChatGPT_Orchestrator |
| 15:30 | 마감 회고 | `08_Close_Review_prompt.md` | ChatGPT_Orchestrator + 사람 |
| 주1회 | 주간 회고 | `09_Weekly_Review_prompt.md` | 사람 + ChatGPT_Orchestrator |

## 각 단계 공통 가드

- 출력 JSON 의 `direct_trade_signal=false`.
- `trade_signal in (null, false)`.
- `target_price` 는 secondary_reference 외 위치 금지.
- Telegram-only 후보 → `WATCH_ONLY` 또는 `THEME_DISCOVERY` 까지만.
- 모든 pack 에 `edge_declared` 필수.
- Drive write / 외부 API client 호출 금지.

## 사람(human gate) 체크포인트

- 11:30 audit 결과 확인.
- `PB_SCOUT` / `PB_TRIGGER` 승격 결재 (자동화 금지).
- 마감 회고에서 invalidation_condition 충족 여부 확인.
