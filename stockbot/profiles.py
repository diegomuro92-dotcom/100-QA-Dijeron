"""Perfiles de búsqueda: solo cambian los pesos. Añade el tuyo aquí."""

PENALTIES = {"rsi_penalty": 10, "microcap_penalty": 5}

PROFILES = {
    "general": {
        "desc": "Equilibrado: momentum, tendencia, volumen y crecimiento",
        "weights": {"momentum": 40, "trend": 15, "volume": 15, "near_high": 10, "growth": 20, **PENALTIES},
    },
    "growth": {
        "desc": "Prioriza crecimiento de ingresos",
        "weights": {"momentum": 25, "trend": 10, "volume": 10, "near_high": 5, "growth": 50, **PENALTIES},
    },
    "momentum": {
        "desc": "Fuerza de precio y tendencia, ignora fundamentales",
        "weights": {"momentum": 60, "trend": 20, "volume": 10, "near_high": 10, **PENALTIES},
    },
    "breakout": {
        "desc": "Volumen inusual cerca de máximos (posibles rupturas)",
        "weights": {"momentum": 15, "trend": 15, "volume": 35, "near_high": 35, **PENALTIES},
    },
    "dip": {
        "desc": "Retrocesos (RSI bajo) dentro de una tendencia alcista",
        "weights": {"oversold": 50, "trend": 25, "growth": 15, "momentum": 10, **PENALTIES},
    },
}
