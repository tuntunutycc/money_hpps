"""Ledger backends: Google Spreadsheet or in-memory mock."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Protocol

import config

logger = logging.getLogger(__name__)

HEADERS = [
    "timestamp",
    "staff_name",
    "telegram_id",
    "type",
    "amount",
    "note",
    "balance",
]


class LedgerProtocol(Protocol):
    def get_balance(self) -> float: ...

    def add_transaction(
        self,
        *,
        staff_name: str,
        telegram_id: int,
        tx_type: str,
        amount: float,
        note: str,
    ) -> float: ...

    def recent(self, limit: int = 5) -> list[dict[str, Any]]: ...


def _parse_amount(value: str | int | float | None) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "").replace(" ", "").strip()
    if not cleaned:
        return 0.0
    return float(cleaned)


def _new_row(
    *,
    staff_name: str,
    telegram_id: int,
    tx_type: str,
    amount: float,
    note: str,
    balance: float,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "staff_name": staff_name,
        "telegram_id": str(telegram_id),
        "type": tx_type,
        "amount": amount,
        "note": note,
        "balance": balance,
    }


class MemoryLedger:
    """In-memory ledger for testing without Google Sheets.

    Data is lost when the process restarts.
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []
        logger.warning("MOCK_MODE: using in-memory ledger (not saved to Sheets)")

    def get_balance(self) -> float:
        if not self._rows:
            return 0.0
        return _parse_amount(self._rows[-1]["balance"])

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
        self._rows.append(
            _new_row(
                staff_name=staff_name,
                telegram_id=telegram_id,
                tx_type=tx_type,
                amount=amount,
                note=note,
                balance=new_balance,
            )
        )
        return new_balance

    def recent(self, limit: int = 5) -> list[dict[str, Any]]:
        return self._rows[-limit:] if self._rows else []


class SheetsLedger:
    def __init__(self) -> None:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        info = config.load_service_account_info()
        creds = Credentials.from_service_account_info(info, scopes=scopes)
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

    def get_balance(self) -> float:
        records = self._all_records()
        if not records:
            return 0.0
        last = records[-1]
        if last.get("balance", "") != "":
            try:
                return _parse_amount(last["balance"])
            except ValueError:
                pass
        balance = 0.0
        for rec in records:
            try:
                amount = _parse_amount(rec.get("amount", 0))
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


# Backwards-compatible name used by older imports
Ledger = SheetsLedger


def create_ledger() -> LedgerProtocol:
    if config.MOCK_MODE:
        return MemoryLedger()
    return SheetsLedger()
