# Google Drive Layout v3.2 — `GEMsPBKR_INTERNAL`

이 문서는 **운영용 Google Drive** 의 표준 폴더 레이아웃을 정의합니다.
실제 데이터는 Drive에 있고, 이 repo에는 **그 구조의 정의**만 담깁니다.

> **원칙: 기존 폴더는 이동/삭제/rename 하지 않습니다.** v3.2 는 기존 위에 **추가**만 합니다.

## 1. 최상위 폴더 구조

```
GEMsPBKR_INTERNAL/
├── 00_INBOX_MOBILE/                  # 모바일 단일 진입점 (raw drop)
├── 01_macro_politics_tech_flow/      # Layer 1
├── 02_attention_flow/                # Layer 2
├── 03_theme_radar/                   # Layer 3 (Telegram 요약 산출만)
├── 04_institutional_justification/   # Layer 4 (WiseReport / Industry)
├── 05_official_evidence/             # Layer 5 (DART / IR)
├── 06_actual_buyer_confirmation/     # Layer 6 (Kiwoom)
├── 07_chart_timing/                  # Layer 7 (TradingView)
├── 08_official_risk_flags/           # Layer 8
├── 09_future_buyer_thesis/           # Layer 9
├── 10_pb_state_decision/             # Layer 10
├── 11_super_pack/                    # SuperPack v3.2 (통합 산출)
├── 90_archive/                       # 기간이 지난 산출 보관
└── stock_research/                   # legacy v1 (READ-ONLY)
```

## 2. legacy `stock_research/` 의 처리

- 기존 `stock_research/` Drive 폴더는 **읽기 전용**(human-only read) 입니다.
- v3.2 자동화는 legacy 폴더에 **쓰기/이동/삭제** 를 하지 않습니다.
- 마이그레이션은 별도의 사람 검토 PR로만 진행합니다 (이 PR 범위 밖).

## 3. `00_INBOX_MOBILE/` 운영 방식

- 모바일에서는 **반드시 `00_INBOX_MOBILE/` 한 곳에만** 파일을 투입합니다.
- 모바일이 직접 분류 폴더에 쓰지 않습니다.
- 분류는 **MacBook + Claude Code** 또는 **Colab ETL 보조** 가 나중에 수행합니다.
- 파일명 규칙은 [`MOBILE_INBOX_RUNBOOK.md`](./MOBILE_INBOX_RUNBOOK.md) 참고.

## 4. 폴더별 파일 명명 규칙(요약)

```
{YYYYMMDD}_{layer-tag}_{ticker_or_theme}_{free-slug}.{ext}
```

- `YYYYMMDD` — 작성/스냅샷 날짜 (KST 기준).
- `layer-tag` — `L1` ~ `L10` 또는 `INBOX`, `SUPER`.
- `ticker_or_theme` — KRX 6자리 종목코드 또는 테마 키 (없으면 `na`).
- `free-slug` — 운영자가 식별 가능한 짧은 영문/숫자.

## 5. 금지 사항 (Drive 측에서도 적용)

- **자동화가 legacy `stock_research/` 폴더에 쓰지 않을 것.**
- **자동화가 폴더를 rename/move/delete 하지 않을 것.**
- **API key / token / 사용자 비밀번호를 Drive 에 저장하지 않을 것.**
- **실제 PDF의 raw text 를 repo 로 복제하지 않을 것** (Drive 안에서만 처리).
