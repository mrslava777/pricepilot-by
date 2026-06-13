"""Парсер маркетплейса Deal.by (платформа EVO/Prom).

Deal.by — крупная белорусская торговая площадка с тысячами магазинов:
здесь есть и техника, и товары для дома, и ПРОДУКТЫ ПИТАНИЯ, и всё прочее.
Поиск отдаёт HTML с аккуратной разметкой data-qaid, которую мы и разбираем.

  Поиск: https://deal.by/search?search_term=...
"""
from __future__ import annotations

import logging
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)

SEARCH_URL = "https://deal.by/search?search_term={query}"

# Слова-маркеры услуг/работ — отсеиваем, чтобы не путать с товарами.
SERVICE_WORDS = (
    "замена экрана", "замена дисплея", "установка", "ремонт", "услуг",
    "диагностика", "настройка", "прошивка", "заправка", "пошив",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru,be;q=0.9",
}


class DealParser(BaseParser):
    """Поиск товаров и продуктов на Deal.by.

    :param max_items: сколько предложений вернуть
    """

    name = "Deal.by"

    def __init__(self, max_items: int = 8, timeout: int = 12) -> None:
        self.max_items = max_items
        self.timeout = timeout

    async def _get_html(self, url: str) -> str | None:
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as sess:
                async with sess.get(url) as resp:
                    if resp.status != 200:
                        logger.warning("Deal.by: HTTP %s", resp.status)
                        return None
                    return await resp.text()
        except Exception as e:  # noqa: BLE001
            logger.warning("Deal.by: ошибка запроса: %s", e)
            return None

    @staticmethod
    def _q(el):
        return el.get_text(strip=True) if el else ""

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        url = SEARCH_URL.format(query=urllib.parse.quote(query))
        html = await self._get_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        tokens = [t for t in query.lower().split() if len(t) > 2]

        offers: list[ParsedOffer] = []
        for block in soup.select('[data-qaid="product_block"]'):
            price_el = block.select_one('[data-qaid="product_price"]')
            name_el = block.select_one('[data-qaid="product_name"]')
            if not price_el or not name_el:
                continue

            price = self.clean_price(price_el.get("data-qaprice"))
            if price is None or price <= 0:
                continue

            title = self._q(name_el)
            low = title.lower()
            # Релевантность: хотя бы один значимый токен запроса в названии
            if tokens and not any(t in low for t in tokens):
                continue
            # Отсекаем услуги/работы (замена экрана, ремонт, установка…)
            if any(w in low for w in SERVICE_WORDS):
                continue

            link_el = block.select_one('[data-qaid="product_link"]')
            href = link_el.get("href") if link_el else ""
            if href and href.startswith("/"):
                href = "https://deal.by" + href

            store = self._q(block.select_one('[data-qaid="company_name"]')) or "Deal.by"
            store = store.strip('"').strip()
            # Сервисные центры/запчасти продают ремонт и детали, а не сам товар —
            # их цены вводят в заблуждение (напр. «iPhone 15» за 180 BYN). Пропускаем.
            store_low = store.lower()
            if "сервис" in store_low or "запчаст" in store_low:
                continue
            region = self._q(block.select_one('[data-qaid="region_title"]'))
            region = region.replace("г.", "").strip() if region else (city or "Беларусь")

            offers.append(
                ParsedOffer(
                    title=title,
                    price=price,
                    store=store,
                    city=region,
                    url=href or url,
                    source="Deal.by",
                    condition="new",
                    category="Маркетплейс",
                )
            )
            if len(offers) >= self.max_items:
                break
        return offers
