"""Создание и настройка бота, диспетчера и фоновых задач."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import settings
from app.database.db import init_db
from app.database.seed import seed_db
from app.handlers import get_main_router
from app.services.alerts import check_alerts

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="search", description="Найти товар"),
            BotCommand(command="city", description="Выбрать город"),
            BotCommand(command="favorites", description="Избранное"),
            BotCommand(command="alerts", description="Подписки на цену"),
            BotCommand(command="help", description="Помощь"),
        ]
    )


async def alert_worker(bot: Bot) -> None:
    """Фоновая проверка подписок на снижение цены."""
    while True:
        try:
            for hit in check_alerts():
                text = (
                    "🔔 *Цена снижена!*\n\n"
                    f"🛒 {hit['query']}\n"
                    f"💰 Сейчас: *{hit['found_price']:.0f} BYN* "
                    f"(ваша цель ≤ {hit['target_price']:.0f} BYN)\n"
                    f"🏪 {hit['store']} ({hit['city']})\n"
                    f"🔗 {hit['url']}"
                )
                try:
                    await bot.send_message(hit["telegram_id"], text, disable_web_page_preview=True)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Не удалось отправить уведомление: %s", e)
        except Exception as e:  # noqa: BLE001
            logger.exception("Ошибка в alert_worker: %s", e)
        await asyncio.sleep(settings.alert_interval)


def create_bot() -> Bot:
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен от @BotFather."
        )
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(get_main_router())
    return dp


async def run_bot() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    seed_db()  # наполняем демо-каталог при первом запуске

    bot = create_bot()
    dp = create_dispatcher()

    await set_commands(bot)
    asyncio.create_task(alert_worker(bot))

    logger.info("🚀 PricePilot BY запущен")
    await dp.start_polling(bot)
