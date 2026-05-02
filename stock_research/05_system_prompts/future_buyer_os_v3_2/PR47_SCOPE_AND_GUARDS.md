# PR #47 — Scope and Guards

이 문서는 PR #47 의 **변경 가능 범위(scope)** 와 **금지(guards)** 를 명시합니다.

## 1. PR 개요

- 제목: `chore(pbkr): add Future Buyer Momentum OS prompts and schemas`
- 분기: PR #46 merge 이후의 최신 `main` 에서 분기.
- 성격: **additive-only**. 기존 파일 수정/삭제/이동 없음.
- 매매 신호: **생성하지 않음**.

## 2. 추가 범위 (allowed)

다음 디렉토리에만 파일을 추가합니다.

```
stock_research/05_system_prompts/future_buyer_os_v3_2/
├── README.md
├── TEN_LAYER_PIPELINE.md
├── FUTURE_BUYER_THESIS.md
├── GOOGLE_DRIVE_LAYOUT_v3_2.md
├── DAILY_OPERATION_RUNBOOK.md
├── MOBILE_INBOX_RUNBOOK.md
├── PR47_SCOPE_AND_GUARDS.md          # (이 문서)
├── project_prompts/                  # 9개 system prompt
├── daily_prompts/                    # 10개 daily prompt
├── schemas/                          # 12개 JSON Schema
├── runbooks/                         # 추가 runbook
├── examples/                         # synthetic 예시 (실제 데이터 아님)
└── colab/                            # notebook skeleton (외부 호출 없음)
```

## 3. 금지 (forbidden in this PR)

| 항목 | 사유 |
|---|---|
| `parser/` 코드 수정 | 별도 PR. parser 변경은 phase3 fixture 회귀 위험. |
| `bridge/` `merge/` `build/` `emit/` 수정 | 동일. |
| `stock_research/phase3_report_pipeline/scripts/*` 수정 | 동일. |
| `ticker_map` 변경 | 데이터 정합성 위험, 별도 PR. |
| 실제 PDF 커밋 | 저작권/용량 위험. Drive 만 사용. |
| 추출 텍스트 커밋 | 동일. |
| 출력 JSON / CSV / parquet 커밋 | 모든 출력은 Drive 또는 사용자 로컬에. repo 비커밋. |
| API key / token / password / secret 저장 | 모든 비밀은 환경변수 / secret store. |
| Drive write/rename/delete 코드 추가 | 본 PR은 운영 정의만. |
| OCR / Vision / 외부 LLM API client 추가 | 동일. |
| `latest/` `promote/` `SuperPack/` 의 자동 이동 코드 추가 | 동일. |
| `rolling --apply` 추가 | 동일. |
| `direct_trade_signal=true` 출력 | 스키마가 `false` 만 허용. |
| `trade_signal` truthy 출력 | 스키마가 `null` 또는 `false` 만 허용. |
| `target_price` 를 primary signal 로 사용 | `secondary_reference` 로만 등장 허용. |
| 매수/매도 단정 표현 | "사라/팔라" 같은 명령형 출력 금지. |

## 4. 검증 체크리스트

- [x] `parser/bridge/merge/build/emit` 코드 미수정.
- [x] `ticker_map` 미수정.
- [x] 모든 추가 파일이 `stock_research/05_system_prompts/future_buyer_os_v3_2/` 하위.
- [x] 실제 PDF / 추출 텍스트 / 출력 JSON·CSV 미커밋.
- [x] API key/token/password 미커밋.
- [x] 모든 schema 의 `direct_trade_signal` 디폴트는 `false`, `const`로 강제.
- [x] 모든 schema 의 `trade_signal` 은 `null` 또는 `false` 만 허용.
- [x] `target_price` 는 `secondary_reference` 위치에만 등장.
- [x] Drive write/rename/delete 코드 없음.
- [x] OCR/Vision/외부 LLM client import 없음.

## 5. 다음 PR 후보 (out of scope here)

- 분류 자동화(Drive write).
- Colab ETL 의 실제 raw → ThemeRadar 자동 변환 코드.
- SuperPack 의 자동 emit / fixture 회귀 추가.
- `rolling --apply` 의 안전한 실행 경로.

위 항목은 **본 PR에 포함되지 않습니다.**
