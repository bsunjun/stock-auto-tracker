# stock_research/

이 디렉토리는 **GitHub repo 측의 코드/스키마/프롬프트 저장소**입니다.
실제 리서치 데이터(원본)는 **Google Drive `stock_research/`** 에 위치합니다.

## 역할 분리

| 위치 | 담당 |
| --- | --- |
| GitHub repo (`stock_research/` — 여기) | 자동화 코드, 스키마, 프롬프트, 마이그레이션 스크립트, 운영 문서 |
| Google Drive (`stock_research/`) | 종목별 리서치 노트, 수집 데이터, 산출물 (원본) |

→ Drive의 데이터를 repo로 복제하지 않습니다. 데이터 파일(csv, parquet, xlsx 등)은 PR/커밋에 포함시키지 마십시오.

## 하위 디렉토리

- `scripts/` — 데이터 수집/변환/마이그레이션 파이썬 스크립트
- `schemas/` — JSON Schema, Pydantic 모델 등 데이터 스키마 정의
- `prompts/` — LLM 프롬프트 템플릿 (자동 요약/분석)
- `workflows/` — 작업 흐름 정의 (`.github/workflows/`와 연동되는 보조 yaml/사양)
- `templates/` — 종목 리서치 노트 마크다운 등 템플릿
- `docs/` — 운영 가이드, repo↔Drive 동기화 정책 문서

## 참고

- 자동 가격 수집기: 루트의 `serpapi_automator.py` (현재는 `current_prices.json/csv`를 repo 루트에 저장)
- 스케줄: `.github/workflows/serp_run.yml` (매일 09:00 KST)
