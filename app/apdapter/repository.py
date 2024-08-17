from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.orm import Mapper, Session

T = TypeVar("T")


class AbcSeen(ABC, Generic[T]):
    def __init__(self):
        self.seen = set[T]()

    def add_seen(self, model_obj: T):
        self.seen.add(model_obj)


class AbcAdd(AbcSeen[T], ABC, Generic[T]):
    def add(self, model_obj: T):
        self._add(model_obj)
        self.add_seen(model_obj)

    @abstractmethod
    def _add(self, model_obj: T): ...


class AbcGet(AbcSeen[T], ABC, Generic[T]):
    def get(self, id) -> T | None:
        model_obj = self._get(id)
        if model_obj:
            self.add_seen(model_obj)
        return model_obj

    @abstractmethod
    def _get(self, id) -> T | None: ...


class CommonRDBRepository(AbcAdd[T], AbcGet[T], Generic[T]):
    def __init__(self, session: Session, model_cls: Mapper[T]):
        super().__init__()
        self.session = session
        self.model_cls = model_cls

    def _add(self, model_obj: T) -> None:
        self.session.add(model_obj)
        self.session.flush()

    def _get(self, id) -> T | None:
        return self.session.get(self.model_cls, id)
