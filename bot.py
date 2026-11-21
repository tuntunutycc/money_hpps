"""Telegram bot for cash in/out ledger backed by Google Spreadsheet."""

from __future__ import annotations

import logging
import os
import threading
from functools import wraps
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Awaitable, Callable

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from sheets import Ledger

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ledger = Ledger()


def _start_health_server() -> None:
    """Bind $PORT so Railway (and similar hosts) keep the service alive."""
    port = int(os.getenv("PORT", "8080"))

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health server on port %s", port)


def allowed_only(
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None or user.id not in config.ALLOWED_TELEGRAM_IDS:
            if update.message:
                await update.message.reply_text(
                    "သင့်မှာ ဒီ bot သုံးခွင့် မရှိပါ။ Admin ကို ဆက်သွယ်ပါ။"
                )
            return
        await handler(update, context)

    return wrapper


def _staff_name(update: Update) -> str:
    user = update.effective_user
    if user is None:
        return "unknown"
    return user.full_name or user.username or str(user.id)


def _parse_amount_and_note(args: list[str]) -> tuple[float, str]:
    if not args:
        raise ValueError("ပမာဏ ထည့်ပေးပါ။ ဥပမာ: /in 50000 လစာ")
    amount = float(args[0].replace(",", ""))
    if amount <= 0:
        raise ValueError("ပမာဏသည် ၀ ထက် ကြီးရမယ်။")
    note = " ".join(args[1:]).strip() or "-"
    return amount, note


def _format_money(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


@allowed_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ငွေစာရင်း bot မှ ကြိုဆိုပါတယ်။\n\n"
        "အမိန့်များ:\n"
        "/in <ပမာဏ> [မှတ်ချက်] — ငွေသွင်း\n"
        "/out <ပမာဏ> [မှတ်ချက်] — ငွေထုတ်\n"
        "/balance — လက်ကျန်\n"
        "/history — နောက်ဆုံး ၅ ခု"
    )


@allowed_only
async def cmd_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        amount, note = _parse_amount_and_note(context.args or [])
        balance = ledger.add_transaction(
            staff_name=_staff_name(update),
            telegram_id=update.effective_user.id,
            tx_type="in",
            amount=amount,
            note=note,
        )
        await update.message.reply_text(
            f"✅ သွင်း: {_format_money(amount)}\n"
            f"မှတ်ချက်: {note}\n"
            f"လက်ကျန်: {_format_money(balance)}"
        )
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
    except Exception:
        logger.exception("Failed /in")
        await update.message.reply_text("❌ Spreadsheet ရေးမရပါ။ နောက်မှ ထပ်ကြိုးစားပါ။")


@allowed_only
async def cmd_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        amount, note = _parse_amount_and_note(context.args or [])
        balance = ledger.add_transaction(
            staff_name=_staff_name(update),
            telegram_id=update.effective_user.id,
            tx_type="out",
            amount=amount,
            note=note,
        )
        await update.message.reply_text(
            f"✅ ထုတ်: {_format_money(amount)}\n"
            f"မှတ်ချက်: {note}\n"
            f"လက်ကျန်: {_format_money(balance)}"
        )
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
    except Exception:
        logger.exception("Failed /out")
        await update.message.reply_text("❌ Spreadsheet ရေးမရပါ။ နောက်မှ ထပ်ကြိုးစားပါ။")


@allowed_only
async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        balance = ledger.get_balance()
        await update.message.reply_text(f"💰 လက်ကျန်: {_format_money(balance)}")
    except Exception:
        logger.exception("Failed /balance")
        await update.message.reply_text("❌ လက်ကျန် မဖတ်နိုင်ပါ။")


@allowed_only
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rows = ledger.recent(5)
        if not rows:
            await update.message.reply_text("မှတ်တမ်း မရှိသေးပါ။")
            return
        lines = ["📋 နောက်ဆုံး ၅ ခု:"]
        for r in rows:
            ts = r.get("timestamp", "")
            tx = r.get("type", "")
            amt = r.get("amount", "")
            note = r.get("note", "")
            staff = r.get("staff_name", "")
            bal = r.get("balance", "")
            sign = "+" if tx == "in" else "-" if tx == "out" else tx
            lines.append(
                f"• {ts} | {sign}{amt} | {note} | {staff} | bal {bal}"
            )
        await update.message.reply_text("\n".join(lines))
    except Exception:
        logger.exception("Failed /history")
        await update.message.reply_text("❌ မှတ်တမ်း မဖတ်နိုင်ပါ။")


def main() -> None:
    _start_health_server()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("in", cmd_in))
    app.add_handler(CommandHandler("out", cmd_out))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("history", cmd_history))
    logger.info("Bot starting (polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
