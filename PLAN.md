# money_hpps — Plan & decisions (2026-11-21)

နောက်မှ ဆက်ရေးမယ့် အတွက် မှတ်တမ်း။ အခုအဆင့် Telegram mock bot အလုပ်လုပ်ပြီးသား။

## ပန်းတိုင် (လက်ရှိ သဘောတူချက်)

```
Staff (Telegram bot)  →  ငွေသွင်း/ထုတ် မှတ်  →  Google Sheet
Admin (Web dashboard) →  ကြည့် / ရှာ / အနှစ်ချုပ်     ↗
```

- ဝန်ထမ်း ~၄–၅ ယောက် (အများဆုံး ~၂၀ အထိ Hobby နဲ့ သက်သာနိုင်)
- Data source of truth: **Google Spreadsheet**
- Hosting: **Railway Hobby (~$5/လ)** — bot + dashboard တစ်ခုတည်းတင်လို့ရ
- တကယ့်ဘဏ်ချိတ်တာ မဟုတ် — ledger / မှတ်တမ်းသာ

## ပြီးပြီးသား

- Python Telegram bot: `/start` `/in` `/out` `/balance` `/history`
- Whitelist: `ALLOWED_TELEGRAM_IDS` နှင့်/သို့မဟုတ် `ALLOWED_TELEGRAM_USERNAMES`
- `MOCK_MODE=true` — Sheet မရှိဘဲ memory မှာ စမ်းနိုင် (restart ရင် ပျက်)
- Railway config (`Procfile`, `railway.toml`, health port)
- GitHub: https://github.com/tuntunutycc/money_hpps
- Bot: https://t.me/gurusavebot (username `gurusavebot`)
- စမ်းသုံး account: `@akmdeep` — mock နဲ့ ပြန်စာရပြီး

## နောက်အဆင့် (အစဉ်အတိုင်း)

1. **Google Sheets ချိတ်**
   - Spreadsheet + service account (Editor share)
   - Headers: `timestamp | staff_name | telegram_id | type | amount | note | balance`
   - Railway: `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`
   - `MOCK_MODE=false` (သို့မဟုတ် ဖျက်) → redeploy
   - Code ဘက် Sheets support ရေးပြီးသား (`sheets.py`)

2. **User management (Sheet `Users` tab)**
   - Columns ဥပမာ: `telegram_id | username | name | role | active`
   - Roles: `admin` / `staff`
   - staff = `/in` `/out` သာ; admin = ပိုမိုကြည့် / စီမံ
   - Env whitelist အစား Sheet ကနေ ဖတ် (env redeploy လျှော့)

3. **Admin web dashboard (read-first)**
   - Staff က bot နဲ့ပဲ ရေး; admin က browser မှ ကြည့်
   - Login မဖြစ်မနေထား
   - Railway မှာ bot နဲ့ service တစ်ခုတည်း သို့မဟုတ် web သီးခြား
   - Sheet ကနေ ဖတ်: လက်ကျန်၊ မှတ်တမ်း၊ filter

4. **နောက်မှ တိုးချင်ရင်**
   - ကြီးတဲ့ငွေ admin approve
   - `/undo` သို့မဟုတ် void row (ဖျက်မယ့်အစား)
   - နေ့စဉ်/လစဉ် summary bot က admin ကို ပို့
   - User ၅၀+ / ရေးချက်များရင် Sheet → Postgres စဉ်းစား

## Railway Variables (လက်ရှိ mock)

| Variable | တန်ဖိုး |
|----------|--------|
| `TELEGRAM_BOT_TOKEN` | BotFather token (`.env` မှာ local သိမ်း; git မထည့်) |
| `ALLOWED_TELEGRAM_USERNAMES` | `akmdeep` |
| `MOCK_MODE` | `true` |

Sheet ရရင် ထပ်ထည့်: `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, ပြီး `MOCK_MODE=false`။

## မလုပ်သေးရန် (အခုမလို)

- Full auth system / password per staff
- Database သီးသန့် (Sheet မလောက်မှ)
- Dashboard ကို staff ရေးရန် အဓိက လမ်းကြောင်းလုပ်ခြင်း

## ကိုးကား ဖိုင်များ

- `SETUP.md` — credential / Railway လုပ်နည်း
- `bot.py` / `sheets.py` / `config.py`
- `.env.example` — env နမူနာ (secrets မပါ)
