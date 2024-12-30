from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum
from urllib.parse import quote

from orjson import dumps, loads
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from structlog import get_logger

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
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
    ),
    expire_on_commit=False,
    class_=Session,
)


def _create_session() -> Session:
    return DEFAULT_SESSION_FACTORY()


# FastAPI Dependency
def get_session() -> Generator[Session]:
    session = _create_session()
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
    finally:
        session.close()


class PropagationType(Enum):
    REQUIRED = "REQUIRED"  # 기존 트랜잭션 사용, 없으면 새로 생성
    REQUIRES_NEW = "REQUIRES_NEW"  # 항상 새로운 트랜잭션 생성
    NOT_SUPPORTED = "NOT_SUPPORTED"  # 트랜잭션 없이 실행


@contextmanager
def transactional(propagation: PropagationType = PropagationType.REQUIRED):
    if propagation == PropagationType.NOT_SUPPORTED:
        db_session = _create_session()
        try:
            yield db_session
        finally:
            db_session.close()
        return

    db_session = _create_session() if propagation == PropagationType.REQUIRES_NEW else next(get_session())

    try:
        yield db_session
        db_session.commit()
    except Exception as e:
        log.error(f"Transaction error: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()
