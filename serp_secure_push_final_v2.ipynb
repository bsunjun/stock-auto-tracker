#!/usr/bin/env python
"""
SerpApi 자동 주가·뉴스 수집 → JSON/CSV 저장 → GitHub 푸시 스크립트
-------------------------------------------------------------------
• Google Colab 로컬 실행 : `!python serpapi_automator.py`
• GitHub Actions 자동화  : SERPAPI_KEY · GH_TOKEN 시크릿만 등록하면 주기적으로 실행

작성 원칙
────────
1. API 키 노출 금지  → 환경변수 SERPAPI_KEY 사용
2. 엔진 단일 호출     → google_finance / google_news 별도 요청
3. 실패 견고성       → 예외 캐치 후 "error" 필드로 로그
4. 출력 포맷         → JSON (dict) + CSV (table) 동시 생성
5. Git 푸시          → OCO 같은 자동 발주 용도로 다운스트림에서 사용
"""
from __future__ import annotations

import os
import json
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

import requests

###############################################################################
# 1. 환경변수 · 상수 설정
###############################################################################
SERP_API_KEY: str | None = os.getenv("SERPAPI_KEY")
GH_TOKEN: str | None = os.getenv("GH_TOKEN")  # Actions 환경에서만 필요

if not SERP_API_KEY:
    raise RuntimeError("⚠️ SERPAPI_KEY 환경변수가 설정돼 있지 않습니다.")

# Git 정보 
GITHUB_USERNAME = "bsunjun"
GITHUB_EMAIL    = "bsunjun@gmail.com"
GITHUB_REPO     = "stock-auto-tracker"
REPO_DIR        = Path(f"./{GITHUB_REPO}")
FILE_JSON       = "current_prices.json"
FILE_CSV        = "current_prices.csv"
JSON_PATH       = REPO_DIR / FILE_JSON
CSV_PATH        = REPO_DIR / FILE_CSV

# 포트폴리오 (티커 → SerpApi 쿼리)
PORTFOLIO: dict[str, str] = {
    "리노공업": "KRX:058470",
    "에스티팜": "KRX:237690",
    "에이피알": "KRX:278470",
    "ENF테크": "KRX:102710",
    "알테오젠": "KRX:196170",
    "현대로템": "KRX:064350",
    "세아베스틸지주": "KRX:001430",
    "YG PLUS": "KRX:037270",
}

###############################################################################
# 2. SerpApi 호출 유틸리티
###############################################################################

def _serp_search(engine: str, query: str) -> dict:
    """SerpApi 검색 호출(단일 엔진)."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": engine,
        "q": query,
        "api_key": SERP_API_KEY,
        "hl": "ko",
        "gl": "kr",
        "no_cache": "true",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_price(ticker: str) -> dict:
    """구글파이낸스 실시간 주가·등락률."""
    data = _serp_search("google_finance", ticker)
    summary = data.get("summary", {})
    return {
        "price": summary.get("price"),
        "change": summary.get("price_movement", {}).get("percentage"),
    }


def fetch_news(keyword: str, n: int = 3) -> List[dict]:
    """최신 뉴스 n건 헤드라인."""
    data = _serp_search("google_news", keyword)
    articles = data.get("news_results", [])[:n]
    return [
        {"title": a.get("title"), "link": a.get("link"), "snippet": a.get("snippet")}
        for a in articles
    ]

###############################################################################
# 3. 데이터 수집
###############################################################################

def collect_portfolio() -> List[dict]:
    rows: List[dict] = []
    for name, ticker in PORTFOLIO.items():
        try:
            price_info = fetch_price(ticker)
            row = {
                "name": name,
                "ticker": ticker,
                "price": price_info["price"],
                "change": price_info["change"],
                "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
            }
        except Exception as e:
            row = {
                "name": name,
                "ticker": ticker,
                "price": None,
                "change": None,
                "error": str(e),
            }
        rows.append(row)
    return rows

###############################################################################
# 4. 저장 (json / csv)
###############################################################################

def save_outputs(rows: List[dict]):
    REPO_DIR.mkdir(exist_ok=True, parents=True)
    # JSON
    with JSON_PATH.open("w", encoding="utf-8") as jf:
        json.dump({r["name"]: r for r in rows}, jf, ensure_ascii=False, indent=2)
    # CSV
    with CSV_PATH.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("✅ 저장 완료 (JSON + CSV)")

###############################################################################
# 5. GitHub 푸시(옵션)
###############################################################################

def push_to_github():
    """GH_TOKEN 존재 시 자동 커밋 + 푸시."""
    if not GH_TOKEN:
        print("ℹ️ GH_TOKEN 없음 → 푸시 스킵")
        return
    import subprocess
    subprocess.run(["git", "config", "--global", "user.email", GITHUB_EMAIL], check=True)
    subprocess.run(["git", "config", "--global", "user.name", GITHUB_USERNAME], check=True)
    # origin 원격 URL (토큰 인증)
    origin = f"https://{GITHUB_USERNAME}:{GH_TOKEN}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO}.git"
    if not (REPO_DIR / ".git").exists():
        subprocess.run(["git", "clone", origin, str(REPO_DIR)], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "add", FILE_JSON, FILE_CSV], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", f"🗓️ update prices {datetime.now().date()}"], check=False)
    subprocess.run(["git", "-C", str(REPO_DIR), "push", "origin", "main"], check=True)
    print("🚀 GitHub 푸시 완료")

###############################################################################
# 6. Main routine
###############################################################################

def main():
    rows = collect_portfolio()
    save_outputs(rows)
    push_to_github()
    # 뉴스 샘플 로그 (삼성전자)
    news = fetch_news("삼성전자")
    for article in news:
        print("📰", article["title"])


if __name__ == "__main__":
    main()
