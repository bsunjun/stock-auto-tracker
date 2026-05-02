# Future Buyer Momentum OS v3.2

이 디렉토리는 PBKR(주식 리서치) 운영을 위한 **시스템 프롬프트, 스키마, 런북 모음**입니다.
실제 매매 신호(주문)를 만들지 않습니다. 의사결정의 마지막 단계는 항상 사람(human gate)에 둡니다.

## 0. 한 줄 정의

> **Future Buyer Momentum OS v3.2**는 "내가 산 다음에 누가 살 것인가(future buyer)"를
> 10개 레이어의 정보 흐름으로 구조화하고, 그 결과를 PB 상태(WATCH_ONLY ~ PB_TRIGGER)로 정리하는
> 운영 체계입니다.

## 1. 핵심 원칙

- `direct_trade_signal=false` 가 모든 산출물의 디폴트입니다. 이 디렉토리의 어떤 파일도 매매 주문을 발행하지 않습니다.
- `trade_signal` 필드는 `null` 또는 `false` 만 허용합니다. truthy 값은 스키마 위반입니다.
- 목표주가(`target_price`)는 **primary signal로 사용 금지**입니다. `secondary_reference`로만 등장할 수 있습니다.
- **Telegram-only** 단서로는 후보를 **PB_READY 이상으로 승격할 수 없습니다.**
  Telegram만 있는 후보는 `WATCH_ONLY` 또는 `THEME_DISCOVERY` 까지만 허용됩니다.
- 모든 후보는 **WiseReport / DART / Kiwoom / TradingView** 검증 순서를 통과해야 PB_SCOUT 이상으로 올라갈 수 있습니다.
- 모든 산출물에는 `edge_declared` 필드가 필수입니다. "왜 이 거래가 시장 평균보다 우위가 있다고 보는가"를 한 줄로 선언합니다.

## 2. 10-Layer Pipeline (요약)

| # | Layer | 의미 | 담당 프로젝트 |
|---|---|---|---|
| 1 | Macro / Politics / Technology Flow | 큰 돈의 방향 | `Gemini_PBKR_NewsGrounder_v3_2` |
| 2 | Newspaper / Major News | 개인 관심의 방향 | `Gemini_PBKR_NewsGrounder_v3_2` |
| 3 | Telegram / Paid Channels | 단기 돈과 테마 확산 방향 | `Telegram_ThemeRadar_v3_2` |
| 4 | WiseReport / Industry Report | 기관이 살 명분 | `Claude_ReportReader_v3_2` |
| 5 | DART / Company IR | 공식 숫자 확인 | `Claude_ReportReader_v3_2` |
| 6 | Kiwoom Flow | 실제 매수 주체 확인 | `ChartSupplyReader_v3_2` |
| 7 | TradingView Chart | 언제 살지 확인 | `ChartSupplyReader_v3_2` |
| 8 | Official Risk Flags | 사면 안 되는 것 제거 | `Claude_PBKR_Auditor_v3_2` |
| 9 | Future Buyer Thesis | 나 다음에 누가 살지 판단 | `ChatGPT_PBKR_Orchestrator_v3_2` |
| 10 | PB State | `WATCH_ONLY` / `PB_READY` / `PB_SCOUT` / `PB_TRIGGER` | `ChatGPT_PBKR_Orchestrator_v3_2` |

상세는 [`TEN_LAYER_PIPELINE.md`](./TEN_LAYER_PIPELINE.md) 참고.

## 3. 디렉토리 구성

```
future_buyer_os_v3_2/
├── README.md                          # (이 문서)
├── TEN_LAYER_PIPELINE.md              # 10-layer 입출력 정의
├── FUTURE_BUYER_THESIS.md             # "다음 매수자" 데이터 구조
├── GOOGLE_DRIVE_LAYOUT_v3_2.md        # GEMsPBKR_INTERNAL Drive 표준 폴더
├── DAILY_OPERATION_RUNBOOK.md         # 일일 운영 절차
├── MOBILE_INBOX_RUNBOOK.md            # 00_INBOX_MOBILE 운영
├── PR47_SCOPE_AND_GUARDS.md           # 본 PR의 가드
├── project_prompts/                   # 각 AI 프로젝트의 system prompt
├── daily_prompts/                     # 일일 운영 프롬프트
├── schemas/                           # JSON Schema (12종)
├── runbooks/                          # 추가 운영 런북
├── examples/                          # 스키마 예시 (synthetic only)
└── colab/                             # Colab notebook skeleton
```

## 4. 본 PR 스코프

- 이 PR(#47)은 **additive-only** 입니다.
- `parser/bridge/merge/build/emit` 엔진 코드를 수정하지 않습니다.
- ticker_map 을 수정하지 않습니다.
- 실제 PDF / 추출 텍스트 / 산출 JSON·CSV / API 키 / 토큰 / 비밀번호를 커밋하지 않습니다.
- `latest/` `promote/` `SuperPack/` `rolling --apply` 동작을 추가하지 않습니다.
- Drive write/rename/delete 코드를 추가하지 않습니다.
- OCR/Vision/LLM API 클라이언트를 추가하지 않습니다.

본 PR이 보장하는 것은 **운영 체계의 기록**이며, 실행 가능한 매매 자동화의 추가는 별도 PR로 분리합니다.

## 5. 인접 자산

- 기존 prompts: `stock_research/prompts/PBKR-*.md` (legacy v1, 유지)
- 기존 schemas: `stock_research/schemas/*.schema.json` (legacy v1, 유지)
- phase3 파이프라인: `stock_research/phase3_report_pipeline/` (수정 금지)

이 디렉토리(`05_system_prompts/future_buyer_os_v3_2/`)는 위 legacy 자산을 **수정하지 않고 옆에 새로 추가**된 v3.2 운영 정의입니다.
