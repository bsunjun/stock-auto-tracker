#!/usr/bin/env python3
"""
Phase 3 — Monday Seed Pack builder.

Goal: produce the **minimum operating pack** ChatGPT will read before Monday's
open, given only the last N days (default 4) of:

  * `<wisereport-root>/<YYYY-MM-DD>/{기업|산업}/*.pdf`           (WiseReport raw)
  * `<telegram-root>/<YYYY-MM-DD>/<channel>/attachments/*`     (Telegram raw)

Behavioral contract (read first):

  * **No buy/sell signal is emitted.** Every row carries `signal_use=0` and
    `notes` explicitly says it is metadata-only. Telegram items are restricted
    to `name / sector / event` and never flow into a tradeable score.
  * **Read-only on inputs.** PDF / telegram source files are NEVER modified,
    moved, or copied. We read bytes for sha256 + (optionally) pdfplumber text
    extraction.
  * **`--dry-run` is the default.** `--apply` is required to write the 5
    output artifacts.
  * **PDF body parse is best-effort.** If `pdfplumber` is not installed, or
    body parse cannot find a `매출/영업이익/순이익/EPS` revision pair, the
    row is recorded as `parsed_status=data_insufficient` with the exact
    `missing_fields` listed. Filename-derived metadata is still emitted.
  * **`latest` is a copy.** `MONDAY_SEED_CANDIDATES_latest.csv` is generated
    by copying the dated CSV — no symlinks. The script does NOT promote
    anything to the wider Drive pipeline (no `output/latest/`, no Super Pack).

Outputs (under `<out>/`):

  1. `RAW_SOURCE_INDEX_<YYYYMMDD>.md`        — every source file, sha256, size
  2. `NEWS_REPORT_PACK_<YYYYMMDD>.md`        — readable per-category summary
  3. `MONDAY_SEED_CANDIDATES_<YYYYMMDD>.csv` — seed candidate rows (no signal)
  4. `MONDAY_SEED_CANDIDATES_latest.csv`     — copy of the dated CSV
  5. `DATA_GAP_REPORT_<YYYYMMDD>.md`         — dry-run log + missing_fields

CLI standard: `--wisereport-root`, `--telegram-root`, `--out`, `--as-of`,
`--days-back`, `--ticker-map`, `--dry-run` / `--apply`.

Env fallbacks: `WISE_REPORT_ROOT`, `TELEGRAM_ROOT`, `PHASE3_OUTPUT_ROOT`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

SOURCE_KEY = "phase3:build_monday_seed_pack:v1"
SCHEMA_VERSION = "monday_seed_pack:v1"

DEFAULT_DAYS_BACK = 4
DEFAULT_TICKER_MAP = THIS_FILE.parent.parent / "examples" / "ticker_map.example.csv"

KNOWN_BROKERS = (
    "삼성증권", "NH투자증권", "KB증권", "미래에셋증권", "키움증권", "한국투자증권",
    "신한투자증권", "대신증권", "메리츠증권", "하나증권", "유진투자증권",
    "교보증권", "이베스트투자증권", "DB금융투자", "유안타증권", "현대차증권",
    "SK증권", "다올투자증권", "IBK투자증권", "BNK투자증권", "상상인증권",
    "WiseFn", "WISEfn", "에프앤가이드",
)

# Heuristic only — leaves blank when no keyword matches.
SECTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "반도체": ("반도체", "메모리", "DRAM", "NAND", "파운드리", "HBM"),
    "디스플레이": ("디스플레이", "OLED", "LCD"),
    "2차전지": ("2차전지", "이차전지", "배터리", "양극재", "음극재", "분리막", "전해질"),
    "자동차": ("자동차", "완성차", "EV", "전기차", "현대차", "기아"),
    "조선": ("조선", "수주", "LNG선", "컨테이너선"),
    "바이오/제약": ("바이오", "제약", "임상", "신약", "FDA"),
    "인터넷/플랫폼": ("플랫폼", "커머스", "검색", "네이버", "카카오"),
    "게임": ("게임", "MMORPG", "신작"),
    "건설/건자재": ("건설", "건자재", "분양", "수주"),
    "유틸리티": ("전력", "한전", "가스", "유틸리티"),
    "철강/소재": ("철강", "POSCO", "포스코", "비철"),
    "금융": ("은행", "증권사", "보험", "지주"),
    "소비재": ("화장품", "식품", "의류", "리테일", "면세"),
    "통신": ("통신", "5G", "SKT", "KT", "LGU"),
    "방산": ("방산", "방위산업", "K2", "K9"),
    "항공/물류": ("항공", "물류", "해운", "택배"),
}

PDF_BODY_METRIC_LABELS: dict[str, str] = {
    "매출": "sales",
    "매출액": "sales",
    "영업이익": "op_profit",
    "순이익": "net_income",
    "지배주주순이익": "net_income",
    "당기순이익": "net_income",
    "EPS": "eps",
    "주당순이익": "eps",
}

CANDIDATE_HEADER = [
    "ticker", "name_kr", "sector", "broker", "report_date", "title",
    "category", "parsed_status",
    "sales_old", "sales_new",
    "op_profit_old", "op_profit_new",
    "net_income_old", "net_income_new",
    "eps_old", "eps_new",
    "target_old", "target_new",
    "horizon", "confidence",
    "source_kind", "source_path", "source_sha256",
    "missing_fields", "signal_use", "notes",
    "as_of", "source_key",
]

# Telegram event signal words — used to extract one event line per file.
EVENT_KEYWORDS = (
    "발표", "공시", "잠정", "실적", "수주", "출시", "계약", "체결", "허가", "승인",
    "리콜", "감산", "증산", "투자", "인수", "합병", "분할", "자사주", "배당", "유상증자",
    "무상증자", "감자", "상장", "FDA", "긴급", "정정", "예고",
)

DATE_PAT_DASH = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
DATE_PAT_USCORE = re.compile(r"(?<!\d)(\d{4})_(\d{2})_(\d{2})(?!\d)")
DATE_PAT_PLAIN = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")
TICKER_BRACKET = re.compile(r"\[([^\]]+)\]")
KRX_CODE_PAT = re.compile(r"(?<![\d])(\d{6})(?![\d])")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--wisereport-root",
                   default=os.getenv("WISE_REPORT_ROOT"),
                   help="WiseReport root (env fallback: WISE_REPORT_ROOT). "
                        "Layout: <root>/<YYYY-MM-DD>/{기업|산업}/*.pdf")
    p.add_argument("--telegram-root",
                   default=os.getenv("TELEGRAM_ROOT"),
                   help="Telegram raw root (env fallback: TELEGRAM_ROOT). "
                        "Layout: <root>/<YYYY-MM-DD>/<channel>/attachments/*")
    p.add_argument("--out",
                   default=os.getenv("PHASE3_OUTPUT_ROOT"),
                   help="Output directory (required for --apply). "
                        "Recommended: <stock-research-root>/03_daily_reports/<YYYY-MM-DD>/monday_seed_pack")
    p.add_argument("--as-of", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Pack reference date YYYY-MM-DD (default: today)")
    p.add_argument("--days-back", type=int, default=DEFAULT_DAYS_BACK,
                   help=f"How many days (incl. as-of) to scan (default: {DEFAULT_DAYS_BACK})")
    p.add_argument("--ticker-map", default=str(DEFAULT_TICKER_MAP),
                   help=f"Korean-name → KRX code CSV (default: {DEFAULT_TICKER_MAP})")
    p.add_argument("--no-pdf-parse", action="store_true",
                   help="Skip pdfplumber body parse even if available (filename-only).")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) summarize only; write nothing.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize the 5 output artifacts under --out.")
    return p.parse_args(argv)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _date_range(as_of: str, days_back: int) -> list[str]:
    base = datetime.strptime(as_of, "%Y-%m-%d").date()
    return [(base - timedelta(days=i)).isoformat() for i in range(days_back)]


def _sha256(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def _load_ticker_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "name_kr" not in reader.fieldnames or "ticker" not in reader.fieldnames:
            return {}
        for row in reader:
            n = (row.get("name_kr") or "").strip()
            t = (row.get("ticker") or "").strip()
            if n and t:
                out[n] = t
    return out


def _infer_filename_meta(stem: str) -> dict:
    out = {"report_date": "", "broker": "", "name_kr": "", "krx_code": "", "title": stem}
    for pat in (DATE_PAT_DASH, DATE_PAT_USCORE, DATE_PAT_PLAIN):
        m = pat.search(stem)
        if not m:
            continue
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 2000 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
            out["report_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            break
    m = TICKER_BRACKET.search(stem)
    if m:
        out["name_kr"] = m.group(1).strip()
    m = KRX_CODE_PAT.search(stem)
    if m:
        out["krx_code"] = f"KRX:{m.group(1)}"
    for b in KNOWN_BROKERS:
        if b in stem:
            out["broker"] = b
            break
    title = stem
    for s in (out["broker"], out["report_date"], out["name_kr"]):
        if s:
            title = title.replace(s, "")
    if out["name_kr"]:
        title = title.replace(f"[{out['name_kr']}]", "")
    title = re.sub(r"[\[\]\(\)_\-\.]+", " ", title).strip()
    if title:
        out["title"] = title
    return out


def _classify_sector(text: str) -> str:
    if not text:
        return ""
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return sector
    return ""


def _resolve_ticker(name_kr: str, krx_code: str, ticker_map: dict[str, str]) -> tuple[str, bool]:
    """Return (ticker, mapped). `mapped=False` when we had to fall back."""
    if krx_code and krx_code.startswith("KRX:"):
        return krx_code, True
    if name_kr and name_kr in ticker_map:
        return ticker_map[name_kr], True
    return name_kr, False


# ----------------------------------------------------------------------------
# PDF body parse (best-effort, deterministic-only)
# ----------------------------------------------------------------------------

def _try_import_pdfplumber():
    try:
        import pdfplumber  # type: ignore
        return pdfplumber
    except Exception:
        return None


_NUM_PAT = re.compile(r"[-+]?\d{1,3}(?:,\d{3})+|[-+]?\d+(?:\.\d+)?")


def _parse_num(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_revision_table(text: str) -> dict[str, dict[str, float | None]]:
    """Very conservative deterministic parser for "수정 후 / 수정 전" tables.

    Returns a dict keyed by metric ('sales' / 'op_profit' / 'net_income' / 'eps')
    with values {'old': float|None, 'new': float|None}. Empty when no
    recognizable revision table is found. Detection signals are intentionally
    narrow — anything ambiguous is left to the (separate) Vision OCR pipeline.
    """
    if not text or not text.strip():
        return {}
    has_anchor = any(k in text for k in (
        "수정 후", "수정후", "수정 전", "수정전",
        "변경 후", "변경후", "변경 전", "변경전",
        "기존", "변경",
    ))
    if not has_anchor:
        return {}
    out: dict[str, dict[str, float | None]] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        for label, key in PDF_BODY_METRIC_LABELS.items():
            if not s.startswith(label) and f" {label} " not in f" {s} ":
                continue
            nums = _NUM_PAT.findall(s)
            if len(nums) < 2:
                continue
            old_val = _parse_num(nums[-2])
            new_val = _parse_num(nums[-1])
            if old_val is None and new_val is None:
                continue
            if key in out:
                continue
            out[key] = {"old": old_val, "new": new_val}
            break
    return out


def _read_pdf_text(path: Path, pdfplumber) -> str:
    try:
        with pdfplumber.open(str(path)) as pdf:
            chunks = []
            for page in pdf.pages[:8]:  # estimate tables live on early pages
                t = page.extract_text() or ""
                chunks.append(t)
            return "\n".join(chunks)
    except Exception as exc:
        return f"__PDFPLUMBER_ERROR__: {exc}"


# ----------------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------------

def _walk_company(wisereport_root: Path, dates: list[str]) -> Iterable[tuple[Path, str, str]]:
    for d in dates:
        sub = wisereport_root / d / "기업"
        if not sub.exists():
            continue
        for p in sorted(sub.glob("*.pdf")):
            if p.is_file():
                yield p, d, "company"


def _walk_industry(wisereport_root: Path, dates: list[str]) -> Iterable[tuple[Path, str, str]]:
    for d in dates:
        sub = wisereport_root / d / "산업"
        if not sub.exists():
            continue
        for p in sorted(sub.glob("*.pdf")):
            if p.is_file():
                yield p, d, "industry"


def _walk_telegram(telegram_root: Path, dates: list[str]) -> Iterable[tuple[Path, str, str]]:
    accept_ext = {".pdf", ".txt", ".html", ".htm", ".json", ".eml", ".md"}
    for d in dates:
        date_dir = telegram_root / d
        if not date_dir.exists():
            continue
        for p in sorted(date_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in accept_ext:
                yield p, d, "telegram"


# ----------------------------------------------------------------------------
# Telegram event extraction (name / sector / event ONLY, no signal)
# ----------------------------------------------------------------------------

def _read_telegram_text(path: Path, max_bytes: int = 256_000) -> str:
    try:
        if path.suffix.lower() == ".pdf":
            # PDF telegram attachments stay metadata-only here.
            return ""
        raw = path.read_bytes()[:max_bytes]
        for enc in ("utf-8", "utf-16", "cp949", "euc-kr"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_telegram_event(text: str, filename_meta: dict) -> tuple[str, str]:
    """Return (name_kr, event_line). Best-effort, never used as a signal."""
    name = filename_meta.get("name_kr", "") or ""
    if not name:
        # Try to grab the first [브래킷] from body text.
        m = TICKER_BRACKET.search(text or "")
        if m:
            name = m.group(1).strip()
    event = ""
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if any(k in s for k in EVENT_KEYWORDS):
            event = s[:240]
            break
    if not event and text:
        event = text.strip().splitlines()[0][:240]
    return name, event


# ----------------------------------------------------------------------------
# Row builders
# ----------------------------------------------------------------------------

def _make_company_row(path: Path, date_dir: str, filename_meta: dict,
                       parsed_metrics: dict, parse_error: str | None,
                       sha: str, size: int, ticker_map: dict[str, str],
                       as_of: str, pdfplumber_available: bool,
                       no_pdf_parse: bool) -> dict:
    name_kr = filename_meta["name_kr"]
    title = filename_meta["title"]
    sector_text = " ".join([name_kr, title])
    sector = _classify_sector(sector_text)
    ticker, mapped = _resolve_ticker(name_kr, filename_meta["krx_code"], ticker_map)

    sales = parsed_metrics.get("sales", {})
    op_profit = parsed_metrics.get("op_profit", {})
    net_income = parsed_metrics.get("net_income", {})
    eps = parsed_metrics.get("eps", {})

    has_any_metric = any(parsed_metrics.get(k, {}) for k in ("sales", "op_profit", "net_income", "eps"))
    missing: list[str] = []
    if no_pdf_parse:
        parsed_status = "filename_only_by_flag"
        missing.append("body_parse_skipped")
    elif not pdfplumber_available:
        parsed_status = "data_insufficient"
        missing.append("pdfplumber_unavailable")
    elif parse_error:
        parsed_status = "data_insufficient"
        missing.append(f"parse_error:{parse_error[:60]}")
    elif has_any_metric:
        parsed_status = "estimate_revision_parsed"
    else:
        parsed_status = "data_insufficient"
        missing.append("no_revision_anchor")

    if not filename_meta["report_date"]:
        missing.append("report_date")
    if not filename_meta["broker"]:
        missing.append("broker")
    if not name_kr:
        missing.append("name_kr")
    if not mapped:
        missing.append("ticker_unmapped")

    notes = "estimate-revision metadata; not a buy/sell signal"
    return {
        "ticker": ticker,
        "name_kr": name_kr,
        "sector": sector,
        "broker": filename_meta["broker"],
        "report_date": filename_meta["report_date"] or date_dir,
        "title": title,
        "category": "company",
        "parsed_status": parsed_status,
        "sales_old": sales.get("old", "") if sales else "",
        "sales_new": sales.get("new", "") if sales else "",
        "op_profit_old": op_profit.get("old", "") if op_profit else "",
        "op_profit_new": op_profit.get("new", "") if op_profit else "",
        "net_income_old": net_income.get("old", "") if net_income else "",
        "net_income_new": net_income.get("new", "") if net_income else "",
        "eps_old": eps.get("old", "") if eps else "",
        "eps_new": eps.get("new", "") if eps else "",
        "target_old": "",
        "target_new": "",
        "horizon": "",
        "confidence": "",
        "source_kind": "wisereport_company_pdf",
        "source_path": str(path),
        "source_sha256": sha,
        "missing_fields": ";".join(missing),
        "signal_use": "0",
        "notes": notes,
        "as_of": as_of,
        "source_key": SOURCE_KEY,
        "_size": size,
    }


def _make_industry_row(path: Path, date_dir: str, filename_meta: dict,
                        sha: str, size: int, as_of: str) -> dict:
    title = filename_meta["title"]
    sector = _classify_sector(title)
    return {
        "ticker": "",
        "name_kr": filename_meta["name_kr"],
        "sector": sector,
        "broker": filename_meta["broker"],
        "report_date": filename_meta["report_date"] or date_dir,
        "title": title,
        "category": "industry",
        "parsed_status": "industry_meta_only",
        "sales_old": "", "sales_new": "",
        "op_profit_old": "", "op_profit_new": "",
        "net_income_old": "", "net_income_new": "",
        "eps_old": "", "eps_new": "",
        "target_old": "", "target_new": "",
        "horizon": "", "confidence": "",
        "source_kind": "wisereport_industry_pdf",
        "source_path": str(path),
        "source_sha256": sha,
        "missing_fields": "industry_no_per_company_metrics",
        "signal_use": "0",
        "notes": "industry/sector context only; not a buy/sell signal",
        "as_of": as_of,
        "source_key": SOURCE_KEY,
        "_size": size,
    }


def _make_telegram_row(path: Path, date_dir: str, filename_meta: dict,
                        text: str, sha: str, size: int,
                        ticker_map: dict[str, str], as_of: str) -> dict:
    name_kr, event = _extract_telegram_event(text, filename_meta)
    sector = _classify_sector(" ".join([name_kr, event, filename_meta["title"]]))
    ticker, mapped = _resolve_ticker(name_kr, filename_meta["krx_code"], ticker_map)
    missing = []
    if not name_kr:
        missing.append("name_kr")
    if not event:
        missing.append("event_line")
    if not mapped:
        missing.append("ticker_unmapped")
    return {
        "ticker": ticker,
        "name_kr": name_kr,
        "sector": sector,
        "broker": "",
        "report_date": filename_meta["report_date"] or date_dir,
        "title": event or filename_meta["title"],
        "category": "telegram_event",
        "parsed_status": "event_only",
        "sales_old": "", "sales_new": "",
        "op_profit_old": "", "op_profit_new": "",
        "net_income_old": "", "net_income_new": "",
        "eps_old": "", "eps_new": "",
        "target_old": "", "target_new": "",
        "horizon": "", "confidence": "",
        "source_kind": f"telegram:{path.suffix.lstrip('.').lower() or 'unknown'}",
        "source_path": str(path),
        "source_sha256": sha,
        "missing_fields": ";".join(missing) or "financials_not_applicable",
        "signal_use": "0",
        "notes": "telegram event metadata only; explicitly NOT a buy/sell signal",
        "as_of": as_of,
        "source_key": SOURCE_KEY,
        "_size": size,
    }


# ----------------------------------------------------------------------------
# Output writers
# ----------------------------------------------------------------------------

def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANDIDATE_HEADER, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CANDIDATE_HEADER})


def _render_raw_index(rows: list[dict], dates: list[str], as_of: str,
                      wisereport_root: Path | None, telegram_root: Path | None) -> str:
    lines = io.StringIO()
    lines.write(f"# RAW_SOURCE_INDEX — {as_of}\n\n")
    lines.write(f"- schema: `{SCHEMA_VERSION}`\n")
    lines.write(f"- as_of: `{as_of}`\n")
    lines.write(f"- date_window: `{dates[-1]}` … `{dates[0]}`  ({len(dates)} days)\n")
    lines.write(f"- wisereport_root: `{wisereport_root or '(unset)'}`\n")
    lines.write(f"- telegram_root: `{telegram_root or '(unset)'}`\n\n")

    by_kind: dict[str, list[dict]] = {}
    for r in rows:
        by_kind.setdefault(r["source_kind"], []).append(r)

    lines.write("## Counts by source_kind\n\n")
    lines.write("| source_kind | count |\n| --- | --: |\n")
    for k, vs in sorted(by_kind.items()):
        lines.write(f"| `{k}` | {len(vs)} |\n")
    lines.write("\n")

    lines.write("## Files\n\n")
    lines.write("| date | category | source_kind | filename | size (bytes) | sha256 (12) |\n")
    lines.write("| --- | --- | --- | --- | --: | --- |\n")
    for r in sorted(rows, key=lambda x: (x["report_date"], x["category"], x["source_path"])):
        fn = Path(r["source_path"]).name
        size = r.get("_size", "")
        lines.write(
            f"| {r['report_date']} | {r['category']} | `{r['source_kind']}` | "
            f"{fn} | {size} | `{r['source_sha256'][:12]}…` |\n"
        )
    return lines.getvalue()


def _render_news_pack(rows: list[dict], as_of: str, dates: list[str]) -> str:
    company = [r for r in rows if r["category"] == "company"]
    industry = [r for r in rows if r["category"] == "industry"]
    tele = [r for r in rows if r["category"] == "telegram_event"]

    out = io.StringIO()
    out.write(f"# NEWS_REPORT_PACK — {as_of}\n\n")
    out.write("> Metadata-only. **No buy/sell signal**. Telegram items are extracted "
              "as `name / sector / event` and explicitly excluded from any tradeable score.\n\n")
    out.write(f"- date_window: `{dates[-1]}` … `{dates[0]}`\n")
    out.write(f"- company_reports: {len(company)}\n")
    out.write(f"- industry_reports: {len(industry)}\n")
    out.write(f"- telegram_events: {len(tele)}\n\n")

    out.write("## 기업 리포트 (Company)\n\n")
    if not company:
        out.write("_no company reports in window_\n\n")
    else:
        out.write("| date | name | ticker | broker | sector | parsed_status | title |\n")
        out.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for r in sorted(company, key=lambda x: (x["report_date"], x["name_kr"])):
            out.write(
                f"| {r['report_date']} | {r['name_kr']} | `{r['ticker']}` | "
                f"{r['broker']} | {r['sector']} | `{r['parsed_status']}` | "
                f"{r['title']} |\n"
            )
        out.write("\n")
        parsed_rows = [r for r in company if r["parsed_status"] == "estimate_revision_parsed"]
        if parsed_rows:
            out.write("### Estimate revisions parsed\n\n")
            out.write("| date | name | broker | sales (old→new) | op_profit (old→new) | "
                      "net_income (old→new) | eps (old→new) |\n")
            out.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            for r in parsed_rows:
                out.write(
                    f"| {r['report_date']} | {r['name_kr']} | {r['broker']} | "
                    f"{r['sales_old']}→{r['sales_new']} | "
                    f"{r['op_profit_old']}→{r['op_profit_new']} | "
                    f"{r['net_income_old']}→{r['net_income_new']} | "
                    f"{r['eps_old']}→{r['eps_new']} |\n"
                )
            out.write("\n")

    out.write("## 산업 리포트 (Industry)\n\n")
    if not industry:
        out.write("_no industry reports in window_\n\n")
    else:
        out.write("| date | sector | broker | title |\n")
        out.write("| --- | --- | --- | --- |\n")
        for r in sorted(industry, key=lambda x: (x["report_date"], x["sector"])):
            out.write(f"| {r['report_date']} | {r['sector']} | {r['broker']} | {r['title']} |\n")
        out.write("\n")

    out.write("## 텔레그램 이벤트 (event-only, NOT a signal)\n\n")
    if not tele:
        out.write("_no telegram events in window_\n\n")
    else:
        out.write("| date | name | ticker | sector | event |\n")
        out.write("| --- | --- | --- | --- | --- |\n")
        for r in sorted(tele, key=lambda x: (x["report_date"], x["name_kr"])):
            out.write(
                f"| {r['report_date']} | {r['name_kr']} | `{r['ticker']}` | "
                f"{r['sector']} | {r['title']} |\n"
            )
        out.write("\n")

    return out.getvalue()


def _render_gap_report(rows: list[dict], as_of: str, dates: list[str],
                       pdfplumber_available: bool, no_pdf_parse: bool,
                       wisereport_root: Path | None, telegram_root: Path | None,
                       dry_run_log: list[str], out_dir: Path,
                       latest_was_missing: bool) -> str:
    out = io.StringIO()
    out.write(f"# DATA_GAP_REPORT — {as_of}\n\n")
    out.write(f"- schema: `{SCHEMA_VERSION}`\n")
    out.write(f"- as_of: `{as_of}`\n")
    out.write(f"- date_window: `{dates[-1]}` … `{dates[0]}`\n")
    out.write(f"- pdfplumber_available: `{pdfplumber_available}`\n")
    out.write(f"- pdf_parse_skipped_by_flag: `{no_pdf_parse}`\n")
    out.write(f"- wisereport_root: `{wisereport_root or '(unset)'}`\n")
    out.write(f"- telegram_root: `{telegram_root or '(unset)'}`\n")
    out.write(f"- output_dir: `{out_dir}`\n")
    out.write(f"- latest_csv_was_missing_before_run: `{latest_was_missing}`\n\n")

    out.write("## Missing fields by row\n\n")
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["parsed_status"]] = by_status.get(r["parsed_status"], 0) + 1
    out.write("### parsed_status histogram\n\n")
    out.write("| parsed_status | count |\n| --- | --: |\n")
    for s, c in sorted(by_status.items(), key=lambda x: -x[1]):
        out.write(f"| `{s}` | {c} |\n")
    out.write("\n")

    out.write("### Per-row missing_fields\n\n")
    out.write("| date | category | name | parsed_status | missing_fields |\n")
    out.write("| --- | --- | --- | --- | --- |\n")
    for r in sorted(rows, key=lambda x: (x["report_date"], x["category"], x["name_kr"])):
        if not r.get("missing_fields"):
            continue
        out.write(
            f"| {r['report_date']} | {r['category']} | {r['name_kr'] or '(none)'} | "
            f"`{r['parsed_status']}` | `{r['missing_fields']}` |\n"
        )
    out.write("\n")

    out.write("## Dry-run / runner log\n\n")
    if dry_run_log:
        out.write("```\n")
        for line in dry_run_log:
            out.write(line + "\n")
        out.write("```\n")
    else:
        out.write("_(no log lines)_\n")
    return out.getvalue()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    log: list[str] = []

    def L(msg: str) -> None:
        log.append(msg)
        print(msg)

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    L(f"[{mode}] schema={SCHEMA_VERSION}  as_of={args.as_of}  days_back={args.days_back}")

    try:
        dates = _date_range(args.as_of, args.days_back)
    except ValueError as exc:
        print(f"error: --as-of must be YYYY-MM-DD ({exc})", file=sys.stderr)
        return 2
    L(f"[{mode}] date_window = {dates[-1]} ... {dates[0]}")

    # Intentionally NOT resolving — keeps relative inputs relative in the CSV /
    # markdown outputs so the committed fixture stays portable. Real Drive paths
    # are absolute on the operator host so they remain absolute by themselves.
    wisereport_root = Path(args.wisereport_root).expanduser() if args.wisereport_root else None
    telegram_root = Path(args.telegram_root).expanduser() if args.telegram_root else None
    L(f"[{mode}] wisereport_root = {wisereport_root or '(unset)'}")
    L(f"[{mode}] telegram_root   = {telegram_root or '(unset)'}")

    if not wisereport_root and not telegram_root:
        print("error: at least one of --wisereport-root / --telegram-root must be set "
              "(or via env WISE_REPORT_ROOT / TELEGRAM_ROOT)", file=sys.stderr)
        return 2

    ticker_map_path = Path(args.ticker_map).expanduser()
    ticker_map = _load_ticker_map(ticker_map_path)
    L(f"[{mode}] ticker_map = {ticker_map_path} (entries={len(ticker_map)})")

    pdfplumber = None if args.no_pdf_parse else _try_import_pdfplumber()
    pdfplumber_available = pdfplumber is not None
    L(f"[{mode}] pdfplumber_available = {pdfplumber_available}")

    rows: list[dict] = []

    if wisereport_root and wisereport_root.exists():
        for path, date_dir, _kind in _walk_company(wisereport_root, dates):
            try:
                sha = _sha256(path)
                size = path.stat().st_size
            except OSError as exc:
                L(f"  [warn] unreadable: {path}: {exc}")
                continue
            fmeta = _infer_filename_meta(path.stem)
            parsed: dict[str, dict[str, float | None]] = {}
            parse_err: str | None = None
            if pdfplumber and not args.no_pdf_parse:
                txt = _read_pdf_text(path, pdfplumber)
                if txt.startswith("__PDFPLUMBER_ERROR__"):
                    parse_err = txt.removeprefix("__PDFPLUMBER_ERROR__:").strip()
                else:
                    parsed = _parse_revision_table(txt)
            row = _make_company_row(path, date_dir, fmeta, parsed, parse_err,
                                    sha, size, ticker_map, args.as_of,
                                    pdfplumber_available, args.no_pdf_parse)
            rows.append(row)

        for path, date_dir, _kind in _walk_industry(wisereport_root, dates):
            try:
                sha = _sha256(path)
                size = path.stat().st_size
            except OSError as exc:
                L(f"  [warn] unreadable: {path}: {exc}")
                continue
            fmeta = _infer_filename_meta(path.stem)
            rows.append(_make_industry_row(path, date_dir, fmeta, sha, size, args.as_of))
    else:
        L(f"  [info] wisereport_root not present — skipping company/industry walk")

    if telegram_root and telegram_root.exists():
        for path, date_dir, _kind in _walk_telegram(telegram_root, dates):
            try:
                sha = _sha256(path)
                size = path.stat().st_size
            except OSError as exc:
                L(f"  [warn] unreadable: {path}: {exc}")
                continue
            fmeta = _infer_filename_meta(path.stem)
            text = _read_telegram_text(path)
            rows.append(_make_telegram_row(path, date_dir, fmeta, text, sha, size,
                                            ticker_map, args.as_of))
    else:
        L(f"  [info] telegram_root not present — skipping telegram walk")

    by_kind: dict[str, int] = {}
    for r in rows:
        by_kind[r["source_kind"]] = by_kind.get(r["source_kind"], 0) + 1
    L(f"[{mode}] total_rows = {len(rows)}")
    for k, v in sorted(by_kind.items()):
        L(f"  {k}: {v}")

    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["parsed_status"]] = by_status.get(r["parsed_status"], 0) + 1
    for s, c in sorted(by_status.items(), key=lambda x: -x[1]):
        L(f"  parsed_status={s}: {c}")

    yyyymmdd = args.as_of.replace("-", "")
    if args.out:
        out_dir = Path(args.out).expanduser().resolve()
    else:
        out_dir = Path("./output").resolve() / args.as_of / "monday_seed_pack"
    L(f"[{mode}] out_dir = {out_dir}")

    raw_index = _render_raw_index(rows, dates, args.as_of, wisereport_root, telegram_root)
    news_pack = _render_news_pack(rows, args.as_of, dates)
    candidates_csv_path = out_dir / f"MONDAY_SEED_CANDIDATES_{yyyymmdd}.csv"
    latest_csv_path = out_dir / "MONDAY_SEED_CANDIDATES_latest.csv"
    raw_index_path = out_dir / f"RAW_SOURCE_INDEX_{yyyymmdd}.md"
    news_pack_path = out_dir / f"NEWS_REPORT_PACK_{yyyymmdd}.md"
    gap_report_path = out_dir / f"DATA_GAP_REPORT_{yyyymmdd}.md"

    latest_was_missing = not latest_csv_path.exists()

    if args.dry_run:
        L(f"[DRY-RUN] would write {raw_index_path.name}    ({len(raw_index)} chars)")
        L(f"[DRY-RUN] would write {news_pack_path.name}    ({len(news_pack)} chars)")
        L(f"[DRY-RUN] would write {candidates_csv_path.name} ({len(rows)} rows)")
        L(f"[DRY-RUN] would write MONDAY_SEED_CANDIDATES_latest.csv "
          f"({'create' if latest_was_missing else 'replace'})")
        L(f"[DRY-RUN] would write {gap_report_path.name}    (per-row missing_fields)")
        L("[DRY-RUN] re-run with --apply to materialize.")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_index_path.write_text(raw_index, encoding="utf-8")
    L(f"[APPLY] wrote {raw_index_path}")
    news_pack_path.write_text(news_pack, encoding="utf-8")
    L(f"[APPLY] wrote {news_pack_path}")
    _write_csv(candidates_csv_path, rows)
    L(f"[APPLY] wrote {candidates_csv_path} ({len(rows)} rows)")
    shutil.copyfile(candidates_csv_path, latest_csv_path)
    L(f"[APPLY] copied -> {latest_csv_path} "
      f"({'created (was missing)' if latest_was_missing else 'replaced existing'})")
    gap_report_path.write_text(
        _render_gap_report(rows, args.as_of, dates, pdfplumber_available,
                           args.no_pdf_parse, wisereport_root, telegram_root,
                           log, out_dir, latest_was_missing),
        encoding="utf-8",
    )
    L(f"[APPLY] wrote {gap_report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
