# notify/line_notifier.py — 發送 LINE Messaging API（fail-safe，不崩潰）
import os

import requests

from utils.logger import get_logger

log = get_logger("line")
_API = "https://api.line.me/v2/bot/message/push"


def send_line(text: str, silent: bool = False) -> bool:
    token = os.getenv("LINE_TOKEN")
    uid = os.getenv("LINE_ID")
    if not token or not uid:
        log.info("LINE secrets 未設定 → 跳過 LINE")
        return False
    try:
        r = requests.post(
            _API,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "to": uid,
                "messages": [{"type": "text", "text": text}],
                "notificationDisabled": bool(silent),
            },
            timeout=15,
        )
        if r.status_code == 200:
            log.info("LINE 推播成功（silent=%s）", silent)
            return True
        log.warning("LINE 失敗 %s：%s", r.status_code, r.text[:200])
        return False
    except Exception as e:  # noqa: BLE001  fail-safe
        log.warning("LINE 例外：%s", e)
        return False
