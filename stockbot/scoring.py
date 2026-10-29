"""Lógica pura de puntuación: sin red, fácil de probar."""
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Fundamentals:
    market_cap: float | None = None
    revenue_growth: float | None = None   # interanual, 0.25 = 25%
    gross_margin: float | None = None
    pe: float | None = None
    sector: str | None = None


@dataclass
class Result:
    ticker: str
    score: float
    price: float
    ret_1m: float
    ret_3m: float
    ret_6m: float
    rsi: float
    rel_volume: float
    pct_from_high: float
    market_cap: float | None
    revenue_growth: float | None
    sector: str | None = None
    avg_dollar_volume: float = 0.0
    flags: list[str] = field(default_factory=list)


def rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    last_loss = loss.iloc[-1]
    if last_loss == 0:
        return 100.0
    return float(100 - 100 / (1 + gain.iloc[-1] / last_loss))


def _ret(close: pd.Series, days: int) -> float:
    if len(close) <= days:
        return float("nan")
    return float(close.iloc[-1] / close.iloc[-days - 1] - 1)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score_ticker(ticker: str, hist: pd.DataFrame, fund: Fundamentals,
                 weights: dict[str, float] | None = None) -> Result | None:
    """hist: DataFrame diario con columnas Close y Volume (>= ~130 filas).

    Cada componente vale 0..1 y se pondera con `weights` (ver profiles.py).
    Un componente sin dato (p. ej. crecimiento) sale del denominador, para no
    castigar a quien no tiene fundamentales. Score final: 0..100 menos penalizaciones.
    """
    from profiles import PROFILES
    w = weights or PROFILES["general"]["weights"]
    if hist is None or len(hist) < 130:
        return None
    close, volume = hist["Close"].dropna(), hist["Volume"].dropna()
    price = float(close.iloc[-1])
    ret_1m, ret_3m, ret_6m = _ret(close, 21), _ret(close, 63), _ret(close, 126)
    r = rsi(close)
    rel_vol = float(volume.iloc[-5:].mean() / volume.iloc[-65:-5].mean())
    high = float(close.iloc[-252:].max())
    pct_from_high = price / high - 1
    sma50 = float(close.iloc[-50:].mean())
    sma200 = float(close.iloc[-200:].mean()) if len(close) >= 200 else float("nan")
    uptrend = sma200 == sma200 and sma50 > sma200
    dollar_vol = float((close.iloc[-20:] * volume.iloc[-20:]).mean())

    flags: list[str] = []
    comp: dict[str, float | None] = {
        "momentum": (_clamp(ret_3m / 0.60) + _clamp(ret_6m / 1.00)) / 2,
        "trend": ((price > sma50) + (1 if uptrend else 0)) / 2,
        "volume": _clamp((rel_vol - 1) / 1.5),
        "near_high": _clamp(1 + pct_from_high / 0.30),
        "growth": None if fund.revenue_growth is None else _clamp(fund.revenue_growth / 0.50),
        "oversold": _clamp((40 - r) / 20) if uptrend else 0.0,
    }
    if uptrend:
        flags.append("tendencia alcista (SMA50>SMA200)")
    if rel_vol >= 1.8:
        flags.append(f"volumen {rel_vol:.1f}x lo normal")
    if pct_from_high > -0.05:
        flags.append("cerca de máximos de 52 sem")
    if fund.revenue_growth is not None and fund.revenue_growth >= 0.30:
        flags.append(f"ingresos +{fund.revenue_growth:.0%} a/a")

    used = {k: v for k, v in comp.items() if v is not None and w.get(k, 0) > 0}
    total_w = sum(w[k] for k in used)
    pts = 100 * sum(w[k] * v for k, v in used.items()) / total_w if total_w else 0.0

    if r > 80:
        pts -= w.get("rsi_penalty", 10)
        flags.append(f"RSI {r:.0f}: sobrecomprada")
    elif r < 30:
        flags.append(f"RSI {r:.0f}: sobrevendida")
    if fund.market_cap is not None and fund.market_cap < 300e6:
        pts -= w.get("microcap_penalty", 5)
        flags.append("micro-cap (<$300M): riesgo alto")

    return Result(ticker, round(pts, 1), price, ret_1m, ret_3m, ret_6m, r, rel_vol,
                  pct_from_high, fund.market_cap, fund.revenue_growth, fund.sector,
                  dollar_vol, flags)
