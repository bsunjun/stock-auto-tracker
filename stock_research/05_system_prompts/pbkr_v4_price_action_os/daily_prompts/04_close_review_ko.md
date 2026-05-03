# 04 장마감 리뷰 (Close Review, KST 15:30–16:30)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 목적

장이 끝난 직후 보유 / 후보 / 리스크 / stop migration 을 점검하고,
오늘의 거래·관찰을 저널에 기록한다. 이 단계는 **다음 거래일 준비
전 단계** 다 — 다음 거래일 daily focus list 는 05 단계에서 만든다.

---

## 1. 보유 포지션 점검

각 보유 종목에 대해:

- 종가 기준 stop 위반 여부 → 위반 시 risk_stop 청산 처리.
- Structural exit 트리거 발동 여부:
  - failed higher-low
  - distribution print
  - two closes below MA (swing=21EMA, position=50SMA / 10주선)
  - failure_level 침범
  - 섹터 / 그룹 붕괴
  - key reversal bar
- Trim-into-strength 조건 충족 여부 (+5%, R-multiple, base
  extension 20–25%, climax-style session).
- Trim-into-weakness 조건 충족 여부 (첫 close below MA, failed HL test,
  adverse group signal).
- Time-stop window 카운트 업데이트.

각 발동에 대해 `position_management_ticket_template.md` 작성.

---

## 2. Stop Migration 결정

규칙:

- 보유 종목이 doctrinal trim-into-strength 를 완료했다면 → 잔여 분
  stop을 **breakeven** 으로 이동.
- 보유 종목이 confirmed higher-low 를 형성했다면 → stop을 그
  higher-low 아래 (변동성 버퍼 차감) 로 이동.
- **stop은 절대 넓히지 않는다**. 넓히는 것은 `stop_drift` mistake.

각 migration 결정을 `position_update` 페이로드로 기록.

---

## 3. TOR / 섹터 / 상관관계 점검

- 종가 기준 `total_open_risk_pct` 갱신.
- `K * tor_ceiling_pct` 대비 헤드룸 계산.
- 섹터 캡 / 상관관계 throttle 갱신.
- 드로우다운 거버너 트리거 여부:
  - mild → R, K 0.75 스케일.
  - moderate → 0.50 스케일.
  - severe → 0.25 스케일 + 신규 진입 일시 중지.

---

## 4. 오늘 후보의 재분류

오늘 daily focus list 의 각 항목에 대해:

- 진입했는가? → `executed`
- 5/5 통과했지만 운영자가 미진입했는가? → `passed_gate_no_act`
- watch 로 남겼는가? → `watch_carry`
- demote 되었는가? → `demoted`
- thesis 손상으로 watchlist 에서 retired 되는가? → `retired`

각 분류에 대한 한 줄 사유.

---

## 5. 리스크 노트

- 오늘 가장 위험했던 모멘트 한 개를 적는다.
- 룰 위반이 있었다면 mistake taxonomy 항목으로 기록
  (`process_skip` / `tactic_drift` / `stop_drift` / `size_overrun` /
  `sector_overrun` / `correlation_overrun` / `audit_override` /
  `gate_override` / `signal_leak` / `evidence_gap` /
  `time_window_breach`).

---

## 6. 저널 항목

세션 저널 (개인 / 비공개) 에 다음을 기록:

- 종가 stage / sub-grade / K / TOR_pct / 섹터 분포.
- 오늘 진입 / 청산 / 조정 요약.
- 위반 / 교훈 / corrective action.
- 모델북 부속 항목 (closed trade 가 있었다면).

저널은 **저장소에 커밋되지 않는다**. 본 PR 의 운영 패키지는 템플릿만
제공한다.

---

## 7. 금지

- 본 단계에서 신규 진입 금지.
- 단정적 매수 / 매도 표현 금지.
- stop 을 넓히는 변경 금지.
- 안전 플래그 변경 금지.

---

## 8. 산출물

- 보유별 `position_update` (트리거 발동 시).
- TOR / K / 섹터 / 상관관계 갱신 노트.
- 오늘 daily focus list 항목별 분류.
- 모델북 후보 항목 메모 (entry 가 닫힌 경우).

이 산출물은 05 단계 (다음날 준비) 의 입력으로 흘러간다.
