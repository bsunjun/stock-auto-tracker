# 안전 관찰 런북 (Safe Observation Runbook, KR)

본 문서는 향후 read-only real-data observation 단계가 별도 PR과 명시
승인을 거쳐 시작될 경우 사용될 **운영 절차 초안**을 한국어로 정리한
것이다. PR #60 자체는 실제 관찰을 시작하지 않는다. 실제 데이터를
도입하지 않는다. 실제 종목, 실제 코드, 실제 가격, 실제 뉴스, 실제
공시번호, 실제 수급, 실제 주문, 실제 계좌 정보를 본 문서에서 다루지
않는다.

## 전제

- 모든 단계는 사람이 직접 수행하는 수동 단계이다.
- 어떤 단계도 자동 실행되지 않는다.
- 어떤 단계도 broker, API, Kiwoom, WiseReport, Drive 연결을 가정하지
  않는다.
- 모든 결과는 private journal 에만 기록된다. 이 repo 에는 commit 하지
  않는다.
- 단계 실행 전, `HUMAN_APPROVAL_FOR_OBSERVATION.md` 의 승인 문구가
  서면으로 확인되어야 한다.

## 일자별 리허설 (단, 본 PR 에서는 실제 데이터 미사용)

다음의 Day 0 – Day 5 항목은 본 PR 에서는 **실제 데이터를 사용하지
않는다**. 향후 별도 PR 에서 실제 관찰이 승인되었을 때, 이 절차의
순서를 따른다는 약속만 기록한다.

### Day 0: 승인 문구 확인

- 승인 문구가 정확히 다음 문장으로만 기록되었는지 확인한다.
  > read-only real-data observation only
- 금지 승인 문구(`trade allowed`, `auto execution allowed`,
  `order enabled`, `signal enabled`, `live trading enabled`) 가
  단 한 줄도 등장하지 않았는지 확인한다.
- 승인 기록은 본 repo 가 아닌 private journal 에 둔다.

### Day 1: source tier 수동 분류 리허설

- 가상의 (실제 종목/사명이 아닌) 묘사 한 줄을 두고, Tier 1 – Tier 5
  중 어디에 해당하는지를 사람이 판단하는 연습만 수행한다.
- 분류 결과는 private journal 에만 적는다.
- 본 PR 에는 어떠한 실제 분류 사례도 기록하지 않는다.

### Day 2: field allowlist 수동 매핑 리허설

- `REAL_DATA_FIELD_ALLOWLIST_POLICY.md` 의 field name 만을 사용해
  묘사를 표현할 수 있는지 확인한다.
- 값은 입력하지 않는다. field name 과 묘사의 대응 가능성만 확인한다.
- 결과는 private journal.

### Day 3: prohibited field 차단 리허설

- 묘사가 `REAL_DATA_REDACTION_AND_STORAGE_POLICY.md` 의 금지 항목을
  포함하는지 확인하고, 포함될 가능성이 있다면 그 자리에서 폐기한다.
- 폐기 자체에 대한 코멘트만 private journal 에 남긴다.

### Day 4: human gate 확인

- 자동화 경로가 활성화되어 있지 않은지 사람이 직접 확인한다.
- broker / API / Kiwoom / WiseReport / Drive 자동 연결이 없는지
  사람이 직접 확인한다.
- 확인 결과는 private journal.

### Day 5: no-execution audit

- 본 절차가 candidate scoring, order preparation, 또는 execution
  으로 변질되지 않았음을 사람이 직접 점검한다.
- `NO_EXECUTION_GUARDRAILS.md` 항목을 한 줄씩 다시 확인한다.
- 점검 결과는 private journal.

## 강제 사항

- 본 런북은 본 PR 에서는 실행되지 않는다. 본 PR 의 merge 만으로
  Day 0 – Day 5 가 시작되지 않는다.
- 실제 관찰의 시작은 별도 PR 과 명시 승인 후에만 가능하다.
- 본 런북의 모든 산출물은 private journal 에만 기록된다.
- 본 런북의 산출물은 어떤 형태로도 본 repo 에 commit 되지 않는다.
- 본 런북은 매매 지시 문서가 아니다. 어떠한 종류의 매매 가이드도,
  매매 신호 산출 절차도 아니다.

## 범위 밖

- 실제 실행, 자동 실행, 알림 자동 발송.
- 실제 broker / API 연결.
- 실제 데이터 사례, 실제 종목 묘사, 실제 차트 캡처.
- 실제 관찰 결과의 repo commit.
