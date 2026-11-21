# money_hpps

Telegram bot for staff cash in/out logging to Google Spreadsheet.

## Commands

| Command | Example | Meaning |
|---------|---------|---------|
| `/in` | `/in 50000 လစာ` | Deposit |
| `/out` | `/out 10000 ကုန်ကျ` | Withdrawal |
| `/balance` | `/balance` | Current balance |
| `/history` | `/history` | Last 5 entries |

Only Telegram user IDs listed in `ALLOWED_TELEGRAM_IDS` can use the bot.

## Quick start (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env + place service_account.json
python bot.py
```

## Deploy (Railway)

See [SETUP.md](SETUP.md) for Telegram, Google Cloud, and Railway steps.

Set these variables on Railway:

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_IDS`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

Start command: `python bot.py`
