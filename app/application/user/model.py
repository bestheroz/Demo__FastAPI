from pydantic import AwareDatetime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.apdapter.orm import Base, TZDateTime
from app.application.user.event import UserUpdated, UserRemoved, UserPasswordReset
from app.application.user.schema import UserResponse
from app.common.exception import SystemException500
from app.common.model import IdCreatedUpdated
from app.common.type import UserTypeEnum
from app.utils.datetime_utils import utcnow


class User(IdCreatedUpdated, Base):
    __tablename__ = "user"

    name: Mapped[str]
    use_flag: Mapped[bool]
    login_id: Mapped[str]

    token: Mapped[str | None]
    password: Mapped[bytes | None]
    change_password_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=True
    )
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=False
    )

    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    additional_info: Mapped[str] = mapped_column(JSON, nullable=False)

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    created_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(User.created_by_id) == remote(Admin.id)",
    )
    updated_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(User.updated_by_id) == remote(Admin.id)",
    )

    created_by_user: Mapped["User"] = relationship(
        viewonly=True,
        primaryjoin="foreign(User.created_by_id) == remote(User.id)",
    )
    updated_by_user: Mapped["User"] = relationship(
        viewonly=True,
        primaryjoin="foreign(User.updated_by_id) == remote(User.id)",
    )

    @property
    def created_by(self):
        if self.created_object_type == UserTypeEnum.user:
            return self.created_by_user
        elif self.created_object_type == UserTypeEnum.admin:
            return self.created_by_admin
        raise SystemException500()

    @property
    def updated_by(self):
        if self.updated_object_type == UserTypeEnum.user:
            return self.updated_by_user
        elif self.updated_object_type == UserTypeEnum.admin:
            return self.updated_by_admin
        raise SystemException500()

    def reset_password(self, operator_id: int):
        now = utcnow()
        self.password = None
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin

    def on_password_reset(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        self.events.append(UserPasswordReset(data=UserResponse.model_validate(self)))
        return UserResponse.model_validate(self)

    def on_removed(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserRemoved(data=event_data))
        return event_data

    def on_updated(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserUpdated(data=event_data))
        return event_data
