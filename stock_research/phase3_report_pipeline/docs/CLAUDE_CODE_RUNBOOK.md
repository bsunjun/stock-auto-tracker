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
# PR #22 hotfix: bridge gate가 빈 ticker도 filename bracket fallback을 타게
# 통과시키는지 end-to-end 확인
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

## Deterministic estimate table parser (PR #12 + PR #17 + PR #18 + PR #19 + PR #20)

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
- `no_metric_pair` — anchor 는 발견됐으나 old/new pair 추출 실패
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

precedence (위에서 아래로, 먼저 만족하는 항목이 win):
`parsed_metric_pair` → `empty_text` → `target_price_only` →
`variant_rejected_growth_rate` (PR #20) → `no_metric_pair` →
`side_anchor_no_near_header` / `side_anchor_header_found_no_metric_pair`
(PR #19) → `ambiguous_year_pivot` → `no_revision_anchor`.

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

## What this pack does NOT do

- 실제 PDF 파싱 (외부 파서가 담당)
- 실제 매매·주문·체결
- Drive 원본 PDF 이동/복사/삭제
- 자동 promote
- Super Pack 재생성
