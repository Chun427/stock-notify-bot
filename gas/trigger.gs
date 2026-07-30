/**
 * ⚠️⚠️⚠️ 警告：本檔尚未經線上驗證，嚴禁直接貼入 GAS 編輯器 ⚠️⚠️⚠️
 *
 * 本檔是依 README 規格從零重寫的版本，從未在真實 GAS 環境執行過一次。
 * 線上目前實際運作的 GAS 專案，已經穩定跑了兩週以上（每個 slot 每天精確
 * 觸發 1 次，見對話中的 Actions run 稽核），版控應該記錄「實際運行的那一份」，
 * 不是這份沒跑過的重寫版——這份檔案目前只是佔位/草稿，方向尚未校正。
 *
 * 具體風險：本檔的 setupTriggers() 只會刪除「本檔自己命名」的 handler
 * （triggerTwOpen / triggerTwMid / triggerTwClose / triggerUsOpen /
 * triggerUsMid / triggerUsClose）。如果線上實際的 GAS 專案用的是不同的
 * 函式名稱，直接貼上本檔並執行 setupTriggers()：
 *   - 不會刪除線上原本的 6 個 trigger
 *   - 會另外新增本檔的 6 個 trigger
 *   - 結果變成 12 個 trigger 同時存在，每個 slot 每天觸發 2 次
 *   - repository_dispatch 變成每 slot 送 2 次、Telegram/LINE 各推 2 則
 *   - LINE 免費額度目前餘裕僅 1.5 倍（見 ADR-001），會立即被打爆
 *
 * 正確流程：先從 GAS 編輯器匯出線上實際運行的原始碼，與本檔逐項 diff，
 * 用線上版本覆蓋本檔，而不是把本檔貼上去。在完成這個比對之前，
 * 本檔僅供閱讀 / 版本追蹤參考，不得部署。
 */

/**
 * trigger.gs — GAS 定時觸發器（repository_dispatch 為唯一正式入口，見 README「觸發架構」）。
 *
 * 部署方式（本檔僅為版控副本，不會自動同步到 GAS）：
 *   1. 複製本檔全部內容，貼到 script.google.com 的 GAS 編輯器
 *   2. 專案設定 → Script Properties → 新增 GITHUB_PAT（fine-grained PAT，
 *      Contents: Read and write，只授權本 repo；絕不放進 GitHub Secrets）
 *   3. 執行 setupTriggers()（貼上新 code 不會自動重建 trigger，必須手動執行一次；
 *      見 README「故障排查」的事件經驗）
 *   4. 執行 testNow() 確認 Logger 顯示 HTTP 204
 */

// ===== 基本設定（部署前請填入實際值）=====
const GITHUB_OWNER = 'Chun427';
const GITHUB_REPO = 'stock-notify-bot';
const RETRY_DELAYS_MS = [5000, 15000]; // HTTP Retry：5s、15s
const MAX_LOG_ENTRIES = 20;

// event_type 對照與 GAS 觸發時刻（README「自動推播排程」章節）
const TRIGGER_DEFINITIONS = [
  { handler: 'triggerTwOpen', action: 'tw_open', market: 'tw', hour: 9, minute: 5 },
  { handler: 'triggerTwMid', action: 'tw_mid', market: 'tw', hour: 11, minute: 30 },
  { handler: 'triggerTwClose', action: 'tw_close', market: 'tw', hour: 13, minute: 35 },
  { handler: 'triggerUsOpen', action: 'us_open', market: 'us', hour: 9, minute: 35 },
  { handler: 'triggerUsMid', action: 'us_mid', market: 'us', hour: 12, minute: 0 },
  { handler: 'triggerUsClose', action: 'us_close', market: 'us', hour: 16, minute: 5 },
];

// ===== 假日清單（_isTradingDay 用；README「交易日判斷」章節）=====
//
// TW_HOLIDAYS：僅 2026-01-01（元旦）可 100% 確認 —— 各主要市場皆固定休市，
// 無爭議。其餘 2026 台股休市日（農曆春節、和平紀念日、兒童節／民族掃墓節、
// 端午節、中秋節、國慶日、其他官方公告之休市日）因無法取得可信賴、可交叉驗證
// 的官方來源（實際查詢 TWSE 官網查詢頁為 JS 動態頁面，本次工具鏈無法穩定讀取
// 其查詢結果，兩次嘗試給出互相矛盾的內容，故不採信），一律不填入，
// 標記【待查證】，避免把不可靠資料當成契約凍結。
//
// 待查證清單（請上 TWSE 官方「市場開休市日期」查詢頁手動核對後回填）：
//   https://www.twse.com.tw/zh/trading/holiday.html
//   - 農曆春節（約 2026 年 2 月中旬，確切區間需查官方公告）【待查證】
//   - 和平紀念日 228（含補假）【待查證】
//   - 兒童節／民族掃墓節（4 月）【待查證】
//   - 端午節【待查證】
//   - 中秋節【待查證】
//   - 國慶日（含補假）【待查證】
//   - 其餘 TWSE 官方公告之休市日【待查證】
const TW_HOLIDAYS = [
  '2026-01-01', // 元旦
];

// US_HOLIDAYS：2026 年 NYSE 全日休市日期。
// 驗證方式（誠實記錄，非直接讀取官方文件確認）：
//   - WebSearch 搜尋結果的摘要文字提及並引用 NYSE Group《2024, 2025 and 2026
//     Holiday and Early Closings Calendar》官方公告內容，但這是搜尋引擎摘要，
//     不是我親自完整讀過的原始公告
//   - 曾嘗試 WebFetch 直接讀取該公告原始頁面
//     （ir.theice.com/press/news-details/2023/...），但該次擷取結果內部不一致
//     （例如遺漏感恩節/聖誕節、Independence Day 全休或提前收盤的認定前後矛盾），
//     判斷為擷取失真，未採信、未單獨依賴
//   - 固定規則假日（如「一月第三個星期一」等聯邦假日規則）已用日期運算獨立複核
//   - Good Friday（復活節前兩天）已用復活節演算法獨立計算 = 2026-04-03，
//     與 WebSearch 摘要一致
// 上述為交叉比對後的結論，並非官方文件的第一手確認，正式上線前仍請至
// nyse.com/markets/hours-calendars 人工核對一次。
const US_HOLIDAYS = [
  '2026-01-01', // New Year's Day
  '2026-01-19', // Martin Luther King, Jr. Day
  '2026-02-16', // Washington's Birthday
  '2026-04-03', // Good Friday
  '2026-05-25', // Memorial Day
  '2026-06-19', // Juneteenth National Independence Day
  '2026-07-03', // Independence Day (observed; 07-04 falls on Saturday)
  '2026-09-07', // Labor Day
  '2026-11-26', // Thanksgiving Day
  '2026-12-25', // Christmas Day
];

// ===== 交易日判斷 =====
function _isTradingDay(market) {
  const tz = market === 'tw' ? 'Asia/Taipei' : 'America/New_York';
  const now = new Date();

  const weekday = Number(Utilities.formatDate(now, tz, 'u')); // 1=Mon ... 7=Sun
  if (weekday >= 6) return false;

  const dateStr = Utilities.formatDate(now, tz, 'yyyy-MM-dd');
  const holidays = market === 'tw' ? TW_HOLIDAYS : US_HOLIDAYS;
  return holidays.indexOf(dateStr) === -1;
}

// ===== dispatch（GITHUB_PAT 每次即時重讀，不快取）=====
function dispatch_(action) {
  const pat = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  if (!pat) {
    Logger.log('❌ 尚未設定 GITHUB_PAT');
    _appendLog_(action, 'NO_PAT');
    return;
  }

  const url = 'https://api.github.com/repos/' + GITHUB_OWNER + '/' + GITHUB_REPO + '/dispatches';
  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + pat,
      Accept: 'application/vnd.github+json',
    },
    payload: JSON.stringify({ event_type: action }),
    muteHttpExceptions: true,
  };

  const delaysBeforeAttempt = [0].concat(RETRY_DELAYS_MS); // 立即嘗試一次 + 兩次重試
  let lastCode = null;

  for (let i = 0; i < delaysBeforeAttempt.length; i++) {
    if (delaysBeforeAttempt[i] > 0) {
      Utilities.sleep(delaysBeforeAttempt[i]);
    }
    const resp = UrlFetchApp.fetch(url, options);
    lastCode = resp.getResponseCode();

    if (lastCode === 204) {
      Logger.log('✅ 觸發成功：' + action + '（HTTP ' + lastCode + '）');
      _appendLog_(action, lastCode);
      return;
    }
    Logger.log('❌ HTTP ' + lastCode + '：' + resp.getContentText());
  }

  _appendLog_(action, lastCode);
}

// ===== scheduler_logs（最近 20 筆，showLogs() 可查）=====
function _appendLog_(action, httpCode) {
  const props = PropertiesService.getScriptProperties();
  const raw = props.getProperty('SCHEDULER_LOGS');
  let logs = raw ? JSON.parse(raw) : [];

  logs.push({ time: new Date().toISOString(), action: action, httpCode: httpCode });
  if (logs.length > MAX_LOG_ENTRIES) {
    logs = logs.slice(logs.length - MAX_LOG_ENTRIES);
  }
  props.setProperty('SCHEDULER_LOGS', JSON.stringify(logs));
}

function showLogs() {
  const raw = PropertiesService.getScriptProperties().getProperty('SCHEDULER_LOGS');
  const logs = raw ? JSON.parse(raw) : [];
  logs.forEach(function (entry) {
    Logger.log(entry.time + ' | ' + entry.action + ' | HTTP ' + entry.httpCode);
  });
  return logs;
}

// ===== 6 個 trigger handler =====
function _run_(market, action) {
  if (!_isTradingDay(market)) {
    Logger.log('⏭ ' + action + ' 非交易日，跳過');
    return;
  }
  dispatch_(action);
}

function triggerTwOpen() { _run_('tw', 'tw_open'); }
function triggerTwMid() { _run_('tw', 'tw_mid'); }
function triggerTwClose() { _run_('tw', 'tw_close'); }
function triggerUsOpen() { _run_('us', 'us_open'); }
function triggerUsMid() { _run_('us', 'us_mid'); }
function triggerUsClose() { _run_('us', 'us_close'); }

// ===== 觸發器管理 =====
function setupTriggers() {
  _deleteManagedTriggers_();

  TRIGGER_DEFINITIONS.forEach(function (def) {
    const tz = def.market === 'tw' ? 'Asia/Taipei' : 'America/New_York';
    ScriptApp.newTrigger(def.handler)
      .timeBased()
      .everyDays(1)
      .atHour(def.hour)
      .nearMinute(def.minute)
      .inTimezone(tz)
      .create();
  });

  Logger.log('✅ 已建立 ' + TRIGGER_DEFINITIONS.length + ' 個觸發器');
}

function _deleteManagedTriggers_() {
  const handlerNames = TRIGGER_DEFINITIONS.map(function (d) { return d.handler; });
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (handlerNames.indexOf(trigger.getHandlerFunction()) !== -1) {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

// ===== 手動測試 =====
function testNow() {
  dispatch_('tw_open');
}
