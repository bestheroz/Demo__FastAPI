from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from fastapi_events.dispatcher import dispatch
from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from app.core.exception import UnknownSystemException500
from app.dependencies.orm import SQLModelBase, TZDateTime
from app.types.base import UserTypeEnum
from app.utils.datetime_utils import utcnow

if TYPE_CHECKING:
    from app.models.admin import Admin
    from app.models.user import User


# =============================================================================
# Notice SQLModel - 모델과 스키마 통합
# =============================================================================


class NoticeBase(SQLModelBase):
    """Notice 기본 필드 - 스키마와 모델 공통"""

    title: str = Field(description="제목")
    content: str = Field(description="내용")
    use_flag: bool = Field(default=True, description="사용 여부")


class NoticeCreate(NoticeBase):
    """Notice 생성 스키마"""

    pass


class NoticeTable(NoticeBase, table=True):
    """Notice 테이블 모델"""

    __tablename__ = "notice"  # pyright: ignore[reportAssignmentType]

    # Primary Key
    id: int | None = Field(default=None, primary_key=True)

    # Audit 필드 - Created
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column("created_at", TZDateTime, nullable=False),
    )
    created_object_id: int = Field(default=0)
    created_object_type: UserTypeEnum = Field(default=UserTypeEnum.ADMIN)

    # Audit 필드 - Updated
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column("updated_at", TZDateTime, nullable=False),
    )
    updated_object_id: int = Field(default=0)
    updated_object_type: UserTypeEnum = Field(default=UserTypeEnum.ADMIN)

    # Soft delete
    removed_flag: bool = Field(default=False)
    removed_at: datetime | None = Field(
        default=None,
        sa_column=Column("removed_at", TZDateTime, nullable=True),
    )

    # Relationships - Admin
    created_by_admin: Admin = Relationship(  # type: ignore[assignment]
        sa_relationship=relationship(
            "Admin",
            viewonly=True,
            primaryjoin="foreign(NoticeTable.created_object_id) == remote(Admin.id)",
            lazy="joined",
        )
    )
    updated_by_admin: Admin = Relationship(  # type: ignore[assignment]
        sa_relationship=relationship(
            "Admin",
            viewonly=True,
            primaryjoin="foreign(NoticeTable.updated_object_id) == remote(Admin.id)",
            lazy="joined",
        )
    )

    # Relationships - User
    created_by_user: User = Relationship(  # type: ignore[assignment]
        sa_relationship=relationship(
            "User",
            viewonly=True,
            primaryjoin="foreign(NoticeTable.created_object_id) == remote(User.id)",
            lazy="joined",
        )
    )
    updated_by_user: User = Relationship(  # type: ignore[assignment]
        sa_relationship=relationship(
            "User",
            viewonly=True,
            primaryjoin="foreign(NoticeTable.updated_object_id) == remote(User.id)",
            lazy="joined",
        )
    )

    @property
    def created_by(self):
        if self.created_object_type == UserTypeEnum.USER:
            return self.created_by_user
        elif self.created_object_type == UserTypeEnum.ADMIN:
            return self.created_by_admin
        raise UnknownSystemException500()

    @property
    def updated_by(self):
        if self.updated_object_type == UserTypeEnum.USER:
            return self.updated_by_user
        elif self.updated_object_type == UserTypeEnum.ADMIN:
            return self.updated_by_admin
        raise UnknownSystemException500()

    @staticmethod
    def new(data: NoticeCreate, operator_id: int) -> NoticeTable:
        now = utcnow()
        return NoticeTable(
            **data.model_dump(),
            created_at=now,
            created_object_id=operator_id,
            created_object_type=UserTypeEnum.ADMIN,
            updated_at=now,
            updated_object_id=operator_id,
            updated_object_type=UserTypeEnum.ADMIN,
            removed_flag=False,
        )

    def update(self, data: NoticeCreate, operator_id: int):
        now = utcnow()
        self.title = data.title
        self.content = data.content
        self.use_flag = data.use_flag
        self.updated_at = now
        self.updated_object_id = operator_id
        self.updated_object_type = UserTypeEnum.ADMIN

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_object_id = operator_id
        self.updated_object_type = UserTypeEnum.ADMIN

    def on_created(self) -> NoticeResponse:
        from sqlalchemy.orm import object_session

        from app.events.notice import NoticeEvent

        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = NoticeResponse.model_validate(self)
        dispatch(NoticeEvent.NOTICE_CREATED, event_data)
        return event_data

    def on_updated(self) -> NoticeResponse:
        from sqlalchemy.orm import object_session

        from app.events.notice import NoticeEvent

        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = NoticeResponse.model_validate(self)
        dispatch(NoticeEvent.NOTICE_UPDATED, event_data)
        return event_data

    def on_removed(self) -> NoticeResponse:
        from sqlalchemy.orm import object_session

        from app.events.notice import NoticeEvent

        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = NoticeResponse.model_validate(self)
        dispatch(NoticeEvent.NOTICE_REMOVED, event_data)
        return event_data


# =============================================================================
# Response 스키마 - 조회용
# =============================================================================

from app.schemas.base import IdCreatedUpdatedDto, Schema  # noqa: E402


class NoticeResponse(IdCreatedUpdatedDto, Schema):
    """Notice 응답 스키마 - Pydantic 기반"""

    title: str = Field(description="제목")  # type: ignore[assignment]
    content: str = Field(description="내용")  # type: ignore[assignment]
    use_flag: bool = Field(default=True, description="사용 여부")


# =============================================================================
# 하위 호환성을 위한 별칭
# =============================================================================

# 기존 코드 호환을 위한 별칭
Notice = NoticeTable
