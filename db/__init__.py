from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import config
from db.models import Base

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
