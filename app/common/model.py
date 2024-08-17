from sqlalchemy.orm import Mapped

from app.apdapter.orm import (
    mapped_created_at,
    mapped_created_by_id,
    mapped_intpk,
    mapped_updated_at,
    mapped_updated_by_id,
)
from app.common.type import UserTypeEnum


class IdCreated:
    id: Mapped[mapped_intpk]
    created_object_type: Mapped[UserTypeEnum]
    created_at: Mapped[mapped_created_at]
    created_by_id: Mapped[mapped_created_by_id]


class IdCreatedUpdated(IdCreated):
    updated_object_type: Mapped[UserTypeEnum]
    updated_at: Mapped[mapped_updated_at]
    updated_by_id: Mapped[mapped_updated_by_id]
