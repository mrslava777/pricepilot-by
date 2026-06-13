"""Сервис избранного."""
from __future__ import annotations

from app.database.db import get_session
from app.models.models import Favorite, Product, User


def _resolve_product(s, query: str) -> Product | None:
    return (
        s.query(Product)
        .filter(Product.title.ilike(f"%{query.strip()}%"))
        .order_by(Product.title)
        .first()
    )


def add_favorite(telegram_id: int, query: str) -> str | None:
    """Добавляет первый подходящий товар в избранное. Возвращает название."""
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        product = _resolve_product(s, query)
        if not user or not product:
            return None
        exists = (
            s.query(Favorite)
            .filter_by(user_id=user.id, product_id=product.id)
            .first()
        )
        if not exists:
            s.add(Favorite(user_id=user.id, product_id=product.id))
        return product.title


def remove_favorite(telegram_id: int, product_id: int) -> bool:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False
        fav = (
            s.query(Favorite)
            .filter_by(user_id=user.id, product_id=product_id)
            .first()
        )
        if fav:
            s.delete(fav)
            return True
        return False


def list_favorites(telegram_id: int) -> list[dict]:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return []
        favs = s.query(Favorite).filter_by(user_id=user.id).all()
        return [{"product_id": f.product_id, "title": f.product.title} for f in favs]
