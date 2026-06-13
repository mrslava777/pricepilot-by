"""Хендлер помощи."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

HELP_TEXT = (
    "ℹ️ *Помощь — PricePilot BY*\n\n"
    "*Как искать:*\n"
    "Нажмите «🔍 Найти товар» или просто отправьте название, например:\n"
    "`iPhone 17`, `Ноутбук Lenovo`, `PlayStation 6`\n\n"
    "*Город:* «📍 Выбрать город» — бот запомнит и будет показывать предложения в нём.\n\n"
    "*Новые и Б/У:* в карточке результата показываются обе секции с разницей в цене.\n\n"
    "*Подписка на цену:* «🔔 Подписки» → укажите товар и желаемую цену. "
    "Когда цена опустится ниже — пришлю уведомление.\n\n"
    "*Избранное:* «❤️ Избранное» — сохраняйте товары и быстро проверяйте цены.\n\n"
    "*Команды:* /start, /menu, /help\n\n"
    "_Примечание: в демо-версии цены берутся из встроенного каталога. "
    "Подключение реальных магазинов — следующий этап развития._"
)


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
