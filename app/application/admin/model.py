from pydantic import AwareDatetime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.apdapter.orm import Base, TZDateTime
from app.application.admin.event import (
    AdminRemoved,
    AdminUpdated,
    AdminCreated,
    AdminLoggedIn,
    AdminPasswordChanged,
)
from app.application.admin.schema import (
    AdminResponse,
    AdminCreate,
    AdminToken,
)
from app.common.exception import SystemException500
from app.common.model import IdCreatedUpdated
from app.common.schema import AccessTokenClaims
from app.common.type import AuthorityEnum, UserTypeEnum
from app.utils.datetime_utils import utcnow
from app.utils.jwt import create_access_token
from app.utils.password import verify_password, get_password_hash


class Admin(IdCreatedUpdated, Base):
    __tablename__ = "admin"

    login_id: Mapped[str]
    password: Mapped[str | None]
    token: Mapped[str | None]

    name: Mapped[str]
    use_flag: Mapped[bool]
    manager_flag: Mapped[bool]

    _authorities: Mapped[set[AuthorityEnum]] = mapped_column(
        "authorities", JSON, nullable=False
    )

    change_password_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=True
    )
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=False
    )

    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    created_by: Mapped["Admin"] = relationship(
        lazy="joined",
        innerjoin=True,
        viewonly=True,
        primaryjoin="foreign(Admin.created_by_id) == remote(Admin.id)",
    )
    updated_by: Mapped["Admin"] = relationship(
        lazy="joined",
        innerjoin=True,
        viewonly=True,
        primaryjoin="foreign(Admin.updated_by_id) == remote(Admin.id)",
    )

    @property
    def type(self):
        return UserTypeEnum.admin

    @property
    def authorities(self):
        return (
            {item for item in AuthorityEnum} if self.manager_flag else self._authorities
        )

    @staticmethod
    def new(
        data: AdminCreate,
        operator_id: int,
    ) -> "Admin":
        now = utcnow()
        return Admin(
            **data.model_dump(),
            removed_flag=False,
            created_at=now,
            created_by_id=operator_id,
            created_object_type=UserTypeEnum.admin,
            updated_at=now,
            updated_by_id=operator_id,
            updated_object_type=UserTypeEnum.admin,
        )

    def update(self, data: AdminCreate, operator_id: int):
        self.login_id = data.login_id
        self.name = data.name
        self.use_flag = data.use_flag
        self._authorities = data.authorities  # type: ignore
        self.manager_flag = data.manager_flag
        self.updated_at = utcnow()
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin

    def renew_token(self, refresh_token: str):
        self.token = refresh_token
        self.latest_active_at = utcnow()

    def sign_out(self):
        self.token = None

    def check_password(self, password: str):
        return verify_password(password, self.password)

    def change_password(self, password: str):
        now = utcnow()
        self.password = get_password_hash(password)
        self.change_password_at = now
        self.updated_at = now

    def on_created(self) -> AdminResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminResponse.model_validate(self)
        self.events.append(AdminCreated(data=event_data))
        return AdminResponse.model_validate(self)

    def on_updated(self) -> AdminResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminResponse.model_validate(self)
        self.events.append(AdminUpdated(data=event_data))
        return event_data

    def on_removed(self) -> AdminResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminResponse.model_validate(self)
        self.events.append(AdminRemoved(data=event_data))
        return event_data

    def on_logged_in(self) -> AdminToken:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        self.events.append(AdminLoggedIn(data=(AdminResponse.model_validate(self))))
        if self.token is None:
            raise SystemException500()
        return AdminToken(
            access_token=create_access_token(AccessTokenClaims.model_validate(self)),
            refresh_token=self.token,
        )

    def on_password_changed(self) -> AdminResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminResponse.model_validate(self)
        self.events.append(AdminPasswordChanged(data=event_data))
        return event_data
