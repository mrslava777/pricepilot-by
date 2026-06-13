"""Сервис поиска товаров и цен.

В MVP читает предложения из локальной БД (демо-каталог).
Чтобы подключить реальные источники (Onliner, Kufar, Евроопт и т.д.) —
наполняйте таблицу offers данными парсеров; интерфейс функций менять не нужно.
"""
from __future__ import annotations

from sqlalchemy import func

from app.database.db import get_session
from app.models.models import Offer, Product, Store, City


def _offer_to_dict(offer: Offer) -> dict:
    return {
        "product": offer.product.title,
        "store": offer.store.name,
        "city": offer.city.name,
        "price": offer.price,
        "condition": offer.condition,
        "url": offer.url,
        "source": offer.source,
    }


def _stats(offers: list[dict]) -> dict:
    """Минимальная, средняя цена и количество предложений."""
    if not offers:
        return {"min": None, "avg": None, "count": 0}
    prices = [o["price"] for o in offers]
    return {
        "min": round(min(prices), 2),
        "avg": round(sum(prices) / len(prices), 2),
        "count": len(prices),
    }


def search_offers(query: str, city: str | None = None, condition: str | None = None,
                  limit: int = 10) -> list[dict]:
    """Поиск предложений по названию товара.

    :param query: текст запроса (часть названия товара)
    :param city: фильтр по городу (опционально)
    :param condition: 'new' | 'used' | None (любое)
    """
    query = (query or "").strip()
    if not query:
        return []

    with get_session() as s:
        q = (
            s.query(Offer)
            .join(Product, Offer.product_id == Product.id)
            .filter(Product.title.ilike(f"%{query}%"))
        )
        if city:
            q = q.join(City, Offer.city_id == City.id).filter(City.name == city)
        if condition in ("new", "used"):
            q = q.filter(Offer.condition == condition)

        offers = q.order_by(Offer.price.asc()).limit(limit).all()
        return [_offer_to_dict(o) for o in offers]


def search_summary(query: str, city: str | None = None) -> dict:
    """Сводка: новые и б/у предложения + статистика и экономия."""
    new_offers = search_offers(query, city=city, condition="new")
    used_offers = search_offers(query, city=city, condition="used")
    all_offers = new_offers + used_offers

    summary = {
        "query": query,
        "city": city,
        "new": new_offers,
        "used": used_offers,
        "min_new": new_offers[0]["price"] if new_offers else None,
        "min_used": used_offers[0]["price"] if used_offers else None,
        # Статистика: min / avg / count
        "stats_new": _stats(new_offers),
        "stats_used": _stats(used_offers),
        "stats_all": _stats(all_offers),
        # Уникальные источники данных
        "sources": sorted({o["source"] for o in all_offers}),
    }
    # Экономия среди новых (макс - мин)
    if new_offers:
        prices = [o["price"] for o in new_offers]
        summary["savings_new"] = round(max(prices) - min(prices), 2)
    else:
        summary["savings_new"] = 0
    # Экономия б/у против нового
    if new_offers and used_offers:
        summary["savings_used"] = round(new_offers[0]["price"] - used_offers[0]["price"], 2)
    else:
        summary["savings_used"] = 0
    return summary


def list_product_titles() -> list[str]:
    with get_session() as s:
        return [p.title for p in s.query(Product).order_by(Product.title).all()]
