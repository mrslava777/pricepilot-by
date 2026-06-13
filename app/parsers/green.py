"""Парсер продуктового магазина GREEN (green-dostavka.by).

Это даёт боту реальные цены на ПРОДУКТЫ ПИТАНИЯ (молоко, хлеб, овощи,
кофе, бакалея и т.д.) — так же, как Onliner даёт цены на технику.

Открытый JSON-API онлайн-магазина GREEN (Минск, storeId=2):
  https://green-dostavka.by/api/v1/products/search/?search=...&storeId=2

Ответ: {skip, limit, count, items:[{title, slug, storeProduct:{price,
priceWithSale, sale, balance, isActive}}]}. Цены — в копейках (/100).
Поиск отсортирован по релевантности.
"""
from __future__ import annotations

import logging
import urllib.parse

import aiohttp

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)

# storeId=2 — минский магазин GREEN с доставкой по РБ.
SEARCH_URL = (
    "https://green-dostavka.by/api/v1/products/search/"
    "?search={query}&storeId={store_id}&limit={limit}"
)
PRODUCT_URL = "https://green-dostavka.by/product/{slug}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru,be;q=0.9",
    "Referer": "https://green-dostavka.by/",
}


class GreenParser(BaseParser):
    """Поиск продуктов питания в онлайн-магазине GREEN.

    :param max_items: сколько предложений вернуть
    :param store_id: идентификатор магазина GREEN (2 — Минск)
    """

    name = "GREEN"

    def __init__(self, max_items: int = 8, store_id: int = 2, timeout: int = 12) -> None:
        self.max_items = max_items
        self.store_id = store_id
        self.timeout = timeout

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        if len(query.strip()) < 2:
            return []
        url = SEARCH_URL.format(
            query=urllib.parse.quote(query),
            store_id=self.store_id,
            limit=max(self.max_items * 3, 15),
        )
        data = await self._get_json(url)
        if not data:
            return []

        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            return []

        # Поиск GREEN всегда что-то возвращает (даже на «iPhone» выдаёт пиццу),
        # поэтому оставляем только товары, где значимое слово запроса есть в названии.
        tokens = [t for t in query.lower().split() if len(t) > 2 and not t.isdigit()]

        offers: list[ParsedOffer] = []
        for it in items:
            title_low = (it.get("title") or "").lower()
            if tokens and not any(t in title_low for t in tokens):
                continue
            sp = it.get("storeProduct") or {}
            if not sp.get("isActive", True):
                continue
            # Текущая цена с учётом скидки (в копейках)
            raw = sp.get("priceWithSale") or sp.get("price")
            price = self.clean_price(raw)
            if price is None or price <= 0:
                continue
            price = round(price / 100, 2)

            title = (it.get("title") or "").strip()
            if not title:
                continue
            slug = it.get("slug")
            url_p = PRODUCT_URL.format(slug=slug) if slug else "https://green-dostavka.by/"

            offers.append(
                ParsedOffer(
                    title=title,
                    price=price,
                    store="GREEN",
                    city=city or "Минск",
                    url=url_p,
                    source="GREEN",
                    condition="new",
                    category="Продукты",
                )
            )
            if len(offers) >= self.max_items:
                break
        return offers

    async def _get_json(self, url: str):
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as sess:
                async with sess.get(url) as resp:
                    if resp.status != 200:
                        logger.warning("GREEN: HTTP %s", resp.status)
                        return None
                    return await resp.json(content_type=None)
        except Exception as e:  # noqa: BLE001
            logger.warning("GREEN: ошибка запроса: %s", e)
            return None
