# core/decision.py — 決策層（純邏輯：該不該推 / 哪個市場 / 哪個時段）
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config import TOLERANCE_MINUTES
from scheduler.calendar import is_trading_day, now_in, to_taipei
from utils.logger import get_logger

log = get_logger("decision")

# 各市場排程目標時間（市場當地時區）：slot -> (hour, minute)
SLOTS = {
    "tw": {"open": (9, 5), "mid": (11, 30), "close": (13, 35)},   # 台北時間
    "us": {"open": (9, 35), "mid": (12, 0), "close": (16, 5)},    # 美東時間
}

# 深夜靜音時段：美股盤中、收盤
_SILENT = {("us", "mid"), ("us", "close")}

_TOL = timedelta(minutes=TOLERANCE_MINUTES)

# 回傳型別：(market, slot, schedule_time_taipei, silent)
Decision = Tuple[str, str, datetime, bool]


def _target(now_market: datetime, market: str, slot: str) -> datetime:
    h, m = SLOTS[market][slot]
    return now_market.replace(hour=h, minute=m, second=0, microsecond=0)


def decide(
    manual: bool = False,
    market: Optional[str] = None,
    slot: Optional[str] = None,
) -> Optional[Decision]:
    """
    manual=True（workflow_dispatch）：跳過時間檢查，直接推指定市場/時段，
        顯示時間用「現在台北時間」。
    manual=False（cron）：掃描所有市場/時段，命中容錯窗（±3 分）才推；
        非交易日 / 錯誤季節 cron 自動跳過。顯示時間用「排程目標時間（台北）」。
    """
    if manual:
        if market not in SLOTS or slot not in SLOTS.get(market, {}):
            log.warning("manual 參數無效：market=%s slot=%s", market, slot)
            return None
        silent = (market, slot) in _SILENT
        return market, slot, now_in("tw"), silent

    for mk in SLOTS:
        now_mkt = now_in(mk)
        if not is_trading_day(now_mkt):
            continue
        for sl in SLOTS[mk]:
            tgt = _target(now_mkt, mk, sl)
            if abs(now_mkt - tgt) <= _TOL:
                silent = (mk, sl) in _SILENT
                log.info(
                    "命中 market=%s slot=%s（now=%s tgt=%s）",
                    mk, sl, now_mkt.strftime("%H:%M:%S"), tgt.strftime("%H:%M"),
                )
                return mk, sl, to_taipei(tgt), silent
    return None
