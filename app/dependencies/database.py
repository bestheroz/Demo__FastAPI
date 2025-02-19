from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from typing import Any, cast
from urllib.parse import quote

from orjson import dumps, loads
from sqlalchemy import CursorResult, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from structlog import get_logger

from app.core.config import get_settings

log = get_logger()


def custom_json_serializer(obj: Any) -> bytes:
    if isinstance(obj, set):
        return dumps(sorted(list(obj)))
    return dumps(obj)


class ReadonlySession(Session):
    """읽기 전용 세션을 위한 커스텀 세션 클래스"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, *args, **kwargs) -> CursorResult[Any]:
        """쿼리 실행을 자동으로 병렬 처리"""
        future = db_manager._thread_pool.submit(super().execute, *args, **kwargs)
        return cast(CursorResult[Any], future.result())


class DatabaseSessionManager:
    def __init__(self) -> None:
        self.config = get_settings()
        self._default_engine: Engine | None = None
        self._readonly_engine: Engine | None = None
        self._default_session_factory: sessionmaker | None = None
        self._readonly_session_factory: sessionmaker | None = None
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.db_pool_size, thread_name_prefix="db_readonly_")

    def _create_engine(self, readonly: bool = False) -> Engine:
        pool_size = int(self.config.db_pool_size * (2 / 3 if readonly else 1 / 3))
        max_overflow = int(self.config.db_max_overflow * (2 / 3 if readonly else 1 / 3))

        connection_url = (
            f"mysql+pymysql://{self.config.db_username}:{quote(self.config.db_password)}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.config.db_name}"
        )

        engine_kwargs = {
            "json_serializer": custom_json_serializer,
            "json_deserializer": loads,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_recycle": self.config.db_pool_recycle,
            "pool_pre_ping": True,
        }

        if readonly:
            engine_kwargs["execution_options"] = {"readonly": True}

        return create_engine(connection_url, **engine_kwargs)

    def _create_session_factory(self, engine: Engine, readonly: bool = False) -> sessionmaker:
        return sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=ReadonlySession if readonly else Session,
            future=True,
        )

    def _get_session_factory(self, readonly: bool = False) -> sessionmaker:
        if readonly:
            if not self._readonly_session_factory:
                if not self._readonly_engine:
                    self._readonly_engine = self._create_engine(readonly=True)
                self._readonly_session_factory = self._create_session_factory(self._readonly_engine, readonly=True)
            return self._readonly_session_factory

        if not self._default_session_factory:
            if not self._default_engine:
                self._default_engine = self._create_engine()
            self._default_session_factory = self._create_session_factory(self._default_engine)
        return self._default_session_factory

    @staticmethod
    def _handle_session_error(session: Session, error: Exception, readonly: bool) -> None:
        error_type = "Read operation" if readonly else "Database"
        log.error(f"{error_type} error", error=str(error), exc_info=True)
        if not readonly:
            session.rollback()
        raise

    def get_session(self, readonly: bool = False) -> Iterator[Session]:
        session = self._get_session_factory(readonly=readonly)()
        try:
            yield session
            if not readonly:
                session.commit()
        except Exception as e:
            self._handle_session_error(session, e, readonly)
        finally:
            session.close()

    @contextmanager
    def transactional(self, readonly: bool = False) -> Iterator[Session]:
        session_generator = self.get_session(readonly=readonly)
        try:
            session = next(session_generator)
            yield session
        finally:
            with suppress(StopIteration):
                next(session_generator, None)


# 싱글톤 인스턴스 생성
db_manager = DatabaseSessionManager()

# FastAPI Dependency
get_session = db_manager.get_session


def get_readonly_session() -> Iterator[Session]:
    return db_manager.get_session(readonly=True)


transactional = db_manager.transactional
