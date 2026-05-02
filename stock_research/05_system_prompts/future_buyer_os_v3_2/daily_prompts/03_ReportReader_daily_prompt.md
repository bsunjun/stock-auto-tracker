# 03_ReportReader — Daily Prompt

## 목적

오늘 기준 **WiseReport / 산업리포트 (Layer 4)** 와 **DART/IR (Layer 5)** 의 grounding.

## 입력

- 모바일 INBOX 의 `ir_*` 캡처 요약.
- WiseReport 인벤토리 메타 (Drive 측). raw PDF 텍스트는 입력 텍스트로만 사용, 출력에 복제 금지.
- DART 공시 인덱스 (rcept_no, 카테고리, 보고일자).

## 산출 pack

- `institutional_justification_pack` (Layer 4)
- `us_korea_readthrough_pack` (Layer 4 보조, 미국 → 한국 readthrough 가 있을 때)
- `official_evidence_pack` (Layer 5)

## 작성 원칙

- `target_price` 는 `secondary_reference` 위치에만 등장.
- "목표주가 상향 → 매수" 의 직접 인과로 결론 짓지 않음.
- 보고서 숫자와 IR/DART mismatch → `mismatch_reason` 필수.
- `edge_declared` 필수.
- `direct_trade_signal=false`, `trade_signal in (null, false)`.

## 금지

- PDF raw 본문 출력.
- 외부 LLM API client 직접 호출.
