# 📲 股票推播機器人 · stock-notify-bot

> 一個自動化的**股市行情推播機器人**：在台股與美股的每個交易時段（開盤／盤中／收盤），
> 自動抓取關注標的的即時報價，整理成固定格式推送到你的 **Telegram 與 LINE**——
> 不用盯盤，也能準時掌握行情。

## 目錄

- [功能特色](#功能特色)
- [標的清單（契約 · 凍結）](#標的清單契約--凍結)
- [自動推播排程](#自動推播排程)
- [觸發架構](#觸發架構)
- [交易日判斷](#交易日判斷)
- [系統運作流程](#系統運作流程)
- [推播訊息範例](#推播訊息範例)
- [推播格式契約（凍結）](#推播格式契約凍結)
- [專案結構](#專案結構)
- [快速開始](#快速開始)
- [取得推播憑證](#取得推播憑證)
- [穩定性機制](#穩定性機制)
- [Fail-safe 機制](#fail-safe-機制)
- [故障排查（Troubleshooting）](#故障排查troubleshooting)
- [已知限制](#已知限制)
- [Release Notes](#release-notes)
- [免責聲明](#免責聲明)

-----


## 功能特色

- ⚡ **事件驅動 · 延遲免疫**：觸發端直接指定市場／時段，延遲多久觸發都照推，不再有時間窗漏推
- ⏰ **外部 GAS 準時觸發**：Google Apps Script 定時打 `repository_dispatch`，為**唯一正式入口**（GitHub cron 已停用）
- 📅 **交易日判斷**：GAS 端過濾週末與假日清單，非交易日不送 dispatch，避免無效推播
- 🇹🇼 **台股報價**：加權指數、元大台灣50、富邦台50、主動統一台股增長、台積電
- 🇺🇸 **美股報價**：S&P500、VOO、QQQM、SMH、Apple、輝達、Google、TSMC ADR、SpaceX
- 📨 **雙管道推播**：同時支援 Telegram Bot 與 LINE Messaging API
- 🔕 **深夜靜音**：美股盤中、收盤自動靜音，不打擾睡眠
- 🌎 **DST 自動對齊**：美股以美東時間為準，夏令／冬令由時區自動換算，永遠不會錯時
- 🛡️ **固定標的**：台股固定 5 檔、美股固定 9 檔，單支抓取失敗仍保留位置，數量與順序永遠固定
- 🛡️ **Fail-safe 設計**：任何錯誤不會讓 Actions 崩潰

-----

## 標的清單（契約 · 凍結）

> ⚠️ 以下**顯示名稱**與**順序**為凍結契約，是推播輸出（formatter）與 `config.py` 的唯一真相來源。
> 不可修改、不可重新排序、不可語意翻譯（例：Google ↔ 谷歌）。
> 允許內部 ticker mapping / API fallback，但**不得影響任何對外顯示字串**。

### 🇹🇼 台股（固定 5 檔）

| # | 顯示名稱         | Ticker      |
|---|----------------|-------------|
| 1 | 台灣加權指數     | `^TWII`     |
| 2 | 元大台灣50       | `0050.TW`   |
| 3 | 富邦台50         | `006208.TW` |
| 4 | 主動統一台股增長 | `00981A.TW` |
| 5 | 台積電           | `2330.TW`   |

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

> 註：`SPCX` 自 2026-04-07 起指向 Space Exploration Technologies（SpaceX，Nasdaq）；顯示名稱固定為 `SpaceX`。

-----

## 自動推播排程

### 🇹🇼 台股（週一 ～ 週五，台北時間）

|台北時間 |說明  |
|-----|----|
|09:05|開盤快報|
|11:30|盤中午報|
|13:35|收盤報價|

### 🇺🇸 美股（週一 ～ 週五，以美東時間為準）

|美東時間 |台北（夏令）|台北（冬令）|說明  |備註  |
|-----|------|------|----|----|
|09:35|21:35 |22:35 |開盤快報|🔔   |
|12:00|00:00 |01:00 |盤中報價|🔕 靜音|
|16:05|04:05 |05:05 |收盤報價|🔕 靜音|

> 💡 美股以**美東時間**為準；台北對應時間由時區自動換算，夏令／冬令自動切換，**不需維護 DST**。
>
> ⏱️ **交易日判斷**：GAS 於觸發時先過 `_isTradingDay(market)`——**週末自動跳過**，並比對可維護的假日清單（`TW_HOLIDAYS`／`US_HOLIDAYS`）跳過國定休市，避免無效推播。

-----

## 觸發架構

```
GAS everyDays trigger（台股 Asia/Taipei、美股 America/New_York）
        ↓
_isTradingDay(market)   ← 週末／假日 → skip（不送 dispatch）
        ↓
repository_dispatch     ← POST { event_type }，成功為 HTTP 204
        ↓
GitHub Actions（只負責執行）
        ↓
main.py                 ← 依 event.action 注入 market / slot
        ↓
LINE / Telegram
```

**觸發入口（GAS 為唯一正式入口）：**

| 入口 | 用途 | 說明 |
|---|---|---|
| `repository_dispatch` | **唯一正式入口** | GAS 打 6 種 event_type：`tw_open/tw_mid/tw_close/us_open/us_mid/us_close` |
| `workflow_dispatch` | 手動補播 | Actions 頁面手動選市場／時段 |
| ~~`schedule`~~ | **已停用** | GitHub cron 不保證準時，且與 GAS 併存會造成重複推播，故已自 workflow 移除 |

> GAS 負責「準時」，GitHub Actions 只負責「執行」。美股以 `America/New_York` 觸發，夏令／冬令由 IANA timezone 自動處理，**不需人工切換**。

-----

## 交易日判斷

非交易日**不送** `repository_dispatch`，從源頭避免休市日產生無效推播（而非讓 Actions 空跑後推出一堆 N/A）。

```
GAS everyDays trigger（每日固定時間觸發）
        ↓
_isTradingDay(market)
        ├─ 市場時區的週六／週日        → skip
        ├─ 在假日清單內（TW/US_HOLIDAYS）→ skip
        └─ 其餘                        → dispatch
```

- **台股**：以 `Asia/Taipei` 判斷星期，比對 `TW_HOLIDAYS`
- **美股**：以 `America/New_York` 判斷星期，比對 `US_HOLIDAYS`

**已知限制**

- `US_HOLIDAYS` **目前為空**（尚需補齊美股國定假日：獨立紀念日、感恩節、聖誕節等）。該日仍會 dispatch，因無交易資料而顯示 N/A。
- `TW_HOLIDAYS` 需依 **TWSE 官方年度行事曆**同步核對與擴充（清明／兒童節／補假等）。
- **臨時休市**（颱風、天災）不在任何清單內，屬預期外情形。

-----

## 系統運作流程

```
觸發（repository_dispatch / workflow_dispatch / schedule）
        ↓
main.py 讀取 TRIGGER / ACTION / CRON / MARKET / TYPE
        ↓
解析觸發來源 → 注入 (market, slot)
  repository_dispatch → github.event.action（如 us_open）→ 白名單驗證 → market/slot
  workflow_dispatch   → MARKET / TYPE（顯示當下台北時間）
  （schedule 已停用；SCHEDULE_CRON_MAP 保留於 config 供 rollback）
        ↓
core/decision.decide()：非交易日跳過；顯示時間 = 固定 slot 時刻（美股經時區換算）
        ↓
抓取股價（Yahoo Finance，period=5d，自動跳過 NaN K 棒）
        ↓
組合固定格式訊息（固定標的，失敗顯示 N/A）→ Telegram / LINE
```

-----

## 推播訊息範例

> 以下為實際推播畫面（範例數值）。台股固定 5 檔、美股固定 9 檔，順序與顯示名稱為凍結契約。

**🇹🇼 台股・開盤**

```
📊 台股報價・開盤
時間：06/15 09:05

🔴 台灣加權指數
   $23,450.18　+142.35（+0.61%）📈

🔴 元大台灣50
   $205.30　+1.15（+0.56%）📈

🟢 富邦台50
   $118.45　-0.35（-0.29%）📉

🔴 主動統一台股增長
   $13.82　+0.09（+0.66%）📈

🟢 台積電
   $1,185.00　-8.00（-0.67%）📉
```

**🇹🇼 台股・收盤**

```
📊 台股報價・收盤
時間：06/15 13:35

🔴 台灣加權指數
   $23,512.44　+204.61（+0.88%）📈

🔴 元大台灣50
   $206.10　+1.95（+0.96%）📈

🔴 富邦台50
   $118.90　+0.10（+0.08%）📈

🔴 主動統一台股增長
   $13.75　+0.02（+0.15%）📈

🟢 台積電
   $1,190.00　-3.00（-0.25%）📉
```

> 台股顏色：**🔴漲 🟢跌**（與美股相反）。

**🇺🇸 美股・開盤**

```
📊 美股報價・開盤
時間：06/15 21:35

🟢 標普500
   $6,285.44　+18.20（+0.29%）📈

🟢 VOO
   $582.15　+1.60（+0.28%）📈

🔴 QQQM
   $241.08　-0.55（-0.23%）📉

🟢 SMH
   $305.72　+2.30（+0.76%）📈

🔴 Apple
   $258.40　-1.10（-0.42%）📉

🟢 輝達
   $195.66　+3.05（+1.58%）📈

🟢 Google
   $214.30　+0.85（+0.40%）📈

🔴 TSMC ADR
   $262.18　-1.45（-0.55%）📉

🟢 SpaceX
   $47.85　+1.20（+2.57%）📈
```

**🇺🇸 美股・收盤（🔕 靜音推播）**

```
📊 美股報價・收盤
時間：06/16 04:05

🟢 標普500
   $6,302.55　+17.11（+0.27%）📈

🟢 VOO
   $583.40　+0.70（+0.12%）📈

🟢 QQQM
   $242.30　+1.75（+0.73%）📈

🔴 SMH
   $306.80　-0.35（-0.11%）📉

🟢 Apple
   $259.10　+1.20（+0.47%）📈

🟢 輝達
   $197.50　+0.62（+0.31%）📈

🔴 Google
   $213.60　-0.45（-0.21%）📉

🟢 TSMC ADR
   $264.05　+0.65（+0.25%）📈

🔴 SpaceX
   $47.90　-0.40（-0.83%）📉
```

> 美股顏色：**🟢漲 🔴跌**；收盤為靜音。時間隨夏/冬令自動位移（開盤 夏令21:35 / 冬令22:35；收盤 夏令04:05 / 冬令05:05）。盤中（台股 11:30、美股 12:00 ET）為相同格式，僅 slot 標籤不同。

**單支抓取失敗（保留位置顯示 N/A，數量與順序永遠固定）**

```
📊 台股報價・開盤
時間：06/15 09:05

🔴 台灣加權指數
   $23,450.18　+142.35（+0.61%）📈

⚪ 元大台灣50
   N/A

🔴 富邦台50
   $118.45　+0.20（+0.17%）📈

🔴 主動統一台股增長
   $13.82　+0.09（+0.66%）📈

🟢 台積電
   $1,185.00　-8.00（-0.67%）📉
```

-----

## 推播格式契約（凍結）

> ⚠️ 以下為推播輸出的**逐字凍結契約**，`formatter.py` 只能套用、不可變動。
> 特殊字元：全形空格 `U+3000`、全形括號 `（）`、中點 `・`、全形冒號 `：`。

**整體結構**

```
📊 {台股|美股}報價・{slot_label}
時間：{MM/DD HH:MM}
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

## 專案結構

```
.
├── main.py                    # orchestration 入口（解析觸發來源、串接各層）
├── config.py                  # 標的契約、SCHEDULE_CRON_MAP（純資料）
├── core/decision.py           # 決策層：事件驅動注入 slot（不做時間窗猜測）
├── scheduler/calendar.py      # 時間真相：timezone / DST / 交易日
├── data/                      # Yahoo Finance 抓價 + StockQuote model
├── service/quote_service.py   # 批次取得報價（固定標的保留順序）
├── notify/                    # formatter（凍結契約）+ Telegram + LINE
├── state/idempotency.py       # 單次執行內防重入（persist 已移除）
├── utils/logger.py            # 統一 log
└── .github/workflows/stock-notify.yml   # workflow_dispatch + repository_dispatch + schedule

外部（不在 repo 內）：
  trigger.gs — Google Apps Script 準時觸發器（打 repository_dispatch）
```

-----

## 快速開始

### 1. 設定 GitHub Secrets

repo → **Settings → Secrets and variables → Actions**：`TG_TOKEN`、`TG_CHAT`、`LINE_TOKEN`、`LINE_ID`。

### 2. 本機測試

```bash
# 手動模式（跳過時間檢查，直接推播）
TRIGGER=workflow_dispatch MARKET=tw TYPE=open python main.py
# 模擬 GAS 事件
TRIGGER=repository_dispatch ACTION=us_open python main.py
```

### 3. 手動補播

GitHub → **Actions → Stock Notify → Run workflow**，選市場（tw / us）與時段（open / mid / close）。

-----

## 取得推播憑證

- **Telegram**：找 [@BotFather](https://t.me/BotFather) 建 Bot 取得 Token，加入群組後取得 Chat ID。
- **LINE Messaging API**：於 [LINE Developers](https://developers.line.biz/) 建 Channel，取得 Channel Access Token 與推播對象 User ID。
- **GitHub PAT（給 GAS 用）**：Fine-grained token，只授權本 repo、`Contents: Read and write`；存入 GAS 的 Script Properties（`GITHUB_PAT`），**不放進 GitHub Secrets**。

-----

## 穩定性機制

|機制       |說明                                 |
|---------|-----------------------------------|
|外部 GAS 準時|排程改由 Google Apps Script 觸發，取代不穩定的 GitHub cron|
|事件驅動 · 延遲免疫|觸發後直接注入 slot，延遲多久都不漏推（無時間窗）|
|美股 DST 自動|美東時間為準，GAS 以 `America/New_York` 觸發、顯示由時區換算，夏令／冬令自動|
|固定標的     |台股 5 檔／美股 9 檔，單支失敗保留位置顯示 N/A，數量與順序永遠固定|
|NaN 過濾   |開盤前資料未生成時自動取最近有效收盤，不顯示 nan        |
|單一觸發入口   |GitHub schedule 已停用，`repository_dispatch`（GAS）為唯一入口，無重複推播風險；cron 保留於 config 供 rollback|
|交易日判斷    |GAS 端 `_isTradingDay()`：週末 + 假日清單自動跳過，避免無效推播|

-----

## Fail-safe 機制

|錯誤情境         |處理方式          |Actions 是否崩潰|
|-------------|--------------|------------|
|單支股票抓取失敗     |保留位置顯示 N/A    |❌ 不崩潰       |
|全部股票抓取失敗     |log + 跳過推播    |❌ 不崩潰       |
|Telegram 發送失敗|log + continue|❌ 不崩潰       |
|LINE 發送失敗    |log + continue|❌ 不崩潰       |
|Secrets 未設定  |跳過對應管道        |❌ 不崩潰       |
|未知 ACTION     |log + 跳過        |❌ 不崩潰       |
|非交易日（週末）     |跳過推播          |❌ 不崩潰       |

-----

## 故障排查（Troubleshooting）

### 問題：GitHub Actions 沒有出現 `repository_dispatch` run

依序檢查（由近而遠，找到即止）：

| # | 檢查 | 怎麼看 | 若異常 |
|---|---|---|---|
| 1 | **GAS Trigger 是否建立** | GAS 左側 ⏰ 觸發條件 → 應有 **6 個** | 執行 `setupTriggers()` |
| 2 | **`GITHUB_PAT` 是否存在且有效** | 執行 `testNow()` 看 Logger | 補上 PAT／重建 PAT |
| 3 | **`testNow()` 是否回 HTTP 204** | Logger：`✅ 觸發成功：tw_open（HTTP 204）` | 見下方 HTTP 對照表 |
| 4 | **GitHub Actions 是否收到 dispatch** | Actions 頁面是否出現 `repository_dispatch` run | 若 204 但無 run → 檢查 PAT 授權的 repo 是否正確 |

**Logger HTTP 對照**

| Logger | 意義 | 處置 |
|---|---|---|
| `✅ HTTP 204` | GAS → GitHub 成功 | 往下游查（Actions / 推播）|
| `❌ 尚未設定 GITHUB_PAT` | PAT 未設定 → **靜默不送 HTTP** | 設定 PAT |
| `❌ HTTP 401` | Token 無效／不完整 | 重建 PAT |
| `❌ HTTP 403` | 權限不足 | PAT 需 **Contents: Read and write** |
| `❌ HTTP 404` | Repo 不符 | PAT 需授權 `stock-notify-bot` |

`showLogs()` 可查最近 20 筆 dispatch 執行紀錄（時間／event／HTTP code）。

### 📌 本次事件經驗（2026-07）

> **修改 GAS 程式碼 ≠ 重新建立 Trigger。**
> Trigger 是 GAS 的**獨立資源**，貼上新 code 後**必須執行 `setupTriggers()`** 才會重新註冊。

> **Code 正確 ≠ 系統已部署完成。**
> 本次「沒收到推播」的根因是 **`GITHUB_PAT` 未設定** —— `dispatch_()` 讀不到 PAT 便靜默 return、不發出 HTTP，導致 GitHub 端 `repository_dispatch` 恆為 0。程式邏輯完全正確，問題出在部署狀態與 runtime 資源未同步。GAS 這類 serverless 平台特別容易踩此坑。

-----

## 已知限制

- **GAS 定時誤差**：Google Apps Script 時間觸發約有 ±15 分鐘誤差（平台特性），符合「15 分鐘內收到」的目標；要求分秒精準需自架 cron。
- **GitHub Actions schedule 已停用**：因免費版 cron 不保證準時、可能漏觸發，且與 GAS 併存會造成重複推播，故 workflow 已移除 `schedule`；`repository_dispatch`（GAS）為唯一正式入口。9 條 cron 保留在 `config.SCHEDULE_CRON_MAP`，必要時可貼回 workflow 作為 rollback。
- **交易日判斷**：GAS 端 `_isTradingDay()` 已涵蓋**週末 + 可維護假日清單**（春節/端午/中秋/國定）；假日清單需依 **TWSE 官方行事曆**核對擴充，且**臨時休市（颱風/天災）不在清單內**，此類日若被觸發會因抓不到資料顯示 N/A。
- **N/A 的成因（設計上的優雅降級）**：資料來源為 Yahoo Finance（免費、非官方 API）。開盤瞬間當日 K 棒可能尚未生成、Yahoo 偶發限流／逾時、或 runner 網路瞬斷時，單支標的會取不到報價。此時系統**保留該檔位置顯示 `N/A`**，而非刪除該列或中止推播——以維持「固定檔數與順序」的凍結契約。通常為暫時性，下一個時段即恢復。
- 資料來源為 Yahoo Finance，可能有數分鐘延遲。

-----

## Release Notes

### v2.2 交易日判斷 + 部署修復（2026-07）

**Added**
- GAS `_isTradingDay(market)`：週末 + 假日清單（`TW_HOLIDAYS` / `US_HOLIDAYS`）過濾，非交易日不送 dispatch
- README：新增「交易日判斷」「故障排查（Troubleshooting）」章節

**Fixed（部署狀態，非程式）**
- 根因：GAS 未設定 `GITHUB_PAT` → `dispatch_()` 靜默 return → GitHub `repository_dispatch` 恆為 0 → 無推播
- 修復：GAS 端設定 PAT + 執行 `setupTriggers()` 重建 6 個 trigger。**repo 程式碼零改動**

**Docs**
- 移除「GitHub schedule 為備援入口」等過時描述；`repository_dispatch` 明確為唯一正式入口

-----

### v2.1 Hardened Trigger

**Added**
- Google Apps Script 改為 Script Properties 管理 GitHub PAT（不硬編碼）
- PAT 每次 dispatch 即時重新讀取（避免快取舊值）
- repository_dispatch HTTP Retry（5s / 15s）
- scheduler_logs 保留最近 20 次執行紀錄（`showLogs()` 可查）
- main.py 新增 `[DISPATCH]` runtime log
- Trigger Timezone 明確指定（台股 Asia/Taipei、美股 America/New_York）
- 美股 DST 由時區自動處理

**No Breaking Changes**

以下模組完全未修改：`decision.py`、`formatter.py`、`quote_service.py`、`config.py 判斷邏輯`。
因此推播內容、格式、股票排序、判斷邏輯全部維持原契約。本次更新僅提升穩定性、可觀測性（Observability）與維護性（Maintainability）。

-----

## 免責聲明

本工具僅提供即時行情資訊，**不構成任何投資建議**。
資料來源為 Yahoo Finance，可能有延遲，請以官方交易所資料為準。
