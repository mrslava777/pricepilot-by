"""Сбор всех роутеров хендлеров."""
from aiogram import Router

from app.handlers import alerts, city, favorites, help, search, start


def get_main_router() -> Router:
    router = Router()
    # Порядок важен: команды/меню/диалоги раньше, свободный текст-поиск — последним
    router.include_router(start.router)
    router.include_router(city.router)
    router.include_router(favorites.router)
    router.include_router(alerts.router)
    router.include_router(help.router)
    router.include_router(search.router)  # содержит catch-all поиск
    return router
