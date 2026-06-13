"""Хендлеры поиска товаров."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.handlers.states import SearchStates
from app.keyboards.menus import main_menu, search_result_keyboard
from app.services.search import search_summary
from app.services.users import get_city
from app.utils.formatting import format_search_card

router = Router()


async def _do_search(message: Message, query: str) -> None:
    city = get_city(message.from_user.id)
    summary = search_summary(query, city=city)
    text = format_search_card(summary)
    has_results = bool(summary["new"] or summary["used"])
    await message.answer(
        text,
        reply_markup=search_result_keyboard(query) if has_results else main_menu(),
        disable_web_page_preview=True,
    )


@router.message(Command("search"))
@router.message(F.text == "🔍 Найти товар")
async def ask_query(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_query)
    await message.answer(
        "🔍 Напишите название товара.\n_Например: iPhone 17, Ноутбук Lenovo, PlayStation 6_"
    )


@router.message(SearchStates.waiting_query)
async def process_query(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _do_search(message, message.text)


@router.callback_query(F.data.startswith("favsearch:"))
async def favsearch_cb(callback: CallbackQuery) -> None:
    query = callback.data.split(":", 1)[1]
    await callback.answer("Ищу актуальные цены…")
    await _do_search(callback.message, query)


# Фолбэк: любой свободный текст (вне диалогов) трактуем как поисковый запрос
@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def freetext_search(message: Message) -> None:
    ignore = {
        "🔍 Найти товар",
        "📍 Выбрать город",
        "❤️ Избранное",
        "🔔 Подписки",
        "ℹ️ Помощь",
        "🏠 Меню",
    }
    if message.text in ignore:
        return
    await _do_search(message, message.text)
