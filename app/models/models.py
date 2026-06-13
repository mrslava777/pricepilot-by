"""Модели базы данных (SQLAlchemy 2.0)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), index=True)
    category: Mapped[str] = mapped_column(String(64), default="Прочее", index=True)

    offers: Mapped[list["Offer"]] = relationship(back_populates="product")


class Offer(Base):
    """Конкретное предложение товара в магазине/городе."""

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    price: Mapped[float] = mapped_column(Float)
    # "new" или "used"
    condition: Mapped[str] = mapped_column(String(8), default="new", index=True)
    url: Mapped[str] = mapped_column(Text, default="")
    # Источник данных: "Демо-каталог", "Onliner", "Kufar (RSS)", "Магазин (XML)" и т.д.
    source: Mapped[str] = mapped_column(String(64), default="Демо-каталог")

    product: Mapped["Product"] = relationship(back_populates="offers")
    store: Mapped["Store"] = relationship()
    city: Mapped["City"] = relationship()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(128), default="")
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    city: Mapped["City"] = relationship()


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship()


class Alert(Base):
    """Подписка на снижение цены."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query: Mapped[str] = mapped_column(String(256))
    target_price: Mapped[float] = mapped_column(Float)
    condition: Mapped[str] = mapped_column(String(8), default="any")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    last_notified_price: Mapped[float | None] = mapped_column(Float, nullable=True)
