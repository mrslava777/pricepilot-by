"""Базовый интерфейс парсера и нормализованная структура предложения."""
from __future__ import annotations

import abc
from dataclasses import dataclass, asdict


@dataclass
class ParsedOffer:
    """Нормализованное предложение от любого парсера."""

    title: str          # название товара
    price: float        # цена в BYN
    store: str          # магазин / продавец
    city: str           # город
    url: str            # ссылка на товар
    source: str         # источник данных (имя парсера)
    condition: str = "new"  # "new" | "used"
    category: str = "Прочее"

    def as_dict(self) -> dict:
        return asdict(self)


class BaseParser(abc.ABC):
    """Базовый класс парсера источника.

    Наследники реализуют `fetch_offers(query, city)` и возвращают список ParsedOffer.
    """

    name: str = "base"

    @abc.abstractmethod
    async def fetch_offers(self, query: str, city: str | None = None) -> list[ParsedOffer]:
        ...

    @staticmethod
    def clean_price(raw: str) -> float | None:
        """Извлекает число из строки вида '3 999 BYN', '3999,00 р.'."""
        if raw is None:
            return None
        digits = (
            str(raw)
            .replace("\xa0", "")
            .replace(" ", "")
            .replace("BYN", "")
            .replace("р.", "")
            .replace("руб", "")
            .replace(",", ".")
            .strip()
        )
        # оставляем только цифры и точку
        cleaned = "".join(ch for ch in digits if ch.isdigit() or ch == ".")
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
