# 10-Layer Pipeline — Future Buyer Momentum OS v3.2

각 레이어는 **고유한 입력 → 산출 pack(JSON Schema)** 구조를 가집니다.
다음 레이어는 이전 레이어의 산출 pack을 입력으로 받습니다.
어떤 레이어도 단독으로 매매 신호를 만들지 않습니다.

---

## Layer 1 — Macro / Politics / Technology Flow

> **큰 돈의 방향**

- **목적**: 글로벌 자본/정치/기술 흐름이 어떤 섹터·테마에 우호적인지 식별.
- **입력**: 모바일 INBOX의 거시 뉴스 스냅샷, 공식 매크로 통계 캡처, 정책 발표.
- **산출 pack**: [`schemas/macro_politics_technology_flow.schema.json`](./schemas/macro_politics_technology_flow.schema.json)
- **담당 프로젝트**: `Gemini_PBKR_NewsGrounder_v3_2`
- **신호 등급**: 방향성 단서 (no PB state 직접 결정)

## Layer 2 — Newspaper / Major News

> **개인 관심의 방향**

- **목적**: 메이저 신문/포털 헤드라인이 향한 종목·테마. 개인의 관심이 어디에 모이는지.
- **입력**: 신문 스냅샷, 메이저 포털 헤드라인 캡처(요약된 형태).
- **산출 pack**: [`schemas/attention_flow_pack.schema.json`](./schemas/attention_flow_pack.schema.json)
- **담당 프로젝트**: `Gemini_PBKR_NewsGrounder_v3_2`
- **신호 등급**: 개인 관심 트래픽 단서.

## Layer 3 — Telegram / Paid Channels

> **단기 돈과 테마 확산 방향**

- **목적**: 단기 자금 흐름과 테마 확산 속도. 채널 간 메시지 싱크/시간차 분석.
- **입력**: Telegram 채널 메시지 요약(원문 저장 금지, raw text는 Drive 모바일 INBOX에만 보관, repo 커밋 금지).
- **산출 pack**: [`schemas/theme_radar_pack.schema.json`](./schemas/theme_radar_pack.schema.json)
- **담당 프로젝트**: `Telegram_ThemeRadar_v3_2`
- **신호 등급**: **WATCH_ONLY 또는 THEME_DISCOVERY 까지만 허용.** Telegram-only 후보를 PB_READY 이상으로 올리는 것은 금지.

## Layer 4 — WiseReport / Industry Report

> **기관이 살 명분**

- **목적**: 증권사 보고서가 제공하는 기관 매수 명분. 목표주가는 secondary_reference 로만 사용.
- **입력**: WiseReport 인벤토리, 산업 리포트 요약(추출 텍스트는 repo 커밋 금지).
- **산출 pack**: [`schemas/institutional_justification_pack.schema.json`](./schemas/institutional_justification_pack.schema.json)
- **담당 프로젝트**: `Claude_ReportReader_v3_2`
- **신호 등급**: 기관 명분 단서 (PB_SCOUT 후보의 사전 조건).
- 보조 입력 pack: [`schemas/us_korea_readthrough_pack.schema.json`](./schemas/us_korea_readthrough_pack.schema.json) — 미국발 산업 흐름의 한국 readthrough.

## Layer 5 — DART / Company IR

> **공식 숫자 확인**

- **목적**: DART 공시 / IR 자료로 보고서 내러티브와 회사 공식 숫자의 차이를 검증.
- **입력**: DART 공시 인덱스(요약), IR 자료의 metadata.
- **산출 pack**: [`schemas/official_evidence_pack.schema.json`](./schemas/official_evidence_pack.schema.json)
- **담당 프로젝트**: `Claude_ReportReader_v3_2`
- **신호 등급**: 공식 검증 단서. IR/DART와 보고서 숫자 mismatch는 후보 자동 강등 사유.

## Layer 6 — Kiwoom Flow

> **실제 매수 주체 확인**

- **목적**: 키움 플로우(외국인/기관/개인/연기금 등)에서 실제 매수 주체가 누구인지 확인.
- **입력**: 키움 일/분 단위 매수 주체 집계(스냅샷, 원시 거래 데이터 커밋 금지).
- **산출 pack**: [`schemas/actual_buyer_confirmation_pack.schema.json`](./schemas/actual_buyer_confirmation_pack.schema.json)
- **담당 프로젝트**: `ChartSupplyReader_v3_2`
- **신호 등급**: 실수요자 확인. PB_READY → PB_SCOUT 승격의 핵심 게이트.

## Layer 7 — TradingView Chart

> **언제 살지 확인**

- **목적**: 차트의 supply/demand zone 으로 진입 타이밍의 적정성 평가.
- **입력**: TradingView 차트 요약 (스크린샷 캡션 + 핵심 레벨, 이미지 자체는 커밋 금지).
- **산출 pack**: [`schemas/chart_timing_pack.schema.json`](./schemas/chart_timing_pack.schema.json)
- **담당 프로젝트**: `ChartSupplyReader_v3_2`
- **신호 등급**: 타이밍 보조. 가격은 신호가 아니다. 시간이 신호다.

## Layer 8 — Official Risk Flags

> **사면 안 되는 것 제거**

- **목적**: 거래정지/감리/관리종목/대주주 매도/유증·CB·BW 임박/회계 risk 등 hard-stop 사유 제거.
- **입력**: DART 공시 keyword 매칭, 거래소 공시 카테고리, 공식 risk feed.
- **산출 pack**: [`schemas/official_risk_flags_pack.schema.json`](./schemas/official_risk_flags_pack.schema.json)
- **담당 프로젝트**: `Claude_PBKR_Auditor_v3_2`
- **신호 등급**: hard-stop 게이트. 한 개라도 매치되면 후보는 자동 `WATCH_ONLY` 강등.

## Layer 9 — Future Buyer Thesis

> **나 다음에 누가 살지 판단**

- **목적**: 위 1~8 레이어를 종합해 "내가 산 다음에 어느 buyer 군집이 추가 매수할 것인가" 를 명시적으로 선언.
- **입력**: 1~8 레이어의 모든 pack.
- **산출 pack**: [`schemas/future_buyer_thesis_pack.schema.json`](./schemas/future_buyer_thesis_pack.schema.json)
- **담당 프로젝트**: `ChatGPT_PBKR_Orchestrator_v3_2`
- **데이터 구조 상세**: [`FUTURE_BUYER_THESIS.md`](./FUTURE_BUYER_THESIS.md)

## Layer 10 — PB State

> **`WATCH_ONLY` / `PB_READY` / `PB_SCOUT` / `PB_TRIGGER`**

- **목적**: 후보의 운영 상태를 결정. 매매 신호가 아니라 **관찰 단계의 라벨**.
- **입력**: Layer 9 thesis + Layer 8 risk flags + Layer 6 actual buyer confirmation.
- **산출 pack**: [`schemas/pb_state_decision_pack.schema.json`](./schemas/pb_state_decision_pack.schema.json)
- **담당 프로젝트**: `ChatGPT_PBKR_Orchestrator_v3_2`
- **승격 규칙**:
  - `WATCH_ONLY` — 최소 단서. Telegram-only 또는 단일 레이어만 매치.
  - `PB_READY` — Layer 4 + Layer 5 + Layer 1/2 흐름 일치. 매수 신호 아님. 준비 단계.
  - `PB_SCOUT` — `PB_READY` 조건 + Layer 6 실수요 확인 + Layer 7 타이밍 zone 진입. **정찰**(소량 노출 가능성 검토 단계). human gate 필수.
  - `PB_TRIGGER` — `PB_SCOUT` 조건 + Layer 9 future buyer thesis가 명확하고 invalidation 조건이 정량 정의됨. **본진 후보**. human gate 통과 전 자동 실행 금지.

## 통합 SuperPack

위 1~10 레이어 산출은 [`schemas/super_pack_v3_2.schema.json`](./schemas/super_pack_v3_2.schema.json) 으로 묶입니다.
SuperPack 자체도 `direct_trade_signal=false`, `trade_signal in (null, false)` 를 강제합니다.
