# 관찰 Day 0 사전 점검 (Observation Day 0 Pre-Check, KR)

본 문서는 read-only real-data observation 을 시작하기 전에 사람이
직접 수행해야 할 **Day 0 precheck** 한국어 체크리스트이다. PR #62
자체는 실제 데이터를 수집하지 않는다. 본 문서의 Day 0 precheck 도
실제 데이터를 사용하지 않으며, 사전 환경/정책 점검만을 다룬다.

## 전제

- Day 0 은 실제 데이터 수집 단계가 **아니다**.
- Day 0 은 자동화 단계가 **아니다**. 모든 항목은 사람이 직접
  확인한다.
- Day 0 의 결과는 본 repo 가 아닌 **private journal** 에만
  기록한다.

## 1. Repo 상태 확인

- [ ] PR #50 (Core Doctrine) main 반영 확인.
- [ ] PR #52 (Operating Package) main 반영 확인.
- [ ] PR #53 (Activation / Operator Runbook) main 반영 확인.
- [ ] PR #54 (Anonymized Dry-Run Fixtures) main 반영 확인.
- [ ] PR #55 (Non-Execution Fixture Validator) main 반영 확인.
- [ ] PR #56 (Dry-Run Report Template) main 반영 확인.
- [ ] PR #57 (First-Week Dry-Run Checklist) main 반영 확인.
- [ ] PR #58 (Second-Week Anonymized Candidate Extension) main
      반영 확인.
- [ ] PR #59 (Real-Data Boundary Planning Checklist) main 반영
      확인.
- [ ] PR #60 (Read-Only Real-Data Observation Plan) main 반영 확인.
- [ ] PR #61 (Read-Only Observation Approval Packet) main 반영
      확인.
- [ ] PR #62 (this Start Gate) main 반영 확인.

## 2. 승인 문구 확인

- [ ] private journal 의 approval 항목에 정확히 다음 문장만
      기록되었는지 확인.
  > read-only real-data observation only
- [ ] 금지 승인 문구(`trade allowed`, `auto execution allowed`,
      `order enabled`, `signal enabled`, `live trading enabled`,
      `candidate scoring enabled`, `broker connection enabled`,
      `Kiwoom enabled`, `real trading enabled`) 가 어느 줄에도
      등장하지 않는지 확인.

## 3. No-Execution Guardrails 확인

- [ ] `automatic_execution_allowed` 플래그가 truthy 로 설정된 경로
      가 없는지 확인.
- [ ] `direct_trade_signal` 플래그가 truthy 로 설정된 경로가 없는지
      확인.
- [ ] `trade_signal` 필드가 truthy 또는 숫자 `1` 로 설정된 경로가
      없는지 확인.
- [ ] `operator_decision` 필드가 execute 리터럴로 설정된 경로가
      없는지 확인.

## 4. 외부 연결 부재 확인

- [ ] broker 연결 (live/sandbox) 부재 확인.
- [ ] 외부 trading API 연결 부재 확인.
- [ ] Kiwoom (또는 동급 retail-broker) order path 부재 확인.
- [ ] WiseReport 자동 feed 부재 확인.
- [ ] Drive 자동 동기화 부재 확인.
- [ ] webhook alert 부재 확인.
- [ ] 자동 알림 (email/SMS/push/mobile/messaging) 부재 확인.

## 5. 출력 자세 확인

- [ ] 본 repo 에 실제 observation output 을 commit 하지 않는다는
      원칙이 유지되는지 확인.
- [ ] private journal 의 저장 위치가 사람에게 명확한지 확인.
- [ ] 실제 candidate / dry-run / validator / approval / observation
      output 이 본 repo 에 들어가지 않을 것이라는 점을 재확인.

## 6. 정책 확인

- [ ] real-data 허용 field 정책 (PR #60 의 field allowlist) 확인.
- [ ] real-data 금지 field 정책 (PR #59 / PR #60 의 prohibited
      categories) 확인.
- [ ] redaction / storage 정책 (PR #60) 확인.
- [ ] no-execution guardrails (PR #60) 확인.
- [ ] approval wording 요구 사항 (PR #61) 확인.
- [ ] observation start blockers (PR #61) 확인.

## 7. 중단 조건 사전 인지

- [ ] `OBSERVATION_ABORT_CONDITIONS.md` 의 즉시 중단 조건을 사람이
      먼저 읽고 인지했는지 확인.

## 미충족 시 조치

- 위 항목 중 하나라도 미충족이면 observation 을 시작하지 **않는다**.
- 미충족 사항은 private journal 에 사실관계만 한 줄로 기록한다.
- 미충족 기록은 본 repo 에 commit 하지 **않는다**.
- 재시도 시 Day 0 precheck 전체를 처음부터 다시 수행한다.

## 범위 밖

- 실제 데이터 수집.
- 실제 가격, 수급, 뉴스, 공시 정보 처리.
- 자동 실행, 자동 알림, 주문 준비, candidate scoring.
- broker / API / Kiwoom / WiseReport / Drive 연결.
