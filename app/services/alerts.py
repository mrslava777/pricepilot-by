"""Сервис подписок на снижение цены."""
from __future__ import annotations

from app.database.db import get_session
from app.models.models import Alert, User
from app.services.search import search_offers


def add_alert(telegram_id: int, query: str, target_price: float) -> bool:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False
        s.add(Alert(user_id=user.id, query=query.strip(), target_price=target_price))
        return True


def list_alerts(telegram_id: int) -> list[dict]:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return []
        alerts = s.query(Alert).filter_by(user_id=user.id, active=True).all()
        return [
            {"id": a.id, "query": a.query, "target_price": a.target_price}
            for a in alerts
        ]


def remove_alert(telegram_id: int, alert_id: int) -> bool:
    with get_session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False
        alert = s.query(Alert).filter_by(id=alert_id, user_id=user.id).first()
        if alert:
            s.delete(alert)
            return True
        return False


def check_alerts() -> list[dict]:
    """Проверяет все активные подписки.

    Возвращает список срабатываний:
    {telegram_id, query, target_price, found_price, store, city, url}
    """
    triggered = []
    with get_session() as s:
        alerts = s.query(Alert).filter_by(active=True).all()
        for a in alerts:
            offers = search_offers(a.query, limit=1)  # лучшее (минимальное) предложение
            if not offers:
                continue
            best = offers[0]
            if best["price"] <= a.target_price:
                # Не спамим повторно одинаковой ценой
                if a.last_notified_price is not None and a.last_notified_price <= best["price"]:
                    continue
                user = s.query(User).filter_by(id=a.user_id).first()
                if not user:
                    continue
                a.last_notified_price = best["price"]
                triggered.append(
                    {
                        "telegram_id": user.telegram_id,
                        "query": a.query,
                        "target_price": a.target_price,
                        "found_price": best["price"],
                        "store": best["store"],
                        "city": best["city"],
                        "url": best["url"],
                    }
                )
    return triggered
