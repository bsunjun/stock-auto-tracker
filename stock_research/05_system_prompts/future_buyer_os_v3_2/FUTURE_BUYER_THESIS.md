# Future Buyer Thesis — 데이터 구조

> "나 다음에 누가 살 것인가" 는 직관이 아니라 **데이터 구조**로 표현됩니다.

이 문서는 [`schemas/future_buyer_thesis_pack.schema.json`](./schemas/future_buyer_thesis_pack.schema.json) 의
설계 근거(rationale)와 buyer 군집 정의입니다.

## 1. buyer_type 분류

| 값 | 의미 | 단서 (어디서 나타나는가) |
|---|---|---|
| `institution` | 기관 (운용사, 보험, 은행 등) | WiseReport 목표주가 상향 + DART/IR 가이던스 + 키움 기관 매수 누적 |
| `retail_attention` | 개인 관심 | 신문/포털 헤드라인 + Telegram 확산 + 검색 트래픽 추정 |
| `fast_money` | 단기성 자금 (헤지펀드형, 단타 자금) | Telegram 채널 sync + 분단위 거래량 spike + 공매도 잔고 변화 |
| `foreign` | 외국인 | 키움 외국인 net buy + 글로벌 동종섹터 흐름 + ADR/2x ETF 흐름 |
| `financial_investment` | 금융투자(증권 자기매매) | 키움 금융투자 net buy + 단기 매수 패턴 |
| `pension` | 연기금 | 키움 연기금 net buy + 중장기 누적 + 정책 기금 발표 |
| `short_cover` | 숏커버 | 공매도 잔고 감소 + 대차 잔고 변화 + 거래량 급증 |

## 2. 필수 필드

`future_buyer_thesis_pack` 의 각 thesis 항목에는 다음 필드가 필수입니다.

- `buyer_type` — 위 분류 중 하나(또는 다중 선택).
- `why_they_buy` — 그 buyer 군집이 매수하는 **명분**. 한 줄 요약 + supporting layer 참조.
  - 예: "운용사가 분기 가이던스 상향분을 반영해 portfolio rebalancing — Layer 4 + Layer 5 근거"
- `when_they_buy` — 매수 시점의 **트리거**. 정량 가능하면 정량.
  - 예: "외국인 5일 net buy 누적 ≥ 시총의 0.3%, KOSPI 일중 약세에서도 양매수 유지"
- `invalidation_condition` — 이 thesis 가 **무효가 되는 조건**. 정량 가능하면 정량.
  - 예: "외국인이 연속 3일 net sell 또는 일 거래대금 절반 이상 비중에서 분배(distribution) 패턴"

## 3. 작성 가이드

- 한 후보에 thesis 가 여러 buyer_type 으로 동시 존재할 수 있습니다. 단, **가장 강한 단서를 가진 1개 이상은 명시적으로 ranked**.
- `why_they_buy` 는 **그들의 목적함수** 관점에서 서술합니다. "주가가 오를 것 같아서"는 잘못된 서술입니다.
  - 올바른 서술 예: "연기금은 정책 펀드 자금 투입 시점에 우선주/대형주 비중 증가가 의무 — Layer 1 정책 발표 + Layer 6 연기금 누적 매수가 단서"
- `when_they_buy` 는 **시점**을 묘사합니다. 가격 레벨은 secondary 입니다.
- `invalidation_condition` 이 정의되지 않은 thesis 는 스키마 위반입니다. 무효 조건이 없는 thesis는 thesis가 아닙니다.

## 4. PB 상태 승격에서의 역할

- `PB_TRIGGER` 등급은 **future_buyer_thesis 가 명확**하고 `invalidation_condition` 이 정량 정의될 때만 부여됩니다.
- thesis가 정성적이거나 모호하면 최대 `PB_SCOUT` 까지만 허용됩니다.
- 단일 thesis가 Telegram-only 단서에 의존하면 thesis 전체가 무효(승격 불가).

## 5. 금지 표현

- "사야 한다", "지금이 매수 타이밍" 같은 단정적 매수 표현은 thesis 본문에 사용하지 않습니다.
- 매매 의사결정은 인간(human gate)이 합니다. thesis는 그 의사결정을 위한 **구조화된 가설**입니다.
