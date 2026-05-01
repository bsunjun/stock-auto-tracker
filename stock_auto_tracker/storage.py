from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from stock_auto_tracker.models import SnapshotRow


def save_snapshot(rows: list[SnapshotRow], output_dir: str | Path = "output/snapshots") -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"portfolio_snapshot_{stamp}.csv"
    json_path = output_dir / f"portfolio_snapshot_{stamp}.json"

    records = [asdict(row) for row in rows]

    pd.DataFrame(records).to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    latest_csv = output_dir / "latest.csv"
    latest_json = output_dir / "latest.json"

    pd.DataFrame(records).to_csv(latest_csv, index=False, encoding="utf-8-sig")
    latest_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    return csv_path, json_path
