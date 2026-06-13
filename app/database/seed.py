"""Заполнение БД демо-каталогом.

В MVP нет бесплатного публичного API цен по магазинам Беларуси,
поэтому каталог наполняется реалистичными демо-данными.
Чтобы подключить реальные цены — замените логику в services/search.py
и наполняйте таблицы offers данными ваших парсеров.
"""
from __future__ import annotations

import random

from app.config import CITIES
from app.database.db import get_session, init_db
from app.models.models import City, Offer, Product, Store

STORES = ["5 Element", "Электросила", "Onliner Market", "Ozon BY", "21vek", "Kufar"]

# title, category, базовая цена (новый), есть ли б/у
CATALOG = [
    ("iPhone 17", "Смартфоны", 3999, True),
    ("iPhone 17 Pro", "Смартфоны", 5499, True),
    ("Samsung Galaxy S25", "Смартфоны", 3299, True),
    ("Ноутбук Lenovo IdeaPad 3", "Ноутбуки", 1899, True),
    ("Ноутбук Lenovo ThinkPad X1", "Ноутбуки", 4599, True),
    ("Ноутбук ASUS VivoBook", "Ноутбуки", 1699, True),
    ("PlayStation 6", "Игровые консоли", 1999, True),
    ("PlayStation 5 Slim", "Игровые консоли", 1499, True),
    ("Xbox Series X", "Игровые консоли", 1399, True),
    ("Телевизор LG OLED 55", "Телевизоры", 3499, True),
    ("Холодильник LG", "Бытовая техника", 2199, True),
    ("Робот-пылесос Xiaomi", "Бытовая техника", 899, True),
    ("Наушники Sony WH-1000XM5", "Аудио", 1099, True),
    ("Apple Watch Series 10", "Гаджеты", 1299, True),
]


def seed_db(force: bool = False) -> None:
    init_db()
    with get_session() as s:
        if s.query(Product).count() > 0 and not force:
            return  # уже заполнено

        # Города
        cities = {}
        for name in CITIES:
            c = s.query(City).filter_by(name=name).first()
            if not c:
                c = City(name=name)
                s.add(c)
                s.flush()
            cities[name] = c

        # Магазины
        stores = {}
        for name in STORES:
            st = s.query(Store).filter_by(name=name).first()
            if not st:
                st = Store(name=name)
                s.add(st)
                s.flush()
            stores[name] = st

        random.seed(42)
        for title, category, base, has_used in CATALOG:
            p = Product(title=title, category=category)
            s.add(p)
            s.flush()

            # Новые предложения: 3-5 магазинов в нескольких городах
            n_offers = random.randint(3, 5)
            chosen_stores = random.sample(STORES[:-1], n_offers)  # без Kufar для новых
            for store_name in chosen_stores:
                city_name = random.choice(CITIES)
                price = round(base * random.uniform(0.97, 1.08), 2)
                s.add(
                    Offer(
                        product_id=p.id,
                        store_id=stores[store_name].id,
                        city_id=cities[city_name].id,
                        price=price,
                        condition="new",
                        url=f"https://example.by/{p.id}/{store_name.replace(' ', '-').lower()}",
                        source="Демо-каталог",
                    )
                )

            # Б/У предложения (Kufar) дешевле
            if has_used:
                for _ in range(random.randint(1, 3)):
                    city_name = random.choice(CITIES)
                    price = round(base * random.uniform(0.55, 0.80), 2)
                    s.add(
                        Offer(
                            product_id=p.id,
                            store_id=stores["Kufar"].id,
                            city_id=cities[city_name].id,
                            price=price,
                            condition="used",
                            url=f"https://kufar.by/item/{p.id}",
                            source="Демо-каталог (Kufar)",
                        )
                    )

        print("✅ Демо-каталог загружен:", s.query(Product).count(), "товаров,",
              s.query(Offer).count(), "предложений")


if __name__ == "__main__":
    seed_db(force=True)
