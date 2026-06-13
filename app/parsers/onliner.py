"""Парсер каталога Onliner.by — крупнейшего агрегатора цен Беларуси.

Onliner отдаёт открытый JSON-API каталога (используется их же сайтом):
  * Поиск товаров:   https://catalog.onliner.by/sdapi/catalog.api/search/products?query=...
  * Цены по магазинам: https://shop.api.onliner.by/products/{key}/positions

Источник покрывает практически ВСЮ технику и электронику РБ:
смартфоны, ноутбуки, ТВ, бытовую технику, аудио, гаджеты и т.д.
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)

SEARCH_URL = "https://catalog.onliner.by/sdapi/catalog.api/search/products"
POSITIONS_URL = "https://shop.api.onliner.by/products/{key}/positions"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "ru,be;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


class OnlinerParser(BaseParser):
    """Поиск новых товаров и цен по магазинам через каталог Onliner.

    :param max_products: сколько товаров из поиска обрабатывать
    :param expand_top: для скольких верхних товаров тянуть цены по магазинам
    :param max_positions: максимум предложений-магазинов на товар
    """

    name = "Onliner"

    def __init__(
        self,
        max_products: int = 5,
        expand_top: int = 2,
        max_positions: int = 6,
        timeout: int = 12,
    ) -> None:
        self.max_products = max_products
        self.expand_top = expand_top
        self.max_positions = max_positions
        self.timeout = timeout

    async def _get_json(self, session: aiohttp.ClientSession, url: str, params=None):
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning("Onliner: HTTP %s для %s", resp.status, url)
                    return None
                return await resp.json(content_type=None)
        except Exception as e:  # noqa: BLE001
            logger.warning("Onliner: ошибка запроса %s: %s", url, e)
            return None

    @staticmethod
    def _amount(price_node: dict | None) -> float | None:
        if not price_node:
            return None
        try:
            return round(float(price_node["amount"]), 2)
        except (KeyError, TypeError, ValueError):
            return None

    async def _positions_offers(
        self,
        session: aiohttp.ClientSession,
        product: dict,
        fallback_city: str,
    ) -> list[ParsedOffer]:
        """Тянет цены по магазинам для одного товара."""
        key = product.get("key")
        if not key:
            return []
        data = await self._get_json(session, POSITIONS_URL.format(key=key))
        if not data:
            return []

        shops_raw = data.get("shops") or {}
        shops = {}
        if isinstance(shops_raw, dict):
            for sh in shops_raw.values():
                shops[sh.get("id")] = sh
        elif isinstance(shops_raw, list):
            for sh in shops_raw:
                shops[sh.get("id")] = sh

        positions = (data.get("positions") or {}).get("primary") or []
        product_url = product.get("html_url", "")
        prices_url = f"{product_url}/prices" if product_url else ""
        title = product.get("full_name") or product.get("name") or key

        offers: list[ParsedOffer] = []
        for pos in positions:
            price = self._amount(pos.get("position_price"))
            if price is None:
                continue
            shop = shops.get(pos.get("shop_id")) or {}
            store = shop.get("title") or "Магазин Onliner"
            city = fallback_city
            addrs = shop.get("addresses") or []
            if addrs:
                town = (addrs[0] or {}).get("town") or {}
                city = town.get("title") or fallback_city
            offers.append(
                ParsedOffer(
                    title=title,
                    price=price,
                    store=store,
                    city=city,
                    url=prices_url or product_url,
                    source="Onliner",
                    condition="new",
                    category=self._category(product),
                )
            )
        # Самые дешёвые предложения вперёд
        offers.sort(key=lambda o: o.price)
        return offers[: self.max_positions]

    @staticmethod
    def _category(product: dict) -> str:
        schema = product.get("schema") or {}
        return schema.get("name") or "Техника"

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        fallback_city = city or "Минск"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            search = await self._get_json(
                session, SEARCH_URL, params={"query": query}
            )
            if not search:
                return []
            products = (search.get("products") or [])[: self.max_products]
            if not products:
                return []

            offers: list[ParsedOffer] = []

            # 1) Детализация по магазинам для самых релевантных товаров
            expand = products[: self.expand_top]
            tasks = [
                self._positions_offers(session, p, fallback_city) for p in expand
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            expanded_keys = set()
            for p, res in zip(expand, results):
                if isinstance(res, Exception):
                    logger.warning("Onliner positions упал: %s", res)
                    continue
                if res:
                    expanded_keys.add(p.get("key"))
                    offers.extend(res)

            # 2) Для остальных товаров — карточка с минимальной ценой каталога
            for p in products:
                if p.get("key") in expanded_keys:
                    continue
                price = self._amount((p.get("prices") or {}).get("price_min"))
                if price is None:
                    continue
                count = ((p.get("prices") or {}).get("offers") or {}).get("count")
                store = f"Onliner ({count} предл.)" if count else "Onliner"
                offers.append(
                    ParsedOffer(
                        title=p.get("full_name") or p.get("name") or query,
                        price=price,
                        store=store,
                        city=fallback_city,
                        url=p.get("html_url", ""),
                        source="Onliner",
                        condition="new",
                        category=self._category(p),
                    )
                )
            return offers
