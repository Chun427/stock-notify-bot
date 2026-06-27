# scheduler/calendar.py — 時間真相來源（timezone / DST / 交易日）
#
# 美股以美東時間（America/New_York）判斷，夏令／冬令由 zoneinfo 自動切換。
from datetime import datetime
from zoneinfo import ZoneInfo

_TAIPEI = ZoneInfo("Asia/Taipei")
_US_EAST = ZoneInfo("America/New_York")

TZ = {"tw": _TAIPEI, "us": _US_EAST}


def now_in(market: str) -> datetime:
    """該市場時區的現在時間（tz-aware）。"""
    return datetime.now(TZ[market])


def to_taipei(dt: datetime) -> datetime:
    """任意 tz-aware 時間轉台北時區（推播顯示一律台北時間）。"""
    return dt.astimezone(_TAIPEI)


def is_trading_day(dt: datetime) -> bool:
    """週一～週五為交易日（不含國定假日，屬已知限制）。"""
    return dt.weekday() < 5
