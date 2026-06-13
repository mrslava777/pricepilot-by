"""Хендлеры избранного."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.menus import favorites_keyboard
from app.services.favorites import add_favorite, list_favorites, remove_favorite
from app.utils.formatting import format_favorites

router = Router()


@router.message(Command("favorites"))
@router.message(F.text == "❤️ Избранное")
async def show_favorites(message: Message) -> None:
    favs = list_favorites(message.from_user.id)
    await message.answer(format_favorites(favs), reply_markup=favorites_keyboard(favs))


@router.callback_query(F.data.startswith("fav:"))
async def add_favorite_cb(callback: CallbackQuery) -> None:
    query = callback.data.split(":", 1)[1]
    title = add_favorite(callback.from_user.id, query)
    if title:
        await callback.answer(f"❤️ Добавлено: {title}")
    else:
        await callback.answer("Не удалось добавить", show_alert=True)


@router.callback_query(F.data.startswith("favdel:"))
async def del_favorite_cb(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":", 1)[1])
    remove_favorite(callback.from_user.id, product_id)
    favs = list_favorites(callback.from_user.id)
    await callback.message.edit_text(
        format_favorites(favs), reply_markup=favorites_keyboard(favs)
    )
    await callback.answer("Удалено")
