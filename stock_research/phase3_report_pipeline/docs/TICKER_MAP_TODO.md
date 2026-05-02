# Ticker map TODO list (PR #21+)

Purpose
-------
Companies that the WiseReport pipeline **frequently encounters** but for
which a confirmed `KRX:NNNNNN` code is NOT yet in
`stock_research/phase3_report_pipeline/resources/ticker_map.csv`. This
file is the single place to track entries deferred for verification —
the resolver itself never guesses a ticker from a Korean name.

Governance
----------
- **Listed entities only.** IPO candidates, pre-listing companies, ATS-only
  vehicles, and de-listed entities are NOT eligible.
- **Codes only when you can cite the source.** When in doubt, leave it
  here and someone will look it up against KRX/DART.
- This file is **NOT** a trading signal. Phase 3 keeps
  `direct_trade_signal=false` everywhere; the ticker map exists only to
  translate Korean names from broker PDFs into `KRX:NNNNNN` for the
  strict gate.
- Do NOT add codes you found by typing into a search engine without
  cross-checking against the official KRX listing or DART corp registry.

Process for adding an entry to `resources/ticker_map.csv`
---------------------------------------------------------
1. Confirm the code on at least ONE primary source: KRX listing portal
   (`kind.krx.co.kr`) OR DART (`dart.fss.or.kr`).
2. Note the market exactly as KRX records it (KOSPI / KOSDAQ / KONEX).
3. Add aliases ONLY for genuine alternate names: a documented rename,
   the well-known English form, or a common abbreviation. Do NOT use
   preferred-share names as aliases (those carry distinct codes).
4. Run the verifier:
   ```
   python3 stock_research/phase3_report_pipeline/scripts/ticker_resolver.py \
       --verify \
       --ticker-map stock_research/phase3_report_pipeline/resources/ticker_map.csv
   ```
   `validation: PASS` is required. Any duplicate / collision is a
   blocking failure.
5. Run the resolver fixture:
   ```
   python3 stock_research/phase3_report_pipeline/examples/run_ticker_resolver_fixture.py
   ```

Explicitly EXCLUDED (do not add)
--------------------------------
- 마키나락스 — pre-IPO; planning a public listing but not yet registered.
- 대한조선 — privately held shipbuilder; not listed on any exchange.
- 케이뱅크 — IPO has been deferred multiple times; not yet listed.
- 켄벨인터내셔널 / 토스플레이스 / 비바리퍼블리카 — pre-IPO / private.
- 샘플전자 / SAMPLECO — synthetic placeholder used in PR #12+ test
  fixtures; intentionally never resolves.

Pending verification (NOT added)
--------------------------------
The list below is provisional. Each entry needs a primary-source
confirmation before it can land in `resources/ticker_map.csv`. Add the
KRX code in the "code" column once verified.

| company_name_kr | proposed code | market | notes |
| --- | --- | --- | --- |
| 한화비전 | KRX:013570 (?) | KOSPI | Surfaced in 2026-04-30 search results; code not independently confirmed at PR #25 merge time. |
| 저스템 | (?) | KOSDAQ | Recent IPO; KRX code requires confirmation against KIND. |

Recently added (PR #32 — 3rd expansion)
---------------------------------------
- `LX인터내셔널 → KRX:001120` (KOSPI) — surfaced as `ticker_unresolved` ×2
  in the PR #31 20-PDF official `--pdf-dir` runner smoke. Code unchanged
  from the pre-rename 'LG상사'; aliases added: `LG상사`, `엘지상사`,
  `LX International`.
- `LG이노텍 → KRX:011070` (KOSPI) — surfaced as `ticker_unresolved` ×1
  in the same smoke. Aliases added: `엘지이노텍`, `LG INNOTEK`,
  `LG Innotek`.

Recently added (PR #35 — 4th expansion)
---------------------------------------
Surfaced as `ticker_unresolved` in the PR #34 100-PDF wider smoke
(50 + 50 chunks; HARD_MAX_PDFS=50 preserved). Each row added below
reflects a KRX-listed canonical name with the code re-confirmed
against KRX listing portal / DART corp registry; legacy renames are
recorded as aliases so historical filings still resolve.

| company_name_kr | ticker | market | aliases / notes |
| --- | --- | --- | --- |
| `현대건설` | `KRX:000720` | KOSPI | `Hyundai E&C`, `Hyundai Engineering & Construction` |
| `대우건설` | `KRX:047040` | KOSPI | `Daewoo E&C`, `Daewoo Engineering & Construction` |
| `한화솔루션` | `KRX:009830` | KOSPI | `한화케미칼`, `Hanwha Solutions`, `Hanwha Chemical` (renamed 2020) |
| `한국타이어앤테크놀로지` | `KRX:161390` | KOSPI | `한국타이어`, `Hankook Tire`, `Hankook Tire & Technology` (renamed 2019; holdco is `한국앤컴퍼니 KRX:000240`) |
| `롯데정밀화학` | `KRX:004000` | KOSPI | `삼성정밀화학`, `Lotte Fine Chemical` (renamed 2016) |
| `롯데렌탈` | `KRX:089860` | KOSPI | `Lotte Rental` (2021 IPO) |
| `롯데하이마트` | `KRX:071840` | KOSPI | `Lotte Himart` |
| `제일기획` | `KRX:030000` | KOSPI | `Cheil Worldwide` |
| `넥센타이어` | `KRX:002350` | KOSPI | `Nexen Tire` |
| `금호타이어` | `KRX:073240` | KOSPI | `Kumho Tire` |
| `대한전선` | `KRX:001440` | KOSPI | `Taihan Cable & Solution` |
| `인텔리안테크` | `KRX:189300` | KOSDAQ | `Intellian Technologies` |
| `HK이노엔` | `KRX:195940` | KOSDAQ | `HK inno.N` (2021 IPO) |
| `KG모빌리티` | `KRX:003620` | KOSPI | `쌍용자동차`, `Ssangyong Motor`, `KG Mobility` (renamed 2023) |
| `iM금융지주` | `KRX:139130` | KOSPI | `DGB금융지주`, `DGB Financial Group`, `iM Financial` (renamed 2024) |

Pending verification (NOT added by PR #35)
------------------------------------------
The following surfaced in the PR #34 100-PDF smoke but their codes
were not added in PR #35 either because the canonical company is a
recent rename / split / new listing, or because the code could not be
confirmed against an authoritative source at PR #35 merge time. Each
should be re-verified against KIND/DART before any future addition.

| company_name_kr | proposed code | market | notes |
| --- | --- | --- | --- |
| 한화비전 | KRX:013570 (?) | KOSPI | Surfaced in 2026-04-30 search results; Hanwha Group surveillance carve-out. Code requires re-confirmation; KRX:013570 belongs to a different issuer (디와이파워) per PR #25 review. |
| 저스템 | (?) | KOSDAQ | Recent IPO; KRX code requires confirmation against KIND. |
| LIG디펜스앤에어로스페이스 | (?) | KOSPI (?) | Newer name surfaced in 2026-04-30 cohort; possible recent spinoff/rename. Not yet confirmed against KIND. |
| RFHIC | (?) | KOSDAQ | Surfaced ×2 in PR #34 cohort. KOSDAQ-listed semiconductor RF company; code not yet confirmed at PR #35 merge time. |
| RF머트리얼즈 | (?) | KOSDAQ | Surfaced ×2 in PR #34 cohort. Code not yet confirmed. |
| 샘씨엔에스 | (?) | KOSDAQ (?) | Surfaced ×1; code not yet confirmed. |
| 세나테크놀로지 | (?) | KOSDAQ (?) | Surfaced ×1; code not yet confirmed. |
| 에치에프알 (HFR) | KRX:230240 (?) | KOSDAQ | Surfaced ×1; KOSDAQ-listed networking equipment company. Code requires KIND confirmation before adding. |
| 환인제약 | KRX:016580 (?) | KOSPI/KOSDAQ (?) | Surfaced ×1; both code and exact market need re-verification before adding. |

Add to this table whenever you encounter a Korean company name in a
WiseReport PDF that the resolver returns `None` for AND the company
appears to be listed but you cannot cite the code immediately. The
companion bridge `missing_fields=['ticker_unmapped']` already records
these at runtime; this file is the human-curated complement.

Resolved in PR #25 (added to ticker_map.csv after primary-source check)
----------------------------------------------------------------------
Captured here for audit; these no longer need TODO entries.

- 두산 KRX:000150 (KOSPI)
- 두산퓨얼셀 KRX:336260 (KOSPI; 2019 split from 두산)
- 두산테스나 KRX:131970 (KOSDAQ; renamed from 테스나 after 2022 acquisition)
- 하이브 KRX:352820 (KOSPI; 2020 IPO)
- 세아베스틸지주 KRX:001430 (KOSPI; renamed from 세아베스틸 in 2022 holdco restructure)
- HD현대에너지솔루션 KRX:322000 (KOSPI; renamed from 현대에너지솔루션)
- HL만도 KRX:204320 (KOSPI; renamed from 만도 in 2022 Halla restructure)
- 한미사이언스 KRX:008930 (KOSPI; Hanmi pharma holding)
- SK아이이테크놀로지 KRX:361610 (KOSPI; 2021 IPO)
- 대한유화 KRX:006650 (KOSPI)
- 에코프로 KRX:086520 (KOSDAQ; parent of 에코프로비엠)
- 에코프로비엠 KRX:247540 (KOSDAQ)
- 에이비엘바이오 KRX:298380 (KOSDAQ)
