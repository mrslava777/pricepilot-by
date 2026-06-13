"""Хендлеры подписок на снижение цены."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.handlers.states import AlertStates
from app.keyboards.menus import alerts_keyboard
from app.services.alerts import add_alert, list_alerts, remove_alert
from app.utils.formatting import format_alerts

router = Router()


@router.message(Command("alerts"))
@router.message(F.text == "🔔 Подписки")
async def show_alerts(message: Message) -> None:
    alerts = list_alerts(message.from_user.id)
    text = format_alerts(alerts)
    text += "\n\n➕ Чтобы добавить подписку — отправьте /subscribe"
    await message.answer(text, reply_markup=alerts_keyboard(alerts))


@router.message(Command("subscribe"))
async def start_subscribe(message: Message, state: FSMContext) -> None:
    await state.set_state(AlertStates.waiting_query)
    await message.answer("🔔 Введите название товара для подписки:")


@router.callback_query(F.data.startswith("sub:"))
async def subscribe_from_card(callback: CallbackQuery, state: FSMContext) -> None:
    query = callback.data.split(":", 1)[1]
    await state.update_data(query=query)
    await state.set_state(AlertStates.waiting_price)
    await callback.message.answer(
        f"🔔 Подписка на *{query}*.\nВведите желаемую цену в BYN (например: 3500):"
    )
    await callback.answer()


@router.message(AlertStates.waiting_query)
async def alert_query(message: Message, state: FSMContext) -> None:
    await state.update_data(query=message.text.strip())
    await state.set_state(AlertStates.waiting_price)
    await message.answer("Введите желаемую цену в BYN (например: 3500):")


@router.message(AlertStates.waiting_price)
async def alert_price(message: Message, state: FSMContext) -> None:
    raw = message.text.replace(",", ".").replace("BYN", "").strip()
    try:
        price = float(raw)
    except ValueError:
        await message.answer("⚠️ Введите число, например: 3500")
        return
    data = await state.get_data()
    await state.clear()
    add_alert(message.from_user.id, data["query"], price)
    await message.answer(
        f"✅ Подписка создана!\n🔔 *{data['query']}* → уведомлю, когда цена будет ≤ *{price:.0f} BYN*"
    )


@router.callback_query(F.data.startswith("subdel:"))
async def del_alert_cb(callback: CallbackQuery) -> None:
    alert_id = int(callback.data.split(":", 1)[1])
    remove_alert(callback.from_user.id, alert_id)
    alerts = list_alerts(callback.from_user.id)
    await callback.message.edit_text(format_alerts(alerts), reply_markup=alerts_keyboard(alerts))
    await callback.answer("Подписка удалена")


@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery) -> None:
    await callback.answer()
