"""Парсер RSS / XML / Atom фидов магазинов (aiohttp + xml.etree).

Многие магазины и маркетплейсы публикуют товарные фиды (YML/RSS/XML)
для прайс-агрегаторов — это бесплатный и стабильный источник.
Заготовка разбирает типовой YML/RSS со структурой <offer>/<item>.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import aiohttp

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)


class RssXmlParser(BaseParser):
    """Парсер товарного XML/RSS-фида.

    :param name: имя источника
    :param feed_url: URL фида (YML/RSS/XML)
    :param item_tag: тег элемента товара ('offer' для YML, 'item' для RSS)
    """

    def __init__(
        self,
        name: str,
        feed_url: str,
        item_tag: str = "offer",
        default_city: str = "Минск",
        timeout: int = 10,
    ) -> None:
        self.name = name
        self.feed_url = feed_url
        self.item_tag = item_tag
        self.default_city = default_city
        self.timeout = timeout

    async def _get_xml(self) -> str | None:
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.get(self.feed_url) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.text()
        except Exception as e:  # noqa: BLE001
            logger.warning("%s: ошибка фида %s: %s", self.name, self.feed_url, e)
            return None

    @staticmethod
    def _text(el, *tags) -> str:
        for tag in tags:
            found = el.find(tag)
            if found is not None and found.text:
                return found.text.strip()
        return ""

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        raw = await self._get_xml()
        if not raw:
            return []
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            logger.warning("%s: не удалось разобрать XML: %s", self.name, e)
            return []

        q = query.lower()
        offers: list[ParsedOffer] = []
        for item in root.iter(self.item_tag):
            title = self._text(item, "name", "title", "model")
            if not title or q not in title.lower():
                continue
            price = self.clean_price(self._text(item, "price"))
            if price is None:
                continue
            url = self._text(item, "url", "link")
            offers.append(
                ParsedOffer(
                    title=title,
                    price=price,
                    store=self.name,
                    city=city or self.default_city,
                    url=url or self.feed_url,
                    source=self.name,
                    condition="new",
                )
            )
        return offers
