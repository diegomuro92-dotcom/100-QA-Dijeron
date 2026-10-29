# Stock screener bot (acciones de EE. UU.)

Cribado cuantitativo del mercado: momentum, tendencia, volumen inusual, cercanía a máximos y crecimiento de ingresos.

    pip install -r requirements.txt
    python bot.py                                              # watchlist.txt
    python bot.py --universe sp500 --profile breakout --top 15
    python bot.py --universe sp500+nasdaq100 --sector tech --min-cap 2e9
    python bot.py --telegram                                   # envía el ranking
    python telegram_bot.py                                     # bot con comandos /top /analiza /perfiles
    python backtest.py --universe sp500 --profile momentum     # ¿los scores altos rinden más?
    pip install pytest && pytest

Variables de Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (esta última restringe quién puede usar el bot).

**Perfiles** (`profiles.py`): general, growth, momentum, breakout, dip. Para algo más específico,
añade un perfil con tus pesos o usa los filtros (`--sector`, `--min-cap`, `--max-cap`, `--min-dollar-volume`).
Los fundamentales se cachean 24 h en `~/.cache/stockbot`.

No es asesoría financiera: datos retrasados de Yahoo Finance y una heurística, no una predicción.
