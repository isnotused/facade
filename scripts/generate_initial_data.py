"""Generate deterministic seed data for the Streamlit-based facade console."""

from __future__ import annotations

import json
from pathlib import Path

from facade.core import build_dataset

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "system_dataset.json"


def main() -> None:
    dataset = build_dataset()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(dataset, ensure_ascii=False, indent=2))
    print(f"Dataset generated at: {DATA_PATH}")


if __name__ == "__main__":
    main()

