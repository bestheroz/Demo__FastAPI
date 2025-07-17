from fastapi_events.dispatcher import dispatch
from pydantic import AwareDatetime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.core.exception import UnknownSystemException500
from app.dependencies.orm import Base, TZDateTime
from app.events.admin import AdminEvent
from app.models.base import IdCreatedUpdated
from app.schemas.admin import (
    AdminCreate,
    AdminResponse,
    AdminUpdate,
)
from app.schemas.base import Operator, Token
from app.types.base import AuthorityEnum, UserTypeEnum
from app.utils.datetime_utils import utcnow
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.password import get_password_hash


class Admin(IdCreatedUpdated, Base):
    __tablename__ = "admin"

    login_id: Mapped[str]
    password: Mapped[str | None]
    token: Mapped[str | None]

    name: Mapped[str]
    use_flag: Mapped[bool]
    manager_flag: Mapped[bool]

    _authorities: Mapped[set[AuthorityEnum]] = mapped_column("authorities", JSON, nullable=False)

    change_password_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=False)

    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    created_by: Mapped["Admin"] = relationship(
        lazy="joined",
        innerjoin=True,
        viewonly=True,
        primaryjoin="foreign(Admin.created_object_id) == remote(Admin.id)",
    )
    updated_by: Mapped["Admin"] = relationship(
        lazy="joined",
        innerjoin=True,
        viewonly=True,
        primaryjoin="foreign(Admin.updated_object_id) == remote(Admin.id)",
    )

    @property
    def type(self):
        return UserTypeEnum.ADMIN

    @property
    def authorities(self):
        return {item for item in AuthorityEnum} if self.manager_flag else self._authorities

    @staticmethod
    def new(
        data: AdminCreate,
        operator_id: int,
    ) -> "Admin":
        now = utcnow()
        return Admin(
            **data.model_dump(exclude={"authorities", "password"}),
            _authorities=data.authorities,
            password=get_password_hash(data.password.get_secret_value()),
            removed_flag=False,
            joined_at=now,
            created_at=now,
            created_object_id=operator_id,
            created_object_type=UserTypeEnum.ADMIN,
            updated_at=now,
            updated_object_id=operator_id,
            updated_object_type=UserTypeEnum.ADMIN,
        )

    def update(self, data: AdminUpdate, operator_id: int):
        now = utcnow()
        self.login_id = data.login_id
        self.name = data.name
        self.use_flag = data.use_flag
        self._authorities = data.authorities  # type: ignore
        self.manager_flag = data.manager_flag
        self.updated_at = now
        self.updated_object_id = operator_id
        self.updated_object_type = UserTypeEnum.ADMIN
        if data.password and data.password.get_secret_value():
            self.password = get_password_hash(data.password.get_secret_value())
            self.change_password_at = now

    def change_password(self, password: str, operator: Operator):
        now = utcnow()
        self.password = get_password_hash(password)
        self.change_password_at = now
        self.updated_at = now
        self.updated_object_id = operator.id
        self.updated_object_type = operator.type

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_object_id = operator_id
        self.updated_object_type = UserTypeEnum.ADMIN

    def renew_token(self):
        self.token = create_refresh_token(self)
        self.latest_active_at = utcnow()

    def logout(self):
        self.token = None

    def on_created(self) -> AdminResponse:
        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = AdminResponse.model_validate(self)
        dispatch(AdminEvent.ADMIN_CREATED, event_data)
        return AdminResponse.model_validate(self)

    def on_updated(self) -> AdminResponse:
        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = AdminResponse.model_validate(self)
        dispatch(AdminEvent.ADMIN_UPDATED, event_data)
        return event_data

    def on_removed(self) -> AdminResponse:
        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = AdminResponse.model_validate(self)
        dispatch(AdminEvent.ADMIN_REMOVED, event_data)
        return event_data

    def on_logged_in(self) -> Token:
        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        dispatch(AdminEvent.ADMIN_LOGGED_IN, AdminResponse.model_validate(self))
        if self.token is None:
            raise UnknownSystemException500()
        return Token(
            access_token=create_access_token(self),
            refresh_token=self.token,
        )

    def on_password_changed(self) -> AdminResponse:
        session = object_session(self)
        if not session:
            raise UnknownSystemException500()
        session.flush()

        event_data = AdminResponse.model_validate(self)
        dispatch(AdminEvent.ADMIN_PASSWORD_CHANGED, event_data)
        return event_data
