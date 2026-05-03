# 06 이벤트 리스크 재점검 (Event-Risk Recheck)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 언제 실행하는가

- 장전 (01 단계) 직후, 그리고 장중 임의 시점에 새 공시 / 뉴스가
  발생할 때.
- 보유 / 후보 종목에 직접 영향 가능한 이벤트가 떠오를 때.

본 단계는 **이벤트로 인한 셋업 무효화** 와 **자격 박탈
(disqualification)** 을 잡는 게 목적이다.

---

## 1. 점검 항목

각 보유 / 후보 종목에 대해 다음을 확인한다:

### 1.1 공시 (DART / KIND)
- 정정공시.
- 자율공시 / 주요사항보고서.
- 거래량 / 가격 변동 사유 답변.
- 단일판매 / 공급계약 / 양도양수.
- 자기주식 취득 / 처분.
- 유상증자 / 무상증자 / 감자.
- 합병 / 분할 / 인적분할 / 물적분할.

### 1.2 거래소 지정 / 조치
- 투자주의 (`investment_attention`).
- 투자경고 (`investment_warning`).
- 투자위험 (`investment_risk`).
- 관리종목 (`administrative_issue`).
- 거래정지 (`trading_halt`).
- 상장 적격성 실질심사 (`listing_review`).

이 중 어떤 라벨이라도 적용되면 → daily focus list 에서 즉시 제거,
보유 시 즉시 청산 평가.

### 1.3 자본 이벤트
- 유상증자 / CB / BW / EB 발행 결정.
- 대규모 보호예수 해제 임박.
- 무상증자 권리락 / 배당락.

이벤트 윈도우 안의 신규 진입은 `event_window` 노트를 ticket 에 명시.

### 1.4 계약 / 사업
- 대규모 계약 취소 / 축소.
- 주요 고객 이탈.
- 주요 임원 이탈.
- 회계 감사 의견 수정.
- 외부 감사인 변경.

### 1.5 매크로 / 정책
- BoK 금리 / 한국 정부 정책.
- 산업 규제 변화.
- 글로벌 매크로 (FOMC / 미 CPI / 미 PPI / 미 PMI / 미 고용 / 환율).

---

## 2. 출력 형태

각 발견 항목에 대해:

```yaml
asof: <YYYY-MM-DDTHH:MM:SS+09:00>
name: <anonymized identifier>
event_type: filing | designation | capital_event | contract | macro
source_tier: 1 | 2 | 3 | 4 | 5
source: <url or attribution>
summary: <한 줄 중립 요약, 따옴표 인용 시 출처 명시>
impact_class: setup_invalidating | size_reducing | observation_only
action_required: <full_exit | partial_exit | demote | observation>
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```

---

## 3. 발견 시 절차

- `setup_invalidating` → 즉시 daily focus 에서 제거. 보유 시 즉시
  청산 평가 (인간 게이트 통과 후 운영자가 결정).
- `size_reducing` → 다음 ticket 의 `size_plan` 에 적용 / 기존 보유
  의 trim-into-weakness 트리거 갱신.
- `observation_only` → 노트로 남기고 다음 점검 사이클까지 유지.

---

## 4. 금지

- 단일 이벤트 발견을 근거로 자동 실행 금지.
- 단정적 매수 / 매도 표현 금지.
- Tier 5 (Telegram-only) 단일 발견을 근거로 size 변경 금지 — Tier
  1~3 출처로 교차 확인 필요.
- 안전 플래그 변경 금지.

---

## 5. 산출물

- 발견 항목 리스트 (위 출력 형태).
- 영향받은 ticket / position_update 갱신.
- 저널에 한 줄 메모 (어느 이벤트가 어느 종목의 어떤 분류를 바꿨는가).
