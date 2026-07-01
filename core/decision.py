# core/decision.py — 決策層（事件驅動：cron 直接注入 slot，不做時間窗猜測）
#
# P1 修復：移除脆弱的 ±容錯窗（cron=T-3 + ±3 → 僅 ~5.5 分預算，GitHub 延遲常超出
#          → 靜默漏推）。改為事件驅動——market/slot 由觸發端直接注入。
#          US 雙季 cron 以「當前 DST 實際狀態」消歧（延遲免疫），非時間窗。
from datetime import datetime, timedelta
from typing import Optional, Tuple

from scheduler.calendar import is_trading_day, now_in, to_taipei
from utils.logger import get_logger

log = get_logger("decision")

# 各市場各時段的「顯示用固定時刻」(hour, minute)
SLOTS = {
    "tw": {"open": (9, 5), "mid": (11, 30), "close": (13, 35)},   # 台北時間
    "us": {"open": (9, 35), "mid": (12, 0), "close": (16, 5)},    # 美東時間
}

# 深夜靜音：美股盤中、收盤
_SILENT = {("us", "mid"), ("us", "close")}

# 回傳型別：(market, slot, schedule_time_taipei, silent)
Decision = Tuple[str, str, datetime, bool]


def _target(now_market: datetime, market: str, slot: str) -> datetime:
    """該 slot 今天的固定排程時刻（市場當地時區）——僅供顯示時間用。"""
    h, m = SLOTS[market][slot]
    return now_market.replace(hour=h, minute=m, second=0, microsecond=0)


def decide(
    event: str,
    market: Optional[str],
    slot: Optional[str],
    season: Optional[str] = None,
) -> Optional[Decision]:
    """
    事件驅動：market / slot 由觸發端直接指定
      - workflow（schedule）：依 github.event.schedule 對應的 cron 注入
      - manual（workflow_dispatch）：依 inputs 注入
    不再用 ±容錯窗反推 slot，故不受 GitHub cron 延遲影響（延遲多久都照推）。

    顯示時間：
      - workflow_dispatch → 當下台北時間（idempotency 由 main 端略過）
      - schedule          → 該 slot 的固定排程時間（台北）

    US 雙季 cron（EDT/EST 各一條，GitHub 以 UTC 每日皆觸發）以「當前 DST 實際
    狀態」判斷這條 cron 是否屬當前季節；非當季直接跳過（不靠時間接近度，延遲免疫）。
    """
    if market not in SLOTS or slot not in SLOTS.get(market, {}):
        log.warning("參數無效：market=%s slot=%s", market, slot)
        return None

    silent = (market, slot) in _SILENT

    # 手動：直接推指定 slot，顯示當下台北時間
    if event == "workflow_dispatch":
        return market, slot, now_in("tw"), silent

    # 排程：事件驅動注入
    now_mkt = now_in(market)
    if not is_trading_day(now_mkt):
        log.info("非交易日 → 跳過 market=%s slot=%s", market, slot)
        return None

    # US 雙季 cron 消歧：以實際 DST 狀態比對這條 cron 的季節
    if market == "us" and season:
        current = "EDT" if now_mkt.dst() != timedelta(0) else "EST"
        if season != current:
            log.info("季節不符（此 cron 屬 %s，現在 %s）→ 跳過", season, current)
            return None

    tgt = _target(now_mkt, market, slot)
    disp = to_taipei(tgt)
    log.info("注入 market=%s slot=%s 顯示時間=%s", market, slot, disp.strftime("%m/%d %H:%M"))
    return market, slot, disp, silent
