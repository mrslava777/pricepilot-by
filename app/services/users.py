"""Сервис пользователей и выбора города."""
from __future__ import annotations

from app.database.db import get_session
from app.models.models import City, User


def get_or_create_user(telegram_id: int, username: str = "") -> dict:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            s.add(user)
            s.flush()
        city_name = user.city.name if user.city else None
        return {"id": user.id, "telegram_id": user.telegram_id, "city": city_name}


def set_city(telegram_id: int, city_name: str) -> bool:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        city = s.query(City).filter_by(name=city_name).first()
        if not user or not city:
            return False
        user.city_id = city.id
        return True


def get_city(telegram_id: int) -> str | None:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if user and user.city:
            return user.city.name
        return None


def get_user_id(telegram_id: int) -> int | None:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        return user.id if user else None
