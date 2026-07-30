"""R1 稽核：把本次 session 的 config 契約斷言，套用在遠端 config.py 上。
僅調整取值方式（遠端用 tuple list TW_SYMBOLS/US_SYMBOLS，非 dict list），
斷言內容與期望值逐字沿用 tests/test_config_contract.py，未改動。
"""
import config

EXPECTED_TW = [
    ("台灣加權指數", "^TWII"),
    ("元大台灣50", "0050.TW"),
    ("富邦台50", "006208.TW"),
    ("主動統一台股增長", "00981A.TW"),
    ("台積電", "2330.TW"),
]

EXPECTED_US = [
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


def test_tw_stock_count():
    assert len(config.TW_SYMBOLS) == 5


def test_us_stock_count():
    assert len(config.US_SYMBOLS) == 9


def test_tw_stocks_order_and_names():
    assert config.TW_SYMBOLS == EXPECTED_TW


def test_us_stocks_order_and_names():
    assert config.US_SYMBOLS == EXPECTED_US
