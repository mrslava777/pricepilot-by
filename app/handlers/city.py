"""Хендлеры выбора города."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.menus import cities_keyboard
from app.services.users import get_city, set_city

router = Router()


@router.message(Command("city"))
@router.message(F.text == "📍 Выбрать город")
async def choose_city(message: Message) -> None:
    current = get_city(message.from_user.id)
    text = "📍 *Выберите ваш город:*"
    if current:
        text += f"\n\nТекущий город: *{current}*"
    await message.answer(text, reply_markup=cities_keyboard())


@router.callback_query(F.data.startswith("city:"))
async def set_city_cb(callback: CallbackQuery) -> None:
    city = callback.data.split(":", 1)[1]
    set_city(callback.from_user.id, city)
    await callback.message.edit_text(f"✅ Город сохранён: *{city}*")
    await callback.answer(f"Город: {city}")
