"""Хендлеры старта и главного меню."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.keyboards.menus import main_menu
from app.services.users import get_or_create_user

router = Router()

WELCOME = (
    "👋 *PricePilot BY*\n"
    "_Найду дешевле. Скажу когда покупать._\n\n"
    "Я помогу найти самые дешёвые товары в Беларуси.\n\n"
    "Что умею:\n"
    "🔍 Искать товары и сравнивать цены\n"
    "📍 Учитывать ваш город\n"
    "🆕/♻️ Показывать новые и Б/У товары\n"
    "🔔 Уведомлять о снижении цены\n"
    "❤️ Сохранять избранное\n\n"
    "Выберите действие в меню или просто напишите название товара 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = get_or_create_user(message.from_user.id, message.from_user.username or "")
    text = WELCOME
    if not user.get("city"):
        text += "\n\n💡 Совет: задайте город через «📍 Выбрать город» для точных результатов."
    await message.answer(text, reply_markup=main_menu())


@router.message(Command("menu"))
@router.message(F.text == "🏠 Меню")
async def cmd_menu(message: Message) -> None:
    await message.answer("Главное меню 👇", reply_markup=main_menu())
