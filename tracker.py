import logging

from db import get_session, init_db
from notifier import send_episode_notifications
from parser import parse_notifications
from repository import mark_notified, pending_episodes, save_new_episodes

log = logging.getLogger(__name__)


def check_once(url: str, user_data_dir: str) -> None:
    """Один цикл: спарсить -> сохранить новое -> разослать уведомления."""
    init_db()
    notifications = parse_notifications(url, user_data_dir)

    with get_session() as session:
        new_episodes = save_new_episodes(session, notifications)
        # Отправляем и свежесохранённые, и те, что остались
        # неотправленными после прошлого (неудачного) прогона
        to_notify = new_episodes + [
            e for e in pending_episodes(session) if e not in new_episodes
        ]
        if not to_notify:
            log.info("Новых серий нет")
            return
        send_episode_notifications(to_notify)
        mark_notified(session, to_notify)
