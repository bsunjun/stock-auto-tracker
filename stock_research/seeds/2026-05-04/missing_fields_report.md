# Missing Fields Report — 2026-05-04 Monday Seed

본 보고서는 Gemini NewsReportPack을 월요일 매매 시드 후보로 정제하는 과정에서 데이터 미확인/누락으로 인해 보수적으로 강등하거나 `data_insufficient` 처리한 필드를 정리한다.

## 1. estimate_revision_status = data_insufficient

`estimate_revision_link=true`로 태깅된 종목 중 실제 매출/영업이익/순이익/EPS 추정치 변경표(WiseReport PDF 또는 동등한 출처)를 본 파이프라인에서 확인하지 못한 항목.

| ticker | 종목명 | 원본 estimate_revision_link | 처리 후 estimate_revision_status | 사유 |
| --- | --- | --- | --- | --- |
| KRX:098460 | 고영 | true | data_insufficient | WiseReport 본문은 'AI 모멘텀 수혜' 정성 코멘트만 인용. 추정치 변경표 미첨부. |
| KRX:486990 | 노타 | true | data_insufficient | 신규 커버리지 코멘트만 확인. 매출/OP/NI/EPS 추정치 변경표 미첨부. |
| KRX:170900 | 동아에스티 | true | data_insufficient | 1Q 실적 + AACR 파이프라인 본문은 확인되나, 추정치 변경표 행 구조 미확인. |
| KRX:376300 | 디어유 | true | data_insufficient | 밸류에이션 코멘트만 인용. 추정치 변경표 미첨부. |
| KRX:089860 | 롯데렌탈 | true | data_insufficient | 이익 체력 코멘트만 인용. 추정치 변경표 미첨부. |
| UNLISTED:MAKINAROCKS | 마키나락스 | true | data_insufficient | 비상장. 컨센서스/추정치 변경표 정의 자체 부재 (IPO_WATCH로 별도 처리). |
| KRX:084990 | 헬릭스미스 | true | data_insufficient | 텔레그램 단독 출처. 추정치 변경표 미존재. |

`estimate_revision_link=false`로 원본 표기된 종목(동국제강)은 `estimate_revision_status=not_applicable`로 둔다.

## 2. PB 상태 강제 false 처리

Kiwoom 수급 스냅샷과 TradingView 차트 트리거가 본 사이클에 입력되지 않았다. 따라서 모든 후보에 대해:

- `pb_ready = false`
- `pb_scout = false`
- `pb_trigger = false`

월요일 장전 다음 데이터가 들어오면 재평가:
- Kiwoom: 외인/기관 순매수 상위, 프로그램 매수 누적, 거래대금 회전율
- TradingView: 일/주봉 추세선, 거래량 임계치, 모멘텀 지표(RSI/MACD)

## 3. ticker 매핑 미확정 / 가정

| 종목명 | 사용 ticker | 비고 |
| --- | --- | --- |
| 노타 | KRX:486990 | 사용자가 명시 매핑한 값 사용. 종목코드 매핑 테이블 갱신 필요. |
| 동국제강 | KRX:460860 | 2023 인적분할 후 신규 동국제강 코드 사용. (홀딩스/씨엠과 구분.) 매핑 테이블에 명시적 등록 권고. |
| 마키나락스 | UNLISTED:MAKINAROCKS | 비상장 placeholder. IPO 후 KRX 코드 부여 시 갱신. |

## 4. veto_candidate 처리

- **헬릭스미스 (KRX:084990)**: CB 400만주(전환가 750원) / BW / 오버행 관련 공식 공시 확인 전까지 `veto_candidate=true`. DART 또는 거래소 정정공시 입수 후 해제 검토.

## 5. 후속 액션 (월요일 장전 09:00 이전)

1. WiseReport 원문 PDF에서 estimate_revision_link=true 6종목의 추정치 변경표 추출 → `data_insufficient` 항목 갱신.
2. Kiwoom 수급 + TradingView 차트 입력 → `pb_ready / pb_scout / pb_trigger` 재평가.
3. DART 공시 확인 → 헬릭스미스 veto 유지 여부 결정.
4. 텔레그램 단독 테마(메모리/전력/로봇) 주도주 발굴 후 별도 보강 입력.
5. 본 사이클 산출(`corrected_monday_seed_candidates.csv`)을 Drive 측 `MONDAY_SEED_CANDIDATES_latest.csv` 정본 위치로 승격.
