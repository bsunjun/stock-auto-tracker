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

### 3a) bridge로 parsed_meta.json 생성 (PR #4 + PR #21, OCR/Vision 미사용)
```
python3 scripts/bridge_scan_to_parsed_meta.py \
    --scan-json ./output/2026-04-30/scan_company.json \
    --manual-meta ./manual_meta.json \
    --ticker-map resources/ticker_map.csv \
    --out ./output/2026-04-30/parsed_meta.json
# dry-run에서 매칭/missing_fields 분포 확인 → --apply
```

PR #21 ticker resolver 강화:
- rich schema (`company_name_kr,ticker,aliases,market,notes`) 또는 legacy
  schema (`name_kr,ticker`) 자동 인식.
- 한글 정규화: `(주)`, `㈜`, `주식회사`, 끝 괄호 숫자 (`대덕전자(353200)`),
  내부 공백 정규화.
- 별칭 매칭: 영문명 (`Samsung Electronics`), 사명변경 이전 형 (`두산중공업`,
  `현대중공업`, `대우조선해양` 등) 도 동일 ticker 로 해석.
- 파일명 fallback: value 가 비었거나 매핑 미스이면 manual record 의
  `filename` 에서 첫 `[...]` 브래킷을 꺼내 normalization → 재시도.
- 매핑 실패 시 ticker 는 그대로 두고 `missing_fields`에 `ticker_unmapped`
  를 추가 — `build --strict` 가 reject 한다.

ticker_map 검증:
```
python3 scripts/ticker_resolver.py --verify \
    --ticker-map resources/ticker_map.csv
python3 examples/run_ticker_resolver_fixture.py
# PR #22 hotfix + PR #32: bridge gate가 빈 ticker도 ticker_hint와
# filename bracket fallback을 타게 통과시키는지 end-to-end 확인.
# PR #32 가 추가한 ticker_hint 우선순위:
#   1. row.ticker 가 KRX 면 그대로 사용
#   2. row.ticker 가 비어 있거나 비-KRX면 row.ticker_hint 로 ticker_resolver 호출
#      (ticker_hint 자체에 filename 도 함께 전달되어 bracket fallback 동시 시도)
#   3. ticker_hint 매칭 실패 시 기존 row.ticker (legacy 경로) + filename bracket
#   4. 그래도 미해결이면 ticker_unmapped 로 기록 (KRX 임의 생성 절대 금지)
python3 examples/bridge_filename_fallback_fixture/run_bridge_filename_fallback_fixture.py
```
- bridge는 sha256/filename을 채우고 한글 종목명을 KRX 코드로 매핑하며 direction을 자동 계산한다.
- **누락된 필드는 추정하지 않고 `missing_fields`에 기록**한다.

### 3b) (선택) Vision 구조화 추출 (PR #5, 비용 게이트 별도)
```
# 항상 dry-run 먼저 — 호출 횟수와 모델 확인
python3 scripts/vision_ocr_pdf.py --pdf <path-to-pdf> --extract-mode estimate
# 명시 승인 후 --apply (env ANTHROPIC_API_KEY 필요)
python3 scripts/vision_ocr_pdf.py --pdf <path> --extract-mode estimate \
    --apply --output ./output/2026-04-30/structured_extraction.json
```
- estimate 모드는 임시 1-page PDF를 만들어 **ONLY page-1만 API에 전송**한다. 전체 PDF는 전송되지 않으며, 임시 파일은 finally 블록에서 자동 cleanup된다.
- 결과 record에는 `payload_bytes_sent` (page-1 사이즈) 와 `original_pdf_bytes` (원본 사이즈) 가 함께 기록되어 사후 감사 가능.
- 결과 형식은 `examples/structured_extraction.example.json` 와 동일.
- **추가 의존성**: `pip install pypdf` 필요 (estimate `--apply` 사용 시). 미설치 환경에서도 `--help` / `--dry-run` 은 정상 동작.
- LLM이 ```` ```json ... ``` ```` markdown fence로 응답해도 자동 제거 후 파싱.

### 3c) merge_meta로 parsed_meta.json 보강 (PR #5, OCR/Vision 미호출)
```
python3 scripts/merge_meta.py \
    --bridge-meta ./output/2026-04-30/parsed_meta.json \
    --structured ./output/2026-04-30/structured_extraction.json \
    --out ./output/2026-04-30/parsed_meta.merged.json
# dry-run에서 priority/conflict 검토 → --apply
```
- sha256 기준 left-join. 우선순위: **manual > structured_extraction > filename_only**.
- 충돌 시 manual 보존, 다른 후보는 `merge_conflicts` 에 기록.
- target 정규화: `"80,000"` / `"95000"` / `80000` 모두 numeric으로. `null` / `""` / `"N/A"` / `"-"` 는 absent로 처리. 인식 불가 문자열은 `parse_failures` 에 기록되고 `missing_fields` 에 `target_parse_failed` 추가.
- `complete=true` 는 **이중 가드**: missing_fields가 비어있고 AND direction ∈ {up, down, flat} 일 때만. 즉 old/new target이 실제 numeric일 때만.
- 동일 `source_pdf_sha256` 가 `--structured` 입력에서 두 번 등장하면 merge_meta는 **fail-fast (exit 2)**, 조용한 덮어쓰기 없음.
- **`complete=false` 레코드는 history CSV append 대상에서 제외**한다 (수동 검토 또는 `--strict` 게이트는 별도 PR).

### 4) Estimate revision row 생성
```
python3 scripts/build_report_estimate_v132.py --input parsed_meta.json --date 2026-04-30
# dry-run에서 row 수/방향 분포 확인 → --apply
# → ./output/2026-04-30/estimate_revision_rows.json
```

#### 4a) `--strict` 게이트 (PR #7)

PR #6 의 `parsed_meta.merged.json` 산출물 중 history CSV 로 흘려도 안전한
row 만 남긴다. 제외된 row 는 drop 하지 않고 별도 파일에 reject 사유와 함께 보존한다.

dry-run (파일 쓰지 않음):
```
python3 scripts/build_report_estimate_v132.py \
    --input ./output/2026-04-30/parsed_meta.merged.json \
    --date 2026-04-30 \
    --strict
```

apply:
```
python3 scripts/build_report_estimate_v132.py \
    --input ./output/2026-04-30/parsed_meta.merged.json \
    --date 2026-04-30 \
    --strict \
    --apply
# → ./output/2026-04-30/estimate_revision_rows.json
# → ./output/2026-04-30/estimate_revision_rejected_rows.json
# → ./output/2026-04-30/estimate_revision_summary.json
```

Reject 게이트 (하나라도 해당하면 reject):
- `complete` 가 true 가 아님
- `missing_fields` 가 비어있지 않음 — `[]` 또는 absent 만 통과. **non-empty list / string / dict 등 다른 truthy 형태도 reject** (defensive against producers that emit `"target_parse_failed"` as a bare string).
- `direction == "unknown"`
- `old_target` / `new_target` 이 null / empty / non-numeric — **NaN / +inf / -inf 도 reject** (`math.isfinite` 통과 필수). 이는 downstream direction 비교를 오염시키지 않기 위함.
- `ticker` 가 `KRX:` 형식 아님
- `broker` 가 비어있음
- `report_date` (또는 `date`) 가 비어있음
- `horizon` 이 비어있음

Accepted row 에는 `direct_trade_signal=false` 가 명시된다 — Phase3 산출물은
추정치/실적 모멘텀 입력일 뿐, 매매 신호가 아니다. Summary 의
`direct_trade_signal_all_false` 는 항상 true 여야 한다.

`--strict` 미지정 시 기존 동작이 그대로 유지된다 (단일
`estimate_revision_rows.json` 만 작성, reject 게이트 미적용).

### 4b) (선택) Dry-run 파이프라인 한 번에 (PR #9)

`merge_meta` → `build_report_estimate --strict` → `rolling_append --strict-estimate` 의
3단계를 단일 명령으로 묶는 dry-run 전용 connector. 실전 promote/append 도구가 아니다.

```
python3 stock_research/phase3_report_pipeline/scripts/run_estimate_revision_dryrun.py \
    --date 2026-04-30 \
    --bridge-meta ./output/2026-04-30/parsed_meta.json \
    --structured  ./output/2026-04-30/structured_extraction.json \
    --workdir /tmp/phase3_pr9 \
    --print-commands
```

원칙 (PR #9):
- **runner 자체는 rolling/promotion 측면에서 항상 dry-run**. `--apply` 플래그는
  의도적으로 거부된다 (exit 2). 실제 누적은 PR #8 의
  `rolling_append.py --strict-estimate --apply` 를 사용자가 별도로 승인 후 실행.
- 모든 임시 산출물은 `--workdir` 아래 (저장소 바깥) 에서만 만들어지고 종료 시 삭제된다.
  `--keep-workdir` 로 보존 가능.
- repo 의 `templates/*.csv` 는 절대 수정되지 않는다 (헤더만 읽고 workdir 에 시드 복사).
- `direct_trade_signal_all_false=true` 가 false 면 runner 가 즉시 abort (exit 4).
- **`--strict` 가 운영 기본값**. `--no-strict` 는 legacy compatibility 검증
  전용이며 일상 운영에서는 사용하지 말 것. non-strict 경로에서는
  `estimate_revision_summary.json` 이 생성되지 않으므로 runner 가
  `estimate_revision_rows.json` 만으로 카운트를 도출하고
  `direct_trade_signal_all_false` 도 row 들에서 직접 계산한다.
  `pipeline_summary.json` 의 `strict_enabled` 필드로 어떤 경로로 돌렸는지 식별 가능.

#### "금지되는 apply" vs "허용되는 내부 apply"

| 분류 | 항목 | runner 동작 |
| --- | --- | --- |
| 🚫 금지 | `rolling_append.py --apply` | 호출하지 않음 (rolling step 은 항상 `--dry-run`) |
| 🚫 금지 | `promote_report_outputs.py --apply` | 호출하지 않음 |
| 🚫 금지 | `latest` 갱신 | 수행하지 않음 |
| 🚫 금지 | Super Pack 재생성 | 수행하지 않음 |
| 🚫 금지 | Drive / repo / templates 수정 | 수행하지 않음 |
| 🚫 금지 | OCR / Vision / API 호출 | 수행하지 않음 |
| ✅ 허용 (내부) | `merge_meta.py --apply --out <workdir>/parsed_meta.merged.json` | 다음 단계 입력 JSON 생성 목적의 임시 산출물; **`/tmp` workdir 만**. |
| ✅ 허용 (내부) | `build_report_estimate_v132.py --strict --apply --output-root <workdir>` | 다음 단계 입력 JSON 생성 목적의 임시 산출물; **`/tmp` workdir 만**. |

이 두 내부 `--apply` 는 repo / Drive / latest / promote / Super Pack / 실제
rolling CSV 어디에도 영향을 주지 않으며, `--keep-workdir` 미지정 시 종료와 함께
삭제된다.

산출 (workdir 안):
```
parsed_meta.merged.json
2026-04-30/estimate_revision_rows.json
2026-04-30/estimate_revision_rejected_rows.json
2026-04-30/estimate_revision_summary.json
seeded_estimate_history.csv     # templates 헤더 + 1개 dup 시드 (apply 대상 아님)
rolling_input.json
pipeline_summary.json           # runner 요약 (status / counts / commands_run / forbidden_actions_confirmed)
```

### 5) CSV 누적 (PR #2 도구로, PR #8 strict-estimate 포함)
본 패키지는 직접 CSV append하지 않는다. `stock_research/scripts/rolling_append.py` 사용.

**dry-run** — `stock_research/templates/...` 경로는 헤더/스키마 검증용으로만 쓰며 dry-run 전용:
```
python3 ../scripts/rolling_append.py \
    --csv stock_research/templates/estimate_revision_history.csv \
    --rows ./output/2026-04-30/estimate_revision_rows.json \
    --dedupe-keys date,ticker,broker,source_key \
    --strict-estimate
```

**apply** — 실제 누적은 Drive 의 `_rolling/` 경로에서:
```
python3 ../scripts/rolling_append.py \
    --csv "$STOCK_RESEARCH_ROOT/03_daily_reports/_rolling/estimate_revision_history.csv" \
    --rows ./output/2026-04-30/estimate_revision_rows.json \
    --dedupe-keys date,ticker,broker,source_key \
    --strict-estimate \
    --apply
```

`--apply` 가 `stock_research/templates/...` 를 가리키면 PR #8 hardening 가드가 거부한다 (exit 2):
```
error: refusing to --apply into stock_research/templates; use a real rolling csv path outside templates
```

`--strict-estimate` (PR #8) 는 PR #7 의 strict 산출물 (`direct_trade_signal=false`,
KRX ticker, valid direction, source_key 등) 만 통과시키고, 잘못 들어온
`estimate_revision_rejected_rows.json` 형태도 마지막 보안망에서 차단한다.
자세한 내용은 `stock_research/workflows/rolling_append_workflow.md` 참조.

> ⚠️ `estimate_revision_rejected_rows.json` 은 history CSV append 대상이 아니다.

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

## Real-data sample dry-run (PR #11)

> **PR #11 is not a PDF body parser.** It is the safe sampling and
> operator-run procedure for the later real-data test.

실제 WiseReport PDF 샘플로 파이프라인을 점검하는 절차는 별도 문서에 있다 —
[`REALDATA_SAMPLE_RUN.md`](REALDATA_SAMPLE_RUN.md). PR #11 의 entry point 는
`scripts/wisereport_sample_select.py` 이며, hard-cap 10 PDFs / Drive 읽기 전용 /
저장소 바깥 workdir 만 허용한다. 이 절차는 모바일 / Claude 샌드박스가 아니라
Drive 가 마운트된 운영자 호스트에서 직접 실행한다. 실데이터 결과는 repo 에
커밋하지 않고 PR comment 또는 외부 채팅에 요약만 paste 한다.

## Real-PDF pdfplumber smoke (PR #14, 1–3 PDFs)

> **PR #14 는 코드 PR 이 아니라 runbook + 결과 스키마 PR 이다.** 실제 PDF
> 1–3 개에 대해 PR #13 의 `--pdf` deterministic 경로를 operator host 에서
> 실행하기 위한 절차와, 결과를 안전하게 paste 하기 위한 템플릿만 추가한다.

- 절차 ("PR #14 — Real-PDF pdfplumber smoke (1–3 PDFs)" 섹션):
  [`REALDATA_SAMPLE_RUN.md`](REALDATA_SAMPLE_RUN.md)
- 결과 스키마 (paste-back 전용; 절대 commit 금지):
  [`REAL_PDF_SMOKE_RESULT_TEMPLATE.md`](REAL_PDF_SMOKE_RESULT_TEMPLATE.md)

PR #14 hard caps:
- `pdf_count <= 3`
- `direct_trade_signal=true row 0건`
- OCR/Vision/API 호출 0건 (`pdfplumber` deterministic only)
- Drive 원본 변경 0건, `latest`/promote/Super Pack 0건, `rolling --apply` 0건
- 실 PDF / 추출 텍스트 / 출력 JSON 어느 것도 repo 커밋 금지 — schema-aligned
  카운터만 PR comment 또는 외부 채팅에 paste.

## Cloud-Drive PDF fetch probe (PR #15, ≤ 1 PDF)

> **PR #15 는 parser 개선 PR 이 아니라 capability-discovery PR 이다.**
> Claude Code cloud 세션이 Google Drive 의 PDF 본문 fetch 를 안전하게
> 수행할 수 있는지 확인하는 절차와 paste-back 스키마만 추가한다.

- 절차 ("Phase 0 — capability discovery" 부터 "Phase 5 — cleanup" 까지):
  [`CLOUD_DRIVE_PDF_FETCH_PROBE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE.md)
- 결과 스키마 (paste-back 전용; 절대 commit 금지):
  [`CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE_RESULT_TEMPLATE.md)

PR #15 hard caps:
- `pdf_count == 0` (Phase 0/1 stop) **또는** `pdf_count == 1` (Phase 2+).
  PR #14 의 3 보다 더 작다 — 본 PR 은 capability discovery 우선이다.
- Drive 원본 수정 / 이동 / 삭제 / rename 0건 (read-only API surfaces 만 사용).
- OCR / Vision / API 호출 0건. PDF 본문은 deterministic `--pdf` (pdfplumber) 만 사용.
- `direct_trade_signal=true` row 0건. Phase3 invariant.
- `latest` / promote / Super Pack / `rolling --apply` 0건.
- 실 PDF / 추출 텍스트 / 출력 JSON / 전체 sha256 어느 것도 repo 커밋 또는
  paste-back 금지. schema-aligned 카운터 + sha **prefix(12 chars)** 만 paste.
- Drive 가 마운트된 operator host 에서의 실제 sample run 은 PR #14 가 담당한다 —
  PR #15 와 PR #14 는 독립적이며 동시에 사용해도 무방하다.

## Deterministic estimate table parser (PR #12 + PR #17 + PR #18 + PR #19 + PR #20 + PR #26 + PR #27 + PR #28 + PR #29 + PR #30)

> **PR #12 는 deterministic-first PDF estimate table parser 의 시작점이다.**
> synthetic text fixture 기반 검증만 수행했고, 실제 WiseReport PDF 본문 파싱은
> operator host 에서 별도 제한 실행한다. OCR/Vision fallback 은 아직 실행하지 않으며,
> 본 PR 은 trade-signal 생성 도구가 아니다.
>
> **PR #17 은 OCR fallback 이 아니라 real WiseReport "표3. 실적 전망 / 수정 후 /
> 수정 전 / 변동률" 표 layout parser 보강이다.** 4-column horizon 헤더에서
> forward-year `YYYYE` 우선 선택, compact + split-line 두 형태 모두 처리.
>
> **PR #18 은 PR #17 외에도 흔한 broker-template 변형을 추가로 인식한다:**
> `기존 / 변경`, `변경 전 / 변경 후`, `직전 / 현재` column header 와
> `<metric>(<year>) <new> <old> ▲|▼|-` side-anchor row 까지 포함. 표가
> 명확한 old/new pair 를 주지 않는 forecast-only 케이스는 `gap_reason` audit
> 필드로 추적되며 structured row 는 emit 되지 않는다 (`ambiguous_year_pivot`
> 등). 여전히 deterministic-only — OCR / Vision / API 호출 없음. PR #12 의
> arrow-pair 경로가 우선이며, PR #17 / PR #18 layout 은 그것이 못 잡은
> metric 만 보완한다.
>
> **PR #19 는 side-anchor scan 을 revision-header proximity 안으로 제한한다:**
> `<metric>(<year>) <a> <b> ▲|▼|-` 패턴이 본문 어디에든 있을 수 있으나
> 실제 revision panel 은 항상 `직전/현재` (또는 `기존/변경`, `변경 전/후`,
> `수정 전/후`, `추정치 변경`) 헤더 근처 ~15줄 안에 위치한다. 이를 벗어나면
> growth-rate / YoY 행이 같은 모양으로 우연히 매치될 수 있어 reject 한다.
>
> **PR #20 은 variant column-window scan (직전/현재 등) 도 동일한 정확도
> 처리를 적용한다:** 헤더 이후 window 길이를 40→15줄로 좁히고, window 안
> 에서도 `목표주가` 라인을 stop condition 으로 사용해 그 다음 본문의
> growth-rate 행이 실수로 metric pair 로 잡히지 않도록 한다. 추가로 각
> 후보 row 에 value-shape filter 를 통과시켜 `sales / operating_profit /
> net_income` 의 `old` `new` 두 값이 모두 abs<100 이면 growth-rate 으로
> 보고 reject (`variant_rejected_growth_rate` gap_reason). EPS 는 원 단위
> 라 작은 값이 정상이므로 면제. 본 변경은 실제 대덕전자 PDF cloud smoke 에서
> `1.9 → -6.2` 가 op revision 으로 잘못 잡히던 false positive 를 제거한다.

`gap_reason` (PR #18 + PR #19 + PR #20) 가능한 값:
- `parsed_metric_pair` — primary metric 추출 성공
- `no_revision_anchor` — 어떤 revision marker 도 발견 못 함
- `no_metric_pair` — anchor 는 발견됐으나 old/new pair 추출 실패. PR #34
  부터는 window-shape 분류기가 4 개 sub-category 로 세분화하므로 실제
  발화는 defensive fallback 일 때만 발생.
- **`no_metric_pair_target_price_only_window`** (PR #34) — revision
  window 안에 `목표주가` mention 만 있고 매출액 / 영업이익 / 순이익 /
  EPS metric label row 가 0 인 경우. target_price audit 은 별도
  `target_price_secondary.json` 이 처리하며 strict 게이트는 primary
  로 절대 승격하지 않는다.
- **`no_metric_pair_anchor_outside_pivot`** (PR #34) — text 안의 모든
  year-pivot header 라인이 revision window 가장자리에서 25 줄 이상
  떨어진 경우. revision marker 와 forecast 표가 서로 다른 page /
  section 에 있다는 신호.
- **`no_metric_pair_split_window_too_long`** (PR #34) — revision window
  길이가 30 줄 초과 AND revision-marker line 과 가장 가까운 metric-
  label line 사이 거리가 10 줄 초과인 경우. 본문이 두 개의 표를
  걸쳤거나 prose 가 길게 끼어 있는 신호.
- **`no_metric_pair_unhandled_broker_template`** (PR #34) — 위 3 sub-
  category trigger 에 걸리지 않은 catch-all. 기존 `no_metric_pair`
  보다 더 구체적인 fallback 이며, 향후 broker template 별 분석을 위해
  유지된다.
- `ambiguous_year_pivot` — forecast-only 표 (e.g. `2024A 2025A 2026E 2027F`)
- `target_price_only` — metric 없이 목표주가만 발견
- `empty_text` — pdfplumber 가 빈 text 반환
- **`side_anchor_no_near_header`** (PR #19) — side-anchor 패턴이 본문에 있으나
  recognized 헤더 (직전/현재, 기존/변경, 변경 전/후, 수정 전/후, 추정치 변경)
  근처 (~15줄) 가 아니어서 거부됨. growth-rate / YoY 행 false positive 방지.
- **`side_anchor_header_found_no_metric_pair`** (PR #19) — 헤더는 발견했지만
  proximity window 내에 metric side-anchor row 가 없음.
- **`variant_rejected_growth_rate`** (PR #20) — variant column-window 안
  에서 적어도 1개의 후보 metric row 가 있었으나 모두 value-shape filter
  로 growth-rate / YoY 로 reject 되어 surviving metric 이 없음. 헤더는
  실재하나 그 아래 표는 절대값 revision 이 아니라 % 변동률 표였음을 의미.
- **`natural_language_revision_ambiguous`** (PR #26) — 본문에 자연어
  revision pair (`<metric> X에서 Y로`) 가 있었으나 direction word
  (`상향/하향/raise/raised/lowered/cut/...`) 가 60-char tail window 안
  에 없거나, 두 클래스가 동시에 매칭되거나, direction word 와 numeric
  방향이 일치하지 않아 모두 reject. metric 추출 0 이며 false positive
  방지가 recall 보다 우선 — 임의 추정 금지.
- **`year_pivot_forecast_only_no_revision`** (PR #26 detector, PR #31
  rename) — strict forecast-only year-pivot 표.
  `parse_year_pivot_revision_rows` 가 True (3+ year 토큰) AND 본문에
  `목표주가 / 가이던스 / guidance / 추정치 변경 / 변동률 / revision`
  키워드가 모두 부재할 때만 발생. 동일 텍스트가 키워드 중 하나라도
  가지면 PR #31 의 `classify_year_pivot_gap` 분류기로 진입하고, 그것도
  None 이면 legacy `ambiguous_year_pivot` 로 fall through (PR #18 fixture
  의 byte-identity 보존을 위한 분기). 함수 이름은 `parse_year_pivot_no_revision_pair`
  로 유지되며, 표면 gap_reason 라벨만 PR #31 에서 rename 되었다.
- **`year_pivot_initiation_no_revision`** (PR #31) — year-pivot 검출 +
  legacy keyword 존재 + 신규 추정 / 신규 커버리지 / 최초 보고서 / 신규
  분석 / Coverage 시작 / initiation 키워드 중 하나가 본문에 있는 경우.
  Initiation 보고서는 정의상 old/new pair 가 존재하지 않으므로 metric 0
  이 정상.
- **`year_pivot_revision_labels_too_far`** (PR #31) — year-pivot +
  legacy keyword + strict revision label (`기존(`, `변경(`, `직전(`,
  `현재(`, `이전(`, `수정 후`, `수정 전`, `변경 후`, `변경 전`, 영문
  `previous(`, `current(`, `prev(`, `curr(`, `old(`, `new(`) 중 하나가
  본문에 있으나 year-pivot 헤더 라인과 ≥10 줄 떨어진 위치에 있는 경우.
- **`year_pivot_positional_revision_candidate`** (PR #31) — year-pivot +
  legacy keyword + strict revision label 이 year-pivot 헤더 ±10 줄 안에
  있으나 column-pair 형태로 묶이지 않은 경우 (e.g. 본문 prose 내 단발성
  언급). 명시적 old/new label-numeric 연결이 없으므로 conservative
  parser 가 metric 을 emit 하지 않는다.
- **`year_pivot_has_metric_headers_no_old_new`** (PR #31; PR #33 에서
  fallback 으로 강등) — year-pivot + legacy keyword + 행에 `(%)`,
  `(margin)`, `(YoY)`, `(QoQ)`, `OPM(%)`, `GPM(%)` 등 % / 성장률
  marker 가 있고 strict revision label 은 없는 경우. PR #33 부터는
  primary 라벨 자리를 row-level 분류기에 양보하고, 분류기가 metric
  label row 를 0개 발견했을 때만 fallback 으로 발화한다.
- **`year_pivot_metric_rows_all_yoy_growth`** (PR #33) — 위 부모 카테고리
  진입 후 row-level 분류기가 검출한 모든 metric label row 가 yoy/
  성장률 marker 를 가진 경우. yoy marker 셋: `(YoY) / (yoy) / (YOY) /
  (QoQ) / (qoq) / (%, YoY) / (%, yoy) / 성장률 / 증가율 / 증감률 /
  growth`. 이 row 들은 절대값 revision pair 가 정의상 없으므로
  structured row 를 emit 하지 않는다 (false-positive 방지).
- **`year_pivot_metric_rows_all_margin`** (PR #33) — 모든 metric label
  row 가 margin / 이익률 marker 를 가진 경우. margin marker 셋:
  `(margin) / (Margin) / (MARGIN) / OPM(%) / GPM(%) / NPM(%) / 이익률 /
  원가율 / (%)`. 마찬가지로 절대값 revision pair 추출 대상 아님.
- **`year_pivot_metric_rows_mixed_units`** (PR #33) — metric label row
  들이 절대값 (`매출액 892 1,065 ...`) + margin (`영업이익률(%)`) +
  yoy (`EPS 성장률(YoY)`) 같은 형태로 단위가 섞인 경우. 실제 broker
  report 의 가장 흔한 패턴이며 conservative 파서가 row 별 단위 차이를
  결합해 revision pair 를 합성하지 않는다.
- **`duplicate_column_flat_rejected`** (PR #27) — variant column-window
  scanner 가 한 metric row 에서 byte-identical 두 numeric token (old
  == new as strings) 을 보았으나 같은 line 에 명시적 flat context
  (`유지 / 동일 / 변동 없음 / unchanged / flat / no change`) 가 없어
  reject. variant scan 안에서 모든 후보 row 가 reject 되어 surviving
  metric 이 0 일 때만 발화. 일부 row 만 reject 되는 mixed 케이스에서는
  발화하지 않으며 (gap=parsed_metric_pair) rejected metric 은 단순히
  breakdown 의 metrics dict 에서 빠진다.

precedence (위에서 아래로, 먼저 만족하는 항목이 win):
`parsed_metric_pair` → `empty_text` → `target_price_only` →
`variant_rejected_growth_rate` (PR #20) → `duplicate_column_flat_rejected`
(PR #27) → `no_metric_pair` (PR #34: replaced by 4 sub-categories
`no_metric_pair_target_price_only_window` /
`no_metric_pair_anchor_outside_pivot` /
`no_metric_pair_split_window_too_long` /
`no_metric_pair_unhandled_broker_template`; legacy label kept as
defensive fallback) → `side_anchor_no_near_header` /
`side_anchor_header_found_no_metric_pair` (PR #19) →
`natural_language_revision_ambiguous` (PR #26) →
`year_pivot_forecast_only_no_revision` (PR #26 detector, PR #31 rename) →
`classify_year_pivot_gap` (PR #31; `year_pivot_initiation_no_revision` /
`year_pivot_positional_revision_candidate` /
`year_pivot_revision_labels_too_far` /
`year_pivot_metric_rows_all_yoy_growth` (PR #33) /
`year_pivot_metric_rows_all_margin` (PR #33) /
`year_pivot_metric_rows_mixed_units` (PR #33) /
`year_pivot_has_metric_headers_no_old_new` (PR #33 fallback)) →
`ambiguous_year_pivot` → `no_revision_anchor`. 단, variant scan 안에서
growth-rate 와 dup-flat reject 가 동시에 일어나면
`variant_rejected_growth_rate` 가 우선 (보다 구체적 시그널). PR #31
classifier 는 (a) year-pivot 검출, (b) legacy neutral keyword 존재 두
조건을 모두 만족할 때만 fire 하며 PR #18 synthetic fixture
(`real_layout_variant_ambiguous_year_pivot.txt`) 는 어떤 sub-category
trigger 에도 매칭되지 않아 legacy `ambiguous_year_pivot` 가 그대로
유지된다.

PR #27: variant column-window scanner 의 byte-identical 두 numeric
token 처리 contract:
1. arrow-pair scanner (PR #12; `<metric> X → Y`) 는 별도 코드 경로이며
   `validate_flat_revision_pair` 게이트를 호출하지 않는다. PR #12
   broker_b_op_only_up_sales_flat fixture 처럼 `매출액 30,000 → 30,000`
   같은 legacy flat 은 그대로 admit.
2. variant column-window scanner 에서 old==new 인 row 는 같은 line 에
   `_FLAT_CONTEXT_KEYWORDS` (`유지`, `동일`, `변동 없음`, `변동없음`,
   `unchanged`, `flat`, `no change`, `no-change`) 중 하나가 있을 때만
   admit. 없으면 reject (metrics dict 진입 금지).
3. PR #26 audit flag `flat_possible_duplicate_column` 은 제거.

PR #28: side-anchor template 보강:
1. **Multi-line KV form** — `<metric>(year)?` 만 있는 line 다음 1-3줄
   안에서 `<old_label> <num>` AND `<new_label> <num>` 페어를 찾으면
   commit. metric line 자체에 숫자/추가 텍스트가 있으면 anchor 안 됨
   (false positive 방지). label 순서 무관 (기존-then-변경 또는
   변경-then-기존 모두 처리).
2. **Reversed-inline KV form** — PR #26 inline KV regex 의 forward
   순서 (`<metric>(year): 기존 X / 변경 Y`) 외에 reversed 순서
   (`<metric>(year): 변경 Y / 기존 X`) 도 매칭하도록 두 번째 regex
   추가. 두 패턴 모두 fall-through; 첫 매칭이 우선.
3. **Row-level margin / yoy / (%) reject** — PR #26 inline KV 가
   매칭한 row 가 `영업이익률 / 이익률 / 변동률 / 성장률 / yoy / qoq /
   margin / growth / yield / (%)` 중 하나를 포함하면 거부. multi-line
   KV helper 도 lookahead window 안에 같은 marker 가 있으면 거부.
4. 새 helper 4개:
   - `parse_side_anchor_multiline_kv_revision(text)` — multi-line 진입점
   - `collect_metric_context_window(lines, idx, window=4)` — lookahead helper
   - `extract_labeled_old_new_pair(window_text)` — 양쪽 label REQUIRED;
     없으면 (None, None) 반환
   - `reject_percentage_or_margin_context(line)` — margin/% 게이트

PR #29: --inventory batch path 정비:
1. **`HARD_MAX_PDFS` 50 / `DEFAULT_MAX_PDFS` 10** — 단일 PDF smoke 는
   변화 없음. operator-host batch smoke 는 `--max-pdfs` 를 50까지
   올릴 수 있고 51 이상은 exit 2 로 거부.
2. **신규 4번째 output `parser_batch_summary.json`** — `--apply` 시
   `<workdir>/` 에 항상 작성. counter / file-name 만 포함하며 PDF
   본문이나 추출 텍스트 leak 없음. schema =
   `phase3:parser_batch_summary:v1`. 필드: `pdf_count`,
   `parsed_pdf_count`, `failed_pdf_count`, `structured_rows_total`,
   `breakdown_rows_total`, `target_price_secondary_rows_total`,
   `direct_trade_signal_true_count`, `pdf_engine_used_counts`,
   `gap_reason_counts`, `parsed_metric_pair_count`,
   `ticker_hint_counts`, `files_with_structured_rows`,
   `files_without_structured_rows`, `files_with_target_price_only`,
   `files_with_empty_text`, `files_with_parser_errors`,
   `forbidden_actions_confirmed` (OCR/Vision/API, dts=true,
   target_price-as-primary, repo write, drive write, rolling --apply,
   promote/Super Pack 모두 0).
3. **별도 chain runner**: `examples/run_inventory_batch_smoke.py` —
   parser → (선택) bridge → (선택) merge → (선택) build --strict
   (모두 dry-run-friendly; outputs to `/tmp` only). `--chain-bridge`,
   `--chain-merge`, `--chain-build` 플래그로 단계별 활성. rolling
   --apply 는 코드 어디에도 호출하지 않음. workdir 가 repo 안에 있으면
   exit 2; `--max-pdfs` 51+ 도 exit 2.

PR #30: real-PDF batch path first-class:
1. **parser `--inventory` 모드 확장** — per-entry source resolution 우선순위:
   `selected[].local_pdf_path / pdf_path` (절대경로; repo 내부 거부) →
   `--pdf-dir / <filename>` → `--text-dir / <stem>.txt`. PR #12-#29
   synthetic-text fixture 동작은 byte-identical 보존.
2. **새 CLI**: `--pdf-dir <DIR>`. PDF 추출은 기존 pdfplumber/pypdf 경로
   그대로 (OCR/Vision fallback 없음). 누락 파일은 batch abort 없이 entry
   단위 missing 으로 기록.
3. **`parser_batch_summary.json` schema 확장** (additive; 기존 필드 보존):
   - `source_mode_counts` — `{text_fixture, pdf_file, empty, missing, error}` 별 count
   - `files_with_pdf_parse_errors` — pdfplumber/pypdf 둘 다 실패한 파일 (PDF 자체 문제)
   - `files_with_missing_pdf` — `--pdf-dir` 또는 `selected[].pdf_path` 에서 찾지 못한 파일
4. **chain runner `--pdf-dir`** — parser 로 그대로 forward. workdir 외부
   가드, `--max-pdfs` 51+ 거부 동일.

PR #31: year-pivot gap taxonomy refinement:
1. **`ambiguous_year_pivot` 분해 (10/20 → 더 구체적 분포)** — PR #30 20-PDF
   smoke 에서 dominant 였던 `ambiguous_year_pivot` 를 4 개 sub-category 로
   세분화. classifier `classify_year_pivot_gap(text)` 는 (a) year-pivot
   검출, (b) PR #26 `_YEAR_PIVOT_NEUTRAL_KEYWORDS` 중 하나가 본문에 존재
   두 조건을 모두 만족할 때만 fire. 어떤 sub-category 도 매칭 안되면
   None 을 반환하고 legacy `ambiguous_year_pivot` 가 그대로 표면 라벨로
   유지됨 (PR #18 fixture byte-identity 보존).
2. **`year_pivot_no_revision_pair` → `year_pivot_forecast_only_no_revision`
   rename**. 함수 `parse_year_pivot_no_revision_pair` 의 truth table 은
   byte-identical; 표면 gap_reason 라벨만 PR #31 에서 변경. PR #26 fixture
   `real_layout_year_pivot_forecast_only.txt` 의 gap_reason 출력은 새
   라벨로 출력되며, 입력 텍스트는 unchanged.
3. **신규 helper** (5):
   - `classify_year_pivot_gap(text) -> str | None` — 메인 분류기
   - `_year_pivot_has_initiation_keyword(text)` — 신규 추정 / Coverage 시작
   - `_year_pivot_has_strict_revision_label(text)` — paren-bound 또는
     spelled-out column heading (e.g. `기존(`, `수정 후`)
   - `_year_pivot_has_margin_yoy_marker(text)` — `(%)`, `(margin)`,
     `(YoY)`, `(QoQ)`, `OPM(%)`, `GPM(%)`
   - `_year_pivot_label_near_pivot(text)` — strict label 이 year-pivot
     header 라인과 ±10 줄 안에 있는지
4. **신규 gap_reason 4 개**:
   - `year_pivot_initiation_no_revision`
   - `year_pivot_positional_revision_candidate`
   - `year_pivot_revision_labels_too_far`
   - `year_pivot_has_metric_headers_no_old_new`
5. **conservative 보장**: 어떤 신규 helper 도 forecast-only year-pivot
   table 에서 임의로 old/new pair 를 합성하지 않는다. 명시적 column-
   pair label (e.g. `기존(26E)` / `변경(26E)` 페어가 같은 헤더 라인에)
   가 있어야만 기존 PR #18 variant scanner 가 metric 을 추출하며, 그
   외에는 sub-category gap_reason 만 audit 로 남는다.
6. **fixture 7 개** (`stock_research/phase3_report_pipeline/examples/estimate_table_fixtures/texts/`):
   - `real_layout_year_pivot_forecast_only_no_revision.txt`
     → `year_pivot_forecast_only_no_revision`
   - `real_layout_year_pivot_labeled_existing_changed.txt`
     → `parsed_metric_pair` (operating_profit primary, direction=up)
   - `real_layout_year_pivot_metric_headers_no_old_new.txt`
     → `year_pivot_metric_rows_mixed_units` *(PR #33; was
     `year_pivot_has_metric_headers_no_old_new` in PR #31 — fixture
     text unchanged, gap_reason refined by row-level classifier)*
   - `real_layout_year_pivot_positional_candidate_rejected.txt`
     → `year_pivot_positional_revision_candidate`
   - `real_layout_year_pivot_margin_yoy_rejected.txt`
     → `year_pivot_metric_rows_mixed_units` *(PR #33; was
     `year_pivot_has_metric_headers_no_old_new` in PR #31)*
   - `real_layout_year_pivot_metric_rows_all_yoy_growth.txt`
     *(PR #33 new)* → `year_pivot_metric_rows_all_yoy_growth`
   - `real_layout_year_pivot_metric_rows_all_margin.txt`
     *(PR #33 new)* → `year_pivot_metric_rows_all_margin`
7. **inventory** `examples/estimate_table_fixtures/inventory.year_pivot_taxonomy.json`
   (5 → **7** entries; SAMPLECO synthetic; 모든 sha 는 deterministic
   placeholder).

PR #33: year-pivot metric-header sub-taxonomy:
1. **`year_pivot_has_metric_headers_no_old_new` 분해 (PR #31)**:
   row-level 분류기가 metric label row 별 marker 단위를 검사해 4개
   하위 카테고리로 분리. (a) `year_pivot_metric_rows_all_yoy_growth`
   — 모든 metric row 가 yoy 단위 (b)
   `year_pivot_metric_rows_all_margin` — 모든 metric row 가 margin
   단위 (c) `year_pivot_metric_rows_mixed_units` — 단위 혼재 (d) 기존
   `year_pivot_has_metric_headers_no_old_new` — metric label row 가 0 인
   fallback.
2. **신규 helper (3 + 1)**:
   - `_classify_metric_row_marker(line) -> 'yoy' | 'margin' | 'absolute' | None`
   - `_aggregate_year_pivot_metric_row_kinds(text) -> dict`
   - `classify_year_pivot_metric_header_subgap(text) -> str`
   - 신규 marker tuple `_YEAR_PIVOT_ROW_YOY_MARKERS`,
     `_YEAR_PIVOT_ROW_MARGIN_MARKERS` (yoy 우선 검사 → `(%, YoY)` 같은
     overlap 케이스가 yoy 로 안전하게 분류된다).
3. **conservative 보장**:
   - row-level 분류기는 metric label row (line.startswith(label) for
     label in `_METRIC_LABEL_PREFIXES`) 만 고려.
   - 절대값 + margin / yoy mix 일 때 절대값과 margin/yoy 행을 결합해
     revision pair 를 합성하지 않는다.
   - structured row 추출은 PR #18 variant scanner 와 PR #31
     labeled_existing_changed 경로에 그대로 위임.
4. **reserved (문서만)**: `year_pivot_metric_headers_no_revision_value`,
   `year_pivot_unhandled_broker_template` — 실제 PDF smoke 에서 명확한
   trigger 가 보일 때 별도 PR 로 활성화.
5. **fixture 2 개 추가**: `real_layout_year_pivot_metric_rows_all_yoy_growth.txt`,
   `real_layout_year_pivot_metric_rows_all_margin.txt` (SAMPLECO synthetic).
   `inventory.year_pivot_taxonomy.json` 5 → 7 entries.

CLI 사용 예시 (operator-host real-PDF batch smoke):
```
python3 stock_research/phase3_report_pipeline/examples/run_inventory_batch_smoke.py \
    --inventory <real_inventory.json> \
    --pdf-dir   /tmp/phase3_batch_pdfs \
    --pdf-engine auto \
    --workdir   /tmp/phase3_batch_smoke \
    --max-pdfs  20 \
    --manual-meta <manual_meta.json> \
    --ticker-map  stock_research/phase3_report_pipeline/resources/ticker_map.csv \
    --chain-bridge --chain-merge --chain-build
```
Paste-back: report ONLY `parser_batch_summary.json` +
`inventory_batch_smoke_summary.json` 카운터; PDF 본문 / 추출 텍스트 /
full sha256 절대 paste 금지.

CLI 사용 예시 (synthetic batch fixture; dry-run 끝까지):
```
python3 stock_research/phase3_report_pipeline/examples/run_inventory_batch_smoke.py \
    --inventory stock_research/phase3_report_pipeline/examples/estimate_table_fixtures/inventory.batch_smoke.json \
    --text-dir  stock_research/phase3_report_pipeline/examples/estimate_table_fixtures/texts \
    --workdir   /tmp/pr29_smoke \
    --manual-meta /tmp/pr29_smoke/manual_meta.json \
    --ticker-map  stock_research/phase3_report_pipeline/resources/ticker_map.csv \
    --chain-bridge --chain-merge --chain-build
```
산출 (workdir):
- `parser_batch_summary.json` — 항상 작성 (PR #29)
- `parsed_meta.json` — `--chain-bridge` 시
- `merged_parsed_meta.json` — `--chain-merge` 시
- `build_output/<date>/estimate_revision_*.json` — `--chain-build` 시
- `inventory_batch_smoke_summary.json` — runner 의 aggregated summary

핵심 원칙:
- **primary signal 은 `sales` / `operating_profit` / `net_income` / `eps` 추정치 변경**
  이다. 목표주가는 `secondary_reference` 로만 취급되며 primary estimate row
  로 emit 되지 않는다.
- primary metric 선택 우선순위: `operating_profit > net_income > sales > eps`
  (PR #12 의 `PRIMARY_METRIC_PRIORITY` 상수). `merge_meta.py` 가 sha256 당 1 row
  만 허용하므로 PDF 당 정확히 한 개의 primary metric row 만 emit 된다.
- 목표주가는 항상 `secondary_reference` audit 로만 기록된다.
  `target_price_secondary.json` 은 **primary emission 여부와 무관**하게
  목표주가 numeric pair 가 있는 모든 PDF 를 audit 로 보관한다 (primary 도
  같이 emit 된 PDF 는 `primary_metric_present=true`, 목표주가-only 는 `false`).
  - 목표주가-only 리포트는 `structured_extraction.json` 에 절대 들어가지 않는다.
  - `target_price_secondary.json` 은 audit-only — `merge_meta.py` /
    `build_report_estimate_v132.py` / `rolling_append.py` 어느 것도 소비하지 않는다.
  - target price 가 `N/A` / 비numeric 이면 secondary 에도 기록되지 않는다.
- `horizon_missing` / `malformed` row 는 strict gate 에서 reject 대상이다.
  parser 가 metric 을 찾았더라도 `horizon` 이 비어있으면 build `--strict` 가 거부.
- **모든 row 의 `direct_trade_signal` 은 항상 `False`**. main() 의 hard invariant
  로 emit 단계에서 다시 한 번 검증한다.

CLI 사용 예시 (synthetic 검증):
```
python3 stock_research/phase3_report_pipeline/scripts/extract_report_estimate_table.py \
    --inventory stock_research/phase3_report_pipeline/examples/estimate_table_fixtures/inventory.json \
    --text-dir  stock_research/phase3_report_pipeline/examples/estimate_table_fixtures/texts \
    --date 2026-04-30 \
    --workdir /tmp/phase3_pr12 \
    --apply
```

산출 (workdir 내):
- `structured_extraction.json` — primary metric row (PDF 당 최대 1개; merge_meta
  호환)
- `estimate_table_breakdown.json` — audit-only (모든 metric breakdown)
- `target_price_secondary.json` — audit-only. **모든** PDF 의 목표주가 numeric
  pair 를 보관 (primary 도 같이 emit 된 PDF 포함). `merge_meta.py` /
  `build_report_estimate_v132.py` / `rolling_append.py` 는 이 파일을 소비하지
  않는다.

체인 연결 (`merge_meta → build --strict → rolling --strict-estimate dry-run`)
은 PR #9/#10 의 `run_estimate_revision_dryrun.py` 가 그대로 받아 처리한다.
synthetic fixture 6 records 기준 기대 결과:
- `rows_in / accepted / rejected = 6 / 3 / 3`
- `direct_trade_signal_all_false = true`
- `rolling validated/rejected/dup/to_add = 3 / 0 / 1 / 2`

### `--pdf` (PR #13 + PR #16 fallback)

PR #13 은 `extract_report_estimate_table.py` 에 단일 PDF 입력 경로를
추가했고, **PR #16** 이 `--pdf-engine {auto,pdfplumber,pypdf}` 옵션을 더해
deterministic 추출 엔진을 선택할 수 있게 했다. **OCR/Vision/API 호출은
여전히 없다** — pdfplumber 와 pypdf 모두 local-only deterministic 라이브러리.

```
# 둘 중 하나는 설치되어 있어야 한다 (둘 다 설치도 OK)
pip install pdfplumber   # 권장 — table 추출 정확도
pip install pypdf        # 가벼운 fallback (PR #16; pdfplumber native dep 가
                         # 깨진 환경에서도 import 됨)

python3 stock_research/phase3_report_pipeline/scripts/extract_report_estimate_table.py \
    --pdf /path/to/wisereport_company.pdf \
    --pdf-engine auto \
    --date 2026-04-30 \
    --workdir /tmp/phase3_pr16 \
    --apply

# 옵션:
#   --pdf-engine pdfplumber   # 강제로 pdfplumber 만 사용
#   --pdf-engine pypdf        # 강제로 pypdf 만 사용 (PR #16)
#   --debug-text-out /tmp/phase3_pr16/extracted.txt   # 저장소 외부 경로만 허용
```

`--pdf-engine` 동작 (PR #16):
- `auto` (기본) — pdfplumber 시도 → 실패하면 pypdf 시도 → 둘 다 안 되면 exit 2.
  실패 사유는 stderr 의 `[pdf engine] <name>: <reason>` 줄로 모두 노출된다.
- `pdfplumber` / `pypdf` — 해당 엔진만 시도. import 또는 parse 실패 시 즉시 exit 2.
- 사용된 엔진은 row 의 `extraction_method` 에 `deterministic_pdf_table_v1+<engine>`
  형태로 stamp 된다 (audit 용; merge_meta 의 priority gate 에는 영향 없음).
- 빈 PDF text → structured row 0, breakdown audit 에 primary=None 으로 기록.

PR #13 가드:
- pdfplumber 미설치 → exit 2 + `pip install pdfplumber` 안내. `--text` /
  `--inventory` 경로는 pdfplumber 없이도 그대로 동작한다.
- `--pdf` 파일 부재 → exit 2.
- `--debug-text-out` 가 repo 내부 경로 → exit 2 (실데이터 leak 방지).
- `--debug-text-out` 가 `--pdf` 없이 사용되면 exit 2.
- `--ocr` 는 여전히 refused (PR #12/#13 모두 deterministic-only).
- `--max-pdfs > 10` 거부, `--apply` 시 `--workdir` repo 내부 거부.

`--pdf` 는 단일 파일 처리 전용이다. inventory 의 `selected[]` PDF 들을
일괄 처리하는 경로는 PR #14+ 의 별도 작업으로 남긴다 — 그 시점에는 PR #11 의
selector inventory 와 함께 묶일 예정이다. **실제 WiseReport 10-PDF batch 는
여전히 operator host 에서 제한 실행하며 결과는 repo 에 커밋하지 않는다.**

## PR #38 — Revision-trend 운영 산출물 (`emit_revision_trend.py`)

`build_report_estimate_v132 --strict --apply` 가 만든 accepted rows 를 받아 두 가지 운영 산출물 (CSV + JSON) 을 만든다. 모두 dry-run-default. parser / bridge / merge / build / ticker_map / broker autodetect 코드는 변경하지 않는다 (다운스트림 emit-only).

### Dry-run 단독 실행

```
python3 stock_research/phase3_report_pipeline/scripts/emit_revision_trend.py \
    --accepted-rows /tmp/phase3_runner/wk/build_output/2026-04-30/estimate_revision_rows.json \
    --structured /tmp/phase3_runner/wk/structured_extraction.json \
    --output-dir /tmp/phase3_runner/wk/emit \
    --date 2026-04-30
# (dry-run; 파일 작성 없음. summary 만 stdout)
```

### Apply (파일 생성)

```
python3 stock_research/phase3_report_pipeline/scripts/emit_revision_trend.py \
    --accepted-rows /tmp/phase3_runner/wk/build_output/2026-04-30/estimate_revision_rows.json \
    --structured /tmp/phase3_runner/wk/structured_extraction.json \
    --output-dir /tmp/phase3_runner/wk/emit \
    --date 2026-04-30 \
    --apply
# /tmp/phase3_runner/wk/emit/2026-04-30/ 아래에 다음 5개 파일이 생긴다:
#   report_revision_trend.json
#   report_revision_trend.csv
#   report_estimate_high_table_candidates.json
#   report_estimate_high_table_candidates.csv
#   emit_revision_trend_summary.json
```

### 분류 5종 (one per accepted row)

| classification | 조건 |
| --- | --- |
| `high_conviction` | direction=up AND metric ∈ {operating_profit / net_income / sales / eps} AND `|new-old|/|old|` ≥ 5% AND old_target ≠ 0 |
| `margin_expansion` | (예약; v1 에서는 항상 0) |
| `marginal_review` | direction=flat, OR direction=up + delta < 5%, OR direction=up + old_target = 0 |
| `downside_guard_excluded` | direction=down (high_table 후보 영구 제외) |
| `data_insufficient` | required field 누락 / invalid; `metric=target_price` 도 여기 (secondary reference 전용) |

### Invariant (PR #38 가드)

- `direct_trade_signal` 은 출력 row / summary 모두에서 **항상 false**. 입력에 true 가 한 건이라도 있으면 exit 3 거부.
- `metric=target_price` 인 row 는 절대 `high_conviction` / `margin_expansion` 으로 들어가지 않는다 (target_price-as-primary 금지).
- direction=down 인 row 는 `report_estimate_high_table_candidates` 에 절대 포함되지 않는다.
- `--output-dir` 가 repo 안이면 거부 (PR #29 chain runner 가드와 동일 정책).
- Default dry-run; `--apply` 명시 시에만 파일 생성. `rolling_append.py` 호출 절대 없음.

### Self-test

```
python3 stock_research/phase3_report_pipeline/examples/run_emit_revision_trend_fixture.py
```

9-case fixture (5/5 분류 + target_price-only + horizon-empty + direction-down + old_target=0 invariant) 모두 cover. PASS 시에만 exit 0.

## PR #39 — WiseReport date-folder inventory (`build_wisereport_inventory.py`)

operator-host 로컬 마운트 또는 Drive 마운트의 `<root>/<YYYY-MM-DD>/{기업,산업}` 폴더를 스캔해 단일 inventory JSON 을 작성한다. parser / bridge / merge / build / emit 어느 곳도 변경하지 않는다.

### Dry-run

```
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_inventory.py \
    --root /mnt/wisereport \
    --date 2026-04-30 \
    --include-company \
    --include-industry \
    --out /tmp/wisereport_inv.json
# (dry-run; 파일 작성 없음. summary 만 stdout)
```

### Apply (파일 생성)

```
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_inventory.py \
    --root /mnt/wisereport \
    --date 2026-04-30 \
    --include-company \
    --include-industry \
    --out /tmp/wisereport_inv.json \
    --max-company-pdfs 50 \
    --max-industry-pdfs 50 \
    --apply
```

### 회사 entry vs 산업 entry

| | company (`기업`) | industry (`산업`) |
| --- | --- | --- |
| report_type | `company` | `industry` |
| folder_type | `기업` | `산업` |
| bracket field | `ticker_hint` | `sector_hint` |
| `summary_queue` | (없음) | `true` (LLM 요약 큐 후보) |
| 다운스트림 | PR #29 chain runner `--inventory` 입력으로 OK (PR #40 `selected[]` alias 덕분에 변환 없이 직접 소비) | parser 에 절대 들어가지 않음 (`selected[]` alias 에 미포함) |

### PR #40 `selected[]` alias

inventory output 은 두 동등한 자리에 회사 entry 를 노출한다:

- `selected_company[]` — schema-stable canonical 회사 리스트
- `selected[]`         — `selected_company[]` 의 byte-equal mirror (PR #40 추가). 기존 `extract_report_estimate_table.py` (`selected[]` 를 읽음) 와 `run_inventory_batch_smoke.py --inventory` 가 별도 adapter 없이 바로 소비.

`selected_industry[]` 는 절대 `selected[]` 에 mirror 되지 않는다. summary 의 `selected_alias_count` (= len(selected) = len(selected_company)) 와 `selected_alias_matches_company: true` 가 매번 alias invariant 를 명시적으로 기록한다.

### 가드

- `--out` repo 안 + `--apply` → exit 2
- `--max-*-pdfs` > 50 → exit 2
- `--include-company` / `--include-industry` 둘 다 누락 → exit 2
- dry-run default; `--apply` 만 파일 생성
- `direct_trade_signal=false` 강제; `summary.direct_trade_signal_true_count=0`; `forbidden_actions_confirmed.*=0`
- sha256 prefix 12 hex 만 — PDF body fingerprint 누출 방지

### Self-test

```
python3 stock_research/phase3_report_pipeline/examples/run_wisereport_inventory_fixture.py
```

5 scenarios + 4 guards. PASS 시에만 exit 0.

## What this pack does NOT do

- 실제 PDF 파싱 (외부 파서가 담당)
- 실제 매매·주문·체결
- Drive 원본 PDF 이동/복사/삭제
- 자동 promote
- Super Pack 재생성
