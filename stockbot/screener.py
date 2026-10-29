"""Orquesta datos + puntuación + filtros. Lo usan el CLI y el bot de Telegram."""
from dataclasses import dataclass
from pathlib import Path

from profiles import PROFILES
from scoring import Result, score_ticker


@dataclass
class Filters:
    min_cap: float = 0
    max_cap: float = float("inf")
    min_price: float = 1.0
    min_dollar_volume: float = 1e6   # liquidez mínima diaria en USD
    sector: str | None = None        # subcadena, sin distinguir mayúsculas


def run_screen(tickers: list[str], profile: str = "general", filters: Filters | None = None,
               top: int = 10) -> list[Result]:
    from data import fetch_fundamentals, fetch_prices  # import tardío: tests sin yfinance
    f = filters or Filters()
    weights = PROFILES[profile]["weights"]
    prices = fetch_prices(tickers)
    funds = fetch_fundamentals(list(prices))
    results = []
    for tk, hist in prices.items():
        fund = funds[tk]
        if fund.market_cap is not None and not (f.min_cap <= fund.market_cap <= f.max_cap):
            continue
        if f.sector and (not fund.sector or f.sector.lower() not in fund.sector.lower()):
            continue
        r = score_ticker(tk, hist, fund, weights)
        if r and r.price >= f.min_price and r.avg_dollar_volume >= f.min_dollar_volume:
            results.append(r)
    return sorted(results, key=lambda r: r.score, reverse=True)[:top]


def format_report(results: list[Result], profile: str = "general") -> str:
    out = [f"📈 Screener acciones EE. UU. — perfil: {profile}", ""]
    for i, r in enumerate(results, 1):
        cap = f"${r.market_cap / 1e9:.1f}B" if r.market_cap else "n/d"
        sec = f" · {r.sector}" if r.sector else ""
        out.append(f"{i}. {r.ticker}  score {r.score}  ${r.price:.2f}  cap {cap}{sec}")
        out.append(f"   1m {r.ret_1m:+.0%} | 3m {r.ret_3m:+.0%} | 6m {r.ret_6m:+.0%} | RSI {r.rsi:.0f}")
        if r.flags:
            out.append("   · " + "; ".join(r.flags))
    out += ["", "⚠️ Solo cribado cuantitativo con datos retrasados; no es asesoría financiera."]
    return "\n".join(out)
