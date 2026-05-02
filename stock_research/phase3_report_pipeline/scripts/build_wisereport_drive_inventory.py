#!/usr/bin/env python3
"""
Phase 3 — PR #44 — WiseReport Google Drive folder URL inventory builder.

Sibling to PR #39's `build_wisereport_inventory.py`, but takes Google
Drive `folders/<FOLDER_ID>` URLs (or bare folder IDs) instead of a local
filesystem mount. Useful when the operator does NOT have the WiseReport
Drive mounted on their MacBook and only has the share URLs.

Two folder roles:

  * `--company-drive-folder-url <URL>`   — 기업 (company) PDFs, fed to the
                                          existing PR #29 chain runner via
                                          the top-level `selected[]` alias.
  * `--industry-drive-folder-url <URL>`  — 산업 (industry) PDFs, isolated
                                          into `selected_industry[]` and
                                          NEVER folded into `selected[]`
                                          (so the deterministic parser
                                          cannot accidentally process
                                          industry reports).

Usage
-----
    python3 scripts/build_wisereport_drive_inventory.py \
        --date 2026-04-30 \
        --company-drive-folder-url "https://drive.google.com/drive/folders/1-GiNJ47og07Jwvj2-PbQLqs7EwpN21va" \
        --industry-drive-folder-url "https://drive.google.com/drive/folders/1Y4AhlpSSGW6GiroVMS1mSpyCCiF7JUEW" \
        --out /tmp/wisereport_drive_inventory.json \
        --max-company-pdfs 50 \
        --max-industry-pdfs 50 \
        [--download-dir /tmp/wisereport_pdfs] \
        [--max-download-pdfs 5] \
        [--download-which company,industry] \
        [--apply]

Offline / fixture mode
----------------------
For tests and offline operator runs, an HTML cache may be supplied with
`--listing-cache-dir <DIR>`. The script will then read the listing HTML
from `<DIR>/<folder_id>.html` instead of fetching from `drive.google.com`.
Similarly `--download-cache-dir <DIR>` substitutes per-file PDF bytes
from `<DIR>/<file_id>.pdf` so download paths can be exercised without
network.

Schema (`phase3:wisereport_drive_folder_inventory:v1`)
------------------------------------------------------
{
  "schema": "phase3:wisereport_drive_folder_inventory:v1",
  "date": "YYYY-MM-DD",
  "company_drive_folder_id": "<id or null>",
  "industry_drive_folder_id": "<id or null>",
  "max_company_pdfs": 50,
  "max_industry_pdfs": 50,
  "download_dir": "<abs path or null>",
  "max_download_pdfs": int,
  "download_which": ["company"|"industry", ...],
  "summary": {
    "company_pdf_count": int,
    "industry_pdf_count": int,
    "malformed_filename_count": int,
    "duplicate_basename_count": int,
    "skipped_non_pdf_count": int,
    "capped_company_count": int,
    "capped_industry_count": int,
    "direct_trade_signal_true_count": 0,
    "selected_alias_count": int,
    "selected_alias_matches_company": true,
    "downloaded_pdf_count": int,
    "failed_download_count": int,
    "files_with_download_errors": [ { file_id, filename, reason } ... ]
  },
  "selected":          [ ... ],   # alias of selected_company[]; never industry
  "selected_company":  [ ... ],   # capped at max-company-pdfs
  "selected_industry": [ ... ],   # capped at max-industry-pdfs
  "malformed":          [ {filename, folder, reason} ... ],
  "skipped_non_pdf":    [ {filename, folder} ... ],
  "duplicate_basename": [ {basename, folder, count} ... ],
  "forbidden_actions_confirmed": { ... }
}

Per-PDF entry shape
-------------------
Company (selected_company[] and selected[]):
  { report_date, report_type=company,
    filename, drive_file_id, drive_web_url,
    ticker_hint, title_hint,
    folder_type=기업, source=drive,
    direct_trade_signal=false,
    [local_pdf_path]  # only if PDF was actually downloaded
  }

Industry (selected_industry[]):
  { report_date, report_type=industry,
    filename, drive_file_id, drive_web_url,
    sector_hint, title_hint,
    folder_type=산업, source=drive,
    direct_trade_signal=false, summary_queue=true,
    [local_pdf_path]  # only if PDF was actually downloaded
  }

Forbidden / refused operations
------------------------------
  * No Drive writes / renames / deletes — script only issues GET requests
    against the public folder/file URLs, never PATCH / POST / DELETE.
  * No OCR / Vision / API client. Network calls are only:
      - GET https://drive.google.com/embeddedfolderview?id=<FOLDER_ID>
      - GET https://drive.google.com/uc?export=download&id=<FILE_ID>
    via stdlib `urllib.request`. No `googleapiclient`, no API key.
  * `--out` resolving inside the repo + `--apply` → exit 2.
  * `--download-dir` resolving inside the repo (under --apply) → exit 2.
  * `--max-*-pdfs` > 50 → exit 2 (HARD_MAX invariant).
  * Default dry-run; only `--apply` writes the file or downloads bytes.
  * `direct_trade_signal=true` would never be emitted by this script;
    if any consumer-supplied entry tried to set it true (the field is
    never read from user input) the script would exit 3 by guard.
  * Drive listing fetch failure (network error / 403) → exit 4 with
    a hint pointing the operator at --listing-cache-dir for offline mode.
  * --listing-cache-dir cache miss (file expected at
    `<DIR>/<folder_id>.html` is missing) → also exit 4, with a hint
    that distinguishes the cache-miss case from the network case.

This script does NOT change parser / bridge / merge / build / emit / ticker
map / broker autodetect logic. It is purely a Drive-folder lister + raw
PDF downloader that builds an inventory JSON for downstream consumption.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

INVENTORY_SCHEMA = "phase3:wisereport_drive_folder_inventory:v1"

HARD_MAX_PDFS = 50

FOLDER_COMPANY = "기업"
FOLDER_INDUSTRY = "산업"

PDF_EXT_LOWER = ".pdf"

# `YYYYMMDD_[<bracket>] <title>.pdf`  (same shape as PR #39).
_FILENAME_RE = re.compile(
    r"^(?P<date>\d{8})_\[(?P<bracket>[^\]]+)\]\s*(?P<title>.+)\.pdf$",
    re.IGNORECASE,
)

# `https://drive.google.com/drive/folders/<ID>` (with optional ?usp=...)
# Or bare `<ID>` (Drive folder IDs are 25-44 chars of [A-Za-z0-9_-]).
_FOLDER_URL_RE = re.compile(
    r"https?://drive\.google\.com/(?:drive/(?:u/\d+/)?)?folders/(?P<id>[A-Za-z0-9_\-]+)"
)
_BARE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{20,80}$")

# `https://drive.google.com/file/d/<ID>/...`
_FILE_URL_RE = re.compile(
    r"https?://drive\.google\.com/file/d/(?P<id>[A-Za-z0-9_\-]+)"
)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _extract_folder_id(value: str) -> str | None:
    """Return the Drive folder ID from a URL or bare ID, or None."""
    if not value:
        return None
    m = _FOLDER_URL_RE.search(value)
    if m:
        return m.group("id")
    if _BARE_ID_RE.match(value.strip()):
        return value.strip()
    return None


def _file_web_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"


def _file_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _folder_listing_url(folder_id: str) -> str:
    # `embeddedfolderview` returns a small static HTML page that lists the
    # folder's files. Public folders can be fetched without auth. We never
    # use the authenticated Drive API.
    return f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"


def _http_get(url: str, *, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "phase3-pr44-drive-inventory/1.0 (+stdlib-urllib)",
            "Accept": "*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_folder_listing_html(
    folder_id: str,
    *,
    listing_cache_dir: Path | None,
) -> str:
    """Fetch the embedded-folder-view HTML for a Drive folder.

    With --listing-cache-dir set, reads `<dir>/<folder_id>.html` instead.
    This makes the script fully testable offline and lets the operator
    pre-fetch listings on a network-allowed host and feed them in.
    """
    if listing_cache_dir is not None:
        cache_path = listing_cache_dir / f"{folder_id}.html"
        if not cache_path.is_file():
            raise FileNotFoundError(
                f"listing cache miss: {cache_path} (provide it or drop --listing-cache-dir)"
            )
        return cache_path.read_text(encoding="utf-8")
    raw = _http_get(_folder_listing_url(folder_id))
    return raw.decode("utf-8", errors="replace")


def _parse_listing_html(html_text: str) -> list[tuple[str, str]]:
    """Return [(file_id, filename), ...] parsed from a Drive folder listing HTML.

    The embeddedfolderview page renders each entry as an `<a>` whose
    `href` points to `/file/d/<FILE_ID>/...` and whose visible label is
    inside an element with class containing `flip-entry-title`. We extract
    the file IDs and pair them positionally with titles.

    Falls back to a simpler "all file IDs in document order" pairing if
    the strict pattern misses entries — file titles are still recovered
    from the `flip-entry-title` divs in document order.
    """
    # Order-preserving collection of file IDs and titles; pair by index.
    ids: list[str] = []
    titles: list[str] = []

    for m in _FILE_URL_RE.finditer(html_text):
        fid = m.group("id")
        if fid not in ids:
            ids.append(fid)

    # Title divs (Drive currently uses class="flip-entry-title").
    for m in re.finditer(
        r'<div[^>]*class="[^"]*flip-entry-title[^"]*"[^>]*>(?P<t>.*?)</div>',
        html_text,
        flags=re.DOTALL,
    ):
        raw = m.group("t")
        # Strip nested tags, decode entities, collapse whitespace.
        bare = re.sub(r"<[^>]+>", "", raw)
        bare = html.unescape(bare).strip()
        bare = re.sub(r"\s+", " ", bare)
        titles.append(bare)

    pairs: list[tuple[str, str]] = []
    for idx, fid in enumerate(ids):
        title = titles[idx] if idx < len(titles) else ""
        pairs.append((fid, title))
    return pairs


def _classify_filename(filename: str) -> tuple[str | None, str | None, str | None]:
    """Return (bracket_text, title_text, malformed_reason).

    On success: (bracket, title, None).
    On malformed: (None, None, reason_token).
    """
    m = _FILENAME_RE.match(filename)
    if m:
        return m.group("bracket").strip(), m.group("title").strip(), None

    if not filename.lower().endswith(PDF_EXT_LOWER):
        return None, None, "not_pdf_extension"
    if "[" not in filename or "]" not in filename:
        return None, None, "no_bracket_segment"
    if not re.match(r"^\d{8}_", filename):
        return None, None, "no_yyyymmdd_prefix"
    return None, None, "regex_match_failed"


def _list_drive_folder(
    folder_id: str,
    folder_type: str,
    report_type: str,
    report_date: str,
    max_pdfs: int,
    *,
    listing_cache_dir: Path | None,
) -> tuple[list[dict], list[dict], list[dict], list[dict], int, int]:
    """List a Drive folder via embeddedfolderview HTML.

    Returns (selected, malformed, skipped_non_pdf, duplicate_basename,
             scanned_pdf_count, capped_dropped) — same shape as PR #39's
    `_scan_folder()` so the two scripts converge on the same downstream
    consumer expectations.
    """
    selected: list[dict] = []
    malformed: list[dict] = []
    skipped_non_pdf: list[dict] = []
    duplicate_basename: list[dict] = []
    scanned_pdf_count = 0
    capped_dropped = 0

    html_text = _fetch_folder_listing_html(folder_id, listing_cache_dir=listing_cache_dir)
    raw_entries = _parse_listing_html(html_text)

    # Deterministic ordering for capping: by filename.
    raw_entries.sort(key=lambda x: x[1])

    seen_basename_to_count: dict[str, int] = {}
    valid_pre_cap: list[tuple[str, str, str, str]] = []  # (file_id, filename, bracket, title)

    for file_id, filename in raw_entries:
        if not filename:
            # An entry with no recoverable title — record as malformed
            # rather than silently dropping it.
            malformed.append({
                "filename": "",
                "folder": folder_type,
                "reason": "empty_title",
                "drive_file_id": file_id,
            })
            continue

        if not filename.lower().endswith(PDF_EXT_LOWER):
            skipped_non_pdf.append({
                "filename": filename,
                "folder": folder_type,
                "drive_file_id": file_id,
            })
            continue

        scanned_pdf_count += 1
        seen_basename_to_count[filename] = seen_basename_to_count.get(filename, 0) + 1

        bracket, title, reason = _classify_filename(filename)
        if reason is not None:
            malformed.append({
                "filename": filename,
                "folder": folder_type,
                "reason": reason,
                "drive_file_id": file_id,
            })
            continue

        valid_pre_cap.append((file_id, filename, bracket or "", title or ""))

    for bn, cnt in seen_basename_to_count.items():
        if cnt > 1:
            duplicate_basename.append({
                "basename": bn,
                "folder": folder_type,
                "count": cnt,
            })

    if len(valid_pre_cap) > max_pdfs:
        capped_dropped = len(valid_pre_cap) - max_pdfs
        valid_pre_cap = valid_pre_cap[:max_pdfs]

    for file_id, filename, bracket, title in valid_pre_cap:
        entry: dict = {
            "report_date": report_date,
            "report_type": report_type,
            "filename": filename,
            "drive_file_id": file_id,
            "drive_web_url": _file_web_url(file_id),
            "title_hint": title,
            "folder_type": folder_type,
            "source": "drive",
            "direct_trade_signal": False,
        }
        if report_type == "company":
            entry["ticker_hint"] = bracket
        else:  # industry
            entry["sector_hint"] = bracket
            entry["summary_queue"] = True
        selected.append(entry)

    return (selected, malformed, skipped_non_pdf,
            duplicate_basename, scanned_pdf_count, capped_dropped)


def _download_pdf_bytes(file_id: str, *, download_cache_dir: Path | None,
                        timeout: float = 60.0) -> bytes:
    """Fetch raw PDF bytes for a Drive file ID.

    With `--download-cache-dir` set, reads `<dir>/<file_id>.pdf` from disk
    instead of issuing a network call. The download endpoint is the
    public `uc?export=download&id=<ID>` URL — no auth, no API key.
    """
    if download_cache_dir is not None:
        cache_path = download_cache_dir / f"{file_id}.pdf"
        if not cache_path.is_file():
            raise FileNotFoundError(
                f"download cache miss: {cache_path}"
            )
        return cache_path.read_bytes()
    return _http_get(_file_download_url(file_id), timeout=timeout)


def _attempt_downloads(
    entries: list[dict],
    folder_role: str,
    download_dir: Path,
    download_cache_dir: Path | None,
    max_remaining: int,
) -> tuple[int, int, list[dict]]:
    """Download up to `max_remaining` PDFs from `entries` into `download_dir`.

    Mutates entries in place to add `local_pdf_path` on success. Returns
    (downloaded_count, failed_count, files_with_errors[]).
    """
    downloaded = 0
    failed = 0
    errors: list[dict] = []

    if max_remaining <= 0:
        return downloaded, failed, errors

    sub_dir = download_dir / folder_role
    sub_dir.mkdir(parents=True, exist_ok=True)

    for ent in entries:
        if downloaded >= max_remaining:
            break
        file_id = ent.get("drive_file_id")
        filename = ent.get("filename") or f"{file_id}.pdf"
        if not file_id:
            failed += 1
            errors.append({
                "file_id": None,
                "filename": filename,
                "reason": "missing_drive_file_id",
            })
            continue
        target = sub_dir / filename
        try:
            data = _download_pdf_bytes(file_id, download_cache_dir=download_cache_dir)
        except (urllib.error.URLError, FileNotFoundError, OSError) as exc:
            failed += 1
            errors.append({
                "file_id": file_id,
                "filename": filename,
                "reason": f"{type(exc).__name__}: {exc}",
            })
            continue
        # Trivial sanity guard: refuse to materialize a file that obviously
        # is HTML (e.g., a sign-in interstitial). PDFs start with '%PDF'.
        if not data.startswith(b"%PDF"):
            failed += 1
            errors.append({
                "file_id": file_id,
                "filename": filename,
                "reason": "downloaded_bytes_are_not_pdf_magic",
            })
            continue
        target.write_bytes(data)
        ent["local_pdf_path"] = str(target.resolve())
        downloaded += 1

    return downloaded, failed, errors


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--date", required=True,
                   help="Report-date label (YYYY-MM-DD). Drive folders themselves "
                        "are NOT date-keyed; this is the date stamped onto every "
                        "emitted entry.")
    p.add_argument("--company-drive-folder-url", default=None,
                   help="Drive folder URL (or bare ID) for the 기업 cohort.")
    p.add_argument("--industry-drive-folder-url", default=None,
                   help="Drive folder URL (or bare ID) for the 산업 cohort.")
    p.add_argument("--out", required=True,
                   help="Output JSON path. With --apply this file is written; "
                        "without --apply this script is dry-run and prints the "
                        "summary only. Refuses paths inside the repo under --apply.")
    p.add_argument("--max-company-pdfs", type=int, default=50,
                   help=f"Per-folder cap on company entries (HARD_MAX={HARD_MAX_PDFS}).")
    p.add_argument("--max-industry-pdfs", type=int, default=50,
                   help=f"Per-folder cap on industry entries (HARD_MAX={HARD_MAX_PDFS}).")
    p.add_argument("--download-dir", default=None,
                   help="If set, raw PDFs are downloaded under this dir. MUST live "
                        "outside the repo. Disabled by default (listing-only).")
    p.add_argument("--max-download-pdfs", type=int, default=0,
                   help="Cap on the total number of PDFs to download across both "
                        "company+industry. 0 disables downloads even if "
                        "--download-dir is set.")
    p.add_argument("--download-which", default="company",
                   help="Comma-separated subset of {company,industry} to download "
                        "from. Default: company. Use 'company,industry' for both.")
    p.add_argument("--listing-cache-dir", default=None,
                   help="(Offline mode) Read folder listings from "
                        "<dir>/<folder_id>.html instead of fetching from "
                        "drive.google.com. Used by tests and operators on hosts "
                        "without outbound network access.")
    p.add_argument("--download-cache-dir", default=None,
                   help="(Offline mode) Read raw PDF bytes from "
                        "<dir>/<file_id>.pdf instead of fetching.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Do not write --out; do not download PDFs.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize the inventory JSON at --out, and (if "
                        "--download-dir + --max-download-pdfs > 0) materialize "
                        "the requested PDFs.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.max_company_pdfs > HARD_MAX_PDFS or args.max_company_pdfs < 0:
        print(f"error: --max-company-pdfs must be 0..{HARD_MAX_PDFS} "
              f"(got {args.max_company_pdfs})", file=sys.stderr)
        return 2
    if args.max_industry_pdfs > HARD_MAX_PDFS or args.max_industry_pdfs < 0:
        print(f"error: --max-industry-pdfs must be 0..{HARD_MAX_PDFS} "
              f"(got {args.max_industry_pdfs})", file=sys.stderr)
        return 2
    if args.max_download_pdfs < 0 or args.max_download_pdfs > HARD_MAX_PDFS * 2:
        print(f"error: --max-download-pdfs must be 0..{HARD_MAX_PDFS * 2} "
              f"(got {args.max_download_pdfs})", file=sys.stderr)
        return 2

    if not (args.company_drive_folder_url or args.industry_drive_folder_url):
        print("error: at least one of --company-drive-folder-url / "
              "--industry-drive-folder-url must be set", file=sys.stderr)
        return 2

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        print(f"error: --date must be YYYY-MM-DD (got {args.date})", file=sys.stderr)
        return 2

    company_id = _extract_folder_id(args.company_drive_folder_url) \
        if args.company_drive_folder_url else None
    industry_id = _extract_folder_id(args.industry_drive_folder_url) \
        if args.industry_drive_folder_url else None
    if args.company_drive_folder_url and not company_id:
        print(f"error: cannot extract folder ID from "
              f"--company-drive-folder-url={args.company_drive_folder_url!r}",
              file=sys.stderr)
        return 2
    if args.industry_drive_folder_url and not industry_id:
        print(f"error: cannot extract folder ID from "
              f"--industry-drive-folder-url={args.industry_drive_folder_url!r}",
              file=sys.stderr)
        return 2

    out_path = Path(args.out).expanduser().resolve()
    if not args.dry_run and _is_inside_repo(out_path):
        print(f"error: --out must live outside the repo under --apply "
              f"(got {out_path})", file=sys.stderr)
        return 2

    download_dir: Path | None = None
    if args.download_dir:
        download_dir = Path(args.download_dir).expanduser().resolve()
        if not args.dry_run and _is_inside_repo(download_dir):
            print(f"error: --download-dir must live outside the repo under "
                  f"--apply (got {download_dir})", file=sys.stderr)
            return 2

    download_which_raw = (args.download_which or "").strip()
    download_which: list[str] = []
    if download_which_raw:
        for tok in download_which_raw.split(","):
            tok = tok.strip()
            if tok and tok not in ("company", "industry"):
                print(f"error: --download-which token must be company|industry "
                      f"(got {tok!r})", file=sys.stderr)
                return 2
            if tok:
                download_which.append(tok)

    listing_cache_dir = (Path(args.listing_cache_dir).expanduser().resolve()
                         if args.listing_cache_dir else None)
    download_cache_dir = (Path(args.download_cache_dir).expanduser().resolve()
                          if args.download_cache_dir else None)

    selected_company: list[dict] = []
    selected_industry: list[dict] = []
    malformed_all: list[dict] = []
    skipped_non_pdf_all: list[dict] = []
    duplicate_basename_all: list[dict] = []
    capped_company_count = 0
    capped_industry_count = 0

    def _safe_list(folder_id: str, folder_type: str, report_type: str,
                    max_pdfs: int) -> tuple[list[dict], list[dict], list[dict],
                                            list[dict], int, int]:
        try:
            return _list_drive_folder(
                folder_id,
                folder_type=folder_type,
                report_type=report_type,
                report_date=args.date,
                max_pdfs=max_pdfs,
                listing_cache_dir=listing_cache_dir,
            )
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            print(
                f"error: failed to fetch Drive folder listing for "
                f"folder_id={folder_id!r} ({folder_type}): "
                f"{type(exc).__name__}: {exc}\n"
                f"hint: this script needs outbound HTTPS to drive.google.com. "
                f"If your host blocks it, pre-fetch "
                f"https://drive.google.com/embeddedfolderview?id={folder_id} "
                f"on a network-allowed host, save as <DIR>/{folder_id}.html, "
                f"and re-run with --listing-cache-dir <DIR>.",
                file=sys.stderr,
            )
            raise SystemExit(4)
        except FileNotFoundError as exc:
            # `--listing-cache-dir` is set but the per-folder cache file is
            # missing. This is an expected operator-side input mistake, not
            # an internal crash, so it gets the same controlled exit-4 path
            # as a network failure (Codex review on PR #44).
            cache_path = listing_cache_dir / f"{folder_id}.html" \
                if listing_cache_dir else None
            print(
                f"error: listing cache miss for folder_id={folder_id!r} "
                f"({folder_type}): {exc}\n"
                f"hint: --listing-cache-dir is set, but the expected file "
                f"{cache_path} is missing. Either pre-fetch "
                f"https://drive.google.com/embeddedfolderview?id={folder_id} "
                f"into that path on a network-allowed host, or drop "
                f"--listing-cache-dir to fetch live from drive.google.com.",
                file=sys.stderr,
            )
            raise SystemExit(4)

    if company_id:
        (selected_company, mal, npdf, dup, _scanned_c, capped_c) = _safe_list(
            company_id, FOLDER_COMPANY, "company", args.max_company_pdfs,
        )
        malformed_all.extend(mal)
        skipped_non_pdf_all.extend(npdf)
        duplicate_basename_all.extend(dup)
        capped_company_count = capped_c

    if industry_id:
        (selected_industry, mal, npdf, dup, _scanned_i, capped_i) = _safe_list(
            industry_id, FOLDER_INDUSTRY, "industry", args.max_industry_pdfs,
        )
        malformed_all.extend(mal)
        skipped_non_pdf_all.extend(npdf)
        duplicate_basename_all.extend(dup)
        capped_industry_count = capped_i

    # Defensive guard: if any entry somehow carries direct_trade_signal=true
    # (cannot happen by construction — the field is always set to False
    # above — but we double-check before emit).
    for ent in selected_company + selected_industry:
        if ent.get("direct_trade_signal") is not False:
            print(f"error: refusing to emit entry with "
                  f"direct_trade_signal != False: {ent.get('filename')!r}",
                  file=sys.stderr)
            return 3

    # Optional download phase.
    downloaded_pdf_count = 0
    failed_download_count = 0
    files_with_download_errors: list[dict] = []

    if (not args.dry_run) and download_dir is not None and args.max_download_pdfs > 0:
        remaining = args.max_download_pdfs
        if "company" in download_which and selected_company and remaining > 0:
            d, f, errs = _attempt_downloads(
                selected_company, "기업", download_dir, download_cache_dir, remaining,
            )
            downloaded_pdf_count += d
            failed_download_count += f
            files_with_download_errors.extend(errs)
            remaining -= d
        if "industry" in download_which and selected_industry and remaining > 0:
            d, f, errs = _attempt_downloads(
                selected_industry, "산업", download_dir, download_cache_dir, remaining,
            )
            downloaded_pdf_count += d
            failed_download_count += f
            files_with_download_errors.extend(errs)
            remaining -= d

    summary = {
        "company_pdf_count": len(selected_company),
        "industry_pdf_count": len(selected_industry),
        "malformed_filename_count": len(malformed_all),
        "duplicate_basename_count": len(duplicate_basename_all),
        "skipped_non_pdf_count": len(skipped_non_pdf_all),
        "capped_company_count": capped_company_count,
        "capped_industry_count": capped_industry_count,
        "direct_trade_signal_true_count": 0,
        "selected_alias_count": len(selected_company),
        "selected_alias_matches_company": True,
        "downloaded_pdf_count": downloaded_pdf_count,
        "failed_download_count": failed_download_count,
        "files_with_download_errors": files_with_download_errors,
    }

    inventory = {
        "schema": INVENTORY_SCHEMA,
        "date": args.date,
        "company_drive_folder_id": company_id,
        "industry_drive_folder_id": industry_id,
        "max_company_pdfs": args.max_company_pdfs,
        "max_industry_pdfs": args.max_industry_pdfs,
        "download_dir": str(download_dir) if download_dir else None,
        "max_download_pdfs": args.max_download_pdfs,
        "download_which": list(download_which),
        "summary": summary,
        # Top-level alias of selected_company[] (PR #40 invariant carried
        # forward). Industry entries are NEVER folded in.
        "selected": list(selected_company),
        "selected_company": selected_company,
        "selected_industry": selected_industry,
        "malformed": malformed_all,
        "skipped_non_pdf": skipped_non_pdf_all,
        "duplicate_basename": duplicate_basename_all,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "drive_renames": 0,
            "drive_deletes": 0,
            "repo_writes": 0,
            "rolling_apply": 0,
            "promote_or_super_pack": 0,
            "direct_trade_signal_true": 0,
            "target_price_as_primary": 0,
            "pdf_body_text_committed": 0,
            "extracted_text_committed": 0,
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] date  = {args.date}")
    print(f"[{mode}] company_drive_folder_id  = {company_id}")
    print(f"[{mode}] industry_drive_folder_id = {industry_id}")
    print(f"[{mode}] download_dir   = {download_dir}")
    print(f"[{mode}] download_which = {download_which}")
    for k, v in summary.items():
        if k == "files_with_download_errors":
            print(f"[{mode}]   summary.{k:35s} = {len(v)} entries")
        else:
            print(f"[{mode}]   summary.{k:35s} = {v}")

    if args.dry_run:
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[APPLY] wrote {out_path}")
    print(f"[NEXT] feed selected_company entries to "
          f"`examples/run_inventory_batch_smoke.py --inventory <out>` if "
          f"the existing PR #29 chain runner is desired.")
    print(f"[NEXT] selected_industry entries are NOT fed to the parser; "
          f"they are queued for downstream LLM summarization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
