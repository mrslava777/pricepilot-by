"""Формирование красивых карточек-сообщений для Telegram."""
from __future__ import annotations

MEDALS = ["🥇", "🥈", "🥉"]

PRODUCT_EMOJI = {
    "Смартфоны": "📱",
    "Ноутбуки": "💻",
    "Игровые консоли": "🎮",
    "Телевизоры": "📺",
    "Бытовая техника": "🧊",
    "Аудио": "🎧",
    "Гаджеты": "⌚",
}


def _emoji_for(title: str) -> str:
    t = title.lower()
    if "iphone" in t or "samsung" in t or "galaxy" in t:
        return "📱"
    if "ноутбук" in t or "laptop" in t:
        return "💻"
    if "playstation" in t or "xbox" in t:
        return "🎮"
    if "телевизор" in t or "tv" in t or "oled" in t:
        return "📺"
    if "холодильник" in t or "пылесос" in t:
        return "🧊"
    if "наушники" in t:
        return "🎧"
    if "watch" in t or "часы" in t:
        return "⌚"
    return "🛒"


def format_offers_block(offers: list[dict], max_items: int = 5) -> str:
    """Список предложений с медалями для топ-3 (магазин, город, цена, источник, ссылка)."""
    lines = []
    for i, o in enumerate(offers[:max_items]):
        prefix = MEDALS[i] if i < 3 else "•"
        lines.append(
            f"{prefix} {o['store']} ({o['city']}) — {o['price']:.0f} BYN\n"
            f"   🗂 {o['source']}  •  🔗 {o['url']}"
        )
    return "\n".join(lines)


def _format_stats(stats: dict) -> str:
    """Строка со сводной статистикой: мин / средняя / количество."""
    if not stats or not stats.get("count"):
        return ""
    return (
        f"📊 мин: *{stats['min']:.0f}* BYN  •  "
        f"средняя: *{stats['avg']:.0f}* BYN  •  "
        f"предложений: *{stats['count']}*"
    )


def format_search_card(summary: dict) -> str:
    """Главная карточка результата поиска."""
    query = summary["query"]
    city = summary.get("city")
    new_offers = summary["new"]
    used_offers = summary["used"]

    emoji = _emoji_for(query)
    head = f"{emoji} *{query}*"
    if city:
        head += f"\n📍 {city}"

    if not new_offers and not used_offers:
        return (
            f"{head}\n\n😕 Ничего не найдено.\n"
            "Попробуйте другое название или уберите фильтр по городу."
        )

    parts = [head, ""]

    # Общая статистика по всем предложениям
    stats_all = _format_stats(summary.get("stats_all", {}))
    if stats_all:
        parts.append(stats_all)
        parts.append("")

    if new_offers:
        parts.append("🆕 *Новые товары*")
        stats_new = _format_stats(summary.get("stats_new", {}))
        if stats_new:
            parts.append(stats_new)
        parts.append(format_offers_block(new_offers))
        if summary.get("savings_new"):
            parts.append(f"\n💰 Экономия (выбрав дешевле): *{summary['savings_new']:.0f} BYN*")
        parts.append("")

    if used_offers:
        parts.append("♻️ *Б/У товары*")
        stats_used = _format_stats(summary.get("stats_used", {}))
        if stats_used:
            parts.append(stats_used)
        parts.append(format_offers_block(used_offers))
        if summary.get("savings_used") and summary.get("savings_used") > 0:
            parts.append(f"\n💸 Б/У дешевле нового на: *{summary['savings_used']:.0f} BYN*")
        parts.append("")

    # Источники данных
    sources = summary.get("sources") or []
    if sources:
        parts.append(f"📡 Источники: {', '.join(sources)}")

    return "\n".join(parts).strip()


def format_favorites(favorites: list[dict]) -> str:
    if not favorites:
        return "❤️ *Избранное пусто*\n\nНайдите товар и нажмите «В избранное»."
    lines = ["❤️ *Избранное*", ""]
    for f in favorites:
        lines.append(f"{_emoji_for(f['title'])} {f['title']}")
    return "\n".join(lines)


def format_alerts(alerts: list[dict]) -> str:
    if not alerts:
        return (
            "🔔 *Подписок нет*\n\n"
            "Создайте подписку — и бот напишет, когда цена опустится ниже вашей."
        )
    lines = ["🔔 *Ваши подписки на цену*", ""]
    for a in alerts:
        lines.append(f"• {a['query']} → ≤ {a['target_price']:.0f} BYN")
    return "\n".join(lines)
