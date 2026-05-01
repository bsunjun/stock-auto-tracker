# stock-auto-tracker

자동 주가 조회 및 포트폴리오 스냅샷 생성을 위한 Python CLI 프로젝트입니다.

## 현재 MVP 기능

- YAML 기반 관심종목/보유종목 입력
- `yfinance` 기반 현재가 조회
- 오프라인 CSV 가격 파일 기반 테스트 실행
- 평가금액, 평가손익, 손익률 계산
- 손절가/목표가까지의 거리 계산
- CSV/JSON 스냅샷 저장

## 빠른 시작

```bash
git clone https://github.com/bsunjun/stock-auto-tracker.git
cd stock-auto-tracker
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp config/watchlist.example.yaml config/watchlist.yaml
python -m stock_auto_tracker.cli snapshot --config config/watchlist.yaml
```

## 오프라인 구조 검증

네트워크 없이 샘플 가격 파일로 실행할 수 있습니다.

```bash
python -m stock_auto_tracker.cli snapshot \
  --config config/watchlist.example.yaml \
  --offline-prices tests/fixtures/prices_sample.csv
```

## 출력 파일

```text
output/snapshots/portfolio_snapshot_YYYYMMDD_HHMMSS.csv
output/snapshots/portfolio_snapshot_YYYYMMDD_HHMMSS.json
output/snapshots/latest.csv
output/snapshots/latest.json
```

## 확장 방향

- Kiwoom REST 가격 공급자
- pykrx 일봉/수급 공급자
- Telegram/Slack 알림
- GitHub Actions 또는 로컬 cron 자동 실행
- PB_READY / PB_SCOUT / PB_TRIGGER 판단 모듈 연결
