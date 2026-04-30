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

Output (JSON list, one entry per page):
    [{pdf, page, text, model, usage_tokens}, ...]
Written to --output if given, else stdout.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import List

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_PAGES = 5
DEFAULT_API_KEY_ENV = "ANTHROPIC_API_KEY"


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
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) plan only; NO API calls")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="actually call the Vision API (requires API key in env)")
    return p.parse_args(argv)


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

    pages = parse_pages_spec(args.pages, args.max_pages)
    if not pages:
        print("error: no pages selected", file=sys.stderr)
        return 2

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] pdf       = {pdf_path}")
    print(f"[{mode}] pages     = {pages}")
    print(f"[{mode}] model     = {args.model}")
    print(f"[{mode}] api_key_env = {args.api_key_env}  (value NOT printed)")
    print(f"[{mode}] expected api calls = {len(pages)}")

    if args.dry_run:
        print("[DRY-RUN] no API call performed. Re-run with --apply to invoke Vision.")
        return 0

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        print(f"error: env var {args.api_key_env} is not set; refusing to call API.", file=sys.stderr)
        return 2

    try:
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
