"""Конфигурация приложения PricePilot BY.

Все настройки читаются из переменных окружения (.env).
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Поддерживаемые города Беларуси
CITIES = [
    "Минск",
    "Гомель",
    "Витебск",
    "Брест",
    "Гродно",
    "Могилев",
]


@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    # Путь к файлу БД SQLite
    db_path: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "pricepilot.db"))
    # Через сколько секунд проверять подписки на снижение цены
    alert_interval: int = int(os.getenv("ALERT_INTERVAL", "60"))
    # Настройки FastAPI
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cities: list = field(default_factory=lambda: CITIES)

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
