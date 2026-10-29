"""Capa de datos (yfinance + Wikipedia para universos). Sustituible sin tocar scoring.py."""
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from scoring import Fundamentals

CACHE = Path.home() / ".cache" / "stockbot"
FUND_TTL = 24 * 3600
UA = {"User-Agent": "Mozilla/5.0 (stockbot)"}
WIKI = {
    "sp500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "nasdaq100": "https://en.wikipedia.org/wiki/Nasdaq-100",
}


def load_universe(name: str, watchlist: Path) -> list[str]:
    """name: watchlist | sp500 | nasdaq100 | sp500+nasdaq100 (unión)."""
    tickers: list[str] = []
    for part in name.split("+"):
        if part == "watchlist":
            lines = (l.split("#")[0].strip().upper() for l in watchlist.read_text().splitlines())
            tickers += [l for l in lines if l]
        elif part in WIKI:
            html = requests.get(WIKI[part], headers=UA, timeout=30).text
            for t in pd.read_html(io.StringIO(html)):
                col = next((c for c in t.columns if str(c) in ("Symbol", "Ticker")), None)
                if col is not None and len(t) > 50:
                    tickers += [str(s).replace(".", "-").upper() for s in t[col]]
                    break
            else:
                raise RuntimeError(f"No encontré la tabla de tickers de {part}")
        else:
            raise ValueError(f"Universo desconocido: {part}")
    return list(dict.fromkeys(tickers))


def fetch_prices(tickers: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """Descarga en lote (rápido); devuelve {ticker: DataFrame con Close/Volume}."""
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), 100):
        chunk = tickers[i:i + 100]
        df = yf.download(chunk, period=period, interval="1d", auto_adjust=True,
                         group_by="ticker", threads=True, progress=False)
        if df is None or df.empty:
            continue
        for tk in chunk:
            sub = df if len(chunk) == 1 else (df[tk] if tk in df.columns.get_level_values(0) else None)
            if sub is not None:
                sub = sub.dropna(subset=["Close"])
                if len(sub):
                    out[tk] = sub
    return out


def _fund_one(ticker: str) -> Fundamentals:
    path = CACHE / f"{ticker}.json"
    try:
        if path.exists() and time.time() - path.stat().st_mtime < FUND_TTL:
            return Fundamentals(**json.loads(path.read_text()))
    except Exception:
        pass
    info = yf.Ticker(ticker).info or {}
    f = Fundamentals(market_cap=info.get("marketCap"), revenue_growth=info.get("revenueGrowth"),
                     gross_margin=info.get("grossMargins"), pe=info.get("trailingPE"),
                     sector=info.get("sector"))
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(f.__dict__))
    return f


def fetch_fundamentals(tickers: list[str], workers: int = 8) -> dict[str, Fundamentals]:
    def safe(tk: str) -> Fundamentals:
        try:
            return _fund_one(tk)
        except Exception:
            return Fundamentals()
    with ThreadPoolExecutor(workers) as ex:
        return dict(zip(tickers, ex.map(safe, tickers)))
