# state/idempotency.py — 防重複推播（已推 → SKIP）
#
# 狀態檔 state/sent.json 由 GitHub Actions 於 schedule 模式 commit 回 repo，
# 達成跨 runner 去重。manual 補播不受此限（一律放行）。
import json
import os
import tempfile
from datetime import datetime, timezone

from utils.logger import get_logger

log = get_logger("idempotency")

_STATE_FILE = os.path.join("state", "sent.json")
_MAX_KEEP = 60  # 僅保留最近 N 筆，避免無限膨脹


def _load() -> dict:
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def already_sent(key: str) -> bool:
    return key in _load()


def mark_sent(key: str) -> None:
    data = _load()
    data[key] = datetime.now(timezone.utc).isoformat()
    if len(data) > _MAX_KEEP:
        for old in sorted(data, key=lambda k: data[k])[: len(data) - _MAX_KEEP]:
            data.pop(old, None)
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    # atomic write：先寫 tmp 再 os.replace，避免寫到一半中斷造成 JSON 損毀
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(_STATE_FILE), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())  # 確保資料落盤後才 rename
        os.replace(tmp, _STATE_FILE)  # 同檔案系統 rename → 原子操作
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    log.info("已標記推播：%s", key)
