"""Веб-парсер HTML-страниц (aiohttp + BeautifulSoup).

Используется как fallback, если у источника нет открытого API/фида.
Это РАБОЧАЯ ЗАГОТОВКА: задайте `search_url_template` и CSS-селекторы
под конкретный сайт-источник. Парсер уважает таймауты и ошибки сети.
"""
from __future__ import annotations

import logging

import aiohttp
from bs4 import BeautifulSoup

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru,be;q=0.9",
}


class HttpHtmlParser(BaseParser):
    """Универсальный HTML-парсер каталога магазина.

    :param name: имя источника (попадёт в карточку как «источник»)
    :param search_url_template: URL с плейсхолдером {query}, напр.
        "https://shop.by/search?q={query}"
    :param item_selector: CSS-селектор карточки товара
    :param title_selector / price_selector / link_selector: селекторы полей
    """

    def __init__(
        self,
        name: str,
        search_url_template: str,
        item_selector: str,
        title_selector: str,
        price_selector: str,
        link_selector: str | None = None,
        base_url: str = "",
        default_city: str = "Минск",
        timeout: int = 10,
    ) -> None:
        self.name = name
        self.search_url_template = search_url_template
        self.item_selector = item_selector
        self.title_selector = title_selector
        self.price_selector = price_selector
        self.link_selector = link_selector
        self.base_url = base_url
        self.default_city = default_city
        self.timeout = timeout

    async def _get_html(self, url: str) -> str | None:
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS, timeout=timeout) as sess:
                async with sess.get(url) as resp:
                    if resp.status != 200:
                        logger.warning("%s: HTTP %s для %s", self.name, resp.status, url)
                        return None
                    return await resp.text()
        except Exception as e:  # noqa: BLE001
            logger.warning("%s: ошибка запроса %s: %s", self.name, url, e)
            return None

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        url = self.search_url_template.format(query=query)
        html = await self._get_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        offers: list[ParsedOffer] = []
        for card in soup.select(self.item_selector):
            title_el = card.select_one(self.title_selector)
            price_el = card.select_one(self.price_selector)
            if not title_el or not price_el:
                continue
            price = self.clean_price(price_el.get_text())
            if price is None:
                continue

            link = url
            if self.link_selector:
                a = card.select_one(self.link_selector)
                if a and a.get("href"):
                    href = a["href"]
                    link = href if href.startswith("http") else f"{self.base_url}{href}"

            offers.append(
                ParsedOffer(
                    title=title_el.get_text(strip=True),
                    price=price,
                    store=self.name,
                    city=city or self.default_city,
                    url=link,
                    source=self.name,
                    condition="new",
                )
            )
        return offers
