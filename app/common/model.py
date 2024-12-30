from sqlalchemy.orm import Mapped

from app.common.type import UserTypeEnum
from app.config.orm import (
    mapped_created_at,
    mapped_intpk,
    mapped_updated_at,
)


class IdCreated:
    id: Mapped[mapped_intpk]
    created_object_type: Mapped[UserTypeEnum]
    created_at: Mapped[mapped_created_at]
    created_object_id: Mapped[int]


class IdCreatedUpdated(IdCreated):
    updated_object_type: Mapped[UserTypeEnum]
    updated_at: Mapped[mapped_updated_at]
    updated_object_id: Mapped[int]
