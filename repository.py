import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Episode, Team, Title
from parser import Notification

log = logging.getLogger(__name__)


def _get_or_create(session: Session, model, **kwargs):
    instance = session.scalar(select(model).filter_by(**kwargs))
    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
    return instance


def _get_or_create_title(session: Session, n: Notification) -> Title:
   
    title = None
    if n.title_id is not None:
        title = session.scalar(select(Title).where(Title.site_id == n.title_id))
    if title is None:
        title = session.scalar(select(Title).where(Title.title_name == n.title_name))
    if title is None:
        
        title = Title(site_id=n.title_id, title_name=n.title_name, url=n.url)
        session.add(title)
        session.flush()
        return title
   
    if n.title_name and title.title_name != n.title_name:
        title.title_name = n.title_name
    if n.url and title.url != n.url:
        title.url = n.url
    if n.title_id is not None and title.site_id is None:
        title.site_id = n.title_id
    return title


def save_new_episodes(session: Session, notifications: list[Notification]) -> list[Episode]:
    """Сохраняет уведомления, которых ещё нет в БД.

    Возвращает Episode-записи с notified_at IS NULL — их надо разослать.
    """
    new_episodes: list[Episode] = []
    for n in notifications:
        if n.episode_number is None:
            log.warning("Не удалось извлечь номер серии, пропуск: %r", n.raw_text)
            continue
        title = _get_or_create_title(session, n)
        team = _get_or_create(session, Team, name=n.team_name)
        exists = session.scalar(
            select(Episode).filter_by(
                title_id=title.id,
                team_id=team.id,
                episode_number=n.episode_number,
                quality=n.quality,
            )
        )
        if exists is None:
            episode = Episode(
                title_id=title.id,
                team_id=team.id,
                episode_number=n.episode_number,
                quality=n.quality,
                url=n.url,
            )
            session.add(episode)
            new_episodes.append(episode)
    session.commit()
    log.info("Новых серий: %d из %d уведомлений", len(new_episodes), len(notifications))
    return new_episodes


def pending_episodes(session: Session) -> list[Episode]:
    """Все серии, по которым ещё не отправляли уведомление."""
    return list(
        session.scalars(select(Episode).where(Episode.notified_at.is_(None)))
    )


def mark_notified(session: Session, episodes: list[Episode]) -> None:
    now = datetime.now(timezone.utc)
    for episode in episodes:
        episode.notified_at = now
    session.commit()
