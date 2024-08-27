from abc import ABC
from collections import deque
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from orjson import dumps, loads
from pydantic import AwareDatetime
from sqlalchemy import DateTime, ForeignKey, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.common.event import Event
from app.config.config import get_settings

settings = get_settings()


def custom_json_serializer(obj):
    if isinstance(obj, set):
        return dumps(sorted(list(obj)))  # set은 정렬해서 반환(테스트 코드 이슈)
    # 다른 타입에 대한 처리가 필요하면 여기에 추가
    return dumps(obj)


DEFAULT_SESSION_FACTORY = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_async_engine(
        f"mysql+aiomysql://{settings.db_username}:{quote(settings.db_password)}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        isolation_level="REPEATABLE READ",
        json_serializer=lambda obj: dumps(obj).decode(),
        json_deserializer=loads,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=True,
    ),
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def session_scope():
    _session = DEFAULT_SESSION_FACTORY()
    try:
        yield _session
        await _session.commit()
    except Exception:
        await _session.rollback()
        raise
    finally:
        await _session.close()


# FastAPI Dependency
async def get_session():
    session = DEFAULT_SESSION_FACTORY()
    try:
        yield session
    finally:
        await session.close()


class TZDateTime(TypeDecorator, ABC):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("tzinfo is required")
            value = value.astimezone(UTC)
            if isinstance(value, datetime):
                value = datetime(
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                    tzinfo=value.tzinfo,
                )
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=UTC)
        return value


mapped_intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
mapped_created_at = Annotated[
    AwareDatetime,
    mapped_column(
        "created_at",
        TZDateTime,
    ),
]
mapped_updated_at = Annotated[
    AwareDatetime,
    mapped_column(
        "updated_at",
        TZDateTime,
    ),
]
mapped_created_by_id = Annotated[
    int,
    mapped_column(ForeignKey("admin.id")),
]
mapped_updated_by_id = Annotated[
    int,
    mapped_column(ForeignKey("admin.id")),
]


def events_getter(self) -> deque[Event]:
    """Usage:
    events = property(events_getter)
    """
    if not hasattr(self, "__events"):
        self.__events = deque()

    return self.__events


class Base(DeclarativeBase):
    __allow_unmapped__ = True

    events = property(events_getter)
