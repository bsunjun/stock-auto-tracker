# Colab Skeleton — v3.2

이 폴더에는 Google Colab notebook 의 **skeleton(설명서 + outline)** 만 포함합니다.
실제 Drive 파일 다운로드 / 원문 복사 / 민감정보 저장은 **하지 않습니다.**

## 목적

- Telegram / 뉴스 raw 텍스트의 정규화 보조 (ThemeRadar 초안 작성 보조).
- Layer 3 (`theme_radar_pack`) 의 부분 입력을 정리.

## 절대 금지

- OCR / Vision / 외부 LLM API client 추가 금지 (본 PR 범위).
- 사용자 ID / 비밀번호 / 세션 토큰 / 인증 쿠키 저장 금지.
- 실제 Drive 파일 raw 다운로드 → notebook 결과 첨부 금지.
- 메시지 raw 본문을 출력 셀에 그대로 남기지 않을 것.

## 산출

- ThemeRadar 초안 (`theme_radar_pack` 의 부분 채움).
- 정규화된 메타 인덱스 (KST 시각, 채널 ID, 메시지 ID 해시).

## 권장 흐름 (개념)

1. INBOX_MOBILE 의 `tg_*` 캡처 요약 텍스트를 사람이 Colab 에 붙여넣음 (수동 입력).
2. notebook 이 텍스트를 정규화 (시각/채널/테마 후보 추출).
3. 사람이 결과를 검토 후 ThemeRadar 초안으로 확정.
4. 사람이 초안을 PBKR Drive 의 03_theme_radar 폴더에 저장 (자동 저장 금지).

## skeleton 파일

- `theme_radar_starter.skeleton.ipynb` — outline 만. 외부 호출/민감정보 미포함.
