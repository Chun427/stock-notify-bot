"""R1 稽核：把本次 session 的 formatter golden 契約測試，套用在遠端 notify/formatter.py 上。

golden fixture（tests/fixtures/*.txt）逐字沿用本次 session 從 README 擷取的版本，
完全未修改。唯一調整的是「取值方式」——遠端的 format_message 簽章與資料模型跟
本次重寫版不同（StockQuote(name, symbol, price, prev_close)，change/pct 為
計算屬性），這裡只是把 golden 解析出的 (price, change) 換算回
(price, prev_close) 餵給遠端建構子，斷言本身（== golden 全文）逐字沿用。
"""
import os

import pytest

from notify.formatter import format_message
from data.models import StockQuote
from tests.golden_parser import parse_golden

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
CASES = ["tw_open", "tw_close", "us_open", "us_close", "na_example"]


def _load(name):
    path = os.path.join(FIXTURE_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _to_remote_quotes(parsed_quotes):
    """golden_parser 給的是 (name, price, change, pct)；遠端模型要 (name, symbol,
    price, prev_close)，change/pct 用 price - prev_close 反推為計算屬性。"""
    quotes = []
    for q in parsed_quotes:
        if q["price"] is None:
            quotes.append(StockQuote(name=q["name"], symbol="", price=None, prev_close=None))
        else:
            prev_close = q["price"] - q["change"]
            quotes.append(StockQuote(name=q["name"], symbol="", price=q["price"], prev_close=prev_close))
    return quotes


@pytest.mark.parametrize("case", CASES)
def test_remote_formatter_matches_golden_exactly(case):
    golden = _load(case)
    market, slot, dt, parsed_quotes = parse_golden(golden)
    quotes = _to_remote_quotes(parsed_quotes)

    actual = format_message(market, slot, dt, quotes)

    assert actual == golden
