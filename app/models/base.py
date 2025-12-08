from sqlalchemy.orm import Mapped

from app.dependencies.orm import (
    mapped_created_at,
    mapped_intpk,
    mapped_updated_at,
)
from app.types.base import UserTypeEnum


class IdCreated:
    id: mapped_intpk
    created_object_type: Mapped[UserTypeEnum]
    created_at: mapped_created_at
    created_object_id: Mapped[int]


class IdCreatedUpdated(IdCreated):
    updated_object_type: Mapped[UserTypeEnum]
    updated_at: mapped_updated_at
    updated_object_id: Mapped[int]
