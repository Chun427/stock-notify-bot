# main.py — orchestration 入口（串接各層，不含決策細節）
#
# 模式：
#   cron            → 依時間真相 + 容錯窗判斷該推哪個市場/時段
#   workflow_dispatch → 依 MARKET / TYPE 直接補播（跳過時間檢查、跳過去重）
#
# Fail-safe：任何例外都被攔截，Actions 永不崩潰（exit 0）。
import os

from config import SCHEDULE_CRON_MAP
from core.decision import decide
from notify.formatter import format_message
from notify.line_notifier import send_line
from notify.telegram_notifier import send_telegram
from service.quote_service import get_quotes
from state.idempotency import already_sent, mark_sent
from utils.logger import get_logger

log = get_logger("main")


def run() -> None:
    event = os.getenv("TRIGGER", "schedule")  # = github.event_name
    manual = event == "workflow_dispatch"

    if manual:
        market, slot, season = os.getenv("MARKET") or None, os.getenv("TYPE") or None, None
    else:
        # 事件驅動：github.event.schedule（cron 字串）→ (market, slot, season)
        market, slot, season = SCHEDULE_CRON_MAP.get(
            os.getenv("CRON", ""), (None, None, None)
        )

    decision = decide(event=event, market=market, slot=slot, season=season)
    if decision is None:
        log.info("無可執行 slot（參數無效 / 非交易日 / 季節不符）→ 跳過")
        return

    market, slot, sched_taipei, silent = decision
    key = f"{sched_taipei:%Y-%m-%d}_{market}_{slot}"

    if not manual and already_sent(key):
        log.info("已推播過 %s → SKIP", key)
        return

    quotes = get_quotes(market)
    if not any(q.is_valid for q in quotes):
        log.warning("全部標的抓取失敗 → 跳過推播（不推全 N/A 訊息）")
        return

    msg = format_message(market, slot, sched_taipei, quotes)
    ok_tg = send_telegram(msg, silent=silent)
    ok_line = send_line(msg, silent=silent)

    if (ok_tg or ok_line) and not manual:
        mark_sent(key)

    log.info(
        "完成 market=%s slot=%s silent=%s tg=%s line=%s",
        market, slot, silent, ok_tg, ok_line,
    )


def main() -> None:
    try:
        run()
    except Exception as e:  # noqa: BLE001  fail-safe：永不讓 Actions 崩潰
        log.error("Fatal but contained：%s", e, exc_info=True)


if __name__ == "__main__":
    main()
