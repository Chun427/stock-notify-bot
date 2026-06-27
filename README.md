# 📲 股票推播機器人 · stock-notify-bot

> 透過 GitHub Actions 定時抓取台股 / 美股即時報價，自動推播到 Telegram Bot 與 LINE。

-----

## ✨ 功能特色

- 🇹🇼 **台股報價**：加權指數、元大台灣50、富邦台50、台積電
- 🇺🇸 **美股報價**：S&P500、VOO、QQQM、SMH、Apple、輝達、Google、TSMC ADR、SpaceX
- 📨 **雙管道推播**：同時支援 Telegram Bot 與 LINE Messaging API
- 🔕 **深夜靜音**：美股盤中、收盤自動靜音，不打擾睡眠
- 🌎 **DST 自動對齊**：美股以美東時間判斷，夏令／冬令自動切換，不會抓錯日期
- 🛡️ **固定標的**：台股固定 4 檔、美股固定 9 檔，單支抓取失敗仍保留位置，數量與順序永遠固定
- ⏱️ **±3 分鐘容錯**：GitHub Actions 延遲 6 分鐘內仍可正常推播
- 🛡️ **Fail-safe 設計**：任何錯誤不會讓 Actions 崩潰
- ⚙️ **手動補播**：`workflow_dispatch` 可隨時手動觸發指定市場與時段

-----

## 📌 標的清單（契約 · 凍結）

> ⚠️ 以下**顯示名稱**與**順序**為凍結契約，是推播輸出（formatter）與 `config.py` 的唯一真相來源。
> 不可修改、不可重新排序、不可增刪、不可語意翻譯（例：Google ↔ 谷歌）。
> 允許內部 ticker mapping / API fallback，但**不得影響任何對外顯示字串**。

### 🇹🇼 台股（固定 4 檔）

| # | 顯示名稱     | Ticker      |
|---|------------|-------------|
| 1 | 台灣加權指數 | `^TWII`     |
| 2 | 元大台灣50   | `0050.TW`   |
| 3 | 富邦台50     | `006208.TW` |
| 4 | 台積電       | `2330.TW`   |

### 🇺🇸 美股（固定 9 檔）

| # | 顯示名稱  | Ticker  |
|---|----------|---------|
| 1 | 標普500   | `^GSPC` |
| 2 | VOO      | `VOO`   |
| 3 | QQQM     | `QQQM`  |
| 4 | SMH      | `SMH`   |
| 5 | Apple    | `AAPL`  |
| 6 | 輝達      | `NVDA`  |
| 7 | Google   | `GOOGL` |
| 8 | TSMC ADR | `TSM`   |
| 9 | SpaceX   | `SPCX`  |

> 註：`SPCX` 自 2026-04-07 起指向 Space Exploration Technologies（SpaceX，Nasdaq）；舊「SPAC and New Issue ETF」已改 ticker 為 `SPCK`，與本標的無關。顯示名稱固定為 `SpaceX`。

-----

## 📅 自動推播排程

### 🇹🇼 台股（週一 ～ 週五，台北時間）

|台北時間 |說明  |
|-----|----|
|09:05|開盤快報|
|11:30|盤中午報|
|13:35|收盤報價|

### 🇺🇸 美股（週一 ～ 週五，以美東時間為準）

|美東時間 |台北時間（夏令）|台北時間（冬令）|說明  |備註  |
|-----|--------|--------|----|----|
|09:35|21:35   |22:35   |開盤快報|🔔   |
|12:00|00:00   |01:00   |盤中報價|🔕 靜音|
|16:05|04:05   |05:05   |收盤報價|🔕 靜音|


> 💡 美股推播時間以**美東時間**固定，台北對應時間會隨美國日光節約自動變動，確保永遠在美股實際交易時段推播。
> 
> ⚠️ GitHub Actions cron 通常有數分鐘延遲，本系統內建 ±3 分鐘容錯（cron 提前 3 分觸發，可容忍 6 分鐘內延遲）。

-----

## 🔄 系統運作流程

```
GitHub Actions cron 觸發（夏令 + 冬令各一組）
        ↓
main.py（orchestration 入口）
        ↓
判斷觸發模式：cron 或 manual
        ↓
cron：scheduler/calendar 提供時間真相（市場時區 / DST / 交易日）
      → core/decision 依容錯窗（±3 分鐘）判斷該不該推
      → 錯誤季節的 cron 自動跳過
        ↓
state/idempotency 檢查是否已推播（防重複）
        ↓
抓取股價（Yahoo Finance，period=5d，自動跳過 NaN K 棒）
        ↓
組合固定格式推播訊息（固定標的，失敗顯示 N/A）
        ↓
發送 Telegram（若有設定）
發送 LINE（若有設定）
        ↓
推播成功後 state/idempotency 標記已推
```

-----

## 📤 推播訊息範例

**🇹🇼 台股**

```
📊 台股報價・開盤
時間：06/01 09:05

🔴 台灣加權指數
   $21,845.32　+123.45（+0.57%）📈

🟢 元大台灣50
   $198.50　-1.20（-0.60%）📉
```

> 💡 台股顏色與美股相反（台灣習慣：🔴漲 🟢跌）

**🇺🇸 美股**

```
📊 美股報價・收盤
時間：06/01 04:05

🟢 標普500
   $5,432.10　+45.20（+0.84%）📈

🔴 輝達
   $1,087.50　-23.40（-2.11%）📉
```

-----

## 📤 推播格式契約（凍結）

> ⚠️ 以下為推播輸出的**逐字凍結契約**，`formatter.py` 只能套用、不可變動。
> 特殊字元：全形空格 `U+3000`、全形括號 `（）`、中點 `・`、全形冒號 `：`。

**整體結構**

```
📊 {台股|美股}報價・{slot_label}
時間：{MM/DD HH:MM}
（空行）
{block}
（空行）
{block}
```

**標頭**

- 市場標籤：`tw → 台股`、`us → 美股`
- slot 標籤：`open → 開盤`、`mid → 盤中`、`close → 收盤`
- 時間：**排程時間**，固定以**台北時區**顯示，格式 `%m/%d %H:%M`

**每檔 block（有資料）**

```
{color} {顯示名稱}
   ${price:,.2f}　{change:+,.2f}（{pct:+.2f}%）{trend}
```

- 縮排 = 3 個半形空格；數值千分位 + 2 位小數；漲跌與百分比帶正負號。
- `color`（行首）：台股 🔴漲／🟢跌；美股 🟢漲／🔴跌。
- `trend`（行尾）：📈漲／📉跌（兩市相同）。
- 漲跌判定：**`change ≥ 0` 視為漲**。

**每檔 block（N/A，單支抓取失敗時仍保留位置）**

```
⚪ {顯示名稱}
   N/A
```

-----

## 📁 專案結構

```
.
├── main.py                    # orchestration 入口（串接各層，不含決策細節）
├── config.py                  # 標的契約、常數設定（純資料）
├── core/
│   └── decision.py            # 決策層：該不該推 / 哪個市場 / 哪個時段（純邏輯）
├── scheduler/
│   └── calendar.py            # 時間真相來源：timezone / DST / 交易日 / 開收盤
├── data/
│   ├── fetcher.py             # Yahoo Finance 抓價（retry + NaN 過濾）
│   └── models.py              # StockQuote dataclass（含 NaN 檢查）
├── service/
│   └── quote_service.py       # 批次取得報價（固定標的保留順序）
├── notify/
│   ├── formatter.py           # 組合固定格式訊息（凍結契約）
│   ├── telegram_notifier.py   # 發送 Telegram
│   └── line_notifier.py       # 發送 LINE
├── state/
│   └── idempotency.py         # 防重複推播（已推 → SKIP）
├── utils/
│   └── logger.py              # 統一 log 格式
└── .github/
    └── workflows/
        └── stock-notify.yml   # GitHub Actions 排程（夏令+冬令雙 cron）
```

-----

## 🚀 快速開始

### 1. Fork / Clone 此 Repository

```bash
git clone https://github.com/<your-username>/stock-notify-bot.git
cd stock-notify-bot
```

### 2. 安裝套件（本機測試用）

```bash
pip install yfinance requests
```

### 3. 設定 GitHub Secrets

前往 repo → **Settings → Secrets and variables → Actions**：

#### Telegram（可選）

|Secret 名稱 |說明                |
|----------|------------------|
|`TG_TOKEN`|Telegram Bot Token|
|`TG_CHAT` |Telegram Chat ID  |

#### LINE Messaging API（可選）

|Secret 名稱   |說明                       |
|------------|-------------------------|
|`LINE_TOKEN`|LINE Channel Access Token|
|`LINE_ID`   |LINE 推播對象的 User ID       |

### 4. 本機測試

```bash
# cron 模式（會依市場時區檢查時間）
python main.py

# 手動模式（跳過時間檢查，直接推播）
TRIGGER=workflow_dispatch MARKET=tw TYPE=open  python main.py
TRIGGER=workflow_dispatch MARKET=tw TYPE=mid   python main.py
TRIGGER=workflow_dispatch MARKET=tw TYPE=close python main.py
TRIGGER=workflow_dispatch MARKET=us TYPE=open  python main.py
TRIGGER=workflow_dispatch MARKET=us TYPE=mid   python main.py
TRIGGER=workflow_dispatch MARKET=us TYPE=close python main.py
```

### 5. 手動補播

GitHub → **Actions → Stock Notify → Run workflow**

選擇市場（tw / us）和時段（open / mid / close）即可立即推播。

-----

## 🔑 取得推播憑證

### Telegram

1. 找 [@BotFather](https://t.me/BotFather) → `/newbot` → 取得 **Bot Token**
1. 將 Bot 加入頻道或群組
1. 瀏覽器開啟取得 Chat ID：

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

### LINE Messaging API

1. 前往 [LINE Developers Console](https://developers.line.biz/) → 建立 Messaging API Channel
1. 取得 **Channel Access Token**
1. 取得推播對象的 **User ID**

-----

## 🛡️ 穩定性機制

|機制       |說明                                 |
|---------|-----------------------------------|
|美股 DST 對齊|以美東時間判斷，夏令／冬令雙 cron，Python 自動篩選正確季節|
|±3 分鐘容錯  |cron 提前觸發，可容忍 GitHub 延遲 6 分鐘內      |
|固定標的     |台股 4 檔／美股 9 檔，單支抓取失敗保留位置顯示 N/A，數量與順序永遠固定|
|NaN 過濾   |開盤前資料未生成時自動取最近有效收盤，不會顯示 nan        |
|防重複      |idempotency 標記 + 同季節每時段僅一組 cron 命中，不會重複推播|

-----

## 🛡️ Fail-safe 機制

|錯誤情境         |處理方式          |Actions 是否崩潰|
|-------------|--------------|------------|
|單支股票抓取失敗     |保留位置顯示 N/A    |❌ 不崩潰       |
|全部股票抓取失敗     |log + 跳過推播    |❌ 不崩潰       |
|Telegram 發送失敗|log + continue|❌ 不崩潰       |
|LINE 發送失敗    |log + continue|❌ 不崩潰       |
|Secrets 未設定  |跳過對應管道        |❌ 不崩潰       |
|時間不符         |跳過推播          |❌ 不崩潰       |
|錯誤季節 cron    |自動跳過          |❌ 不崩潰       |

-----

## ⚠️ 已知限制

- **GitHub Actions cron 延遲**：免費版 cron 不保證準時，延遲超過 6 分鐘的單次推播會略過（屬平台限制，非程式問題）。
- **交易日僅判斷週一～週五**：未含台股／美股國定假日，休市日仍可能觸發（抓不到資料時顯示 N/A）。
- **yfinance per-call timeout**：以參數方式傳入，極端情況下不保證硬性中斷。
- 資料來源為 Yahoo Finance，可能有數分鐘延遲。

-----

## ⚠️ 免責聲明

本工具僅提供即時行情資訊，**不構成任何投資建議**。
資料來源為 Yahoo Finance，可能有延遲，請以官方交易所資料為準。
