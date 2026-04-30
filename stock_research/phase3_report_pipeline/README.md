# Phase 3 — Mobile Claude Code Report Parser Pack

모바일 Claude Code 세션에서 WiseReport 기업 PDF를 빠르게 스캔하고, 외부 파서 산출물을 받아 estimate revision row를 만들고, 승인 게이트를 통해서만 promote하는 운영 패키지.

> 본 디렉토리는 **코드/스키마/문서/설정 예시**만을 담는다. 실제 PDF/CSV/JSON 산출물, 개인 절대경로, API key는 절대 들어가지 않는다.

## 구성

```
phase3_report_pipeline/
├── README.md
├── scripts/
│   ├── scan_wisereport_company.py        # <root>/<date>/기업/*.pdf 인덱싱 (read-only)
│   ├── bridge_scan_to_parsed_meta.py     # scan + manual + ticker_map → parsed_meta.json (PR #4)
│   ├── merge_meta.py                     # bridge + structured_extraction → merged parsed_meta (PR #5)
│   ├── build_report_estimate_v132.py     # parsed_meta.json → estimate_revision_rows.json (v1.3.2; PR #7 --strict)
│   ├── run_estimate_revision_dryrun.py   # merge → build --strict → rolling --strict-estimate dry-run 묶음 (PR #9)
│   ├── promote_report_outputs.py         # output/<date> → output/latest (이중 gate)
│   └── vision_ocr_pdf.py                 # Vision OCR (raw / --extract-mode estimate; default 호출 안 함)
├── examples/
│   ├── parsed_meta.example.json          # manual partial meta 입력 형식 예시
│   ├── parsed_meta.strict_fixture.json   # PR #7 strict gate fixture (8 records)
│   ├── estimate_revision_rows.rolling_fixture.json # PR #8 strict-estimate fixture
│   ├── pipeline_runner_fixture/          # PR #9 dry-run runner fixture (bridge/structured/extra/expected/README)
│   ├── ticker_map.example.csv            # 한글 종목명 → KRX 코드 매핑 예시
│   └── structured_extraction.example.json # vision_ocr --extract-mode estimate 출력 형식 예시 (PR #5)
├── docs/
│   ├── CLAUDE_CODE_RUNBOOK.md            # 단계별 실행 가이드
│   ├── PIPELINE_SCHEMA.md                # 데이터 흐름·스키마 매핑
│   └── MOBILE_CLAUDE_CODE_PROMPT.md      # 모바일 에이전트 시스템 프롬프트
└── config/
    └── phase3_report_pipeline.example.json
```

## Defaults (전 스크립트 공통)

| 키 | 값 |
| --- | --- |
| `DEFAULT_ROOT` (입력) | `./data_inbox/wisereport` |
| `DEFAULT_OUTPUT` (산출) | `./output` |
| `--dry-run` | 항상 default (적용은 `--apply` 명시) |
| 환경변수 fallback | `PHASE3_REPORT_ROOT`, `PHASE3_OUTPUT_ROOT`, `WISE_REPORT_ROOT` (호환), `ANTHROPIC_API_KEY` (Vision) |

## 실행 흐름 (요약)

자세한 순서는 [`docs/CLAUDE_CODE_RUNBOOK.md`](docs/CLAUDE_CODE_RUNBOOK.md) 참조.

1. `scan_wisereport_company.py` → `output/<date>/scan_company.json` (read-only 인덱스)
2. (선택) `vision_ocr_pdf.py` → 페이지별 본문 텍스트 (사용자 명시 승인 후)
3. 사람/외부 파서가 `manual_meta.json` 생성 (형식: `examples/parsed_meta.example.json` 참고)
3a. `bridge_scan_to_parsed_meta.py` → scan + manual + ticker_map → `parsed_meta.json` (PR #4, OCR/Vision 미호출)
3b. (선택, 비용 게이트 후) `vision_ocr_pdf.py --extract-mode estimate --apply` → `structured_extraction.json` (PR #5)
3c. `merge_meta.py` → bridge + structured_extraction → 우선순위(manual > structured > filename_only) 적용된 merged `parsed_meta.json` (PR #5; missing_fields 남으면 `complete=false`)
4. `build_report_estimate_v132.py --strict` → `output/<date>/estimate_revision_rows{,_rejected_rows,_summary}.json` (PR #7)
4b. (선택, rolling/promotion 측면에서 dry-run 전용) `run_estimate_revision_dryrun.py` 로 3c/4 + rolling 검증을 한 번에 (PR #9). runner 의 `--apply` 는 거부된다. 단, `merge_meta`/`build_report_estimate` 는 다음 단계 입력 JSON 생성을 위해 `/tmp` workdir 안에서만 내부적으로 `--apply` 로 호출된다 — repo/Drive/templates/latest/promote/Super Pack/실제 rolling CSV 어디에도 쓰지 않는다.
5. `stock_research/scripts/rolling_append.py --strict-estimate`(PR #8) 로 CSV 누적 (dedupe-keys: `date,ticker,broker,source_key`). `templates/*.csv` 는 dry-run 전용; `--apply` 가 templates 경로를 가리키면 거부됨.
6. `promote_report_outputs.py --apply --confirm-promote` (이중 gate, 사용자 직접만)

## Safety Gates

- **모든 스크립트는 dry-run이 기본**이다. `--apply`는 명시적 입력이 필요하다.
- **promote는 이중 gate**: `--apply` 단독은 거부된다. `--apply --confirm-promote` 둘 다 필요.
- **Vision OCR는 비용**이 발생한다. 기본 페이지 한도 5, API key는 env에서만 읽음.
- **promote / `output/latest/` 갱신 / Super Pack 재생성은 별도 승인 후 수동 실행**한다. 자동화·에이전트는 사용자 입력 없이 수행하지 말 것.
- 원본 PDF는 절대 이동/복사/삭제하지 않는다.

## What this pack does NOT do

- 실제 PDF 본문 파싱 로직 구현 (외부 파서가 담당; 본 패키지는 row projection만)
- Drive ↔ repo 동기화
- 자동 promote, 자동 latest 갱신
- Super Pack 재생성
- 매매·주문·체결

## See also

- `stock_research/docs/data_locations.md` — 외부 데이터 위치 정책 (PR #2)
- `stock_research/scripts/scan_report_sources.py` — multi-source 풀스캐너 (PR #2)
- `stock_research/scripts/rolling_append.py` — idempotent CSV append (PR #2)
- `stock_research/templates/estimate_revision_history.csv` — 헤더 호환 대상
- repo 루트 `.env.example` — 환경변수 네이밍 컨벤션
