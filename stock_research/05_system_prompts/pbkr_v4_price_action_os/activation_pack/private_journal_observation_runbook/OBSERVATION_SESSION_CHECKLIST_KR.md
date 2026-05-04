# 관찰 세션 체크리스트 (Observation Session Checklist, KR)

본 문서는 향후 read-only real-data observation 세션을 사람이 직접
운용할 때 사용할 한국어 체크리스트이다. PR #63 자체는 세션을
시작하지 **않는다**. 본 PR 의 merge 만으로 자동 실행, 주문 발주,
후보 산출, candidate scoring, broker 연결이 시작되지 않는다.

## 전제

- 모든 단계는 사람이 수동으로 수행한다.
- 자동 실행 경로는 어디에도 추가되지 않는다.
- 모든 기록은 private journal 에만 남긴다.
- 본 repo 에는 어떠한 실제 observation output 도 commit 하지
  않는다.

## 세션 시작 전

- [ ] approval 문구가 정확히 다음 한 줄로만 기록되었는지 확인.
  > read-only real-data observation only
- [ ] 금지 승인 문구(`trade allowed`, `auto execution allowed`,
      `order enabled`, `signal enabled`, `live trading enabled`,
      `candidate scoring enabled`, `broker connection enabled`,
      `Kiwoom enabled`, `real trading enabled`) 가 어느 줄에도
      등장하지 않는지 확인.
- [ ] private journal 위치가 사람에게 명확한지 확인.
- [ ] 본 repo 에 어떤 observation output 도 commit 하지 않을
      것이라는 점을 사람이 직접 인지.
- [ ] broker / API / Kiwoom / WiseReport / Drive 자동 연결이
      없음을 확인.
- [ ] 자동 실행 경로(스케줄러, cron, webhook, agent loop) 가
      없음을 확인.

## 세션 중

- [ ] raw value 를 기록하지 않는다.
- [ ] 모든 기록은 label / category 수준에서만 작성한다.
- [ ] candidate scoring 을 수행하지 않는다.
- [ ] trade ticket / order draft 를 생성하지 않는다.
- [ ] order preparation 을 수행하지 않는다.
- [ ] 자동 알림 (email / SMS / push / messaging) 을 트리거하지
      않는다.
- [ ] 외부 시스템에 write 하지 않는다 (Drive, Telegram, mail 등).

## 세션 종료

- [ ] private journal 에만 저장이 끝났는지 확인한다.
- [ ] 본 repo 의 working tree 에 새로 들어온 observation artifact
      가 없는지 확인한다.
- [ ] output artifact (raw 또는 derived) 가 본 repo 에 없는지
      확인한다.
- [ ] 본 세션이 execution 권한을 만들지 않았다는 점을 명시적으로
      재확인한다.
- [ ] 본 세션이 candidate scoring 또는 order preparation 을 만들지
      않았다는 점을 재확인한다.

## 미충족 시

- 위 항목 중 하나라도 미충족이면 세션을 즉시 중단한다.
- `PRIVATE_JOURNAL_ABORT_AND_DISCARD_RULES.md` 의 규칙을 따른다.
- 미충족 사실은 private journal 에 짧은 한 줄로만 기록한다.
- 미충족 기록은 본 repo 에 commit 하지 않는다.

## 범위 밖

- 자동 실행, 자동 알림, 주문 준비, candidate scoring.
- broker / API / Kiwoom / WiseReport / Drive 연결 추가.
- 실제 raw value 를 본 repo 또는 private journal 에 기록.
- 실제 observation output 을 본 repo 에 commit.
