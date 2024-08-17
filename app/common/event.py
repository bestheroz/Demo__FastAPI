from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Event(BaseModel, Generic[T]):
    data: T
