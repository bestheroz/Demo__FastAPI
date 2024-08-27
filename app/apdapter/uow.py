from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import TypeVar

T = TypeVar("T", bound="AbstractUnitOfWork")


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

    async def __aexit__(self, *args):
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
    async def autocommit(self):
        async with self as this:
            yield this
            await self.commit()
