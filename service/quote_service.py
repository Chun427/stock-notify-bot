# service/quote_service.py — 批次取得報價（固定標的、保留順序）
from typing import List

from config import TW_SYMBOLS, US_SYMBOLS
from data.fetcher import fetch_price
from data.models import StockQuote
from utils.logger import get_logger

log = get_logger("quote_service")

_SYMBOLS = {"tw": TW_SYMBOLS, "us": US_SYMBOLS}


def get_quotes(market: str) -> List[StockQuote]:
    """
    依契約固定清單逐檔抓取，順序與數量永遠固定。
    單支失敗 → price=None（formatter 轉 N/A），不影響其他標的。
    """
    symbols = _SYMBOLS[market]
    quotes: List[StockQuote] = []
    for name, ticker in symbols:
        price, prev = fetch_price(ticker)
        quotes.append(
            StockQuote(name=name, symbol=ticker, price=price, prev_close=prev)
        )
    failed = [q.symbol for q in quotes if not q.is_valid]
    log.info("market=%s 取得 %d/%d 檔有效", market, len(quotes) - len(failed), len(quotes))
    if failed:
        log.warning("market=%s 抓取失敗（顯示 N/A）：%s", market, ", ".join(failed))
    return quotes
