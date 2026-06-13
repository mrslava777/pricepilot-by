"""Клавиатуры и меню Telegram."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.config import CITIES


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню (нижние кнопки)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти товар")],
            [KeyboardButton(text="📍 Выбрать город"), KeyboardButton(text="❤️ Избранное")],
            [KeyboardButton(text="🔔 Подписки"), KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите название товара…",
    )


def cities_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, city in enumerate(CITIES, 1):
        row.append(InlineKeyboardButton(text=city, callback_data=f"city:{city}"))
        if i % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_result_keyboard(query: str) -> InlineKeyboardMarkup:
    """Кнопки под карточкой результата поиска."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav:{query[:48]}"),
                InlineKeyboardButton(text="🔔 Подписка", callback_data=f"sub:{query[:48]}"),
            ]
        ]
    )


def favorites_keyboard(favorites: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for f in favorites:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🔄 Цены: {f['title'][:24]}", callback_data=f"favsearch:{f['title'][:40]}"
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"favdel:{f['product_id']}"),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="—", callback_data="noop")]])


def alerts_keyboard(alerts: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for a in alerts:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {a['query'][:30]} (≤{a['target_price']:.0f})",
                    callback_data=f"subdel:{a['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="—", callback_data="noop")]])
