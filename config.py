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


def _truthy(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


TELEGRAM_BOT_TOKEN = _required("TELEGRAM_BOT_TOKEN")

ALLOWED_TELEGRAM_IDS: set[int] = set()
for part in _split_csv(os.getenv("ALLOWED_TELEGRAM_IDS", "")):
    ALLOWED_TELEGRAM_IDS.add(int(part))

ALLOWED_TELEGRAM_USERNAMES: set[str] = set()
for part in _split_csv(os.getenv("ALLOWED_TELEGRAM_USERNAMES", "")):
    ALLOWED_TELEGRAM_USERNAMES.add(part.lstrip("@").lower())

if not ALLOWED_TELEGRAM_IDS and not ALLOWED_TELEGRAM_USERNAMES:
    raise RuntimeError(
        "Set ALLOWED_TELEGRAM_IDS and/or ALLOWED_TELEGRAM_USERNAMES"
    )

# MOCK_MODE=true → store ledger in memory (no Google Sheets needed)
MOCK_MODE = _truthy("MOCK_MODE")

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "").strip()
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1").strip() or "Sheet1"

if not MOCK_MODE and not GOOGLE_SHEETS_ID:
    raise RuntimeError(
        "Set GOOGLE_SHEETS_ID, or set MOCK_MODE=true to test without Sheets"
    )


def is_allowed_user(*, user_id: int, username: str | None) -> bool:
    if user_id in ALLOWED_TELEGRAM_IDS:
        return True
    if username and username.lower() in ALLOWED_TELEGRAM_USERNAMES:
        return True
    return False


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
