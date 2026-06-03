# 공식 리스크 플래그 분류 (Official Risk Flag Taxonomy, KR)

본 문서는 한국거래소(KRX) / KIND / DART 등 공식 시장 채널에서
지정되는 리스크 플래그를 PBKR v4 관점에서 **네 가지 분류**로 나눠
정리한 운영 doctrine 이다. 어떤 분류도 그 자체로 매매 신호가 아니다.
어떤 분류도 자동 실행을 정당화하지 않는다.

본 문서는 실제 종목명, 실제 종목코드, 실제 가격, 실제 공시번호,
실제 주문/계좌 정보를 포함하지 않는다.

각 분류는 운영상 다루는 status label 로 매핑된다. status label 자체
는 매매 신호가 아니며, 자동 실행 / 자동 알림 / 본진 진입 권한을
부여하지 않는다.

## 분류 A — Fundamental / Corporate Hard Exclude

**Status label: `HARD_EXCLUDE`**

기업의 펀더멘털 / 거버넌스 / 회계 / 재무 자체에 의문이 제기되는
공식 상태이다. **무조건 hard exclude** 다.

대표 카테고리:

- 관리종목.
- 상장폐지 실질심사 (상장적격성 실질심사 포함).
- 거래정지 (회계 이슈, 횡령/배임 혐의, 기간 중 정정 등으로 인한
  정지).
- 불성실공시 (불성실공시법인 지정, 공시번복, 공시변경 누적 등).
- 감사의견 문제 (한정, 부적정, 의견거절 등).
- 횡령/배임 (혐의, 발생, 처분 등 공식화 단계 모두 포함).
- 회생 / 파산 (회생절차 개시, 파산신청, 파산선고 등).

운영 원칙:

- `HARD_EXCLUDE` 로 라벨링한다.
- `RISK_FLAG_PULLBACK_WATCH` 대상이 **아니다**.
- `EXTREME_RISK_FLAG_WATCH` 대상이 **아니다**.
- 주도주 후보, 풀백 후보, 관찰 후보 어디에도 포함되지 않는다.
- 일정 기간 내 해소되더라도, 본 doctrine 단독으로 자동 복귀시키지
  않는다.

## 분류 B — Market-Structure Cooling Risk

**Status label: `REGULAR_PB_EXCLUDE` (with possible
`RISK_FLAG_PULLBACK_WATCH` posture)**

거래소가 **가격 / 거래대금 / 회전율 / 공매도 잔고 등의 과열을
식히려고** 부착하는 경고 유형이다. 기업 펀더멘털에 대한 직접 부정
의견이 아닐 수 있다.

대표 카테고리:

- 투자주의.
- 투자경고 지정예고.
- 투자경고.
- 단기과열 예고 / 단기과열종목 지정.
- 공매도 과열종목.

운영 원칙:

- 매매 신호가 **아니다**.
- 본 분류 동안 정상 풀백 경로(`PB_TRIGGER`, 본진 진입)에서 제외한다.
  즉 `REGULAR_PB_EXCLUDE` 로 라벨링한다.
- 단, 다음 조건이 모두 충족될 때에 한해 별도의 고위험 관찰 상태인
  `RISK_FLAG_PULLBACK_WATCH` 로만 분류할 수 있다 (조건은
  `RISK_FLAG_PULLBACK_WATCH_CHECKLIST.md` 참조).
  - 분류 A 가 아님.
  - 분류 C 가 아님.
  - 분류 D 가 아님.
  - 주도 업종 / 주도 테마.
  - 실적 / 추정치 상향 또는 구조적 촉매 존재.
  - 첫 눌림.
  - 눌림 거래량 감소.
  - 수급 재점화 신호.
  - 짧고 논리적인 손절 위치.
- `RISK_FLAG_PULLBACK_WATCH` 는 본진 진입 / 매수 사유 / 자동 실행
  / 자동 알림 어디에도 연결되지 않는다.

## 분류 C — Extreme Market-Structure Cooling Risk

**Status label: `EXTREME_RISK_FLAG_WATCH`**

분류 B 를 넘어 정지 조건에 한층 더 근접한 단계의 경고다. 신규 진입
은 보류되며, 그 자체로는 매수 사유가 아니다.

대표 카테고리:

- 투자위험 지정예고.
- 투자위험종목.
- 투자경고 이후 추가 급등으로 매매거래정지 조건에 접근한 상태.

운영 원칙:

- `EXTREME_RISK_FLAG_WATCH` 로 라벨링한다.
- **신규 진입 보류** (no new entry while the flag is active).
- `PB_TRIGGER` / 본진 진입 / 매수 사유로 사용하지 **않는다**.
- 자동 실행, 자동 알림, 자동 주문 경로에 연결하지 **않는다**.
- 본 분류 동안 `RISK_FLAG_PULLBACK_WATCH` 대상이 **아니다**.
- 본 분류가 공식적으로 해제(분류 B 또는 그 이하로 격하)된 경우에
  한해, 분류 B 의 운영 원칙을 적용해 `RISK_FLAG_PULLBACK_WATCH`
  로 재분류할 수 있다. 해제 자체가 자동 진입 권한이 되는 것은
  **아니다**.

## 분류 D — Active Trading Halt / Corporate Suspension

**Status label: `NO_ENTRY`**

거래 자체가 정지되었거나, 정지의 원인이 기업 행위에 있는 단계다.

대표 카테고리:

- 매매거래정지.
- 상장폐지 실질심사 관련 정지.
- 공시불이행 등으로 인한 거래정지.

운영 원칙:

- `NO_ENTRY` 로 라벨링한다.
- 신규 진입 / 추가 진입 / 평가 / 후보 등재 어느 것도 하지 **않는다**.
- `RISK_FLAG_PULLBACK_WATCH` 대상이 **아니다**.
- `EXTREME_RISK_FLAG_WATCH` 대상이 **아니다**.
- 정지 해제 사실 자체가 진입 권한이 되는 것은 **아니다**. 정지 해제
  이후의 분류는 다시 위 A / B / C 기준에 따라 재평가한다.

## 분류별 status label 요약

- 분류 A → `HARD_EXCLUDE`
- 분류 B → `REGULAR_PB_EXCLUDE` (필요 시 `RISK_FLAG_PULLBACK_WATCH`
  posture 가능)
- 분류 C → `EXTREME_RISK_FLAG_WATCH` (신규 진입 보류; 해제 후 분류
  B 의 `RISK_FLAG_PULLBACK_WATCH` 로 재분류 가능)
- 분류 D → `NO_ENTRY`

## 공통 원칙

- 본 분류 자체가 매매 신호가 **아니다**.
- 본 분류는 후보 평가의 사전 필터로 사용된다 — 분류 A 는 완전
  배제, 분류 D 는 정지 상태 동안 완전 배제, 분류 C 는 신규 진입
  보류, 분류 B 는 별도 고위험 관찰 상태 후보일 수 있다.
- 어떤 분류 / 어떤 status label 도 자동 실행, 자동 알림, 본진 진입
  을 정당화하지 않는다.
- 분류 작업 자체는 **read-only** 이고, 결과 기록은 private journal
  에만 둔다. 본 repo 에는 실제 종목 / 가격 / 공시번호 데이터를
  commit 하지 않는다.

## 범위 밖

- 자동 분류 코드.
- 자동 알림 / 자동 주문.
- 실제 종목 raw value, 실제 공시번호, 실제 가격 예시.
- broker / API / Kiwoom / WiseReport / Drive 자동 연결.
