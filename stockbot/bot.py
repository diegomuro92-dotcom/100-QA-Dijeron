"""Screener de acciones tech / small caps de EE. UU. con potencial de crecimiento.

Uso:
  python bot.py                      # imprime el ranking
  python bot.py --top 5 --min-cap 3e8 --max-cap 2e10
  python bot.py --telegram           # además lo envía a Telegram
                                     # (TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID)
"""
import argparse
import os
import sys
from pathlib import Path

import requests

from scoring import Result, score_ticker


def load_watchlist(path: Path) -> list[str]:
    lines = (l.split("#")[0].strip().upper() for l in path.read_text().splitlines())
    return list(dict.fromkeys(l for l in lines if l))


def format_report(results: list[Result]) -> str:
    out = ["📈 Screener de crecimiento (EE. UU.)", ""]
    for i, r in enumerate(results, 1):
        cap = f"${r.market_cap / 1e9:.1f}B" if r.market_cap else "n/d"
        out.append(f"{i}. {r.ticker}  score {r.score}  ${r.price:.2f}  cap {cap}")
        out.append(f"   1m {r.ret_1m:+.0%} | 3m {r.ret_3m:+.0%} | 6m {r.ret_6m:+.0%} | RSI {r.rsi:.0f}")
        if r.flags:
            out.append("   · " + "; ".join(r.flags))
    out += ["", "⚠️ Solo cribado cuantitativo con datos retrasados; no es asesoría financiera."]
    return "\n".join(out)


def send_telegram(text: str) -> None:
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                         json={"chat_id": chat, "text": text}, timeout=30)
    resp.raise_for_status()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watchlist", type=Path, default=Path(__file__).with_name("watchlist.txt"))
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-cap", type=float, default=0)
    ap.add_argument("--max-cap", type=float, default=float("inf"))
    ap.add_argument("--telegram", action="store_true")
    args = ap.parse_args()

    from data import fetch  # import tardío: scoring/tests no requieren yfinance

    results: list[Result] = []
    for tk in load_watchlist(args.watchlist):
        try:
            hist, fund = fetch(tk)
            if fund.market_cap and not (args.min_cap <= fund.market_cap <= args.max_cap):
                continue
            r = score_ticker(tk, hist, fund)
            if r:
                results.append(r)
        except Exception as e:  # un ticker fallido no debe tumbar el resto
            print(f"[aviso] {tk}: {e}", file=sys.stderr)

    if not results:
        print("Sin resultados (¿sin conexión a Yahoo Finance?).", file=sys.stderr)
        return 1
    report = format_report(sorted(results, key=lambda r: r.score, reverse=True)[: args.top])
    print(report)
    if args.telegram:
        send_telegram(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
