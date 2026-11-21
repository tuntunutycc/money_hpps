# Credential setup (သင်ကိုယ်တိုင် လုပ်ရမယ့်အပိုင်း)

## အရင် Telegram ပဲ စမ်းချင်ရင် (MOCK)

Railway Variables မှာ ဒီ ၃ ခုပဲ ထည့်:

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_IDS`
- `MOCK_MODE` = `true`

Sheet မလိုသေးဘူး။ မှတ်တမ်းက memory ထဲပဲ — redeploy/restart ရင် ပျက်မယ်။  
Sheet ရရင် `MOCK_MODE` ဖျက် (သို့မဟုတ် `false`) ပြီး Google vars ထည့်။

---

အောက်ပါက Sheet ချိတ်မယ့် အပြည့်အစုံ setup:

## 1. Telegram Bot Token + Staff IDs

1. Telegram မှာ [@BotFather](https://t.me/BotFather) ဖွင့် → `/newbot`
2. Bot အမည်ပေး → ရလာတဲ့ **token** ကို `TELEGRAM_BOT_TOKEN` ထဲထည့်
3. ဝန်ထမ်း တစ်ယောက်ချင်း [@userinfobot](https://t.me/userinfobot) ကို ဖွင့် → **Id** ကိုယူ
4. IDs များကို `ALLOWED_TELEGRAM_IDS` ထဲ ထည့် (comma ခြား)  
   ဥပမာ: `111111111,222222222`

## 2. Google Spreadsheet

1. [Google Sheets](https://sheets.google.com) မှာ sheet အသစ်ဖန်တီး (ဥပမာ `money_hpps`)
2. ပထမ row မှာ header ထား:

| timestamp | staff_name | telegram_id | type | amount | note | balance |
|-----------|------------|-------------|------|--------|------|---------|

3. URL ထဲက ID ကို `GOOGLE_SHEETS_ID` ထဲထည့်  
   `https://docs.google.com/spreadsheets/d/`**`SPREADSHEET_ID`**`/edit`

## 3. Google Cloud Service Account

1. [Google Cloud Console](https://console.cloud.google.com/) → project အသစ်
2. **APIs & Services → Library** → **Google Sheets API** → Enable
3. **IAM & Admin → Service Accounts** → Create  
   - Key → Add key → JSON → download
4. JSON ထဲက `client_email` ကို Spreadsheet မှာ **Share → Editor** ပေး
5. Railway / `.env` မှာ:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` = JSON တစ်ကြောင်းလုံး၊ သို့မဟုတ်
   - local အတွက် `GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json`

## 4. Railway (၂၄ နာရီ)

1. [railway.app](https://railway.app/) အကောင့်ဖွင့် (GitHub ချိတ်)
2. New Project → Deploy from GitHub (ဒီ repo)
3. Variables ထဲ env များထည့်:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_TELEGRAM_IDS`
   - `GOOGLE_SHEETS_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (JSON တစ်ကြောင်း)
4. Deploy ပြီး bot ကို Telegram မှာ `/start` ပို့ပြီး စမ်း
