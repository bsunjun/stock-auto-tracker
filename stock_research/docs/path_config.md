# Path Config & Data Flow

이 repo는 **코드/스키마/프롬프트/템플릿/설정 예시**만 담는다. 실제 데이터(PDF, CSV, 메모리 JSON 등)는 모두 Google Drive 측에 위치하며, 경로는 로컬 `.env`로 주입한다.

## Local environment variables

`.env.example`을 복제하여 `.env`로 만들고 자기 환경에 맞게 수정한다. `.env`는 `.gitignore`에 의해 커밋되지 않는다.

| 변수 | 의미 |
| --- | --- |
| `PBKR_ROOT` | repo 루트 (보통 `./`) |
| `STOCK_RESEARCH_ROOT` | Drive 측 `stock_research/` 절대경로 |
| `WISE_REPORT_ROOT` | Drive 측 `Chrome에서 저장됨/wisereport/` 절대경로 |
| `TELEGRAM_ROOT` | Drive 측 `stock_research/01_raw_telegram/` 절대경로 |
| `TZ` | `Asia/Seoul` |
| `ENV` | `local` / `colab` / `actions` 등 |

## Data flow

```
1) WiseReport PDF 원본 (Drive)
   $WISE_REPORT_ROOT/<YYYY-MM-DD>/{기업|산업}/*.pdf

2) 파싱/인덱스/latest CSV (Drive — repo에 복사 금지)
   $STOCK_RESEARCH_ROOT/06_wise_report/
     ├── parsed/<YYYY-MM-DD>/{기업|산업}/*.parsed.json
     ├── index/<YYYY-MM-DD>.json
     └── latest.csv

3) 일일 분석 산출 (Drive)
   $STOCK_RESEARCH_ROOT/03_daily_reports/<YYYY-MM-DD>/
     ├── candidate_score_pack.json
     ├── audit_pack.json
     ├── news_pack.json
     └── trade_ticket.json

4) 누적 history (Drive)
   $STOCK_RESEARCH_ROOT/03_daily_reports/_rolling/*.csv
   (헤더 형식은 repo 의 stock_research/templates/*.csv 와 동일)
```

## Repo vs Drive 경계

| 항목 | repo | Drive |
| --- | --- | --- |
| 자동화 코드 (Python) | O | X |
| 스키마 / 프롬프트 / 워크플로 | O | X |
| 템플릿 CSV (헤더만) | O | X |
| 실제 PDF 원본 | X | O |
| 파싱 결과 / 인덱스 / latest CSV | X | O |
| 누적 history CSV (실데이터) | X | O |
| 일일 분석 JSON 산출 | X | O |
| `rolling_memory.json` | X | O |
| 계좌/평단/주문 데이터 | X (절대 금지) | (사용자 책임) |
| API key / 토큰 | X (`.env`만, 미커밋) | X |

## CLI 표준 인자

`scripts/`의 마이그레이션·append·검증 도구는 다음 인자를 공통적으로 수용한다 (스크립트별 일부 차이):

- `--wisereport-root` (env fallback `WISE_REPORT_ROOT`)
- `--stock-research-root` (env fallback `STOCK_RESEARCH_ROOT`)
- `--date` (YYYY-MM-DD, 기본 오늘)
- `--category` (`기업` / `산업` / `all`, 기본 `all`)
- `--dry-run` (기본 활성). 실제 변경은 `--apply`로 명시.

## 주의

- Drive 마운트 경로는 환경마다 다르다 (`/Volumes/GoogleDrive/...`, `/content/drive/...`, `~/Library/CloudStorage/...`). 절대 하드코딩하지 말고 `.env`로만 주입.
- `serpapi_automator.py`의 `current_prices.json/csv`는 repo 루트에 남아 있는 기존 산출이며 PBKR 파이프라인의 가격 스냅샷 단계로 사용한다 (이번 작업에서 동작 변경 없음).
