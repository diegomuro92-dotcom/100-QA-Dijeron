"""Bot de Telegram con comandos (long polling, solo requests).

  export TELEGRAM_BOT_TOKEN=... ; export TELEGRAM_CHAT_ID=...   # CHAT_ID restringe quién puede usarlo
  python telegram_bot.py

Comandos: /top [perfil] [universo] · /analiza TICKER · /perfiles · /ayuda
"""
import os
import time
from pathlib import Path

import requests

from profiles import PROFILES
from screener import format_report, run_screen

WATCHLIST = Path(__file__).with_name("watchlist.txt")
HELP = ("/top [perfil] [universo]  p. ej. /top breakout sp500\n"
        "/analiza TICKER\n/perfiles\nUniversos: watchlist, sp500, nasdaq100 (combina con +)")


def handle(text: str) -> str:
    from data import load_universe
    parts = text.strip().split()
    cmd = parts[0].split("@")[0].lower() if parts else ""
    if cmd in ("/start", "/ayuda", "/help"):
        return HELP
    if cmd == "/perfiles":
        return "\n".join(f"{k}: {v['desc']}" for k, v in PROFILES.items())
    if cmd == "/top":
        profile = parts[1] if len(parts) > 1 else "general"
        universe = parts[2] if len(parts) > 2 else "watchlist"
        if profile not in PROFILES:
            return f"Perfil desconocido. Opciones: {', '.join(PROFILES)}"
        res = run_screen(load_universe(universe, WATCHLIST), profile, top=8)
        return format_report(res, profile) if res else "Sin resultados."
    if cmd == "/analiza" and len(parts) > 1:
        res = run_screen([parts[1].upper()], "general", top=1)
        return format_report(res) if res else "No encontré datos suficientes para ese ticker."
    return HELP


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    allowed = os.environ.get("TELEGRAM_CHAT_ID")
    api = f"https://api.telegram.org/bot{token}"
    offset = 0
    while True:
        try:
            updates = requests.get(f"{api}/getUpdates", params={"timeout": 50, "offset": offset},
                                   timeout=60).json().get("result", [])
        except requests.RequestException:
            time.sleep(5)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            chat, text = str(msg.get("chat", {}).get("id")), msg.get("text", "")
            if not text.startswith("/") or (allowed and chat != allowed):
                continue
            try:
                reply = handle(text)
            except Exception as e:
                reply = f"Error: {e}"
            requests.post(f"{api}/sendMessage", json={"chat_id": chat, "text": reply[:4096]}, timeout=30)


if __name__ == "__main__":
    main()
