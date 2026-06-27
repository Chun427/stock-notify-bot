# data/fetcher.py — Yahoo Finance 抓價（retry + NaN 過濾 + per-call timeout）
from typing import Optional, Tuple

import yfinance as yf

from config import FETCH_RETRIES, FETCH_TIMEOUT, HISTORY_PERIOD
from utils.logger import get_logger

log = get_logger("fetcher")


def _valid_closes(hist) -> list:
    """取出非 NaN 的收盤價（依時間順序）。NaN != NaN 用來過濾。"""
    try:
        return [c for c in hist["Close"].tolist() if c == c]
    except Exception:
        return []


def fetch_price(symbol: str) -> Tuple[Optional[float], Optional[float]]:
    """
    回傳 (price, prev_close)：
      - price     = 最近一根有效收盤
      - prev_close= 前一根有效收盤（不足 2 根時退回 price → change 0.00）
    任一錯誤都不拋出，回傳 (None, None) 由上層轉 N/A。
    """
    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            hist = yf.Ticker(symbol).history(
                period=HISTORY_PERIOD, timeout=FETCH_TIMEOUT
            )
            closes = _valid_closes(hist)
            if not closes:
                log.warning("[%s] 無有效收盤（第 %d 次）", symbol, attempt)
                continue
            price = float(closes[-1])
            prev = float(closes[-2]) if len(closes) >= 2 else price
            return price, prev
        except Exception as e:  # noqa: BLE001  fail-safe
            log.warning("[%s] 抓取失敗（第 %d 次）：%s", symbol, attempt, e)
    log.warning("[%s] 全部重試失敗 → N/A", symbol)
    return None, None
