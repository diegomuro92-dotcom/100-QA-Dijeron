"""Capa de datos (yfinance). Sustituible por otra fuente sin tocar scoring.py."""
import pandas as pd
import yfinance as yf

from scoring import Fundamentals


def fetch(ticker: str) -> tuple[pd.DataFrame, Fundamentals]:
    t = yf.Ticker(ticker)
    hist = t.history(period="1y", interval="1d", auto_adjust=True)
    info = t.info or {}
    return hist, Fundamentals(
        market_cap=info.get("marketCap"),
        revenue_growth=info.get("revenueGrowth"),
        gross_margin=info.get("grossMargins"),
        sector=info.get("sector"),
    )
