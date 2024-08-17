from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TypeVar

T = TypeVar("T", bound="AbstractUnitOfWork")


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

    def __exit__(self, *args):
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
    def autocommit(self):
        with self as this:
            yield this
            this.commit()
