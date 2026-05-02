# 04_ChartSupplyReader — Daily Prompt

## 목적

오늘 기준 **키움 매수주체 net flow (Layer 6)** 와 **TradingView 차트 zone (Layer 7)** grounding.

## 입력

- 키움 매수주체 일/분 단위 집계 스냅샷 (개인 식별정보 제거된 것).
- TradingView 차트 캡션 메모 (이미지 자체는 INBOX 에 있고 출력에 임베드 금지).

## 산출 pack

- `actual_buyer_confirmation_pack` (Layer 6)
- `chart_timing_pack` (Layer 7)

## 작성 원칙

- buyer 군집은 enum 안에서만: `foreign`, `institution`, `pension`, `financial_investment`, `insurance`, `bank`, `private_equity`, `retail`, `program`, `other_inst`.
- net flow 단위와 윈도우(`window`) 명시.
- chart zone 은 가격 범위 + `zone_reason`.
- 보조 지표(MA/MACD/RSI 등)는 보조이지 단독 신호 아님.
- `target_price` 가 등장하면 `secondary_reference`.
- `edge_declared` 필수.
- `direct_trade_signal=false`, `trade_signal in (null, false)`.

## 금지

- 단정 매수가/손절가/목표가 출력.
- 키움 매매화면 캡처에서 사용자 식별정보 출력.
