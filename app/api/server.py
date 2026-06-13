"""FastAPI-сервер PricePilot BY.

Лёгкий REST-слой поверх тех же сервисов, что использует бот.
Запуск: uvicorn app.api.server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, Query

from app.config import CITIES
from app.database.db import init_db
from app.database.seed import seed_db
from app.services.search import list_product_titles, search_summary

app = FastAPI(
    title="PricePilot BY API",
    description="API поиска самых дешёвых товаров в Беларуси",
    version="1.0.0",
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    seed_db()


@app.get("/")
def root() -> dict:
    return {"service": "PricePilot BY", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/cities")
def cities() -> dict:
    return {"cities": CITIES}


@app.get("/products")
def products() -> dict:
    return {"products": list_product_titles()}


@app.get("/search")
def search(
    q: str = Query(..., description="Название товара"),
    city: str | None = Query(None, description="Город Беларуси"),
) -> dict:
    """Поиск товара: мин/средняя цена, количество предложений, источники."""
    summary = search_summary(q, city=city)
    return {
        "query": q,
        "city": city,
        "stats": summary["stats_all"],
        "sources": summary["sources"],
        "new": summary["new"],
        "used": summary["used"],
        "savings_new": summary["savings_new"],
        "savings_used": summary["savings_used"],
    }
