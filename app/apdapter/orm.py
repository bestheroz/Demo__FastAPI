from abc import ABC
from collections import deque
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from orjson import dumps, loads
from pydantic import AwareDatetime
from sqlalchemy import DateTime, TypeDecorator, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker
from structlog import get_logger

from app.common.event import Event
from app.config.config import get_settings

settings = get_settings()

log = get_logger()


def custom_json_serializer(obj):
    if isinstance(obj, set):
        return dumps(sorted(list(obj)))  # set은 정렬해서 반환(테스트 코드 이슈)
    # 다른 타입에 대한 처리가 필요하면 여기에 추가
    return dumps(obj)


DEFAULT_SESSION_FACTORY = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        f"mysql+pymysql://{settings.db_username}:{quote(settings.db_password)}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        json_serializer=custom_json_serializer,
        json_deserializer=loads,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
    ),
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def session_scope():
    with DEFAULT_SESSION_FACTORY() as session:
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            log.error(f"Database error: {e}")
            session.rollback()
            raise
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            session.rollback()
            raise


# FastAPI Dependency
def get_session():
    with session_scope() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            log.error(f"Database error: {e}")
            session.rollback()
            raise
        finally:
            session.close()


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
        if not value or value == "0000-00-00 00:00:00":
            return None

        try:
            return value.astimezone(UTC)
        except (ValueError, AttributeError):
            return value.replace(tzinfo=UTC)


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
