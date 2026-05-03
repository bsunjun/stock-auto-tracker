# 일간 운영 런북 (KST)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 본 문서가 하는 일

본 런북은 PR #52에서 추가된 prompt / template / schema 들을 **시각대별로
어떤 순서로** 사용하는지 한국 시장 (KST) 기준으로 정리한다. 본 런북은
실행 권한을 부여하지 않으며, 모든 거래는 인간 게이트가 통과한 후 인간
운영자가 결정한다.

---

## 1. 시각대별 흐름 (KST)

| 구간 | 시간 | 용도 | 사용 산출물 |
|---|---|---|---|
| 장전 | 08:00–08:50 | pre-open 플래닝 | `../daily_prompts/01_pre_open_planner_ko.md` |
| 시초 발견 | 09:00–09:15 | 관찰만, 신규 실행 금지 | `../daily_prompts/02_opening_discovery_ko.md` |
| 본장 | 09:15–11:30 | S.N.I.P.E. 체크 | `../daily_prompts/03_primary_window_snipe_check_ko.md` |
| 점심대 | 11:30–13:30 | 거짓 신호대; near-yes 한정 | `../daily_prompts/03_primary_window_snipe_check_ko.md` §4 |
| 오후 | 13:30–15:10 | 본장 연장; 구조 청산 우선 | `../daily_prompts/03_primary_window_snipe_check_ko.md` §3, §4 |
| 종가대 | 15:10–15:30 | 신규 실행 금지; risk_stop / structural exit 만 | `../daily_prompts/03_primary_window_snipe_check_ko.md` §5 |
| 장후 | 15:30–17:00 | 저널 / 모델북 / 다음날 준비 | `../daily_prompts/04_close_review_ko.md` + `../daily_prompts/05_post_close_next_day_prep_ko.md` |
| 임시 | (이벤트 발생 시) | 공시 / 지정 / 자본 이벤트 점검 | `../daily_prompts/06_event_risk_recheck_ko.md` |

---

## 2. 08:00–08:50 — 장전 플래닝 (Pre-Open)

순서:
1. **시장 레짐 (Market Cycle).** `../schemas/market_cycle.schema.json`
   형식의 한 줄 요약을 작성. **레짐은 노출 다이얼이며, 매매 신호가
   아니다.**
2. **News Grounding 요청 → Gemini.** Gemini에게
   `news_grounding_pack` 요청
   (`../ai_project_instructions/PBKR_V4_NEWS_GROUNDER_INSTRUCTIONS.md`).
3. **후보 → GPT Orchestrator.** Watchlist + news pack + market cycle
   + TOR state 입력으로 `daily_focus_list` 초안 요청
   (`../ai_project_instructions/PBKR_V4_ORCHESTRATOR_INSTRUCTIONS.md`).
4. **Audit → Claude.** 초안 focus list를 Claude에게 audit 요청
   (`../ai_project_instructions/PBKR_V4_AUDITOR_INSTRUCTIONS.md`).
5. **Ticket fill.** audit `pass` 항목별로
   `../ticket_templates/trade_ticket_template.md` 작성, JSON 페이로드는
   `../ticket_templates/trade_ticket_template.json` 형식으로
   `../schemas/trade_ticket.schema.json` 검증.
6. **Snipe queue build.** TOR headroom 한도 안에서 1~5개로 압축.

체크 조건 (모두 만족해야 본장 진행):
- `entry_tactic` + `trigger_level` + `failure_level` + `stop_logic`
  명시되어 있는가?
- `stop_level` 사전 정의 + `stop_distance_pct` 산출되어 있는가?
- `total_open_risk_after ≤ K * tor_ceiling_pct` 인가?
- `sell_rules` 에 trim-into-strength 1개 이상, structural_exit 1개
  이상 명시되어 있는가?
- 4종 안전 플래그가 정확히 `false / null|false / false / true` 인가?

---

## 3. 09:00–09:15 — 시초 발견 (Opening Discovery)

- **관찰만**. 신규 실행 금지. 동시호가 인쇄는 가격 발견이지 확인이
  아니다.
- 사용 문서: `../daily_prompts/02_opening_discovery_ko.md`.
- 각 포커스 종목에 한 줄 노트 (`observe` / `demote` / `maintain`).
- 보유 종목의 시초 stop level 위반 여부는 `stop_evaluation_basis` 가
  `intraday_hard` 인 경우에만 즉시 처리. `closing` 인 경우에는 종가까지
  대기.

---

## 4. 09:15–11:30 — 본장 1부 (Primary Window)

각 snipe queue 종목에 대해 **S.N.I.P.E. 체크 (5개)**:

```
S — Setup confirmed?
N — Number / TOR ok?
I — Indicator alignment? (range / volume / close strength / macro non-contradiction)
P — Price at trigger?
E — Exit defined? (stop_logic / sell_rules / time_stop_window)
```

5/5 모두 `yes` → `../ai_project_instructions/PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`
체크리스트로 인계 → 게이트 `pass` → 인간 운영자가 `execute` 또는
`abstain` 결정.

5/5 미만 → 종목은 `watch` 또는 `demote`. 추격 금지. trigger_level /
failure_level 의 임의 조정은 `tactic_drift`.

보유 포지션 동시 모니터링: risk stop / structural exit / trim-into-strength /
trim-into-weakness / time stop 트리거. 발동 시
`../ticket_templates/position_management_ticket_template.md` 작성 후
인간 게이트 통과해야 처리.

---

## 5. 11:30–13:30 — 점심대 (Mid-Day)

- 거짓 신호대. 본장 1부에서 **near-yes** 였던 종목만 진입 가능.
- 본장 1부에서 stop-out 된 종목의 동일 pivot 재진입 금지.

---

## 6. 13:30–15:10 — 오후 (Afternoon)

- 본장 모니터링 연장.
- **구조 청산이 신규 진입보다 우선.**
- 종가 30분 전부터는 구조 / risk_stop 만, 신규 진입 금지.

---

## 7. 15:10–15:30 — 종가대 (Closing Window)

- **신규 실행 금지.**
- 종가 단일가 (`15:20`–`15:30`) 인쇄는 distribution / accumulation 관찰
  목적만.
- 종가 stop 침범 시 종가 기준 처리; 그 외는 다음 거래일 처리.

---

## 8. 15:30–17:00 — 장후 (Post-Close)

순서:
1. **장마감 리뷰.** `../daily_prompts/04_close_review_ko.md`. 보유 /
   stop migration / TOR / 후보 재분류.
2. **저널 작성.** 종가 stage / sub-grade / K / TOR_pct / 섹터 분포 /
   진입 / 청산 / 위반 / 교훈 — 비공개 저널, repo에 commit하지 않음.
3. **모델북 업데이트.** closed trade / missed trade 별
   `../modelbook_templates/modelbook_entry_template.md`.
4. **failure / best case 회고.** 해당 시
   `../modelbook_templates/failure_case_review_template.md` 또는
   `best_case_review_template.md`.
5. **다음날 준비.** `../daily_prompts/05_post_close_next_day_prep_ko.md`.
   잠정 daily focus list 1~5개 (이상적으로 1~3개).
6. **주중 마지막 거래일이면 주간 리뷰.**
   `../weekly_review/weekly_review_template.md` +
   `../weekly_review/weekly_review_prompt_ko.md`.

---

## 9. 임시 — 이벤트 리스크 재점검 (Event-Risk Recheck)

새 공시 / 뉴스가 발생했을 때 임의 시점에 실행:
- `../daily_prompts/06_event_risk_recheck_ko.md`.
- 영향받은 보유 / 후보의 분류 갱신 (`setup_invalidating` /
  `size_reducing` / `observation_only`).
- 인간 게이트 통과 후 인간 운영자가 결정.

---

## 10. 절대 금지

- 동시호가 (09:00–09:15 / 15:20–15:30) 안에서 신규 진입.
- 사이드카 / 서킷브레이커 발동 중 거래.
- 사전 정의되지 않은 stop으로 진입.
- `trigger_level` / `failure_level` 의 세션 중 임의 조정.
- 인간 게이트 우회.
- 단정적 매수 / 매도 표현.
- 안전 플래그 변경.
- 자동 실행 연결.

---

## 11. 운영 우선순위

1. 사람의 안전 (운영자의 인지 상태, 피로도) > 모든 신호.
2. 도덕성 (doctrine) > 즉흥성 (real-time intuition).
3. 프로세스 일관성 > 단일 거래 P&L.
4. 인간 게이트 무결성 > 속도.
