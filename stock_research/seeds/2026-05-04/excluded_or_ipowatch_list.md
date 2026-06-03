# Excluded / IPO_WATCH List — 2026-05-04 Monday Seed

생성 기준: Gemini NewsReportPack (2026-04-28 ~ 2026-05-01) + 최근 4일 WiseReport 원문 + 텔레그램 원문.
월요일(2026-05-04) 매매 후보 풀에서 제외하거나 강등한 항목을 정리한다.

## 1. IPO_WATCH (trading_universe=false)

| 종목명 | ticker | 사유 | 후속 조치 |
| --- | --- | --- | --- |
| 마키나락스 | UNLISTED:MAKINAROCKS | 비상장/IPO 진행 기업. WiseReport에 산업용 특화 AI 모멘텀이 보도되었으나 매매 가능 종목이 아님. | IPO 일정/공모가 확정 시 ticker 부여 후 trading_universe=true로 재편입 검토. WiseReport 신규 자료는 IPO_WATCH 풀에서 계속 추적. |

## 2. WATCH_ONLY (trading_universe=true 유지, 월요일 시드에서 강등)

| 종목명 | ticker | 강등 사유 | 비고 |
| --- | --- | --- | --- |
| 헬릭스미스 | KRX:084990 | (a) 텔레그램 단독 후보(Confidence=Low). WiseReport 등 1차 출처 없음. (b) CB 400만주(전환가 750원) / BW / 오버행 공식 공시 확인 전까지 `veto_candidate=true` 적용. | 52주 신고가 + 엔젠시스 당뇨병성신경병증 논문 모멘텀은 기록만 유지. DART/거래소 공시 확인 후 veto 해제 가능 여부 재평가. |

## 3. 텔레그램 단독 테마 (구체 종목 미특정)

| 테마 | 출처 | 처리 |
| --- | --- | --- |
| 메모리 반도체 | Telegram | 주도주 미특정. trading_universe에 추가하지 않음. 월요일 장전 Kiwoom 수급 + WiseReport 산업 자료 확인 후 후보 발굴. |
| 전력설비 | Telegram | 동상. |
| 로봇 | Telegram | 동상. |

## 4. 후속 검증 트리거

- **마키나락스**: IPO 증권신고서 / 공모일정 공시 → IPO_WATCH 항목 갱신.
- **헬릭스미스**: DART에 CB·BW 잔량/오버행 관련 공식 공시 게시 시 → veto 재검토.
- **메모리/전력/로봇 테마**: 월요일 장전 Kiwoom 외인·기관 순매수 상위 + WiseReport 산업 리포트 교차 확인 → 신규 시드 후보 추출.
