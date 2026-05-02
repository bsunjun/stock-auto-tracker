# Human Gate Checklist

`PB_SCOUT` 또는 `PB_TRIGGER` 승격 시 사람(human gate)이 직접 확인하는 체크리스트.

## 공통

- [ ] 후보의 `edge_declared` 가 한 줄로 명확히 채워져 있다.
- [ ] `direct_trade_signal == false`, `trade_signal in (null, false)` 인지 확인.
- [ ] `target_price` 가 primary 위치에 사용되지 않았다.
- [ ] Telegram-only 단서로 PB_READY 이상이 부여되지 않았다.
- [ ] L8 risk flag 매치가 **없다**.

## PB_SCOUT 특수

- [ ] L4 (institutional) + L5 (DART/IR) + L1/L2 매크로/관심 흐름 일치 확인.
- [ ] L6 actual buyer net flow 의 buyer_type 가 thesis 와 정합.
- [ ] L7 chart timing zone 진입 (가격이 아니라 시간대 기준).
- [ ] Layer 9 thesis 의 `invalidation_condition` 이 정량 또는 정량에 가까운 표현으로 기재.

## PB_TRIGGER 특수

- [ ] PB_SCOUT 모든 조건 충족.
- [ ] thesis 의 `ranked=1` thesis 가 단 하나로 명확.
- [ ] `invalidation_condition` 이 정량 표현 (예: 외국인 net sell N일, 거래대금 비중 X% 이상 분배 등).
- [ ] 자동 실행 금지 — 주문은 사람이 별도 도구로.

## 강등 즉시 트리거

- L8 risk flag 신규 매치.
- 24시간 이내 buyer_type 가 thesis 와 반대 방향으로 전환.
- `invalidation_condition` 이 사후적으로 충족됨.
