from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.config import settings


def create_database_engine(database_url: str | None = None):
    url = database_url or settings.sqlalchemy_database_url
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(url, connect_args=connect_args, **engine_kwargs)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_database_status() -> dict[str, str]:
    return {"status": "configured", "mode": "sqlalchemy"}
