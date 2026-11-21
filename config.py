"""Load configuration from environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


TELEGRAM_BOT_TOKEN = _required("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEETS_ID = _required("GOOGLE_SHEETS_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1").strip() or "Sheet1"

_raw_ids = _required("ALLOWED_TELEGRAM_IDS")
ALLOWED_TELEGRAM_IDS: set[int] = set()
for part in _raw_ids.split(","):
    part = part.strip()
    if part:
        ALLOWED_TELEGRAM_IDS.add(int(part))

if not ALLOWED_TELEGRAM_IDS:
    raise RuntimeError("ALLOWED_TELEGRAM_IDS must contain at least one Telegram user ID")


def load_service_account_info() -> dict:
    """Return service-account credentials dict from env JSON or file path."""
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw_json:
        return json.loads(raw_json)

    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    if file_path:
        path = Path(file_path)
        if not path.is_file():
            raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_FILE not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    raise RuntimeError(
        "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE"
    )
