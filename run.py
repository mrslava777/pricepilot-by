"""Точка входа: запуск Telegram-бота PricePilot BY."""
import asyncio

from app.bot import run_bot

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 PricePilot BY остановлен")
