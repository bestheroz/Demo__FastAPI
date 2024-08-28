from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Generic

from app.apdapter.event import EventHandler
from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository, T


class DuplicateUnitOfWork(Exception):
    pass


class AbstractUnitOfWork(ABC):
    def __init__(self):
        self._run = False

    async def __aenter__(self, *args):
        if self._run:
            raise DuplicateUnitOfWork("already in use")
        self._run = True
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        self._run = False

    async def commit(self):
        await self._handle_events()
        await self._commit()

    async def flush(self):
        await self._flush()

    async def rollback(self):
        await self._rollback()

    @abstractmethod
    async def _handle_events(self): ...

    @abstractmethod
    async def _commit(self): ...

    @abstractmethod
    async def _flush(self): ...

    @abstractmethod
    async def _rollback(self): ...

    @asynccontextmanager
    async def transaction(self):
        if self._run:
            # 이미 트랜잭션이 실행 중이면, 새로운 트랜잭션을 시작하지 않고 현재 상태를 유지
            yield self
            return

        async with self as this:
            try:
                yield this
                await self.commit()
            except Exception:
                await self.rollback()
                raise


class CommonRDBUow(AbstractUnitOfWork, ABC, Generic[T]):
    def __init__(self, event_handler: type[EventHandler], session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = event_handler()

    async def __aenter__(self, *args):
        self.session = self.session_factory()
        self.repository = CommonRDBRepository[T](self.session, T)  # type: ignore
        return await super().__aenter__(*args)

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self.session.close()

    async def _handle_events(self):
        for seen in self.repository.seen:
            while seen.events:  # type: ignore
                event = seen.events.popleft()  # type: ignore
                await self.event_handler.handle(event, self, self.session)

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def _flush(self):
        await self.session.flush()
