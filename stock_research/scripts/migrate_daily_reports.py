#!/usr/bin/env python3
"""
WiseReport 일일 PDF 원본을 stock_research 측 파싱/인덱스 영역으로 마이그레이션
'계획'하는 스크립트. PDF 자체는 repo에 복사하지 않는다.

Data flow:
    <wisereport-root>/<YYYY-MM-DD>/{기업|산업}/*.pdf      (원본, 외부 Drive)
        |
        v   (parse + index — 별도 파서가 수행)
    <stock-research-root>/06_wise_report/                (parsed/index/latest CSV)
    <stock-research-root>/03_daily_reports/<YYYY-MM-DD>/ (당일 분석 산출)

이 스크립트의 역할:
    1) 입력 디렉토리에서 PDF 파일 목록 발견
    2) 각각의 목표 산출 경로(매니페스트) 계획
    3) 기본 dry-run: 무엇이 처리될지 stdout과 manifest.json에 출력
    4) --apply: 산출 디렉토리(.keep/manifest.json)만 생성. PDF 복사·파싱은 별도 도구.

CLI 표준 인자(전제):
    --wisereport-root, --stock-research-root, --date, --category, --dry-run
환경변수 fallback: WISE_REPORT_ROOT, STOCK_RESEARCH_ROOT.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

CATEGORIES = ("기업", "산업")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wisereport-root", default=os.getenv("WISE_REPORT_ROOT"),
                   help="WiseReport PDF 루트. 예: '<Drive>/Chrome에서 저장됨/wisereport'")
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"),
                   help="stock_research 루트 (Drive 측). 예: '<Drive>/내 드라이브/stock_research'")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="대상 날짜 YYYY-MM-DD (기본: 오늘)")
    p.add_argument("--category", choices=("기업", "산업", "all"), default="all",
                   help="처리 카테고리 (기본: all)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(기본) 변경 없이 계획만 출력")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="실제 적용 (산출 디렉토리/manifest 생성)")
    return p.parse_args(argv)


def discover_pdfs(wisereport_root: Path, date: str, category: str) -> list[Path]:
    cats = CATEGORIES if category == "all" else (category,)
    found: list[Path] = []
    for cat in cats:
        d = wisereport_root / date / cat
        if not d.exists():
            print(f"[discover] missing: {d}", file=sys.stderr)
            continue
        for f in sorted(d.glob("*.pdf")):
            found.append(f)
    return found


def plan_targets(stock_research_root: Path, date: str, pdfs: list[Path]) -> dict:
    parsed_dir = stock_research_root / "06_wise_report" / "parsed" / date
    index_path = stock_research_root / "06_wise_report" / "index" / f"{date}.json"
    latest_csv = stock_research_root / "06_wise_report" / "latest.csv"
    daily_dir = stock_research_root / "03_daily_reports" / date

    items = []
    for pdf in pdfs:
        cat = pdf.parent.name
        stem = pdf.stem
        items.append({
            "source_pdf": str(pdf),
            "category": cat,
            "parsed_target": str(parsed_dir / cat / f"{stem}.parsed.json"),
            "index_entry_key": f"{date}/{cat}/{stem}",
        })
    return {
        "date": date,
        "parsed_dir": str(parsed_dir),
        "index_path": str(index_path),
        "latest_csv": str(latest_csv),
        "daily_dir": str(daily_dir),
        "items": items,
        "totals": {
            "by_category": {c: sum(1 for it in items if it["category"] == c) for c in CATEGORIES},
            "all": len(items),
        },
    }


def summarize(plan: dict, dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[{mode}] date={plan['date']}")
    print(f"[{mode}] discovered: {plan['totals']['all']} pdf(s) "
          f"(기업={plan['totals']['by_category'].get('기업', 0)}, "
          f"산업={plan['totals']['by_category'].get('산업', 0)})")
    print(f"[{mode}] parsed_dir = {plan['parsed_dir']}")
    print(f"[{mode}] index_path = {plan['index_path']}")
    print(f"[{mode}] latest_csv = {plan['latest_csv']}")
    print(f"[{mode}] daily_dir  = {plan['daily_dir']}")
    for it in plan["items"][:5]:
        print(f"  - {it['source_pdf']}  ->  {it['parsed_target']}")
    if len(plan["items"]) > 5:
        print(f"  ... (+{len(plan['items']) - 5} more)")


def apply_plan(plan: dict) -> None:
    """디렉토리와 manifest만 생성. PDF 복사/파싱은 하지 않는다."""
    parsed_dir = Path(plan["parsed_dir"])
    parsed_dir.mkdir(parents=True, exist_ok=True)
    (parsed_dir / ".keep").touch()
    Path(plan["daily_dir"]).mkdir(parents=True, exist_ok=True)
    (Path(plan["daily_dir"]) / ".keep").touch()
    manifest_path = parsed_dir / "manifest.json"
    manifest_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote manifest: {manifest_path}")


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if not args.wisereport_root or not args.stock_research_root:
        print("error: --wisereport-root and --stock-research-root are required "
              "(or set WISE_REPORT_ROOT / STOCK_RESEARCH_ROOT).", file=sys.stderr)
        return 2

    wr = Path(args.wisereport_root).expanduser()
    sr = Path(args.stock_research_root).expanduser()
    if not wr.exists():
        print(f"error: wisereport-root not found: {wr}", file=sys.stderr)
        return 2

    pdfs = discover_pdfs(wr, args.date, args.category)
    plan = plan_targets(sr, args.date, pdfs)
    summarize(plan, args.dry_run)

    if not args.dry_run:
        apply_plan(plan)
    else:
        print("[DRY-RUN] no changes written. Re-run with --apply to materialize directories+manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
