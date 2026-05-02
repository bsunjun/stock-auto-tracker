# PR #39 — WiseReport Date-Folder Inventory

`scripts/build_wisereport_inventory.py` 는 `<root>/<YYYY-MM-DD>/{기업,산업}`
구조의 폴더를 스캔해 단일 inventory JSON 을 만든다. parser / bridge /
merge / build / emit / ticker_map / broker autodetect 코드는 전혀 건드리지
않는다 — 본 PR 은 **새 스캐너 한 개만 추가**한다.

## Why

Phase 3 의 기존 chain runner (`examples/run_inventory_batch_smoke.py`) 는
이미 `--inventory` 입력을 받지만, inventory 자체를 만드는 표준 도구가
없었다. PR #11 의 `wisereport_sample_select.py` 는 `--max-pdfs 10` 까지만
다루고 회사/산업 분리도 하지 않는다. PR #39 는:

1. **기업 / 산업 folder type 분리** — 두 폴더를 한 번에 스캔하면서 entry
   shape 을 분리한다. 회사 entry 는 PR #29 chain runner 의 `--inventory`
   로 그대로 흘러갈 수 있다. 산업 entry 는 `summary_queue=true` 로 표시되어
   parser 에 들어가지 않으며 다운스트림 LLM-summary 큐로만 보관된다.
2. **운영 가드 일원화** — `--out` repo 안 거부, `--max-*-pdfs > 50` 거부,
   `--include-*` 둘 다 누락 거부, dry-run default, `direct_trade_signal=false`
   영구 강제 등 PR #29 / PR #38 와 같은 가드 정책을 그대로 적용.
3. **sha256 prefix 12 만 노출** — full sha256 / PDF body fingerprint 가
   inventory 에 누출되지 않게 한다.

## CLI

```
python3 scripts/build_wisereport_inventory.py \
    --root <root> \
    --date YYYY-MM-DD \
    [--include-company] \
    [--include-industry] \
    --out <out-path> \
    [--max-company-pdfs N]   # default 50, hard cap 50
    [--max-industry-pdfs N]  # default 50, hard cap 50
    [--apply]
```

| flag | required | 의미 |
| --- | --- | --- |
| `--root` | ✓ | WiseReport root (operator-host local mount 또는 Drive mount). `<root>/<date>/{기업,산업}/` 구조 가정. |
| `--date` | ✓ | `YYYY-MM-DD` 형식만 허용. 다른 형식 → exit 2. |
| `--include-company` | (둘 중 하나는 필수) | `<root>/<date>/기업` 스캔. |
| `--include-industry` | (둘 중 하나는 필수) | `<root>/<date>/산업` 스캔. |
| `--out` | ✓ | 출력 JSON 경로. `--apply` + repo 안 → exit 2. |
| `--max-company-pdfs` | | per-folder 캡 (default 50, HARD_MAX=50). |
| `--max-industry-pdfs` | | per-folder 캡 (default 50, HARD_MAX=50). |
| `--apply` | | 파일 생성. 없으면 dry-run. |

## 출력 스키마 (`phase3:wisereport_date_folder_inventory:v1`)

```json
{
  "schema": "phase3:wisereport_date_folder_inventory:v1",
  "root": "<root>",
  "date": "YYYY-MM-DD",
  "include_company": true|false,
  "include_industry": true|false,
  "max_company_pdfs": 50,
  "max_industry_pdfs": 50,
  "summary": {
    "company_pdf_count": int,
    "industry_pdf_count": int,
    "malformed_filename_count": int,
    "duplicate_basename_count": int,
    "skipped_non_pdf_count": int,
    "capped_company_count": int,
    "capped_industry_count": int,
    "direct_trade_signal_true_count": 0
  },
  "selected_company": [
    {
      "report_date": "2026-04-30",
      "report_type": "company",
      "filename": "20260430_[샘플전자] 1Q26 어닝 서프라이즈.pdf",
      "local_pdf_path": "/mnt/wisereport/2026-04-30/기업/20260430_[샘플전자] 1Q26 어닝 서프라이즈.pdf",
      "ticker_hint": "샘플전자",
      "title_hint": "1Q26 어닝 서프라이즈",
      "folder_type": "기업",
      "sha256_prefix_12": "3f1c92aabb04",
      "direct_trade_signal": false
    }
  ],
  "selected_industry": [
    {
      "report_date": "2026-04-30",
      "report_type": "industry",
      "filename": "20260430_[반도체] 1Q 업황 점검.pdf",
      "local_pdf_path": "/mnt/wisereport/2026-04-30/산업/20260430_[반도체] 1Q 업황 점검.pdf",
      "sector_hint": "반도체",
      "title_hint": "1Q 업황 점검",
      "folder_type": "산업",
      "sha256_prefix_12": "9b22ff012c70",
      "direct_trade_signal": false,
      "summary_queue": true
    }
  ],
  "malformed": [{"filename": ..., "folder": "기업", "reason": "no_bracket_segment"}],
  "skipped_non_pdf": [{"filename": "notes.txt", "folder": "기업"}],
  "duplicate_basename": [],
  "forbidden_actions_confirmed": {
    "ocr_or_vision_or_api_calls": 0,
    "drive_writes": 0,
    "drive_renames": 0,
    "drive_deletes": 0,
    "repo_writes": 0,
    "rolling_apply": 0,
    "promote_or_super_pack": 0,
    "direct_trade_signal_true": 0,
    "target_price_as_primary": 0,
    "pdf_body_text_committed": 0
  },
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## Filename 분류 규칙

`^(?P<date>\d{8})_\[(?P<bracket>[^\]]+)\]\s*(?P<title>.+)\.pdf$` (case-insensitive
extension).

| 케이스 | 결과 |
| --- | --- |
| `20260430_[샘플전자] 1Q26 ....pdf` | `selected_company[]` 에 추가 (회사) 또는 `selected_industry[]` (산업) |
| `notes.txt` | `skipped_non_pdf[]` |
| `no_bracket_segment.pdf` | `malformed[]` reason=`no_bracket_segment` |
| `[no_yyyymmdd_prefix] 제목.pdf` | `malformed[]` reason=`no_yyyymmdd_prefix` |
| `20260430_no_brackets_either.pdf` | `malformed[]` reason=`no_bracket_segment` |
| 기타 회귀 실패 | `malformed[]` reason=`regex_match_failed` |

## Invariants (PR #39 가드)

- `--out` repo 안 + `--apply` → exit 2.
- `--max-*-pdfs > 50` → exit 2 (HARD_MAX 침범).
- `--include-*` 둘 다 누락 → exit 2.
- dry-run default; `--apply` 만 파일 생성.
- `direct_trade_signal` 모든 entry 에서 `false`; `summary.direct_trade_signal_true_count=0`.
- sha256 prefix 12 hex 만 노출 (PDF body fingerprint 누출 방지).
- `selected_industry[]` 는 절대 parser / bridge / merge / build / emit 으로
  흘러가지 않는다 (스키마상 `summary_queue=true` 로만 표시).

## 호환 흐름

```
# 1. operator-host 에서 inventory 작성 (PDF 본문 절대 repo 에 들어가지 않음)
python3 .../build_wisereport_inventory.py --root /mnt/wisereport \
    --date 2026-04-30 --include-company --out /tmp/inv.json --apply

# 2. 회사 PDF 만 PR #29 chain runner 로
python3 .../examples/run_inventory_batch_smoke.py \
    --inventory /tmp/inv.json \
    --pdf-dir /mnt/wisereport/2026-04-30/기업 \
    --workdir /tmp/chain --max-pdfs 50 \
    --manual-meta /tmp/manual_meta.json \
    --ticker-map .../resources/ticker_map.csv \
    --chain-bridge --chain-merge --chain-build

# 3. (옵션) PR #38 emit 으로 운영 산출물
python3 .../scripts/emit_revision_trend.py \
    --accepted-rows /tmp/chain/build_output/2026-04-30/estimate_revision_rows.json \
    --structured /tmp/chain/structured_extraction.json \
    --output-dir /tmp/chain/emit \
    --date 2026-04-30 --apply
```

산업 entries 는 별도 LLM-summary 워크플로우가 처리하며, 본 패키지의 범위
밖이다.

## Self-test

```
python3 stock_research/phase3_report_pipeline/examples/run_wisereport_inventory_fixture.py
```

5 scenarios (happy_path / malformed / non_pdf / cap_test / empty_industry)
+ 4 guards (HARDMAX violation / repo-out + apply / dry-run no-write /
no-include) — PASS 시에만 exit 0.
