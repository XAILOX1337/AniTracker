import asyncio
import logging

from telegram import Bot

import config
from db.models import Episode

log = logging.getLogger(__name__)


def format_message(episode: Episode) -> str:
    parts = [f"Вышла {episode.episode_number} серия «{episode.title.title_name}»"]
    if episode.team.name:
        parts.append(f"в озвучке {episode.team.name}")
    if episode.quality:
        parts.append(f"({episode.quality})")
    if episode.url:
        parts.append(episode.url)
    return " ".join(parts)


def send_episode_notifications(episodes: list[Episode]) -> None:
    """Отправляет уведомления; без токена — только логирует."""
    messages = [format_message(e) for e in episodes]
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        for text in messages:
            log.warning("Telegram не настроен, уведомление не отправлено: %s", text)
        return

    async def _send() -> None:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        for text in messages:
            await bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=text)

    asyncio.run(_send())
    log.info("Отправлено уведомлений: %d", len(messages))
