# 일일 감사 프롬프트 패치 (Daily Audit Prompt Patch, KR)

본 문서는 일일 운영 / 감사 프롬프트에 **추가**할 한국어 문구를
정리한다. 기존 PBKR v4 doctrine 의 어떤 항목도 약화시키지 않으며,
본 PR 이 새로 도입한 Risk-Flag Pullback Policy 를 운영 흐름에
일관되게 반영하기 위한 patch 이다.

본 문서는 실제 종목명, 실제 가격, 실제 공시번호, 실제 주문/계좌
데이터를 포함하지 않는다.

## 일일 프롬프트에 추가할 문구

다음 일곱 줄을 일일 운영 프롬프트 / 감사 프롬프트에 그대로
포함한다.

> 공식 리스크 플래그는 먼저 taxonomy 로 분류한다 (분류 A / B / C / D).

> 분류 A (관리종목, 상장폐지 실질심사, 거래정지, 불성실공시,
> 감사의견 문제, 횡령/배임, 회생/파산) 는 `HARD_EXCLUDE` 다.

> 분류 B (투자주의, 투자경고 지정예고, 투자경고, 단기과열 예고/지정,
> 공매도 과열) 는 market-structure cooling risk 다.
> 일반 `PB_TRIGGER` 로 승격하지 않으며, `REGULAR_PB_EXCLUDE` 가
> 기본값이고 별도 조건 충족 시 `RISK_FLAG_PULLBACK_WATCH` 로만
> 라벨링한다.

> 분류 C (투자위험 지정예고, 투자위험종목, 투자경고 후 정지 임박)
> 는 `EXTREME_RISK_FLAG_WATCH` 다. 신규 진입을 보류하며, 해제 후에만
> 분류 B 의 `RISK_FLAG_PULLBACK_WATCH` 로 재분류할 수 있다.

> 분류 D (매매거래정지, 상장폐지 실질심사 관련 정지, 공시불이행
> 거래정지) 는 `NO_ENTRY` 다.

> 어떤 status label 도 매수 신호 / 자동 실행 / 본진 진입을 의미하지
> 않는다.

> 모든 분류 작업 결과는 private journal 에만 기록한다.

## 감사 시 확인할 항목

- [ ] 일일 후보 / 관찰 노트가 위 일곱 줄을 적용했는지 확인.
- [ ] 분류 A (`HARD_EXCLUDE`: 관리종목, 상장폐지 실질심사, 거래정지,
      불성실공시, 감사의견 문제, 횡령/배임, 회생/파산) 에 해당하는
      이름이 watch / candidate 어디에도 포함되지 않았는지 확인.
- [ ] 분류 C (`EXTREME_RISK_FLAG_WATCH`: 투자위험 지정예고,
      투자위험종목, 투자경고 후 정지 임박 단계) 에 해당하는 이름이
      `RISK_FLAG_PULLBACK_WATCH` 또는 `PB_TRIGGER` 로 라벨링되어
      있지 않은지 확인. 신규 진입이 보류 상태로 운영되고 있는지
      확인.
- [ ] 분류 D (`NO_ENTRY`: 매매거래정지, 상장폐지 실질심사 관련
      정지, 공시불이행 거래정지) 에 해당하는 이름이 watch /
      candidate 어디에도 포함되지 않았는지 확인.
- [ ] 분류 B (`REGULAR_PB_EXCLUDE`) 에 해당하는 이름이
      `PB_TRIGGER`, 본진, 매수 신호, 자동 실행 어휘로 표현되어
      있지 않은지 확인.
- [ ] 분류 B 의 이름이 `RISK_FLAG_PULLBACK_WATCH` 라는
      labelled status 로만 다뤄지는지 (그리고 사전 조건 PASS 시
      에만 라벨링되는지) 확인.
- [ ] 자동 실행 (`automatic_execution_allowed` truthy), truthy 한
      `trade_signal` / `direct_trade_signal`, 또는 `operator_decision`
      필드가 execute 리터럴로 설정된 경로가 어디에도 등장하지
      않는지 확인.
- [ ] private journal 외부 (본 repo, Drive, Telegram, mail 등)
      로 새 observation output 이 흘러가지 않았는지 확인.

## 적용 우선순위

1. 분류 D → `NO_ENTRY`. 정지 상태 동안 신규 / 추가 진입 / 관찰
   후보 등재 모두 하지 않는다.
2. 분류 A → `HARD_EXCLUDE`. 즉시 배제. 풀백 / 관찰 검토를 하지
   않는다.
3. 분류 C → `EXTREME_RISK_FLAG_WATCH`. 신규 진입 보류. 공식 해제
   이전까지 `RISK_FLAG_PULLBACK_WATCH` 로 다루지 않는다.
4. 분류 B → 기본값 `REGULAR_PB_EXCLUDE`. 정상 풀백 경로
   (`PB_TRIGGER`, 본진 진입) 에서 제외한다.
   `RISK_FLAG_PULLBACK_WATCH_CHECKLIST.md` 의 모든 사전 조건이
   PASS 한 경우에만 `RISK_FLAG_PULLBACK_WATCH` 로 라벨링한다.
   그 이상으로 승격하지 않는다.

## 절대 금지

- 분류 B 또는 분류 C 를 매수 신호로 해석하는 한국어 문구 추가.
- 분류 B / 분류 C 를 자동 실행 / 자동 알림 경로에 연결.
- 분류 A / 분류 D 를 watch posture 로 끌어올리는 표현.
- `RISK_FLAG_PULLBACK_WATCH` 또는 `EXTREME_RISK_FLAG_WATCH` 를
  `PB_TRIGGER` 와 동의어처럼 사용.
- 분류 C 를 `RISK_FLAG_PULLBACK_WATCH` 로 직접 라벨링 (해제 후에만
  재분류 가능).
- 본 patch 가 doctrine 을 약화시킨다는 해석.

## 범위 밖

- 자동 prompt 주입 도구.
- 실제 종목 / 실제 가격 / 실제 공시 데이터.
- 자동 실행 / 자동 알림 / 외부 시스템 write.
