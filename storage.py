"""Local JSON persistence and analytics helpers for receipt records."""

from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
RECEIPTS_FILE = DATA_DIR / "receipts.json"


def load_receipts() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RECEIPTS_FILE.exists():
        return []
    try:
        content = json.loads(RECEIPTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return content if isinstance(content, list) else []


def save_receipts(receipts: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPTS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(RECEIPTS_FILE)


def add_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    records = load_receipts()
    saved = {**receipt, "id": str(uuid.uuid4()), "created_at": date.today().isoformat()}
    records.insert(0, saved)
    save_receipts(records)
    return saved


def delete_receipt(receipt_id: str) -> None:
    save_receipts([r for r in load_receipts() if r.get("id") != receipt_id])
