#!/usr/bin/env python3
"""
Phase 3 — Promote `<output-root>/<date>/*` artifacts to `<output-root>/latest/`.

DOUBLE-GATED: --apply alone is REJECTED. Both --apply AND --confirm-promote
must be explicitly provided. Original files are preserved (copy, not move).

Super Pack regeneration is OUT OF SCOPE for this script and must be run
separately under explicit user approval.

CLI: --output-root, --date, --dry-run | --apply [--confirm-promote]
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

DEFAULT_OUTPUT = "./output"
SOURCE_KEY = "phase3:promote_report_outputs:v1"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output-root",
                   default=os.getenv("PHASE3_OUTPUT_ROOT") or DEFAULT_OUTPUT,
                   help=f"Output root (default: {DEFAULT_OUTPUT})")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Source date YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="first gate; insufficient by itself")
    p.add_argument("--confirm-promote", dest="confirm_promote", action="store_true",
                   default=False,
                   help="second gate; required together with --apply")
    return p.parse_args(argv)


def plan(src_dir: Path, latest_dir: Path) -> list[tuple[Path, Path]]:
    if not src_dir.exists():
        return []
    pairs: list[tuple[Path, Path]] = []
    for f in sorted(src_dir.rglob("*")):
        if f.is_dir():
            continue
        rel = f.relative_to(src_dir)
        pairs.append((f, latest_dir / rel))
    return pairs


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    out_root = Path(args.output_root).expanduser()
    src_dir = out_root / args.date
    latest_dir = out_root / "latest"
    pairs = plan(src_dir, latest_dir)

    mode = "DRY-RUN" if args.dry_run else ("APPLY" if args.confirm_promote else "GATE-CHECK")
    print(f"[{mode}] source     = {src_dir}")
    print(f"[{mode}] latest     = {latest_dir}")
    print(f"[{mode}] candidates = {len(pairs)} file(s)")
    for s, t in pairs[:8]:
        print(f"  - {s}  ->  {t}")
    if len(pairs) > 8:
        print(f"  ... (+{len(pairs) - 8} more)")

    if args.dry_run:
        print("[DRY-RUN] no promotion performed.")
        print("[NOTE] To actually promote, both --apply AND --confirm-promote are required.")
        print("[NOTE] Super Pack regeneration is OUT OF SCOPE; run separately.")
        return 0

    if not args.confirm_promote:
        print("error: --apply requires --confirm-promote (double-gated promotion).", file=sys.stderr)
        print("       Re-run with: --apply --confirm-promote", file=sys.stderr)
        return 2

    if not pairs:
        print("[APPLY] nothing to promote.")
        return 0

    latest_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f"[APPLY] promoted {copied} file(s) (originals preserved at {src_dir})")
    print("[NOTE] Super Pack regeneration is OUT OF SCOPE; run separately under explicit approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
