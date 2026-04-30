# pipeline_runner_fixture

PR #9 의 `run_estimate_revision_dryrun.py` 가 단일 명령으로 묶는
다음 3단계 파이프라인을 검증하기 위한 synthetic 입력.

```
merge_meta.py
  └─> build_report_estimate_v132.py --strict
        └─> rolling_append.py --strict-estimate (dry-run only)
```

## Files

| File | 역할 |
| --- | --- |
| `bridge_meta.json` | bridge 산출물 흉내 (3 records) |
| `structured_extraction.json` | structured extraction 산출물 흉내 (1 partial) |
| `rolling_extra_rows.json` | rolling-step 검증을 위한 hostile rows (`direct_trade_signal=true`, `direction=unknown`). 정상 파이프라인에서는 발생하지 않지만, 잘못된 입력이 들어와도 rolling validator 가 막아내는지 확인하기 위한 negative test row. |
| `expected_pipeline_summary.json` | runner 가 만들 `pipeline_summary.json` 의 reference shape + 본 fixture 에 대한 기대 카운트 |

## Records & Expected Behavior

| sha256 prefix | 역할 | merge 후 | build --strict | rolling --strict-estimate (dry-run) |
| --- | --- | --- | --- | --- |
| `29220cc9…` (KRX:402340 SK스퀘어) | 정상 manual record | complete=true | accepted | **duplicate skip** (runner 가 이 row 의 dedupe key 를 미리 시드) |
| `e6d8596c…` (KRX:028260 삼성물산) | filename-only + partial extraction | complete=false (old_target 여전히 없음) | rejected | (build 단계에서 이미 제외) |
| `aaaaaaaa…` (KRX:058470 리노공업) | 정상 manual record | complete=true | accepted | **to_add=1** (시드 CSV 에 없음) |

추가 (`rolling_extra_rows.json` 에서 합류):

| ticker | 의도 | rolling validator 결과 |
| --- | --- | --- |
| KRX:005930 (삼성증권) | `direct_trade_signal=true` 가 새어나왔다고 가정 | reject `direct_trade_signal_not_false` |
| KRX:000660 (메리츠증권) | `direction=unknown` 이 새어나왔다고 가정 | reject `direction_invalid` |

## Expected Numeric Outcome

```
rows_in                       = 3
rows_accepted                 = 2     # build accepted
rows_rejected                 = 1     # build rejected (KRX:028260)
direct_trade_signal_all_false = true
rolling_validated             = 2     # the two build-accepted rows pass rolling validator
rolling_rejected              = 2     # KRX:005930, KRX:000660 from rolling_extra_rows.json
rolling_duplicate_skip        = 1     # KRX:402340 matches the seed row
rolling_to_add                = 1     # KRX:058470
```

## Hard Constraints

- 본 fixture 사용은 OCR/Vision/API/Drive/promote 호출을 발생시키지 않는다.
- runner 는 repo `templates/*.csv` 를 절대 수정하지 않는다.
  rolling step 은 `<workdir>/seeded_estimate_history.csv` (templates 헤더 + 1 dup row)
  에 대한 dry-run 으로 수행된다.
- runner 의 `--apply` 는 의도적으로 거부된다 (PR #9 는 dry-run 연결 검증 PR).
