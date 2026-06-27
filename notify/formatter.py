# notify/formatter.py — 組合固定格式訊息（凍結契約，只能套用、不可變動）
#
# 特殊字元：全形空格 U+3000「　」、全形括號（）、中點・、全形冒號：
# 漲跌判定：change >= 0 視為漲。
# 顏色：台股 🔴漲 🟢跌；美股 🟢漲 🔴跌。  趨勢：📈漲 📉跌（兩市相同）。
# 縮排：3 個半形空格。數值千分位 + 2 位小數；漲跌與百分比帶正負號。
from datetime import datetime
from typing import List

from data.models import StockQuote

_MARKET_LABEL = {"tw": "台股", "us": "美股"}
_SLOT_LABEL = {"open": "開盤", "mid": "盤中", "close": "收盤"}

_FULL_SPACE = "\u3000"  # U+3000 全形空格


def _color(market: str, change: float) -> str:
    up = change >= 0
    if market == "tw":
        return "🔴" if up else "🟢"
    return "🟢" if up else "🔴"  # us


def _trend(change: float) -> str:
    return "📈" if change >= 0 else "📉"


def _block(market: str, q: StockQuote) -> str:
    if not q.is_valid:
        return f"⚪ {q.name}\n   N/A"
    change = q.change
    color = _color(market, change)
    trend = _trend(change)
    return (
        f"{color} {q.name}\n"
        f"   ${q.price:,.2f}{_FULL_SPACE}{change:+,.2f}（{q.pct:+.2f}%）{trend}"
    )


def format_message(
    market: str, slot: str, schedule_time_taipei: datetime, quotes: List[StockQuote]
) -> str:
    header = f"📊 {_MARKET_LABEL[market]}報價・{_SLOT_LABEL[slot]}"
    time_line = f"時間：{schedule_time_taipei.strftime('%m/%d %H:%M')}"
    blocks = [_block(market, q) for q in quotes]
    return header + "\n" + time_line + "\n\n" + "\n\n".join(blocks)
