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
