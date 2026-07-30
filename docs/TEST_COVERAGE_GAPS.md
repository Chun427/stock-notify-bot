# 測試覆蓋缺口清單

本次 session 產出的 59 個測試（golden string 逐字取自 README）全部綠燈，
但綠燈只證明「格式契約」被守住，不代表 README 所有明文規定都有對應測試。
以下為已知缺口，**只記錄，未實作、未新增測試**。

## 1. `workflow_dispatch` 顯示時間

README「系統運作流程」明文：

> workflow_dispatch → MARKET / TYPE（顯示當下台北時間）

本次 59 個測試從未斷言過「manual 模式顯示的是即時時間，而非固定 slot 時刻」。
本機重寫版原本的實作（修正前）反而是兩種觸發來源都顯示固定 slot 時刻，
與 README 這條契約牴觸；R2 稽核發現遠端生產版本（`now_in("tw")`）才是對的。
**狀態：已知行為差異，非測試覆蓋問題本身，但暴露了測試從未驗證過這條規則。**

## 2. 深夜靜音（silent / disable_notification）

README「功能特色」與「自動推播排程」明文：

> 深夜靜音：美股盤中、收盤自動靜音，不打擾睡眠

沒有任何測試斷言過「美股 mid/close 這兩個 slot 應該以靜音方式推播、其餘 slot 不靜音」。
本機重寫版的 `notify/telegram.py`、`notify/line.py` **完全沒有實作**這個參數；
遠端生產版本有實作（`silent` 依 `(market, slot)` 判斷，傳入
`disable_notification` / `notificationDisabled`）。

## 3. 靜音旗標是否真的傳進 API payload

即使補上第 2 項的邏輯測試（「哪些 slot 該靜音」），還需要再驗證一層：
呼叫 Telegram/LINE API 時，`silent` 的值有沒有正確放進實際送出的 payload
（`disable_notification` 欄位、`notificationDisabled` 欄位）。這是兩個獨立的
斷言層次，目前都是空白。

## 4. idempotency 的持久化語意 — 遠端已確認的真實缺陷

**這一項不是「待驗證的潛在問題」，而是本次稽核（R1/R0）已經直接讀 code 確認的
真實缺陷**：

- 遠端 `state/idempotency.py` 會寫入 `state/sent.json`，程式註解宣稱
  「由 GitHub Actions 於 schedule 模式 commit 回 repo，達成跨 runner 去重」
- 但實際檢視 `.github/workflows/stock-notify.yml`，工作流程**沒有任何
  `git add` / `git commit` / `git push` 步驟**，把 `state/sent.json` 寫回 repo
- 結果：每次 Actions run 都是全新 checkout，`state/sent.json` 從未真正被提交過，
  `already_sent()` 永遠讀到空字典 → **跨 run 防重入實際上是死的**，
  只是程式碼看起來像有做

沒有任何自動化測試覆蓋「同一個 slot 觸發兩次，第二次應該被擋下來」這個情境
（也覆蓋不到，因為現行 workflow 設計下這個情境本來就不會發生於單一 run 內）。
這正是這個缺口從未被發現的原因——它不是「測試沒寫」，而是「這個持久化機制
本身的因果鏈（寫入 → commit → 下次 run 讀到）沒有被任何一層驗證過」。

## 備註

以上四項均為**記錄**，不代表待辦優先序。是否修、何時修、修哪個，
由你決定；本文件僅確保這些缺口不會在下次討論時被重新發現一次。
