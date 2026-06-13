"""Агрегатор парсеров: собирает предложения и пишет их в БД.

По умолчанию ENABLED_PARSERS пуст — бот работает на демо-каталоге.
Чтобы подключить реальный источник, добавьте парсер в ENABLED_PARSERS,
например:

    from app.parsers.rss_parser import RssXmlParser
    from app.parsers.http_parser import HttpHtmlParser

    ENABLED_PARSERS = [
        RssXmlParser(name="Магазин (YML)", feed_url="https://shop.by/yml.xml"),
        HttpHtmlParser(
            name="Onliner",
            search_url_template="https://catalog.onliner.by/search?query={query}",
            item_selector=".product-item",
            title_selector=".product-title",
            price_selector=".product-price",
            link_selector="a",
            base_url="https://catalog.onliner.by",
        ),
    ]
"""
from __future__ import annotations

import asyncio
import logging

from app.database.db import get_session
from app.models.models import City, Offer, Product, Store
from app.parsers.base import BaseParser, ParsedOffer
from app.parsers.deal import DealParser
from app.parsers.kufar import KufarParser
from app.parsers.onliner import OnlinerParser

logger = logging.getLogger(__name__)

# Список активных парсеров реальных источников Беларуси.
# Onliner — новые товары и цены по магазинам (вся техника/электроника).
# Kufar   — объявления (Б/У и новые от частников).
# Deal.by — маркетплейс EVO: тысячи магазинов, товары + ПРОДУКТЫ питания.
# Пустой список => бот работает только на демо-каталоге.
ENABLED_PARSERS: list[BaseParser] = [
    OnlinerParser(max_products=5, expand_top=2, max_positions=6),
    KufarParser(size=12, max_items=8),
    DealParser(max_items=8),
]


def offer_to_dict(off: ParsedOffer) -> dict:
    """Приводит ParsedOffer к виду, который ожидает карточка поиска."""
    return {
        "product": off.title,
        "store": off.store,
        "city": off.city,
        "price": off.price,
        "condition": off.condition,
        "url": off.url,
        "source": off.source,
    }


async def fetch_live_dicts(query: str, city: str | None = None) -> list[dict]:
    """Опрашивает реальные источники и возвращает предложения как словари."""
    offers = await fetch_all(query, city)
    return [offer_to_dict(o) for o in offers]


async def fetch_all(query: str, city: str | None = None) -> list[ParsedOffer]:
    """Параллельно опрашивает все включённые парсеры (с защитой от ошибок)."""
    if not ENABLED_PARSERS:
        return []
    tasks = [p.fetch_offers(query, city) for p in ENABLED_PARSERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    offers: list[ParsedOffer] = []
    for res in results:
        if isinstance(res, Exception):
            logger.warning("Парсер упал: %s", res)
            continue
        offers.extend(res)
    return offers


def ingest_offers(offers: list[ParsedOffer]) -> int:
    """Сохраняет распарсенные предложения в БД (создаёт товары/магазины/города)."""
    saved = 0
    with get_session() as s:
        for off in offers:
            product = (
                s.query(Product).filter(Product.title.ilike(off.title)).first()
            )
            if not product:
                product = Product(title=off.title, category=off.category)
                s.add(product)
                s.flush()

            store = s.query(Store).filter_by(name=off.store).first()
            if not store:
                store = Store(name=off.store)
                s.add(store)
                s.flush()

            city = s.query(City).filter_by(name=off.city).first()
            if not city:
                city = City(name=off.city)
                s.add(city)
                s.flush()

            s.add(
                Offer(
                    product_id=product.id,
                    store_id=store.id,
                    city_id=city.id,
                    price=off.price,
                    condition=off.condition,
                    url=off.url,
                    source=off.source,
                )
            )
            saved += 1
    return saved


async def refresh(query: str, city: str | None = None) -> int:
    """Опрашивает источники и складывает свежие предложения в БД."""
    offers = await fetch_all(query, city)
    if not offers:
        return 0
    return ingest_offers(offers)
