# Stock screener bot

Cribado de acciones tech / small caps de EE. UU. con momentum, volumen inusual y crecimiento de ingresos.

    pip install -r requirements.txt
    python bot.py --top 10 --min-cap 3e8 --max-cap 2e10
    python bot.py --telegram     # requiere TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID

Edita `watchlist.txt` para definir el universo. Pruebas: `pip install pytest && pytest`.
Score (0-100): momentum 40, tendencia 15, volumen 15, cercanía a máximos 10, crecimiento de ingresos 20; penaliza RSI>80 y micro-caps.
No es asesoría financiera.
