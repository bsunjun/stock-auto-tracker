# 첫 주 dry-run 일별 실행 계획 (Day-by-Day)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.
>
> **이번 주는 dry-run only**. 실제 후보, 실제 종목, 실제 가격, 실제
> 뉴스, 실제 공시번호, 실제 주문은 등장하지 않는다.

---

## 0. 일별 공통 규칙

매일 적용되는 7가지 절대 금지:

1. 실제 종목명 / 종목코드 / 가격 / 뉴스 / 공시 / 주문 / 거래량 /
   수급 / 계좌 사용 금지.
2. 실제 validator console output 또는 instantiated report 를
   repository 에 commit 금지.
3. 자동 실행 / 자동 매매 / 외부 API 연결 / 브로커리지 연결 금지.
4. `direct_trade_signal` / `trade_signal` / `automatic_execution_allowed`
   를 truthy 로 설정 금지.
5. `operator_decision` 을 `"execute"` 로 설정 금지.
6. 한국어 retail-trading 단정 매매 표현 또는 영어 imperative
   buy/sell 구문 금지.
7. 인간 게이트 우회 또는 게이트 결과를 자동 권한 부여로 해석 금지.

매일 마지막에는 instantiated 한 dry-run report 초안을 운영자의
**비공개 저널**에만 저장한다 (이 repository 에 commit 하지 않는다).

---

## 1. Day 1 — 환경 확인 + Repo Sync + Validator 실행

### 1.1 목표
- 운영 환경이 PR #50–#56 의 모든 산출물을 정확히 가지고 있는지
  확인한다.
- `validate_fixtures.py` 가 6/6 PASS 로 동작하는지 확인한다.

### 1.2 단계
- [ ] `git fetch && git status` — `main` 이 최신 merge commit 까지
      반영되었는지 확인.
- [ ] `MANUAL_VALIDATION_CHECKLIST.md` (PR #53) 의 §1 / §2 를
      따라 PR #50 / PR #52 / PR #53 / PR #54 / PR #55 / PR #56
      의 모든 파일이 존재하는지 수동으로 확인.
- [ ] `cd activation_pack/dry_run_fixtures && python3 validate_fixtures.py`
      실행. `OVERALL: PASS`, exit 0 확인.
- [ ] 결과를 비공개 저널의 Day 1 entry 로 기록.

### 1.3 금지
- validator output 또는 setup 결과를 repository 에 commit 하지
  않는다. Day 1 산출물은 운영자의 비공개 저널에만 존재한다.

---

## 2. Day 2 — S1 + S2 hand-walk

### 2.1 목표
- S1 (clean pass) 과 S2 (hard veto) 시나리오를 운영자가 직접
  hand-walk 한다.

### 2.2 단계
- [ ] `cd activation_pack/dry_run_fixtures && python3 validate_fixtures.py` 실행 후 PASS 확인.
- [ ] `scenario_s1_clean_pass.fixture.json` 을 열고
      `HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md` 의 5단계 흐름 (Gemini
      → GPT → Claude Auditor → Claude Gate → Human → Claude
      Journal) 을 종이/저널에 따라가며 yes/no 체크.
- [ ] `scenario_s2_hard_veto.fixture.json` 도 같은 방식으로
      hand-walk. 단 audit 단계에서 `block` finding `A001` 이
      나오는지 확인.
- [ ] Day 2 entry 를 `DRY_RUN_REPORT_TEMPLATE.md` 형식으로 작성하여
      비공개 저널에 저장.

### 2.3 금지
- Candidate A / B 외에 다른 종목명 등장 금지.
- 실제 가격 / 뉴스 / 공시번호 도입 금지.
- gate `pass` 결과를 transaction permission 으로 해석 금지.

---

## 3. Day 3 — S3 + S4 hand-walk

### 3.1 목표
- S3 (Tier-5 demote) 와 S4 (TOR saturation) 시나리오를 hand-walk.

### 3.2 단계
- [ ] validator 실행 후 PASS 확인.
- [ ] `scenario_s3_tier5_demote.fixture.json` — Tier-5-only
      candidate 가 demote 되는지, audit finding `A204` 가 나오는지
      확인.
- [ ] `scenario_s4_tor_saturation.fixture.json` — focus list 가 2
      에서 1 로 압축되는지, lower-priority 항목이
      `revise_required` 와 `A102` 를 받는지 확인.
- [ ] Day 3 entry 를 비공개 저널에 저장.

### 3.3 금지
- Tier-5 단일 근거를 leader / position 분류로 승격하는 시도 금지.
- TOR ceiling 우회 시도 금지.
- 실제 데이터 도입 금지.

---

## 4. Day 4 — S5 + S6 hand-walk

### 4.1 목표
- S5 (gate deny) 와 S6 (no-action day) 시나리오를 hand-walk.

### 4.2 단계
- [ ] validator 실행 후 PASS 확인.
- [ ] `scenario_s5_gate_deny.fixture.json` — gate 가 `deny` 를
      반환하고 `unchecked_items` 가
      `sell_rules.time_stop_window_sessions` 를 포함하는지 확인.
- [ ] `scenario_s6_no_action_day.fixture.json` — Stage 4 정의 하에
      focus list 가 empty 인지, no-action journal 의 `reason_for_no_action`
      이 `regime_defensive` 인지 확인.
- [ ] Day 4 entry 를 비공개 저널에 저장.

### 4.3 금지
- gate `deny` 를 운영자 임의로 무시하는 시도 금지.
- empty focus list 를 process failure 로 잘못 해석 금지 (cash 는
  doctrinal posture).

---

## 5. Day 5 — Full Chain Rehearsal

### 5.1 목표
- 5단계 handoff 를 처음부터 끝까지 한 번 더 따라간다 (Gemini →
  GPT → Claude Auditor → Claude Gate → Human → Claude Journal).
- 6개 fixture 를 모두 한 자리에서 review 한다.

### 5.2 단계
- [ ] validator 실행 후 PASS 확인.
- [ ] 6개 fixture 를 순서대로 hand-walk (S1 → S2 → S3 → S4 → S5
      → S6).
- [ ] `DRY_RUN_REPORT_TEMPLATE.md` §1–§10 모든 섹션을 채운 Day 5
      종합 entry 를 비공개 저널에 저장.
- [ ] §10 Final Dry-Run Status 가 `PASS` / `RE-RUN_REQUIRED` /
      `FAIL` 중 무엇인지 단언.

### 5.3 금지
- Day 5 의 종합 entry 를 repository 에 commit 하지 않는다.
- `RE-RUN_REQUIRED` 또는 `FAIL` 인 경우, 운영자 임의 판단으로
  `PASS` 로 격상 금지.

---

## 6. Day 6 — Failure Scenario Rerun

### 6.1 목표
- Day 1–5 에서 발견된 issue 가 있다면 해당 시나리오를 다시
  hand-walk 한다.
- 발견된 issue 가 없다면 의도적으로 가장 까다로운 시나리오 (보통
  S2 hard veto 또는 S5 gate deny) 를 한 번 더 rehearse 한다.

### 6.2 단계
- [ ] validator 실행 후 PASS 확인.
- [ ] 선택한 시나리오의 fixture 를 다시 hand-walk.
- [ ] 운영자가 잘못 해석할 수 있었던 부분이 있는지 점검.
- [ ] Day 6 entry 를 비공개 저널에 저장.

### 6.3 금지
- 시나리오 재실행 결과를 자동 권한 부여로 해석 금지.
- 모의 reset 명목으로 안전 플래그 변경 금지.

---

## 7. Day 7 — Weekly Dry-Run Review

### 7.1 목표
- 5 trading sessions + 2 review sessions 동안 누적된 비공개 저널을
  메타-리뷰 한다.
- 다음 주 활동을 결정한다 (계속 dry-run vs. 매우 제한된 단계로
  이행 vs. 추가 review 필요).

### 7.2 단계
- [ ] 비공개 저널의 Day 1–6 entry 5–6개를 모두 다시 읽는다.
- [ ] 다음 카운트를 메타-기록한다:
  - validator runs (목표 5/5 PASS)
  - fixture walk-throughs (목표 30/30 PASS)
  - safety / anonymization / gate violations (목표 0)
  - operator deviations (목표 0)
- [ ] Final 주간 status:
  - `PASS` — 모든 카운트가 목표 달성. 운영자는 다음 단계 (예:
    매우 제한된 anonymized candidate 추가) 를 고려할 수 있으나,
    여전히 real-data 진입은 별도 PR 과 별도 승인이 필요하다.
  - `RE-RUN_REQUIRED` — 일부 issue 발견. 한 주를 더 dry-run only
    로 운영한다.
  - `FAIL` — 안전 / 익명화 / 게이트 violation 1건 이상 발생.
    근본 원인 분석 후 별도 corrective action PR 을 작성한다.
- [ ] Day 7 메타-리뷰 entry 를 비공개 저널에 저장.

### 7.3 금지
- 주간 리뷰의 `PASS` 결과를 real-data 진입 자동 권한으로 해석 금지.
- 메타-리뷰 결과를 repository 에 commit 금지.
- 다음 주에 자동 실행 도입 시도 금지.

---

## 8. 일주일 동안의 절대 boundary

이 한 주 전체에 적용되는 boundary:

- **dry-run only** — anonymized fixture 만 다룬다.
- **private journal only** — Day 1–7 entry 는 모두 비공개 저널에만
  존재한다. repository 는 template 의 모양만 commit 한다.
- **no real data** — 실제 종목 / 가격 / 뉴스 / 공시 / 주문 /
  거래량 / 수급 / 계좌 / API key 어떤 것도 등장하지 않는다.
- **no automated execution** — 어떤 agent 도, 어떤 pipeline 도,
  어떤 webhook 도 자동 거래를 하지 않는다.
- **human gate** — 모든 transaction-인접 결정의 마지막 gate 는
  사람이다.
- **PASS ≠ permission** — validator PASS 또는 daily PASS 는
  schema-flow consistency 가 성립한다는 사실 한 가지만 의미한다.
  거래 권한이 아니다.
