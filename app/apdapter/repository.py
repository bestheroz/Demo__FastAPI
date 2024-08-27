from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapper

T = TypeVar("T")


class AbcSeen(ABC, Generic[T]):
    def __init__(self):
        self.seen = set[T]()

    def add_seen(self, model_obj: T):
        self.seen.add(model_obj)


class AbcAdd(AbcSeen[T], ABC, Generic[T]):
    async def add(self, model_obj: T):
        await self._add(model_obj)
        self.add_seen(model_obj)

    @abstractmethod
    async def _add(self, model_obj: T): ...


class AbcGet(AbcSeen[T], ABC, Generic[T]):
    async def get(self, id) -> T | None:
        model_obj = await self._get(id)
        if model_obj:
            self.add_seen(model_obj)
        return model_obj

    @abstractmethod
    async def _get(self, id) -> T | None: ...


class CommonRDBRepository(AbcAdd[T], AbcGet[T], Generic[T]):
    def __init__(self, session: AsyncSession, model_cls: Mapper[T | None]):
        super().__init__()
        self.session = session
        self.model_cls = model_cls

    async def _add(self, model_obj: T) -> None:
        self.session.add(model_obj)
        await self.session.flush()

    async def _get(self, id) -> T | None:
        return await self.session.get(self.model_cls, id)
