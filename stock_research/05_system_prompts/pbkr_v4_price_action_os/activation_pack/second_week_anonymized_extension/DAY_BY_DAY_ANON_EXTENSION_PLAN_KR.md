# 두 번째 주 익명 후보 확장 — 일자별 계획 (KR)

이 문서는 PBKR v4 dry-run 프로그램의 **두 번째 주** 일자별 운영 계획이다.
첫 주(PR #54~#57)의 고정 fixture(S1~S6, *Candidate A/B/C*) 검증을
완료한 운영자가, 두 번째 주에 *Candidate X / Candidate Y / Candidate Z*
라는 새로운 익명 후보를 직접 만들어보는 훈련 단계이다.

## 공통 원칙

- 모든 후보는 **익명**으로만 작성한다.
  허용 이름은 `Candidate X / Candidate Y / Candidate Z` 뿐이다.
- 실제 종목명, 실제 종목코드, 실제 가격, 실제 뉴스, 실제 공시번호,
  실제 거래량, 실제 수급, 실제 계좌는 어떤 형태로도 사용하지 않는다.
- 모든 날짜 값은 `2099-` 접두 합성 날짜만 사용한다.
- 매일의 결과는 **개인 journal에만** 기록한다.
  생성된 candidate JSON, validator 출력, 리뷰 노트는 **repo에 commit
  하지 않는다.**
- 매일 `validate_fixtures.py` 를 실행하여 schema 부합 여부를
  확인하되, `PASS` 는 매수/매도 신호도, 실행 권한도 아니다.
- 모든 후보에는 `human_gate` 와 `signal_safety` 섹션이 반드시
  포함되어야 한다.
- 자동 실행, 자동 주문, 자동 알림 어떤 것도 허용되지 않는다.

## Day 1 — Candidate X clean-pass 초안

- 목표: clean-pass 시나리오 한 건을 *Candidate X* 로 익명 작성.
- 필수 필드: setup, edge, entry_tactic, trigger_level (`anon-pivot-X`),
  failure_level (`anon-failure-X`), stop_logic, stop_level
  (`anon-stop-X`), sell_rules, human_gate, signal_safety.
- 동작: 로컬 임시 경로에 저장 → `validate_fixtures.py` 실행 → 결과를
  private journal에 기록 → 로컬 artifact 삭제.
- repo commit: **금지.**

## Day 2 — Candidate Y hard-veto 초안

- 목표: hard veto 시나리오를 *Candidate Y* 로 익명 작성.
- 포커스: 진입을 막는 invalidation 조건의 명확화. `anon-failure-Y`
  가 trigger 보다 명백히 우선시됨을 확인한다.
- 동작: validator 실행 후 hard veto 처리 흐름을 journal에 기록.
- repo commit: **금지.**

## Day 3 — Candidate Z Tier-5-only 강등(demotion)

- 목표: 출처 신뢰도가 낮은 정보(`synthetic-tier5-unattributable-channel`)
  만으로 후보가 구성될 때 자동 강등(demotion)되는 흐름을
  *Candidate Z* 로 작성.
- 확인: Tier-5 단독 입력은 격상되지 않으며, human_gate 없이는 절대
  실행 후보가 되지 않는다.
- repo commit: **금지.**

## Day 4 — Candidate X / Candidate Y TOR saturation

- 목표: TOR(Time-Of-Risk) 포화 상태를 모사. *Candidate X* 와
  *Candidate Y* 두 건을 동일 위험 슬롯에 배치하여, 신규 후보가
  포화 상태 때문에 실행 불가 처리되는 흐름을 점검한다.
- 확인: TOR 포화 시 신규 후보는 자동 보류되며, 우회 경로가
  존재하지 않는다.
- repo commit: **금지.**

## Day 5 — Candidate X gate-deny

- 목표: validator/schema는 PASS 이지만 운영자 human gate에서 명시적
  거부(deny)되는 흐름을 *Candidate X* 로 재구성.
- 확인: PASS ≠ 실행 권한. operator decision 이 deny 인 한 어떤
  실행 경로도 열리지 않는다.
- repo commit: **금지.**

## Day 6 — no-action synthetic day

- 목표: 그날의 후보가 단 한 건도 조건을 충족하지 않는 “no-action
  day” 를 합성 데이터로 재현한다.
- 확인: 후보 부재 자체가 정상 결과이며, 억지로 후보를 만들어내려
  하지 않는다.
- repo commit: **금지.**

## Day 7 — 주간 익명 확장 리뷰

- 목표: Day 1~Day 6 의 private journal 기록을
  `SECOND_WEEK_REVIEW_TEMPLATE.md` 에 따라 정리한다.
- 확인 항목:
  - 모든 후보가 *Candidate X / Y / Z* 익명 이름만 사용했는가.
  - 실제 데이터(종목명/가격/뉴스/공시번호/계좌)가 단 한 건도
    유입되지 않았는가.
  - 모든 후보에 human_gate, signal_safety 가 포함됐는가.
  - 생성된 candidate, validator 출력, 리뷰 노트가 repo에
    commit되지 않았는가.
  - 자동 실행 흔적이 전혀 없는가.
- 결과는 private journal에만 저장한다. repo에는 어떤 generated
  artifact 도 commit 하지 않는다.

## 다음 단계

두 번째 주 리뷰가 PASS 로 마감되더라도, 그 자체는 실데이터 단계로의
진입 권한이 아니다. 실데이터 단계는 **별도의 PR과 명시적 승인**을
요구하며, 본 PR(#58)의 범위를 벗어난다.
