# 02 시초 가격 발견 (Opening Discovery, KST 09:00–09:15)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 핵심 원칙

**관찰만 한다. 신규 실행은 금지한다.**

09:00 동시호가는 밤사이 정보가 단일 가격으로 압축되는 시점이다. 이
구간의 인쇄(print)는 가격 발견이지 확인(confirmation)이 아니다.
PBKR v4 doctrine상 이 시간대의 신규 진입은 비도덕(non-doctrinal)이다.

---

## 1. 무엇을 보는가

- KOSPI / KOSDAQ 시초 갭 / 시초 호가창 / 외인·기관 시초 추정.
- 어제 단일가 마감 대비 시초가의 위치.
- 일일 포커스 리스트의 각 종목 시초 위치:
  - 시초가 entry tactic의 `trigger_level`을 크게 돌파했나?
  - 시초가 `failure_level` 아래에서 시작했나?
  - 갭과 동시에 거래량이 평소 대비 어떤가?

---

## 2. 어떻게 기록하는가

각 포커스 종목에 대해 한 줄 노트:

```
<name>: open=<text>, vs trigger=<above|near|below>, vs failure=<above|near|below>, gap_volume=<low|normal|high>, action=<observe|demote|maintain>
```

판정 규칙:

- 시초가 `trigger_level` 보다 크게 위 → **demote** (추격 금지, 오늘
  세션에서 이 종목 신규 진입은 배제).
- 시초가 `failure_level` 아래 → **demote** (셋업 손상).
- 시초가 정상 범위 → **maintain** (본장에서 확인 필요).

---

## 3. 보유 종목 모니터링

- 시초가 stop level을 종가 기준 평가가 아닌 **하드 스탑** 기준 위반
  하면 본장 개시 후 첫 가능 시점에 처리한다 (단,
  `stop_evaluation_basis = closing` 인 경우에는 종가까지 기다린다).
- 시초 갭 + 즉시 반전 + 대량 거래량은 분배(distribution) 인쇄
  후보 — 본장 구조적 청산(structural exit) 트리거로 마킹한다.

---

## 4. 사이드카 / 서킷브레이커

- 발동 시 본 구간의 인쇄는 **비-증거(non-evidence)** 로 간주.
- 발동이 풀리고 양방향 유동성이 회복된 후에야 패턴 해석을 다시 시작한다.

---

## 5. 금지

- 동시호가 구간 내 / 09:15 이전 신규 진입 금지.
- 09:15 이전 add-on entry 금지.
- 단정적 매수 / 매도 표현 금지.
- 추격(chase) 금지.
- 안전 플래그 변경 금지.

---

## 6. 산출물

- 일일 포커스 리스트의 각 종목별 한 줄 시초 노트.
- 각 종목의 `action` 라벨 (`observe` / `demote` / `maintain`).
- 보유 종목 stop / 구조 변경 메모.

본 산출물은 03 본장 S.N.I.P.E. 체크 단계의 입력으로 흘러간다.
