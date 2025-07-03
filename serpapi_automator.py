#!/usr/bin/env python
"""
SerpApi 자동 주가·뉴스 수집 → JSON/CSV 저장 → GitHub 푸시 스크립트
────────────────────────────────────────────────────────────
• **Colab 로컬 실행** : `!python serpapi_automator.py`
• **GitHub Actions**  : `SERPAPI_KEY` · `GH_TOKEN` 시크릿만 등록하면 주기적으로 실행

### 설계 원칙 v1.0.1
1. **API 키 노출 금지**   → 환경변수 `SERPAPI_KEY` 사용.
2. **엔진 단일 호출**     → `google_finance` / `google_news` 별도 요청.
3. **예외 견고성**        → 실패 시 `error` 필드에 기록, 스크립트 계속 실행.
4. **출력 포맷**         → JSON(dict) + CSV(table) 동시 생성.
5. **Git 푸시**          → `GH_TOKEN` 있으면 자동 커밋·푸시, 없으면 스킵.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

import requests

###############################################################################
# 1. 환경변수 · 상수 설정
###############################################################################
SERP_API_KEY: str | None = os.getenv("SERPAPI_KEY")
GH_TOKEN: str | None = os.getenv("GH_TOKEN")  # Actions 환경에서만 필요

if not SERP_API_KEY:
    raise RuntimeError("⚠️  SERPAPI_KEY 환경변수가 설정돼 있지 않습니다.")

# Git 기본 정보 — 필요 시 사용자 값으로 교체
GITHUB_USERNAME = "bsunjun"
GITHUB_EMAIL = "bsunjun@gmail.com"
GITHUB_REPO = "stock-auto-tracker"

# **현재 작업 디렉터리(=GitHub Actions에서 checkout 된 repo 루트)**
REPO_DIR = Path(".")
FILE_JSON = "current_prices.json"
FILE_CSV = "current_prices.csv"
JSON_PATH = REPO_DIR / FILE_JSON
CSV_PATH = REPO_DIR / FILE_CSV

# 포트폴리오 (티커 → SerpApi 쿼리)
PORTFOLIO: Dict[str, str] = {
    "리노공업": "KRX:058470",
    "에스티팜": "KRX:237690",
    "에이피알": "KRX:278470",
    "ENF테크": "KRX:102710",
    "알테오젠": "KRX:196170",
    "현대로템": "KRX:064350",
    "세아베스틸지주": "KRX:001430",
    "YG PLUS": "KRX:037270",
}

###############################################################################
# 2. SerpApi 호출 유틸리티
###############################################################################

def _serp_search(engine: str, query: str) -> dict:  # noqa: D401
    """엔진 단일 호출 wrapper."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": engine,
        "q": query,
        "api_key": SERP_API_KEY,
        "hl": "ko",
        "gl": "kr",
        "no_cache": "true",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_price(ticker: str) -> dict:
    data = _serp_search("google_finance", ticker)
    summary = data.get("summary", {})
    return {
        "price": summary.get("price"),
        "change_pct": summary.get("price_movement", {}).get("percentage"),
    }


def fetch_news(keyword: str, n: int = 3) -> List[dict]:
    data = _serp_search("google_news", keyword)
    articles = data.get("news_results", [])[:n]
    return [
        {"title": a.get("title"), "link": a.get("link"), "snippet": a.get("snippet")}
        for a in articles
    ]

###############################################################################
# 3. 데이터 수집
###############################################################################

def collect_portfolio() -> List[dict]:
    rows: List[dict] = []
    now_kst = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    for name, ticker in PORTFOLIO.items():
        try:
            price_info = fetch_price(ticker)
            row = {
                "name": name,
                "ticker": ticker,
                "price": price_info["price"],
                "change_pct": price_info["change_pct"],
                "timestamp": now_kst,
            }
        except Exception as exc:  # noqa: BLE001
            row = {
                "name": name,
                "ticker": ticker,
                "price": None,
                "change_pct": None,
                "error": str(exc),
                "timestamp": now_kst,
            }
        rows.append(row)
    return rows

###############################################################################
# 4. 저장 (JSON / CSV)
###############################################################################

def save_outputs(rows: List[dict]):
    # JSON
    with JSON_PATH.open("w", encoding="utf-8") as jf:
        json.dump({r["name"]: r for r in rows}, jf, ensure_ascii=False, indent=2)
    # CSV
    with CSV_PATH.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("✅  저장 완료 (JSON / CSV)")

###############################################################################
# 5. GitHub 푸시 (옵션)
###############################################################################

def push_to_github():
    if not GH_TOKEN:
        print("ℹ️  GH_TOKEN 없음 → 푸시 스킵")
        return
    # git config 이미 되어 있을 수 있음. — 실패 무시
    subprocess.run(["git", "config", "--global", "user.email", GITHUB_EMAIL], check=False)
    subprocess.run(["git", "config", "--global", "user.name", GITHUB_USERNAME], check=False)
    subprocess.run(["git", "add", FILE_JSON, FILE_CSV], check=True)
    commit_msg = f"🗓️  update prices {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=False)
        repo_https = f"https://x-access-token:{GH_TOKEN}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO}.git"
