"""將 README 逐字擷取的 golden fixture 解析回結構化輸入。

golden 文字本身完全來自 README（見 tests/fixtures/*.txt 的擷取腳本紀錄），
這裡只是把它拆成 formatter 的輸入參數，避免手動重打數字造成誤植；
最終仍然是拿 formatter 的輸出去跟同一份 golden 文字做逐字比對。
"""
import re
from datetime import datetime

HEADER_RE = re.compile(r"^📊 (?P<market_label>.+?)報價・(?P<slot_label>.+)$")
TIME_RE = re.compile(r"^時間：(?P<month>\d{2})/(?P<day>\d{2}) (?P<hour>\d{2}):(?P<minute>\d{2})$")
BLOCK_RE = re.compile(r"^(?P<color>🔴|🟢|⚪) (?P<name>.+)\n   (?P<body>.+)$", re.M)
DATA_BODY_RE = re.compile(
    r"^\$(?P<price>[\d,]+\.\d+)　(?P<change>[+-][\d,]+\.\d+)"
    r"（(?P<pct>[+-]\d+\.\d+)%）(?P<trend>📈|📉)$"
)

MARKET_LABEL_TO_CODE = {"台股": "tw", "美股": "us"}
SLOT_LABEL_TO_CODE = {"開盤": "open", "盤中": "mid", "收盤": "close"}


def parse_golden(text: str):
    lines = text.split("\n")
    header = HEADER_RE.match(lines[0])
    time_m = TIME_RE.match(lines[1])

    market = MARKET_LABEL_TO_CODE[header.group("market_label")]
    slot = SLOT_LABEL_TO_CODE[header.group("slot_label")]
    dt = datetime(
        2026,
        int(time_m.group("month")),
        int(time_m.group("day")),
        int(time_m.group("hour")),
        int(time_m.group("minute")),
    )

    quotes = []
    for m in BLOCK_RE.finditer(text):
        name = m.group("name")
        body = m.group("body")
        if body == "N/A":
            quotes.append({"name": name, "price": None, "change": None, "pct": None})
            continue
        dm = DATA_BODY_RE.match(body)
        assert dm, f"golden body 不符預期格式: {body!r}"
        quotes.append({
            "name": name,
            "price": float(dm.group("price").replace(",", "")),
            "change": float(dm.group("change").replace(",", "")),
            "pct": float(dm.group("pct")),
        })

    return market, slot, dt, quotes
