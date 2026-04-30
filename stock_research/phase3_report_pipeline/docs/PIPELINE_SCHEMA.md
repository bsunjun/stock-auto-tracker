# Phase 3 — Pipeline Schema

데이터 흐름과 단계별 산출 형식.

## Flow

```
<PHASE3_REPORT_ROOT>/<date>/기업/*.pdf      (입력 - PDF 원본; repo 외부)
        |
        |  scripts/scan_wisereport_company.py  --apply
        v
<PHASE3_OUTPUT_ROOT>/<date>/scan_company.json  (read-only 인덱스)
        |
        |  사람/외부 파서가 manual partial meta JSON 작성
        |  (형식: examples/parsed_meta.example.json)
        v
manual_meta.json (broker/old/new/horizon 일부 또는 전부 포함)
        |
        |  scripts/bridge_scan_to_parsed_meta.py
        |    --scan-json <scan_company.json>
        |    --manual-meta <manual_meta.json>
        |    --ticker-map examples/ticker_map.example.csv
        v
parsed_meta.json (sha256/source_key/direction/missing_fields 자동 채움)
        |
        |  scripts/build_report_estimate_v132.py  --input parsed_meta.json --apply
        v
<PHASE3_OUTPUT_ROOT>/<date>/estimate_revision_rows.json
        |
        |  ../../../scripts/rolling_append.py  (PR #2 도구)
        v
<STOCK_RESEARCH_ROOT>/03_daily_reports/_rolling/estimate_revision_history.csv
        |
        |  scripts/promote_report_outputs.py --apply --confirm-promote   (사용자 직접 게이트)
        v
<PHASE3_OUTPUT_ROOT>/latest/...                (승격된 사본; 원본 보존)
```

## scan_company.json (per-record)

```json
{
  "path": "/abs/path/to/<date>/기업/sample.pdf",
  "filename": "sample.pdf",
  "sha256": "<64 hex>",
  "size_bytes": "12345",
  "mtime": "2026-04-30T10:00:00+00:00",
  "source_key": "phase3:scan_wisereport_company:v1"
}
```

규약:
- `sha256` 정규식: `^[0-9a-f]{64}$` (PR #2 `report_inventory.schema.json` 와 호환)
- `size_bytes`, `mtime` 은 문자열 (CSV 호환성)

## parsed_meta.json (외부 단계 입력)

```json
[
  {
    "ticker": "KRX:058470",
    "broker": "NH투자증권",
    "report_date": "2026-04-30",
    "old_target": 240000,
    "new_target": 260000,
    "horizon": "12M",
    "source_pdf_sha256": "<64 hex, optional>"
  }
]
```

## estimate_revision_rows.json (build_report_estimate_v132 산출)

`stock_research/templates/estimate_revision_history.csv` 헤더와 정확히 일치하는 컬럼 집합:

| 컬럼 | 의미 |
| --- | --- |
| `date` | report_date (YYYY-MM-DD) |
| `ticker` | KRX:NNNNNN |
| `broker` | 증권사 |
| `old_target` | 기존 목표가 (string) |
| `new_target` | 신규 목표가 (string) |
| `direction` | `up` / `down` / `flat` (자동 도출) |
| `horizon` | 투자 horizon (e.g., 12M) |
| `source_key` | `phase3:report_estimate:v1.3.2[+<sha256[:12]>]` |

## Source Key Convention

각 단계에서 누가 만들었는지를 추적하는 태그:

| 단계 | source_key |
| --- | --- |
| 스캔 | `phase3:scan_wisereport_company:v1` |
| Bridge | `phase3:bridge_scan_to_parsed_meta:v1` (parsed_meta record는 estimate builder의 source_key를 사용; 이는 bridge 모듈 식별용) |
| Estimate row 빌더 | `phase3:report_estimate:v1.3.2` (+`+<sha_short>` 부착 시 추적성 강화) |
| Vision OCR | (별도 키 없음 — 본문은 row 가 아닌 보조 산출) |
| Promote | `phase3:promote_report_outputs:v1` (감사 로그용; row 산출 없음) |

## 외부 데이터 위치

repo 외부의 실제 데이터 위치는 본 PR 범위가 아니다.
관련 정책은 `stock_research/docs/data_locations.md` (PR #2)를 참조하라.

## Repo / 외부 경계

| 항목 | repo | 외부 (Drive 등) |
| --- | --- | --- |
| 본 패키지 코드/스키마/문서 | O | X |
| `data_inbox/wisereport/<date>/기업/*.pdf` | X | O (default 상대경로는 로컬 작업 트리 외부 가정) |
| `output/<date>/*.json` | X | O |
| `output/latest/*` | X | O |
| `estimate_revision_history.csv` 데이터 | X | O |
