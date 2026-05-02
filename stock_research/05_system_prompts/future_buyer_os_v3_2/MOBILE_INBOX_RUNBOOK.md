# Mobile INBOX Runbook — `00_INBOX_MOBILE/`

> 모바일에서는 **단일 진입점** 만 사용합니다. 분류는 나중에 합니다.

## 1. 단일 진입점 원칙

- 모바일 운영자는 **`GEMsPBKR_INTERNAL/00_INBOX_MOBILE/`** 에만 파일을 투입합니다.
- 모바일에서 layer별 폴더(01~10)에 **직접 쓰지 않습니다.**
- 분류·정리는 MacBook + Claude Code 또는 Colab ETL 보조가 **나중에** 수행합니다.

## 2. 파일명 규칙

```
{YYYYMMDD}_{HHMM}_{source}_{ticker_or_theme}_{free-slug}.{ext}
```

- `YYYYMMDD_HHMM` — 캡처 시각 (KST). 모바일이 자동으로 채울 수 있으면 자동.
- `source` — 다음 중 하나:
  - `news` — 신문/포털 헤드라인
  - `tg` — Telegram 채널
  - `paid` — 유료 채널
  - `macro` — 거시/정책 캡처
  - `ir` — IR/공시 캡처
  - `chart` — TradingView 스크린샷
  - `flow` — 키움 매수주체 스냅샷
  - `misc` — 기타
- `ticker_or_theme` — 6자리 KRX 코드, 또는 테마 키, 없으면 `na`.
- `free-slug` — 짧은 영문/숫자, 공백 금지, 한글 사용 가능하지만 영문 권장.

## 3. 파일 형식

- 이미지: `.png`, `.jpg`
- 텍스트 캡처: `.txt`, `.md`
- 메모: `.md` 권장
- PDF는 모바일 INBOX 에 그대로 두지 않고, **MacBook 에서 사람이 검토** 후 layer 폴더로 이동.

## 4. 절대 금지

- API key, 토큰, 비밀번호 등을 모바일에서 INBOX에 투입하지 않는다.
- 사용자 ID/password 가 화면에 보이는 캡처를 INBOX에 투입하지 않는다.
- 매매 주문 화면 캡처를 INBOX에 투입하지 않는다.
- 모바일에서 **legacy `stock_research/` 폴더 또는 분류 폴더(01~10)** 에 쓰지 않는다.

## 5. INBOX 비우기 (Drainer) — 사람 작업

- MacBook 에서 운영자가 INBOX 파일을 검토 후 적절한 layer 폴더로 이동.
- 자동화는 **분류 제안만** 가능하고, 실제 이동은 **사람** 이 수행 (이 PR 범위에서는 자동 이동 코드를 추가하지 않는다).

## 6. INBOX 보관 기간

- 운영 가이드: 7일 이내에 분류 완료가 권장. 7일 초과 항목은 운영자가 수동 정리.
- 30일 초과 INBOX 잔여물은 `90_archive/INBOX_aged/` 로 사람이 이동.
