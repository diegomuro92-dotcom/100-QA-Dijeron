"""Backtest de la puntuación técnica: ¿los scores altos rinden más a 21 días?

  python backtest.py --universe sp500 --profile momentum

Solo usa componentes técnicos (los fundamentales de Yahoo son de hoy y meterían
sesgo de anticipación). Es una validación orientativa, no una garantía.
"""
import argparse
from pathlib import Path

import pandas as pd

from profiles import PROFILES
from scoring import Fundamentals, score_ticker


def backtest_frames(prices: dict[str, pd.DataFrame], weights: dict, horizon: int = 21,
                    step: int = 21, warmup: int = 252) -> pd.DataFrame:
    rows = []
    for tk, df in prices.items():
        close = df["Close"].to_numpy()
        for i in range(warmup, len(df) - horizon, step):
            r = score_ticker(tk, df.iloc[:i], Fundamentals(), weights)
            if r:
                rows.append((tk, r.score, close[i - 1 + horizon] / close[i - 1] - 1))
    return pd.DataFrame(rows, columns=["ticker", "score", "fwd"])


def summarize(obs: pd.DataFrame, buckets: int = 5) -> pd.DataFrame:
    obs = obs.copy()
    obs["bucket"] = pd.qcut(obs["score"].rank(method="first"), buckets, labels=range(1, buckets + 1))
    g = obs.groupby("bucket", observed=True)["fwd"]
    return pd.DataFrame({"n": g.size(), "ret_medio": g.mean(), "mediana": g.median(),
                         "%_positivos": g.apply(lambda s: (s > 0).mean())})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="watchlist")
    ap.add_argument("--watchlist", type=Path, default=Path(__file__).with_name("watchlist.txt"))
    ap.add_argument("--profile", choices=PROFILES, default="momentum")
    a = ap.parse_args()
    from data import fetch_prices, load_universe
    prices = fetch_prices(load_universe(a.universe, a.watchlist), period="5y")
    obs = backtest_frames(prices, PROFILES[a.profile]["weights"])
    if obs.empty:
        print("Sin datos suficientes.")
        return
    print(f"{len(obs)} observaciones de {obs.ticker.nunique()} tickers; bucket 5 = scores más altos\n")
    print(summarize(obs).to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
