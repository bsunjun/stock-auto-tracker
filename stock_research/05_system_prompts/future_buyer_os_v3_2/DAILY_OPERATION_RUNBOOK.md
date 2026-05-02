# Daily Operation Runbook — Future Buyer Momentum OS v3.2

이 런북은 **하루 단위** 의 운영 흐름과 도구 분담을 정의합니다.
모든 분담은 **추가 가능** 하지만 매매 신호 자동 발행은 **불가** 입니다.

## 1. 환경별 역할

| 환경 | 역할 | 주의 |
|---|---|---|
| **모바일** | `00_INBOX_MOBILE/` 에 단일 진입. 신문/Telegram/뉴스 캡처 raw drop. | 분류·해석을 모바일에서 하지 않는다. |
| **MacBook** | INBOX 분류, layer 폴더 정리, ChatGPT/Claude/Gemini 데스크톱 운영, 최종 사람 검토(human gate). | Drive 쓰기 권한은 사람만 행사. |
| **Claude Code** | repo 측 자동화 (스키마 검증, 프롬프트 갱신, py_compile, fixture 회귀). | `parser/bridge/merge/build/emit` 코드 미수정. Drive write 미수행. |
| **Google Colab** | Telegram/뉴스 raw 텍스트 정규화 → ThemeRadar 초안 작성 보조. | OCR/Vision/외부 LLM API 클라이언트 추가 금지. 민감정보 저장 금지. |

## 2. AI 프로젝트 분담

| AI 프로젝트 | 담당 layer | 산출 pack |
|---|---|---|
| `ChatGPT_PBKR_Orchestrator_v3_2` | Layer 9, Layer 10 통합 | future_buyer_thesis_pack, pb_state_decision_pack, super_pack_v3_2 |
| `Claude_PBKR_Auditor_v3_2` | Layer 8 (risk flags), 전체 audit | official_risk_flags_pack |
| `Gemini_PBKR_NewsGrounder_v3_2` | Layer 1, Layer 2 | macro_politics_technology_flow, attention_flow_pack |
| `Claude_ReportReader_v3_2` | Layer 4, Layer 5 | institutional_justification_pack, us_korea_readthrough_pack, official_evidence_pack |
| `Telegram_ThemeRadar_v3_2` | Layer 3 | theme_radar_pack |
| `ChartSupplyReader_v3_2` | Layer 6, Layer 7 | actual_buyer_confirmation_pack, chart_timing_pack |
| `ClaudeCode_Automation_v3_2` | repo 측 schema/prompt 위생 관리 | (코드 변경 없이 검증·정리) |
| `Codex_Reviewer_v3_2` | repo PR 리뷰 보조 | (코드 변경 없이 리뷰 코멘트) |
| `GoogleColab_ETL_v3_2` | Telegram/뉴스 raw 정규화 보조 | theme_radar_pack 초안 |

## 3. 일일 흐름 (KST 기준)

```
07:00  모바일/맥북: 00_INBOX_MOBILE/ 에 raw drop (신문, 매크로, Telegram 캡처)
07:30  Gemini: Layer 1 / Layer 2 pack 작성 (macro + attention)
08:00  Telegram_ThemeRadar: Layer 3 pack 초안 (Colab 보조 가능)
08:30  Claude_ReportReader: Layer 4 / Layer 5 pack (WiseReport/DART)
09:00  장 시작 — 키움/TradingView 모니터링 시작
09:30  ChartSupplyReader: Layer 6 / Layer 7 pack 1차
10:30  Claude_Auditor: Layer 8 risk flags pack
11:00  ChatGPT_Orchestrator: Layer 9 future_buyer_thesis_pack
11:30  ChatGPT_Orchestrator: Layer 10 pb_state_decision_pack + super_pack
12:00  사람(human gate) 1차 리뷰
13:30  Intraday_PB_Update (07_Intraday_PB_Update_prompt.md)
15:30  장 마감 후 Close_Review (08_Close_Review_prompt.md)
주 1회  Weekly_Review (09_Weekly_Review_prompt.md)
```

## 4. 사람(human gate) 책임

- `PB_SCOUT` / `PB_TRIGGER` 승격 결재.
- invalidation_condition 충족 여부 사람이 직접 확인.
- 자동화는 **신호를 제안**, 사람이 **신호를 채택**.

## 5. 본 PR과의 관계

- 이 런북은 **운영 정의** 입니다. 새 코드를 추가하지 않습니다.
- 본 PR(#47) 가 추가하는 것은 운영 정의(프롬프트/스키마/문서)뿐입니다.
- 자동 실행(파일 분류 자동화, Drive write 자동화 등)은 별도 PR에서 다룹니다.
