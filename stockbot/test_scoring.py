import numpy as np
import pandas as pd

from backtest import backtest_frames, summarize
from profiles import PROFILES
from scoring import Fundamentals, rsi, score_ticker


def make(drift, n=260, vol_boost=1.0, seed=0):
    rng = np.random.default_rng(seed)
    close = 20 * np.cumprod(1 + drift + rng.normal(0, 0.01, n))
    volume = np.full(n, 1e6)
    volume[-5:] *= vol_boost
    return pd.DataFrame({"Close": close, "Volume": volume})


def test_winner_beats_loser():
    win = score_ticker("W", make(0.006, vol_boost=3), Fundamentals(5e9, 0.6))
    lose = score_ticker("L", make(-0.003), Fundamentals(5e9, -0.05))
    assert win.score > lose.score
    assert any("volumen" in f for f in win.flags)
    assert 0 <= lose.score <= 100 and win.score <= 100


def test_microcap_penalty_and_short_history():
    big = score_ticker("A", make(0.004), Fundamentals(5e9, 0.3))
    micro = score_ticker("A", make(0.004), Fundamentals(1e8, 0.3))
    assert micro.score == big.score - 5
    assert score_ticker("X", make(0.004, n=50), Fundamentals()) is None


def test_missing_growth_not_punished():
    # sin dato de crecimiento el componente sale del denominador
    r = score_ticker("A", make(0.006), Fundamentals(5e9, None), PROFILES["momentum"]["weights"])
    assert r.score > 50


def test_profiles_change_ranking():
    breakout = score_ticker("A", make(0.002, vol_boost=4), Fundamentals(5e9, None), PROFILES["breakout"]["weights"])
    quiet = score_ticker("A", make(0.002, vol_boost=1), Fundamentals(5e9, None), PROFILES["breakout"]["weights"])
    assert breakout.score > quiet.score


def test_rsi_bounds():
    assert rsi(pd.Series(range(1, 60), dtype=float)) == 100.0
    assert 0 <= rsi(make(0.0)["Close"]) <= 100


def test_backtest_runs():
    prices = {f"T{i}": make(0.001 * (i - 3), n=400, seed=i) for i in range(6)}
    obs = backtest_frames(prices, PROFILES["momentum"]["weights"])
    assert len(obs) > 10
    assert len(summarize(obs)) == 5
