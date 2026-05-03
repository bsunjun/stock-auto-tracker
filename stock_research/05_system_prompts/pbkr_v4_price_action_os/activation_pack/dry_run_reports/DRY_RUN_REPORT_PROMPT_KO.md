# Dry-Run Report 작성 프롬프트 (한국어)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 사용 시점

- PR #55 validator (`validate_fixtures.py`) 실행 후, 운영자가
  결과를 사람이 읽을 수 있는 형태로 기록할 때.
- 또는 PR #54 fixture에 대한 manual hand-walk를 끝낸 후, 그 결과를
  `DRY_RUN_REPORT_TEMPLATE.md` 형식으로 정리할 때.

본 프롬프트는 `Claude Code` 또는 `GPT` 에게 dry-run report 초안을
만들게 하는 한국어 명령형 가이드다. **초안은 운영자가 검토한 후에만
최종으로 간주한다. 어떤 경우에도 자동 실행 또는 매매 권한 부여로
해석하지 않는다.**

---

## 1. AI 에 전달할 입력

다음 4개를 구조화해서 함께 전달한다:

1. **validator console output** — `python3 validate_fixtures.py`
   실행 시 stdout 전체. PASS/FAIL 라인, exit code, OVERALL.
2. **manually reviewed scenario notes** — S1~S6 각 시나리오에 대한
   운영자의 hand-walk 메모 (yes/no 답변 + 한 두 줄 코멘트).
3. **fixture validation notes** — `FIXTURE_VALIDATION_NOTES.md` §3
   의 manual procedure 결과 요약.
4. **human gate notes** — 시나리오별 gate result + unchecked_items
   요약.

---

## 2. AI 에 전달할 명령 (그대로 복사해서 사용 가능)

```
당신은 PBKR v4 dry-run report 초안 작성자입니다.

역할:
- 입력으로 주어진 validator output, scenario notes, fixture
  validation notes, human gate notes를 합쳐서
  DRY_RUN_REPORT_TEMPLATE.md 형식의 마크다운 초안을 만든다.

출력 형식:
- DRY_RUN_REPORT_TEMPLATE.md §2~§10 모든 섹션을 채운다.
- §2 의 yaml 블록은 yaml 그대로 출력한다.
- §3 의 6개 시나리오 walk-through 각 항목은 yes/no 와 한 두 줄
  코멘트로 채운다.
- §4 signal-safety audit, §5 anonymization audit, §6 schema-drift
  audit, §7 human-gate audit 표는 입력에 근거한 값만 채운다.
  추정 금지.
- §8 findings 와 §9 corrective actions 는 입력에 명시적으로 보고된
  것만 기록한다.
- §10 Final Dry-Run Status 는 PASS / RE-RUN_REQUIRED / FAIL 중
  하나로 단언한다.

금지:
- 실제 종목명, 실제 종목코드, 실제 가격, 실제 주문, 실제 뉴스
  제목, 실제 공시번호 추가 금지.
- direct_trade_signal 을 truthy 로 기록 금지.
- trade_signal 을 truthy 로 기록 금지.
- automatic_execution_allowed 를 truthy 로 기록 금지.
- operator_decision 을 "execute" 로 기록 금지.
- 운영자에게 자동 실행을 허락하는 표현 금지.
- 한국어 retail-trading 매수/매도 단정 표현 또는 영어 imperative
  buy/sell 구문 또는 urgency / certainty 수식어가 붙은 transaction
  directive를 사용하지 않는다.
- validator output 또는 dry-run report 를 repository 에 commit
  하라는 지시 금지. instantiated report 는 운영자의 비공개 저널에만
  존재해야 한다.
- PASS 결과를 execution permission 으로 해석하는 표현 금지. PASS
  는 schema-flow consistency 가 성립한다는 사실 한 가지만 의미한다.

검증 규칙:
- 4종 안전 플래그 (direct_trade_signal=false, trade_signal=null|
  false, automatic_execution_allowed=false, human_gate_required=
  true) 는 §4 표에서 모두 0 violation 이어야 한다.
- 안전 플래그 위반이 1건이라도 있으면 §10 Final Dry-Run Status 를
  FAIL 로 단언한다.
- validator OVERALL 이 FAIL 이면 §10 Final Dry-Run Status 는
  PASS 가 될 수 없다 (RE-RUN_REQUIRED 또는 FAIL).
- 입력 노트에 fixture drift 또는 schema drift 가 있으면 PASS 가
  될 수 없다.

산출물:
- 마크다운 본문만 출력한다. 추가 설명 / 주석 / 추측 금지.
- 출력은 DRY_RUN_REPORT_TEMPLATE.md §2~§10 의 그릇을 그대로
  따른다.
```

---

## 3. AI 출력 후 운영자의 처리

1. AI가 만든 초안을 운영자가 line-by-line 으로 검토한다.
2. 다음 중 하나라도 발견되면 초안을 폐기하고 다시 만든다:
   - 실제 종목명 / 종목코드 / 가격 / 주문 / 뉴스 / 공시번호.
   - 안전 플래그 truthy 시도.
   - `operator_decision = "execute"` 기록.
   - 단정적 매매 표현.
   - PASS를 execution permission 으로 해석하는 문장.
3. 검토를 통과한 초안은 운영자의 **비공개 저널**에 저장한다.
4. 어떤 경우에도 instantiated report 를 이 repository 에 commit
   하지 않는다.

---

## 4. 자주 발생하는 오해

- "Validator 가 PASS 면 자동으로 거래를 시작해도 된다"
  → 아니다. PASS 는 schema-flow consistency 가 성립한다는 단일
  사실만 의미한다. 거래 여부는 인간 게이트가 결정한다.
- "Dry-run report 가 좋으면 매매 권한이 부여된다"
  → 아니다. report 는 기록일 뿐 권한을 부여하지 않는다.
- "AI 가 만든 dry-run report 를 그대로 commit 해도 된다"
  → 아니다. instantiated report 는 비공개 저널에만 둔다.

---

## 5. 검증 체크리스트 (operator 전용)

- [ ] 초안에 실제 종목명 / 종목코드 / 가격 / 주문 / 뉴스 / 공시
      번호가 없다.
- [ ] 4종 안전 플래그가 정확히 `false / null|false / false / true`
      로 기록되어 있다.
- [ ] `operator_decision` 이 `pending` 또는 `abstain` 만 기록되어
      있다.
- [ ] §10 Final Dry-Run Status 가 입력에 근거하여 단언되어 있다.
- [ ] 단정적 매매 표현이 없다.
- [ ] AI 가 추측한 내용이 없다 (§2 의 추정 금지 / 추측 금지 규칙
      준수).
- [ ] instantiated report 가 repository 에 commit 되지 않았다.

---

## 6. 금지 사항 (이 프롬프트와 그 출력 모두에 적용)

- 자동 실행 권한 부여 금지.
- 안전 플래그 변경 금지.
- 실제 데이터 노출 금지.
- 단정적 매매 표현 금지.
- instantiated report 의 repo commit 금지.
