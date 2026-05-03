# 주간 리뷰 프롬프트 (Weekly Review Prompt, KR)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 사용 시점

- 주중 마지막 거래일 장후 (보통 금요일).
- `04_close_review_ko.md` 와 `05_post_close_next_day_prep_ko.md` 가
  끝난 후 작성.

본 프롬프트는 주간 리뷰 산출물을 생성하기 위한 한국어 명령형 가이드다.
산출물은 `weekly_review_template.md` 형식과
`schemas/weekly_review.schema.json` 형식 양쪽을 만족해야 한다.

---

## 1. 입력으로 모을 것

- 이번 주 5세션 의 일자별 저널 항목.
- 이번 주 모든 `trade_ticket` 인스턴스.
- 이번 주 모든 `position_update` 인스턴스.
- 이번 주 모든 `audit_pack` 인스턴스.
- 이번 주 추가된 모델북 항목.
- 이번 주 시작/종료 시점의 `market_cycle` 페이로드.
- 드로우다운 거버너 상태 (week_start / week_end).

---

## 2. 작성 순서 (위 weekly_review_template.md 의 12개 섹션)

각 섹션을 빠짐없이 채운다. 비어있는 섹션은 명시적으로 `n_a` 라고
표시.

1. 시장 레짐 (MCS-KR)
2. 주도 업종
3. 후보 품질
4. 실행 티켓
5. TOR 관리
6. exit 품질
7. process adherence
8. 모델북 업데이트
9. expectancy 리뷰
10. 드로우다운 거버너 상태
11. 다음 주 focus
12. signal safety (반드시 4개 플래그)

---

## 3. 한국어 작성 톤

- 서술적·중립적. 매수/매도 단정 표현 금지. 가격 예측 금지. 목표가
  금지.
- 종목명은 익명화 식별자 (`anonymized identifier`) 만 사용.
- 매크로 코멘트는 1차 출처 (DART, KRX, 중앙은행 발표) 우선 인용,
  2차 코멘트 (신문/리포트) 는 출처 명시.
- Telegram-only 정보는 어떤 결론도 지지하지 않는 것으로 처리.

---

## 4. mistake taxonomy 분류

이번 주 발생한 모든 일탈을 다음 분류 중 하나 이상으로 태깅:

- `process_skip` — 필수 단계 (audit/schema/gate) 우회.
- `tactic_drift` — entry tactic 의 trigger / failure 가 세션 중
  임의 조정.
- `stop_drift` — stop 을 넓히거나 평가 기준이 선언 외로 적용.
- `size_overrun` — stage cap / TOR 위반.
- `sector_overrun` — 섹터 캡 위반.
- `correlation_overrun` — 상관관계 throttle 위반.
- `audit_override` — Auditor block / revise_required 무시.
- `gate_override` — Human Gate deny 무시.
- `signal_leak` — 단정적 매수/매도 표현, 가격 단정, 안전 플래그
  truthy 시도.
- `evidence_gap` — Tier-5 단일 근거 진입.
- `time_window_breach` — 시초/종가 동시호가, 사이드카/서킷
  브레이커 중 거래.

---

## 5. expectancy 산출

```
expectancy_r = hit_rate * avg_winner_r - (1 - hit_rate) * abs(avg_loser_r)
```

이 값을 다음 주 `K` 조정의 입력으로 사용:

- `expectancy_r` 가 음수이고 process adherence 가 낮음 → `dial_down`.
- `expectancy_r` 가 양수이고 process adherence 가 높음 → 기본 `hold`,
  과거 N주 일관 시 `dial_up`.
- 그 외 → `hold`.

---

## 6. 다음 주 focus 노트

- carry-over watchlist (active 상태) 종목 수.
- tactic-ready 임박 종목 수.
- 다음 주 알려진 이벤트 윈도우 (실적 발표 / FOMC / BoK / 정책
  발표 / 지정 변경 가능성).
- 기본값 조정 (있을 경우 합리화 1줄).

---

## 7. 산출물 검증

- `weekly_review_template.md` 의 모든 섹션 채워짐.
- `schemas/weekly_review.schema.json` 으로 검증.
- 4종 안전 플래그 정확히 명시:
  ```yaml
  direct_trade_signal: false
  trade_signal: null
  automatic_execution_allowed: false
  human_gate_required: true
  ```

검증 실패 시 산출물을 발행하지 않는다.

---

## 8. 금지

- 단정적 매수/매도 표현.
- 가격/목표가 예측.
- 익명화되지 않은 실종목명 노출.
- 안전 플래그 변경.
- 자동 실행 권한 부여.
