"""JSON file persistence for SyncCents data."""

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_DATA_PATH = Path(__file__).parent.parent / "data" / "synccents.json"


def load_data(path: Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    if not path.exists():
        return _empty_state()
    with open(path, "r") as f:
        return json.load(f)


def save_data(state: dict[str, Any], path: Path = DEFAULT_DATA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def _empty_state() -> dict[str, Any]:
    return {
        "enrolled": False,
        "monthly_income": 3500.0,
        "checking_balance": 1247.83,
        "savings_balance": 0.0,
        "min_balance_threshold": 500.0,
        "daily_contribution_cents": 50,
        "deposit_cents": 50,
        "expenses": [],
        "auto_deposits": [],
        "total_auto_saved": 0.0,
        "enrolled_at": None,
    }
