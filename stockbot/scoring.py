"""Lógica pura de puntuación: sin red, fácil de probar."""
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Fundamentals:
    market_cap: float | None = None
    revenue_growth: float | None = None   # interanual, 0.25 = 25%
    gross_margin: float | None = None
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


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_ticker(ticker: str, hist: pd.DataFrame, fund: Fundamentals) -> Result | None:
    """hist: DataFrame diario con columnas Close y Volume (>= ~130 filas)."""
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

    flags: list[str] = []
    # Momentum (0-40): rendimiento 3m y 6m
    pts = 0.0
    pts += _clamp(ret_3m / 0.60, 0, 1) * 20
    pts += _clamp(ret_6m / 1.00, 0, 1) * 20
    # Tendencia (0-15)
    if price > sma50:
        pts += 7.5
    if sma200 == sma200 and sma50 > sma200:  # nan-safe
        pts += 7.5
        flags.append("tendencia alcista (SMA50>SMA200)")
    # Volumen inusual (0-15)
    pts += _clamp((rel_vol - 1) / 1.5, 0, 1) * 15
    if rel_vol >= 1.8:
        flags.append(f"volumen {rel_vol:.1f}x lo normal")
    # Cercanía a máximos de 52 semanas (0-10)
    pts += _clamp(1 + pct_from_high / 0.30, 0, 1) * 10
    if pct_from_high > -0.05:
        flags.append("cerca de máximos de 52 sem")
    # Crecimiento de ingresos (0-20)
    if fund.revenue_growth is not None:
        pts += _clamp(fund.revenue_growth / 0.50, 0, 1) * 20
        if fund.revenue_growth >= 0.30:
            flags.append(f"ingresos +{fund.revenue_growth:.0%} a/a")
    # Penalizaciones
    if r > 80:
        pts -= 10
        flags.append(f"RSI {r:.0f}: sobrecomprada")
    elif r < 30:
        flags.append(f"RSI {r:.0f}: sobrevendida")
    if fund.market_cap is not None and fund.market_cap < 300e6:
        pts -= 5
        flags.append("micro-cap (<$300M): riesgo alto")

    return Result(ticker, round(pts, 1), price, ret_1m, ret_3m, ret_6m, r,
                  rel_vol, pct_from_high, fund.market_cap, fund.revenue_growth, flags)
