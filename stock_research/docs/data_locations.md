# PBKR Data Locations (Multi-Source)

리포트 PDF 원본은 단일 위치에만 존재한다고 가정하지 않는다. Telegram 채널 다운로드, Chrome 저장 폴더, 수동 업로드 모두 가능. 본 문서는 multi-source 스캔 파이프라인이 인식하는 위치를 정리한다.

## Source Roots

| 라벨 | 절대경로 (예시) | 환경변수 |
| --- | --- | --- |
| `wisereport` | `<Drive>/Chrome에서 저장됨/wisereport` | `WISE_REPORT_ROOT` |
| `telegram_attachments` | `<Drive>/내 드라이브/stock_research/01_raw_telegram` | `TELEGRAM_ROOT` |
| `stock_research_06_wise_report` | `<Drive>/내 드라이브/stock_research/06_wise_report` | `STOCK_RESEARCH_ROOT` 하위 |
| `daily_reports` | `<Drive>/내 드라이브/stock_research/03_daily_reports` | `STOCK_RESEARCH_ROOT` 하위 |
| `manual_upload` / `unknown` | `--source-root`로 추가된 임의 경로 | — |

repo는 위 어디에도 PDF를 복사·동기화하지 않는다. 인덱싱(메타데이터 CSV)만 만든다.

## Discovery Patterns

스캐너가 인식하는 하위 패턴 (`storage_source` / `discovery_source`):

```
wisereport
  └ <DATE>/기업/*.pdf                  -> discovery_source = "wisereport/<DATE>/기업"
  └ <DATE>/산업/*.pdf                  -> discovery_source = "wisereport/<DATE>/산업"
  └ <DATE>/*.pdf                       -> discovery_source = "wisereport/<DATE>"
  └ *.pdf                              -> discovery_source = "wisereport/loose"

telegram_attachments
  └ <DATE>/<channel>/attachments/*.pdf -> discovery_source = "telegram/<DATE>/<channel>/attachments"

stock_research_06_wise_report
  └ **/*.pdf                           -> discovery_source = "manual_06_wise_report"

daily_reports
  └ <DATE>/**/*.pdf                    -> discovery_source = "daily_reports/<DATE>"

unknown (--source-root로 들어온 임의 경로)
  └ **/*.pdf                           -> discovery_source = "source_root"
```

## Inventory Outputs

스캔/빌드 산출은 모두 Drive 측 stock_research 안에 들어간다.

```
$STOCK_RESEARCH_ROOT/06_wise_report/inventory/
  ├── scan_<YYYY-MM-DD>.json                 # raw scan (sha256 포함)
  ├── REPORT_INVENTORY_<YYYYMMDD>.csv        # 일자별 정식 인벤토리
  └── REPORT_INVENTORY_latest.csv            # 최신 사본 (심볼릭이 아닌 복사본 — 크로스 플랫폼 호환)
```

## CLI 표준 인자 (multi-source)

scan / build / dedupe / validate 스크립트는 다음 인자를 공통적으로 수용한다.

| 인자 | 설명 |
| --- | --- |
| `--wisereport-root` | env fallback `WISE_REPORT_ROOT` |
| `--telegram-root` | env fallback `TELEGRAM_ROOT` |
| `--stock-research-root` | env fallback `STOCK_RESEARCH_ROOT` |
| `--source-root` | 추가 경로, 반복 가능 (`--source-root A --source-root B`) |
| `--date` | YYYY-MM-DD, 기본 오늘 |
| `--dry-run` / `--apply` | 기본 dry-run, 실제 변경은 `--apply` |

## Dedupe Policy

1. **1차: sha256 동일** — 같은 바이트의 파일은 무조건 동일.
2. **2차: 메타 동일 + 제목 유사** — `ticker`, `broker`, `report_date` 셋 모두 일치하고 제목 SequenceMatcher ratio ≥ 0.85일 때.
3. **canonical 선정 우선순위** (낮을수록 정본):
   `stock_research_06_wise_report < daily_reports < wisereport < telegram_attachments < manual_upload < unknown`
   동순위면 `mtime` 가장 이른 행, 그래도 동률이면 path 사전순.
4. 중복 row는 `duplicate_of`에 정본 row의 `id`를 채우고 `dedupe_method`를 `sha256` 또는 `fuzzy`로 기록한다. **PDF 파일 자체는 절대 이동/삭제하지 않는다.**

## Repo / Drive 경계 재확인

- repo: 코드, 스키마, 프롬프트, 템플릿 CSV(헤더만), `.env.example`, 워크플로 문서, **식별 보조 reference data (PR #21)**.
- Drive: 모든 PDF, 스캔/인벤토리 결과 CSV/JSON, 일일 분석 산출, rolling memory.
- repo에 실제 데이터(PDF/추출 텍스트/output JSON)가 들어갔다면 그것은 사고이며, `git rm` 후 재커밋이 필요하다.

## Reference data (PR #21)

식별 보조 reference data 는 repo 내 `phase3_report_pipeline/resources/` 아래에 둔다:

- `stock_research/phase3_report_pipeline/resources/ticker_map.csv` — 한글
  종목명 ↔ `KRX:NNNNNN` 매핑. 컬럼:
  `company_name_kr,ticker,aliases,market,notes`. 유지 원칙은
  `phase3_report_pipeline/docs/TICKER_MAP_TODO.md` 참조.
  **상장사만**, KRX 코드 확실한 경우만, IPO/비상장 제외.
  ticker_map 은 **매매 신호가 아니다** — Phase 3 전체에서
  `direct_trade_signal=false` 가 유지된다.

레거시 호환: `phase3_report_pipeline/examples/ticker_map.example.csv` 의 2-col
schema (`name_kr,ticker`) 도 PR #21 resolver 가 자동 인식한다 — 기존 operator
host 의 ticker_map 파일을 그대로 `--ticker-map` 으로 넘겨도 동작.
