# PR #38 — Report Revision Trend Output

`build_report_estimate_v132 --strict --apply` 의 accepted rows
(`estimate_revision_rows.json`) 를 받아 두 가지 운영 산출물을 만든다:

1. **`REPORT_REVISION_TREND`** — accepted row 전체에 분류 라벨을 붙인 trend table.
2. **`REPORT_ESTIMATE_HIGH_TABLE_CANDIDATES`** — 위에서 `high_conviction` 으로
   분류된 row 만 추려낸 candidate table.

본 산출물은 모두 **dry-run default** 이며, repo 에 커밋되지 않는다. 실제
파일은 `--apply --output-dir <repo-외부>` 일 때만 생성된다. 다운스트림
`rolling_append.py` 를 호출하지 않는다 — 이 단계는 운영 review 용 read-only
artifact 일 뿐이다.

## CLI

```
python3 stock_research/phase3_report_pipeline/scripts/emit_revision_trend.py \
    --accepted-rows <path>/estimate_revision_rows.json \
    --structured    <path>/structured_extraction.json \
    --output-dir    <path-outside-repo> \
    --date          YYYY-MM-DD \
    [--apply]
```

| flag | 역할 |
| --- | --- |
| `--accepted-rows` | (required) `build_report_estimate_v132 --strict --apply` 의 `estimate_revision_rows.json` (list of accepted row dicts). |
| `--structured` | (optional) `extract_report_estimate_table.py` 의 `structured_extraction.json`. metric 룩업 (sha256 → metric) 만 사용한다. 누락 시 row 별 metric 은 `None` 으로 처리되고 분류는 `data_insufficient` 가 된다. |
| `--output-dir` | (required) 출력 루트. `<output-dir>/<date>/` 하위에 5개 파일 생성. repo 안 경로면 `--apply` 시 거부 (PR #29 가드와 같은 정책). |
| `--date` | (default = today) 날짜 서브디렉토리 이름 + 산출물의 `date` 컬럼. |
| `--apply` | 명시 시 파일 생성. 미명시 = dry-run. |

## 출력 파일

`--apply` 시 `<output-dir>/<date>/` 아래에:

| 파일 | 스키마 |
| --- | --- |
| `report_revision_trend.json` | `phase3:report_revision_trend:v1` (per-row) |
| `report_revision_trend.csv` | (header: date, ticker, broker, metric, old_target, new_target, delta_pct, direction, horizon, classification, is_target_price_only, source_key, source_pdf_sha256_short) |
| `report_estimate_high_table_candidates.json` | `phase3:report_estimate_high_table_candidates:v1` |
| `report_estimate_high_table_candidates.csv` | (header: date, ticker, broker, metric, old_target, new_target, delta_pct, direction, horizon, source_key, source_pdf_sha256_short) |
| `emit_revision_trend_summary.json` | `phase3:emit_revision_trend_summary:v1` |

각 row 는 `direct_trade_signal: false` 를 명시적으로 들고 다닌다. summary 도
`direct_trade_signal_all_false: true` 와 `forbidden_actions_confirmed` 블록을
포함한다.

## 분류 5종

| classification | 조건 | 설명 |
| --- | --- | --- |
| `high_conviction` | direction=up AND metric ∈ primary 4종 AND `|new-old|/|old|` ≥ 5% AND old_target ≠ 0 AND old/new finite | high_table 후보. primary metric 의 의미 있는 상향. |
| `margin_expansion` | (예약 버킷; v1 에서는 항상 0) | 향후 margin metric 이 primary 로 추가되면 사용. 스키마 안정을 위해 미리 자리 확보. |
| `marginal_review` | direction=flat, OR direction=up AND delta < 5%, OR direction=up AND old_target = 0 | 약한 신호. 추가 분석 후 판단. |
| `downside_guard_excluded` | direction=down | high_table 후보 영구 제외. trend table 에는 보존 (history 추적용). |
| `data_insufficient` | required field (ticker / broker / horizon / metric / old_target / new_target / direction) 누락 또는 invalid; metric=`target_price` 도 여기 (secondary reference 전용) | high_table 후보 영구 제외. |

primary metric (4종): `operating_profit`, `net_income`, `sales`, `eps`.
secondary reference (1종): `target_price` — `is_target_price_only=true` 로
표시되며, **절대 high_conviction 으로 분류되지 않는다.**

## Invariant 가드 (PR #38)

- **`direct_trade_signal` 영구 false**: 출력 row / summary 모두. 입력에 true 가
  하나라도 있으면 exit 3 으로 거부 (upstream `build --strict` 가 이미 강제하지만
  belt-and-braces).
- **target_price never primary**: `metric=target_price` 인 row 는
  `is_target_price_only=true` 로 표시되고 `data_insufficient` 로 분류된다.
  `report_estimate_high_table_candidates` 에 들어갈 가능성은 0.
- **direction=down never high_conviction**: `report_estimate_high_table_candidates`
  에 direction=down 이 들어갈 가능성은 0.
- **`--output-dir` repo 안 거부**: `--apply` 시 `--output-dir` 가 repo
  하위로 resolve 되면 exit 2.
- **dry-run default**: `--apply` 미명시 시 파일을 만들지 않는다. `rolling_append.py`
  를 호출하지 않는다. `--latest`, `--promote`, `--super-pack` 같은 플래그 자체가 없다.

## 분류 결정 트리 (의사코드)

```
if metric == "target_price":
    return "data_insufficient", is_target_price_only=True
required = (
    ticker is KRX:NNNNNN AND broker non-empty AND horizon non-empty AND
    metric in {operating_profit, net_income, sales, eps} AND
    direction in {up, down, flat} AND
    old_target finite AND new_target finite
)
if not required:
    return "data_insufficient"
delta_pct = |new - old| / |old|  if old != 0 else None
if direction == "down":
    return "downside_guard_excluded"
if direction == "flat":
    return "marginal_review"
# direction == "up"
if delta_pct is None:
    return "marginal_review"  # old_target == 0
if delta_pct < 0.05:
    return "marginal_review"
return "high_conviction"
```

## Self-test

```
python3 stock_research/phase3_report_pipeline/examples/run_emit_revision_trend_fixture.py
```

9-case fixture (`examples/emit_revision_trend_fixture/`) — 5/5 분류 + 모든
invariant cover. PASS 시에만 exit 0.

## What this script does NOT do

- 실제 매매·주문·체결 신호 생성
- `rolling_append.py` 호출 / `estimate_revision_history.csv` 갱신
- `latest` / `promote` / `Super Pack` 갱신
- `parser` / `bridge` / `merge` / `build` / `ticker_map` / `broker autodetect` 코드 수정
- `metric=target_price` 를 primary signal 로 격상
- direction=down 또는 missing 인 row 를 high_table 후보로 격상
