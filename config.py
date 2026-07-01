# config.py — 標的契約、常數設定（純資料，無 IO、無邏輯）
#
# ⚠️ 凍結契約：顯示名稱與順序為唯一真相來源（formatter 唯一依據）。
#    不可修改、不可重新排序、不可語意翻譯。
#    允許內部 ticker mapping / fallback，但不得影響任何對外顯示字串。

# 🇹🇼 台股（固定 4 檔）：(顯示名稱, ticker)
TW_SYMBOLS = [
    ("台灣加權指數", "^TWII"),
    ("元大台灣50", "0050.TW"),
    ("富邦台50", "006208.TW"),
    ("台積電", "2330.TW"),
]

# 🇺🇸 美股（固定 9 檔）：(顯示名稱, ticker)
#   #9 SpaceX：契約修訂 — 經 governance 核准新增。
#   註：SPCX 自 2026-04-07 起已指向 Space Exploration Technologies (SpaceX)，
#       舊「SPAC and New Issue ETF」已改 ticker 為 SPCK，與本標的無關。
US_SYMBOLS = [
    ("標普500", "^GSPC"),
    ("VOO", "VOO"),
    ("QQQM", "QQQM"),
    ("SMH", "SMH"),
    ("Apple", "AAPL"),
    ("輝達", "NVDA"),
    ("Google", "GOOGL"),
    ("TSMC ADR", "TSM"),
    ("SpaceX", "SPCX"),
]

# 抓價設定
FETCH_RETRIES = 3
FETCH_TIMEOUT = 10  # 秒（per-call，避免單支卡死整批）
HISTORY_PERIOD = "5d"
