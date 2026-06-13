"""Парсер объявлений Kufar.by — крупнейшей доски объявлений Беларуси.

Kufar отдаёт открытый JSON-API поиска (тот же, что использует их сайт):
  https://api.kufar.by/search-api/v2/search/rendered-paginated?query=...

Источник покрывает Б/У и новые товары от частников и магазинов:
техника, электроника, бытовая техника и всё остальное.
"""
from __future__ import annotations

import logging

import aiohttp

from app.parsers.base import BaseParser, ParsedOffer

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.kufar.by/search-api/v2/search/rendered-paginated"

# Слова-маркеры аксессуаров/услуг/«куплю» — такие объявления отсеиваем,
# чтобы в выдаче по товару не было чехлов, стёкол и ремонта.
NOISE_WORDS = (
    "чехол", "стекло", "защит", "плёнк", "пленк", "ремонт", "услуг",
    "куплю", "обмен на", "подвесн", "полка", "кабель", "зарядк",
    "наклейк", "запчаст", "брелок", "держатель", "подставк", "сумк",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "ru,be;q=0.9",
}


class KufarParser(BaseParser):
    """Поиск объявлений (Б/У и новые) на Kufar.

    :param size: сколько объявлений запрашивать
    :param max_items: максимум предложений в выдачу
    """

    name = "Kufar"

    def __init__(self, size: int = 12, max_items: int = 8, timeout: int = 12) -> None:
        self.size = size
        self.max_items = max_items
        self.timeout = timeout

    @staticmethod
    def _param(ad: dict, *names: str) -> str | None:
        """Достаёт значение параметра объявления по ключу `p`."""
        for p in ad.get("ad_parameters", []) or []:
            if p.get("p") in names:
                vl = p.get("vl")
                if isinstance(vl, list):
                    vl = ", ".join(str(x) for x in vl)
                return str(vl) if vl else None
        return None

    @staticmethod
    def _price(ad: dict) -> float | None:
        raw = ad.get("price_byn")
        if raw in (None, ""):
            return None
        try:
            # price_byn приходит в копейках
            return round(int(raw) / 100, 2)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _condition(ad: dict) -> str:
        cond = KufarParser._param(ad, "condition", "state", "cnd") or ""
        c = cond.lower()
        if "нов" in c:
            return "new"
        return "used"

    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        params = {
            "query": query,
            "size": str(self.size),
            "lang": "ru",
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
                async with session.get(SEARCH_URL, params=params) as resp:
                    if resp.status != 200:
                        logger.warning("Kufar: HTTP %s", resp.status)
                        return []
                    data = await resp.json(content_type=None)
        except Exception as e:  # noqa: BLE001
            logger.warning("Kufar: ошибка запроса: %s", e)
            return []

        ads = data.get("ads") or []
        offers: list[ParsedOffer] = []
        for ad in ads:
            price = self._price(ad)
            if price is None or price <= 0:
                continue
            title = ad.get("subject") or query
            low = title.lower()
            if any(w in low for w in NOISE_WORDS):
                continue
            town = self._param(ad, "area") or self._param(ad, "region") or "Беларусь"
            offers.append(
                ParsedOffer(
                    title=title,
                    price=price,
                    store="Kufar (частник)",
                    city=town,
                    url=ad.get("ad_link", "https://www.kufar.by"),
                    source="Kufar",
                    condition=self._condition(ad),
                    category="Объявления",
                )
            )
        # Отсекаем экстремальные выбросы по цене (аксессуары/диски/мелочёвка,
        # которые случайно попали в выдачу по дорогому товару).
        offers = self._drop_outliers(offers)

        # Сортируем по возрастанию цены и отдаём самые дешёвые
        offers.sort(key=lambda o: o.price)
        return offers[: self.max_items]

    @staticmethod
    def _drop_outliers(offers: list[ParsedOffer]) -> list[ParsedOffer]:
        """Удаляет предложения дешевле 10% медианной цены (явные аксессуары)."""
        if len(offers) < 4:
            return offers
        prices = sorted(o.price for o in offers)
        median = prices[len(prices) // 2]
        threshold = median * 0.1
        return [o for o in offers if o.price >= threshold]
