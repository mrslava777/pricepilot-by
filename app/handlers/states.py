"""FSM-состояния диалогов."""
from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_query = State()


class AlertStates(StatesGroup):
    waiting_query = State()
    waiting_price = State()
