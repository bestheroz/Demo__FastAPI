from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generic

from app.apdapter.event import EventHandler
from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository, T


class DuplicateUnitOfWork(Exception):
    pass


class AbstractUnitOfWork(ABC):
    def __init__(self):
        self._run = False

    def __enter__(self, *args):
        if self._run:
            raise DuplicateUnitOfWork("already in use")
        self._run = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self._run = False

    def commit(self):
        self._handle_events()
        self._commit()

    def flush(self):
        self._flush()

    def rollback(self):
        self._rollback()

    @abstractmethod
    def _handle_events(self): ...

    @abstractmethod
    def _commit(self): ...

    @abstractmethod
    def _flush(self): ...

    @abstractmethod
    def _rollback(self): ...

    @contextmanager
    def transaction(self):
        if self._run:
            # 이미 트랜잭션이 실행 중이면, 새로운 트랜잭션을 시작하지 않고 현재 상태를 유지
            yield self
            return

        with self as this:
            try:
                yield this
                self.commit()
            except Exception:
                self.rollback()
                raise


class CommonRDBUow(AbstractUnitOfWork, ABC, Generic[T]):
    def __init__(self, event_handler: type[EventHandler], model_cls: type[T], session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = event_handler()
        self.model_cls = model_cls

    def __enter__(self, *args):
        self.session = self.session_factory()
        self.repository = CommonRDBRepository[T](self.session, self.model_cls)
        return super().__enter__(*args)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _handle_events(self):
        for seen in self.repository.seen:
            while seen.events:
                event = seen.events.popleft()
                self.event_handler.handle(event, self, self.session)

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()

    def _flush(self):
        self.session.flush()
