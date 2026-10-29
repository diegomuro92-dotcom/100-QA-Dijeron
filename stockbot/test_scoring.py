import numpy as np
import pandas as pd

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


def test_microcap_penalty_and_short_history():
    big = score_ticker("A", make(0.004), Fundamentals(5e9, 0.3))
    micro = score_ticker("A", make(0.004), Fundamentals(1e8, 0.3))
    assert micro.score == big.score - 5
    assert score_ticker("X", make(0.004, n=50), Fundamentals()) is None


def test_rsi_bounds():
    assert rsi(pd.Series(range(1, 60), dtype=float)) == 100.0
    assert 0 <= rsi(make(0.0)["Close"]) <= 100
