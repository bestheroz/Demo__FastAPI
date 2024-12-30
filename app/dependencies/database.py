from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import quote

from orjson import dumps, loads
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from structlog import get_logger

from app.core.config import get_settings

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
        pool_size=int(settings.db_pool_size / 3),
        max_overflow=int(settings.db_max_overflow / 3),
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
    ),
    expire_on_commit=False,
    class_=Session,
)

READONLY_SESSION_FACTORY = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        f"mysql+pymysql://{settings.db_username}:{quote(settings.db_password)}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        json_serializer=custom_json_serializer,
        json_deserializer=loads,
        pool_size=int(settings.db_pool_size * 2 / 3),
        max_overflow=int(settings.db_max_overflow * 2 / 3),
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
        execution_options={"readonly": True},
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


def _create_readonly_session() -> Session:
    return READONLY_SESSION_FACTORY()


# FastAPI Dependency for read-only operations
def get_readonly_session() -> Generator[Session]:
    session = _create_readonly_session()
    try:
        yield session
    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        session.rollback()
        raise
    except Exception as e:
        log.error(f"Read operation error: {e}")
        raise
    finally:
        session.close()


@contextmanager
def transactional(readonly: bool = False):
    if readonly:
        session = next(get_readonly_session())
        try:
            yield session
        except SQLAlchemyError as e:
            log.error(f"Database error: {e}")
            # 굳이 rollback 할 변경사항이 없긴 하지만, 안정성을 위해 남겨둠
            session.rollback()
            raise
        except Exception as e:
            log.error(f"Transaction error: {e}")
            # 굳이 rollback 할 변경사항이 없긴 하지만, 안정성을 위해 남겨둠
            session.rollback()
            raise
        finally:
            session.close()
    else:
        session = next(get_session())
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            log.error(f"Database error: {e}")
            session.rollback()
            raise
        except Exception as e:
            log.error(f"Transaction error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
