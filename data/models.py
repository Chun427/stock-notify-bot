# data/models.py — StockQuote dataclass（含 NaN / 有效性檢查）
import math
from dataclasses import dataclass
from typing import Optional


def _finite(x) -> bool:
    """非 None、為數值、且非 NaN / 非 Inf。"""
    return (
        x is not None
        and isinstance(x, (int, float))
        and not math.isnan(x)
        and not math.isinf(x)
    )


@dataclass
class StockQuote:
    name: str          # 顯示名稱（凍結契約字串）
    symbol: str        # 內部 ticker（不對外顯示）
    price: Optional[float] = None
    prev_close: Optional[float] = None

    @property
    def is_valid(self) -> bool:
        """price 有效才算有資料；否則 formatter 輸出 N/A block。"""
        return _finite(self.price)

    @property
    def _prev(self) -> Optional[float]:
        # prev_close 無效時退回 price（→ change 0.00），不讓 nan 外洩
        return self.prev_close if _finite(self.prev_close) else self.price

    @property
    def change(self) -> float:
        if not self.is_valid:
            return 0.0
        return self.price - self._prev

    @property
    def pct(self) -> float:
        if not self.is_valid:
            return 0.0
        prev = self._prev
        if prev is None or prev == 0:  # 明確擋 None 與 0，避免除零
            return 0.0
        return (self.price - prev) / prev * 100.0
