from abc import ABC, abstractmethod
from contextlib import asynccontextmanager


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
