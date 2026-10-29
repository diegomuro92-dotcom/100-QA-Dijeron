---
name: stock-screener
description: Analiza acciones de EE. UU. con el screener del repo (stockbot). Úsalo cuando el usuario pida buscar, rankear o analizar acciones, escanear el mercado, o probar un perfil (general, growth, momentum, breakout, dip) o un ticker concreto.
---

# Stock screener

Corre `stockbot/bot.py` y explica el resultado en español. No es asesoría financiera; dilo brevemente al final.

## Pasos

1. Dependencias (una vez por sesión): `pip install -q -r stockbot/requirements.txt`
2. Traduce lo que pide el usuario a argumentos y corre desde `stockbot/`:
   - Universo: `--universe watchlist|sp500|nasdaq100` (se combinan con `+`)
   - Perfil: `--profile general|growth|momentum|breakout|dip`
   - Filtros: `--sector`, `--min-cap`, `--max-cap`, `--min-dollar-volume`, `--top N`
   - Ejemplo: `python stockbot/bot.py --universe sp500 --profile breakout --top 10`
3. Un ticker concreto: crea un archivo temporal con ese ticker y pásalo con `--watchlist`.
4. Valida la estrategia si el usuario lo pide: `python stockbot/backtest.py --universe sp500 --profile momentum`
5. Resume el top en una tabla corta (ticker, score, precio, banderas) y comenta qué señales pesan más.

## Si falla

- Error de conexión a `finance.yahoo.com`, `query1/query2.finance.yahoo.com`, `fc.yahoo.com` o `en.wikipedia.org`: el entorno bloquea el host. Dile al usuario que en la configuración del entorno (menú del entorno en la barra del título → Edit → Network access) permita esos dominios. No inventes ni simules resultados.
- "Sin resultados": filtros muy estrictos o sin datos; sugiere relajarlos.

## Ampliar

Perfiles nuevos: añade pesos en `stockbot/profiles.py`. Pruebas: `cd stockbot && pytest`.
