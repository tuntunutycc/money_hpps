"""Google Spreadsheet ledger helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "timestamp",
    "staff_name",
    "telegram_id",
    "type",
    "amount",
    "note",
    "balance",
]


class Ledger:
    def __init__(self) -> None:
        info = config.load_service_account_info()
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(config.GOOGLE_SHEETS_ID)
        try:
            self.worksheet = spreadsheet.worksheet(config.GOOGLE_SHEET_NAME)
        except gspread.WorksheetNotFound:
            self.worksheet = spreadsheet.sheet1
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        first_row = self.worksheet.row_values(1)
        if not first_row:
            self.worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
            return
        # If header cells are missing/mismatched, leave existing data alone.

    def _all_records(self) -> list[dict[str, Any]]:
        rows = self.worksheet.get_all_values()
        if len(rows) <= 1:
            return []
        headers = [h.strip().lower() for h in rows[0]]
        records: list[dict[str, Any]] = []
        for row in rows[1:]:
            padded = row + [""] * (len(headers) - len(row))
            records.append(dict(zip(headers, padded[: len(headers)])))
        return records

    @staticmethod
    def _parse_amount(value: str | int | float) -> float:
        if value is None or value == "":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).replace(",", "").replace(" ", "").strip()
        if not cleaned:
            return 0.0
        return float(cleaned)

    def get_balance(self) -> float:
        records = self._all_records()
        if not records:
            return 0.0
        last = records[-1]
        if last.get("balance", "") != "":
            try:
                return self._parse_amount(last["balance"])
            except ValueError:
                pass
        # Fallback: recompute from all rows
        balance = 0.0
        for rec in records:
            try:
                amount = self._parse_amount(rec.get("amount", 0))
            except ValueError:
                continue
            tx_type = str(rec.get("type", "")).strip().lower()
            if tx_type == "in":
                balance += amount
            elif tx_type == "out":
                balance -= amount
        return balance

    def add_transaction(
        self,
        *,
        staff_name: str,
        telegram_id: int,
        tx_type: str,
        amount: float,
        note: str,
    ) -> float:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if tx_type not in ("in", "out"):
            raise ValueError("type must be 'in' or 'out'")

        current = self.get_balance()
        new_balance = current + amount if tx_type == "in" else current - amount
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        self.worksheet.append_row(
            [
                timestamp,
                staff_name,
                str(telegram_id),
                tx_type,
                amount,
                note,
                new_balance,
            ],
            value_input_option="USER_ENTERED",
        )
        return new_balance

    def recent(self, limit: int = 5) -> list[dict[str, Any]]:
        records = self._all_records()
        return records[-limit:] if records else []
