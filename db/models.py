from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Title(Base):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    title_name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)

    episodes: Mapped[list["Episode"]] = relationship(back_populates="title")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    episodes: Mapped[list["Episode"]] = relationship(back_populates="team")


class Episode(Base):
    __tablename__ = "episodes"
    # quality входит в уникальность тк одна серия одной команды может выйти в нескольких разрешениях (FullHD, 4K) - это разные релизы
    __table_args__ = (
        UniqueConstraint(
            "title_id", "team_id", "episode_number", "quality",
            name="uq_episode",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    episode_number: Mapped[int] = mapped_column(Integer)
    quality: Mapped[str] = mapped_column(String, default="")
    url: Mapped[str] = mapped_column(String, default="")
    # NULL — серия известна, но уведомление ещё не отправлено
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    title: Mapped[Title] = relationship(back_populates="episodes")
    team: Mapped[Team] = relationship(back_populates="episodes")
