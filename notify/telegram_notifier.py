# notify/telegram_notifier.py — 發送 Telegram（fail-safe，不崩潰）
import os

import requests

from utils.logger import get_logger

log = get_logger("telegram")
_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(text: str, silent: bool = False) -> bool:
    token = os.getenv("TG_TOKEN")
    chat = os.getenv("TG_CHAT")
    if not token or not chat:
        log.info("Telegram secrets 未設定 → 跳過 Telegram")
        return False
    try:
        r = requests.post(
            _API.format(token=token),
            json={
                "chat_id": chat,
                "text": text,
                "disable_notification": bool(silent),
            },
            timeout=15,
        )
        ok = False
        if r.status_code == 200:
            try:
                ok = bool(r.json().get("ok"))
            except Exception:  # noqa: BLE001  body 非 JSON 時視為失敗
                ok = False
        if ok:
            log.info("Telegram 推播成功（silent=%s）", silent)
            return True
        log.warning("Telegram 失敗 status=%s body=%s", r.status_code, r.text[:200])
        return False
    except Exception as e:  # noqa: BLE001  fail-safe
        log.warning("Telegram 例外：%s", e)
        return False
