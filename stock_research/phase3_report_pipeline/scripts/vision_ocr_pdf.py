#!/usr/bin/env python3
"""
Phase 3 — Vision OCR for PDFs (Anthropic Vision via SDK).

SAFETY DEFAULTS:
- --dry-run by default → NO API calls, only prints the planned request shape.
- --apply attempts real calls; requires the API key to be present in the
  environment variable named by --api-key-env (default ANTHROPIC_API_KEY).
- API key is NEVER accepted as a CLI argument.
- Default page limit is 5; bypass with --max-pages.
- The anthropic SDK is imported lazily so --help and --dry-run work even
  when the package isn't installed.
- estimate mode extracts ONLY page 1 to a temporary single-page PDF
  before sending to the API. The full PDF is NEVER transmitted. The
  temp file is removed in a finally block. This requires `pypdf`
  (lazy-imported; install with `pip install pypdf`).

Modes (--extract-mode):
- raw       (default) per-page text dump.
            Output: [{pdf, page, text, model, usage_tokens}, ...]
- estimate  page-1 structured extraction of broker / old_target /
            new_target / horizon for downstream merge_meta.py.
            Forces page=1 (single API call per PDF). Sends ONLY page 1
            (extracted to a temp PDF) to the API; full PDF is NOT sent.
            Output: [{source_pdf_sha256, filename, page, broker,
                      old_target, new_target, horizon, model,
                      confidence, extraction_method, raw_text_excerpt,
                      extracted_at, payload_bytes_sent,
                      original_pdf_bytes}]
            Shape matches examples/structured_extraction.example.json.

Written to --output if given, else stdout.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_PAGES = 5
DEFAULT_API_KEY_ENV = "ANTHROPIC_API_KEY"

ESTIMATE_PROMPT = """You are a financial-report parser. From the FIRST PAGE of the
attached Korean broker research PDF, extract the investment-opinion box and
return ONLY a single JSON object with these keys:

- broker     (string, Korean brokerage name; null if not visible)
- old_target (number, KRW; null if not stated or 'N/A')
- new_target (number, KRW; null if not stated or 'N/A')
- horizon    (string, e.g. "12M" / "6M"; null if not stated)
- confidence (number 0..1 indicating how clearly the four fields were stated)

Rules:
* Use Korean stock-market conventions; KRW values are integers.
* Do NOT guess. If a field is not on page 1, return null and lower confidence.
* Output ONLY the JSON object. No prose. No markdown fences.
"""


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pdf", required=True, help="Path to input PDF")
    p.add_argument("--pages", default=None,
                   help="Page range, e.g. '1-3' or '2,4,7' (1-indexed). "
                        "If omitted, first --max-pages pages are used.")
    p.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                   help=f"Hard cap on processed pages (default: {DEFAULT_MAX_PAGES})")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Vision-capable Claude model (default: {DEFAULT_MODEL})")
    p.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV,
                   help=f"Env var that holds the API key (default: {DEFAULT_API_KEY_ENV}). "
                        "API key is never accepted as a CLI arg.")
    p.add_argument("--output", default=None,
                   help="Write JSON list to this path; default = stdout")
    p.add_argument("--extract-mode", choices=["raw", "estimate"], default="raw",
                   help="raw (default): per-page text dump. estimate: page-1 "
                        "structured extraction of broker/old_target/new_target/horizon.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) plan only; NO API calls")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="actually call the Vision API (requires API key in env)")
    return p.parse_args(argv)


def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


def _strip_json_fences(text: str) -> str:
    """Remove leading ```json / ``` and trailing ``` fences if present."""
    s = text.strip()
    if s.startswith("```"):
        nl = s.find("\n")
        s = s[nl + 1:] if nl != -1 else s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _extract_page1_pdf(src_path: Path) -> Path:
    """Write a temp 1-page PDF containing only page 1 of src and return its path.

    Caller MUST unlink the returned path (call_vision_estimate does so in finally).
    Lazy-imports `pypdf`; raises RuntimeError if pypdf is not installed.
    """
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for --extract-mode estimate. "
            "Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(src_path))
    if len(reader.pages) == 0:
        raise RuntimeError(f"PDF has 0 pages: {src_path}")

    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    fd, tmp = tempfile.mkstemp(prefix="phase3_p1_", suffix=".pdf")
    os.close(fd)
    out_path = Path(tmp)
    with out_path.open("wb") as f:
        writer.write(f)
    return out_path


def call_vision_estimate(pdf_path: Path, model: str, api_key: str) -> dict:
    """Single page-1 structured-extraction call.

    Sends ONLY page 1 (extracted to a temp single-page PDF) to the API.
    The full PDF is never transmitted. The temp file is cleaned up
    in a finally block.
    """
    page1_path: Path | None = None
    try:
        page1_path = _extract_page1_pdf(pdf_path)
        page1_bytes = page1_path.read_bytes()
        original_sha = sha256_of(pdf_path)
        original_size = pdf_path.stat().st_size

        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "anthropic SDK is not installed. Install with: pip install anthropic"
            ) from exc

        client = Anthropic(api_key=api_key)
        pdf_b64 = base64.standard_b64encode(page1_bytes).decode("ascii")

        msg = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                        "context": "This is page 1 only of a Korean broker research report.",
                    },
                    {"type": "text", "text": ESTIMATE_PROMPT},
                ],
            }],
        )
        raw_full = "".join(getattr(b, "text", "") for b in (msg.content or []))
        raw = _strip_json_fences(raw_full)
        parsed: dict = {"broker": None, "old_target": None, "new_target": None,
                        "horizon": None, "confidence": 0.0}
        parse_error: str | None = None
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                parsed.update({k: loaded.get(k) for k in parsed.keys()})
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
            parsed["confidence"] = 0.0

        usage = getattr(msg, "usage", None)
        return {
            "source_pdf_sha256": original_sha,
            "filename": pdf_path.name,
            "page": 1,
            "broker": parsed.get("broker"),
            "old_target": parsed.get("old_target"),
            "new_target": parsed.get("new_target"),
            "horizon": parsed.get("horizon"),
            "confidence": float(parsed.get("confidence") or 0.0),
            "extraction_method": "vision_ocr_estimate",
            "model": model,
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_text_excerpt": raw[:200] if not parse_error else f"[parse_error:{parse_error[:60]}]",
            "payload_bytes_sent": len(page1_bytes),
            "original_pdf_bytes": original_size,
            "usage_tokens": {
                "input": getattr(usage, "input_tokens", None),
                "output": getattr(usage, "output_tokens", None),
            },
        }
    finally:
        if page1_path is not None and page1_path.exists():
            try:
                page1_path.unlink()
            except OSError:
                pass


def parse_pages_spec(spec: str | None, max_pages: int) -> list[int]:
    if not spec:
        return list(range(1, max_pages + 1))
    pages: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(chunk))
    pages = sorted(set(p for p in pages if p >= 1))
    return pages[:max_pages]


def call_vision(pdf_path: Path, pages: list[int], model: str, api_key: str) -> list[dict]:
    """Issue per-page Vision requests. Imported lazily so --help works without SDK."""
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "anthropic SDK is not installed. Install with: pip install anthropic"
        ) from exc

    client = Anthropic(api_key=api_key)
    pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")

    out: list[dict] = []
    for page in pages:
        msg = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                        "context": f"Extract page {page}.",
                    },
                    {
                        "type": "text",
                        "text": (
                            f"You are an OCR engine. Extract the full text of page {page} "
                            "of the attached PDF. Output the raw text only, no commentary."
                        ),
                    },
                ],
            }],
        )
        text = "".join(getattr(b, "text", "") for b in (msg.content or []))
        usage = getattr(msg, "usage", None)
        out.append({
            "pdf": str(pdf_path),
            "page": page,
            "text": text,
            "model": model,
            "usage_tokens": {
                "input": getattr(usage, "input_tokens", None),
                "output": getattr(usage, "output_tokens", None),
            },
        })
    return out


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    pdf_path = Path(args.pdf).expanduser()
    if not pdf_path.exists():
        print(f"error: --pdf not found: {pdf_path}", file=sys.stderr)
        return 2

    if args.extract_mode == "estimate":
        pages = [1]
        if args.pages:
            print("[NOTE] --pages is ignored under --extract-mode estimate (forced page=1).",
                  file=sys.stderr)
    else:
        pages = parse_pages_spec(args.pages, args.max_pages)
        if not pages:
            print("error: no pages selected", file=sys.stderr)
            return 2

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] pdf          = {pdf_path}")
    print(f"[{mode}] extract_mode = {args.extract_mode}")
    print(f"[{mode}] pages        = {pages}")
    print(f"[{mode}] model        = {args.model}")
    print(f"[{mode}] api_key_env  = {args.api_key_env}  (value NOT printed)")
    print(f"[{mode}] expected api calls = {len(pages)}")

    if args.dry_run:
        if args.extract_mode == "estimate":
            print("[DRY-RUN] estimate mode: would extract page 1 to a temp 1-page PDF and "
                  "send ONLY that to the API.")
            print("[DRY-RUN] full PDF is NOT transmitted. Temp file auto-cleanup in finally.")
            print("[DRY-RUN] runtime dependency for --apply: pypdf (pip install pypdf)")
            print("[DRY-RUN] expected output schema matches "
                  "examples/structured_extraction.example.json.")
        print("[DRY-RUN] no API call performed. Re-run with --apply to invoke Vision.")
        return 0

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        print(f"error: env var {args.api_key_env} is not set; refusing to call API.", file=sys.stderr)
        return 2

    try:
        if args.extract_mode == "estimate":
            results = [call_vision_estimate(pdf_path, args.model, api_key)]
        else:
            results = call_vision(pdf_path, pages, args.model, api_key)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        out_path = Path(args.output).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"[APPLY] wrote {out_path}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
