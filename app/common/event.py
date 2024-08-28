from typing import Generic

from pydantic import BaseModel

from app.common.schema import T


class Event(BaseModel, Generic[T]):
    data: T
