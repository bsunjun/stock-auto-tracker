# Integration Notes — v3.2 ↔ legacy

이 문서는 v3.2 운영 정의가 기존 자산과 어떻게 공존하는지 설명합니다.

## legacy 자산 (보존)

- `stock_research/prompts/PBKR-Auditor.md`
- `stock_research/prompts/PBKR-NewsGrounder.md`
- `stock_research/prompts/PBKR-Orchestrator.md`
- `stock_research/schemas/*.schema.json` (audit_pack, candidate_score_pack, news_pack, report_inventory, rolling_memory, trade_ticket)

위 파일은 본 PR에서 **수정/삭제하지 않습니다.**

## phase3 파이프라인 (수정 금지)

- `stock_research/phase3_report_pipeline/scripts/*` 는 본 PR에서 수정 대상이 아닙니다.
- v3.2 의 schema 는 phase3 출력 파일 형식을 강제하지 않습니다 (phase3 fixture 회귀 영향 없음).

## v3.2 위치

- 모든 v3.2 자산은 `stock_research/05_system_prompts/future_buyer_os_v3_2/` 하위에 있습니다.
- legacy schemas/prompts 와 v3.2 schemas/prompts 는 **이름/번호가 다르므로 충돌하지 않습니다.**

## 향후 PR (별도 분리)

- v3.2 SuperPack 자동 emit / fixture 회귀.
- Drive write/rename 자동화.
- Colab ETL 의 raw → ThemeRadar 자동 변환 코드.
- legacy → v3.2 마이그레이션.

본 PR(#47)은 위 향후 작업의 **계약서(스키마) 와 절차서(프롬프트)** 만 추가합니다.
