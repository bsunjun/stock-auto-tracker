# Phase 3 — Claude Code Runbook (mobile)

모바일 Claude Code 세션에서 WiseReport 기업 리포트 파이프라인을 실행하는 표준 절차.
**모든 단계는 dry-run 우선**이며, 실제 적용 단계는 사용자가 명시적으로 `--apply`(필요 시 `--confirm-promote`)를 입력해야 한다.

## Pre-flight

1. 환경변수 확인 (없으면 default 상대경로 사용):
   - `PHASE3_REPORT_ROOT` (default `./data_inbox/wisereport`)
   - `PHASE3_OUTPUT_ROOT` (default `./output`)
   - 필요 시 `WISE_REPORT_ROOT`, `STOCK_RESEARCH_ROOT` (PR #2의 다른 도구와 호환)
   - Vision OCR 사용 시 `ANTHROPIC_API_KEY`
2. `git status`로 작업 트리 깨끗한지 확인
3. 본 패키지 위치에서 작업: `stock_research/phase3_report_pipeline/`

## Standard Steps

### 1) 기업 PDF 스캔 (read-only)
```
python3 scripts/scan_wisereport_company.py --date 2026-04-30
```
Dry-run 결과 검토 → 문제 없으면:
```
python3 scripts/scan_wisereport_company.py --date 2026-04-30 --apply
# → ./output/2026-04-30/scan_company.json
```

### 2) (선택) Vision OCR
페이지 본문 추출이 필요한 PDF에 대해서만. 비용·페이지 한도 인지 후 실행:
```
python3 scripts/vision_ocr_pdf.py --pdf <path> --pages "1-3" --max-pages 5
# dry-run에서 호출 횟수/모델 확인 → --apply 로 실제 호출
```
- API key는 `ANTHROPIC_API_KEY` env에서만 읽음. CLI 인자로 전달 금지.
- 본 도구는 비용을 발생시키므로 사용자 명시 승인 후에만 실행.

### 3) manual partial meta JSON 준비 (사람/외부 파서)
- `examples/parsed_meta.example.json` 형식을 따른다.
- broker / old_target / new_target / horizon은 **PDF 본문 정보가 필요**하므로 사람 또는 별도 파서가 채운다 (현재 PR #4 범위에서는 OCR/Vision 미수행).
- ticker는 한글명("SK스퀘어") 또는 KRX 코드("KRX:402340") 둘 다 허용 — bridge가 정규화한다.

### 3a) bridge로 parsed_meta.json 생성 (PR #4, OCR/Vision 미사용)
```
python3 scripts/bridge_scan_to_parsed_meta.py \
    --scan-json ./output/2026-04-30/scan_company.json \
    --manual-meta ./manual_meta.json \
    --ticker-map examples/ticker_map.example.csv \
    --out ./output/2026-04-30/parsed_meta.json
# dry-run에서 매칭/missing_fields 분포 확인 → --apply
```
- bridge는 sha256/filename을 채우고 한글 종목명을 KRX 코드로 매핑하며 direction을 자동 계산한다.
- **누락된 필드는 추정하지 않고 `missing_fields`에 기록**한다.

### 4) Estimate revision row 생성
```
python3 scripts/build_report_estimate_v132.py --input parsed_meta.json --date 2026-04-30
# dry-run에서 row 수/방향 분포 확인 → --apply
# → ./output/2026-04-30/estimate_revision_rows.json
```

### 5) CSV 누적 (PR #2 도구로)
본 패키지는 직접 CSV append하지 않는다. `stock_research/scripts/rolling_append.py` 사용:
```
python3 ../scripts/rolling_append.py \
    --csv $STOCK_RESEARCH_ROOT/03_daily_reports/_rolling/estimate_revision_history.csv \
    --rows ./output/2026-04-30/estimate_revision_rows.json \
    --dedupe-keys date,ticker,broker,source_key
# dry-run 후 --apply
```

### 6) Promote (이중 게이트, 사용자 직접만)
```
# 항상 dry-run 먼저
python3 scripts/promote_report_outputs.py --date 2026-04-30

# --apply 만으로는 거부됨 (의도적). 인지 후:
python3 scripts/promote_report_outputs.py --date 2026-04-30 --apply --confirm-promote
```
- **Promote/latest/Super Pack 갱신은 별도 승인 후 수동 실행**한다.
- Super Pack 재생성은 본 스크립트 책임이 아니며, OUT OF SCOPE이다.
- 자동화 도구나 mobile 에이전트는 사용자 입력 없이 promote를 수행하지 말 것.

## Refusal Conditions

다음 상황에서는 절차를 중단하고 사용자에게 알린다:
- 입력 디렉토리/파일 누락 (e.g., `<report-root>/<date>/기업/` 없음)
- `--apply --confirm-promote` 둘 중 하나만 있는 경우 (promote)
- `ANTHROPIC_API_KEY` 미설정 상태에서 `vision_ocr_pdf.py --apply`
- parsed_meta.json 형식 불일치 (list of dict 아님)
- 페이지 한도 초과 요청 (Vision OCR `--max-pages` 가드)

## What this pack does NOT do

- 실제 PDF 파싱 (외부 파서가 담당)
- 실제 매매·주문·체결
- Drive 원본 PDF 이동/복사/삭제
- 자동 promote
- Super Pack 재생성
