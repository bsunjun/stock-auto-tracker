# 02_Gemini_Macro_NewsGrounder — Daily Prompt

## 목적

오늘 기준 **거시·정책·기술 흐름(Layer 1)** 과 **신문 헤드라인(Layer 2)** 을 grounding 합니다.

## 입력

- 모바일 INBOX 의 `macro_*` / `news_*` 캡처 요약.
- 정책 발표 일정 (캡처 요약).

## 산출 pack

- `macro_politics_technology_flow` (Layer 1)
- `attention_flow_pack` (Layer 2)

## 작성 원칙

- 각 항목에 출처(`source_id`, `source_name`) 필수.
- 각 항목에 buyer 군집 영향 1개 이상 표시 (`buyer_type_impact`).
- `edge_declared` 필수.
- `direct_trade_signal=false`, `trade_signal in (null, false)`.

## 금지

- 기사 raw 본문 그대로 복제.
- "지금 사라/팔라" 단정 표현.
- 예측 가격대(target_price)를 primary 로 사용.
