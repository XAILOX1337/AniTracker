import asyncio
import logging

from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest

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


def _build_bot() -> Bot:
    if config.TELEGRAM_PROXY:
        # Например, socks5://127.0.0.1:1080 — если api.telegram.org
        # недоступен напрямую из сети
        return Bot(
            token=config.TELEGRAM_BOT_TOKEN,
            request=HTTPXRequest(proxy=config.TELEGRAM_PROXY),
        )
    return Bot(token=config.TELEGRAM_BOT_TOKEN)


def send_episode_notifications(episodes: list[Episode]) -> list[Episode]:
    """Отправляет уведомления поштучно.

    Возвращает эпизоды, доставленные успешно (только их можно помечать
    notified_at); без токена или при сбоях сети — пустой список.
    """
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        for episode in episodes:
            log.warning("Telegram не настроен: %s", format_message(episode))
        return []

    async def _send() -> list[Episode]:
        bot = _build_bot()
        sent: list[Episode] = []
        for episode in episodes:
            try:
                await bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=format_message(episode),
                )
                sent.append(episode)
            except TelegramError as exc:
                # Сбой сети/API не должен ронять весь прогон:
                # эпизод остаётся в очереди (notified_at IS NULL) и будет
                # отправлен повторно на следующей проверке
                log.warning("Уведомление не доставлено (%s): %s",
                            exc, format_message(episode))
        return sent

    return asyncio.run(_send())
