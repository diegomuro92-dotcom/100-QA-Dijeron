"""Screener de acciones de EE. UU.

  python bot.py                                   # watchlist.txt, perfil general
  python bot.py --universe sp500 --profile breakout --top 15
  python bot.py --universe sp500+nasdaq100 --sector tech --min-cap 2e9
  python bot.py --telegram                        # envía el resultado (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
"""
import argparse
import os
import sys
from pathlib import Path

import requests

from profiles import PROFILES
from screener import Filters, format_report, run_screen


def send_telegram(text: str) -> None:
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                  json={"chat_id": chat, "text": text[:4096]}, timeout=30).raise_for_status()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="watchlist", help="watchlist | sp500 | nasdaq100 (combina con +)")
    ap.add_argument("--watchlist", type=Path, default=Path(__file__).with_name("watchlist.txt"))
    ap.add_argument("--profile", choices=PROFILES, default="general")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-cap", type=float, default=0)
    ap.add_argument("--max-cap", type=float, default=float("inf"))
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--min-dollar-volume", type=float, default=1e6)
    ap.add_argument("--sector", help="p. ej. technology, healthcare, energy")
    ap.add_argument("--telegram", action="store_true")
    a = ap.parse_args()

    from data import load_universe
    try:
        tickers = load_universe(a.universe, a.watchlist)
    except Exception as e:
        print(f"No pude cargar el universo '{a.universe}': {e}", file=sys.stderr)
        return 1
    results = run_screen(tickers, a.profile,
                         Filters(a.min_cap, a.max_cap, a.min_price, a.min_dollar_volume, a.sector), a.top)
    if not results:
        print("Sin resultados (¿sin conexión a Yahoo Finance o filtros muy estrictos?).", file=sys.stderr)
        return 1
    report = format_report(results, a.profile)
    print(report)
    if a.telegram:
        send_telegram(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
